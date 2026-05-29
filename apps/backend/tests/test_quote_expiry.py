"""Tests for P1 Item 4 — Enforce Quote Expiry.

Covered scenarios:
  1. Client approves quote where valid_until is yesterday → 400
  2. Client approves quote where valid_until is today → 200 (boundary: still valid)
  3. Client approves quote where valid_until is tomorrow → 200
  4. Client approves quote where valid_until is null → 200
  5. Client rejects an expired quote → 200 (expiry only blocks approval)
"""

from datetime import date, timedelta

import pytest

from app.core.statuses import QuoteStatus, RequirementStatus
from app.models.client_profile import ClientProfile
from app.models.quote import Quote
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
        company_name="Expiry Test Co",
        contact_name="Tester",
        city="Chennai",
        state="Tamil Nadu",
        address="T Nagar",
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


@pytest.fixture
def client_headers(db, client_user):
    access_token, _ = build_token_pair(
        db,
        user_id=client_user.id,
        subject=client_user.phone,
        role=client_user.role,
    )
    return {"Authorization": f"Bearer {access_token}"}


def _make_quoted_requirement_with_quote(
    db, client_profile, admin_user, valid_until: date | None
) -> tuple[Requirement, Quote]:
    """Create a requirement in 'quoted' state with a SENT quote."""
    req = Requirement(
        client_id=client_profile.id,
        category="Security",
        number_of_workers=1,
        work_location="Gate A",
        city="Chennai",
        state="Tamil Nadu",
        start_date=date.today() + timedelta(days=7),
        duration_days=30,
        status=RequirementStatus.QUOTED.value,
        created_by_user_id=client_profile.user_id,
    )
    db.add(req)
    db.flush()

    quote = Quote(
        requirement_id=req.id,
        quoted_amount=40000,
        rate_per_worker=1000,
        total_worker_days=40,
        advance_amount=10000,
        payment_model="advance",
        valid_until=valid_until,
        status=QuoteStatus.SENT.value,
        created_by_user_id=admin_user.id,
    )
    db.add(quote)
    db.commit()
    db.refresh(req)
    db.refresh(quote)
    return req, quote


# ──────────────────────────────────────────────────────────────────
# Tests
# ──────────────────────────────────────────────────────────────────


class TestQuoteExpiryEnforcement:
    def test_approve_expired_quote_returns_400(
        self, client, client_headers, client_profile, admin_user, db
    ):
        yesterday = date.today() - timedelta(days=1)
        req, _ = _make_quoted_requirement_with_quote(db, client_profile, admin_user, yesterday)

        resp = client.post(
            f"{BASE}/client/requirements/{req.id}/quote-decision",
            json={"action": "approve"},
            headers=client_headers,
        )
        assert resp.status_code == 400
        assert "expired" in resp.json()["message"].lower()

    def test_approve_quote_expiring_today_succeeds(
        self, client, client_headers, client_profile, admin_user, db
    ):
        today = date.today()
        req, _ = _make_quoted_requirement_with_quote(db, client_profile, admin_user, today)

        resp = client.post(
            f"{BASE}/client/requirements/{req.id}/quote-decision",
            json={"action": "approve"},
            headers=client_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["requirement_status"] == RequirementStatus.APPROVED.value

    def test_approve_quote_expiring_tomorrow_succeeds(
        self, client, client_headers, client_profile, admin_user, db
    ):
        tomorrow = date.today() + timedelta(days=1)
        req, _ = _make_quoted_requirement_with_quote(db, client_profile, admin_user, tomorrow)

        resp = client.post(
            f"{BASE}/client/requirements/{req.id}/quote-decision",
            json={"action": "approve"},
            headers=client_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["requirement_status"] == RequirementStatus.APPROVED.value

    def test_approve_quote_with_null_valid_until_succeeds(
        self, client, client_headers, client_profile, admin_user, db
    ):
        req, _ = _make_quoted_requirement_with_quote(db, client_profile, admin_user, None)

        resp = client.post(
            f"{BASE}/client/requirements/{req.id}/quote-decision",
            json={"action": "approve"},
            headers=client_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["requirement_status"] == RequirementStatus.APPROVED.value

    def test_reject_expired_quote_is_allowed(
        self, client, client_headers, client_profile, admin_user, db
    ):
        """Expiry check only blocks approval; rejection should still be allowed."""
        yesterday = date.today() - timedelta(days=1)
        req, _ = _make_quoted_requirement_with_quote(db, client_profile, admin_user, yesterday)

        resp = client.post(
            f"{BASE}/client/requirements/{req.id}/quote-decision",
            json={"action": "reject"},
            headers=client_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["requirement_status"] == RequirementStatus.UNDER_REVIEW.value
