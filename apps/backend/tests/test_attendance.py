"""Integration coverage for worker attendance and admin correction flow."""
from datetime import date, timedelta

import pytest

from app.core.assignment_constants import AssignmentStatus
from app.core.attendance_constants import AttendanceStatus
from app.core.payroll_constants import PayrollRunStatus
from app.core.statuses import RequirementStatus
from app.models.assignment import Assignment
from app.models.client_profile import ClientProfile
from app.models.payroll_item import PayrollItem
from app.models.payroll_run import PayrollRun
from app.models.requirement import Requirement
from app.models.user import User
from app.models.worker_profile import WorkerProfile
from app.services.token_service import build_token_pair

BASE = "/api/v1"


@pytest.fixture
def client_profile(db, client_user):
    profile = ClientProfile(
        user_id=client_user.id,
        client_type="company",
        company_name="Annam Textiles",
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
def approved_requirement(db, client_profile, client_user):
    requirement = Requirement(
        client_id=client_profile.id,
        category="Security",
        subcategory="Night Guard",
        number_of_workers=1,
        work_location="Warehouse Gate 1",
        city="Chennai",
        state="Tamil Nadu",
        start_date=date.today(),
        duration_days=5,
        shift_details="Night 20:00-06:00",
        food_required=True,
        accommodation_required=False,
        budget_amount=30000,
        notes="Report to the security supervisor.",
        site_latitude=13.0827,
        site_longitude=80.2707,
        geofence_radius_meters=500,
        status=RequirementStatus.WORKERS_ASSIGNED.value,
        created_by_user_id=client_user.id,
    )
    db.add(requirement)
    db.commit()
    db.refresh(requirement)
    return requirement


@pytest.fixture
def worker_profile(db, worker_user):
    profile = WorkerProfile(
        user_id=worker_user.id,
        full_name="Ravi Kumar",
        category="Security",
        subcategory="Night Guard",
        city="Chennai",
        state="Tamil Nadu",
        address="Velachery",
        skills="Security,Night Guard",
        available_shifts="Night",
        is_available=True,
        verification_status="approved",
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


@pytest.fixture
def other_worker_user(db):
    user = User(
        phone="9000000077",
        email="attendance-other-worker@annai-illam.test",
        role="worker",
        is_active=True,
        is_phone_verified=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def other_worker_profile(db, other_worker_user):
    profile = WorkerProfile(
        user_id=other_worker_user.id,
        full_name="Karthik Raj",
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
def assignment(db, approved_requirement, worker_profile, admin_user):
    item = Assignment(
        requirement_id=approved_requirement.id,
        worker_profile_id=worker_profile.id,
        assigned_by_user_id=admin_user.id,
        status=AssignmentStatus.ACCEPTED.value,
        assigned_role="Night Security Guard",
        assigned_shift="Night 20:00-06:00",
        salary_amount=1250,
        notes="Bring uniform and ID card.",
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@pytest.fixture
def other_assignment(db, approved_requirement, other_worker_profile, admin_user):
    item = Assignment(
        requirement_id=approved_requirement.id,
        worker_profile_id=other_worker_profile.id,
        assigned_by_user_id=admin_user.id,
        status=AssignmentStatus.ACCEPTED.value,
        assigned_role="Night Security Guard",
        assigned_shift="Night 20:00-06:00",
        salary_amount=1250,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


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


@pytest.fixture
def other_worker_headers(db, other_worker_user):
    access_token, _ = build_token_pair(
        db,
        user_id=other_worker_user.id,
        subject=other_worker_user.phone,
        role=other_worker_user.role,
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


def check_in_payload(assignment_id: int, **overrides):
    payload = {
        "assignment_id": assignment_id,
        "latitude": 13.0827,
        "longitude": 80.2707,
        "selfie_url": "https://example.test/check-in.jpg",
        "qr_code": "QR-ATTENDANCE-001",
        "notes": "Reached main gate.",
    }
    payload.update(overrides)
    return payload


def check_out_payload(assignment_id: int, **overrides):
    payload = {
        "assignment_id": assignment_id,
        "latitude": 13.0828,
        "longitude": 80.2708,
        "selfie_url": "https://example.test/check-out.jpg",
        "notes": "Shift completed.",
    }
    payload.update(overrides)
    return payload


def check_in(client, assignment_id: int, headers, **overrides):
    response = client.post(
        f"{BASE}/worker/attendance/check-in",
        json=check_in_payload(assignment_id, **overrides),
        headers=headers,
    )
    assert response.status_code == 200
    return response.json()["data"]


class TestWorkerAttendanceFlow:
    def test_worker_can_check_in_check_out_and_list_attendance(
        self,
        client,
        db,
        worker_headers,
        assignment,
        approved_requirement,
    ):
        check_in_data = check_in(client, assignment.id, worker_headers)
        assert check_in_data["assignment_id"] == assignment.id
        assert check_in_data["status"] == AttendanceStatus.PRESENT.value
        assert check_in_data["check_in_latitude"] == 13.0827
        assert check_in_data["check_in_longitude"] == 80.2707

        db.refresh(assignment)
        db.refresh(approved_requirement)
        assert assignment.status == AssignmentStatus.ACTIVE.value
        assert approved_requirement.status == RequirementStatus.IN_PROGRESS.value

        check_out = client.post(
            f"{BASE}/worker/attendance/check-out",
            json=check_out_payload(assignment.id),
            headers=worker_headers,
        )
        assert check_out.status_code == 200
        check_out_data = check_out.json()["data"]
        assert check_out_data["assignment_id"] == assignment.id
        assert check_out_data["check_out_time"] is not None
        assert check_out_data["check_out_latitude"] == 13.0828

        listing = client.get(f"{BASE}/worker/attendance", headers=worker_headers)
        assert listing.status_code == 200
        page_data = listing.json()["data"]
        assert page_data["total"] == 1
        assert page_data["page"] == 1
        rows = page_data["items"]
        assert len(rows) == 1
        assert rows[0]["assignment_id"] == assignment.id
        assert rows[0]["check_in_time"] is not None
        assert rows[0]["check_out_time"] is not None
        assert rows[0]["notes"] == "Shift completed."

    def test_check_in_rejects_outside_geofence(self, client, worker_headers, assignment):
        response = client.post(
            f"{BASE}/worker/attendance/check-in",
            json=check_in_payload(assignment.id, latitude=12.9716, longitude=77.5946),
            headers=worker_headers,
        )
        assert response.status_code == 422
        assert "job site" in response.json()["message"].lower()

    def test_check_in_requires_location_when_requirement_has_geofence(
        self,
        client,
        worker_headers,
        assignment,
    ):
        response = client.post(
            f"{BASE}/worker/attendance/check-in",
            json=check_in_payload(assignment.id, latitude=None, longitude=None),
            headers=worker_headers,
        )
        assert response.status_code == 422
        assert "location is required" in response.json()["message"].lower()

    def test_duplicate_check_in_for_same_day_is_rejected(self, client, worker_headers, assignment):
        check_in(client, assignment.id, worker_headers)

        response = client.post(
            f"{BASE}/worker/attendance/check-in",
            json=check_in_payload(assignment.id),
            headers=worker_headers,
        )
        assert response.status_code == 400
        assert "already marked" in response.json()["message"].lower()

    def test_check_out_requires_active_assignment(self, client, worker_headers, assignment):
        # Fix 12: the ACTIVE guard now fires before the open-attendance check.
        # The fixture assignment starts in ACCEPTED state so check-out is blocked early.
        response = client.post(
            f"{BASE}/worker/attendance/check-out",
            json=check_out_payload(assignment.id),
            headers=worker_headers,
        )
        assert response.status_code == 400
        assert "active" in response.json()["message"].lower()

    def test_worker_cannot_mark_attendance_for_another_workers_assignment(
        self,
        client,
        other_worker_headers,
        assignment,
        other_assignment,
    ):
        response = client.post(
            f"{BASE}/worker/attendance/check-in",
            json=check_in_payload(assignment.id),
            headers=other_worker_headers,
        )
        assert response.status_code == 403

        own_response = client.post(
            f"{BASE}/worker/attendance/check-in",
            json=check_in_payload(other_assignment.id),
            headers=other_worker_headers,
        )
        assert own_response.status_code == 200

    def test_attendance_routes_require_worker_role(self, client, admin_headers, assignment):
        response = client.post(
            f"{BASE}/worker/attendance/check-in",
            json=check_in_payload(assignment.id),
            headers=admin_headers,
        )
        assert response.status_code == 403


class TestAdminAttendanceFlow:
    def test_admin_can_list_and_correct_attendance_record(
        self,
        client,
        admin_headers,
        worker_headers,
        assignment,
    ):
        check_in_data = check_in(client, assignment.id, worker_headers)
        attendance_id = check_in_data["attendance_id"]

        records = client.get(
            f"{BASE}/admin/attendance/assignment/{assignment.id}",
            headers=admin_headers,
        )
        assert records.status_code == 200
        rows = records.json()["data"]
        assert len(rows) == 1
        assert rows[0]["id"] == attendance_id
        assert rows[0]["status"] == AttendanceStatus.PRESENT.value

        correction = client.patch(
            f"{BASE}/admin/attendance/{attendance_id}",
            json={"status": AttendanceStatus.APPROVED.value, "notes": "Verified by supervisor."},
            headers=admin_headers,
        )
        assert correction.status_code == 200
        assert correction.json()["data"]["status"] == AttendanceStatus.APPROVED.value

        updated = client.get(
            f"{BASE}/admin/attendance/assignment/{assignment.id}",
            headers=admin_headers,
        )
        assert updated.json()["data"][0]["notes"] == "Verified by supervisor."

    def test_admin_can_mark_attendance_absent(self, client, admin_headers, worker_headers, assignment):
        check_in_data = check_in(client, assignment.id, worker_headers)
        attendance_id = check_in_data["attendance_id"]

        response = client.patch(
            f"{BASE}/admin/attendance/{attendance_id}",
            json={"status": AttendanceStatus.ABSENT.value, "notes": "No-show confirmed."},
            headers=admin_headers,
        )
        assert response.status_code == 200
        assert response.json()["data"]["status"] == AttendanceStatus.ABSENT.value

    def test_invalid_admin_correction_status_is_rejected(
        self,
        client,
        admin_headers,
        worker_headers,
        assignment,
    ):
        check_in_data = check_in(client, assignment.id, worker_headers)

        response = client.patch(
            f"{BASE}/admin/attendance/{check_in_data['attendance_id']}",
            json={"status": "unknown", "notes": "Bad status."},
            headers=admin_headers,
        )
        assert response.status_code == 400
        assert "invalid attendance status" in response.json()["message"].lower()

    def test_admin_correction_is_blocked_for_locked_payroll_period(
        self,
        client,
        db,
        admin_headers,
        worker_headers,
        assignment,
        worker_profile,
        admin_user,
    ):
        check_in_data = check_in(client, assignment.id, worker_headers)
        attendance_id = check_in_data["attendance_id"]

        attendance_date = date.fromisoformat(check_in_data["attendance_date"])
        payroll_run = PayrollRun(
            period_start=attendance_date - timedelta(days=1),
            period_end=attendance_date + timedelta(days=1),
            status=PayrollRunStatus.LOCKED.value,
            notes="Locked test run.",
            created_by_user_id=admin_user.id,
        )
        db.add(payroll_run)
        db.flush()
        db.add(
            PayrollItem(
                payroll_run_id=payroll_run.id,
                assignment_id=assignment.id,
                worker_profile_id=worker_profile.id,
                gross_amount=1250,
                total_deduction_amount=0,
                net_amount=1250,
                attendance_days=1,
            )
        )
        db.commit()

        response = client.patch(
            f"{BASE}/admin/attendance/{attendance_id}",
            json={"status": AttendanceStatus.APPROVED.value, "notes": "Should be blocked."},
            headers=admin_headers,
        )
        assert response.status_code == 400
        assert "locked payroll period" in response.json()["message"].lower()

    def test_admin_attendance_routes_require_admin_role(
        self,
        client,
        worker_headers,
        assignment,
    ):
        records = client.get(
            f"{BASE}/admin/attendance/assignment/{assignment.id}",
            headers=worker_headers,
        )
        assert records.status_code == 403


# ──────────────────────────────────────────────────────────────────
# Admin Attendance List — date / requirement / status filters
# ──────────────────────────────────────────────────────────────────


class TestAdminAttendanceListFilters:
    """Cover the new date/requirement_id/status query params on GET /admin/attendance."""

    def test_list_defaults_to_today(
        self, client, admin_headers, worker_headers, assignment
    ):
        """Default call (no params) returns today's attendance."""
        check_in(client, assignment.id, worker_headers)
        response = client.get(f"{BASE}/admin/attendance", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert isinstance(data, list)
        assert any(r["assignment_id"] == assignment.id for r in data)

    def test_date_filter_returns_matching_records(
        self, client, admin_headers, worker_headers, assignment
    ):
        check_in_data = check_in(client, assignment.id, worker_headers)
        today = check_in_data["attendance_date"]
        response = client.get(
            f"{BASE}/admin/attendance",
            params={"date": today},
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert all(r["attendance_date"] == today for r in data)

    def test_date_filter_past_date_returns_empty(
        self, client, admin_headers, worker_headers, assignment
    ):
        """A date in the past (before any test data) returns no records."""
        check_in(client, assignment.id, worker_headers)
        response = client.get(
            f"{BASE}/admin/attendance",
            params={"date": "2000-01-01"},
            headers=admin_headers,
        )
        assert response.status_code == 200
        assert response.json()["data"] == []

    def test_requirement_id_filter(
        self,
        client,
        admin_headers,
        worker_headers,
        assignment,
        approved_requirement,
    ):
        check_in(client, assignment.id, worker_headers)
        response = client.get(
            f"{BASE}/admin/attendance",
            params={"requirement_id": approved_requirement.id},
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert any(r["requirement_id"] == approved_requirement.id for r in data)

    def test_requirement_id_filter_wrong_id_returns_empty(
        self, client, admin_headers, worker_headers, assignment
    ):
        check_in(client, assignment.id, worker_headers)
        response = client.get(
            f"{BASE}/admin/attendance",
            params={"requirement_id": 99999},
            headers=admin_headers,
        )
        assert response.status_code == 200
        assert response.json()["data"] == []

    def test_status_filter_present(
        self, client, admin_headers, worker_headers, assignment
    ):
        check_in(client, assignment.id, worker_headers)
        response = client.get(
            f"{BASE}/admin/attendance",
            params={"status": "present"},
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert all(r["status"] == "present" for r in data)

    def test_status_filter_approved_excludes_present(
        self, client, admin_headers, worker_headers, assignment
    ):
        check_in(client, assignment.id, worker_headers)
        response = client.get(
            f"{BASE}/admin/attendance",
            params={"status": "approved"},
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()["data"]
        # freshly checked-in record is "present", not "approved"
        assert all(r["assignment_id"] != assignment.id for r in data)

    def test_correction_updates_status(
        self, client, admin_headers, worker_headers, assignment
    ):
        check_in_data = check_in(client, assignment.id, worker_headers)
        attendance_id = check_in_data["attendance_id"]
        today = check_in_data["attendance_date"]

        correction = client.patch(
            f"{BASE}/admin/attendance/{attendance_id}",
            json={"status": "approved", "notes": "Quick verify"},
            headers=admin_headers,
        )
        assert correction.status_code == 200
        assert correction.json()["data"]["status"] == "approved"

        # Refreshed list reflects update
        refreshed = client.get(
            f"{BASE}/admin/attendance",
            params={"date": today, "status": "approved"},
            headers=admin_headers,
        )
        assert refreshed.status_code == 200
        ids = [r["id"] for r in refreshed.json()["data"]]
        assert attendance_id in ids

    def test_response_includes_requirement_id_field(
        self, client, admin_headers, worker_headers, assignment, approved_requirement
    ):
        check_in(client, assignment.id, worker_headers)
        response = client.get(f"{BASE}/admin/attendance", headers=admin_headers)
        data = response.json()["data"]
        record = next(r for r in data if r["assignment_id"] == assignment.id)
        assert "requirement_id" in record
        assert record["requirement_id"] == approved_requirement.id

    def test_non_admin_cannot_list_all_attendance(
        self, client, worker_headers
    ):
        response = client.get(f"{BASE}/admin/attendance", headers=worker_headers)
        assert response.status_code == 403


# ──────────────────────────────────────────────────────────────────
# P2-3 — Attendance Correction Stales Payroll
# ──────────────────────────────────────────────────────────────────


class TestAttendanceCorrectionStalesPayroll:
    """Attendance correction marks payroll items stale; recalculate updates amounts."""

    def _make_payroll_run(self, db, admin_user, attendance_date, status="draft"):
        run = PayrollRun(
            period_start=attendance_date - timedelta(days=1),
            period_end=attendance_date + timedelta(days=1),
            status=status,
            notes="Test run",
            created_by_user_id=admin_user.id,
        )
        db.add(run)
        db.flush()
        return run

    def _make_payroll_item(self, db, run, assignment, worker_profile, payment_status="pending"):
        item = PayrollItem(
            payroll_run_id=run.id,
            assignment_id=assignment.id,
            worker_profile_id=worker_profile.id,
            gross_amount=1250,
            total_deduction_amount=0,
            net_amount=1250,
            attendance_days=1,
        )
        item.payment_status = payment_status
        db.add(item)
        db.commit()
        db.refresh(item)
        return item

    def test_correction_with_no_payroll_returns_empty_stale_list(
        self, client, db, admin_headers, worker_headers, assignment
    ):
        check_in_data = check_in(client, assignment.id, worker_headers)
        attendance_id = check_in_data["attendance_id"]

        response = client.patch(
            f"{BASE}/admin/attendance/{attendance_id}",
            json={"status": "approved", "notes": "No payroll yet"},
            headers=admin_headers,
        )
        assert response.status_code == 200
        assert response.json()["data"]["stale_payroll_item_ids"] == []

    def test_correction_marks_covering_payroll_item_stale(
        self, client, db, admin_headers, worker_headers, assignment, worker_profile, admin_user
    ):
        check_in_data = check_in(client, assignment.id, worker_headers)
        attendance_id = check_in_data["attendance_id"]
        attendance_date = date.fromisoformat(check_in_data["attendance_date"])

        run = self._make_payroll_run(db, admin_user, attendance_date)
        item = self._make_payroll_item(db, run, assignment, worker_profile)

        response = client.patch(
            f"{BASE}/admin/attendance/{attendance_id}",
            json={"status": "approved", "notes": "Correction"},
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert item.id in data["stale_payroll_item_ids"]

        db.refresh(item)
        assert item.is_stale is True
        assert item.gross_amount == 1250  # amounts unchanged

    def test_correction_marks_paid_item_stale_without_changing_amounts(
        self, client, db, admin_headers, worker_headers, assignment, worker_profile, admin_user
    ):
        check_in_data = check_in(client, assignment.id, worker_headers)
        attendance_id = check_in_data["attendance_id"]
        attendance_date = date.fromisoformat(check_in_data["attendance_date"])

        run = self._make_payroll_run(db, admin_user, attendance_date)
        item = self._make_payroll_item(db, run, assignment, worker_profile, payment_status="paid")

        response = client.patch(
            f"{BASE}/admin/attendance/{attendance_id}",
            json={"status": "approved", "notes": "Late correction on paid item"},
            headers=admin_headers,
        )
        assert response.status_code == 200
        db.refresh(item)
        assert item.is_stale is True
        assert item.net_amount == 1250  # amounts untouched

    def test_recalculate_stale_unpaid_item_updates_amounts(
        self, client, db, admin_headers, worker_headers, assignment, worker_profile, admin_user
    ):
        check_in_data = check_in(client, assignment.id, worker_headers)
        attendance_id = check_in_data["attendance_id"]
        attendance_date = date.fromisoformat(check_in_data["attendance_date"])

        run = self._make_payroll_run(db, admin_user, attendance_date)
        item = self._make_payroll_item(db, run, assignment, worker_profile)

        # Mark stale via correction
        client.patch(
            f"{BASE}/admin/attendance/{attendance_id}",
            json={"status": "approved"},
            headers=admin_headers,
        )
        db.refresh(item)
        assert item.is_stale is True

        # Recalculate
        response = client.post(
            f"{BASE}/admin/payroll/items/{item.id}/recalculate",
            headers=admin_headers,
        )
        assert response.status_code == 200
        db.refresh(item)
        assert item.is_stale is False

    def test_recalculate_paid_item_returns_400(
        self, client, db, admin_headers, worker_headers, assignment, worker_profile, admin_user
    ):
        check_in_data = check_in(client, assignment.id, worker_headers)
        attendance_date = date.fromisoformat(check_in_data["attendance_date"])

        run = self._make_payroll_run(db, admin_user, attendance_date)
        item = self._make_payroll_item(db, run, assignment, worker_profile, payment_status="paid")
        item.is_stale = True
        db.commit()

        response = client.post(
            f"{BASE}/admin/payroll/items/{item.id}/recalculate",
            headers=admin_headers,
        )
        assert response.status_code == 400
        assert "paid" in response.json()["message"].lower()

    def test_recalculate_non_stale_item_returns_400(
        self, client, db, admin_headers, assignment, worker_profile, admin_user
    ):
        today = date.today()
        run = self._make_payroll_run(db, admin_user, today)
        item = self._make_payroll_item(db, run, assignment, worker_profile)
        assert item.is_stale is False

        response = client.post(
            f"{BASE}/admin/payroll/items/{item.id}/recalculate",
            headers=admin_headers,
        )
        assert response.status_code == 400
        assert "stale" in response.json()["message"].lower()

    def test_multiple_corrections_keep_item_stale_until_recalculated(
        self, client, db, admin_headers, worker_headers, assignment, worker_profile, admin_user
    ):
        check_in_data = check_in(client, assignment.id, worker_headers)
        attendance_id = check_in_data["attendance_id"]
        attendance_date = date.fromisoformat(check_in_data["attendance_date"])

        run = self._make_payroll_run(db, admin_user, attendance_date)
        item = self._make_payroll_item(db, run, assignment, worker_profile)

        for note in ("First correction", "Second correction"):
            client.patch(
                f"{BASE}/admin/attendance/{attendance_id}",
                json={"status": "approved", "notes": note},
                headers=admin_headers,
            )

        db.refresh(item)
        assert item.is_stale is True


# ──────────────────────────────────────────────────────────────────
# Fix 4 (P0-4) — Half-day reporting triggers in_progress lifecycle
# ──────────────────────────────────────────────────────────────────


class TestHalfDayLifecycleTrigger:
    """worker_report_half_day must activate assignment and move requirement to in_progress."""

    def test_half_day_transitions_requirement_to_in_progress(
        self,
        client,
        db,
        worker_headers,
        assignment,
        approved_requirement,
    ):
        """First half-day on a workers_assigned requirement must set in_progress."""
        response = client.post(
            f"{BASE}/worker/attendance/half-day",
            json={"assignment_id": assignment.id, "notes": "Left early, doctor visit."},
            headers=worker_headers,
        )

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["status"] == AttendanceStatus.HALF_DAY.value
        assert data["assignment_id"] == assignment.id

        db.refresh(assignment)
        db.refresh(approved_requirement)
        assert assignment.status == AssignmentStatus.ACTIVE.value
        assert approved_requirement.status == RequirementStatus.IN_PROGRESS.value

    def test_half_day_on_already_in_progress_requirement_stays_in_progress(
        self,
        client,
        db,
        worker_headers,
        assignment,
        approved_requirement,
    ):
        """Subsequent half-day when requirement is already in_progress must not regress status."""
        approved_requirement.status = RequirementStatus.IN_PROGRESS.value
        assignment.status = AssignmentStatus.ACTIVE.value
        db.commit()

        response = client.post(
            f"{BASE}/worker/attendance/half-day",
            json={"assignment_id": assignment.id},
            headers=worker_headers,
        )

        assert response.status_code == 200
        db.refresh(approved_requirement)
        assert approved_requirement.status == RequirementStatus.IN_PROGRESS.value

    def test_half_day_duplicate_for_same_day_is_rejected(
        self,
        client,
        worker_headers,
        assignment,
    ):
        """A second half-day report for the same day must be rejected."""
        client.post(
            f"{BASE}/worker/attendance/half-day",
            json={"assignment_id": assignment.id},
            headers=worker_headers,
        )

        response = client.post(
            f"{BASE}/worker/attendance/half-day",
            json={"assignment_id": assignment.id},
            headers=worker_headers,
        )

        assert response.status_code == 400
        assert "already recorded" in response.json()["message"].lower()

    def test_half_day_cannot_be_reported_for_another_workers_assignment(
        self,
        client,
        other_worker_headers,
        other_worker_profile,  # ensures profile row exists so 403 is reached
        assignment,
    ):
        """Worker must not be able to report half-day for a different worker's assignment."""
        response = client.post(
            f"{BASE}/worker/attendance/half-day",
            json={"assignment_id": assignment.id},
            headers=other_worker_headers,
        )

        assert response.status_code == 403

    def test_half_day_and_check_in_both_correctly_set_in_progress(
        self,
        client,
        db,
        worker_headers,
        other_worker_headers,
        assignment,
        other_assignment,
        approved_requirement,
    ):
        """Verify both code paths (check-in and half-day) produce in_progress independently."""
        r1 = client.post(
            f"{BASE}/worker/attendance/half-day",
            json={"assignment_id": assignment.id},
            headers=worker_headers,
        )
        assert r1.status_code == 200

        db.refresh(approved_requirement)
        assert approved_requirement.status == RequirementStatus.IN_PROGRESS.value

        r2 = client.post(
            f"{BASE}/worker/attendance/check-in",
            json={
                "assignment_id": other_assignment.id,
                "latitude": 13.0827,
                "longitude": 80.2707,
            },
            headers=other_worker_headers,
        )
        assert r2.status_code == 200

        db.refresh(approved_requirement)
        assert approved_requirement.status == RequirementStatus.IN_PROGRESS.value


# ──────────────────────────────────────────────────────────────────
# Fix 5 (P1-1) — Check-in state-machine guard
# ──────────────────────────────────────────────────────────────────


class TestCheckInStateMachineGuard:
    """worker_check_in must reject check-ins on requirements in non-transitionable states."""

    def _make_assignment_on_requirement(self, db, requirement, worker_profile, admin_user):
        item = Assignment(
            requirement_id=requirement.id,
            worker_profile_id=worker_profile.id,
            assigned_by_user_id=admin_user.id,
            status=AssignmentStatus.ACCEPTED.value,
            assigned_role="Guard",
            assigned_shift="Day",
            salary_amount=1000,
        )
        db.add(item)
        db.commit()
        db.refresh(item)
        return item

    def _make_requirement(self, db, client_profile, client_user, status):
        req = Requirement(
            client_id=client_profile.id,
            category="Security",
            number_of_workers=1,
            work_location="Gate A",
            city="Chennai",
            state="Tamil Nadu",
            start_date=date.today(),
            duration_days=5,
            site_latitude=13.0827,
            site_longitude=80.2707,
            geofence_radius_meters=500,
            status=status,
            created_by_user_id=client_user.id,
        )
        db.add(req)
        db.commit()
        db.refresh(req)
        return req

    def test_check_in_on_cancelled_requirement_returns_400(
        self,
        client,
        db,
        worker_headers,
        worker_profile,
        admin_user,
        client_profile,
        client_user,
    ):
        """A cancelled requirement must block check-in; status must not be corrupted."""
        req = self._make_requirement(
            db, client_profile, client_user, RequirementStatus.CANCELLED.value
        )
        assignment = self._make_assignment_on_requirement(db, req, worker_profile, admin_user)

        response = client.post(
            f"{BASE}/worker/attendance/check-in",
            json={"assignment_id": assignment.id, "latitude": 13.0827, "longitude": 80.2707},
            headers=worker_headers,
        )

        assert response.status_code == 400
        assert "cannot" in response.json()["message"].lower()
        db.refresh(req)
        assert req.status == RequirementStatus.CANCELLED.value

    def test_check_in_on_completed_requirement_returns_400(
        self,
        client,
        db,
        worker_headers,
        worker_profile,
        admin_user,
        client_profile,
        client_user,
    ):
        """A completed requirement must also block further check-ins."""
        req = self._make_requirement(
            db, client_profile, client_user, RequirementStatus.COMPLETED.value
        )
        assignment = self._make_assignment_on_requirement(db, req, worker_profile, admin_user)

        response = client.post(
            f"{BASE}/worker/attendance/check-in",
            json={"assignment_id": assignment.id, "latitude": 13.0827, "longitude": 80.2707},
            headers=worker_headers,
        )

        assert response.status_code == 400
        db.refresh(req)
        assert req.status == RequirementStatus.COMPLETED.value

    def test_check_in_on_workers_assigned_requirement_succeeds(
        self,
        client,
        db,
        worker_headers,
        assignment,
        approved_requirement,
    ):
        """Happy path: workers_assigned -> in_progress must still succeed after the fix."""
        response = client.post(
            f"{BASE}/worker/attendance/check-in",
            json={"assignment_id": assignment.id, "latitude": 13.0827, "longitude": 80.2707},
            headers=worker_headers,
        )

        assert response.status_code == 200
        db.refresh(approved_requirement)
        assert approved_requirement.status == RequirementStatus.IN_PROGRESS.value

    def test_second_worker_check_in_on_already_in_progress_requirement_succeeds(
        self,
        client,
        db,
        worker_headers,
        other_worker_headers,
        assignment,
        other_assignment,
        approved_requirement,
    ):
        """Worker 2 checking in after requirement is already in_progress must not be blocked."""
        client.post(
            f"{BASE}/worker/attendance/check-in",
            json={"assignment_id": assignment.id, "latitude": 13.0827, "longitude": 80.2707},
            headers=worker_headers,
        )
        db.refresh(approved_requirement)
        assert approved_requirement.status == RequirementStatus.IN_PROGRESS.value

        r2 = client.post(
            f"{BASE}/worker/attendance/check-in",
            json={"assignment_id": other_assignment.id, "latitude": 13.0827, "longitude": 80.2707},
            headers=other_worker_headers,
        )
        assert r2.status_code == 200
        db.refresh(approved_requirement)
        assert approved_requirement.status == RequirementStatus.IN_PROGRESS.value


class TestCheckOutActiveGuard:
    """Fix 12: worker_check_out must reject non-ACTIVE assignments with HTTP 400."""

    def test_check_out_fails_when_assignment_is_assigned_not_active(
        self,
        client,
        db,
        worker_headers,
        assignment,
    ):
        """Check-out on an assignment that is still 'assigned' (never checked in) must return 400."""
        assignment.status = AssignmentStatus.ASSIGNED.value
        db.commit()

        response = client.post(
            f"{BASE}/worker/attendance/check-out",
            json=check_out_payload(assignment.id),
            headers=worker_headers,
        )

        assert response.status_code == 400
        assert "active" in response.json()["message"].lower()

    def test_check_out_fails_when_assignment_is_completed(
        self,
        client,
        db,
        worker_headers,
        assignment,
    ):
        """Check-out on a 'completed' assignment must return 400."""
        assignment.status = AssignmentStatus.COMPLETED.value
        db.commit()

        response = client.post(
            f"{BASE}/worker/attendance/check-out",
            json=check_out_payload(assignment.id),
            headers=worker_headers,
        )

        assert response.status_code == 400
        assert "active" in response.json()["message"].lower()

    def test_check_out_succeeds_when_assignment_is_active(
        self,
        client,
        db,
        worker_headers,
        assignment,
        approved_requirement,
    ):
        """Check-out on a properly ACTIVE assignment (after check-in) must return 200."""
        # Check in first to create an open attendance record and put assignment in ACTIVE state
        check_in(client, assignment.id, worker_headers)

        db.refresh(assignment)
        assert assignment.status == AssignmentStatus.ACTIVE.value

        response = client.post(
            f"{BASE}/worker/attendance/check-out",
            json=check_out_payload(assignment.id),
            headers=worker_headers,
        )

        assert response.status_code == 200
