"""Integration coverage for finance/payment flows.

Covers:
- Razorpay order creation (client-side)
- Payment webhook handling (signature verification, idempotency)
- Manual payment recording (admin)
- Client payment status updates (admin, auto-transition to assigned)
- Worker payout creation and status update
"""
import hashlib
import hmac
import json
from datetime import date
from unittest.mock import Mock, patch

import pytest

from app.core.assignment_constants import AssignmentStatus
from app.core.payment_constants import (
    ClientPaymentStatus,
    PaymentModel,
    PaymentPurpose,
    WorkerPayoutStatus,
)
from app.core.payroll_constants import PayrollItemPaymentStatus
from app.core.statuses import RequirementStatus
from app.models.assignment import Assignment
from app.models.client_payment import ClientPayment
from app.models.client_profile import ClientProfile
from app.models.payroll_item import PayrollItem
from app.models.payroll_run import PayrollRun
from app.models.quote import Quote
from app.models.requirement import Requirement
from app.models.worker_payout import WorkerPayout
from app.models.worker_profile import WorkerProfile
from app.services.payment_ledger_service import build_payment_ledger
from app.services.token_service import build_token_pair

BASE = "/api/v1"
PERIOD_START = date(2026, 5, 1)
PERIOD_END = date(2026, 5, 31)

# ──────────────────────────────────────────────────────────────────
# Shared fixtures
# ──────────────────────────────────────────────────────────────────


@pytest.fixture
def admin_headers(db, admin_user):
    access_token, _ = build_token_pair(
        db,
        user_id=admin_user.id,
        subject=admin_user.email,
        role=admin_user.role,
    )
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def client_headers(db, client_user):
    access_token, _ = build_token_pair(
        db,
        user_id=client_user.id,
        subject=client_user.phone,
        role=client_user.role,
    )
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def worker_headers(db, worker_user):
    access_token, _ = build_token_pair(
        db,
        user_id=worker_user.id,
        subject=worker_user.phone,
        role=worker_user.role,
    )
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def client_profile(db, client_user):
    profile = ClientProfile(
        user_id=client_user.id,
        client_type="company",
        company_name="Annam Textiles",
        contact_name="Priya Raman",
        city="Chennai",
        state="Tamil Nadu",
        address="T Nagar",
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


@pytest.fixture
def approved_requirement(db, client_profile, client_user, admin_user):
    req = Requirement(
        client_id=client_profile.id,
        category="Security",
        subcategory="Night Guard",
        number_of_workers=1,
        work_location="Warehouse Gate 1",
        city="Chennai",
        state="Tamil Nadu",
        start_date=PERIOD_START,
        duration_days=30,
        shift_details="Night 20:00-06:00",
        budget_amount=30000,
        status=RequirementStatus.APPROVED.value,
        created_by_user_id=client_user.id,
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    db.add(
        Quote(
            requirement_id=req.id,
            quoted_amount=30000,
            advance_amount=5000,
            payment_model=PaymentModel.CLIENT_PAYS_COMPANY.value,
            status="approved",
            created_by_user_id=admin_user.id,
        )
    )
    db.commit()
    return req


@pytest.fixture
def approved_requirement_with_advance_quote(db, approved_requirement, admin_user):
    return approved_requirement


@pytest.fixture
def pending_gateway_payment(db, client_profile, approved_requirement):
    payment = ClientPayment(
        client_id=client_profile.id,
        requirement_id=approved_requirement.id,
        amount=5000,
        payment_model=PaymentModel.CLIENT_PAYS_COMPANY.value,
        payment_mode="gateway",
        payment_status=ClientPaymentStatus.PENDING.value,
        gateway_order_id="order_test_pending_001",
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment


@pytest.fixture
def paid_gateway_payment(db, client_profile, approved_requirement):
    payment = ClientPayment(
        client_id=client_profile.id,
        requirement_id=approved_requirement.id,
        amount=5000,
        payment_model=PaymentModel.CLIENT_PAYS_COMPANY.value,
        payment_mode="gateway",
        payment_status=ClientPaymentStatus.PAID.value,
        gateway_order_id="order_test_paid_001",
        gateway_payment_id="pay_test_paid_001",
        gateway_signature="sig_test_paid_001",
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment


@pytest.fixture
def worker_profile(db, worker_user):
    profile = WorkerProfile(
        user_id=worker_user.id,
        full_name="Ravi Kumar",
        category="Security",
        subcategory="Night Guard",
        city="Chennai",
        state="Tamil Nadu",
        address="Velachery",
        skills="Security",
        available_shifts="Night",
        is_available=True,
        verification_status="approved",
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


@pytest.fixture
def payroll_item(db, admin_user, worker_profile, approved_requirement):
    assignment = Assignment(
        requirement_id=approved_requirement.id,
        worker_profile_id=worker_profile.id,
        assigned_by_user_id=admin_user.id,
        status=AssignmentStatus.ACCEPTED.value,
        assigned_role="Night Guard",
        assigned_shift="Night",
        salary_amount=30000,
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)

    run = PayrollRun(
        period_start=PERIOD_START,
        period_end=PERIOD_END,
        status="approved",
        created_by_user_id=admin_user.id,
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    item = PayrollItem(
        payroll_run_id=run.id,
        assignment_id=assignment.id,
        worker_profile_id=worker_profile.id,
        gross_amount=30000,
        total_deduction_amount=0,
        net_amount=30000,
        attendance_days=26,
        half_days=0,
        absent_days=0,
        payment_status=PayrollItemPaymentStatus.PENDING.value,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def _make_webhook_sig(body: bytes, secret: str) -> str:
    return hmac.new(
        secret.encode("utf-8"),
        body,
        hashlib.sha256,
    ).hexdigest()


# ──────────────────────────────────────────────────────────────────
# Razorpay Order Creation
# ──────────────────────────────────────────────────────────────────


def _make_checkout_sig(order_id: str, payment_id: str, secret: str) -> str:
    return hmac.new(
        secret.encode("utf-8"),
        f"{order_id}|{payment_id}".encode(),
        hashlib.sha256,
    ).hexdigest()


def _razorpay_capture_body(
    payment: ClientPayment,
    *,
    gateway_payment_id: str,
    amount_paise: int | None = None,
) -> bytes:
    return json.dumps(
        {
            "event": "payment.captured",
            "payload": {
                "payment": {
                    "entity": {
                        "id": gateway_payment_id,
                        "order_id": payment.gateway_order_id,
                        "amount": amount_paise
                        if amount_paise is not None
                        else payment.amount * 100,
                        "currency": "INR",
                        "status": "captured",
                        "captured": True,
                    }
                }
            },
        },
        separators=(",", ":"),
    ).encode()


def _post_razorpay_capture(
    client,
    body: bytes,
    *,
    secret: str,
    event_id: str,
):
    return client.post(
        f"{BASE}/payments/webhook/razorpay",
        content=body,
        headers={
            "Content-Type": "application/json",
            "X-Razorpay-Signature": _make_webhook_sig(body, secret),
            "X-Razorpay-Event-Id": event_id,
        },
    )


def _post_razorpay_refund_event(
    client,
    refund_payment: ClientPayment,
    source_payment: ClientPayment,
    *,
    gateway_refund_id: str,
    gateway_status: str,
    event: str,
    secret: str,
    event_id: str,
):
    body = json.dumps(
        {
            "event": event,
            "payload": {
                "refund": {
                    "entity": {
                        "id": gateway_refund_id,
                        "payment_id": source_payment.gateway_payment_id,
                        "amount": refund_payment.amount * 100,
                        "currency": "INR",
                        "status": gateway_status,
                        "notes": {"refund_payment_id": str(refund_payment.id)},
                    }
                }
            },
        },
        separators=(",", ":"),
    ).encode()
    return client.post(
        f"{BASE}/payments/webhook/razorpay",
        content=body,
        headers={
            "Content-Type": "application/json",
            "X-Razorpay-Signature": _make_webhook_sig(body, secret),
            "X-Razorpay-Event-Id": event_id,
        },
    )


class TestRazorpayOrderCreation:
    def test_client_creates_payment_order_successfully(
        self, client, client_headers, client_profile, approved_requirement
    ):
        fake_order = {"id": "order_FAKEID001", "amount": 500000, "currency": "INR"}
        with patch("app.api.client_payments.razorpay_service.create_order", return_value=fake_order):
            response = client.post(
                f"{BASE}/client/payments/create-order",
                json={
                    "requirement_id": approved_requirement.id,
                    "amount": 5000,
                    "payment_model": PaymentModel.CLIENT_PAYS_COMPANY.value,
                },
                headers=client_headers,
            )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["gateway_order_id"] == "order_FAKEID001"
        assert data["amount"] == 5000
        assert data["status"] == ClientPaymentStatus.PENDING.value

    def test_client_amount_and_model_cannot_change_authoritative_charge(
        self, client, client_headers, client_profile, approved_requirement
    ):
        fake_order = {"id": "order_SERVER_AUTH", "amount": 500000, "currency": "INR"}
        with patch(
            "app.api.client_payments.razorpay_service.create_order",
            return_value=fake_order,
        ) as create_order:
            response = client.post(
                f"{BASE}/client/payments/create-order",
                json={
                    "requirement_id": approved_requirement.id,
                    "amount": 1,
                    "payment_model": PaymentModel.MIXED.value,
                },
                headers=client_headers,
            )

        assert response.status_code == 200
        assert response.json()["data"]["amount"] == 5000
        create_order.assert_called_once()
        assert create_order.call_args.kwargs["amount_rupees"] == 5000

    def test_non_client_cannot_create_order(
        self, client, admin_headers, approved_requirement
    ):
        response = client.post(
            f"{BASE}/client/payments/create-order",
            json={
                "requirement_id": approved_requirement.id,
                "amount": 5000,
                "payment_model": PaymentModel.CLIENT_PAYS_COMPANY.value,
            },
            headers=admin_headers,
        )
        assert response.status_code == 403

    def test_missing_client_profile_returns_404(
        self, client, client_headers
    ):
        # client_user exists but has no ClientProfile — the endpoint must
        # return 404 before reaching the requirement lookup or Razorpay call.
        response = client.post(
            f"{BASE}/client/payments/create-order",
            json={
                "requirement_id": 1,
                "amount": 1000,
                "payment_model": PaymentModel.CLIENT_PAYS_COMPANY.value,
            },
            headers=client_headers,
        )
        assert response.status_code == 404
        assert "profile" in response.json()["message"].lower()

    def test_requirement_not_found_returns_404(
        self, client, client_headers, client_profile
    ):
        fake_order = {"id": "order_X", "amount": 100, "currency": "INR"}
        with patch("app.api.client_payments.razorpay_service.create_order", return_value=fake_order):
            response = client.post(
                f"{BASE}/client/payments/create-order",
                json={
                    "requirement_id": 999999,
                    "amount": 1000,
                    "payment_model": PaymentModel.CLIENT_PAYS_COMPANY.value,
                },
                headers=client_headers,
            )
        assert response.status_code == 404

    def test_requirement_owned_by_another_client_returns_404(
        self, client, db, client_headers, client_profile, admin_user
    ):
        from app.models.user import User

        other_user = User(
            phone="9000000099",
            role="client",
            is_active=True,
            is_phone_verified=True,
        )
        db.add(other_user)
        db.commit()
        db.refresh(other_user)
        other_profile = ClientProfile(
            user_id=other_user.id,
            client_type="individual",
            contact_name="Other Client",
            city="Madurai",
            state="Tamil Nadu",
            address="Main St",
        )
        db.add(other_profile)
        db.commit()
        db.refresh(other_profile)
        other_req = Requirement(
            client_id=other_profile.id,
            category="Housekeeping",
            number_of_workers=1,
            work_location="Site A",
            city="Madurai",
            state="Tamil Nadu",
            start_date=PERIOD_START,
            duration_days=10,
            shift_details="Day",
            budget_amount=5000,
            status=RequirementStatus.SUBMITTED.value,
            created_by_user_id=other_user.id,
        )
        db.add(other_req)
        db.commit()

        fake_order = {"id": "order_X", "amount": 100, "currency": "INR"}
        with patch("app.api.client_payments.razorpay_service.create_order", return_value=fake_order):
            response = client.post(
                f"{BASE}/client/payments/create-order",
                json={
                    "requirement_id": other_req.id,
                    "amount": 1000,
                    "payment_model": PaymentModel.CLIENT_PAYS_COMPANY.value,
                },
                headers=client_headers,
            )
        assert response.status_code == 404

    def test_invalid_payment_model_returns_422(
        self, client, client_headers, client_profile, approved_requirement
    ):
        response = client.post(
            f"{BASE}/client/payments/create-order",
            json={
                "requirement_id": approved_requirement.id,
                "amount": 1000,
                "payment_model": "invalid_model",
            },
            headers=client_headers,
        )
        assert response.status_code == 422

    def test_gateway_failure_returns_502(
        self, client, client_headers, client_profile, approved_requirement
    ):
        import httpx

        with patch(
            "app.api.client_payments.razorpay_service.create_order",
            side_effect=httpx.RequestError("timeout"),
        ):
            response = client.post(
                f"{BASE}/client/payments/create-order",
                json={
                    "requirement_id": approved_requirement.id,
                    "amount": 5000,
                    "payment_model": PaymentModel.CLIENT_PAYS_COMPANY.value,
                },
                headers=client_headers,
            )
        assert response.status_code == 502


# ──────────────────────────────────────────────────────────────────
# Payment Webhook
# ──────────────────────────────────────────────────────────────────


class TestRazorpayRefundAdapter:
    def test_refund_uses_paise_and_idempotency_header(self):
        from app.services import razorpay_service

        response = Mock()
        response.json.return_value = {
            "id": "rfnd_adapter_test",
            "payment_id": "pay_adapter_test",
            "amount": 12500,
            "currency": "INR",
            "status": "processed",
        }
        with patch(
            "app.services.razorpay_service.httpx.post",
            return_value=response,
        ) as post:
            result = razorpay_service.create_refund(
                "pay_adapter_test",
                125,
                "refund-adapter-key",
                receipt="refund-125",
                notes={"refund_payment_id": "125"},
            )

        response.raise_for_status.assert_called_once_with()
        assert result["id"] == "rfnd_adapter_test"
        _, kwargs = post.call_args
        assert kwargs["headers"] == {
            "X-Refund-Idempotency": "refund-adapter-key"
        }
        assert kwargs["json"]["amount"] == 12500
        assert kwargs["json"]["speed"] == "normal"


class TestPaymentWebhook:
    def _webhook_body(self, gateway_order_id: str, gateway_payment_id: str, sig: str) -> bytes:
        return json.dumps(
            {
                "gateway_order_id": gateway_order_id,
                "gateway_payment_id": gateway_payment_id,
                "gateway_signature": sig,
            }
        ).encode()

    def test_valid_webhook_marks_payment_paid(
        self, client, db, pending_gateway_payment
    ):
        """In local env with no secret, signature check is skipped."""
        body = self._webhook_body(
            gateway_order_id=pending_gateway_payment.gateway_order_id,
            gateway_payment_id="pay_test_new_001",
            sig="any_sig_skipped_in_local",
        )
        response = client.post(
            f"{BASE}/payments/webhook",
            content=body,
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["status"] == ClientPaymentStatus.PAID.value

        db.refresh(pending_gateway_payment)
        assert pending_gateway_payment.payment_status == ClientPaymentStatus.PAID.value
        assert pending_gateway_payment.gateway_payment_id == "pay_test_new_001"
        assert pending_gateway_payment.paid_at is not None

    def test_webhook_with_valid_signature_marks_paid(
        self, client, db, pending_gateway_payment, monkeypatch
    ):
        """When a webhook secret is configured locally and sig matches, payment is marked paid."""
        from app.core import config as _cfg

        monkeypatch.setattr(_cfg.settings, "payment_webhook_secret", "test-wh-secret-123")

        body = self._webhook_body(
            gateway_order_id=pending_gateway_payment.gateway_order_id,
            gateway_payment_id="pay_test_sig_001",
            sig="dummy_not_checked_in_local",
        )
        sig_header = _make_webhook_sig(body, "test-wh-secret-123")
        response = client.post(
            f"{BASE}/payments/webhook",
            content=body,
            headers={
                "Content-Type": "application/json",
                "x-payment-signature": sig_header,
            },
        )
        assert response.status_code == 200
        db.refresh(pending_gateway_payment)
        assert pending_gateway_payment.payment_status == ClientPaymentStatus.PAID.value

    def test_webhook_with_wrong_signature_rejected(
        self, client, pending_gateway_payment, monkeypatch
    ):
        """When a webhook secret is configured locally and sig mismatches, 401 is returned."""
        from app.core import config as _cfg

        monkeypatch.setattr(_cfg.settings, "payment_webhook_secret", "test-wh-secret-123")

        body = self._webhook_body(
            gateway_order_id=pending_gateway_payment.gateway_order_id,
            gateway_payment_id="pay_test_bad_sig",
            sig="dummy_sig",
        )
        response = client.post(
            f"{BASE}/payments/webhook",
            content=body,
            headers={
                "Content-Type": "application/json",
                "x-payment-signature": "wrong-signature-value",
            },
        )
        assert response.status_code == 401

    def test_webhook_order_not_found_returns_404(self, client):
        body = self._webhook_body(
            gateway_order_id="order_does_not_exist",
            gateway_payment_id="pay_xxx",
            sig="sig_xxx",
        )
        response = client.post(
            f"{BASE}/payments/webhook",
            content=body,
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 404

    def test_duplicate_webhook_is_idempotent(
        self, client, paid_gateway_payment
    ):
        """A second webhook for an already-paid order returns 200 without re-processing."""
        body = self._webhook_body(
            gateway_order_id=paid_gateway_payment.gateway_order_id,
            gateway_payment_id="pay_test_dup_002",
            sig="sig_dup",
        )
        response = client.post(
            f"{BASE}/payments/webhook",
            content=body,
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["status"] == ClientPaymentStatus.PAID.value
        # gateway_payment_id must NOT have been overwritten
        assert data["payment_id"] == paid_gateway_payment.id

    def test_webhook_invalid_payload_returns_422(self, client):
        response = client.post(
            f"{BASE}/payments/webhook",
            content=b'{"gateway_order_id": "x"}',  # missing required fields
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 422

    def test_legacy_webhook_is_unavailable_outside_local(
        self,
        client,
        pending_gateway_payment,
        monkeypatch,
    ):
        from app.core import config as _cfg

        monkeypatch.setattr(_cfg.settings, "app_env", "staging")
        body = self._webhook_body(
            gateway_order_id=pending_gateway_payment.gateway_order_id,
            gateway_payment_id="pay_legacy_disabled",
            sig="unused",
        )

        response = client.post(
            f"{BASE}/payments/webhook",
            content=body,
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 404


# ──────────────────────────────────────────────────────────────────
# Manual Payment Recording
# ──────────────────────────────────────────────────────────────────


class TestRazorpayReconciliation:
    WEBHOOK_SECRET = "test-razorpay-webhook-secret"
    KEY_SECRET = "test-razorpay-key-secret"

    def _configure_secrets(self, monkeypatch):
        from app.core import config as _cfg

        monkeypatch.setattr(
            _cfg.settings,
            "payment_webhook_secret",
            self.WEBHOOK_SECRET,
        )
        monkeypatch.setattr(
            _cfg.settings,
            "razorpay_key_secret",
            self.KEY_SECRET,
        )

    def test_duplicate_captured_webhook_is_a_no_op(
        self,
        client,
        db,
        pending_gateway_payment,
        monkeypatch,
    ):
        self._configure_secrets(monkeypatch)
        body = _razorpay_capture_body(
            pending_gateway_payment,
            gateway_payment_id="pay_capture_duplicate",
        )

        first = _post_razorpay_capture(
            client,
            body,
            secret=self.WEBHOOK_SECRET,
            event_id="evt_capture_duplicate",
        )
        assert first.status_code == 200
        db.refresh(pending_gateway_payment)
        first_paid_at = pending_gateway_payment.paid_at

        second = _post_razorpay_capture(
            client,
            body,
            secret=self.WEBHOOK_SECRET,
            event_id="evt_capture_duplicate",
        )
        assert second.status_code == 200
        assert "already" in second.json()["message"].lower()

        db.refresh(pending_gateway_payment)
        assert pending_gateway_payment.gateway_payment_id == "pay_capture_duplicate"
        assert pending_gateway_payment.paid_at == first_paid_at

    def test_duplicate_payment_id_on_another_order_is_a_no_op(
        self,
        client,
        db,
        client_profile,
        approved_requirement,
        pending_gateway_payment,
        monkeypatch,
    ):
        self._configure_secrets(monkeypatch)
        other_payment = ClientPayment(
            client_id=client_profile.id,
            requirement_id=approved_requirement.id,
            amount=pending_gateway_payment.amount,
            purpose=pending_gateway_payment.purpose,
            payment_model=pending_gateway_payment.payment_model,
            payment_mode="gateway",
            payment_status=ClientPaymentStatus.PENDING.value,
            gateway_order_id="order_test_pending_002",
        )
        db.add(other_payment)
        db.commit()
        db.refresh(other_payment)

        first_body = _razorpay_capture_body(
            pending_gateway_payment,
            gateway_payment_id="pay_shared_capture",
        )
        assert _post_razorpay_capture(
            client,
            first_body,
            secret=self.WEBHOOK_SECRET,
            event_id="evt_shared_capture_1",
        ).status_code == 200

        duplicate_body = _razorpay_capture_body(
            other_payment,
            gateway_payment_id="pay_shared_capture",
        )
        duplicate = _post_razorpay_capture(
            client,
            duplicate_body,
            secret=self.WEBHOOK_SECRET,
            event_id="evt_shared_capture_2",
        )
        assert duplicate.status_code == 200
        assert "without changing" in duplicate.json()["message"].lower()

        db.refresh(other_payment)
        assert other_payment.payment_status == ClientPaymentStatus.PENDING.value
        assert other_payment.gateway_payment_id is None

    def test_webhook_before_mobile_callback_reconciles_once(
        self,
        client,
        db,
        client_headers,
        pending_gateway_payment,
        monkeypatch,
    ):
        self._configure_secrets(monkeypatch)
        gateway_payment_id = "pay_webhook_before_callback"
        body = _razorpay_capture_body(
            pending_gateway_payment,
            gateway_payment_id=gateway_payment_id,
        )
        webhook = _post_razorpay_capture(
            client,
            body,
            secret=self.WEBHOOK_SECRET,
            event_id="evt_webhook_before_callback",
        )
        assert webhook.status_code == 200
        db.refresh(pending_gateway_payment)
        first_paid_at = pending_gateway_payment.paid_at

        checkout_signature = _make_checkout_sig(
            pending_gateway_payment.gateway_order_id,
            gateway_payment_id,
            self.KEY_SECRET,
        )
        with patch(
            "app.api.client_payments.razorpay_service.fetch_payment"
        ) as fetch_payment:
            callback = client.post(
                f"{BASE}/client/payments/verify",
                json={
                    "razorpay_order_id": pending_gateway_payment.gateway_order_id,
                    "razorpay_payment_id": gateway_payment_id,
                    "razorpay_signature": checkout_signature,
                },
                headers=client_headers,
            )

        assert callback.status_code == 200
        assert "already" in callback.json()["message"].lower()
        fetch_payment.assert_not_called()
        db.refresh(pending_gateway_payment)
        assert pending_gateway_payment.gateway_signature == checkout_signature
        assert pending_gateway_payment.paid_at == first_paid_at

    def test_mobile_callback_before_webhook_reconciles_once(
        self,
        client,
        db,
        client_headers,
        pending_gateway_payment,
        monkeypatch,
    ):
        self._configure_secrets(monkeypatch)
        gateway_payment_id = "pay_callback_before_webhook"
        checkout_signature = _make_checkout_sig(
            pending_gateway_payment.gateway_order_id,
            gateway_payment_id,
            self.KEY_SECRET,
        )
        gateway_entity = {
            "id": gateway_payment_id,
            "order_id": pending_gateway_payment.gateway_order_id,
            "amount": pending_gateway_payment.amount * 100,
            "currency": "INR",
            "status": "captured",
            "captured": True,
        }
        with patch(
            "app.api.client_payments.razorpay_service.fetch_payment",
            return_value=gateway_entity,
        ):
            callback = client.post(
                f"{BASE}/client/payments/verify",
                json={
                    "razorpay_order_id": pending_gateway_payment.gateway_order_id,
                    "razorpay_payment_id": gateway_payment_id,
                    "razorpay_signature": checkout_signature,
                },
                headers=client_headers,
            )
        assert callback.status_code == 200
        db.refresh(pending_gateway_payment)
        first_paid_at = pending_gateway_payment.paid_at

        body = _razorpay_capture_body(
            pending_gateway_payment,
            gateway_payment_id=gateway_payment_id,
        )
        webhook = _post_razorpay_capture(
            client,
            body,
            secret=self.WEBHOOK_SECRET,
            event_id="evt_callback_before_webhook",
        )
        assert webhook.status_code == 200
        assert "already" in webhook.json()["message"].lower()
        db.refresh(pending_gateway_payment)
        assert pending_gateway_payment.paid_at == first_paid_at

    def test_amount_mismatch_never_changes_ledger(
        self,
        client,
        db,
        pending_gateway_payment,
        monkeypatch,
    ):
        self._configure_secrets(monkeypatch)
        body = _razorpay_capture_body(
            pending_gateway_payment,
            gateway_payment_id="pay_wrong_amount",
            amount_paise=pending_gateway_payment.amount * 100 - 1,
        )

        response = _post_razorpay_capture(
            client,
            body,
            secret=self.WEBHOOK_SECRET,
            event_id="evt_wrong_amount",
        )

        assert response.status_code == 200
        assert "without changing" in response.json()["message"].lower()
        db.refresh(pending_gateway_payment)
        assert pending_gateway_payment.payment_status == ClientPaymentStatus.PENDING.value
        assert pending_gateway_payment.gateway_payment_id is None


class TestManualPaymentRecording:
    def _payload(self, requirement_id: int, **overrides) -> dict:
        base = {
            "requirement_id": requirement_id,
            "amount": 5000,
            "payment_model": PaymentModel.CLIENT_PAYS_COMPANY.value,
            "payment_mode": "upi",
            "payment_status": ClientPaymentStatus.PAID.value,
            "reference_note": "UTR123456",
        }
        base.update(overrides)
        return base

    def test_admin_records_manual_payment_successfully(
        self, client, admin_headers, approved_requirement
    ):
        response = client.post(
            f"{BASE}/admin/finance/client-payments/manual",
            json=self._payload(approved_requirement.id),
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert "payment_id" in data
        assert data["status"] == ClientPaymentStatus.PAID.value

    def test_client_cannot_record_manual_payment(
        self, client, client_headers, client_profile, approved_requirement
    ):
        response = client.post(
            f"{BASE}/admin/finance/client-payments/manual",
            json=self._payload(approved_requirement.id),
            headers=client_headers,
        )
        assert response.status_code == 403

    def test_gateway_refund_cannot_bypass_razorpay_endpoint(
        self, client, admin_headers, approved_requirement
    ):
        response = client.post(
            f"{BASE}/admin/finance/client-payments/manual",
            json=self._payload(
                approved_requirement.id,
                purpose=PaymentPurpose.REFUND.value,
                payment_mode="gateway",
            ),
            headers=admin_headers,
        )
        assert response.status_code == 400
        assert "razorpay refund" in response.json()["message"].lower()

    def test_worker_cannot_record_manual_payment(
        self, client, worker_headers, approved_requirement
    ):
        response = client.post(
            f"{BASE}/admin/finance/client-payments/manual",
            json=self._payload(approved_requirement.id),
            headers=worker_headers,
        )
        assert response.status_code == 403

    def test_requirement_not_found_returns_404(
        self, client, admin_headers
    ):
        response = client.post(
            f"{BASE}/admin/finance/client-payments/manual",
            json=self._payload(999999),
            headers=admin_headers,
        )
        assert response.status_code == 404

    def test_invalid_payment_model_returns_422(
        self, client, admin_headers, approved_requirement
    ):
        # Pydantic validates payment_model before the handler runs → 422
        response = client.post(
            f"{BASE}/admin/finance/client-payments/manual",
            json=self._payload(approved_requirement.id, payment_model="nonexistent_model"),
            headers=admin_headers,
        )
        assert response.status_code == 422

    def test_invalid_payment_status_returns_422(
        self, client, admin_headers, approved_requirement
    ):
        # Pydantic validates payment_status before the handler runs → 422
        response = client.post(
            f"{BASE}/admin/finance/client-payments/manual",
            json=self._payload(approved_requirement.id, payment_status="bad_status"),
            headers=admin_headers,
        )
        assert response.status_code == 422

    def test_manual_payment_recorded_as_pending(
        self, client, admin_headers, approved_requirement
    ):
        response = client.post(
            f"{BASE}/admin/finance/client-payments/manual",
            json=self._payload(
                approved_requirement.id,
                payment_status=ClientPaymentStatus.PENDING.value,
            ),
            headers=admin_headers,
        )
        assert response.status_code == 200
        assert response.json()["data"]["status"] == ClientPaymentStatus.PENDING.value

    def test_manual_payment_recorded_as_failed(
        self, client, admin_headers, approved_requirement
    ):
        response = client.post(
            f"{BASE}/admin/finance/client-payments/manual",
            json=self._payload(
                approved_requirement.id,
                payment_status=ClientPaymentStatus.FAILED.value,
            ),
            headers=admin_headers,
        )
        assert response.status_code == 200
        assert response.json()["data"]["status"] == ClientPaymentStatus.FAILED.value

    def test_manual_payment_recorded_as_refunded(
        self, client, admin_headers, approved_requirement
    ):
        response = client.post(
            f"{BASE}/admin/finance/client-payments/manual",
            json=self._payload(
                approved_requirement.id,
                payment_status=ClientPaymentStatus.REFUNDED.value,
            ),
            headers=admin_headers,
        )
        assert response.status_code == 200
        assert response.json()["data"]["status"] == ClientPaymentStatus.REFUNDED.value


# ──────────────────────────────────────────────────────────────────
# Client Payment Status Update
# ──────────────────────────────────────────────────────────────────


class TestGatewayRefunds:
    WEBHOOK_SECRET = "test-razorpay-refund-webhook-secret"

    @staticmethod
    def _payload(**overrides) -> dict:
        payload = {
            "amount": 2000,
            "idempotency_key": "refund-request-0001",
            "reason": "Approved partial cancellation refund",
        }
        payload.update(overrides)
        return payload

    @staticmethod
    def _gateway_refund(source_payment: ClientPayment, **overrides) -> dict:
        refund = {
            "id": "rfnd_test_0001",
            "payment_id": source_payment.gateway_payment_id,
            "amount": 200000,
            "currency": "INR",
            "status": "processed",
        }
        refund.update(overrides)
        return refund

    def test_admin_refund_executes_once_and_reconciles_ledger(
        self,
        client,
        db,
        admin_headers,
        paid_gateway_payment,
        approved_requirement,
    ):
        gateway_refund = self._gateway_refund(paid_gateway_payment)
        with patch(
            "app.api.admin_finance.razorpay_service.create_refund",
            return_value=gateway_refund,
        ) as create_refund:
            first = client.post(
                f"{BASE}/admin/finance/client-payments/{paid_gateway_payment.id}/refunds",
                json=self._payload(),
                headers=admin_headers,
            )
            second = client.post(
                f"{BASE}/admin/finance/client-payments/{paid_gateway_payment.id}/refunds",
                json=self._payload(),
                headers=admin_headers,
            )

        assert first.status_code == 200, first.json()
        assert second.status_code == 200, second.json()
        assert "already processed" in second.json()["message"].lower()
        refund_payment_id = first.json()["data"]["refund_payment_id"]
        create_refund.assert_called_once_with(
            paid_gateway_payment.gateway_payment_id,
            2000,
            "refund-request-0001",
            receipt=f"refund-{refund_payment_id}",
            notes={
                "refund_payment_id": str(refund_payment_id),
                "requirement_id": str(approved_requirement.id),
            },
        )

        refunds = (
            db.query(ClientPayment)
            .filter(
                ClientPayment.parent_payment_id == paid_gateway_payment.id,
                ClientPayment.purpose == PaymentPurpose.REFUND.value,
            )
            .all()
        )
        assert len(refunds) == 1
        assert refunds[0].payment_status == ClientPaymentStatus.PAID.value
        assert refunds[0].gateway_refund_id == "rfnd_test_0001"

        quote = db.query(Quote).filter_by(requirement_id=approved_requirement.id).one()
        payments = (
            db.query(ClientPayment)
            .filter_by(requirement_id=approved_requirement.id)
            .all()
        )
        ledger = build_payment_ledger(quote, payments)
        assert ledger.gross_paid == 5000
        assert ledger.refunded_amount == 2000
        assert ledger.total_paid == 3000
        assert ledger.outstanding_balance == 27000

    def test_refund_cannot_exceed_source_refundable_balance(
        self,
        client,
        admin_headers,
        paid_gateway_payment,
    ):
        with patch("app.api.admin_finance.razorpay_service.create_refund") as create_refund:
            response = client.post(
                f"{BASE}/admin/finance/client-payments/{paid_gateway_payment.id}/refunds",
                json=self._payload(amount=5001),
                headers=admin_headers,
            )

        assert response.status_code == 400
        assert "cannot exceed" in response.json()["message"].lower()
        create_refund.assert_not_called()

    def test_non_finance_role_cannot_execute_refund(
        self,
        client,
        client_headers,
        paid_gateway_payment,
    ):
        response = client.post(
            f"{BASE}/admin/finance/client-payments/{paid_gateway_payment.id}/refunds",
            json=self._payload(),
            headers=client_headers,
        )
        assert response.status_code == 403

    def test_pending_refund_is_finalized_by_signed_webhook(
        self,
        client,
        db,
        admin_headers,
        paid_gateway_payment,
        monkeypatch,
    ):
        from app.core import config as config_module

        monkeypatch.setattr(
            config_module.settings,
            "payment_webhook_secret",
            self.WEBHOOK_SECRET,
        )
        pending_gateway_refund = self._gateway_refund(
            paid_gateway_payment,
            id="rfnd_test_pending",
            status="pending",
        )
        with patch(
            "app.api.admin_finance.razorpay_service.create_refund",
            return_value=pending_gateway_refund,
        ):
            response = client.post(
                f"{BASE}/admin/finance/client-payments/{paid_gateway_payment.id}/refunds",
                json=self._payload(idempotency_key="refund-request-pending"),
                headers=admin_headers,
            )
        assert response.status_code == 200, response.json()

        refund_payment = db.get(
            ClientPayment,
            response.json()["data"]["refund_payment_id"],
        )
        assert refund_payment.payment_status == ClientPaymentStatus.PENDING.value

        webhook = _post_razorpay_refund_event(
            client,
            refund_payment,
            paid_gateway_payment,
            gateway_refund_id="rfnd_test_pending",
            gateway_status="processed",
            event="refund.processed",
            secret=self.WEBHOOK_SECRET,
            event_id="evt_refund_processed",
        )
        duplicate = _post_razorpay_refund_event(
            client,
            refund_payment,
            paid_gateway_payment,
            gateway_refund_id="rfnd_test_pending",
            gateway_status="processed",
            event="refund.processed",
            secret=self.WEBHOOK_SECRET,
            event_id="evt_refund_processed_duplicate",
        )

        assert webhook.status_code == 200, webhook.json()
        assert duplicate.status_code == 200, duplicate.json()
        db.refresh(refund_payment)
        assert refund_payment.payment_status == ClientPaymentStatus.PAID.value
        assert refund_payment.gateway_refund_status == "processed"


class TestClientPaymentStatusUpdate:
    def test_admin_marks_payment_paid(
        self, client, db, admin_headers, pending_gateway_payment
    ):
        response = client.patch(
            f"{BASE}/admin/finance/client-payments/{pending_gateway_payment.id}/status",
            json={"payment_status": ClientPaymentStatus.PAID.value},
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["status"] == ClientPaymentStatus.PAID.value

        db.refresh(pending_gateway_payment)
        assert pending_gateway_payment.payment_status == ClientPaymentStatus.PAID.value
        assert pending_gateway_payment.paid_at is not None

    def test_admin_marks_payment_failed(
        self, client, db, admin_headers, pending_gateway_payment
    ):
        response = client.patch(
            f"{BASE}/admin/finance/client-payments/{pending_gateway_payment.id}/status",
            json={"payment_status": ClientPaymentStatus.FAILED.value},
            headers=admin_headers,
        )
        assert response.status_code == 200
        db.refresh(pending_gateway_payment)
        assert pending_gateway_payment.payment_status == ClientPaymentStatus.FAILED.value

    def test_same_status_returns_no_change(
        self, client, admin_headers, pending_gateway_payment
    ):
        response = client.patch(
            f"{BASE}/admin/finance/client-payments/{pending_gateway_payment.id}/status",
            json={"payment_status": ClientPaymentStatus.PENDING.value},
            headers=admin_headers,
        )
        assert response.status_code == 200
        assert "No change" in response.json()["message"]

    def test_payment_not_found_returns_404(
        self, client, admin_headers
    ):
        response = client.patch(
            f"{BASE}/admin/finance/client-payments/999999/status",
            json={"payment_status": ClientPaymentStatus.PAID.value},
            headers=admin_headers,
        )
        assert response.status_code == 404

    def test_non_admin_cannot_update_payment_status(
        self, client, client_headers, client_profile, pending_gateway_payment
    ):
        response = client.patch(
            f"{BASE}/admin/finance/client-payments/{pending_gateway_payment.id}/status",
            json={"payment_status": ClientPaymentStatus.PAID.value},
            headers=client_headers,
        )
        assert response.status_code == 403

    def test_paid_does_not_transition_operational_requirement_state(
        self, client, db, admin_headers, approved_requirement_with_advance_quote, client_profile
    ):
        """Finance confirms the payment; Operations still owns assignment."""
        req = approved_requirement_with_advance_quote
        payment = ClientPayment(
            client_id=client_profile.id,
            requirement_id=req.id,
            amount=5000,
            payment_model=PaymentModel.CLIENT_PAYS_COMPANY.value,
            payment_mode="upi",
            payment_status=ClientPaymentStatus.PENDING.value,
        )
        db.add(payment)
        db.commit()
        db.refresh(payment)

        response = client.patch(
            f"{BASE}/admin/finance/client-payments/{payment.id}/status",
            json={"payment_status": ClientPaymentStatus.PAID.value},
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["requirement_auto_transitioned"] is False
        assert data["new_requirement_status"] is None

        db.refresh(req)
        assert req.status == RequirementStatus.APPROVED.value

    def test_paid_no_auto_transition_when_no_advance_quote(
        self, client, db, admin_headers, approved_requirement, client_profile
    ):
        """Approved requirement with no advance quote stays 'approved' even when payment is paid."""
        payment = ClientPayment(
            client_id=client_profile.id,
            requirement_id=approved_requirement.id,
            amount=5000,
            payment_model=PaymentModel.CLIENT_PAYS_COMPANY.value,
            payment_mode="upi",
            payment_status=ClientPaymentStatus.PENDING.value,
        )
        db.add(payment)
        db.commit()
        db.refresh(payment)

        response = client.patch(
            f"{BASE}/admin/finance/client-payments/{payment.id}/status",
            json={"payment_status": ClientPaymentStatus.PAID.value},
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["requirement_auto_transitioned"] is False

        db.refresh(approved_requirement)
        assert approved_requirement.status == RequirementStatus.APPROVED.value


# ──────────────────────────────────────────────────────────────────
# Worker Payout Flow
# ──────────────────────────────────────────────────────────────────


class TestWorkerPayoutFlow:
    def test_admin_creates_worker_payout(
        self, client, admin_headers, payroll_item
    ):
        response = client.post(
            f"{BASE}/admin/finance/worker-payouts",
            json={
                "payroll_item_id": payroll_item.id,
                "amount": payroll_item.net_amount,
                "payout_mode": "bank_transfer",
                "transaction_reference": "TXN123",
            },
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert "payout_id" in data
        assert data["status"] == WorkerPayoutStatus.PENDING.value

    def test_payout_amount_exceeds_net_rejected(
        self, client, admin_headers, payroll_item
    ):
        response = client.post(
            f"{BASE}/admin/finance/worker-payouts",
            json={
                "payroll_item_id": payroll_item.id,
                "amount": payroll_item.net_amount + 1,
                "payout_mode": "bank_transfer",
            },
            headers=admin_headers,
        )
        assert response.status_code == 400

    def test_payroll_item_not_found_returns_404(
        self, client, admin_headers
    ):
        response = client.post(
            f"{BASE}/admin/finance/worker-payouts",
            json={
                "payroll_item_id": 999999,
                "amount": 1000,
                "payout_mode": "upi",
            },
            headers=admin_headers,
        )
        assert response.status_code == 404

    def test_non_admin_cannot_create_worker_payout(
        self, client, client_headers, client_profile, payroll_item
    ):
        response = client.post(
            f"{BASE}/admin/finance/worker-payouts",
            json={
                "payroll_item_id": payroll_item.id,
                "amount": 1000,
                "payout_mode": "upi",
            },
            headers=client_headers,
        )
        assert response.status_code == 403

    def test_admin_marks_payout_paid_updates_payroll_item(
        self, client, db, admin_headers, payroll_item
    ):
        # First create a payout
        create_resp = client.post(
            f"{BASE}/admin/finance/worker-payouts",
            json={
                "payroll_item_id": payroll_item.id,
                "amount": payroll_item.net_amount,
                "payout_mode": "bank_transfer",
            },
            headers=admin_headers,
        )
        assert create_resp.status_code == 200
        payout_id = create_resp.json()["data"]["payout_id"]

        # Then mark it paid
        update_resp = client.patch(
            f"{BASE}/admin/finance/worker-payouts/{payout_id}/status",
            json={"payout_status": WorkerPayoutStatus.PAID.value},
            headers=admin_headers,
        )
        assert update_resp.status_code == 200
        data = update_resp.json()["data"]
        assert data["status"] == WorkerPayoutStatus.PAID.value

        db.refresh(payroll_item)
        assert payroll_item.payment_status == PayrollItemPaymentStatus.PAID.value

    def test_admin_marks_payout_processing(
        self, client, db, admin_headers, payroll_item
    ):
        create_resp = client.post(
            f"{BASE}/admin/finance/worker-payouts",
            json={
                "payroll_item_id": payroll_item.id,
                "amount": 10000,
                "payout_mode": "upi",
            },
            headers=admin_headers,
        )
        payout_id = create_resp.json()["data"]["payout_id"]

        update_resp = client.patch(
            f"{BASE}/admin/finance/worker-payouts/{payout_id}/status",
            json={"payout_status": WorkerPayoutStatus.PROCESSING.value},
            headers=admin_headers,
        )
        assert update_resp.status_code == 200
        assert update_resp.json()["data"]["status"] == WorkerPayoutStatus.PROCESSING.value

    def test_invalid_payout_status_returns_422(
        self, client, admin_headers, payroll_item
    ):
        # Pydantic validates payout_status before the handler runs → 422
        create_resp = client.post(
            f"{BASE}/admin/finance/worker-payouts",
            json={
                "payroll_item_id": payroll_item.id,
                "amount": 1000,
                "payout_mode": "upi",
            },
            headers=admin_headers,
        )
        payout_id = create_resp.json()["data"]["payout_id"]

        update_resp = client.patch(
            f"{BASE}/admin/finance/worker-payouts/{payout_id}/status",
            json={"payout_status": "not_a_valid_status"},
            headers=admin_headers,
        )
        assert update_resp.status_code == 422

    def test_payout_not_found_returns_404(
        self, client, admin_headers
    ):
        response = client.patch(
            f"{BASE}/admin/finance/worker-payouts/999999/status",
            json={"payout_status": WorkerPayoutStatus.PAID.value},
            headers=admin_headers,
        )
        assert response.status_code == 404


# ──────────────────────────────────────────────────────────────────
# List / Read endpoints (smoke tests)
# ──────────────────────────────────────────────────────────────────


class TestFinanceListEndpoints:
    def test_admin_lists_all_client_payments(
        self, client, admin_headers, pending_gateway_payment
    ):
        response = client.get(
            f"{BASE}/admin/finance/client-payments",
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()["data"]
        # Fix 20: response is now paginated — use data["items"]
        assert "items" in data
        ids = [p["id"] for p in data["items"]]
        assert pending_gateway_payment.id in ids

    def test_admin_filters_client_payments_by_status(
        self, client, admin_headers, pending_gateway_payment, paid_gateway_payment
    ):
        response = client.get(
            f"{BASE}/admin/finance/client-payments?status=pending",
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert all(p["payment_status"] == "pending" for p in data["items"])

    def test_admin_lists_payments_for_requirement(
        self, client, admin_headers, pending_gateway_payment, approved_requirement
    ):
        response = client.get(
            f"{BASE}/admin/finance/client-payments/requirement/{approved_requirement.id}",
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert any(p["id"] == pending_gateway_payment.id for p in data)

    def test_admin_lists_worker_payouts_for_payroll_item(
        self, client, db, admin_headers, payroll_item
    ):
        payout = WorkerPayout(
            payroll_item_id=payroll_item.id,
            worker_profile_id=payroll_item.worker_profile_id,
            amount=payroll_item.net_amount,
            payout_mode="bank_transfer",
            payout_status=WorkerPayoutStatus.PENDING.value,
            paid_by_user_id=None,  # pending payout has no payer yet
        )
        db.add(payout)
        db.commit()

        response = client.get(
            f"{BASE}/admin/finance/worker-payouts/payroll-item/{payroll_item.id}",
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data) >= 1
        assert data[0]["payout_mode"] == "bank_transfer"


# ──────────────────────────────────────────────────────────────────
# Reference Payment Submission (client out-of-app transfer)
# ──────────────────────────────────────────────────────────────────


class TestReferencePaymentSubmission:
    def _payload(self, requirement_id: int, **overrides) -> dict:
        base = {
            "requirement_id": requirement_id,
            "amount": 10000,
            "payment_model": PaymentModel.CLIENT_PAYS_COMPANY.value,
            "payment_mode": "upi",
            "reference_note": "UPI/2026/05/123456",
        }
        base.update(overrides)
        return base

    def test_reference_payment_uses_quote_payment_model(
        self, client, db, client_headers, client_profile, approved_requirement
    ):
        """The approved quote, not the request, determines payment_model."""
        response = client.post(
            f"{BASE}/client/payments/submit-reference",
            json=self._payload(
                approved_requirement.id,
                payment_model=PaymentModel.CLIENT_PAYS_COMPANY.value,
            ),
            headers=client_headers,
        )
        assert response.status_code == 200
        payment_id = response.json()["data"]["payment_id"]

        from app.models.client_payment import ClientPayment as CP
        payment = db.get(CP, payment_id)
        assert payment is not None
        assert payment.payment_model == PaymentModel.CLIENT_PAYS_COMPANY.value

    def test_reference_payment_ignores_tampered_valid_payment_model(
        self, client, db, client_headers, client_profile, approved_requirement
    ):
        """A valid-looking client override cannot change the quote's model."""
        response = client.post(
            f"{BASE}/client/payments/submit-reference",
            json=self._payload(
                approved_requirement.id,
                payment_model=PaymentModel.MIXED.value,
            ),
            headers=client_headers,
        )
        assert response.status_code == 200
        payment_id = response.json()["data"]["payment_id"]

        from app.models.client_payment import ClientPayment as CP
        payment = db.get(CP, payment_id)
        assert payment.payment_model == PaymentModel.CLIENT_PAYS_COMPANY.value
        assert payment.amount == 5000

    def test_reference_payment_invalid_payment_model_returns_422(
        self, client, client_headers, client_profile, approved_requirement
    ):
        response = client.post(
            f"{BASE}/client/payments/submit-reference",
            json=self._payload(approved_requirement.id, payment_model="advance"),
            headers=client_headers,
        )
        assert response.status_code == 422

    def test_reference_payment_missing_payment_model_is_supported(
        self, client, client_headers, client_profile, approved_requirement
    ):
        payload = self._payload(approved_requirement.id)
        del payload["payment_model"]
        response = client.post(
            f"{BASE}/client/payments/submit-reference",
            json=payload,
            headers=client_headers,
        )
        assert response.status_code == 200

    def test_reference_payment_appears_in_list_with_correct_model(
        self, client, client_headers, client_profile, approved_requirement
    ):
        """payment_model is returned in the client's payment list endpoint."""
        client.post(
            f"{BASE}/client/payments/submit-reference",
            json=self._payload(
                approved_requirement.id,
                payment_model=PaymentModel.CLIENT_PAYS_COMPANY.value,
            ),
            headers=client_headers,
        )
        list_resp = client.get(
            f"{BASE}/client/payments/requirement/{approved_requirement.id}",
            headers=client_headers,
        )
        assert list_resp.status_code == 200
        payments = list_resp.json()["data"]
        assert len(payments) >= 1
        assert payments[0]["payment_model"] == PaymentModel.CLIENT_PAYS_COMPANY.value


class TestClientPaymentsListPagination:
    """Fix 20: admin client-payments list must return pagination metadata."""

    def test_list_returns_items_and_pagination_meta(
        self, client, db, admin_headers, client_user
    ):
        """GET /admin/finance/client-payments must return items+pagination when no payments exist."""
        response = client.get(
            f"{BASE}/admin/finance/client-payments",
            headers=admin_headers,
        )

        assert response.status_code == 200
        body = response.json()["data"]
        assert "items" in body, "Response must contain 'items'"
        assert "total" in body, "Response must contain 'total'"
        assert "page" in body, "Response must contain 'page'"
        assert "total_pages" in body, "Response must contain 'total_pages'"

    def test_page_size_param_is_honoured(
        self, client, db, admin_headers, client_user
    ):
        """page_size=1 must return at most 1 item per page."""
        cp = ClientProfile(
            user_id=client_user.id,
            client_type="individual",
            contact_name="Payer",
            city="Chennai",
            state="Tamil Nadu",
            address="Mylapore",
        )
        db.add(cp)
        db.flush()

        req = Requirement(
            client_id=cp.id,
            category="Housekeeping",
            number_of_workers=1,
            work_location="Site",
            city="Chennai",
            state="Tamil Nadu",
            start_date=date.today(),
            duration_days=1,
            status="approved",
            created_by_user_id=client_user.id,
        )
        db.add(req)
        db.flush()

        for _ in range(3):
            payment = ClientPayment(
                client_id=cp.id,
                requirement_id=req.id,
                amount=5000,
                payment_model=PaymentModel.CLIENT_PAYS_COMPANY.value,
                payment_mode="upi",
                payment_status=ClientPaymentStatus.PAID.value,
            )
            db.add(payment)
        db.commit()

        response = client.get(
            f"{BASE}/admin/finance/client-payments",
            params={"page_size": 1},
            headers=admin_headers,
        )

        assert response.status_code == 200
        body = response.json()["data"]
        assert len(body["items"]) == 1
        assert body["total"] >= 3
