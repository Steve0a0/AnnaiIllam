"""Tests for Polish 3: Client Dispute Flow.

Covers:
1. Client raises dispute on completed requirement → admin notified
2. Client raises dispute on in_progress requirement → assert 400
3. Another client raises dispute on someone else's requirement → assert 403
4. Admin resolves with credit_amount → credit note created, client notified
5. Admin calls GET /admin/disputes → sees all disputes paginated
"""
from datetime import date
from unittest.mock import patch

import pytest

from app.core.statuses import RequirementStatus
from app.models.client_profile import ClientProfile
from app.models.dispute import DisputeCreditNote
from app.models.requirement import Requirement
from app.models.user import User
from app.services.token_service import build_token_pair

BASE = "/api/v1"


# ──────────────────────────────────────────────────────────────────
# Auth fixtures
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


# ──────────────────────────────────────────────────────────────────
# Second client — for ownership check test
# ──────────────────────────────────────────────────────────────────


@pytest.fixture
def other_client_user(db):
    user = User(
        phone="9000000099",
        email="other@annai-illam.test",
        role="client",
        is_active=True,
        is_phone_verified=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def other_client_headers(db, other_client_user):
    access_token, _ = build_token_pair(
        db,
        user_id=other_client_user.id,
        subject=other_client_user.phone,
        role=other_client_user.role,
    )
    return {"Authorization": f"Bearer {access_token}"}


# ──────────────────────────────────────────────────────────────────
# Domain fixtures
# ──────────────────────────────────────────────────────────────────


@pytest.fixture
def dis_client_profile(db, client_user):
    profile = ClientProfile(
        user_id=client_user.id,
        client_type="company",
        company_name="Dispute Test Corp",
        contact_name="Rani Priya",
        city="Chennai",
        state="Tamil Nadu",
        address="Anna Nagar",
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


@pytest.fixture
def other_client_profile(db, other_client_user):
    profile = ClientProfile(
        user_id=other_client_user.id,
        client_type="individual",
        contact_name="Bala Kumar",
        city="Chennai",
        state="Tamil Nadu",
        address="T. Nagar",
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


@pytest.fixture
def completed_requirement(db, dis_client_profile, client_user):
    req = Requirement(
        client_id=dis_client_profile.id,
        category="Security",
        number_of_workers=1,
        work_location="Main Gate",
        city="Chennai",
        state="Tamil Nadu",
        start_date=date.today(),
        duration_days=5,
        status=RequirementStatus.COMPLETED.value,
        created_by_user_id=client_user.id,
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    return req


@pytest.fixture
def active_requirement(db, dis_client_profile, client_user):
    req = Requirement(
        client_id=dis_client_profile.id,
        category="Cleaning",
        number_of_workers=1,
        work_location="Office Floor",
        city="Chennai",
        state="Tamil Nadu",
        start_date=date.today(),
        duration_days=3,
        status=RequirementStatus.WORKERS_ASSIGNED.value,
        created_by_user_id=client_user.id,
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    return req


# ──────────────────────────────────────────────────────────────────
# Test 1: Client raises dispute on completed requirement → admin notified
# ──────────────────────────────────────────────────────────────────


@patch("app.api.client_disputes.enqueue_push_to_user")
def test_raise_dispute_on_completed_requirement(
    mock_push, client, db, client_headers, completed_requirement, admin_user
):
    resp = client.post(
        f"{BASE}/client/disputes",
        json={
            "requirement_id": completed_requirement.id,
            "dispute_type": "quality",
            "description": "Worker did not complete the assigned tasks properly.",
        },
        headers=client_headers,
    )
    assert resp.status_code == 200, resp.json()
    data = resp.json()["data"]
    assert data["requirement_id"] == completed_requirement.id
    assert data["dispute_type"] == "quality"
    assert data["status"] == "open"

    # Admin was notified
    assert mock_push.called


# ──────────────────────────────────────────────────────────────────
# Test 2: Client raises dispute on non-completed requirement → 400
# ──────────────────────────────────────────────────────────────────


def test_raise_dispute_on_non_completed_requirement(
    client, db, client_headers, active_requirement
):
    resp = client.post(
        f"{BASE}/client/disputes",
        json={
            "requirement_id": active_requirement.id,
            "dispute_type": "billing",
            "description": "Incorrect billing for the assignment.",
        },
        headers=client_headers,
    )
    assert resp.status_code == 400
    assert "completed" in resp.json()["message"].lower()


# ──────────────────────────────────────────────────────────────────
# Test 3: Another client raises dispute on someone else's requirement → 403
# ──────────────────────────────────────────────────────────────────


def test_raise_dispute_on_other_clients_requirement(
    client, db, other_client_headers, other_client_profile, completed_requirement
):
    resp = client.post(
        f"{BASE}/client/disputes",
        json={
            "requirement_id": completed_requirement.id,
            "dispute_type": "attendance",
            "description": "Worker was absent for multiple days.",
        },
        headers=other_client_headers,
    )
    assert resp.status_code == 403
    assert "authorised" in resp.json()["message"].lower()


# ──────────────────────────────────────────────────────────────────
# Test 4: Admin resolves with credit_amount → credit note created, client notified
# ──────────────────────────────────────────────────────────────────


@patch("app.api.admin_disputes.enqueue_push_to_user")
def test_admin_resolves_dispute_with_credit_creates_credit_note(
    mock_push, client, db, admin_headers, client_headers, completed_requirement
):
    # First raise a dispute
    raise_resp = client.post(
        f"{BASE}/client/disputes",
        json={
            "requirement_id": completed_requirement.id,
            "dispute_type": "billing",
            "description": "Overcharged for the service. Requesting a credit.",
        },
        headers=client_headers,
    )
    assert raise_resp.status_code == 200, raise_resp.json()
    dispute_id = raise_resp.json()["data"]["id"]

    # Admin resolves with credit amount (₹200 = 20000 paise)
    resolve_resp = client.patch(
        f"{BASE}/admin/disputes/{dispute_id}/resolve",
        json={
            "resolution_notes": "Credit of Rs.200 issued as partial refund.",
            "credit_amount": 20000,
        },
        headers=admin_headers,
    )
    assert resolve_resp.status_code == 200, resolve_resp.json()
    data = resolve_resp.json()["data"]
    assert data["status"] == "resolved"
    assert data["credit_amount"] == 20000
    assert data["resolution_notes"] == "Credit of Rs.200 issued as partial refund."

    # Credit note was persisted
    credit_note = db.query(DisputeCreditNote).filter_by(dispute_id=dispute_id).first()
    assert credit_note is not None
    assert credit_note.amount == 20000

    # Client was notified
    assert mock_push.called


# ──────────────────────────────────────────────────────────────────
# Test 5: Admin calls GET /admin/disputes → paginated list
# ──────────────────────────────────────────────────────────────────


def test_admin_lists_all_disputes_paginated(
    client, db, admin_headers, client_headers, completed_requirement
):
    # Raise two disputes
    for dispute_type in ["quality", "other"]:
        client.post(
            f"{BASE}/client/disputes",
            json={
                "requirement_id": completed_requirement.id,
                "dispute_type": dispute_type,
                "description": f"Test dispute for type {dispute_type}.",
            },
            headers=client_headers,
        )

    resp = client.get(f"{BASE}/admin/disputes", headers=admin_headers)
    assert resp.status_code == 200, resp.json()
    body = resp.json()
    assert "items" in body["data"]
    assert body["data"]["total"] >= 2
