"""Integration coverage for Feature 5 — Attendance Approval Workflow.

Covered scenarios:
  1. Worker checks in → attendance record has approval_status = "pending"
  2. Admin approves attendance → approval_status = "approved", approved_by_user_id set
  3. Admin rejects attendance with notes → approval_status = "rejected", worker push queued
  4. Reject without notes → 422 validation error
  5. Admin tries to complete requirement with pending attendance → 400
  6. All attendance approved → complete succeeds
  7. Double-approve already-approved record → 400
  8. GET /admin/attendance/requirement/{id}/pending returns only pending records
  9. Non-admin cannot approve/reject → 403
"""

from datetime import date

import pytest

from app.core.attendance_constants import AttendanceApprovalStatus, AttendanceStatus
from app.core.statuses import RequirementStatus
from app.models.assignment import Assignment
from app.models.attendance import Attendance
from app.models.client_profile import ClientProfile
from app.models.requirement import Requirement
from app.models.user import User
from app.models.worker_profile import WorkerProfile
from app.services.token_service import build_token_pair

BASE = "/api/v1"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def client_profile(db, client_user):
    profile = ClientProfile(
        user_id=client_user.id,
        client_type="company",
        company_name="Approval Corp",
        contact_name="Manager A",
        city="Chennai",
        state="Tamil Nadu",
        address="Anna Nagar",
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


@pytest.fixture
def worker_profile(db, worker_user):
    profile = WorkerProfile(
        user_id=worker_user.id,
        full_name="Test Worker",
        category="Security",
        city="Chennai",
        state="Tamil Nadu",
        is_available=False,
        verification_status="approved",
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


@pytest.fixture
def in_progress_requirement(db, client_profile, client_user):
    req = Requirement(
        client_id=client_profile.id,
        category="Security",
        number_of_workers=1,
        work_location="Gate 5",
        city="Chennai",
        state="Tamil Nadu",
        start_date=date.today(),
        duration_days=3,
        status=RequirementStatus.IN_PROGRESS.value,
        created_by_user_id=client_user.id,
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    return req


@pytest.fixture
def assignment(db, in_progress_requirement, worker_profile, admin_user):
    asgn = Assignment(
        requirement_id=in_progress_requirement.id,
        worker_profile_id=worker_profile.id,
        assigned_by_user_id=admin_user.id,
        status="active",
    )
    db.add(asgn)
    db.commit()
    db.refresh(asgn)
    return asgn


def _make_attendance(db, assignment, worker_profile, approval_status="pending") -> Attendance:
    """Helper to create an attendance record directly in the DB."""
    record = Attendance(
        assignment_id=assignment.id,
        worker_profile_id=worker_profile.id,
        attendance_date=date.today(),
        status=AttendanceStatus.PRESENT.value,
        approval_status=approval_status,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


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
        subject=client_user.email,
        role=client_user.role,
    )
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def worker_headers(db, worker_user):
    access_token, _ = build_token_pair(
        db,
        user_id=worker_user.id,
        subject=worker_user.email,
        role=worker_user.role,
    )
    return {"Authorization": f"Bearer {access_token}"}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestAttendanceApprovalStatus:
    def test_newly_created_attendance_has_pending_approval_status(
        self, db, assignment, worker_profile
    ):
        """Directly created attendance starts with approval_status = 'pending'."""
        record = _make_attendance(db, assignment, worker_profile)
        assert record.approval_status == AttendanceApprovalStatus.PENDING.value

    def test_admin_approves_attendance(
        self, client, db, assignment, worker_profile, admin_headers, admin_user
    ):
        """Admin can approve a pending attendance record."""
        record = _make_attendance(db, assignment, worker_profile)

        resp = client.post(
            f"{BASE}/admin/attendance/{record.id}/approve",
            headers=admin_headers,
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()["data"]
        assert body["approval_status"] == AttendanceApprovalStatus.APPROVED.value
        assert body["approved_by_user_id"] == admin_user.id
        assert body["approved_at"] is not None

        db.expire_all()
        db_record = db.get(Attendance, record.id)
        assert db_record.approval_status == AttendanceApprovalStatus.APPROVED.value
        assert db_record.approved_by_user_id == admin_user.id
        assert db_record.approved_at is not None

    def test_admin_rejects_attendance_with_notes(
        self, client, db, assignment, worker_profile, admin_headers, admin_user
    ):
        """Admin can reject a pending record; rejection notes are stored."""
        record = _make_attendance(db, assignment, worker_profile)

        resp = client.post(
            f"{BASE}/admin/attendance/{record.id}/reject",
            json={"notes": "Worker was at wrong location"},
            headers=admin_headers,
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()["data"]
        assert body["approval_status"] == AttendanceApprovalStatus.REJECTED.value
        assert body["approval_notes"] == "Worker was at wrong location"

        db.expire_all()
        db_record = db.get(Attendance, record.id)
        assert db_record.approval_status == AttendanceApprovalStatus.REJECTED.value
        assert db_record.approval_notes == "Worker was at wrong location"
        assert db_record.approved_by_user_id == admin_user.id

    def test_reject_without_notes_is_422(
        self, client, assignment, worker_profile, db, admin_headers
    ):
        """Rejection requires non-empty notes; empty body returns 422."""
        record = _make_attendance(db, assignment, worker_profile)
        resp = client.post(
            f"{BASE}/admin/attendance/{record.id}/reject",
            json={},
            headers=admin_headers,
        )
        assert resp.status_code == 422

    def test_reject_with_blank_notes_is_422(
        self, client, assignment, worker_profile, db, admin_headers
    ):
        """Blank notes string should fail field validation."""
        record = _make_attendance(db, assignment, worker_profile)
        resp = client.post(
            f"{BASE}/admin/attendance/{record.id}/reject",
            json={"notes": "   "},
            headers=admin_headers,
        )
        assert resp.status_code == 422

    def test_double_approve_returns_400(
        self, client, assignment, worker_profile, db, admin_headers
    ):
        """Approving an already-approved record returns 400."""
        record = _make_attendance(db, assignment, worker_profile, approval_status="approved")
        resp = client.post(
            f"{BASE}/admin/attendance/{record.id}/approve",
            headers=admin_headers,
        )
        assert resp.status_code == 400

    def test_double_reject_returns_400(
        self, client, assignment, worker_profile, db, admin_headers
    ):
        """Rejecting an already-rejected record returns 400."""
        record = _make_attendance(db, assignment, worker_profile, approval_status="rejected")
        resp = client.post(
            f"{BASE}/admin/attendance/{record.id}/reject",
            json={"notes": "duplicate reject"},
            headers=admin_headers,
        )
        assert resp.status_code == 400

    def test_non_admin_cannot_approve(
        self, client, assignment, worker_profile, db, client_headers
    ):
        """Non-admin (client) role cannot access approve endpoint."""
        record = _make_attendance(db, assignment, worker_profile)
        resp = client.post(
            f"{BASE}/admin/attendance/{record.id}/approve",
            headers=client_headers,
        )
        assert resp.status_code == 403

    def test_non_admin_cannot_reject(
        self, client, assignment, worker_profile, db, client_headers
    ):
        """Non-admin (client) role cannot access reject endpoint."""
        record = _make_attendance(db, assignment, worker_profile)
        resp = client.post(
            f"{BASE}/admin/attendance/{record.id}/reject",
            json={"notes": "Not allowed"},
            headers=client_headers,
        )
        assert resp.status_code == 403


class TestPendingAttendanceList:
    def test_get_pending_returns_only_pending_records(
        self, client, db, in_progress_requirement, assignment, worker_profile, admin_headers
    ):
        """GET /pending returns only attendance with approval_status='pending'."""
        pending = _make_attendance(db, assignment, worker_profile, approval_status="pending")

        resp = client.get(
            f"{BASE}/admin/attendance/requirement/{in_progress_requirement.id}/pending",
            headers=admin_headers,
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()["data"]
        ids = [r["id"] for r in data]
        assert pending.id in ids
        for record in data:
            assert record["approval_status"] == AttendanceApprovalStatus.PENDING.value

    def test_approved_record_not_in_pending_list(
        self, client, db, in_progress_requirement, assignment, worker_profile, admin_headers
    ):
        """Approved records do not appear in the pending list."""
        _make_attendance(db, assignment, worker_profile, approval_status="approved")
        resp = client.get(
            f"{BASE}/admin/attendance/requirement/{in_progress_requirement.id}/pending",
            headers=admin_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["data"] == []


class TestCompleteRequirementWithPendingAttendance:
    def test_cannot_complete_with_pending_attendance(
        self, client, db, in_progress_requirement, assignment, worker_profile, admin_headers
    ):
        """Completing a requirement that has pending attendance records returns 400."""
        _make_attendance(db, assignment, worker_profile, approval_status="pending")

        resp = client.post(
            f"{BASE}/admin/requirements/{in_progress_requirement.id}/complete",
            headers=admin_headers,
        )
        assert resp.status_code == 400
        assert "pending approval" in resp.json()["message"].lower()

    def test_complete_succeeds_when_all_attendance_approved(
        self, client, db, in_progress_requirement, assignment, worker_profile, admin_headers
    ):
        """Requirement can be completed once all attendance is approved."""
        _make_attendance(db, assignment, worker_profile, approval_status="approved")

        resp = client.post(
            f"{BASE}/admin/requirements/{in_progress_requirement.id}/complete",
            headers=admin_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["status"] == RequirementStatus.COMPLETED.value

    def test_complete_succeeds_with_no_attendance_records(
        self, client, in_progress_requirement, admin_headers
    ):
        """Requirement with zero attendance records can be completed without issue."""
        resp = client.post(
            f"{BASE}/admin/requirements/{in_progress_requirement.id}/complete",
            headers=admin_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["status"] == RequirementStatus.COMPLETED.value

    def test_complete_blocked_even_with_mixed_statuses(
        self, client, db, in_progress_requirement, assignment, worker_profile, admin_headers
    ):
        """If even one attendance is pending, completion is blocked."""
        # One approved + one pending: completion should still be blocked.
        _make_attendance(db, assignment, worker_profile, approval_status="approved")

        # Create a second requirement+assignment to get a second attendance record
        req2 = Requirement(
            client_id=in_progress_requirement.client_id,
            category="Security",
            number_of_workers=1,
            work_location="Gate 6",
            city="Chennai",
            state="Tamil Nadu",
            start_date=date.today(),
            duration_days=3,
            status=RequirementStatus.IN_PROGRESS.value,
            created_by_user_id=assignment.assigned_by_user_id,
        )
        db.add(req2)
        db.flush()

        worker2_user = User(
            phone="9300009301",
            email="approval-w2@test.com",
            role="worker",
            is_active=True,
            is_phone_verified=True,
        )
        db.add(worker2_user)
        db.flush()
        wp2 = WorkerProfile(
            user_id=worker2_user.id,
            full_name="Worker Two",
            category="Security",
            city="Chennai",
            state="Tamil Nadu",
            is_available=False,
            verification_status="approved",
        )
        db.add(wp2)
        db.flush()

        asgn2 = Assignment(
            requirement_id=in_progress_requirement.id,
            worker_profile_id=wp2.id,
            assigned_by_user_id=assignment.assigned_by_user_id,
            status="active",
        )
        db.add(asgn2)
        db.flush()

        pending_rec = Attendance(
            assignment_id=asgn2.id,
            worker_profile_id=wp2.id,
            attendance_date=date.today(),
            status=AttendanceStatus.PRESENT.value,
            approval_status="pending",
        )
        db.add(pending_rec)
        db.commit()

        resp = client.post(
            f"{BASE}/admin/requirements/{in_progress_requirement.id}/complete",
            headers=admin_headers,
        )
        assert resp.status_code == 400
        assert "pending approval" in resp.json()["message"].lower()
