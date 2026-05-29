"""Tests for client rating range validation (P2-8).

Policy: integer-only, 1–5 inclusive.
"""
import pytest
from datetime import date
from sqlalchemy.exc import IntegrityError

from app.models.client_profile import ClientProfile
from app.models.client_rating import ClientRating
from app.models.requirement import Requirement
from app.core.statuses import RequirementStatus
from app.services.token_service import build_token_pair

BASE = "/api/v1"

# ──────────────────────────────────────────────────────────────────
# Shared fixtures
# ──────────────────────────────────────────────────────────────────


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
def client_profile(db, client_user):
    profile = ClientProfile(
        user_id=client_user.id,
        client_type="individual",
        contact_name="Rating Test Client",
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
        category="Housekeeping",
        subcategory="General",
        number_of_workers=1,
        work_location="Home",
        city="Chennai",
        state="Tamil Nadu",
        start_date=date(2026, 6, 1),
        duration_days=7,
        shift_details="Morning 08:00-14:00",
        budget_amount=5000,
        status=RequirementStatus.APPROVED.value,
        created_by_user_id=client_user.id,
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    return req


# ──────────────────────────────────────────────────────────────────
# Pydantic / API-layer validation tests
# ──────────────────────────────────────────────────────────────────


class TestClientRatingApiValidation:
    def _post(self, client, headers, requirement_id, rating, **extra):
        payload = {
            "requirement_id": requirement_id,
            "rating": rating,
        }
        payload.update(extra)
        return client.post(f"{BASE}/client/ratings", json=payload, headers=headers)

    def test_rating_1_is_accepted(
        self, client, client_headers, client_profile, approved_requirement
    ):
        resp = self._post(client, client_headers, approved_requirement.id, 1)
        assert resp.status_code == 200

    def test_rating_5_is_accepted(
        self, client, client_headers, client_profile, approved_requirement
    ):
        resp = self._post(client, client_headers, approved_requirement.id, 5)
        assert resp.status_code == 200

    def test_rating_0_is_rejected(
        self, client, client_headers, client_profile, approved_requirement
    ):
        resp = self._post(client, client_headers, approved_requirement.id, 0)
        assert resp.status_code == 422

    def test_rating_6_is_rejected(
        self, client, client_headers, client_profile, approved_requirement
    ):
        resp = self._post(client, client_headers, approved_requirement.id, 6)
        assert resp.status_code == 422

    def test_rating_minus_1_is_rejected(
        self, client, client_headers, client_profile, approved_requirement
    ):
        resp = self._post(client, client_headers, approved_requirement.id, -1)
        assert resp.status_code == 422

    def test_rating_999_is_rejected(
        self, client, client_headers, client_profile, approved_requirement
    ):
        resp = self._post(client, client_headers, approved_requirement.id, 999)
        assert resp.status_code == 422

    def test_rating_3_point_5_is_rejected(
        self, client, client_headers, client_profile, approved_requirement
    ):
        """Integer-only policy: half-star values must be rejected."""
        resp = self._post(client, client_headers, approved_requirement.id, 3.5)
        assert resp.status_code == 422

    def test_valid_rating_is_stored_correctly(
        self, client, db, client_headers, client_profile, approved_requirement
    ):
        resp = self._post(client, client_headers, approved_requirement.id, 4)
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["rating"] == 4
        assert data["requirement_id"] == approved_requirement.id

    def test_update_rating_replaces_previous_value(
        self, client, client_headers, client_profile, approved_requirement
    ):
        """Submitting again for the same requirement updates (not duplicates) the rating."""
        self._post(client, client_headers, approved_requirement.id, 3)
        resp = self._post(client, client_headers, approved_requirement.id, 5)
        assert resp.status_code == 200
        assert resp.json()["data"]["rating"] == 5


# ──────────────────────────────────────────────────────────────────
# DB-level CheckConstraint tests
# ──────────────────────────────────────────────────────────────────


class TestClientRatingDbConstraint:
    def test_direct_insert_with_rating_0_raises_integrity_error(
        self, db, client_profile, approved_requirement, client_user
    ):
        """CheckConstraint on the table must reject out-of-range values at the DB level."""
        bad_rating = ClientRating(
            requirement_id=approved_requirement.id,
            rated_by_user_id=client_user.id,
            rating=0,
        )
        db.add(bad_rating)
        with pytest.raises((IntegrityError, Exception)):
            db.flush()
        db.rollback()

    def test_direct_insert_with_rating_6_raises_integrity_error(
        self, db, client_profile, approved_requirement, client_user
    ):
        bad_rating = ClientRating(
            requirement_id=approved_requirement.id,
            rated_by_user_id=client_user.id,
            rating=6,
        )
        db.add(bad_rating)
        with pytest.raises((IntegrityError, Exception)):
            db.flush()
        db.rollback()

    def test_direct_insert_with_valid_rating_succeeds(
        self, db, client_profile, approved_requirement, client_user
    ):
        good_rating = ClientRating(
            requirement_id=approved_requirement.id,
            rated_by_user_id=client_user.id,
            rating=4,
        )
        db.add(good_rating)
        db.flush()  # must not raise
        db.rollback()
