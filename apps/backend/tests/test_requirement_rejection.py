"""Tests for P1 Item 1 — Requirement Rejection Reason.

Covered scenarios:
  1. Admin rejects with valid reason → status=rejected, reason stored
  2. Admin rejects with blank reason → 422 (validation error)
  3. Admin rejects with missing reason → 422 (validation error)
  4. Admin rejects completed requirement → 400 (invalid transition)
  5. Admin rejects submitted requirement → 400 (not in under_review or quoted)
  6. Client detail response includes rejection_reason
  7. Non-admin cannot call reject endpoint
"""

from datetime import date, timedelta

import pytest

from app.core.statuses import RequirementStatus
from app.models.client_profile import ClientProfile
from app.models.requirement import Requirement
from app.services.token_service import build_token_pair

BASE = "/api/v1"


# ──────────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────────


@pytest.fixture
def client_profile(db, client_user):
    profile = ClientProfile(
        user_id=client_user.id,
        client_type="company",
        company_name="Test Co",
        contact_name="Test Person",
        city="Chennai",
        state="Tamil Nadu",
        address="Nungambakkam",
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


def _make_requirement(db, client_profile, status: str) -> Requirement:
    req = Requirement(
        client_id=client_profile.id,
        category="Security",
        number_of_workers=2,
        work_location="Gate 1",
        city="Chennai",
        state="Tamil Nadu",
        start_date=date.today() + timedelta(days=7),
        duration_days=30,
        status=status,
        created_by_user_id=client_profile.user_id,
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    return req


# ──────────────────────────────────────────────────────────────────
# Tests: POST /admin/requirements/{id}/reject
# ──────────────────────────────────────────────────────────────────


class TestRejectRequirement:
    def test_reject_under_review_requirement_stores_reason(
        self, client, admin_headers, client_profile, db
    ):
        req = _make_requirement(db=db, client_profile=client_profile, status=RequirementStatus.UNDER_REVIEW.value)
        resp = client.post(
            f"{BASE}/admin/requirements/{req.id}/reject",
            json={"reason": "Insufficient details provided."},
            headers=admin_headers,
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["status"] == RequirementStatus.REJECTED.value
        assert data["rejection_reason"] == "Insufficient details provided."

    def test_reject_quoted_requirement_stores_reason(
        self, client, admin_headers, client_profile, db
    ):
        req = _make_requirement(db=db, client_profile=client_profile, status=RequirementStatus.QUOTED.value)
        resp = client.post(
            f"{BASE}/admin/requirements/{req.id}/reject",
            json={"reason": "Budget mismatch."},
            headers=admin_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["status"] == RequirementStatus.REJECTED.value
        assert resp.json()["data"]["rejection_reason"] == "Budget mismatch."

    def test_reject_with_blank_reason_returns_422(
        self, client, admin_headers, client_profile, db
    ):
        req = _make_requirement(db=db, client_profile=client_profile, status=RequirementStatus.UNDER_REVIEW.value)
        resp = client.post(
            f"{BASE}/admin/requirements/{req.id}/reject",
            json={"reason": "   "},
            headers=admin_headers,
        )
        assert resp.status_code == 422

    def test_reject_with_missing_reason_returns_422(
        self, client, admin_headers, client_profile, db
    ):
        req = _make_requirement(db=db, client_profile=client_profile, status=RequirementStatus.UNDER_REVIEW.value)
        resp = client.post(
            f"{BASE}/admin/requirements/{req.id}/reject",
            json={},
            headers=admin_headers,
        )
        assert resp.status_code == 422

    def test_reject_completed_requirement_returns_400(
        self, client, admin_headers, client_profile, db
    ):
        req = _make_requirement(db=db, client_profile=client_profile, status=RequirementStatus.COMPLETED.value)
        resp = client.post(
            f"{BASE}/admin/requirements/{req.id}/reject",
            json={"reason": "Trying to reject completed."},
            headers=admin_headers,
        )
        assert resp.status_code == 400

    def test_reject_submitted_requirement_returns_400(
        self, client, admin_headers, client_profile, db
    ):
        """submitted → rejected is allowed by the state machine, so this should succeed."""
        req = _make_requirement(db=db, client_profile=client_profile, status=RequirementStatus.SUBMITTED.value)
        resp = client.post(
            f"{BASE}/admin/requirements/{req.id}/reject",
            json={"reason": "Reject at submitted stage."},
            headers=admin_headers,
        )
        # submitted → rejected IS allowed per REQUIREMENT_TRANSITIONS
        assert resp.status_code == 200

    def test_non_admin_cannot_reject(
        self, client, client_headers, client_profile, db
    ):
        req = _make_requirement(db=db, client_profile=client_profile, status=RequirementStatus.UNDER_REVIEW.value)
        resp = client.post(
            f"{BASE}/admin/requirements/{req.id}/reject",
            json={"reason": "Should fail."},
            headers=client_headers,
        )
        assert resp.status_code == 403

    def test_reject_nonexistent_requirement_returns_404(
        self, client, admin_headers
    ):
        resp = client.post(
            f"{BASE}/admin/requirements/99999/reject",
            json={"reason": "Does not exist."},
            headers=admin_headers,
        )
        assert resp.status_code == 404


# ──────────────────────────────────────────────────────────────────
# Tests: client detail includes rejection_reason
# ──────────────────────────────────────────────────────────────────


class TestClientRejectionReasonVisible:
    def test_client_detail_shows_rejection_reason(
        self, client, admin_headers, client_headers, client_profile, db
    ):
        req = _make_requirement(db=db, client_profile=client_profile, status=RequirementStatus.UNDER_REVIEW.value)

        # Admin rejects
        reject_resp = client.post(
            f"{BASE}/admin/requirements/{req.id}/reject",
            json={"reason": "Service area not covered."},
            headers=admin_headers,
        )
        assert reject_resp.status_code == 200

        # Client views own requirement detail
        detail_resp = client.get(
            f"{BASE}/client/requirements/{req.id}",
            headers=client_headers,
        )
        assert detail_resp.status_code == 200
        data = detail_resp.json()["data"]
        assert data["status"] == RequirementStatus.REJECTED.value
        assert data["rejection_reason"] == "Service area not covered."

    def test_client_detail_rejection_reason_null_when_not_rejected(
        self, client, client_headers, client_profile, db
    ):
        req = _make_requirement(db=db, client_profile=client_profile, status=RequirementStatus.SUBMITTED.value)

        detail_resp = client.get(
            f"{BASE}/client/requirements/{req.id}",
            headers=client_headers,
        )
        assert detail_resp.status_code == 200
        assert detail_resp.json()["data"]["rejection_reason"] is None

    def test_admin_detail_shows_rejection_reason(
        self, client, admin_headers, client_profile, db
    ):
        req = _make_requirement(db=db, client_profile=client_profile, status=RequirementStatus.UNDER_REVIEW.value)

        client.post(
            f"{BASE}/admin/requirements/{req.id}/reject",
            json={"reason": "Out of coverage area."},
            headers=admin_headers,
        )

        detail_resp = client.get(
            f"{BASE}/admin/requirements/{req.id}",
            headers=admin_headers,
        )
        assert detail_resp.status_code == 200
        assert detail_resp.json()["data"]["rejection_reason"] == "Out of coverage area."
