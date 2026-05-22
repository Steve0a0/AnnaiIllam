"""Integration coverage for admin and worker assignment flows."""
from datetime import date, timedelta

import pytest

from app.core.assignment_constants import AssignmentStatus
from app.core.statuses import RequirementStatus
from app.models.client_profile import ClientProfile
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
def approved_requirement(db, client_profile, client_user):
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
        params={"skip_payment_check": "true"},
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
            AssignmentStatus.ASSIGNED.value,
            AssignmentStatus.ACCEPTED.value,
            AssignmentStatus.DECLINED.value,
            AssignmentStatus.ACTIVE.value,
            AssignmentStatus.COMPLETED.value,
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
        assert approved_requirement.status == RequirementStatus.ASSIGNED.value

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
            params={"skip_payment_check": "true"},
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
        assert "no confirmed payment" in response.json()["message"].lower()

    def test_assignment_create_requires_available_approved_worker(
        self,
        client,
        admin_headers,
        approved_requirement,
        unavailable_worker_profile,
    ):
        response = client.post(
            f"{BASE}/admin/assignments",
            params={"skip_payment_check": "true"},
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
            params={"skip_payment_check": "true"},
            json=assignment_payload(approved_requirement.id, worker_profile.id),
            headers=admin_headers,
        )
        assert response.status_code == 400
        assert "already assigned" in response.json()["message"]

    def test_admin_assignment_routes_require_admin_role(
        self,
        client,
        client_headers,
        approved_requirement,
        worker_profile,
    ):
        response = client.post(
            f"{BASE}/admin/assignments",
            params={"skip_payment_check": "true"},
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
