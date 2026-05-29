"""Integration tests for the admin dashboard endpoints.

Covers:
  GET /admin/dashboard/summary  — aggregate stats across all domain models
  GET /admin/dashboard/alerts   — overdue complaints, missing attendance, unpaid invoices
"""
from datetime import date, timedelta

import pytest

from app.core.assignment_constants import AssignmentStatus
from app.core.attendance_constants import AttendanceStatus
from app.core.complaint_constants import ComplaintSeverity, ComplaintStatus, ComplaintType
from app.core.statuses import RequirementStatus
from app.models.assignment import Assignment
from app.models.attendance import Attendance
from app.models.client_profile import ClientProfile
from app.models.complaint import Complaint
from app.models.requirement import Requirement
from app.models.worker_profile import WorkerProfile
from app.services.token_service import build_token_pair
from app.utils.time import utcnow

BASE = "/api/v1"


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


@pytest.fixture
def client_profile(db, client_user):
    profile = ClientProfile(
        user_id=client_user.id,
        client_type="company",
        company_name="Annam Textiles",
        contact_name="Priya Raman",
        city="Chennai",
        state="Tamil Nadu",
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


@pytest.fixture
def worker_profile(db, worker_user):
    profile = WorkerProfile(
        user_id=worker_user.id,
        full_name="Ravi Kumar",
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
def submitted_requirement(db, client_profile, client_user):
    req = Requirement(
        client_id=client_profile.id,
        category="Security",
        number_of_workers=1,
        work_location="Gate 1",
        city="Chennai",
        state="Tamil Nadu",
        start_date=date.today(),
        duration_days=5,
        shift_details="Day",
        budget_amount=10000,
        status=RequirementStatus.SUBMITTED.value,
        created_by_user_id=client_user.id,
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    return req


# ──────────────────────────────────────────────────────────────────
# Dashboard Summary
# ──────────────────────────────────────────────────────────────────


class TestDashboardSummary:
    def test_summary_returns_correct_structure(self, client, admin_headers):
        response = client.get(f"{BASE}/admin/dashboard/summary", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert "requirements" in data
        assert "assignments" in data
        assert "workers" in data
        assert "complaints" in data
        assert "attendance" in data
        assert "payroll" in data
        assert "finance" in data

    def test_summary_requirements_counts(self, client, admin_headers, submitted_requirement):
        response = client.get(f"{BASE}/admin/dashboard/summary", headers=admin_headers)
        data = response.json()["data"]
        assert data["requirements"]["total"] >= 1
        assert data["requirements"]["open"] >= 1

    def test_summary_workers_counts_after_adding_worker(self, client, admin_headers, worker_profile):
        response = client.get(f"{BASE}/admin/dashboard/summary", headers=admin_headers)
        data = response.json()["data"]
        assert data["workers"]["total"] >= 1
        assert data["workers"]["available"] >= 1

    def test_summary_counts_are_non_negative(self, client, admin_headers):
        response = client.get(f"{BASE}/admin/dashboard/summary", headers=admin_headers)
        data = response.json()["data"]
        for section in data.values():
            for value in section.values():
                assert value >= 0

    def test_non_admin_cannot_access_summary(self, client, client_headers):
        response = client.get(f"{BASE}/admin/dashboard/summary", headers=client_headers)
        assert response.status_code == 403

    def test_unauthenticated_cannot_access_summary(self, client):
        response = client.get(f"{BASE}/admin/dashboard/summary")
        assert response.status_code == 401


# ──────────────────────────────────────────────────────────────────
# Dashboard Alerts
# ──────────────────────────────────────────────────────────────────


class TestDashboardAlerts:
    def test_alerts_returns_correct_structure(self, client, admin_headers):
        response = client.get(f"{BASE}/admin/dashboard/alerts", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert "overdue_complaints" in data
        assert "missing_attendance" in data
        assert "unpaid_invoices" in data

    def test_recent_open_complaint_not_in_overdue(self, client, db, admin_headers, submitted_requirement, client_user):
        complaint = Complaint(
            requirement_id=submitted_requirement.id,
            raised_by_user_id=client_user.id,
            complaint_type=ComplaintType.BEHAVIOR.value,
            severity=ComplaintSeverity.MEDIUM.value,
            description="Worker was rude to the client staff.",
            status=ComplaintStatus.OPEN.value,
        )
        db.add(complaint)
        db.commit()

        response = client.get(f"{BASE}/admin/dashboard/alerts", headers=admin_headers)
        data = response.json()["data"]
        overdue_ids = [c["id"] for c in data["overdue_complaints"]]
        assert complaint.id not in overdue_ids

    def test_very_old_open_complaint_appears_in_overdue(
        self, client, db, admin_headers, submitted_requirement, client_user
    ):
        old_time = utcnow() - timedelta(hours=200)
        complaint = Complaint(
            requirement_id=submitted_requirement.id,
            raised_by_user_id=client_user.id,
            complaint_type=ComplaintType.PERFORMANCE.value,
            severity=ComplaintSeverity.HIGH.value,
            description="Worker has been consistently underperforming all week.",
            status=ComplaintStatus.OPEN.value,
            created_at=old_time,
        )
        db.add(complaint)
        db.commit()
        db.refresh(complaint)

        response = client.get(f"{BASE}/admin/dashboard/alerts", headers=admin_headers)
        data = response.json()["data"]
        overdue_ids = [c["id"] for c in data["overdue_complaints"]]
        assert complaint.id in overdue_ids

    def test_active_assignment_without_checkin_appears_in_missing_attendance(
        self, client, db, admin_headers, client_profile, client_user, worker_profile, admin_user
    ):
        req = Requirement(
            client_id=client_profile.id,
            category="Security",
            number_of_workers=1,
            work_location="Site A",
            city="Chennai",
            state="Tamil Nadu",
            start_date=date.today(),
            duration_days=5,
            shift_details="Day",
            budget_amount=10000,
            status=RequirementStatus.IN_PROGRESS.value,
            created_by_user_id=client_user.id,
        )
        db.add(req)
        db.commit()
        db.refresh(req)

        assignment = Assignment(
            requirement_id=req.id,
            worker_profile_id=worker_profile.id,
            assigned_by_user_id=admin_user.id,
            status=AssignmentStatus.ACTIVE.value,
            assigned_role="Guard",
            assigned_shift="Day",
            salary_amount=1000,
        )
        db.add(assignment)
        db.commit()
        db.refresh(assignment)

        response = client.get(f"{BASE}/admin/dashboard/alerts", headers=admin_headers)
        data = response.json()["data"]
        missing_ids = [a["assignment_id"] for a in data["missing_attendance"]]
        assert assignment.id in missing_ids

    def test_active_assignment_with_checkin_not_in_missing_attendance(
        self, client, db, admin_headers, client_profile, client_user, worker_profile, admin_user, worker_user
    ):
        req = Requirement(
            client_id=client_profile.id,
            category="Security",
            number_of_workers=1,
            work_location="Site B",
            city="Chennai",
            state="Tamil Nadu",
            start_date=date.today(),
            duration_days=5,
            shift_details="Day",
            budget_amount=10000,
            status=RequirementStatus.IN_PROGRESS.value,
            created_by_user_id=client_user.id,
        )
        db.add(req)
        db.commit()
        db.refresh(req)

        assignment = Assignment(
            requirement_id=req.id,
            worker_profile_id=worker_profile.id,
            assigned_by_user_id=admin_user.id,
            status=AssignmentStatus.ACTIVE.value,
            assigned_role="Guard",
            assigned_shift="Day",
            salary_amount=1000,
        )
        db.add(assignment)
        db.commit()
        db.refresh(assignment)

        attendance = Attendance(
            assignment_id=assignment.id,
            worker_profile_id=worker_profile.id,
            attendance_date=utcnow().date(),
            status=AttendanceStatus.PRESENT.value,
            check_in_time=utcnow(),
            check_in_latitude=13.0827,
            check_in_longitude=80.2707,
            marked_by_user_id=worker_user.id,
        )
        db.add(attendance)
        db.commit()

        response = client.get(f"{BASE}/admin/dashboard/alerts", headers=admin_headers)
        data = response.json()["data"]
        missing_ids = [a["assignment_id"] for a in data["missing_attendance"]]
        assert assignment.id not in missing_ids

    def test_non_admin_cannot_access_alerts(self, client, client_headers):
        response = client.get(f"{BASE}/admin/dashboard/alerts", headers=client_headers)
        assert response.status_code == 403
