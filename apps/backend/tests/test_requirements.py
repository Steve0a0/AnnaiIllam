"""Integration coverage for client requirements and admin quote flow."""
from datetime import date, timedelta
from unittest.mock import patch

import pytest

from app.core.statuses import QuoteStatus, RequirementStatus
from app.models.client_profile import ClientProfile
from app.models.user import User
from app.models.worker_interest import WorkerInterest
from app.models.worker_profile import WorkerProfile
from app.services.token_service import build_token_pair

BASE = "/api/v1"


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
        gst_number="33ABCDE1234F1Z5",
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


@pytest.fixture
def other_client_user(db):
    user = User(
        phone="9000000044",
        email="other-client@annai-illam.test",
        role="client",
        is_active=True,
        is_phone_verified=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    profile = ClientProfile(
        user_id=user.id,
        client_type="company",
        company_name="Kaveri Logistics",
        contact_name="Meena Iyer",
        city="Coimbatore",
        state="Tamil Nadu",
    )
    db.add(profile)
    db.commit()
    return user


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
def other_client_headers(db, other_client_user):
    access_token, _ = build_token_pair(
        db,
        user_id=other_client_user.id,
        subject=other_client_user.phone,
        role=other_client_user.role,
    )
    return {"Authorization": f"Bearer {access_token}"}


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
def worker_headers(db, worker_user):
    access_token, _ = build_token_pair(
        db,
        user_id=worker_user.id,
        subject=worker_user.phone,
        role=worker_user.role,
    )
    return {"Authorization": f"Bearer {access_token}"}


def requirement_payload(**overrides):
    payload = {
        "category": "Security",
        "subcategory": "Night Guard",
        "number_of_workers": 3,
        "work_location": "Warehouse Gate 1",
        "city": "Chennai",
        "state": "Tamil Nadu",
        "start_date": str(date.today() + timedelta(days=7)),
        "duration_days": 10,
        "shift_details": "20:00-06:00",
        "food_required": True,
        "accommodation_required": False,
        "budget_amount": 45000,
        "notes": "Bring ID proof at reporting time.",
        "site_latitude": 13.0827,
        "site_longitude": 80.2707,
        "geofence_radius_meters": 500,
    }
    payload.update(overrides)
    return payload


def quote_payload(requirement_id: int, **overrides):
    payload = {
        "requirement_id": requirement_id,
        "quoted_amount": 39000,
        "rate_per_worker": 1300,
        "total_worker_days": 30,
        "advance_amount": 10000,
        "payment_model": "advance",
        "valid_until": str(date.today() + timedelta(days=14)),
        "terms_notes": "Advance required before assignment.",
        "internal_notes": "Preferred client.",
    }
    payload.update(overrides)
    return payload


def create_requirement(client, headers, **overrides):
    response = client.post(
        f"{BASE}/client/requirements",
        json=requirement_payload(**overrides),
        headers=headers,
    )
    assert response.status_code == 200
    return response.json()["data"]["id"]


def mark_under_review(client, requirement_id: int, headers):
    response = client.post(
        f"{BASE}/admin/requirements/{requirement_id}/mark-review",
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["data"]["status"] == RequirementStatus.UNDER_REVIEW.value


def create_quote(client, requirement_id: int, headers):
    response = client.post(
        f"{BASE}/admin/requirements/{requirement_id}/quote",
        json=quote_payload(requirement_id),
        headers=headers,
    )
    assert response.status_code == 200
    return response.json()["data"]


class TestClientRequirementCreation:
    def test_client_can_create_list_and_view_own_requirement(
        self,
        client,
        client_headers,
        client_profile,
    ):
        requirement_id = create_requirement(client, client_headers)

        detail = client.get(
            f"{BASE}/client/requirements/{requirement_id}",
            headers=client_headers,
        )
        assert detail.status_code == 200
        detail_data = detail.json()["data"]
        assert detail_data["id"] == requirement_id
        assert detail_data["category"] == "Security"
        assert detail_data["status"] == RequirementStatus.SUBMITTED.value
        assert detail_data["quote"] is None

        listing = client.get(f"{BASE}/client/requirements", headers=client_headers)
        assert listing.status_code == 200
        # Fix 19: response is now paginated — use data["items"]
        rows = listing.json()["data"]["items"]
        assert len(rows) == 1
        assert rows[0]["id"] == requirement_id
        assert rows[0]["status"] == RequirementStatus.SUBMITTED.value

    def test_create_requirement_requires_client_profile(self, client, client_headers):
        response = client.post(
            f"{BASE}/client/requirements",
            json=requirement_payload(),
            headers=client_headers,
        )
        assert response.status_code == 400
        assert "Client profile not found" in response.json()["message"]

    def test_create_requirement_requires_client_role(self, client, worker_headers):
        response = client.post(
            f"{BASE}/client/requirements",
            json=requirement_payload(),
            headers=worker_headers,
        )
        assert response.status_code == 403

    def test_other_client_cannot_view_requirement(
        self,
        client,
        client_headers,
        client_profile,
        other_client_headers,
    ):
        requirement_id = create_requirement(client, client_headers)

        response = client.get(
            f"{BASE}/client/requirements/{requirement_id}",
            headers=other_client_headers,
        )
        assert response.status_code == 404


class TestAdminRequirementReview:
    def test_admin_can_list_filter_view_and_mark_requirement_under_review(
        self,
        client,
        client_headers,
        client_profile,
        admin_headers,
    ):
        requirement_id = create_requirement(client, client_headers)

        listing = client.get(f"{BASE}/admin/requirements", headers=admin_headers)
        assert listing.status_code == 200
        assert listing.json()["data"]["total"] == 1

        filtered = client.get(
            f"{BASE}/admin/requirements",
            params={"status": RequirementStatus.SUBMITTED.value},
            headers=admin_headers,
        )
        assert filtered.status_code == 200
        assert filtered.json()["data"]["items"][0]["id"] == requirement_id

        detail = client.get(
            f"{BASE}/admin/requirements/{requirement_id}",
            headers=admin_headers,
        )
        assert detail.status_code == 200
        assert detail.json()["data"]["status"] == RequirementStatus.SUBMITTED.value

        mark_under_review(client, requirement_id, admin_headers)

        updated = client.get(
            f"{BASE}/admin/requirements/{requirement_id}",
            headers=admin_headers,
        )
        assert updated.json()["data"]["status"] == RequirementStatus.UNDER_REVIEW.value

    def test_mark_review_rejects_wrong_status(
        self,
        client,
        client_headers,
        client_profile,
        admin_headers,
    ):
        requirement_id = create_requirement(client, client_headers)
        mark_under_review(client, requirement_id, admin_headers)

        response = client.post(
            f"{BASE}/admin/requirements/{requirement_id}/mark-review",
            headers=admin_headers,
        )
        assert response.status_code == 400
        assert "cannot transition" in response.json()["message"].lower()

    def test_admin_requirement_endpoints_require_admin_role(
        self,
        client,
        client_headers,
        client_profile,
    ):
        requirement_id = create_requirement(client, client_headers)

        response = client.post(
            f"{BASE}/admin/requirements/{requirement_id}/mark-review",
            headers=client_headers,
        )
        assert response.status_code == 403


class TestQuoteFlow:
    def test_admin_creates_quote_and_client_approves_it(
        self,
        client,
        client_headers,
        client_profile,
        admin_headers,
    ):
        requirement_id = create_requirement(client, client_headers)
        mark_under_review(client, requirement_id, admin_headers)

        quote_data = create_quote(client, requirement_id, admin_headers)
        assert quote_data["quote_status"] == QuoteStatus.SENT.value
        assert quote_data["requirement_status"] == RequirementStatus.QUOTED.value

        client_detail = client.get(
            f"{BASE}/client/requirements/{requirement_id}",
            headers=client_headers,
        )
        quote = client_detail.json()["data"]["quote"]
        assert quote["quoted_amount"] == 39000
        assert quote["status"] == QuoteStatus.SENT.value

        decision = client.post(
            f"{BASE}/client/requirements/{requirement_id}/quote-decision",
            json={"action": "approve"},
            headers=client_headers,
        )
        assert decision.status_code == 200
        decision_data = decision.json()["data"]
        assert decision_data["requirement_status"] == RequirementStatus.APPROVED.value
        assert decision_data["quote_status"] == QuoteStatus.APPROVED.value

    def test_client_can_reject_quote_and_requirement_reverts_to_under_review(
        self,
        client,
        client_headers,
        client_profile,
        admin_headers,
    ):
        requirement_id = create_requirement(client, client_headers)
        mark_under_review(client, requirement_id, admin_headers)
        create_quote(client, requirement_id, admin_headers)

        decision = client.post(
            f"{BASE}/client/requirements/{requirement_id}/quote-decision",
            json={"action": "reject"},
            headers=client_headers,
        )
        assert decision.status_code == 200
        assert decision.json()["data"]["requirement_status"] == RequirementStatus.UNDER_REVIEW.value
        assert decision.json()["data"]["quote_status"] == QuoteStatus.REJECTED.value

    def test_admin_can_create_new_quote_after_client_rejection(
        self,
        client,
        client_headers,
        client_profile,
        admin_headers,
    ):
        requirement_id = create_requirement(client, client_headers)
        mark_under_review(client, requirement_id, admin_headers)
        create_quote(client, requirement_id, admin_headers)

        client.post(
            f"{BASE}/client/requirements/{requirement_id}/quote-decision",
            json={"action": "reject"},
            headers=client_headers,
        )

        # Requirement is now under_review — admin can send a revised quote
        second_quote_resp = client.post(
            f"{BASE}/admin/requirements/{requirement_id}/quote",
            json=quote_payload(requirement_id, quoted_amount=36000),
            headers=admin_headers,
        )
        assert second_quote_resp.status_code == 200
        assert second_quote_resp.json()["data"]["requirement_status"] == RequirementStatus.QUOTED.value

    def test_quote_rejection_emits_quote_rejected_by_client_audit_event(
        self,
        client,
        client_headers,
        client_profile,
        admin_headers,
    ):
        requirement_id = create_requirement(client, client_headers)
        mark_under_review(client, requirement_id, admin_headers)
        create_quote(client, requirement_id, admin_headers)

        with patch("app.api.client_requirements.audit_event") as mock_audit:
            decision = client.post(
                f"{BASE}/client/requirements/{requirement_id}/quote-decision",
                json={"action": "reject"},
                headers=client_headers,
            )
        assert decision.status_code == 200

        rejection_call = next(
            (c for c in mock_audit.call_args_list if c.args[0] == "quote_rejected_by_client"),
            None,
        )
        assert rejection_call is not None
        details = rejection_call.args[1]
        assert details["requirement_id"] == requirement_id
        assert details["requirement_reverted_to"] == RequirementStatus.UNDER_REVIEW.value

    def test_quote_approval_still_moves_requirement_to_approved(
        self,
        client,
        client_headers,
        client_profile,
        admin_headers,
    ):
        requirement_id = create_requirement(client, client_headers)
        mark_under_review(client, requirement_id, admin_headers)
        create_quote(client, requirement_id, admin_headers)

        decision = client.post(
            f"{BASE}/client/requirements/{requirement_id}/quote-decision",
            json={"action": "approve"},
            headers=client_headers,
        )
        assert decision.status_code == 200
        assert decision.json()["data"]["requirement_status"] == RequirementStatus.APPROVED.value
        assert decision.json()["data"]["quote_status"] == QuoteStatus.APPROVED.value

    def test_quote_creation_requires_under_review_status(
        self,
        client,
        client_headers,
        client_profile,
        admin_headers,
    ):
        requirement_id = create_requirement(client, client_headers)

        response = client.post(
            f"{BASE}/admin/requirements/{requirement_id}/quote",
            json=quote_payload(requirement_id),
            headers=admin_headers,
        )
        assert response.status_code == 400
        assert "cannot transition" in response.json()["message"].lower()

    def test_quote_creation_rejects_requirement_id_mismatch(
        self,
        client,
        client_headers,
        client_profile,
        admin_headers,
    ):
        requirement_id = create_requirement(client, client_headers)
        mark_under_review(client, requirement_id, admin_headers)

        response = client.post(
            f"{BASE}/admin/requirements/{requirement_id}/quote",
            json=quote_payload(requirement_id + 1),
            headers=admin_headers,
        )
        assert response.status_code == 400
        assert "mismatch" in response.json()["message"].lower()

    def test_duplicate_quote_is_rejected(
        self,
        client,
        client_headers,
        client_profile,
        admin_headers,
    ):
        requirement_id = create_requirement(client, client_headers)
        mark_under_review(client, requirement_id, admin_headers)
        create_quote(client, requirement_id, admin_headers)

        response = client.post(
            f"{BASE}/admin/requirements/{requirement_id}/quote",
            json=quote_payload(requirement_id),
            headers=admin_headers,
        )
        assert response.status_code == 400
        assert "already exists" in response.json()["message"]

    def test_quote_decision_requires_own_client_requirement(
        self,
        client,
        client_headers,
        client_profile,
        other_client_headers,
        admin_headers,
    ):
        requirement_id = create_requirement(client, client_headers)
        mark_under_review(client, requirement_id, admin_headers)
        create_quote(client, requirement_id, admin_headers)

        response = client.post(
            f"{BASE}/client/requirements/{requirement_id}/quote-decision",
            json={"action": "approve"},
            headers=other_client_headers,
        )
        assert response.status_code == 404

    def test_quote_decision_is_single_use(
        self,
        client,
        client_headers,
        client_profile,
        admin_headers,
    ):
        requirement_id = create_requirement(client, client_headers)
        mark_under_review(client, requirement_id, admin_headers)
        create_quote(client, requirement_id, admin_headers)

        first = client.post(
            f"{BASE}/client/requirements/{requirement_id}/quote-decision",
            json={"action": "approve"},
            headers=client_headers,
        )
        assert first.status_code == 200

        second = client.post(
            f"{BASE}/client/requirements/{requirement_id}/quote-decision",
            json={"action": "approve"},
            headers=client_headers,
        )
        assert second.status_code == 400
        assert "not in decision state" in second.json()["message"]

    def test_quote_decision_requires_existing_quote(
        self,
        client,
        client_headers,
        client_profile,
    ):
        requirement_id = create_requirement(client, client_headers)

        response = client.post(
            f"{BASE}/client/requirements/{requirement_id}/quote-decision",
            json={"action": "approve"},
            headers=client_headers,
        )
        assert response.status_code == 400
        assert "Quote not found" in response.json()["message"]

    def test_invalid_quote_decision_action_is_rejected(
        self,
        client,
        client_headers,
        client_profile,
    ):
        requirement_id = create_requirement(client, client_headers)

        response = client.post(
            f"{BASE}/client/requirements/{requirement_id}/quote-decision",
            json={"action": "maybe"},
            headers=client_headers,
        )
        assert response.status_code == 422


class TestRequirementCompletion:
    def _force_status(self, db, requirement_id: int, status: str):
        """Directly set requirement status to bypass the full flow."""
        from app.models.requirement import Requirement

        req = db.get(Requirement, requirement_id)
        req.status = status
        db.commit()

    def test_complete_in_progress_requirement(
        self,
        client,
        db,
        client_headers,
        client_profile,
        admin_headers,
    ):
        requirement_id = create_requirement(client, client_headers)
        self._force_status(db, requirement_id, RequirementStatus.IN_PROGRESS.value)

        response = client.post(
            f"{BASE}/admin/requirements/{requirement_id}/complete",
            headers=admin_headers,
        )
        assert response.status_code == 200
        assert response.json()["data"]["id"] == requirement_id
        assert response.json()["data"]["status"] == RequirementStatus.COMPLETED.value

    def test_complete_rejects_wrong_status(
        self,
        client,
        client_headers,
        client_profile,
        admin_headers,
    ):
        requirement_id = create_requirement(client, client_headers)

        response = client.post(
            f"{BASE}/admin/requirements/{requirement_id}/complete",
            headers=admin_headers,
        )
        assert response.status_code == 400
        assert "cannot transition" in response.json()["message"].lower()

    def test_complete_returns_404_for_unknown_requirement(
        self,
        client,
        admin_headers,
    ):
        response = client.post(
            f"{BASE}/admin/requirements/999999/complete",
            headers=admin_headers,
        )
        assert response.status_code == 404

    def test_complete_requires_admin_role(
        self,
        client,
        client_headers,
        client_profile,
    ):
        requirement_id = create_requirement(client, client_headers)

        response = client.post(
            f"{BASE}/admin/requirements/{requirement_id}/complete",
            headers=client_headers,
        )
        assert response.status_code == 403


# ──────────────────────────────────────────────────────────────────
# Interested workers endpoint
# ──────────────────────────────────────────────────────────────────


class TestRequirementInterests:
    """Tests for GET /admin/requirements/{id}/interests."""

    def _make_worker(self, db, phone: str, full_name: str, category: str, city: str) -> tuple:
        """Create a worker user + profile and return (user, profile)."""
        user = User(
            phone=phone,
            role="worker",
            is_active=True,
            is_phone_verified=True,
        )
        db.add(user)
        db.flush()
        profile = WorkerProfile(
            user_id=user.id,
            full_name=full_name,
            category=category,
            city=city,
            state="Tamil Nadu",
            is_available=True,
            verification_status="verified",
        )
        db.add(profile)
        db.flush()
        return user, profile

    def _make_interest(
        self, db, worker_profile_id: int, requirement_id: int, status: str = "interested"
    ) -> WorkerInterest:
        interest = WorkerInterest(
            worker_profile_id=worker_profile_id,
            requirement_id=requirement_id,
            status=status,
        )
        db.add(interest)
        db.flush()
        return interest

    # ── happy-path tests ────────────────────────────────────────────

    def test_requirement_with_no_interests_returns_empty(
        self, client, db, client_profile, admin_headers, client_headers
    ):
        requirement_id = create_requirement(client, client_headers)
        resp = client.get(
            f"{BASE}/admin/requirements/{requirement_id}/interests",
            headers=admin_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["data"] == []

    def test_requirement_with_interested_worker_returns_record(
        self, client, db, client_profile, admin_headers, client_headers
    ):
        requirement_id = create_requirement(client, client_headers)
        _, wp = self._make_worker(db, "9111111101", "Suresh Kumar", "Security", "Chennai")
        self._make_interest(db, wp.id, requirement_id, status="interested")
        db.commit()

        resp = client.get(
            f"{BASE}/admin/requirements/{requirement_id}/interests",
            headers=admin_headers,
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data) == 1
        row = data[0]
        assert row["worker_profile_id"] == wp.id
        assert row["full_name"] == "Suresh Kumar"
        assert row["city"] == "Chennai"
        assert row["category"] == "Security"
        assert row["status"] == "interested"
        assert "expressed_at" in row

    def test_multiple_interests_are_all_returned(
        self, client, db, client_profile, admin_headers, client_headers
    ):
        requirement_id = create_requirement(client, client_headers)
        _, wp1 = self._make_worker(db, "9111111102", "Ravi Mohan", "Security", "Chennai")
        _, wp2 = self._make_worker(db, "9111111103", "Anitha Devi", "Housekeeping", "Chennai")
        self._make_interest(db, wp1.id, requirement_id)
        self._make_interest(db, wp2.id, requirement_id)
        db.commit()

        resp = client.get(
            f"{BASE}/admin/requirements/{requirement_id}/interests",
            headers=admin_headers,
        )
        assert resp.status_code == 200
        assert len(resp.json()["data"]) == 2

    def test_withdrawn_interest_is_still_returned_with_correct_status(
        self, client, db, client_profile, admin_headers, client_headers
    ):
        """Withdrawn interests should appear so admin sees the full picture."""
        requirement_id = create_requirement(client, client_headers)
        _, wp = self._make_worker(db, "9111111104", "Muthu Raj", "Driving", "Madurai")
        self._make_interest(db, wp.id, requirement_id, status="withdrawn")
        db.commit()

        resp = client.get(
            f"{BASE}/admin/requirements/{requirement_id}/interests",
            headers=admin_headers,
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data) == 1
        assert data[0]["status"] == "withdrawn"

    def test_worker_name_and_status_are_present_in_each_row(
        self, client, db, client_profile, admin_headers, client_headers
    ):
        requirement_id = create_requirement(client, client_headers)
        _, wp = self._make_worker(db, "9111111105", "Kavitha Nair", "Security", "Coimbatore")
        self._make_interest(db, wp.id, requirement_id)
        db.commit()

        resp = client.get(
            f"{BASE}/admin/requirements/{requirement_id}/interests",
            headers=admin_headers,
        )
        row = resp.json()["data"][0]
        assert row["full_name"] == "Kavitha Nair"
        assert row["status"] in {"interested", "withdrawn"}
        assert row["verification_status"] == "verified"
        assert row["is_available"] is True

    def test_optional_subcategory_may_be_none(
        self, client, db, client_profile, admin_headers, client_headers
    ):
        """Workers without a subcategory must not cause a crash."""
        requirement_id = create_requirement(client, client_headers)
        user = User(phone="9111111106", role="worker", is_active=True, is_phone_verified=True)
        db.add(user)
        db.flush()
        wp = WorkerProfile(
            user_id=user.id,
            full_name="No Subcategory Worker",
            category="Security",
            subcategory=None,   # explicitly None
            city="Chennai",
            state="Tamil Nadu",
            is_available=True,
            verification_status="pending",
        )
        db.add(wp)
        db.flush()
        self._make_interest(db, wp.id, requirement_id)
        db.commit()

        resp = client.get(
            f"{BASE}/admin/requirements/{requirement_id}/interests",
            headers=admin_headers,
        )
        assert resp.status_code == 200
        row = resp.json()["data"][0]
        assert row["subcategory"] is None
        assert row["full_name"] == "No Subcategory Worker"

    # ── access control tests ────────────────────────────────────────

    def test_non_admin_cannot_access_interests_endpoint(
        self, client, client_profile, client_headers
    ):
        requirement_id = create_requirement(client, client_headers)
        resp = client.get(
            f"{BASE}/admin/requirements/{requirement_id}/interests",
            headers=client_headers,
        )
        assert resp.status_code == 403

    def test_unauthenticated_request_is_rejected(self, client, db, client_profile, client_headers):
        requirement_id = create_requirement(client, client_headers)
        resp = client.get(
            f"{BASE}/admin/requirements/{requirement_id}/interests",
        )
        assert resp.status_code == 401

    def test_unknown_requirement_returns_404(self, client, admin_headers):
        resp = client.get(
            f"{BASE}/admin/requirements/999999/interests",
            headers=admin_headers,
        )
        assert resp.status_code == 404


# ──────────────────────────────────────────────────────────────────
# Fix 7 — salary_amount must not appear in client requirement detail
# ──────────────────────────────────────────────────────────────────


class TestClientRequirementDetailSalaryLeakage:
    """GET /client/requirements/{id} must not expose worker salary to the client."""

    def test_salary_amount_absent_from_client_requirement_detail(
        self,
        client,
        db,
        client_headers,
        admin_headers,
        client_profile,
        client_user,
    ):
        from datetime import date, timedelta
        from app.core.assignment_constants import AssignmentStatus
        from app.models.assignment import Assignment
        from app.models.requirement import Requirement
        from app.models.worker_profile import WorkerProfile
        from app.models.user import User

        # Create a requirement in workers_assigned state
        req = Requirement(
            client_id=client_profile.id,
            category="Security",
            number_of_workers=1,
            work_location="Gate A",
            city="Chennai",
            state="Tamil Nadu",
            start_date=date.today() + timedelta(days=3),
            duration_days=5,
            status=RequirementStatus.WORKERS_ASSIGNED.value,
            created_by_user_id=client_user.id,
        )
        db.add(req)
        db.flush()

        # Create a worker user + profile
        worker_user = User(
            phone="9111000099",
            role="worker",
            is_active=True,
            is_phone_verified=True,
        )
        db.add(worker_user)
        db.flush()
        worker_profile = WorkerProfile(
            user_id=worker_user.id,
            full_name="Salary Test Worker",
            category="Security",
            city="Chennai",
            state="Tamil Nadu",
            is_available=True,
            verification_status="approved",
        )
        db.add(worker_profile)
        db.flush()

        # Create an admin user reference
        from app.models.user import User as UserModel
        admin_q = db.query(UserModel).filter(UserModel.role == "admin").first()

        assignment = Assignment(
            requirement_id=req.id,
            worker_profile_id=worker_profile.id,
            assigned_by_user_id=admin_q.id,
            status=AssignmentStatus.ACCEPTED.value,
            assigned_role="Guard",
            assigned_shift="Day",
            salary_amount=12500,
        )
        db.add(assignment)
        db.commit()

        response = client.get(
            f"{BASE}/client/requirements/{req.id}",
            headers=client_headers,
        )

        assert response.status_code == 200
        assignments = response.json()["data"]["assignments"]
        assert len(assignments) >= 1
        for a in assignments:
            assert "salary_amount" not in a, (
                f"salary_amount must not be visible to clients; found {a.get('salary_amount')}"
            )


class TestClientRequirementListPagination:
    """Fix 19: client requirement list endpoint must return pagination metadata."""

    @pytest.fixture
    def client_profile_fx(self, db, client_user):
        from app.models.client_profile import ClientProfile
        profile = ClientProfile(
            user_id=client_user.id,
            client_type="individual",
            contact_name="Test Client",
            city="Chennai",
            state="Tamil Nadu",
            address="Anna Nagar",
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)
        return profile

    @pytest.fixture
    def client_headers_fx(self, db, client_user):
        from app.services.token_service import build_token_pair
        access_token, _ = build_token_pair(
            db,
            user_id=client_user.id,
            subject=client_user.phone,
            role=client_user.role,
        )
        return {"Authorization": f"Bearer {access_token}"}

    def test_list_returns_items_and_pagination_meta(
        self, client, db, client_user, client_profile_fx, client_headers_fx
    ):
        """GET /client/requirements must return items array plus page/total metadata."""
        from app.models.requirement import Requirement
        from app.core.statuses import RequirementStatus

        for i in range(3):
            req = Requirement(
                client_id=client_profile_fx.id,
                category="Security",
                number_of_workers=1,
                work_location=f"Site {i}",
                city="Chennai",
                state="Tamil Nadu",
                start_date=__import__("datetime").date.today(),
                duration_days=1,
                status=RequirementStatus.SUBMITTED.value,
                created_by_user_id=client_user.id,
            )
            db.add(req)
        db.commit()

        response = client.get(f"{BASE}/client/requirements", headers=client_headers_fx)

        assert response.status_code == 200
        body = response.json()["data"]
        assert "items" in body, "Response must contain 'items'"
        assert "total" in body, "Response must contain 'total'"
        assert "page" in body, "Response must contain 'page'"
        assert "total_pages" in body, "Response must contain 'total_pages'"
        assert body["total"] >= 3

    def test_page_size_limits_results(
        self, client, db, client_user, client_profile_fx, client_headers_fx
    ):
        """page_size=1 must return exactly one item per page."""
        from app.models.requirement import Requirement
        from app.core.statuses import RequirementStatus

        for i in range(3):
            req = Requirement(
                client_id=client_profile_fx.id,
                category="Security",
                number_of_workers=1,
                work_location=f"Site {i}",
                city="Chennai",
                state="Tamil Nadu",
                start_date=__import__("datetime").date.today(),
                duration_days=1,
                status=RequirementStatus.SUBMITTED.value,
                created_by_user_id=client_user.id,
            )
            db.add(req)
        db.commit()

        response = client.get(
            f"{BASE}/client/requirements",
            params={"page_size": 1},
            headers=client_headers_fx,
        )

        assert response.status_code == 200
        body = response.json()["data"]
        assert len(body["items"]) == 1
        assert body["total_pages"] >= 3


class TestRequirementCancellationFlow:
    """Feature 1: requirement cancellation by admin and client."""

    @pytest.fixture
    def cancel_client_profile(self, db, client_user):
        from app.models.client_profile import ClientProfile
        profile = ClientProfile(
            user_id=client_user.id,
            client_type="individual",
            contact_name="Cancel Test Client",
            city="Chennai",
            state="Tamil Nadu",
            address="Anna Nagar",
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)
        return profile

    @pytest.fixture
    def cancel_client_headers(self, db, client_user):
        from app.services.token_service import build_token_pair
        access_token, _ = build_token_pair(
            db, user_id=client_user.id, subject=client_user.phone, role=client_user.role,
        )
        return {"Authorization": f"Bearer {access_token}"}

    @pytest.fixture
    def cancel_admin_headers(self, db, admin_user):
        from app.services.token_service import build_token_pair
        access_token, _ = build_token_pair(
            db, user_id=admin_user.id, subject=admin_user.email, role=admin_user.role,
        )
        return {"Authorization": f"Bearer {access_token}"}

    def _make_requirement(self, db, client_profile, client_user, status="submitted"):
        import datetime
        from app.models.requirement import Requirement
        req = Requirement(
            client_id=client_profile.id,
            category="Security",
            number_of_workers=2,
            work_location="Test Site",
            city="Chennai",
            state="Tamil Nadu",
            start_date=datetime.date.today(),
            duration_days=5,
            status=status,
            created_by_user_id=client_user.id,
        )
        db.add(req)
        db.commit()
        db.refresh(req)
        return req

    def test_admin_can_cancel_submitted_requirement(
        self, client, db, admin_user, client_user, cancel_client_profile, cancel_admin_headers
    ):
        """Admin can cancel a requirement from 'submitted' with a reason."""
        req = self._make_requirement(db, cancel_client_profile, client_user, status="submitted")

        response = client.post(
            f"{BASE}/admin/requirements/{req.id}/cancel",
            json={"reason": "Client withdrew the project after discussion."},
            headers=cancel_admin_headers,
        )

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["status"] == "cancelled"
        assert "withdrew" in data["cancellation_reason"]

    def test_admin_cancel_sets_active_assignments_cancelled_and_frees_workers(
        self, client, db, admin_user, client_user, cancel_client_profile, cancel_admin_headers
    ):
        """Cancelling a requirement must set active assignments to cancelled and restore is_available."""
        import datetime
        from app.models.assignment import Assignment
        from app.models.worker_profile import WorkerProfile
        from app.models.user import User as UserModel

        req = self._make_requirement(db, cancel_client_profile, client_user, status="approved")

        worker_u = UserModel(phone="9876500099", role="worker", is_active=True, is_phone_verified=True)
        db.add(worker_u)
        db.flush()
        wp = WorkerProfile(
            user_id=worker_u.id, full_name="Cancel Worker", city="Chennai",
            state="Tamil Nadu", category="Security", is_available=False,
        )
        db.add(wp)
        db.flush()

        assignment = Assignment(
            requirement_id=req.id,
            worker_profile_id=wp.id,
            assigned_by_user_id=admin_user.id,
            status="assigned",
            assigned_at=datetime.datetime.utcnow(),
        )
        db.add(assignment)
        db.commit()

        response = client.post(
            f"{BASE}/admin/requirements/{req.id}/cancel",
            json={"reason": "Project scope changed completely by client."},
            headers=cancel_admin_headers,
        )

        assert response.status_code == 200
        db.refresh(assignment)
        db.refresh(wp)
        assert assignment.status == "cancelled"
        assert wp.is_available is True

    def test_admin_cancel_rejected_for_completed_requirement(
        self, client, db, admin_user, client_user, cancel_client_profile, cancel_admin_headers
    ):
        """Admin cannot cancel a requirement that is already completed."""
        req = self._make_requirement(db, cancel_client_profile, client_user, status="completed")

        response = client.post(
            f"{BASE}/admin/requirements/{req.id}/cancel",
            json={"reason": "Trying to cancel completed requirement."},
            headers=cancel_admin_headers,
        )

        assert response.status_code == 400

    def test_client_can_cancel_own_submitted_requirement(
        self, client, db, client_user, cancel_client_profile, cancel_client_headers
    ):
        """Client can cancel their own requirement while it is in 'submitted' status."""
        req = self._make_requirement(db, cancel_client_profile, client_user, status="submitted")

        response = client.post(
            f"{BASE}/client/requirements/{req.id}/cancel",
            json={"reason": "We no longer need this service at this time."},
            headers=cancel_client_headers,
        )

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["status"] == "cancelled"
        assert data["cancellation_reason"] is not None

    def test_client_cannot_cancel_approved_requirement(
        self, client, db, client_user, cancel_client_profile, cancel_client_headers
    ):
        """Client cannot cancel a requirement once it is in 'approved' status."""
        req = self._make_requirement(db, cancel_client_profile, client_user, status="approved")

        response = client.post(
            f"{BASE}/client/requirements/{req.id}/cancel",
            json={"reason": "Trying to cancel after approval is not allowed."},
            headers=cancel_client_headers,
        )

        assert response.status_code == 400


class TestQuoteExpiryAutoEnforcement:
    """Feature 2: quote expiry auto-enforcement."""

    @pytest.fixture
    def exp_client_profile(self, db, client_user):
        from app.models.client_profile import ClientProfile
        profile = ClientProfile(
            user_id=client_user.id,
            client_type="individual",
            contact_name="Expiry Test Client",
            city="Chennai",
            state="Tamil Nadu",
            address="Mylapore",
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)
        return profile

    @pytest.fixture
    def exp_client_headers(self, db, client_user):
        from app.services.token_service import build_token_pair
        access_token, _ = build_token_pair(
            db, user_id=client_user.id, subject=client_user.phone, role=client_user.role,
        )
        return {"Authorization": f"Bearer {access_token}"}

    @pytest.fixture
    def exp_admin_headers(self, db, admin_user):
        from app.services.token_service import build_token_pair
        access_token, _ = build_token_pair(
            db, user_id=admin_user.id, subject=admin_user.email, role=admin_user.role,
        )
        return {"Authorization": f"Bearer {access_token}"}

    def _make_quoted_requirement(self, db, client_profile, client_user, admin_user, valid_until):
        """Create a requirement in 'quoted' status with a sent quote."""
        import datetime
        from app.models.quote import Quote
        from app.models.requirement import Requirement

        req = Requirement(
            client_id=client_profile.id,
            category="Housekeeping",
            number_of_workers=2,
            work_location="Test Facility",
            city="Chennai",
            state="Tamil Nadu",
            start_date=datetime.date.today() + datetime.timedelta(days=10),
            duration_days=5,
            status="quoted",
            created_by_user_id=client_user.id,
        )
        db.add(req)
        db.flush()

        quote = Quote(
            requirement_id=req.id,
            quoted_amount=50000,
            payment_model="platform_collects",
            status="sent",
            valid_until=valid_until,
            created_by_user_id=admin_user.id,
        )
        db.add(quote)
        db.commit()
        db.refresh(req)
        db.refresh(quote)
        return req, quote

    def test_expire_stale_quotes_expires_overdue_quote(
        self, db, client_user, exp_client_profile, admin_user
    ):
        """expire_stale_quotes sets quote.status='expired' and requirement.status='under_review'."""
        import datetime
        from app.core.scheduler import expire_stale_quotes

        yesterday = datetime.date.today() - datetime.timedelta(days=1)
        req, quote = self._make_quoted_requirement(
            db, exp_client_profile, client_user, admin_user, valid_until=yesterday
        )

        result = expire_stale_quotes(db)

        db.refresh(quote)
        db.refresh(req)
        assert result["expired_quotes"] >= 1
        assert quote.status == "expired"
        assert req.status == "under_review"

    def test_client_cannot_approve_expired_quote(
        self, client, db, client_user, exp_client_profile, exp_client_headers, admin_user
    ):
        """Client gets 400 with a clear expiry message when approving a past-due quote."""
        import datetime

        yesterday = datetime.date.today() - datetime.timedelta(days=1)
        req, _ = self._make_quoted_requirement(
            db, exp_client_profile, client_user, admin_user, valid_until=yesterday
        )

        response = client.post(
            f"{BASE}/client/requirements/{req.id}/quote-decision",
            json={"action": "approve"},
            headers=exp_client_headers,
        )

        assert response.status_code == 400
        assert "expired" in response.json()["message"].lower()

    def test_expire_stale_quotes_skips_future_quote(
        self, db, client_user, exp_client_profile, admin_user
    ):
        """expire_stale_quotes does NOT expire a quote whose valid_until is tomorrow."""
        import datetime
        from app.core.scheduler import expire_stale_quotes

        tomorrow = datetime.date.today() + datetime.timedelta(days=1)
        req, quote = self._make_quoted_requirement(
            db, exp_client_profile, client_user, admin_user, valid_until=tomorrow
        )

        expire_stale_quotes(db)

        db.refresh(quote)
        db.refresh(req)
        assert quote.status == "sent"
        assert req.status == "quoted"

    def test_admin_can_requote_after_expiry(
        self, client, db, admin_user, client_user, exp_client_profile, exp_admin_headers
    ):
        """After quote expiry, admin can create a fresh quote (re-quote path unblocked)."""
        import datetime
        from app.core.scheduler import expire_stale_quotes

        yesterday = datetime.date.today() - datetime.timedelta(days=1)
        req, _ = self._make_quoted_requirement(
            db, exp_client_profile, client_user, admin_user, valid_until=yesterday
        )

        expire_stale_quotes(db)
        db.refresh(req)
        assert req.status == "under_review"

        response = client.post(
            f"{BASE}/admin/requirements/{req.id}/quote",
            json={
                "requirement_id": req.id,
                "quoted_amount": 55000,
                "payment_model": "platform_collects",
                "valid_until": str(datetime.date.today() + datetime.timedelta(days=7)),
            },
            headers=exp_admin_headers,
        )

        assert response.status_code == 200
        assert response.json()["data"]["quote_status"] == "sent"
