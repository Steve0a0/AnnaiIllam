"""Tests for Feature 7: Job Extension Flow.

Covers:
1. Request extension on in_progress requirement → extension quote created
2. Client approves extension → duration_days updated, assignment end_date extended
3. Request extension on completed requirement → 400
4. Request extension when a pending extension quote already exists → 400
"""
from datetime import date, timedelta
from unittest.mock import patch

import pytest

from app.core.statuses import RequirementStatus
from app.core.payment_constants import PaymentModel
from app.core.assignment_constants import AssignmentStatus
from app.models.assignment import Assignment
from app.models.client_profile import ClientProfile
from app.models.quote import Quote
from app.models.requirement import Requirement
from app.services.token_service import build_token_pair

BASE = "/api/v1"


# ──────────────────────────────────────────────────────────────────
# Auth header fixtures
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
# Domain fixtures
# ──────────────────────────────────────────────────────────────────


@pytest.fixture
def client_profile(db, client_user):
    profile = ClientProfile(
        user_id=client_user.id,
        client_type="company",
        company_name="Annai Textiles",
        contact_name="Priya Raman",
        city="Chennai",
        state="Tamil Nadu",
        address="T Nagar",
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


def _make_requirement(db, client_profile, client_user, status: str, duration_days: int = 10) -> Requirement:
    req = Requirement(
        client_id=client_profile.id,
        category="Housekeeping",
        subcategory="Sweeping",
        number_of_workers=3,
        work_location="Site A",
        city="Chennai",
        state="Tamil Nadu",
        start_date=date(2026, 6, 1),
        duration_days=duration_days,
        shift_details="Morning",
        budget_amount=50000,
        status=status,
        created_by_user_id=client_user.id,
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    return req


def _make_approved_quote(db, requirement, admin_user, quoted_amount: int = 30000) -> Quote:
    quote = Quote(
        requirement_id=requirement.id,
        quoted_amount=quoted_amount,
        rate_per_worker=1000,
        payment_model=PaymentModel.CLIENT_PAYS_COMPANY.value,
        status="approved",
        quote_type="standard",
        created_by_user_id=admin_user.id,
    )
    db.add(quote)
    db.commit()
    db.refresh(quote)
    return quote


def _make_assignment(db, requirement, admin_user, end_date: date) -> Assignment:
    from app.models.worker_profile import WorkerProfile
    from app.models.user import User
    from app.core.security import hash_password

    worker_user = User(
        phone="9100000099",
        role="worker",
        is_active=True,
        is_phone_verified=True,
    )
    db.add(worker_user)
    db.flush()

    worker = WorkerProfile(
        user_id=worker_user.id,
        full_name="Test Worker",
        city="Chennai",
        state="Tamil Nadu",
        category="Housekeeping",
        date_of_birth=date(1995, 1, 1),
        is_available=False,
    )
    db.add(worker)
    db.flush()

    assignment = Assignment(
        requirement_id=requirement.id,
        worker_profile_id=worker.id,
        assigned_by_user_id=admin_user.id,
        status=AssignmentStatus.ACTIVE.value,
        start_date=requirement.start_date,
        end_date=end_date,
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return assignment


# ──────────────────────────────────────────────────────────────────
# Test 1: Request extension on in_progress requirement → quote created
# ──────────────────────────────────────────────────────────────────


@patch("app.api.admin_requirements.enqueue_push_to_user")
def test_request_extension_creates_quote(mock_push, client, db, admin_headers, admin_user, client_user, client_profile):
    req = _make_requirement(db, client_profile, client_user, RequirementStatus.IN_PROGRESS.value)
    _make_approved_quote(db, req, admin_user)

    resp = client.post(
        f"{BASE}/admin/requirements/{req.id}/request-extension",
        json={"additional_days": 5, "new_rate_per_worker": 1200},
        headers=admin_headers,
    )
    assert resp.status_code == 200, resp.json()
    data = resp.json()["data"]

    assert data["additional_days"] == 5
    assert data["requirement_id"] == req.id
    # extension_amount = 1200 * 3 workers * 5 days = 18000
    assert data["extension_amount"] == 18000
    assert data["quote_status"] == "sent"

    # Verify quote in DB
    db.expire_all()
    ext_quote = db.get(Quote, data["extension_quote_id"])
    assert ext_quote is not None
    assert ext_quote.quote_type == "extension"
    assert ext_quote.extension_days == 5
    assert ext_quote.status == "sent"
    assert ext_quote.valid_until == date.today() + timedelta(days=7)

    # Client should be notified
    mock_push.assert_called_once()


# ──────────────────────────────────────────────────────────────────
# Test 2: Client approves extension → duration_days and assignment
#         end_date extended
# ──────────────────────────────────────────────────────────────────


@patch("app.api.admin_requirements.enqueue_push_to_user")
def test_client_approves_extension_updates_requirement_and_assignments(
    mock_push, client, db, admin_headers, client_headers, admin_user, client_user, client_profile
):
    req = _make_requirement(db, client_profile, client_user, RequirementStatus.IN_PROGRESS.value, duration_days=10)
    _make_approved_quote(db, req, admin_user)
    original_end = date(2026, 6, 1) + timedelta(days=9)  # start + (10 - 1)
    assignment = _make_assignment(db, req, admin_user, end_date=original_end)

    # Admin requests extension
    ext_resp = client.post(
        f"{BASE}/admin/requirements/{req.id}/request-extension",
        json={"additional_days": 3, "new_rate_per_worker": 1000},
        headers=admin_headers,
    )
    assert ext_resp.status_code == 200, ext_resp.json()

    # Client approves the extension quote
    decision_resp = client.post(
        f"{BASE}/client/requirements/{req.id}/quote-decision",
        json={"action": "approve"},
        headers=client_headers,
    )
    assert decision_resp.status_code == 200, decision_resp.json()
    assert decision_resp.json()["data"]["quote_status"] == "approved"

    # Verify requirement duration extended
    db.expire_all()
    updated_req = db.get(Requirement, req.id)
    assert updated_req.duration_days == 13  # 10 + 3

    # Verify assignment end_date extended by 3 days
    updated_assignment = db.get(Assignment, assignment.id)
    assert updated_assignment.end_date == original_end + timedelta(days=3)


# ──────────────────────────────────────────────────────────────────
# Test 3: Request extension on completed requirement → 400
# ──────────────────────────────────────────────────────────────────


def test_request_extension_on_completed_requirement_blocked(
    client, db, admin_headers, admin_user, client_user, client_profile
):
    req = _make_requirement(db, client_profile, client_user, RequirementStatus.COMPLETED.value)
    _make_approved_quote(db, req, admin_user)

    resp = client.post(
        f"{BASE}/admin/requirements/{req.id}/request-extension",
        json={"additional_days": 5, "new_rate_per_worker": 1000},
        headers=admin_headers,
    )
    assert resp.status_code == 400
    assert "extension" in resp.json()["message"].lower()


# ──────────────────────────────────────────────────────────────────
# Test 4: Request extension when pending extension quote exists → 400
# ──────────────────────────────────────────────────────────────────


@patch("app.api.admin_requirements.enqueue_push_to_user")
def test_duplicate_extension_request_blocked(
    mock_push, client, db, admin_headers, admin_user, client_user, client_profile
):
    req = _make_requirement(db, client_profile, client_user, RequirementStatus.IN_PROGRESS.value)
    _make_approved_quote(db, req, admin_user)

    # First extension request
    resp1 = client.post(
        f"{BASE}/admin/requirements/{req.id}/request-extension",
        json={"additional_days": 5, "new_rate_per_worker": 1000},
        headers=admin_headers,
    )
    assert resp1.status_code == 200

    # Second extension request while first is still pending
    resp2 = client.post(
        f"{BASE}/admin/requirements/{req.id}/request-extension",
        json={"additional_days": 3, "new_rate_per_worker": 1000},
        headers=admin_headers,
    )
    assert resp2.status_code == 400
    assert "pending" in resp2.json()["message"].lower()
