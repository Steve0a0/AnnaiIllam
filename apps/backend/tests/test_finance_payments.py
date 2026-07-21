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
from unittest.mock import patch

import pytest

from app.core.assignment_constants import AssignmentStatus
from app.core.payment_constants import ClientPaymentStatus, PaymentModel, WorkerPayoutStatus
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


# ──────────────────────────────────────────────────────────────────
# Manual Payment Recording
# ──────────────────────────────────────────────────────────────────


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
