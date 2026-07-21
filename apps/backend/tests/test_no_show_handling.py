"""Integration coverage for Feature 4 — No-Show / Absent Worker Handling.

Covered scenarios:
  1. Worker with accepted assignment on in_progress requirement, no check-in
     today → flag_no_shows() creates no_show attendance record and notifies admins
  2. Worker who already checked in today → scheduler does NOT flag them
  3. Worker on a completed requirement → scheduler ignores them
  4. Worker on an in_progress requirement whose date window has ended →
     scheduler ignores them (past end_date)
  5. Admin marks a no_show record as excused via PATCH /admin/attendance/{id}
  6. Worker with accepted assignment on a not-yet-started requirement (start_date
     in the future) → scheduler ignores them
"""

from datetime import datetime, time, timedelta
from unittest.mock import patch

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app.core.assignment_constants import AssignmentStatus
from app.core.attendance_constants import AttendanceStatus
from app.core.config import settings
from app.core.statuses import RequirementStatus
from app.core.scheduler import flag_no_shows
from app.models.assignment import Assignment
from app.models.attendance import Attendance
from app.models.client_profile import ClientProfile
from app.models.requirement import Requirement
from app.models.user import User
from app.models.worker_profile import WorkerProfile
from app.services.token_service import build_token_pair
from app.utils.time import IST, business_date

BASE = "/api/v1"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def client_profile(db, client_user):
    profile = ClientProfile(
        user_id=client_user.id,
        client_type="company",
        company_name="NoShow Co",
        contact_name="Priya",
        city="Chennai",
        state="Tamil Nadu",
        address="T Nagar",
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


def _make_worker(db, phone: str, email: str) -> tuple:
    user = User(
        phone=phone,
        email=email,
        role="worker",
        is_active=True,
        is_phone_verified=True,
    )
    db.add(user)
    db.flush()
    profile = WorkerProfile(
        user_id=user.id,
        full_name=f"Worker {phone[-4:]}",
        category="Security",
        city="Chennai",
        state="Tamil Nadu",
        is_available=False,  # already assigned
        verification_status="approved",
    )
    db.add(profile)
    db.flush()
    return user, profile


def _business_time(hour: int, minute: int = 0) -> datetime:
    return datetime.combine(business_date(), time(hour, minute), tzinfo=IST)


def _make_requirement(
    db,
    client_profile,
    client_user,
    status: str,
    start_offset_days: int = -1,
    duration_days: int = 5,
    shift_details: str | None = "09:00-18:00",
) -> Requirement:
    req = Requirement(
        client_id=client_profile.id,
        category="Security",
        number_of_workers=1,
        work_location="Gate 1",
        city="Chennai",
        state="Tamil Nadu",
        start_date=business_date() + timedelta(days=start_offset_days),
        duration_days=duration_days,
        shift_details=shift_details,
        status=status,
        created_by_user_id=client_user.id,
    )
    db.add(req)
    db.flush()
    return req


def _make_assignment(db, requirement, worker_profile, admin_user, status: str) -> Assignment:
    asgn = Assignment(
        requirement_id=requirement.id,
        worker_profile_id=worker_profile.id,
        assigned_by_user_id=admin_user.id,
        status=status,
    )
    db.add(asgn)
    db.flush()
    return asgn


@pytest.fixture
def admin_headers(db, admin_user):
    access_token, _ = build_token_pair(
        db,
        user_id=admin_user.id,
        subject=admin_user.email,
        role=admin_user.role,
    )
    return {"Authorization": f"Bearer {access_token}"}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestFlagNoShows:
    @patch("app.core.scheduler.send_push_to_user")
    def test_no_checkin_today_creates_no_show_record(self, mock_push, db, client_user, client_profile, admin_user):
        """Worker with accepted assignment on in_progress requirement and no attendance → flagged."""
        _, wp = _make_worker(db, "9200000011", "noshow-w1@test.com")
        req = _make_requirement(db, client_profile, client_user, RequirementStatus.IN_PROGRESS.value)
        asgn = _make_assignment(db, req, wp, admin_user, AssignmentStatus.ACCEPTED.value)
        db.commit()

        result = flag_no_shows(db, now=_business_time(11))

        assert result["flagged_no_shows"] == 1

        db.expire_all()
        attendance = db.execute(
            __import__("sqlalchemy").select(Attendance).where(
                Attendance.assignment_id == asgn.id,
                Attendance.attendance_date == business_date(),
            )
        ).scalar_one_or_none()
        assert attendance is not None
        assert attendance.status == AttendanceStatus.NO_SHOW.value
        assert attendance.notes == "Auto-flagged: no check-in recorded"

        # Admin notified
        assert mock_push.call_count >= 1

    @patch("app.core.scheduler.send_push_to_user")
    def test_active_assignment_also_flagged(self, mock_push, db, client_user, client_profile, admin_user):
        """Worker with active (not just accepted) assignment is also flagged."""
        _, wp = _make_worker(db, "9200000012", "noshow-w2@test.com")
        req = _make_requirement(db, client_profile, client_user, RequirementStatus.IN_PROGRESS.value)
        asgn = _make_assignment(db, req, wp, admin_user, AssignmentStatus.ACTIVE.value)
        db.commit()

        result = flag_no_shows(db, now=_business_time(11))

        assert result["flagged_no_shows"] == 1
        db.expire_all()
        attendance = db.execute(
            __import__("sqlalchemy").select(Attendance).where(
                Attendance.assignment_id == asgn.id,
            )
        ).scalar_one_or_none()
        assert attendance is not None
        assert attendance.status == AttendanceStatus.NO_SHOW.value

    @patch("app.core.scheduler.send_push_to_user")
    def test_worker_who_checked_in_is_not_flagged(self, mock_push, db, client_user, client_profile, admin_user):
        """Worker with an existing attendance record today is not flagged."""
        _, wp = _make_worker(db, "9200000013", "noshow-w3@test.com")
        req = _make_requirement(db, client_profile, client_user, RequirementStatus.IN_PROGRESS.value)
        asgn = _make_assignment(db, req, wp, admin_user, AssignmentStatus.ACCEPTED.value)

        # Already has attendance for today
        existing_attendance = Attendance(
            assignment_id=asgn.id,
            worker_profile_id=wp.id,
            attendance_date=business_date(),
            status=AttendanceStatus.PRESENT.value,
        )
        db.add(existing_attendance)
        db.commit()

        result = flag_no_shows(db, now=_business_time(11))

        assert result["flagged_no_shows"] == 0

    @patch("app.core.scheduler.send_push_to_user")
    def test_completed_requirement_is_ignored(self, mock_push, db, client_user, client_profile, admin_user):
        """Workers on completed requirements are not flagged."""
        _, wp = _make_worker(db, "9200000014", "noshow-w4@test.com")
        req = _make_requirement(db, client_profile, client_user, RequirementStatus.COMPLETED.value)
        _make_assignment(db, req, wp, admin_user, AssignmentStatus.ACCEPTED.value)
        db.commit()

        result = flag_no_shows(db, now=_business_time(11))

        assert result["flagged_no_shows"] == 0

    @patch("app.core.scheduler.send_push_to_user")
    def test_requirement_past_end_date_is_ignored(self, mock_push, db, client_user, client_profile, admin_user):
        """In_progress requirement whose end_date has already passed is not flagged."""
        _, wp = _make_worker(db, "9200000015", "noshow-w5@test.com")
        # Start 10 days ago, duration 5 → end_date = 6 days ago (past)
        req = _make_requirement(
            db, client_profile, client_user, RequirementStatus.IN_PROGRESS.value,
            start_offset_days=-10, duration_days=5,
        )
        _make_assignment(db, req, wp, admin_user, AssignmentStatus.ACCEPTED.value)
        db.commit()

        result = flag_no_shows(db, now=_business_time(11))

        assert result["flagged_no_shows"] == 0

    @patch("app.core.scheduler.send_push_to_user")
    def test_future_start_date_requirement_is_ignored(self, mock_push, db, client_user, client_profile, admin_user):
        """Requirements that haven't started yet are not flagged."""
        _, wp = _make_worker(db, "9200000016", "noshow-w6@test.com")
        req = _make_requirement(
            db, client_profile, client_user, RequirementStatus.IN_PROGRESS.value,
            start_offset_days=3,  # starts in 3 days
        )
        _make_assignment(db, req, wp, admin_user, AssignmentStatus.ACCEPTED.value)
        db.commit()

        result = flag_no_shows(db, now=_business_time(11))

        assert result["flagged_no_shows"] == 0

    @patch("app.core.scheduler.send_push_to_user")
    def test_second_run_does_not_duplicate_no_show(self, mock_push, db, client_user, client_profile, admin_user):
        """Running flag_no_shows() twice on the same day must not create duplicate records."""
        _, wp = _make_worker(db, "9200000017", "noshow-w7@test.com")
        req = _make_requirement(db, client_profile, client_user, RequirementStatus.IN_PROGRESS.value)
        asgn = _make_assignment(db, req, wp, admin_user, AssignmentStatus.ACCEPTED.value)
        db.commit()

        flag_no_shows(db, now=_business_time(11))
        result2 = flag_no_shows(db, now=_business_time(11))

        assert result2["flagged_no_shows"] == 0  # already existed, not duplicated

        count = db.execute(
            select(func.count(Attendance.id)).where(Attendance.assignment_id == asgn.id)
        ).scalar_one()
        assert count == 1

    @patch("app.core.scheduler.send_push_to_user")
    def test_early_morning_deploy_does_not_flag_workers(
        self, mock_push, db, client_user, client_profile, admin_user
    ):
        _, wp = _make_worker(db, "9200000018", "noshow-w8@test.com")
        req = _make_requirement(
            db,
            client_profile,
            client_user,
            RequirementStatus.IN_PROGRESS.value,
            shift_details="Day 09:00-18:00",
        )
        _make_assignment(db, req, wp, admin_user, AssignmentStatus.ACTIVE.value)
        db.commit()

        result = flag_no_shows(db, now=_business_time(6))

        assert result["flagged_no_shows"] == 0
        mock_push.assert_not_called()

    @patch("app.core.scheduler.send_push_to_user")
    def test_worker_is_not_flagged_until_grace_period_expires(
        self, mock_push, db, client_user, client_profile, admin_user
    ):
        _, wp = _make_worker(db, "9200000019", "noshow-w9@test.com")
        req = _make_requirement(db, client_profile, client_user, RequirementStatus.IN_PROGRESS.value)
        _make_assignment(db, req, wp, admin_user, AssignmentStatus.ACCEPTED.value)
        db.commit()

        before_grace = flag_no_shows(db, now=_business_time(9, 59))
        after_grace = flag_no_shows(db, now=_business_time(10))

        assert before_grace["flagged_no_shows"] == 0
        assert after_grace["flagged_no_shows"] == 1
        assert mock_push.call_count >= 1

    @patch("app.core.scheduler.send_push_to_user")
    def test_configurable_grace_period_is_enforced(
        self, mock_push, db, client_user, client_profile, admin_user, monkeypatch
    ):
        monkeypatch.setattr(settings, "no_show_grace_period_minutes", 120)
        _, wp = _make_worker(db, "9200000020", "noshow-w10@test.com")
        req = _make_requirement(db, client_profile, client_user, RequirementStatus.IN_PROGRESS.value)
        _make_assignment(db, req, wp, admin_user, AssignmentStatus.ACTIVE.value)
        db.commit()

        result = flag_no_shows(db, now=_business_time(10, 30))

        assert result["flagged_no_shows"] == 0
        mock_push.assert_not_called()

    @pytest.mark.parametrize(
        "terminal_status",
        [AssignmentStatus.CANCELLED.value, AssignmentStatus.REPLACED.value],
    )
    @patch("app.core.scheduler.send_push_to_user")
    def test_cancelled_and_replaced_assignments_are_ignored(
        self,
        mock_push,
        terminal_status,
        db,
        client_user,
        client_profile,
        admin_user,
    ):
        phone_suffix = "21" if terminal_status == AssignmentStatus.CANCELLED.value else "22"
        _, wp = _make_worker(
            db,
            f"92000000{phone_suffix}",
            f"noshow-terminal-{terminal_status}@test.com",
        )
        req = _make_requirement(db, client_profile, client_user, RequirementStatus.IN_PROGRESS.value)
        _make_assignment(db, req, wp, admin_user, terminal_status)
        db.commit()

        result = flag_no_shows(db, now=_business_time(11))

        assert result["flagged_no_shows"] == 0
        mock_push.assert_not_called()

    @patch("app.core.scheduler.send_push_to_user")
    def test_missing_shift_start_fails_safe(
        self, mock_push, db, client_user, client_profile, admin_user
    ):
        _, wp = _make_worker(db, "9200000023", "noshow-w23@test.com")
        req = _make_requirement(
            db,
            client_profile,
            client_user,
            RequirementStatus.IN_PROGRESS.value,
            shift_details="Day shift",
        )
        _make_assignment(db, req, wp, admin_user, AssignmentStatus.ACTIVE.value)
        db.commit()

        result = flag_no_shows(db, now=_business_time(11))

        assert result["flagged_no_shows"] == 0
        mock_push.assert_not_called()

    def test_database_rejects_duplicate_assignment_date(
        self, db, client_user, client_profile, admin_user
    ):
        _, wp = _make_worker(db, "9200000024", "noshow-w24@test.com")
        req = _make_requirement(db, client_profile, client_user, RequirementStatus.IN_PROGRESS.value)
        asgn = _make_assignment(db, req, wp, admin_user, AssignmentStatus.ACTIVE.value)
        db.commit()

        first = Attendance(
            assignment_id=asgn.id,
            worker_profile_id=wp.id,
            attendance_date=business_date(),
            status=AttendanceStatus.PRESENT.value,
        )
        db.add(first)
        db.commit()

        duplicate = Attendance(
            assignment_id=asgn.id,
            worker_profile_id=wp.id,
            attendance_date=business_date(),
            status=AttendanceStatus.NO_SHOW.value,
        )
        db.add(duplicate)
        with pytest.raises(IntegrityError):
            db.flush()
        db.rollback()


class TestAdminMarkNoShowAsExcused:
    @patch("app.core.scheduler.send_push_to_user")
    def test_admin_can_mark_no_show_as_excused(
        self, mock_push, client, db, client_user, client_profile, admin_user, admin_headers
    ):
        """Admin can PATCH a no_show attendance record to excused."""
        _, wp = _make_worker(db, "9200000021", "noshow-w21@test.com")
        req = _make_requirement(db, client_profile, client_user, RequirementStatus.IN_PROGRESS.value)
        asgn = _make_assignment(db, req, wp, admin_user, AssignmentStatus.ACCEPTED.value)
        db.commit()

        # Create no_show record directly (simulating what the scheduler does)
        no_show = Attendance(
            assignment_id=asgn.id,
            worker_profile_id=wp.id,
            attendance_date=business_date(),
            status=AttendanceStatus.NO_SHOW.value,
            notes="Auto-flagged: no check-in recorded",
        )
        db.add(no_show)
        db.commit()
        db.refresh(no_show)

        response = client.patch(
            f"{BASE}/admin/attendance/{no_show.id}",
            json={"status": "excused", "notes": "Worker called in sick — excused."},
            headers=admin_headers,
        )
        assert response.status_code == 200, response.json()

        db.expire_all()
        updated = db.get(Attendance, no_show.id)
        assert updated.status == AttendanceStatus.EXCUSED.value
        assert "sick" in updated.notes
