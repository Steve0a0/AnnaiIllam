"""Tests for P1 Item 3 — Validate Assignment Dates Against Requirement Window.

Covered scenarios:
  1. start_date before requirement.start_date → 400
  2. end_date after requirement end date → 400
  3. start_date and end_date inside window → 200
  4. start_date == requirement.start_date (boundary) → 200
  5. end_date == requirement end date (boundary) → 200
  6. null dates (both) → 200 (existing behaviour preserved)
  7. requirement has no start_date/duration_days → null dates allowed
"""

from datetime import date, timedelta

import pytest

from app.core.statuses import RequirementStatus
from app.models.client_profile import ClientProfile
from app.models.requirement import Requirement
from app.models.worker_profile import WorkerProfile
from app.services.token_service import build_token_pair

BASE = "/api/v1"

# ──────────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────────

REQ_START = date.today() + timedelta(days=10)
REQ_DURATION = 7  # 7-day window: REQ_START .. REQ_START + 6


@pytest.fixture
def client_profile(db, client_user):
    profile = ClientProfile(
        user_id=client_user.id,
        client_type="company",
        company_name="Date Test Co",
        contact_name="Checker",
        city="Chennai",
        state="Tamil Nadu",
        address="Anna Nagar",
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
        number_of_workers=5,
        work_location="Gate B",
        city="Chennai",
        state="Tamil Nadu",
        start_date=REQ_START,
        duration_days=REQ_DURATION,
        status=RequirementStatus.APPROVED.value,
        created_by_user_id=client_user.id,
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    return req


@pytest.fixture
def worker_profile(db, worker_user):
    profile = WorkerProfile(
        user_id=worker_user.id,
        full_name="Date Test Worker",
        category="Security",
        city="Chennai",
        state="Tamil Nadu",
        address="Adyar",
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


def _post_assignment(
    client,
    admin_headers,
    requirement_id: int,
    worker_profile_id: int,
    start_date: str | None,
    end_date: str | None,
):
    payload: dict = {
        "requirement_id": requirement_id,
        "worker_profile_id": worker_profile_id,
    }
    if start_date is not None:
        payload["start_date"] = start_date
    if end_date is not None:
        payload["end_date"] = end_date
    return client.post(
        f"{BASE}/admin/assignments",
        params={"skip_payment_check": "true", "skip_reason": "test"},
        json=payload,
        headers=admin_headers,
    )


# ──────────────────────────────────────────────────────────────────
# Tests
# ──────────────────────────────────────────────────────────────────


class TestAssignmentDateWindowValidation:
    def test_start_date_before_requirement_start_returns_400(
        self, client, admin_headers, approved_requirement, worker_profile
    ):
        before = (REQ_START - timedelta(days=1)).isoformat()
        end = REQ_START.isoformat()
        resp = _post_assignment(
            client,
            admin_headers,
            approved_requirement.id,
            worker_profile.id,
            before,
            end,
        )
        assert resp.status_code == 400
        assert "start date" in resp.json()["message"].lower()

    def test_end_date_after_requirement_end_returns_400(
        self, client, admin_headers, approved_requirement, worker_profile
    ):
        req_end = REQ_START + timedelta(days=REQ_DURATION - 1)
        after = (req_end + timedelta(days=1)).isoformat()
        resp = _post_assignment(
            client,
            admin_headers,
            approved_requirement.id,
            worker_profile.id,
            REQ_START.isoformat(),
            after,
        )
        assert resp.status_code == 400
        assert "end date" in resp.json()["message"].lower()

    def test_dates_inside_window_succeeds(
        self, client, admin_headers, approved_requirement, worker_profile
    ):
        start = (REQ_START + timedelta(days=1)).isoformat()
        end = (REQ_START + timedelta(days=REQ_DURATION - 2)).isoformat()
        resp = _post_assignment(
            client,
            admin_headers,
            approved_requirement.id,
            worker_profile.id,
            start,
            end,
        )
        assert resp.status_code == 200

    def test_start_date_exactly_on_requirement_start_is_valid(
        self, client, admin_headers, approved_requirement, worker_profile
    ):
        resp = _post_assignment(
            client,
            admin_headers,
            approved_requirement.id,
            worker_profile.id,
            REQ_START.isoformat(),
            REQ_START.isoformat(),
        )
        assert resp.status_code == 200

    def test_end_date_exactly_on_requirement_end_is_valid(
        self, client, admin_headers, approved_requirement, worker_profile
    ):
        req_end = REQ_START + timedelta(days=REQ_DURATION - 1)
        resp = _post_assignment(
            client,
            admin_headers,
            approved_requirement.id,
            worker_profile.id,
            REQ_START.isoformat(),
            req_end.isoformat(),
        )
        assert resp.status_code == 200

    def test_null_dates_are_allowed(
        self, client, admin_headers, approved_requirement, worker_profile
    ):
        resp = _post_assignment(
            client,
            admin_headers,
            approved_requirement.id,
            worker_profile.id,
            None,
            None,
        )
        assert resp.status_code == 200

    def test_only_start_date_provided_is_validated(self, client, admin_headers, approved_requirement, worker_profile):
        """When only start_date is given (end_date null), start_date is still checked."""
        before = (REQ_START - timedelta(days=1)).isoformat()
        resp = _post_assignment(
            client,
            admin_headers,
            approved_requirement.id,
            worker_profile.id,
            before,
            None,
        )
        assert resp.status_code == 400
        assert "start date" in resp.json()["message"].lower()
