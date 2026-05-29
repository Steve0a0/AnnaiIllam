"""Tests for Polish 2: Salary Disbursement Tracking.

Covers:
1. Create disbursement for completed assignment → status = pending
2. Create duplicate disbursement for same assignment → 409
3. Mark paid with reference → worker notified, status = paid
4. Worker calls GET /worker/disbursements → sees only their own
5. Create disbursement for in_progress assignment → 400
"""
from datetime import date
from unittest.mock import patch

import pytest

from app.core.assignment_constants import AssignmentStatus
from app.core.statuses import RequirementStatus
from app.models.assignment import Assignment
from app.models.client_profile import ClientProfile
from app.models.requirement import Requirement
from app.models.worker_profile import WorkerProfile
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
def worker_headers(db, worker_user):
    access_token, _ = build_token_pair(
        db,
        user_id=worker_user.id,
        subject=worker_user.phone,
        role=worker_user.role,
    )
    return {"Authorization": f"Bearer {access_token}"}


# ──────────────────────────────────────────────────────────────────
# Domain fixtures
# ──────────────────────────────────────────────────────────────────


@pytest.fixture
def d_client_profile(db, client_user):
    profile = ClientProfile(
        user_id=client_user.id,
        client_type="company",
        company_name="Disburse Test Corp",
        contact_name="Meena Rajan",
        city="Chennai",
        state="Tamil Nadu",
        address="Nungambakkam",
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


@pytest.fixture
def d_worker_profile(db, worker_user):
    profile = WorkerProfile(
        user_id=worker_user.id,
        full_name="Disbursement Worker",
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
def d_requirement(db, d_client_profile, client_user):
    req = Requirement(
        client_id=d_client_profile.id,
        category="Security",
        number_of_workers=1,
        work_location="Main Gate",
        city="Chennai",
        state="Tamil Nadu",
        start_date=date.today(),
        duration_days=5,
        status=RequirementStatus.WORKERS_ASSIGNED.value,
        created_by_user_id=client_user.id,
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    return req


@pytest.fixture
def completed_assignment(db, d_requirement, d_worker_profile, admin_user):
    asgn = Assignment(
        requirement_id=d_requirement.id,
        worker_profile_id=d_worker_profile.id,
        assigned_by_user_id=admin_user.id,
        status=AssignmentStatus.COMPLETED.value,
    )
    db.add(asgn)
    db.commit()
    db.refresh(asgn)
    return asgn


@pytest.fixture
def inprogress_assignment(db, d_requirement, d_worker_profile, admin_user):
    asgn = Assignment(
        requirement_id=d_requirement.id,
        worker_profile_id=d_worker_profile.id,
        assigned_by_user_id=admin_user.id,
        status=AssignmentStatus.ACTIVE.value,
    )
    db.add(asgn)
    db.commit()
    db.refresh(asgn)
    return asgn


# ──────────────────────────────────────────────────────────────────
# Test 1: Create disbursement for completed assignment → pending
# ──────────────────────────────────────────────────────────────────


def test_create_disbursement_for_completed_assignment(
    client, db, admin_headers, completed_assignment
):
    resp = client.post(
        f"{BASE}/admin/disbursements",
        json={
            "assignment_id": completed_assignment.id,
            "amount": 50000,  # ₹500 in paise
            "scheduled_date": str(date.today()),
        },
        headers=admin_headers,
    )
    assert resp.status_code == 200, resp.json()
    data = resp.json()["data"]
    assert data["assignment_id"] == completed_assignment.id
    assert data["disbursement_status"] == "pending"
    assert data["amount"] == 50000


# ──────────────────────────────────────────────────────────────────
# Test 2: Create duplicate disbursement → 409
# ──────────────────────────────────────────────────────────────────


def test_create_duplicate_disbursement_returns_409(
    client, db, admin_headers, completed_assignment
):
    payload = {
        "assignment_id": completed_assignment.id,
        "amount": 50000,
        "scheduled_date": str(date.today()),
    }
    resp1 = client.post(f"{BASE}/admin/disbursements", json=payload, headers=admin_headers)
    assert resp1.status_code == 200, resp1.json()

    resp2 = client.post(f"{BASE}/admin/disbursements", json=payload, headers=admin_headers)
    assert resp2.status_code == 409
    assert "already exists" in resp2.json()["message"].lower()


# ──────────────────────────────────────────────────────────────────
# Test 3: Mark paid → worker notified, status = paid
# ──────────────────────────────────────────────────────────────────


@patch("app.api.admin_disbursements.enqueue_push_to_user")
def test_mark_disbursement_paid_notifies_worker(
    mock_push, client, db, admin_headers, completed_assignment
):
    # Create disbursement first
    create_resp = client.post(
        f"{BASE}/admin/disbursements",
        json={
            "assignment_id": completed_assignment.id,
            "amount": 60000,  # ₹600 in paise
            "scheduled_date": str(date.today()),
        },
        headers=admin_headers,
    )
    assert create_resp.status_code == 200, create_resp.json()
    disbursement_id = create_resp.json()["data"]["id"]

    # Mark as paid
    paid_resp = client.patch(
        f"{BASE}/admin/disbursements/{disbursement_id}/paid",
        json={"payment_reference": "NEFT-20260528-001"},
        headers=admin_headers,
    )
    assert paid_resp.status_code == 200, paid_resp.json()
    data = paid_resp.json()["data"]
    assert data["disbursement_status"] == "paid"
    assert data["payment_reference"] == "NEFT-20260528-001"
    assert data["paid_at"] is not None

    # Worker notification was sent
    assert mock_push.called
    call_kwargs = mock_push.call_args.kwargs
    assert "₹600" in call_kwargs["body"]
    assert "NEFT-20260528-001" in call_kwargs["body"]


# ──────────────────────────────────────────────────────────────────
# Test 4: Worker sees only their own disbursements
# ──────────────────────────────────────────────────────────────────


def test_worker_sees_only_own_disbursements(
    client, db, admin_headers, worker_headers, completed_assignment, d_worker_profile
):
    # Create a disbursement for the worker
    create_resp = client.post(
        f"{BASE}/admin/disbursements",
        json={
            "assignment_id": completed_assignment.id,
            "amount": 70000,
            "scheduled_date": str(date.today()),
        },
        headers=admin_headers,
    )
    assert create_resp.status_code == 200, create_resp.json()

    # Worker fetches their own disbursements
    worker_resp = client.get(f"{BASE}/worker/disbursements", headers=worker_headers)
    assert worker_resp.status_code == 200, worker_resp.json()
    items = worker_resp.json()["data"]["items"]
    assert len(items) == 1
    assert items[0]["worker_profile_id"] == d_worker_profile.id
    assert items[0]["amount"] == 70000


# ──────────────────────────────────────────────────────────────────
# Test 5: Create disbursement for in_progress assignment → 400
# ──────────────────────────────────────────────────────────────────


def test_create_disbursement_for_inprogress_assignment_returns_400(
    client, db, admin_headers, inprogress_assignment
):
    resp = client.post(
        f"{BASE}/admin/disbursements",
        json={
            "assignment_id": inprogress_assignment.id,
            "amount": 50000,
            "scheduled_date": str(date.today()),
        },
        headers=admin_headers,
    )
    assert resp.status_code == 400
    assert "completed" in resp.json()["message"].lower()
