"""Integration coverage for admin and worker assignment flows."""
from datetime import date, timedelta
from unittest.mock import patch

import pytest

from app.core.assignment_constants import AssignmentStatus
from app.core.payment_constants import ClientPaymentStatus, PaymentModel
from app.core.statuses import RequirementStatus
from app.models.client_payment import ClientPayment
from app.models.client_profile import ClientProfile
from app.models.quote import Quote
from app.models.requirement import Requirement
from app.models.user import User
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
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


@pytest.fixture
def approved_requirement(db, client_profile, client_user, admin_user):
    requirement = Requirement(
        client_id=client_profile.id,
        category="Security",
        subcategory="Night Guard",
        number_of_workers=2,
        work_location="Warehouse Gate 1",
        city="Chennai",
        state="Tamil Nadu",
        start_date=date.today() + timedelta(days=10),
        duration_days=5,
        shift_details="Night 20:00-06:00",
        food_required=True,
        accommodation_required=False,
        budget_amount=30000,
        notes="Report to the security supervisor.",
        status=RequirementStatus.APPROVED.value,
        created_by_user_id=client_user.id,
    )
    db.add(requirement)
    db.commit()
    db.refresh(requirement)
    db.add(
        Quote(
            requirement_id=requirement.id,
            quoted_amount=30000,
            advance_amount=5000,
            payment_model=PaymentModel.CLIENT_PAYS_COMPANY.value,
            status="approved",
            created_by_user_id=admin_user.id,
        )
    )
    db.commit()
    return requirement


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
        skills="Security,Night Guard",
        experience_years="2-4 years",
        available_days=None,
        available_shifts="Night",
        is_available=True,
        verification_status="approved",
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


@pytest.fixture
def unavailable_worker_profile(db):
    user = User(
        phone="9000000055",
        email="unavailable-worker@annai-illam.test",
        role="worker",
        is_active=True,
        is_phone_verified=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    profile = WorkerProfile(
        user_id=user.id,
        full_name="Suresh Mani",
        category="Security",
        city="Chennai",
        state="Tamil Nadu",
        is_available=False,
        verification_status="approved",
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


@pytest.fixture
def other_worker_user(db):
    user = User(
        phone="9000000066",
        email="other-worker@annai-illam.test",
        role="worker",
        is_active=True,
        is_phone_verified=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def other_worker_profile(db, other_worker_user):
    profile = WorkerProfile(
        user_id=other_worker_user.id,
        full_name="Karthik Raj",
        category="Security",
        city="Chennai",
        state="Tamil Nadu",
        is_available=True,
        verification_status="approved",
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


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
def other_worker_headers(db, other_worker_user):
    access_token, _ = build_token_pair(
        db,
        user_id=other_worker_user.id,
        subject=other_worker_user.phone,
        role=other_worker_user.role,
    )
    return {"Authorization": f"Bearer {access_token}"}


def assignment_payload(requirement_id: int, worker_profile_id: int, **overrides):
    payload = {
        "requirement_id": requirement_id,
        "worker_profile_id": worker_profile_id,
        "assigned_role": "Night Security Guard",
        "assigned_shift": "Night 20:00-06:00",
        "salary_amount": 1250,
        "notes": "Bring uniform and ID card.",
    }
    payload.update(overrides)
    return payload


def create_assignment(client, requirement_id: int, worker_profile_id: int, admin_headers):
    response = client.post(
        f"{BASE}/admin/assignments",
        params={"skip_payment_check": "true", "skip_reason": "test payment override"},
        json=assignment_payload(requirement_id, worker_profile_id),
        headers=admin_headers,
    )
    assert response.status_code == 200
    return response.json()["data"]["assignment_id"]


class TestAdminAssignmentFlow:
    def test_admin_can_create_list_filter_and_read_requirement_assignments(
        self,
        client,
        admin_headers,
        approved_requirement,
        worker_profile,
    ):
        assignment_id = create_assignment(
            client,
            approved_requirement.id,
            worker_profile.id,
            admin_headers,
        )

        all_assignments = client.get(f"{BASE}/admin/assignments", headers=admin_headers)
        assert all_assignments.status_code == 200
        all_data = all_assignments.json()["data"]
        assert all_data["total"] == 1
        assert all_data["items"][0]["id"] == assignment_id
        assert all_data["items"][0]["status"] == AssignmentStatus.ASSIGNED.value
        assert all_data["items"][0]["worker_name"] == "Ravi Kumar"

        filtered = client.get(
            f"{BASE}/admin/assignments",
            params={
                "requirement_id": approved_requirement.id,
                "status": AssignmentStatus.ASSIGNED.value,
            },
            headers=admin_headers,
        )
        assert filtered.status_code == 200
        assert filtered.json()["data"]["items"][0]["id"] == assignment_id

        requirement_assignments = client.get(
            f"{BASE}/admin/assignments/requirement/{approved_requirement.id}",
            headers=admin_headers,
        )
        assert requirement_assignments.status_code == 200
        rows = requirement_assignments.json()["data"]
        assert len(rows) == 1
        assert rows[0]["id"] == assignment_id
        assert rows[0]["worker_profile_id"] == worker_profile.id
        assert rows[0]["assigned_shift"] == "Night 20:00-06:00"

    @pytest.mark.parametrize(
        "status",
        [
            # Valid transitions from the initial "assigned" state.
            # "assigned→active" and "assigned→completed" are intentionally excluded:
            # those skip intermediate states and are now rejected by ASSIGNMENT_TRANSITIONS.
            # See TestAssignmentStatusTransitionGuard for the full transition matrix tests.
            AssignmentStatus.ACCEPTED.value,
            AssignmentStatus.DECLINED.value,
            AssignmentStatus.CANCELLED.value,
            AssignmentStatus.REPLACED.value,
        ],
    )
    def test_admin_can_update_assignment_to_each_supported_status(
        self,
        client,
        admin_headers,
        approved_requirement,
        worker_profile,
        status,
    ):
        assignment_id = create_assignment(
            client,
            approved_requirement.id,
            worker_profile.id,
            admin_headers,
        )

        response = client.patch(
            f"{BASE}/admin/assignments/{assignment_id}/status",
            json={"status": status},
            headers=admin_headers,
        )
        assert response.status_code == 200
        assert response.json()["data"]["status"] == status

    def test_assignment_creation_sets_requirement_assigned(
        self,
        client,
        db,
        admin_headers,
        approved_requirement,
        worker_profile,
    ):
        create_assignment(client, approved_requirement.id, worker_profile.id, admin_headers)

        db.refresh(approved_requirement)
        assert approved_requirement.status == RequirementStatus.WORKERS_ASSIGNED.value

    def test_assignment_create_requires_approved_requirement(
        self,
        client,
        db,
        admin_headers,
        approved_requirement,
        worker_profile,
    ):
        approved_requirement.status = RequirementStatus.SUBMITTED.value
        db.commit()

        response = client.post(
            f"{BASE}/admin/assignments",
            params={"skip_payment_check": "true", "skip_reason": "test payment override"},
            json=assignment_payload(approved_requirement.id, worker_profile.id),
            headers=admin_headers,
        )
        assert response.status_code == 400
        assert "approved" in response.json()["message"].lower()

    def test_assignment_create_enforces_payment_gate_without_override(
        self,
        client,
        admin_headers,
        approved_requirement,
        worker_profile,
    ):
        response = client.post(
            f"{BASE}/admin/assignments",
            json=assignment_payload(approved_requirement.id, worker_profile.id),
            headers=admin_headers,
        )
        assert response.status_code == 400
        assert "confirmed advance" in response.json()["message"].lower()

    def test_assignment_create_requires_available_approved_worker(
        self,
        client,
        admin_headers,
        approved_requirement,
        unavailable_worker_profile,
    ):
        response = client.post(
            f"{BASE}/admin/assignments",
            params={"skip_payment_check": "true", "skip_reason": "test payment override"},
            json=assignment_payload(approved_requirement.id, unavailable_worker_profile.id),
            headers=admin_headers,
        )
        assert response.status_code == 400
        assert "not available" in response.json()["message"].lower()

    def test_duplicate_active_assignment_is_rejected(
        self,
        client,
        admin_headers,
        approved_requirement,
        worker_profile,
    ):
        create_assignment(client, approved_requirement.id, worker_profile.id, admin_headers)

        response = client.post(
            f"{BASE}/admin/assignments",
            params={"skip_payment_check": "true", "skip_reason": "test payment override"},
            json=assignment_payload(approved_requirement.id, worker_profile.id),
            headers=admin_headers,
        )
        # After Fix 16, worker.is_available=False after first assignment so the
        # "not available" guard fires before "already assigned" — both are 400 rejections.
        assert response.status_code == 400

    def test_admin_assignment_routes_require_admin_role(
        self,
        client,
        client_headers,
        approved_requirement,
        worker_profile,
    ):
        response = client.post(
            f"{BASE}/admin/assignments",
            params={"skip_payment_check": "true", "skip_reason": "test payment override"},
            json=assignment_payload(approved_requirement.id, worker_profile.id),
            headers=client_headers,
        )
        assert response.status_code == 403

    def test_invalid_admin_status_update_is_rejected(
        self,
        client,
        admin_headers,
        approved_requirement,
        worker_profile,
    ):
        assignment_id = create_assignment(
            client,
            approved_requirement.id,
            worker_profile.id,
            admin_headers,
        )

        response = client.patch(
            f"{BASE}/admin/assignments/{assignment_id}/status",
            json={"status": "unknown"},
            headers=admin_headers,
        )
        assert response.status_code == 422


class TestWorkerAssignmentFlow:
    def test_worker_can_list_and_acknowledge_own_assignment(
        self,
        client,
        admin_headers,
        worker_headers,
        approved_requirement,
        worker_profile,
    ):
        assignment_id = create_assignment(
            client,
            approved_requirement.id,
            worker_profile.id,
            admin_headers,
        )

        listing = client.get(f"{BASE}/worker/assignments", headers=worker_headers)
        assert listing.status_code == 200
        rows = listing.json()["data"]
        assert len(rows) == 1
        assert rows[0]["assignment_id"] == assignment_id
        assert rows[0]["status"] == AssignmentStatus.ASSIGNED.value
        assert rows[0]["requirement"]["id"] == approved_requirement.id

        acknowledge = client.post(
            f"{BASE}/worker/assignments/{assignment_id}/acknowledge",
            headers=worker_headers,
        )
        assert acknowledge.status_code == 200
        assert acknowledge.json()["data"]["status"] == AssignmentStatus.ACCEPTED.value

    def test_worker_can_decline_own_assignment_and_reopen_requirement(
        self,
        client,
        db,
        admin_headers,
        worker_headers,
        approved_requirement,
        worker_profile,
    ):
        assignment_id = create_assignment(
            client,
            approved_requirement.id,
            worker_profile.id,
            admin_headers,
        )

        decline = client.post(
            f"{BASE}/worker/assignments/{assignment_id}/decline",
            headers=worker_headers,
        )
        assert decline.status_code == 200
        assert decline.json()["data"]["status"] == AssignmentStatus.DECLINED.value

        db.refresh(approved_requirement)
        assert approved_requirement.status == RequirementStatus.APPROVED.value

    def test_worker_cannot_acknowledge_or_decline_after_state_change(
        self,
        client,
        admin_headers,
        worker_headers,
        approved_requirement,
        worker_profile,
    ):
        assignment_id = create_assignment(
            client,
            approved_requirement.id,
            worker_profile.id,
            admin_headers,
        )

        first = client.post(
            f"{BASE}/worker/assignments/{assignment_id}/acknowledge",
            headers=worker_headers,
        )
        assert first.status_code == 200

        second = client.post(
            f"{BASE}/worker/assignments/{assignment_id}/decline",
            headers=worker_headers,
        )
        assert second.status_code == 400
        assert "Only assigned jobs" in second.json()["message"]

    def test_worker_cannot_act_on_another_workers_assignment(
        self,
        client,
        admin_headers,
        other_worker_headers,
        approved_requirement,
        worker_profile,
        other_worker_profile,
    ):
        assignment_id = create_assignment(
            client,
            approved_requirement.id,
            worker_profile.id,
            admin_headers,
        )

        listing = client.get(f"{BASE}/worker/assignments", headers=other_worker_headers)
        assert listing.status_code == 200
        assert listing.json()["data"] == []

        response = client.post(
            f"{BASE}/worker/assignments/{assignment_id}/acknowledge",
            headers=other_worker_headers,
        )
        assert response.status_code == 404

    def test_worker_assignment_routes_require_worker_role(
        self,
        client,
        admin_headers,
        approved_requirement,
        worker_profile,
    ):
        assignment_id = create_assignment(
            client,
            approved_requirement.id,
            worker_profile.id,
            admin_headers,
        )

        response = client.post(
            f"{BASE}/worker/assignments/{assignment_id}/acknowledge",
            headers=admin_headers,
        )
        assert response.status_code == 403


@pytest.fixture
def single_worker_requirement(db, client_profile, client_user):
    requirement = Requirement(
        client_id=client_profile.id,
        category="Security",
        subcategory="Night Guard",
        number_of_workers=1,
        work_location="Warehouse Gate 2",
        city="Chennai",
        state="Tamil Nadu",
        start_date=date.today() + timedelta(days=10),
        duration_days=5,
        shift_details="Night 20:00-06:00",
        food_required=False,
        accommodation_required=False,
        budget_amount=15000,
        status=RequirementStatus.APPROVED.value,
        created_by_user_id=client_user.id,
    )
    db.add(requirement)
    db.commit()
    db.refresh(requirement)
    return requirement


class TestWorkerCapacityEnforcement:
    def test_cannot_exceed_number_of_workers(
        self,
        client,
        admin_headers,
        single_worker_requirement,
        worker_profile,
        other_worker_profile,
    ):
        # Fill the one slot
        create_assignment(
            client,
            single_worker_requirement.id,
            worker_profile.id,
            admin_headers,
        )

        # Second assignment should be rejected
        response = client.post(
            f"{BASE}/admin/assignments",
            params={"skip_payment_check": "true", "skip_reason": "test payment override"},
            json=assignment_payload(single_worker_requirement.id, other_worker_profile.id),
            headers=admin_headers,
        )
        assert response.status_code == 400
        assert "full capacity" in response.json()["message"].lower()
        assert "1/1" in response.json()["message"]

    def test_declined_assignment_does_not_count_toward_capacity(
        self,
        client,
        db,
        admin_headers,
        single_worker_requirement,
        worker_profile,
        other_worker_profile,
    ):

        # Assign first worker
        assignment_id = create_assignment(
            client,
            single_worker_requirement.id,
            worker_profile.id,
            admin_headers,
        )

        # Admin declines that assignment
        client.patch(
            f"{BASE}/admin/assignments/{assignment_id}/status",
            json={"status": "declined"},
            headers=admin_headers,
        )

        # Slot is now free — second worker should succeed
        response = client.post(
            f"{BASE}/admin/assignments",
            params={"skip_payment_check": "true", "skip_reason": "test payment override"},
            json=assignment_payload(single_worker_requirement.id, other_worker_profile.id),
            headers=admin_headers,
        )
        assert response.status_code == 200

    def test_capacity_error_shows_correct_counts(
        self,
        client,
        db,
        admin_headers,
        approved_requirement,
        worker_profile,
        other_worker_profile,
    ):
        # Fill both slots on a 2-worker requirement
        create_assignment(
            client,
            approved_requirement.id,
            worker_profile.id,
            admin_headers,
        )
        create_assignment(
            client,
            approved_requirement.id,
            other_worker_profile.id,
            admin_headers,
        )

        # Create a third worker directly via DB
        third_user = User(
            phone="9000000077",
            email="third-worker@annai-illam.test",
            role="worker",
            is_active=True,
            is_phone_verified=True,
        )
        db.add(third_user)
        db.commit()
        db.refresh(third_user)

        from app.models.worker_profile import WorkerProfile
        third_profile = WorkerProfile(
            user_id=third_user.id,
            full_name="Murugan S",
            category="Security",
            city="Chennai",
            state="Tamil Nadu",
            is_available=True,
            verification_status="approved",
        )
        db.add(third_profile)
        db.commit()
        db.refresh(third_profile)

        response = client.post(
            f"{BASE}/admin/assignments",
            params={"skip_payment_check": "true", "skip_reason": "test payment override"},
            json=assignment_payload(approved_requirement.id, third_profile.id),
            headers=admin_headers,
        )
        assert response.status_code == 400
        assert "2/2" in response.json()["message"]


class TestPaymentGateBypass:
    def test_skip_without_reason_is_rejected(
        self,
        client,
        admin_headers,
        approved_requirement,
        worker_profile,
    ):
        response = client.post(
            f"{BASE}/admin/assignments",
            params={"skip_payment_check": "true"},
            json=assignment_payload(approved_requirement.id, worker_profile.id),
            headers=admin_headers,
        )
        assert response.status_code == 400
        assert "skip_reason is required" in response.json()["message"].lower()

    def test_skip_with_blank_reason_is_rejected(
        self,
        client,
        admin_headers,
        approved_requirement,
        worker_profile,
    ):
        response = client.post(
            f"{BASE}/admin/assignments",
            params={"skip_payment_check": "true", "skip_reason": "   "},
            json=assignment_payload(approved_requirement.id, worker_profile.id),
            headers=admin_headers,
        )
        assert response.status_code == 400
        assert "skip_reason is required" in response.json()["message"].lower()

    def test_skip_with_valid_reason_proceeds(
        self,
        client,
        admin_headers,
        approved_requirement,
        worker_profile,
    ):
        response = client.post(
            f"{BASE}/admin/assignments",
            params={"skip_payment_check": "true", "skip_reason": "Client confirmed offline bank transfer"},
            json=assignment_payload(approved_requirement.id, worker_profile.id),
            headers=admin_headers,
        )
        assert response.status_code == 200

    def test_skip_not_triggered_without_flag(
        self,
        client,
        admin_headers,
        approved_requirement,
        worker_profile,
    ):
        # No skip_payment_check — should fail on the payment gate, not the reason gate
        response = client.post(
            f"{BASE}/admin/assignments",
            json=assignment_payload(approved_requirement.id, worker_profile.id),
            headers=admin_headers,
        )
        assert response.status_code == 400
        assert "confirmed advance" in response.json()["message"].lower()


class TestPaymentGateBypassAudit:
    def test_bypass_creates_audit_event_with_full_metadata(
        self,
        client,
        admin_user,
        admin_headers,
        approved_requirement,
        worker_profile,
    ):
        """Successful bypass calls audit_event with full metadata including assignment_id."""
        with patch("app.api.admin_assignments.audit_event") as mock_audit:
            response = client.post(
                f"{BASE}/admin/assignments",
                params={"skip_payment_check": "true", "skip_reason": "Client confirmed offline bank transfer"},
                json=assignment_payload(approved_requirement.id, worker_profile.id),
                headers=admin_headers,
            )
        assert response.status_code == 200
        assignment_id = response.json()["data"]["assignment_id"]

        bypass_call = next(
            (c for c in mock_audit.call_args_list if c.args[0] == "payment_gate_bypassed"),
            None,
        )
        assert bypass_call is not None
        details = bypass_call.args[1]
        assert details["assignment_id"] == assignment_id
        assert details["requirement_id"] == approved_requirement.id
        assert details["skip_reason"] == "Client confirmed offline bank transfer"
        assert bypass_call.kwargs.get("actor_user_id") == admin_user.id

    def test_bypass_audit_assignment_id_is_a_positive_integer(
        self,
        client,
        admin_headers,
        approved_requirement,
        worker_profile,
    ):
        """assignment_id passed to audit_event must be a positive integer."""
        with patch("app.api.admin_assignments.audit_event") as mock_audit:
            response = client.post(
                f"{BASE}/admin/assignments",
                params={"skip_payment_check": "true", "skip_reason": "Urgent placement"},
                json=assignment_payload(approved_requirement.id, worker_profile.id),
                headers=admin_headers,
            )
        assert response.status_code == 200

        bypass_call = next(
            (c for c in mock_audit.call_args_list if c.args[0] == "payment_gate_bypassed"),
            None,
        )
        assert bypass_call is not None
        assignment_id = bypass_call.args[1]["assignment_id"]
        assert isinstance(assignment_id, int)
        assert assignment_id > 0

    def test_normal_assignment_with_confirmed_payment_creates_no_bypass_audit(
        self,
        client,
        db,
        admin_headers,
        client_profile,
        approved_requirement,
        worker_profile,
    ):
        """Assignment through the normal payment gate must NOT call audit_event for bypass."""
        payment = ClientPayment(
            requirement_id=approved_requirement.id,
            client_id=client_profile.id,
            amount=30000,
            payment_model=PaymentModel.CLIENT_PAYS_COMPANY.value,
            payment_mode="gateway",
            payment_status=ClientPaymentStatus.PAID.value,
        )
        db.add(payment)
        db.commit()

        with patch("app.api.admin_assignments.audit_event") as mock_audit:
            response = client.post(
                f"{BASE}/admin/assignments",
                json=assignment_payload(approved_requirement.id, worker_profile.id),
                headers=admin_headers,
            )
        assert response.status_code == 200

        bypass_called = any(
            c.args[0] == "payment_gate_bypassed" for c in mock_audit.call_args_list
        )
        assert not bypass_called

    def test_bypass_without_reason_returns_400_and_no_bypass_audit(
        self,
        client,
        admin_headers,
        approved_requirement,
        worker_profile,
    ):
        """Missing skip_reason returns 400 and must not call audit_event for bypass."""
        with patch("app.api.admin_assignments.audit_event") as mock_audit:
            response = client.post(
                f"{BASE}/admin/assignments",
                params={"skip_payment_check": "true"},
                json=assignment_payload(approved_requirement.id, worker_profile.id),
                headers=admin_headers,
            )
        assert response.status_code == 400
        assert "skip_reason" in response.json()["message"].lower()

        bypass_called = any(
            c.args[0] == "payment_gate_bypassed" for c in mock_audit.call_args_list
        )
        assert not bypass_called


class TestWorkerDocumentExpiryWarnings:
    """P2-6: Document expiry soft warning during worker matching and assignment."""

    def test_worker_with_future_expiry_has_no_warning_in_matches(
        self,
        client,
        db,
        admin_headers,
        approved_requirement,
        worker_profile,
    ):
        from app.models.worker_document import WorkerDocument

        doc = WorkerDocument(
            worker_profile_id=worker_profile.id,
            document_type="govt_id",
            file_url="https://example.com/doc.jpg",
            verification_status="approved",
            expiry_date=date.today() + timedelta(days=180),
        )
        db.add(doc)
        db.commit()

        response = client.get(
            f"{BASE}/admin/assignments/requirement/{approved_requirement.id}/matches",
            headers=admin_headers,
        )
        assert response.status_code == 200
        matches = response.json()["data"]
        this_worker = next((m for m in matches if m["worker_profile_id"] == worker_profile.id), None)
        assert this_worker is not None
        assert "document_expired" not in this_worker["reasons"]
        assert this_worker["expired_documents"] == []

    def test_worker_with_expired_doc_has_warning_in_matches(
        self,
        client,
        db,
        admin_headers,
        approved_requirement,
        worker_profile,
    ):
        from app.models.worker_document import WorkerDocument

        doc = WorkerDocument(
            worker_profile_id=worker_profile.id,
            document_type="govt_id",
            file_url="https://example.com/doc.jpg",
            verification_status="approved",
            expiry_date=date.today() - timedelta(days=30),
        )
        db.add(doc)
        db.commit()

        response = client.get(
            f"{BASE}/admin/assignments/requirement/{approved_requirement.id}/matches",
            headers=admin_headers,
        )
        assert response.status_code == 200
        matches = response.json()["data"]
        this_worker = next((m for m in matches if m["worker_profile_id"] == worker_profile.id), None)
        assert this_worker is not None
        assert "document_expired" in this_worker["reasons"]
        assert len(this_worker["expired_documents"]) == 1
        assert this_worker["expired_documents"][0]["document_type"] == "govt_id"

    def test_worker_with_no_expiry_date_has_no_warning_in_matches(
        self,
        client,
        db,
        admin_headers,
        approved_requirement,
        worker_profile,
    ):
        from app.models.worker_document import WorkerDocument

        doc = WorkerDocument(
            worker_profile_id=worker_profile.id,
            document_type="govt_id",
            file_url="https://example.com/doc.jpg",
            verification_status="approved",
            expiry_date=None,
        )
        db.add(doc)
        db.commit()

        response = client.get(
            f"{BASE}/admin/assignments/requirement/{approved_requirement.id}/matches",
            headers=admin_headers,
        )
        assert response.status_code == 200
        matches = response.json()["data"]
        this_worker = next((m for m in matches if m["worker_profile_id"] == worker_profile.id), None)
        assert this_worker is not None
        assert "document_expired" not in this_worker["reasons"]
        assert this_worker["expired_documents"] == []

    def test_assignment_succeeds_with_expired_doc_and_warning_returned(
        self,
        client,
        db,
        admin_headers,
        approved_requirement,
        worker_profile,
    ):
        from app.models.worker_document import WorkerDocument

        doc = WorkerDocument(
            worker_profile_id=worker_profile.id,
            document_type="selfie",
            file_url="https://example.com/selfie.jpg",
            verification_status="approved",
            expiry_date=date.today() - timedelta(days=10),
        )
        db.add(doc)
        db.commit()

        response = client.post(
            f"{BASE}/admin/assignments",
            params={"skip_payment_check": "true", "skip_reason": "test doc expiry"},
            json=assignment_payload(approved_requirement.id, worker_profile.id),
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert "assignment_id" in data
        assert data["warning"] is not None
        assert data["warning"]["code"] == "document_expired"
        assert "selfie" in data["warning"]["message"]
        assert len(data["warning"]["documents"]) == 1

    def test_rejected_expired_doc_does_not_trigger_warning(
        self,
        client,
        db,
        admin_headers,
        approved_requirement,
        worker_profile,
    ):
        from app.models.worker_document import WorkerDocument

        doc = WorkerDocument(
            worker_profile_id=worker_profile.id,
            document_type="govt_id",
            file_url="https://example.com/doc.jpg",
            verification_status="rejected",
            expiry_date=date.today() - timedelta(days=60),
        )
        db.add(doc)
        db.commit()

        response = client.get(
            f"{BASE}/admin/assignments/requirement/{approved_requirement.id}/matches",
            headers=admin_headers,
        )
        assert response.status_code == 200
        matches = response.json()["data"]
        this_worker = next((m for m in matches if m["worker_profile_id"] == worker_profile.id), None)
        assert this_worker is not None
        assert "document_expired" not in this_worker["reasons"]
        assert this_worker["expired_documents"] == []

    def test_multiple_expired_docs_all_appear_in_warning(
        self,
        client,
        db,
        admin_headers,
        approved_requirement,
        worker_profile,
    ):
        from app.models.worker_document import WorkerDocument

        for doc_type in ("govt_id", "selfie"):
            db.add(WorkerDocument(
                worker_profile_id=worker_profile.id,
                document_type=doc_type,
                file_url=f"https://example.com/{doc_type}.jpg",
                verification_status="approved",
                expiry_date=date.today() - timedelta(days=5),
            ))
        db.commit()

        response = client.post(
            f"{BASE}/admin/assignments",
            params={"skip_payment_check": "true", "skip_reason": "test multiple expired"},
            json=assignment_payload(approved_requirement.id, worker_profile.id),
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["warning"] is not None
        assert data["warning"]["code"] == "document_expired"
        assert len(data["warning"]["documents"]) == 2
        doc_types = {d["document_type"] for d in data["warning"]["documents"]}
        assert doc_types == {"govt_id", "selfie"}

    def test_no_warning_when_worker_has_no_documents(
        self,
        client,
        admin_headers,
        approved_requirement,
        worker_profile,
    ):
        """Worker with no documents at all — assignment succeeds, warning is None."""
        response = client.post(
            f"{BASE}/admin/assignments",
            params={"skip_payment_check": "true", "skip_reason": "test no docs"},
            json=assignment_payload(approved_requirement.id, worker_profile.id),
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["warning"] is None


# ──────────────────────────────────────────────────────────────────
# Fix 6 — Worker decline must use validate_requirement_transition
# ──────────────────────────────────────────────────────────────────


class TestWorkerDeclineStateMachineGuard:
    """decline_assignment must not revert requirement to 'approved' from invalid states."""

    def _make_assignment(self, db, requirement, worker_profile, admin_user,
                         status=AssignmentStatus.ASSIGNED.value):
        from app.models.assignment import Assignment
        item = Assignment(
            requirement_id=requirement.id,
            worker_profile_id=worker_profile.id,
            assigned_by_user_id=admin_user.id,
            status=status,
            assigned_role="Guard",
            assigned_shift="Day",
            salary_amount=1000,
        )
        db.add(item)
        db.commit()
        db.refresh(item)
        return item

    def test_decline_on_in_progress_requirement_returns_400(
        self,
        client,
        db,
        worker_headers,
        worker_profile,
        admin_user,
        client_profile,
        client_user,
    ):
        """Last worker declining on an in_progress requirement must raise 400.
        in_progress → approved is not a valid state-machine transition."""
        in_progress_req = Requirement(
            client_id=client_profile.id,
            category="Security",
            number_of_workers=1,
            work_location="Gate A",
            city="Chennai",
            state="Tamil Nadu",
            start_date=date.today(),
            duration_days=5,
            status=RequirementStatus.IN_PROGRESS.value,
            created_by_user_id=client_user.id,
        )
        db.add(in_progress_req)
        db.commit()
        db.refresh(in_progress_req)

        assignment = self._make_assignment(db, in_progress_req, worker_profile, admin_user)

        response = client.post(
            f"{BASE}/worker/assignments/{assignment.id}/decline",
            headers=worker_headers,
        )

        assert response.status_code == 400
        db.refresh(in_progress_req)
        assert in_progress_req.status == RequirementStatus.IN_PROGRESS.value

    def test_last_worker_decline_on_workers_assigned_reverts_to_approved(
        self,
        client,
        db,
        worker_headers,
        worker_profile,
        admin_user,
        approved_requirement,
    ):
        """Happy path: last worker declines on workers_assigned → requirement reverts to approved."""
        # Move requirement to workers_assigned first
        approved_requirement.status = RequirementStatus.WORKERS_ASSIGNED.value
        db.commit()

        assignment = self._make_assignment(db, approved_requirement, worker_profile, admin_user)

        response = client.post(
            f"{BASE}/worker/assignments/{assignment.id}/decline",
            headers=worker_headers,
        )

        assert response.status_code == 200
        db.refresh(approved_requirement)
        assert approved_requirement.status == RequirementStatus.APPROVED.value


# ──────────────────────────────────────────────────────────────────
# Fix 8 — Admin assignment status update must validate transitions
# ──────────────────────────────────────────────────────────────────


class TestAssignmentStatusTransitionGuard:
    """update_assignment_status must reject illegal assignment status transitions."""

    def _get_assignment_id(self, client, requirement, worker_profile, admin_headers):
        return create_assignment(client, requirement.id, worker_profile.id, admin_headers)

    def test_completed_to_assigned_is_rejected(
        self,
        client,
        db,
        admin_headers,
        approved_requirement,
        worker_profile,
    ):
        """completed → assigned is a terminal-state violation; must return 400."""
        assignment_id = self._get_assignment_id(
            client, approved_requirement, worker_profile, admin_headers
        )

        # Manually force to completed in DB
        from app.repositories.assignment_repository import get_assignment_by_id
        assignment = get_assignment_by_id(db, assignment_id)
        assignment.status = AssignmentStatus.COMPLETED.value
        db.commit()

        response = client.patch(
            f"{BASE}/admin/assignments/{assignment_id}/status",
            json={"status": AssignmentStatus.ASSIGNED.value},
            headers=admin_headers,
        )

        assert response.status_code == 400
        assert "cannot transition" in response.json()["message"].lower()

    def test_active_to_completed_is_allowed(
        self,
        client,
        db,
        admin_headers,
        approved_requirement,
        worker_profile,
    ):
        """active → completed is a valid transition; must return 200."""
        assignment_id = self._get_assignment_id(
            client, approved_requirement, worker_profile, admin_headers
        )

        from app.repositories.assignment_repository import get_assignment_by_id
        assignment = get_assignment_by_id(db, assignment_id)
        assignment.status = AssignmentStatus.ACTIVE.value
        db.commit()

        response = client.patch(
            f"{BASE}/admin/assignments/{assignment_id}/status",
            json={"status": AssignmentStatus.COMPLETED.value},
            headers=admin_headers,
        )

        assert response.status_code == 200
        assert response.json()["data"]["status"] == AssignmentStatus.COMPLETED.value

    def test_cancelled_to_active_is_rejected(
        self,
        client,
        db,
        admin_headers,
        approved_requirement,
        worker_profile,
    ):
        """cancelled → active is a terminal-state violation; must return 400."""
        assignment_id = self._get_assignment_id(
            client, approved_requirement, worker_profile, admin_headers
        )

        from app.repositories.assignment_repository import get_assignment_by_id
        assignment = get_assignment_by_id(db, assignment_id)
        assignment.status = AssignmentStatus.CANCELLED.value
        db.commit()

        response = client.patch(
            f"{BASE}/admin/assignments/{assignment_id}/status",
            json={"status": AssignmentStatus.ACTIVE.value},
            headers=admin_headers,
        )

        assert response.status_code == 400
        assert "cannot transition" in response.json()["message"].lower()

    def test_assigned_to_accepted_is_allowed(
        self,
        client,
        db,
        admin_headers,
        approved_requirement,
        worker_profile,
    ):
        """assigned → accepted must remain allowed (admin manually confirms worker)."""
        assignment_id = self._get_assignment_id(
            client, approved_requirement, worker_profile, admin_headers
        )

        response = client.patch(
            f"{BASE}/admin/assignments/{assignment_id}/status",
            json={"status": AssignmentStatus.ACCEPTED.value},
            headers=admin_headers,
        )

        assert response.status_code == 200
        assert response.json()["data"]["status"] == AssignmentStatus.ACCEPTED.value


class TestWorkerInterestStatusSync:
    """Fix 15: assignment creation must set WorkerInterest.status = 'assigned' in the same transaction."""

    def test_assignment_creation_updates_worker_interest_status(
        self,
        client,
        db,
        admin_headers,
        approved_requirement,
        worker_profile,
    ):
        """If a WorkerInterest row exists for the worker+requirement, it must be set to 'assigned'."""
        from app.models.worker_interest import WorkerInterest

        interest = WorkerInterest(
            worker_profile_id=worker_profile.id,
            requirement_id=approved_requirement.id,
            status="interested",
        )
        db.add(interest)
        db.commit()
        db.refresh(interest)

        create_assignment(client, approved_requirement.id, worker_profile.id, admin_headers)

        db.refresh(interest)
        assert interest.status == "assigned"

    def test_assignment_creation_succeeds_without_worker_interest_row(
        self,
        client,
        admin_headers,
        approved_requirement,
        worker_profile,
    ):
        """Assignment creation must succeed even when no WorkerInterest row exists."""
        assignment_id = create_assignment(
            client, approved_requirement.id, worker_profile.id, admin_headers
        )
        assert assignment_id is not None


class TestWorkerAvailabilityManagement:
    """Fix 16: assignment creation sets worker unavailable; terminal status updates restore availability."""

    def test_assignment_creation_marks_worker_unavailable(
        self,
        client,
        db,
        admin_headers,
        approved_requirement,
        worker_profile,
    ):
        """worker_profile.is_available must be False after assignment is created."""
        assert worker_profile.is_available is True

        create_assignment(client, approved_requirement.id, worker_profile.id, admin_headers)

        db.refresh(worker_profile)
        assert worker_profile.is_available is False

    def test_declining_assignment_restores_availability(
        self,
        client,
        db,
        admin_headers,
        approved_requirement,
        worker_profile,
    ):
        """Updating assignment to 'declined' must set worker back to available."""
        assignment_id = create_assignment(
            client, approved_requirement.id, worker_profile.id, admin_headers
        )
        db.refresh(worker_profile)
        assert worker_profile.is_available is False

        client.patch(
            f"{BASE}/admin/assignments/{assignment_id}/status",
            json={"status": AssignmentStatus.DECLINED.value},
            headers=admin_headers,
        )

        db.refresh(worker_profile)
        assert worker_profile.is_available is True

    def test_cancelling_assignment_restores_availability(
        self,
        client,
        db,
        admin_headers,
        approved_requirement,
        worker_profile,
    ):
        """Updating assignment to 'cancelled' must set worker back to available."""
        assignment_id = create_assignment(
            client, approved_requirement.id, worker_profile.id, admin_headers
        )

        client.patch(
            f"{BASE}/admin/assignments/{assignment_id}/status",
            json={"status": AssignmentStatus.CANCELLED.value},
            headers=admin_headers,
        )

        db.refresh(worker_profile)
        assert worker_profile.is_available is True

    def test_completing_assignment_restores_availability(
        self,
        client,
        db,
        admin_headers,
        approved_requirement,
        worker_profile,
    ):
        """Updating assignment through accepted→active→completed must set worker available."""
        assignment_id = create_assignment(
            client, approved_requirement.id, worker_profile.id, admin_headers
        )
        client.patch(
            f"{BASE}/admin/assignments/{assignment_id}/status",
            json={"status": AssignmentStatus.ACCEPTED.value},
            headers=admin_headers,
        )
        client.patch(
            f"{BASE}/admin/assignments/{assignment_id}/status",
            json={"status": AssignmentStatus.ACTIVE.value},
            headers=admin_headers,
        )
        client.patch(
            f"{BASE}/admin/assignments/{assignment_id}/status",
            json={"status": AssignmentStatus.COMPLETED.value},
            headers=admin_headers,
        )

        db.refresh(worker_profile)
        assert worker_profile.is_available is True


class TestWorkerReplacementFlow:
    """Feature 3: atomic worker replacement via POST /admin/assignments/{id}/replace."""

    def test_replace_active_assignment_succeeds(
        self,
        client,
        db,
        admin_headers,
        approved_requirement,
        worker_profile,
        other_worker_profile,
    ):
        """Replace an assigned worker → old = replaced, new = assigned, availability toggled."""
        assignment_id = create_assignment(
            client, approved_requirement.id, worker_profile.id, admin_headers
        )

        response = client.post(
            f"{BASE}/admin/assignments/{assignment_id}/replace",
            json={
                "new_worker_profile_id": other_worker_profile.id,
                "reason": "Worker requested to be removed from this job",
            },
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["old_assignment_status"] == "replaced"
        assert data["new_assignment_status"] == "assigned"

        db.refresh(worker_profile)
        db.refresh(other_worker_profile)
        assert worker_profile.is_available is True, "Old worker should be freed"
        assert other_worker_profile.is_available is False, "New worker should be marked unavailable"

    def test_replace_completed_assignment_returns_400(
        self,
        client,
        db,
        admin_headers,
        approved_requirement,
        worker_profile,
        other_worker_profile,
    ):
        """Cannot replace a completed assignment — terminal state."""
        assignment_id = create_assignment(
            client, approved_requirement.id, worker_profile.id, admin_headers
        )
        for status in ["accepted", "active", "completed"]:
            client.patch(
                f"{BASE}/admin/assignments/{assignment_id}/status",
                json={"status": status},
                headers=admin_headers,
            )

        response = client.post(
            f"{BASE}/admin/assignments/{assignment_id}/replace",
            json={
                "new_worker_profile_id": other_worker_profile.id,
                "reason": "Trying to replace a completed assignment",
            },
            headers=admin_headers,
        )

        assert response.status_code == 400

    def test_replace_with_already_assigned_worker_returns_400(
        self,
        client,
        db,
        admin_headers,
        approved_requirement,
        worker_profile,
        other_worker_profile,
    ):
        """Cannot replace with a worker already actively assigned to the same requirement."""
        assignment_id = create_assignment(
            client, approved_requirement.id, worker_profile.id, admin_headers
        )
        create_assignment(
            client, approved_requirement.id, other_worker_profile.id, admin_headers
        )

        response = client.post(
            f"{BASE}/admin/assignments/{assignment_id}/replace",
            json={
                "new_worker_profile_id": other_worker_profile.id,
                "reason": "Trying to assign an already-assigned worker",
            },
            headers=admin_headers,
        )

        assert response.status_code == 400

    def test_replace_with_unavailable_worker_returns_400(
        self,
        client,
        db,
        admin_headers,
        approved_requirement,
        worker_profile,
        unavailable_worker_profile,
    ):
        """Cannot replace with a worker whose is_available is False."""
        assignment_id = create_assignment(
            client, approved_requirement.id, worker_profile.id, admin_headers
        )

        response = client.post(
            f"{BASE}/admin/assignments/{assignment_id}/replace",
            json={
                "new_worker_profile_id": unavailable_worker_profile.id,
                "reason": "Trying to use an unavailable replacement worker",
            },
            headers=admin_headers,
        )

        assert response.status_code == 400
