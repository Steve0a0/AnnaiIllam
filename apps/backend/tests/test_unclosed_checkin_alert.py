"""Tests for Polish 6: Emergency Check-out Alert.

Covers:
1. Worker checked in 11 hours ago, no check-out → scheduler alerts admin
2. Worker checked in 11 hours ago but already has check-out → no alert
3. Scheduler runs twice → no duplicate alert sent (last_alert_sent_at set)
4. Worker checked in only 5 hours ago (within MAX_SHIFT_HOURS) → no alert
"""
from datetime import date, timedelta
from unittest.mock import patch

import pytest

from app.core.scheduler import check_unclosed_checkins
from app.models.assignment import Assignment
from app.models.attendance import Attendance
from app.models.client_profile import ClientProfile
from app.models.requirement import Requirement
from app.models.worker_profile import WorkerProfile
from app.utils.time import utcnow


# ──────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────


def make_attendance_with_checkin(
    db,
    client_user,
    admin_user,
    worker_user,
    hours_since_checkin: float,
    check_out: bool = False,
) -> Attendance:
    """Create a worker profile, requirement, assignment, and attendance record."""
    profile = ClientProfile(
        user_id=client_user.id,
        client_type="individual",
        contact_name="Alert Test Client",
        city="Chennai",
        state="Tamil Nadu",
        address="Anna Nagar",
    )
    db.add(profile)
    db.flush()

    req = Requirement(
        client_id=profile.id,
        category="Security",
        number_of_workers=1,
        work_location="Gate",
        city="Chennai",
        state="Tamil Nadu",
        start_date=date.today(),
        duration_days=3,
        status="in_progress",
        created_by_user_id=client_user.id,
    )
    db.add(req)
    db.flush()

    worker_profile = WorkerProfile(
        user_id=worker_user.id,
        full_name="Test Worker",
        category="Security",
        city="Chennai",
        state="Tamil Nadu",
        is_available=False,
    )
    db.add(worker_profile)
    db.flush()

    assignment = Assignment(
        requirement_id=req.id,
        worker_profile_id=worker_profile.id,
        assigned_by_user_id=admin_user.id,
        status="active",
    )
    db.add(assignment)
    db.flush()

    checkin_time = utcnow() - timedelta(hours=hours_since_checkin)
    attendance = Attendance(
        assignment_id=assignment.id,
        worker_profile_id=worker_profile.id,
        attendance_date=date.today(),
        status="present",
        check_in_time=checkin_time,
        check_out_time=utcnow() if check_out else None,
    )
    db.add(attendance)
    db.commit()
    db.refresh(attendance)
    return attendance


# ──────────────────────────────────────────────────────────────────
# Test 1: 11-hour check-in with no check-out → alert sent
# ──────────────────────────────────────────────────────────────────


@patch("app.core.scheduler.send_push_to_user")
def test_unclosed_checkin_alerts_admin(mock_push, db, client_user, admin_user, worker_user):
    attendance = make_attendance_with_checkin(
        db, client_user, admin_user, worker_user,
        hours_since_checkin=11, check_out=False,
    )

    result = check_unclosed_checkins(db)

    assert result["unclosed_checkin_alerts"] >= 1
    db.refresh(attendance)
    assert attendance.last_alert_sent_at is not None

    notified_user_ids = [c.kwargs.get("user_id") for c in mock_push.call_args_list]
    assert admin_user.id in notified_user_ids

    # Message should mention the worker name
    bodies = [c.kwargs.get("body", "") for c in mock_push.call_args_list]
    assert any("Test Worker" in b for b in bodies)


# ──────────────────────────────────────────────────────────────────
# Test 2: Worker already checked out → no alert
# ──────────────────────────────────────────────────────────────────


@patch("app.core.scheduler.send_push_to_user")
def test_checked_out_worker_not_alerted(mock_push, db, client_user, admin_user, worker_user):
    attendance = make_attendance_with_checkin(
        db, client_user, admin_user, worker_user,
        hours_since_checkin=11, check_out=True,
    )

    result = check_unclosed_checkins(db)

    db.refresh(attendance)
    assert attendance.last_alert_sent_at is None
    # No alert push for this attendance
    for call in mock_push.call_args_list:
        body = call.kwargs.get("body", "")
        assert "Test Worker" not in body


# ──────────────────────────────────────────────────────────────────
# Test 3: Scheduler runs twice → no duplicate alert
# ──────────────────────────────────────────────────────────────────


@patch("app.core.scheduler.send_push_to_user")
def test_second_run_no_duplicate_alert(mock_push, db, client_user, admin_user, worker_user):
    make_attendance_with_checkin(
        db, client_user, admin_user, worker_user,
        hours_since_checkin=12, check_out=False,
    )

    # First run
    result1 = check_unclosed_checkins(db)
    assert result1["unclosed_checkin_alerts"] >= 1
    first_call_count = mock_push.call_count

    # Second run — no new alert
    result2 = check_unclosed_checkins(db)
    assert result2["unclosed_checkin_alerts"] == 0
    assert mock_push.call_count == first_call_count


# ──────────────────────────────────────────────────────────────────
# Test 4: Worker checked in only 5 hours ago → no alert (within max_shift_hours)
# ──────────────────────────────────────────────────────────────────


@patch("app.core.scheduler.send_push_to_user")
def test_recent_checkin_not_alerted(mock_push, db, client_user, admin_user, worker_user):
    attendance = make_attendance_with_checkin(
        db, client_user, admin_user, worker_user,
        hours_since_checkin=5, check_out=False,
    )

    result = check_unclosed_checkins(db)

    db.refresh(attendance)
    assert attendance.last_alert_sent_at is None
    for call in mock_push.call_args_list:
        body = call.kwargs.get("body", "")
        assert "Test Worker" not in body
