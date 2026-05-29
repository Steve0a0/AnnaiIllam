"""Polish 9: Missing Notifications Audit.

For each of the 11 new push notifications added during the audit, this file
contains one focused test that verifies the push is attempted with the correct
recipient user_id.

Mocking strategy:
  - enqueue_push_to_user (background) → patched at the *calling module*
  - send_push_to_user  (sync)          → patched at the *calling module*
  - _validate_selfie                   → patched where used to avoid
                                         selfie-token validation in check-in tests
"""

from datetime import date, timedelta
from unittest.mock import call, patch

import pytest

from app.core.assignment_constants import AssignmentStatus
from app.core.attendance_constants import AttendanceStatus
from app.core.payment_constants import ClientPaymentStatus
from app.core.statuses import QuoteStatus, RequirementStatus
from app.models.assignment import Assignment
from app.models.attendance import Attendance
from app.models.client_payment import ClientPayment
from app.models.client_profile import ClientProfile
from app.models.quote import Quote
from app.models.requirement import Requirement
from app.models.worker_profile import WorkerProfile
from app.services.token_service import build_token_pair

BASE = "/api/v1"


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------

def _admin_headers(db, admin_user):
    tok, _ = build_token_pair(db, user_id=admin_user.id, subject=admin_user.email, role=admin_user.role)
    return {"Authorization": f"Bearer {tok}"}


def _client_headers(db, client_user):
    tok, _ = build_token_pair(db, user_id=client_user.id, subject=client_user.phone, role=client_user.role)
    return {"Authorization": f"Bearer {tok}"}


def _worker_headers(db, worker_user):
    tok, _ = build_token_pair(db, user_id=worker_user.id, subject=worker_user.phone, role=worker_user.role)
    return {"Authorization": f"Bearer {tok}"}


# ---------------------------------------------------------------------------
# Shared domain fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def notif_client_profile(db, client_user):
    profile = ClientProfile(
        user_id=client_user.id,
        client_type="company",
        company_name="Annai Test Corp",
        contact_name="Priya Raman",
        city="Chennai",
        state="Tamil Nadu",
        address="T Nagar",
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


@pytest.fixture
def notif_worker_profile(db, worker_user):
    profile = WorkerProfile(
        user_id=worker_user.id,
        full_name="Ravi Kumar",
        category="Security",
        subcategory="Night Guard",
        city="Chennai",
        state="Tamil Nadu",
        address="Velachery",
        skills="Security",
        available_shifts="Day",
        is_available=True,
        verification_status="approved",
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


@pytest.fixture
def under_review_requirement(db, notif_client_profile, client_user):
    """Requirement in SUBMITTED status — ready to be moved to UNDER_REVIEW."""
    req = Requirement(
        client_id=notif_client_profile.id,
        category="Security",
        number_of_workers=1,
        work_location="Main Gate",
        city="Chennai",
        state="Tamil Nadu",
        start_date=date.today(),
        duration_days=3,
        status=RequirementStatus.SUBMITTED.value,
        created_by_user_id=client_user.id,
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    return req


@pytest.fixture
def in_progress_requirement(db, notif_client_profile, client_user):
    """Requirement in WORKERS_ASSIGNED status — ready to be completed."""
    req = Requirement(
        client_id=notif_client_profile.id,
        category="Cleaning",
        number_of_workers=1,
        work_location="Office Floor",
        city="Chennai",
        state="Tamil Nadu",
        start_date=date.today() - timedelta(days=2),
        duration_days=2,
        status=RequirementStatus.IN_PROGRESS.value,
        created_by_user_id=client_user.id,
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    return req


@pytest.fixture
def approved_requirement_for_assignment(db, notif_client_profile, client_user):
    """Requirement in APPROVED status — ready for worker assignment."""
    req = Requirement(
        client_id=notif_client_profile.id,
        category="Security",
        subcategory="Night Guard",
        number_of_workers=1,
        work_location="Warehouse",
        city="Chennai",
        state="Tamil Nadu",
        start_date=date.today(),
        duration_days=5,
        status=RequirementStatus.APPROVED.value,
        created_by_user_id=client_user.id,
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    return req


@pytest.fixture
def workers_assigned_requirement(db, notif_client_profile, client_user):
    """Requirement in WORKERS_ASSIGNED status — first check-in triggers IN_PROGRESS."""
    req = Requirement(
        client_id=notif_client_profile.id,
        category="Security",
        number_of_workers=1,
        work_location="Site A",
        city="Chennai",
        state="Tamil Nadu",
        start_date=date.today(),
        duration_days=5,
        require_geofence=False,
        status=RequirementStatus.WORKERS_ASSIGNED.value,
        created_by_user_id=client_user.id,
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    return req


@pytest.fixture
def active_assignment(db, workers_assigned_requirement, notif_worker_profile, admin_user):
    """Assignment in ASSIGNED status ready for first check-in."""
    asgn = Assignment(
        requirement_id=workers_assigned_requirement.id,
        worker_profile_id=notif_worker_profile.id,
        assigned_by_user_id=admin_user.id,
        status=AssignmentStatus.ASSIGNED.value,
        assigned_role="Security Guard",
        assigned_shift="Day",
        salary_amount=1000,
        start_date=date.today(),
        end_date=date.today() + timedelta(days=4),
    )
    db.add(asgn)
    db.commit()
    db.refresh(asgn)
    return asgn


@pytest.fixture
def submitted_requirement(db, notif_client_profile, client_user):
    """Fresh requirement in SUBMITTED status — used for quote-decision flow."""
    req = Requirement(
        client_id=notif_client_profile.id,
        category="Cleaning",
        number_of_workers=2,
        work_location="Office Block",
        city="Chennai",
        state="Tamil Nadu",
        start_date=date.today(),
        duration_days=7,
        status=RequirementStatus.UNDER_REVIEW.value,
        created_by_user_id=client_user.id,
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    return req


@pytest.fixture
def sent_quote(db, submitted_requirement, admin_user):
    """Standard (non-extension) quote in SENT status for decide_quote tests."""
    submitted_requirement.status = RequirementStatus.QUOTED.value
    db.commit()
    q = Quote(
        requirement_id=submitted_requirement.id,
        quoted_amount=50000,
        advance_amount=25000,
        payment_model="client_pays_company",
        status=QuoteStatus.SENT.value,
        created_by_user_id=admin_user.id,
        quote_type="standard",
        valid_until=date.today() + timedelta(days=7),
    )
    db.add(q)
    db.commit()
    db.refresh(q)
    return q


@pytest.fixture
def extension_requirement(db, notif_client_profile, client_user):
    """Requirement in WORKERS_ASSIGNED status — will have an extension quote."""
    req = Requirement(
        client_id=notif_client_profile.id,
        category="Security",
        number_of_workers=1,
        work_location="Extension Site",
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
def extension_assignment(db, extension_requirement, notif_worker_profile, admin_user):
    """Assignment in ASSIGNED status for the extension requirement."""
    asgn = Assignment(
        requirement_id=extension_requirement.id,
        worker_profile_id=notif_worker_profile.id,
        assigned_by_user_id=admin_user.id,
        status=AssignmentStatus.ASSIGNED.value,
        assigned_role="Security Guard",
        assigned_shift="Day",
        salary_amount=1000,
        start_date=date.today(),
        end_date=date.today() + timedelta(days=4),
    )
    db.add(asgn)
    db.commit()
    db.refresh(asgn)
    return asgn


@pytest.fixture
def extension_quote(db, extension_requirement, admin_user):
    """Extension quote in SENT status."""
    q = Quote(
        requirement_id=extension_requirement.id,
        quoted_amount=20000,
        payment_model="client_pays_company",
        status=QuoteStatus.SENT.value,
        created_by_user_id=admin_user.id,
        quote_type="extension",
        extension_days=3,
        valid_until=date.today() + timedelta(days=7),
    )
    db.add(q)
    db.commit()
    db.refresh(q)
    return q


@pytest.fixture
def pending_client_payment(db, notif_client_profile, client_user, admin_user):
    """Pending payment with matching requirement."""
    req = Requirement(
        client_id=notif_client_profile.id,
        category="Security",
        number_of_workers=1,
        work_location="Finance Test Site",
        city="Chennai",
        state="Tamil Nadu",
        start_date=date.today(),
        duration_days=3,
        status=RequirementStatus.APPROVED.value,
        created_by_user_id=client_user.id,
    )
    db.add(req)
    db.commit()
    db.refresh(req)

    payment = ClientPayment(
        client_id=notif_client_profile.id,
        requirement_id=req.id,
        amount=25000,
        payment_model="client_pays_company",
        payment_mode="manual",
        payment_status=ClientPaymentStatus.PENDING.value,
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment


@pytest.fixture
def assigned_assignment_for_decline(db, approved_requirement_for_assignment, notif_worker_profile, admin_user):
    """Assignment in ASSIGNED status for decline tests."""
    # Ensure requirement is in WORKERS_ASSIGNED for decline flow
    approved_requirement_for_assignment.status = RequirementStatus.WORKERS_ASSIGNED.value
    db.commit()
    asgn = Assignment(
        requirement_id=approved_requirement_for_assignment.id,
        worker_profile_id=notif_worker_profile.id,
        assigned_by_user_id=admin_user.id,
        status=AssignmentStatus.ASSIGNED.value,
        assigned_role="Security Guard",
        assigned_shift="Day",
        salary_amount=1000,
    )
    db.add(asgn)
    db.commit()
    db.refresh(asgn)
    return asgn


@pytest.fixture
def attendance_for_correction(db, workers_assigned_requirement, notif_worker_profile, admin_user, active_assignment):
    """Existing attendance record that can be corrected to NO_SHOW."""
    att = Attendance(
        assignment_id=active_assignment.id,
        worker_profile_id=notif_worker_profile.id,
        attendance_date=date.today(),
        status=AttendanceStatus.PRESENT.value,
        marked_by_user_id=admin_user.id,
    )
    db.add(att)
    db.commit()
    db.refresh(att)
    return att


# ---------------------------------------------------------------------------
# 1. mark_requirement_under_review → client notified
# ---------------------------------------------------------------------------

@patch("app.api.admin_requirements.enqueue_push_to_user")
def test_mark_requirement_under_review_notifies_client(
    mock_push, client, db, admin_user, client_user, notif_client_profile, under_review_requirement
):
    headers = _admin_headers(db, admin_user)
    resp = client.post(
        f"{BASE}/admin/requirements/{under_review_requirement.id}/mark-review",
        headers=headers,
    )
    assert resp.status_code == 200, resp.json()
    assert mock_push.called
    # The client's user_id should appear in one of the calls
    recipient_ids = [c.kwargs["user_id"] for c in mock_push.call_args_list]
    assert client_user.id in recipient_ids


# ---------------------------------------------------------------------------
# 2. complete_requirement → client notified
# ---------------------------------------------------------------------------

@patch("app.api.admin_requirements.enqueue_push_to_user")
def test_complete_requirement_notifies_client(
    mock_push, client, db, admin_user, client_user, notif_client_profile, in_progress_requirement
):
    headers = _admin_headers(db, admin_user)
    resp = client.post(
        f"{BASE}/admin/requirements/{in_progress_requirement.id}/complete",
        headers=headers,
    )
    assert resp.status_code == 200, resp.json()
    assert mock_push.called
    recipient_ids = [c.kwargs["user_id"] for c in mock_push.call_args_list]
    assert client_user.id in recipient_ids


# ---------------------------------------------------------------------------
# 3. create_admin_assignment → client notified (workers assigned to your job)
# ---------------------------------------------------------------------------

@patch("app.api.admin_assignments.send_push_to_user")
def test_create_admin_assignment_notifies_client(
    mock_push, client, db, admin_user, client_user,
    notif_client_profile, notif_worker_profile,
    approved_requirement_for_assignment,
):
    headers = _admin_headers(db, admin_user)
    resp = client.post(
        f"{BASE}/admin/assignments"
        f"?skip_payment_check=true&skip_reason=notification+test",
        json={
            "requirement_id": approved_requirement_for_assignment.id,
            "worker_profile_id": notif_worker_profile.id,
        },
        headers=headers,
    )
    assert resp.status_code == 200, resp.json()
    assert mock_push.called
    # Second call should be for the client
    recipient_ids = [c.kwargs["user_id"] for c in mock_push.call_args_list]
    assert client_user.id in recipient_ids


# ---------------------------------------------------------------------------
# 4. worker_check_in → client notified when requirement transitions to IN_PROGRESS
# ---------------------------------------------------------------------------

@patch("app.api.worker_attendance._validate_selfie")
@patch("app.api.worker_attendance.send_push_to_user")
def test_worker_check_in_notifies_client_on_first_check_in(
    mock_push, mock_selfie,
    client, db, worker_user, client_user,
    notif_client_profile, notif_worker_profile,
    workers_assigned_requirement, active_assignment,
):
    mock_selfie.return_value = None  # bypass selfie/liveness check
    headers = _worker_headers(db, worker_user)
    resp = client.post(
        f"{BASE}/worker/attendance/check-in",
        json={
            "assignment_id": active_assignment.id,
            "latitude": 13.0827,
            "longitude": 80.2707,
            "selfie_url": "https://example.test/check-in.jpg",
        },
        headers=headers,
    )
    assert resp.status_code == 200, resp.json()
    assert mock_push.called
    recipient_ids = [c.kwargs["user_id"] for c in mock_push.call_args_list]
    assert client_user.id in recipient_ids


# ---------------------------------------------------------------------------
# 5. create_client_requirement → all admins notified
# ---------------------------------------------------------------------------

@patch("app.api.client_requirements.enqueue_push_to_user")
def test_create_client_requirement_notifies_admins(
    mock_push, client, db, client_user, admin_user, notif_client_profile
):
    headers = _client_headers(db, client_user)
    resp = client.post(
        f"{BASE}/client/requirements",
        json={
            "category": "Security",
            "number_of_workers": 2,
            "work_location": "Main Gate",
            "city": "Chennai",
            "state": "Tamil Nadu",
            "start_date": str(date.today() + timedelta(days=1)),
            "duration_days": 5,
        },
        headers=headers,
    )
    assert resp.status_code == 200, resp.json()
    assert mock_push.called
    recipient_ids = [c.kwargs["user_id"] for c in mock_push.call_args_list]
    assert admin_user.id in recipient_ids


# ---------------------------------------------------------------------------
# 6. decide_quote approve → admins notified
# ---------------------------------------------------------------------------

@patch("app.api.client_requirements.enqueue_push_to_user")
def test_decide_quote_approve_notifies_admins(
    mock_push, client, db, client_user, admin_user,
    notif_client_profile, submitted_requirement, sent_quote,
):
    headers = _client_headers(db, client_user)
    resp = client.post(
        f"{BASE}/client/requirements/{submitted_requirement.id}/quote-decision",
        json={"action": "approve"},
        headers=headers,
    )
    assert resp.status_code == 200, resp.json()
    assert mock_push.called
    recipient_ids = [c.kwargs["user_id"] for c in mock_push.call_args_list]
    assert admin_user.id in recipient_ids
    # Title should mention "approved"
    titles = [c.kwargs["title"] for c in mock_push.call_args_list]
    assert any("approved" in t.lower() for t in titles)


# ---------------------------------------------------------------------------
# 7. decide_quote reject → admins notified
# ---------------------------------------------------------------------------

@patch("app.api.client_requirements.enqueue_push_to_user")
def test_decide_quote_reject_notifies_admins(
    mock_push, client, db, client_user, admin_user,
    notif_client_profile, submitted_requirement, sent_quote,
):
    headers = _client_headers(db, client_user)
    resp = client.post(
        f"{BASE}/client/requirements/{submitted_requirement.id}/quote-decision",
        json={"action": "reject"},
        headers=headers,
    )
    assert resp.status_code == 200, resp.json()
    assert mock_push.called
    recipient_ids = [c.kwargs["user_id"] for c in mock_push.call_args_list]
    assert admin_user.id in recipient_ids
    titles = [c.kwargs["title"] for c in mock_push.call_args_list]
    assert any("rejected" in t.lower() for t in titles)


# ---------------------------------------------------------------------------
# 8. decide_quote extension approve → workers notified
# ---------------------------------------------------------------------------

@patch("app.api.client_requirements.enqueue_push_to_user")
def test_decide_extension_quote_approve_notifies_workers(
    mock_push, client, db, client_user, worker_user,
    notif_client_profile, notif_worker_profile,
    extension_requirement, extension_assignment, extension_quote,
):
    headers = _client_headers(db, client_user)
    resp = client.post(
        f"{BASE}/client/requirements/{extension_requirement.id}/quote-decision",
        json={"action": "approve"},
        headers=headers,
    )
    assert resp.status_code == 200, resp.json()
    assert mock_push.called
    recipient_ids = [c.kwargs["user_id"] for c in mock_push.call_args_list]
    assert worker_user.id in recipient_ids


# ---------------------------------------------------------------------------
# 9. update_client_payment_status PAID → admins notified
# ---------------------------------------------------------------------------

@patch("app.api.admin_finance.enqueue_push_to_user")
def test_update_payment_status_paid_notifies_admins(
    mock_push, client, db, admin_user, pending_client_payment
):
    headers = _admin_headers(db, admin_user)
    resp = client.patch(
        f"{BASE}/admin/finance/client-payments/{pending_client_payment.id}/status",
        json={"payment_status": ClientPaymentStatus.PAID.value},
        headers=headers,
    )
    assert resp.status_code == 200, resp.json()
    assert mock_push.called
    recipient_ids = [c.kwargs["user_id"] for c in mock_push.call_args_list]
    assert admin_user.id in recipient_ids


# ---------------------------------------------------------------------------
# 10. decline_assignment → admins notified
# ---------------------------------------------------------------------------

@patch("app.api.worker_assignments.enqueue_push_to_user")
def test_decline_assignment_notifies_admins(
    mock_push, client, db, worker_user, admin_user,
    notif_worker_profile, assigned_assignment_for_decline,
):
    headers = _worker_headers(db, worker_user)
    resp = client.post(
        f"{BASE}/worker/assignments/{assigned_assignment_for_decline.id}/decline",
        headers=headers,
    )
    assert resp.status_code == 200, resp.json()
    assert mock_push.called
    recipient_ids = [c.kwargs["user_id"] for c in mock_push.call_args_list]
    assert admin_user.id in recipient_ids


# ---------------------------------------------------------------------------
# 11. correct_attendance_record NO_SHOW → worker notified
# ---------------------------------------------------------------------------

@patch("app.api.admin_attendance.enqueue_push_to_user")
def test_correct_attendance_no_show_notifies_worker(
    mock_push, client, db, admin_user, worker_user,
    notif_worker_profile, attendance_for_correction,
):
    headers = _admin_headers(db, admin_user)
    resp = client.patch(
        f"{BASE}/admin/attendance/{attendance_for_correction.id}",
        json={"status": AttendanceStatus.NO_SHOW.value, "notes": "Worker did not report."},
        headers=headers,
    )
    assert resp.status_code == 200, resp.json()
    assert mock_push.called
    recipient_ids = [c.kwargs["user_id"] for c in mock_push.call_args_list]
    assert worker_user.id in recipient_ids
    titles = [c.kwargs["title"] for c in mock_push.call_args_list]
    assert any("no-show" in t.lower() for t in titles)
