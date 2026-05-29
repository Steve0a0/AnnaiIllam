"""Tests for P1 Item 2 — Hard-Block Unavailable Workers and Tighten Conflict Detection.

Covered scenarios:
  1. Assign worker with is_available=False → 400
  2. Assign worker with schedule mismatch → 400
  3. Assign worker with overlapping ACTIVE assignment on a different requirement → 400
  4. Unit: detect_worker_conflict returns None (no crash) when requirement.start_date is None
  5. Unit: detect_worker_conflict returns None (no crash) when requirement.duration_days is None
  6. Worker with COMPLETED previous assignment on another requirement can be assigned again

Note on tests 4/5: requirements.start_date and requirements.duration_days are NOT NULL in the
DB schema, so these cases cannot be created via API.  They are tested at the service level
using plain mock objects to verify the guard added to detect_worker_conflict.
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
from app.services.worker_matching_service import detect_worker_conflict, get_worker_schedule_mismatch

BASE = "/api/v1"

REQ_START = date.today() + timedelta(days=14)
REQ_DURATION = 7


# ──────────────────────────────────────────────────────────────────
# Shared fixtures
# ──────────────────────────────────────────────────────────────────


@pytest.fixture
def client_profile(db, client_user):
    profile = ClientProfile(
        user_id=client_user.id,
        client_type="company",
        company_name="Conflict Test Co",
        contact_name="Tester",
        city="Chennai",
        state="Tamil Nadu",
        address="Mylapore",
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


def _make_approved_req(db, client_profile, client_user, start_date=None, duration_days=None):
    req = Requirement(
        client_id=client_profile.id,
        category="Security",
        number_of_workers=5,
        work_location="Gate A",
        city="Chennai",
        state="Tamil Nadu",
        start_date=start_date or REQ_START,
        duration_days=duration_days or REQ_DURATION,
        status=RequirementStatus.APPROVED.value,
        created_by_user_id=client_user.id,
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    return req


@pytest.fixture
def approved_requirement(db, client_profile, client_user):
    return _make_approved_req(db, client_profile, client_user)


@pytest.fixture
def overlapping_requirement(db, client_profile, client_user):
    """Second requirement whose dates overlap with approved_requirement."""
    return _make_approved_req(
        db,
        client_profile,
        client_user,
        start_date=REQ_START + timedelta(days=2),
        duration_days=REQ_DURATION,
    )


@pytest.fixture
def worker_profile(db, worker_user):
    profile = WorkerProfile(
        user_id=worker_user.id,
        full_name="Block Test Worker",
        category="Security",
        city="Chennai",
        state="Tamil Nadu",
        address="Kodambakkam",
        is_available=True,
        verification_status="approved",
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


@pytest.fixture
def unavailable_worker(db):
    from app.models.user import User
    user = User(
        phone="9111111110",
        email="unavailable@annai-illam.test",
        role="worker",
        is_active=True,
        is_phone_verified=True,
    )
    db.add(user)
    db.flush()
    profile = WorkerProfile(
        user_id=user.id,
        full_name="Not Available Worker",
        category="Security",
        city="Chennai",
        state="Tamil Nadu",
        address="Adyar",
        is_available=False,
        verification_status="approved",
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


@pytest.fixture
def shift_mismatched_worker(db):
    """Worker available only on Morning shift; requirement will use Night shift."""
    from app.models.user import User
    user = User(
        phone="9111111111",
        email="mismatch@annai-illam.test",
        role="worker",
        is_active=True,
        is_phone_verified=True,
    )
    db.add(user)
    db.flush()
    profile = WorkerProfile(
        user_id=user.id,
        full_name="Morning Only Worker",
        category="Security",
        city="Chennai",
        state="Tamil Nadu",
        address="Adyar",
        available_shifts="Morning",
        is_available=True,
        verification_status="approved",
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


@pytest.fixture
def night_shift_requirement(db, client_profile, client_user):
    req = Requirement(
        client_id=client_profile.id,
        category="Security",
        number_of_workers=5,
        work_location="Gate Night",
        city="Chennai",
        state="Tamil Nadu",
        start_date=REQ_START,
        duration_days=REQ_DURATION,
        shift_details="Evening Shift - 14:00 to 22:00",
        status=RequirementStatus.APPROVED.value,
        created_by_user_id=client_user.id,
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    return req


@pytest.fixture
def admin_headers(db, admin_user):
    access_token, _ = build_token_pair(
        db,
        user_id=admin_user.id,
        subject=admin_user.email,
        role=admin_user.role,
    )
    return {"Authorization": f"Bearer {access_token}"}


def _post_assignment(client, admin_headers, requirement_id, worker_profile_id):
    return client.post(
        f"{BASE}/admin/assignments",
        params={"skip_payment_check": "true", "skip_reason": "test"},
        json={"requirement_id": requirement_id, "worker_profile_id": worker_profile_id},
        headers=admin_headers,
    )


# ──────────────────────────────────────────────────────────────────
# Integration tests
# ──────────────────────────────────────────────────────────────────


class TestHardBlocks:
    def test_unavailable_worker_is_blocked(
        self, client, admin_headers, approved_requirement, unavailable_worker
    ):
        resp = _post_assignment(
            client, admin_headers, approved_requirement.id, unavailable_worker.id
        )
        assert resp.status_code == 400
        assert "not available" in resp.json()["message"].lower()

    def test_schedule_mismatch_worker_is_blocked(
        self, client, admin_headers, night_shift_requirement, shift_mismatched_worker
    ):
        resp = _post_assignment(
            client, admin_headers, night_shift_requirement.id, shift_mismatched_worker.id
        )
        assert resp.status_code == 400
        msg = resp.json()["message"].lower()
        assert "shift" in msg or "schedule" in msg or "mismatch" in msg or "worker is" in msg

    def test_overlapping_active_assignment_on_different_requirement_is_blocked(
        self, client, admin_headers, approved_requirement, overlapping_requirement, worker_profile, db
    ):
        # Give the worker an active assignment on approved_requirement
        active_assignment = Assignment(
            requirement_id=approved_requirement.id,
            worker_profile_id=worker_profile.id,
            status=AssignmentStatus.ACTIVE.value,
            assigned_by_user_id=admin_user_id_from_db(db),
        )
        db.add(active_assignment)
        db.commit()

        # Now try assigning the same worker to overlapping_requirement
        resp = _post_assignment(
            client, admin_headers, overlapping_requirement.id, worker_profile.id
        )
        assert resp.status_code == 400
        msg = resp.json()["message"].lower()
        assert "conflict" in msg

    def test_completed_assignment_does_not_block_new_overlapping_assignment(
        self, client, admin_headers, approved_requirement, overlapping_requirement, worker_profile, db
    ):
        # Worker has a COMPLETED assignment on approved_requirement
        completed_assignment = Assignment(
            requirement_id=approved_requirement.id,
            worker_profile_id=worker_profile.id,
            status=AssignmentStatus.COMPLETED.value,
            assigned_by_user_id=admin_user_id_from_db(db),
        )
        db.add(completed_assignment)
        db.commit()

        # Same worker can still be assigned to overlapping_requirement
        resp = _post_assignment(
            client, admin_headers, overlapping_requirement.id, worker_profile.id
        )
        assert resp.status_code == 200


def admin_user_id_from_db(db):
    """Return the ID of the admin user fixture by looking up the known test email."""
    from sqlalchemy import select
    from app.models.user import User
    result = db.execute(
        select(User.id).where(User.email == "admin@annai-illam.test")
    ).scalar_one_or_none()
    return result or 1


# ──────────────────────────────────────────────────────────────────
# Unit tests: null-safety guards in service functions
# ──────────────────────────────────────────────────────────────────


class _MockReq:
    """Minimal stub that mimics a Requirement with controllable date fields."""
    def __init__(self, start_date, duration_days):
        self.start_date = start_date
        self.duration_days = duration_days
        self.id = 999
        self.shift_details = None
        self.available_days = None


class TestServiceNullSafety:
    def test_detect_worker_conflict_returns_none_when_start_date_is_none(self, db):
        req = _MockReq(start_date=None, duration_days=7)
        result = detect_worker_conflict(db, worker_profile_id=1, requirement=req)
        assert result is None

    def test_detect_worker_conflict_returns_none_when_duration_days_is_none(self, db):
        req = _MockReq(start_date=date.today(), duration_days=None)
        result = detect_worker_conflict(db, worker_profile_id=1, requirement=req)
        assert result is None

    def test_get_worker_schedule_mismatch_skips_day_check_when_start_date_is_none(self):
        class MockWorker:
            available_days = "Mon,Tue,Wed"
            available_shifts = None
        req = _MockReq(start_date=None, duration_days=7)
        # Should not raise even though start_date is None
        result = get_worker_schedule_mismatch(MockWorker(), req)
        assert result is None
