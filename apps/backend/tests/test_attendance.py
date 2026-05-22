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
        status=RequirementStatus.ASSIGNED.value,
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
        rows = listing.json()["data"]
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

    def test_check_out_requires_open_check_in(self, client, worker_headers, assignment):
        response = client.post(
            f"{BASE}/worker/attendance/check-out",
            json=check_out_payload(assignment.id),
            headers=worker_headers,
        )
        assert response.status_code == 400
        assert "no open check-in" in response.json()["message"].lower()

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
