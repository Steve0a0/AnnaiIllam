"""Integration tests for the worker jobs (open jobs + interest) API.

Covers:
  GET  /worker/jobs/open                   — list open jobs scored for worker
  POST /worker/jobs/{req_id}/interest      — express interest
  POST /worker/jobs/{req_id}/withdraw      — withdraw interest

Business rules:
  - Only approved/assigned requirements appear in open jobs
  - Jobs where the worker already has an active assignment are excluded
  - Scoring: category/subcategory/city/state/skills contribute to score
  - match_tier: 'best' (>=50), 'nearby' (>=10), 'other'
  - Worker must have a profile
  - Express interest is idempotent (re-expressing sets status='interested')
  - Withdraw requires prior interest record
  - Admin/client role → 403
"""
from datetime import date, timedelta

import pytest

from app.core.assignment_constants import AssignmentStatus
from app.core.statuses import RequirementStatus
from app.models.assignment import Assignment
from app.models.client_profile import ClientProfile
from app.models.requirement import Requirement
from app.models.worker_profile import WorkerProfile
from app.services.token_service import build_token_pair

BASE = "/api/v1"
TODAY = date.today()


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
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


@pytest.fixture
def worker_profile(db, worker_user):
    profile = WorkerProfile(
        user_id=worker_user.id,
        full_name="Ravi Kumar",
        category="Security",
        subcategory="Night Guard",
        city="Chennai",
        state="Tamil Nadu",
        skills=["Security", "Night Guard"],
        is_available=True,
        verification_status="approved",
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


@pytest.fixture
def approved_requirement(db, client_profile, client_user):
    req = Requirement(
        client_id=client_profile.id,
        category="Security",
        subcategory="Night Guard",
        number_of_workers=2,
        work_location="Gate 1",
        city="Chennai",
        state="Tamil Nadu",
        start_date=TODAY + timedelta(days=7),
        duration_days=10,
        shift_details="Night 20:00-06:00",
        budget_amount=30000,
        status=RequirementStatus.APPROVED.value,
        created_by_user_id=client_user.id,
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    return req


@pytest.fixture
def assigned_requirement(db, client_profile, client_user):
    req = Requirement(
        client_id=client_profile.id,
        category="Housekeeping",
        subcategory=None,
        number_of_workers=1,
        work_location="Block B",
        city="Madurai",
        state="Tamil Nadu",
        start_date=TODAY + timedelta(days=3),
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
def submitted_requirement(db, client_profile, client_user):
    """Not open — should not appear in open jobs list."""
    req = Requirement(
        client_id=client_profile.id,
        category="Security",
        number_of_workers=1,
        work_location="Site X",
        city="Chennai",
        state="Tamil Nadu",
        start_date=TODAY + timedelta(days=5),
        duration_days=5,
        shift_details="Day",
        budget_amount=5000,
        status=RequirementStatus.SUBMITTED.value,
        created_by_user_id=client_user.id,
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    return req


# ──────────────────────────────────────────────────────────────────
# Open Jobs Listing
# ──────────────────────────────────────────────────────────────────


class TestOpenJobsListing:
    def test_worker_sees_open_approved_requirement(
        self, client, worker_headers, worker_profile, approved_requirement
    ):
        response = client.get(f"{BASE}/worker/jobs/open", headers=worker_headers)
        assert response.status_code == 200
        ids = [j["requirement_id"] for j in response.json()["data"]]
        assert approved_requirement.id in ids

    def test_worker_sees_open_assigned_requirement(
        self, client, worker_headers, worker_profile, assigned_requirement
    ):
        response = client.get(f"{BASE}/worker/jobs/open", headers=worker_headers)
        assert response.status_code == 200
        ids = [j["requirement_id"] for j in response.json()["data"]]
        assert assigned_requirement.id in ids

    def test_submitted_requirement_not_in_open_jobs(
        self, client, worker_headers, worker_profile, submitted_requirement
    ):
        response = client.get(f"{BASE}/worker/jobs/open", headers=worker_headers)
        assert response.status_code == 200
        ids = [j["requirement_id"] for j in response.json()["data"]]
        assert submitted_requirement.id not in ids

    def test_job_has_expected_fields(
        self, client, worker_headers, worker_profile, approved_requirement
    ):
        response = client.get(f"{BASE}/worker/jobs/open", headers=worker_headers)
        jobs = response.json()["data"]
        job = next(j for j in jobs if j["requirement_id"] == approved_requirement.id)
        assert "category" in job
        assert "city" in job
        assert "score" in job
        assert "match_tier" in job
        assert "match_reasons" in job
        assert job["match_tier"] in ("best", "nearby", "other")

    def test_category_match_gives_high_score(
        self, client, worker_headers, worker_profile, approved_requirement
    ):
        response = client.get(f"{BASE}/worker/jobs/open", headers=worker_headers)
        jobs = response.json()["data"]
        job = next(j for j in jobs if j["requirement_id"] == approved_requirement.id)
        # Worker is Security/Chennai; requirement is Security/Chennai → high score
        assert job["score"] >= 50
        assert job["match_tier"] == "best"
        assert "category match" in job["match_reasons"]

    def test_worker_already_assigned_job_excluded(
        self, client, db, worker_headers, worker_profile, approved_requirement, admin_user
    ):
        assignment = Assignment(
            requirement_id=approved_requirement.id,
            worker_profile_id=worker_profile.id,
            assigned_by_user_id=admin_user.id,
            status=AssignmentStatus.ACCEPTED.value,
            assigned_role="Guard",
            assigned_shift="Night",
            salary_amount=1000,
        )
        db.add(assignment)
        db.commit()

        response = client.get(f"{BASE}/worker/jobs/open", headers=worker_headers)
        ids = [j["requirement_id"] for j in response.json()["data"]]
        assert approved_requirement.id not in ids

    def test_worker_without_profile_returns_404(self, client, worker_headers):
        response = client.get(f"{BASE}/worker/jobs/open", headers=worker_headers)
        assert response.status_code == 404

    def test_admin_cannot_list_open_jobs(self, client, admin_headers):
        response = client.get(f"{BASE}/worker/jobs/open", headers=admin_headers)
        assert response.status_code == 403

    def test_client_cannot_list_open_jobs(self, client, client_headers):
        response = client.get(f"{BASE}/worker/jobs/open", headers=client_headers)
        assert response.status_code == 403

    def test_unauthenticated_cannot_list_open_jobs(self, client):
        response = client.get(f"{BASE}/worker/jobs/open")
        assert response.status_code == 401


# ──────────────────────────────────────────────────────────────────
# Express Interest
# ──────────────────────────────────────────────────────────────────


class TestExpressInterest:
    def test_worker_expresses_interest_in_open_job(
        self, client, worker_headers, worker_profile, approved_requirement
    ):
        response = client.post(
            f"{BASE}/worker/jobs/{approved_requirement.id}/interest",
            headers=worker_headers,
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["requirement_id"] == approved_requirement.id
        assert data["status"] == "interested"

    def test_interest_appears_in_open_jobs_list(
        self, client, worker_headers, worker_profile, approved_requirement
    ):
        client.post(
            f"{BASE}/worker/jobs/{approved_requirement.id}/interest",
            headers=worker_headers,
        )
        response = client.get(f"{BASE}/worker/jobs/open", headers=worker_headers)
        jobs = response.json()["data"]
        job = next((j for j in jobs if j["requirement_id"] == approved_requirement.id), None)
        assert job is not None
        assert job["my_interest"] == "interested"

    def test_re_expressing_interest_is_idempotent(
        self, client, worker_headers, worker_profile, approved_requirement
    ):
        client.post(
            f"{BASE}/worker/jobs/{approved_requirement.id}/interest",
            headers=worker_headers,
        )
        response = client.post(
            f"{BASE}/worker/jobs/{approved_requirement.id}/interest",
            headers=worker_headers,
        )
        assert response.status_code == 200
        assert response.json()["data"]["status"] == "interested"

    def test_cannot_express_interest_in_nonexistent_job(
        self, client, worker_headers, worker_profile
    ):
        response = client.post(
            f"{BASE}/worker/jobs/999999/interest",
            headers=worker_headers,
        )
        assert response.status_code == 404

    def test_cannot_express_interest_in_submitted_requirement(
        self, client, worker_headers, worker_profile, submitted_requirement
    ):
        response = client.post(
            f"{BASE}/worker/jobs/{submitted_requirement.id}/interest",
            headers=worker_headers,
        )
        assert response.status_code == 404

    def test_cannot_express_interest_when_already_assigned(
        self, client, db, worker_headers, worker_profile, approved_requirement, admin_user
    ):
        assignment = Assignment(
            requirement_id=approved_requirement.id,
            worker_profile_id=worker_profile.id,
            assigned_by_user_id=admin_user.id,
            status=AssignmentStatus.ACCEPTED.value,
            assigned_role="Guard",
            assigned_shift="Night",
            salary_amount=1000,
        )
        db.add(assignment)
        db.commit()

        response = client.post(
            f"{BASE}/worker/jobs/{approved_requirement.id}/interest",
            headers=worker_headers,
        )
        assert response.status_code == 400

    def test_worker_without_profile_cannot_express_interest(
        self, client, worker_headers, approved_requirement
    ):
        response = client.post(
            f"{BASE}/worker/jobs/{approved_requirement.id}/interest",
            headers=worker_headers,
        )
        assert response.status_code == 404

    def test_admin_cannot_express_interest(self, client, admin_headers, approved_requirement):
        response = client.post(
            f"{BASE}/worker/jobs/{approved_requirement.id}/interest",
            headers=admin_headers,
        )
        assert response.status_code == 403


# ──────────────────────────────────────────────────────────────────
# Withdraw Interest
# ──────────────────────────────────────────────────────────────────


class TestWithdrawInterest:
    def test_worker_withdraws_expressed_interest(
        self, client, worker_headers, worker_profile, approved_requirement
    ):
        client.post(
            f"{BASE}/worker/jobs/{approved_requirement.id}/interest",
            headers=worker_headers,
        )
        response = client.post(
            f"{BASE}/worker/jobs/{approved_requirement.id}/withdraw",
            headers=worker_headers,
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["status"] == "withdrawn"

    def test_withdrawn_interest_reflected_in_open_jobs(
        self, client, worker_headers, worker_profile, approved_requirement
    ):
        client.post(
            f"{BASE}/worker/jobs/{approved_requirement.id}/interest",
            headers=worker_headers,
        )
        client.post(
            f"{BASE}/worker/jobs/{approved_requirement.id}/withdraw",
            headers=worker_headers,
        )
        response = client.get(f"{BASE}/worker/jobs/open", headers=worker_headers)
        jobs = response.json()["data"]
        job = next((j for j in jobs if j["requirement_id"] == approved_requirement.id), None)
        if job:
            assert job["my_interest"] == "withdrawn"

    def test_withdraw_without_prior_interest_returns_404(
        self, client, worker_headers, worker_profile, approved_requirement
    ):
        response = client.post(
            f"{BASE}/worker/jobs/{approved_requirement.id}/withdraw",
            headers=worker_headers,
        )
        assert response.status_code == 404

    def test_admin_cannot_withdraw_interest(self, client, admin_headers, approved_requirement):
        response = client.post(
            f"{BASE}/worker/jobs/{approved_requirement.id}/withdraw",
            headers=admin_headers,
        )
        assert response.status_code == 403
