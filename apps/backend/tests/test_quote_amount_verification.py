"""Tests for Polish 8: Server-side Quote Amount Verification.

Covers:
1. Submit quote with tampered quoted_amount=1 → stored = correct computed value
2. Submit with correct amount → stored unchanged
3. Submit with amount off by 1 rupee (trivial rounding) → corrected silently

Requirement fixture: 3 workers × 10 days → expected = rate_per_worker × 30
"""
from datetime import date, timedelta

import pytest

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
        company_name="QA Verify Co",
        contact_name="Sundar",
        city="Chennai",
        state="Tamil Nadu",
        address="Velachery",
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


@pytest.fixture
def admin_headers(db, admin_user):
    access_token, _ = build_token_pair(
        db, user_id=admin_user.id, subject=admin_user.email, role=admin_user.role
    )
    return {"Authorization": f"Bearer {access_token}"}


def _make_submitted_requirement(db, client_profile, client_user) -> int:
    """Create a requirement in 'submitted' status (3 workers × 10 days)."""
    req = Requirement(
        client_id=client_profile.id,
        category="Security",
        number_of_workers=3,
        work_location="Main Gate",
        city="Chennai",
        state="Tamil Nadu",
        start_date=date.today() + timedelta(days=7),
        duration_days=10,
        status="submitted",
        created_by_user_id=client_user.id,
    )
    db.add(req)
    db.commit()
    db.refresh(req)

    # Move to under_review so quote endpoint accepts it
    req.status = "under_review"
    db.commit()
    return req.id


def _quote_payload(requirement_id: int, quoted_amount: int, rate_per_worker: int = 1300) -> dict:
    return {
        "requirement_id": requirement_id,
        "quoted_amount": quoted_amount,
        "rate_per_worker": rate_per_worker,
        "total_worker_days": 30,
        "advance_amount": 10000,
        "payment_model": "advance",
        "valid_until": str(date.today() + timedelta(days=14)),
        "terms_notes": "Advance before assignment.",
    }


# ──────────────────────────────────────────────────────────────────
# Test 1: Tampered quoted_amount → overridden with computed value
# ──────────────────────────────────────────────────────────────────


def test_tampered_amount_is_overridden(client, db, client_user, client_profile, admin_headers):
    """Submitting quoted_amount=1 with rate_per_worker=1300 on 3×10 req
    should store 1300×3×10=39000, not 1."""
    req_id = _make_submitted_requirement(db, client_profile, client_user)
    payload = _quote_payload(req_id, quoted_amount=1, rate_per_worker=1300)

    resp = client.post(
        f"{BASE}/admin/requirements/{req_id}/quote",
        json=payload,
        headers=admin_headers,
    )

    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["quoted_amount"] == 39000  # 1300 × 3 × 10

    # Confirm stored in DB
    quote = db.query(Quote).filter(Quote.requirement_id == req_id).first()
    assert quote is not None
    assert quote.quoted_amount == 39000


# ──────────────────────────────────────────────────────────────────
# Test 2: Correct amount submitted → stored unchanged
# ──────────────────────────────────────────────────────────────────


def test_correct_amount_stored_unchanged(client, db, client_user, client_profile, admin_headers):
    """Submitting the exact computed amount → stored as-is."""
    req_id = _make_submitted_requirement(db, client_profile, client_user)
    # 1300 × 3 × 10 = 39000 — correct
    payload = _quote_payload(req_id, quoted_amount=39000, rate_per_worker=1300)

    resp = client.post(
        f"{BASE}/admin/requirements/{req_id}/quote",
        json=payload,
        headers=admin_headers,
    )

    assert resp.status_code == 200
    assert resp.json()["data"]["quoted_amount"] == 39000

    quote = db.query(Quote).filter(Quote.requirement_id == req_id).first()
    assert quote.quoted_amount == 39000


# ──────────────────────────────────────────────────────────────────
# Test 3: Off by 1 rupee → corrected silently
# ──────────────────────────────────────────────────────────────────


def test_off_by_one_rupee_corrected_silently(
    client, db, client_user, client_profile, admin_headers
):
    """quoted_amount one rupee off from computed → overridden to correct value."""
    req_id = _make_submitted_requirement(db, client_profile, client_user)
    # 39001 is 1 off from 39000 — small rounding error
    payload = _quote_payload(req_id, quoted_amount=39001, rate_per_worker=1300)

    resp = client.post(
        f"{BASE}/admin/requirements/{req_id}/quote",
        json=payload,
        headers=admin_headers,
    )

    assert resp.status_code == 200
    assert resp.json()["data"]["quoted_amount"] == 39000

    quote = db.query(Quote).filter(Quote.requirement_id == req_id).first()
    assert quote.quoted_amount == 39000
