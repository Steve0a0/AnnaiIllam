"""Integration coverage for Feature 3 — Worker Replacement Flow.

Covered scenarios:
  1. Replace an active worker → old assignment = replaced, new assignment =
     assigned, replacement_reason and replaced_by_assignment_id set
  2. Replace a completed assignment → assert 400
  3. Replace a cancelled assignment → assert 400
  4. Replace with a worker already actively assigned to the same requirement
     → assert 400
  5. Replace with an unavailable worker → assert 400
  6. Non-admin cannot call replace endpoint → assert 403
"""

from datetime import date, timedelta
from unittest.mock import patch

import pytest

from app.core.assignment_constants import AssignmentStatus
from app.core.statuses import RequirementStatus
from app.models.assignment import Assignment
from app.models.client_payment import ClientPayment
from app.models.client_profile import ClientProfile
from app.models.requirement import Requirement
from app.models.user import User
from app.models.worker_profile import WorkerProfile
from app.core.payment_constants import ClientPaymentStatus, PaymentModel
from app.services.token_service import build_token_pair

BASE = "/api/v1"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


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
        food_required=False,
        accommodation_required=False,
        budget_amount=30000,
        status=RequirementStatus.APPROVED.value,
        created_by_user_id=client_user.id,
    )
    db.add(requirement)
    db.commit()
    db.refresh(requirement)
    return requirement


def _make_worker(db, phone: str, email: str, is_available: bool = True) -> tuple:
    user = User(
        phone=phone,
        email=email,
        role="worker",
        is_active=True,
        is_phone_verified=True,
    )
    db.add(user)
    db.flush()
    profile = WorkerProfile(
        user_id=user.id,
        full_name=f"Worker {phone[-4:]}",
        category="Security",
        subcategory="Night Guard",
        city="Chennai",
        state="Tamil Nadu",
        address="Velachery",
        skills="Security",
        experience_years="2-4 years",
        available_shifts="Night",
        is_available=is_available,
        verification_status="approved",
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return user, profile


@pytest.fixture
def worker_user_a(db):
    user, _ = _make_worker(db, "9100000011", "worker-a@annai-illam.test")
    return user


@pytest.fixture
def worker_profile_a(db, worker_user_a):
    from sqlalchemy import select
    from app.models.worker_profile import WorkerProfile
    wp = db.execute(
        select(WorkerProfile).where(WorkerProfile.user_id == worker_user_a.id)
    ).scalar_one()
    return wp


@pytest.fixture
def worker_user_b(db):
    user, _ = _make_worker(db, "9100000022", "worker-b@annai-illam.test")
    return user


@pytest.fixture
def worker_profile_b(db, worker_user_b):
    from sqlalchemy import select
    from app.models.worker_profile import WorkerProfile
    wp = db.execute(
        select(WorkerProfile).where(WorkerProfile.user_id == worker_user_b.id)
    ).scalar_one()
    return wp


@pytest.fixture
def unavailable_worker_user(db):
    user, _ = _make_worker(db, "9100000033", "worker-unavail@annai-illam.test", is_available=False)
    return user


@pytest.fixture
def unavailable_worker_profile(db, unavailable_worker_user):
    from sqlalchemy import select
    from app.models.worker_profile import WorkerProfile
    wp = db.execute(
        select(WorkerProfile).where(WorkerProfile.user_id == unavailable_worker_user.id)
    ).scalar_one()
    return wp


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
def worker_headers_a(db, worker_user_a):
    access_token, _ = build_token_pair(
        db,
        user_id=worker_user_a.id,
        subject=worker_user_a.phone,
        role=worker_user_a.role,
    )
    return {"Authorization": f"Bearer {access_token}"}


def _create_assignment(client, requirement_id: int, worker_profile_id: int, admin_headers) -> int:
    """Create an assignment, skipping the payment gate for tests."""
    response = client.post(
        f"{BASE}/admin/assignments",
        params={"skip_payment_check": "true", "skip_reason": "test payment override"},
        json={
            "requirement_id": requirement_id,
            "worker_profile_id": worker_profile_id,
            "assigned_role": "Night Security Guard",
            "assigned_shift": "Night 20:00-06:00",
            "salary_amount": 1250,
        },
        headers=admin_headers,
    )
    assert response.status_code == 200, response.json()
    return response.json()["data"]["assignment_id"]


def _set_assignment_status(db, assignment_id: int, new_status: str):
    """Directly update assignment status in DB to bypass transition checks."""
    assignment = db.get(Assignment, assignment_id)
    assignment.status = new_status
    db.commit()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestWorkerReplacement:
    @patch("app.api.admin_assignments.enqueue_push_to_user")
    def test_replace_assigned_worker_success(
        self,
        mock_push,
        client,
        db,
        admin_headers,
        approved_requirement,
        worker_profile_a,
        worker_profile_b,
    ):
        """Replace a worker with status=assigned → old replaced, new assigned."""
        old_id = _create_assignment(
            client, approved_requirement.id, worker_profile_a.id, admin_headers
        )

        response = client.post(
            f"{BASE}/admin/assignments/{old_id}/replace",
            json={"new_worker_profile_id": worker_profile_b.id, "reason": "No-show on day one"},
            headers=admin_headers,
        )
        assert response.status_code == 200, response.json()
        data = response.json()["data"]

        assert data["old_assignment_id"] == old_id
        assert data["old_assignment_status"] == AssignmentStatus.REPLACED.value
        new_id = data["new_assignment_id"]
        assert new_id != old_id
        assert data["new_assignment_status"] == AssignmentStatus.ASSIGNED.value

        # DB state
        db.expire_all()
        old_asgn = db.get(Assignment, old_id)
        new_asgn = db.get(Assignment, new_id)

        assert old_asgn.status == AssignmentStatus.REPLACED.value
        assert old_asgn.replacement_reason == "No-show on day one"
        assert old_asgn.replaced_by_assignment_id == new_id

        assert new_asgn.status == AssignmentStatus.ASSIGNED.value
        assert new_asgn.worker_profile_id == worker_profile_b.id
        assert new_asgn.assigned_role == old_asgn.assigned_role
        assert new_asgn.salary_amount == old_asgn.salary_amount

        # Old worker freed, new worker unavailable
        db.refresh(worker_profile_a)
        db.refresh(worker_profile_b)
        assert worker_profile_a.is_available is True
        assert worker_profile_b.is_available is False

        # Both workers notified
        assert mock_push.call_count == 2

    @patch("app.api.admin_assignments.enqueue_push_to_user")
    def test_replace_active_worker_success(
        self,
        mock_push,
        client,
        db,
        admin_headers,
        approved_requirement,
        worker_profile_a,
        worker_profile_b,
    ):
        """Replace a worker with status=active → same outcome."""
        old_id = _create_assignment(
            client, approved_requirement.id, worker_profile_a.id, admin_headers
        )
        _set_assignment_status(db, old_id, AssignmentStatus.ACTIVE.value)
        # worker_profile_a is marked unavailable by create, keep it that way
        worker_profile_a.is_available = False
        db.commit()

        response = client.post(
            f"{BASE}/admin/assignments/{old_id}/replace",
            json={"new_worker_profile_id": worker_profile_b.id, "reason": "Medical emergency"},
            headers=admin_headers,
        )
        assert response.status_code == 200, response.json()
        data = response.json()["data"]
        assert data["old_assignment_status"] == AssignmentStatus.REPLACED.value
        assert data["new_assignment_status"] == AssignmentStatus.ASSIGNED.value

    @patch("app.api.admin_assignments.enqueue_push_to_user")
    def test_cannot_replace_completed_assignment(
        self,
        mock_push,
        client,
        db,
        admin_headers,
        approved_requirement,
        worker_profile_a,
        worker_profile_b,
    ):
        """Replacing a completed assignment must return 400."""
        old_id = _create_assignment(
            client, approved_requirement.id, worker_profile_a.id, admin_headers
        )
        _set_assignment_status(db, old_id, AssignmentStatus.COMPLETED.value)

        response = client.post(
            f"{BASE}/admin/assignments/{old_id}/replace",
            json={"new_worker_profile_id": worker_profile_b.id, "reason": "Trying to replace completed"},
            headers=admin_headers,
        )
        assert response.status_code == 400
        assert "completed" in response.json()["message"].lower() or "replace" in response.json()["message"].lower()

    @patch("app.api.admin_assignments.enqueue_push_to_user")
    def test_cannot_replace_cancelled_assignment(
        self,
        mock_push,
        client,
        db,
        admin_headers,
        approved_requirement,
        worker_profile_a,
        worker_profile_b,
    ):
        """Replacing a cancelled assignment must return 400."""
        old_id = _create_assignment(
            client, approved_requirement.id, worker_profile_a.id, admin_headers
        )
        _set_assignment_status(db, old_id, AssignmentStatus.CANCELLED.value)
        worker_profile_a.is_available = True
        db.commit()

        response = client.post(
            f"{BASE}/admin/assignments/{old_id}/replace",
            json={"new_worker_profile_id": worker_profile_b.id, "reason": "Trying to replace cancelled"},
            headers=admin_headers,
        )
        assert response.status_code == 400

    @patch("app.api.admin_assignments.enqueue_push_to_user")
    def test_cannot_replace_with_already_active_worker_on_same_requirement(
        self,
        mock_push,
        client,
        db,
        admin_headers,
        approved_requirement,
        worker_profile_a,
        worker_profile_b,
    ):
        """Replacing with a worker already actively assigned to the same requirement must return 400."""
        old_id = _create_assignment(
            client, approved_requirement.id, worker_profile_a.id, admin_headers
        )
        # Also assign worker_b to the same requirement
        _create_assignment(
            client, approved_requirement.id, worker_profile_b.id, admin_headers
        )

        response = client.post(
            f"{BASE}/admin/assignments/{old_id}/replace",
            json={"new_worker_profile_id": worker_profile_b.id, "reason": "Duplicate worker attempt"},
            headers=admin_headers,
        )
        assert response.status_code == 400
        assert "already" in response.json()["message"].lower()

    @patch("app.api.admin_assignments.enqueue_push_to_user")
    def test_cannot_replace_with_unavailable_worker(
        self,
        mock_push,
        client,
        db,
        admin_headers,
        approved_requirement,
        worker_profile_a,
        unavailable_worker_profile,
    ):
        """Replacing with an unavailable worker must return 400."""
        old_id = _create_assignment(
            client, approved_requirement.id, worker_profile_a.id, admin_headers
        )

        response = client.post(
            f"{BASE}/admin/assignments/{old_id}/replace",
            json={
                "new_worker_profile_id": unavailable_worker_profile.id,
                "reason": "Trying unavailable worker",
            },
            headers=admin_headers,
        )
        assert response.status_code == 400
        assert "not available" in response.json()["message"].lower()

    def test_non_admin_cannot_replace_worker(
        self,
        client,
        db,
        admin_headers,
        worker_headers_a,
        approved_requirement,
        worker_profile_a,
        worker_profile_b,
    ):
        """Worker role must get 403 on the replace endpoint."""
        old_id = _create_assignment(
            client, approved_requirement.id, worker_profile_a.id, admin_headers
        )

        response = client.post(
            f"{BASE}/admin/assignments/{old_id}/replace",
            json={"new_worker_profile_id": worker_profile_b.id, "reason": "Unauthorized attempt"},
            headers=worker_headers_a,
        )
        assert response.status_code == 403

    @patch("app.api.admin_assignments.enqueue_push_to_user")
    def test_replace_nonexistent_assignment_returns_404(
        self,
        mock_push,
        client,
        db,
        admin_headers,
        worker_profile_b,
    ):
        """Replace on a non-existent assignment ID must return 404."""
        response = client.post(
            f"{BASE}/admin/assignments/999999/replace",
            json={"new_worker_profile_id": worker_profile_b.id, "reason": "Ghost assignment"},
            headers=admin_headers,
        )
        assert response.status_code == 404
