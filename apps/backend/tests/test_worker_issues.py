"""Integration tests for the worker issues API.

Covers:
  POST /worker/issues  — create issue (profile check, assignment ownership, role)
  GET  /worker/issues  — list own issues (profile check, role isolation)
"""
import pytest

from app.core.assignment_constants import AssignmentStatus
from app.models.assignment import Assignment
from app.models.client_profile import ClientProfile
from app.models.requirement import Requirement
from app.models.user import User
from app.models.worker_profile import WorkerProfile
from app.services.token_service import build_token_pair
from app.core.statuses import RequirementStatus

BASE = "/api/v1"
TODAY = __import__("datetime").date.today()


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
def worker_profile(db, worker_user):
    profile = WorkerProfile(
        user_id=worker_user.id,
        full_name="Ravi Kumar",
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
def other_worker_user(db):
    user = User(
        phone="9000000088",
        email="other-worker-issues@annai-illam.test",
        role="worker",
        is_active=True,
        is_phone_verified=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def other_worker_headers(db, other_worker_user):
    access_token, _ = build_token_pair(
        db,
        user_id=other_worker_user.id,
        subject=other_worker_user.phone,
        role=other_worker_user.role,
    )
    return {"Authorization": f"Bearer {access_token}"}


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
def client_profile(db, client_user):
    profile = ClientProfile(
        user_id=client_user.id,
        client_type="company",
        company_name="Annam Textiles",
        contact_name="Priya Raman",
        city="Chennai",
        state="Tamil Nadu",
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


@pytest.fixture
def requirement(db, client_profile, client_user):
    req = Requirement(
        client_id=client_profile.id,
        category="Security",
        number_of_workers=1,
        work_location="Gate 1",
        city="Chennai",
        state="Tamil Nadu",
        start_date=TODAY,
        duration_days=5,
        shift_details="Day",
        budget_amount=10000,
        status=RequirementStatus.WORKERS_ASSIGNED.value,
        created_by_user_id=client_user.id,
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    return req


@pytest.fixture
def assignment(db, requirement, worker_profile, admin_user):
    item = Assignment(
        requirement_id=requirement.id,
        worker_profile_id=worker_profile.id,
        assigned_by_user_id=admin_user.id,
        status=AssignmentStatus.ACCEPTED.value,
        assigned_role="Guard",
        assigned_shift="Day",
        salary_amount=1000,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def _issue_payload(**overrides):
    payload = {
        "issue_type": "safety",
        "description": "There is a broken glass on the floor near the entrance that needs immediate attention.",
    }
    payload.update(overrides)
    return payload


# ──────────────────────────────────────────────────────────────────
# Create Worker Issue
# ──────────────────────────────────────────────────────────────────


class TestCreateWorkerIssue:
    def test_worker_creates_issue_without_assignment(self, client, worker_headers, worker_profile):
        response = client.post(
            f"{BASE}/worker/issues",
            json=_issue_payload(),
            headers=worker_headers,
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert "id" in data
        assert data["status"] == "open"

    def test_worker_creates_issue_linked_to_own_assignment(
        self, client, worker_headers, worker_profile, assignment
    ):
        response = client.post(
            f"{BASE}/worker/issues",
            json=_issue_payload(assignment_id=assignment.id),
            headers=worker_headers,
        )
        assert response.status_code == 200

    def test_worker_cannot_create_issue_for_another_workers_assignment(
        self, client, other_worker_headers, other_worker_profile, assignment
    ):
        response = client.post(
            f"{BASE}/worker/issues",
            json=_issue_payload(assignment_id=assignment.id),
            headers=other_worker_headers,
        )
        assert response.status_code == 404

    def test_worker_without_profile_cannot_create_issue(self, client, other_worker_headers):
        response = client.post(
            f"{BASE}/worker/issues",
            json=_issue_payload(),
            headers=other_worker_headers,
        )
        assert response.status_code == 404
        assert "profile" in response.json()["message"].lower()

    def test_admin_cannot_create_worker_issue(self, client, admin_headers):
        response = client.post(
            f"{BASE}/worker/issues",
            json=_issue_payload(),
            headers=admin_headers,
        )
        assert response.status_code == 403

    def test_client_cannot_create_worker_issue(self, client, client_headers):
        response = client.post(
            f"{BASE}/worker/issues",
            json=_issue_payload(),
            headers=client_headers,
        )
        assert response.status_code == 403

    def test_unauthenticated_cannot_create_worker_issue(self, client):
        response = client.post(f"{BASE}/worker/issues", json=_issue_payload())
        assert response.status_code == 401

    def test_nonexistent_assignment_id_returns_404(self, client, worker_headers, worker_profile):
        response = client.post(
            f"{BASE}/worker/issues",
            json=_issue_payload(assignment_id=999999),
            headers=worker_headers,
        )
        assert response.status_code == 404


# ──────────────────────────────────────────────────────────────────
# List Worker Issues
# ──────────────────────────────────────────────────────────────────


class TestListWorkerIssues:
    def test_worker_lists_own_issues(self, client, worker_headers, worker_profile):
        client.post(f"{BASE}/worker/issues", json=_issue_payload(), headers=worker_headers)

        response = client.get(f"{BASE}/worker/issues", headers=worker_headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_worker_sees_only_own_issues(
        self, client, worker_headers, other_worker_headers, worker_profile, other_worker_profile
    ):
        client.post(f"{BASE}/worker/issues", json=_issue_payload(), headers=worker_headers)

        response = client.get(f"{BASE}/worker/issues", headers=other_worker_headers)
        data = response.json()["data"]
        assert data == []

    def test_listed_issue_has_expected_fields(self, client, worker_headers, worker_profile):
        client.post(f"{BASE}/worker/issues", json=_issue_payload(), headers=worker_headers)

        response = client.get(f"{BASE}/worker/issues", headers=worker_headers)
        item = response.json()["data"][0]
        assert "id" in item
        assert "issue_type" in item
        assert "description" in item
        assert "status" in item
        assert "created_at" in item

    def test_worker_without_profile_cannot_list_issues(self, client, other_worker_headers):
        response = client.get(f"{BASE}/worker/issues", headers=other_worker_headers)
        assert response.status_code == 404

    def test_admin_cannot_list_worker_issues(self, client, admin_headers):
        response = client.get(f"{BASE}/worker/issues", headers=admin_headers)
        assert response.status_code == 403

    def test_unauthenticated_cannot_list_worker_issues(self, client):
        response = client.get(f"{BASE}/worker/issues")
        assert response.status_code == 401
