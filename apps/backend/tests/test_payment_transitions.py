"""Payment confirmation updates the ledger without changing operational state."""
from datetime import date, timedelta

import pytest

from app.core.payment_constants import ClientPaymentStatus
from app.core.statuses import QuoteStatus, RequirementStatus
from app.models.client_payment import ClientPayment
from app.models.client_profile import ClientProfile
from app.models.quote import Quote
from app.models.requirement import Requirement
from app.services.token_service import build_token_pair

BASE = "/api/v1"


# ─────────────────────────────── fixtures ───────────────────────────────


@pytest.fixture
def client_profile(db, client_user):
    profile = ClientProfile(
        user_id=client_user.id,
        client_type="company",
        company_name="Nandhini Logistics",
        contact_name="Nandhini",
        city="Chennai",
        state="Tamil Nadu",
        address="Anna Salai",
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


@pytest.fixture
def approved_requirement(db, client_profile, client_user):
    req = Requirement(
        client_id=client_profile.id,
        category="Housekeeping",
        number_of_workers=5,
        work_location="Hotel Block B",
        city="Chennai",
        state="Tamil Nadu",
        start_date=date.today() + timedelta(days=3),
        duration_days=10,
        status=RequirementStatus.APPROVED.value,
        created_by_user_id=client_user.id,
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    return req


@pytest.fixture
def requirement_quote(db, approved_requirement, admin_user):
    """Quote with advance_amount=10000 and quoted_amount=50000."""
    q = Quote(
        requirement_id=approved_requirement.id,
        quoted_amount=50000,
        rate_per_worker=1000,
        total_worker_days=50,
        advance_amount=10000,
        payment_model="annai_manages_payroll",
        valid_until=date.today() + timedelta(days=7),
        status=QuoteStatus.APPROVED.value,
        created_by_user_id=admin_user.id,
    )
    db.add(q)
    db.commit()
    db.refresh(q)
    return q


def _make_pending_payment(db, client_profile, requirement, admin_user, amount: int):
    payment = ClientPayment(
        client_id=client_profile.id,
        requirement_id=requirement.id,
        amount=amount,
        payment_model="annai_manages_payroll",
        payment_mode="bank_transfer",
        payment_status=ClientPaymentStatus.PENDING.value,
        recorded_by_user_id=admin_user.id,
        reference_note="UTR12345",
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment


@pytest.fixture
def admin_headers(db, admin_user):
    access_token, _ = build_token_pair(
        db,
        user_id=admin_user.id,
        subject=admin_user.email,
        role=admin_user.role,
    )
    return {"Authorization": f"Bearer {access_token}"}


# ─────────────────────────────── tests ───────────────────────────────────


class TestPaymentStatusTransitionGuards:
    """Finance status changes never bypass operational lifecycle actions."""

    def test_partial_advance_payment_is_confirmed_without_transition(
        self,
        client,
        db,
        admin_headers,
        client_profile,
        approved_requirement,
        requirement_quote,
        admin_user,
    ):
        """Split advances are valid, but do not unlock state automatically."""
        payment = _make_pending_payment(
            db, client_profile, approved_requirement, admin_user, amount=9999
        )

        response = client.patch(
            f"{BASE}/admin/finance/client-payments/{payment.id}/status",
            json={"payment_status": "paid"},
            headers=admin_headers,
        )

        assert response.status_code == 200
        assert response.json()["data"]["requirement_auto_transitioned"] is False

        db.refresh(approved_requirement)
        assert approved_requirement.status == RequirementStatus.APPROVED.value

    def test_exact_advance_does_not_transition_requirement(
        self,
        client,
        db,
        admin_headers,
        client_profile,
        approved_requirement,
        requirement_quote,
        admin_user,
    ):
        """Operations must assign workers after the aggregate advance is met."""
        payment = _make_pending_payment(
            db, client_profile, approved_requirement, admin_user, amount=10000
        )

        response = client.patch(
            f"{BASE}/admin/finance/client-payments/{payment.id}/status",
            json={"payment_status": "paid"},
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["requirement_auto_transitioned"] is False
        assert data["new_requirement_status"] is None

        db.refresh(approved_requirement)
        assert approved_requirement.status == RequirementStatus.APPROVED.value

    def test_payment_above_advance_does_not_transition(
        self,
        client,
        db,
        admin_headers,
        client_profile,
        approved_requirement,
        requirement_quote,
        admin_user,
    ):
        """A confirmed payment never changes the operational state."""
        payment = _make_pending_payment(
            db, client_profile, approved_requirement, admin_user, amount=15000
        )

        response = client.patch(
            f"{BASE}/admin/finance/client-payments/{payment.id}/status",
            json={"payment_status": "paid"},
            headers=admin_headers,
        )

        assert response.status_code == 200
        assert response.json()["data"]["requirement_auto_transitioned"] is False

        db.refresh(approved_requirement)
        assert approved_requirement.status == RequirementStatus.APPROVED.value

    def test_payment_on_non_approved_requirement_does_not_auto_transition(
        self,
        client,
        db,
        admin_headers,
        client_profile,
        admin_user,
        client_user,
    ):
        """A requirement in 'submitted' status must NOT be jumped to workers_assigned."""
        submitted_req = Requirement(
            client_id=client_profile.id,
            category="Security",
            number_of_workers=2,
            work_location="Gate A",
            city="Chennai",
            state="Tamil Nadu",
            start_date=date.today() + timedelta(days=5),
            duration_days=7,
            status=RequirementStatus.SUBMITTED.value,
            created_by_user_id=client_user.id,
        )
        db.add(submitted_req)
        db.flush()
        q = Quote(
            requirement_id=submitted_req.id,
            quoted_amount=20000,
            advance_amount=5000,
            payment_model="annai_manages_payroll",
            status=QuoteStatus.SENT.value,
            created_by_user_id=admin_user.id,
        )
        db.add(q)
        db.commit()

        payment = _make_pending_payment(
            db, client_profile, submitted_req, admin_user, amount=5000
        )

        response = client.patch(
            f"{BASE}/admin/finance/client-payments/{payment.id}/status",
            json={"payment_status": "paid"},
            headers=admin_headers,
        )

        assert response.status_code == 400
        assert "invalid" in response.json()["message"].lower()

        db.refresh(submitted_req)
        assert submitted_req.status == RequirementStatus.SUBMITTED.value

    def test_full_payment_on_in_progress_does_not_complete(
        self,
        client,
        db,
        admin_headers,
        client_profile,
        admin_user,
        client_user,
    ):
        """Operational completion is independent from balance collection."""
        in_progress_req = Requirement(
            client_id=client_profile.id,
            category="Housekeeping",
            number_of_workers=3,
            work_location="Block C",
            city="Chennai",
            state="Tamil Nadu",
            start_date=date.today() - timedelta(days=5),
            duration_days=10,
            status=RequirementStatus.IN_PROGRESS.value,
            created_by_user_id=client_user.id,
        )
        db.add(in_progress_req)
        db.flush()
        q = Quote(
            requirement_id=in_progress_req.id,
            quoted_amount=30000,
            advance_amount=10000,
            payment_model="annai_manages_payroll",
            status=QuoteStatus.APPROVED.value,
            created_by_user_id=admin_user.id,
        )
        db.add(q)
        db.flush()
        # Existing paid advance
        existing_paid = ClientPayment(
            client_id=client_profile.id,
            requirement_id=in_progress_req.id,
            amount=10000,
            payment_model="annai_manages_payroll",
            payment_mode="bank_transfer",
            payment_status=ClientPaymentStatus.PAID.value,
            recorded_by_user_id=admin_user.id,
        )
        db.add(existing_paid)
        db.commit()

        # Final balance payment
        balance_payment = _make_pending_payment(
            db, client_profile, in_progress_req, admin_user, amount=20000
        )

        response = client.patch(
            f"{BASE}/admin/finance/client-payments/{balance_payment.id}/status",
            json={"payment_status": "paid"},
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["requirement_auto_transitioned"] is False
        assert data["new_requirement_status"] is None

        db.refresh(in_progress_req)
        assert in_progress_req.status == RequirementStatus.IN_PROGRESS.value

    def test_partial_final_payment_does_not_complete_requirement(
        self,
        client,
        db,
        admin_headers,
        client_profile,
        admin_user,
        client_user,
    ):
        """Paying only part of the balance must NOT mark completed."""
        in_progress_req = Requirement(
            client_id=client_profile.id,
            category="Driver",
            number_of_workers=1,
            work_location="HQ",
            city="Chennai",
            state="Tamil Nadu",
            start_date=date.today() - timedelta(days=2),
            duration_days=5,
            status=RequirementStatus.IN_PROGRESS.value,
            created_by_user_id=client_user.id,
        )
        db.add(in_progress_req)
        db.flush()
        q = Quote(
            requirement_id=in_progress_req.id,
            quoted_amount=10000,
            advance_amount=3000,
            payment_model="annai_manages_payroll",
            status=QuoteStatus.APPROVED.value,
            created_by_user_id=admin_user.id,
        )
        db.add(q)
        db.flush()
        existing_paid = ClientPayment(
            client_id=client_profile.id,
            requirement_id=in_progress_req.id,
            amount=3000,
            payment_model="annai_manages_payroll",
            payment_mode="bank_transfer",
            payment_status=ClientPaymentStatus.PAID.value,
            recorded_by_user_id=admin_user.id,
        )
        db.add(existing_paid)
        db.commit()

        # Only Rs. 2000 of remaining Rs. 7000 balance
        partial = _make_pending_payment(
            db, client_profile, in_progress_req, admin_user, amount=2000
        )

        response = client.patch(
            f"{BASE}/admin/finance/client-payments/{partial.id}/status",
            json={"payment_status": "paid"},
            headers=admin_headers,
        )

        assert response.status_code == 200
        assert response.json()["data"]["requirement_auto_transitioned"] is False

        db.refresh(in_progress_req)
        assert in_progress_req.status == RequirementStatus.IN_PROGRESS.value

    def test_marking_payment_failed_never_transitions_requirement(
        self,
        client,
        db,
        admin_headers,
        client_profile,
        approved_requirement,
        requirement_quote,
        admin_user,
    ):
        """A failed payment must never change requirement status."""
        payment = _make_pending_payment(
            db, client_profile, approved_requirement, admin_user, amount=15000
        )

        response = client.patch(
            f"{BASE}/admin/finance/client-payments/{payment.id}/status",
            json={"payment_status": "failed"},
            headers=admin_headers,
        )

        assert response.status_code == 200
        assert response.json()["data"]["requirement_auto_transitioned"] is False

        db.refresh(approved_requirement)
        assert approved_requirement.status == RequirementStatus.APPROVED.value
