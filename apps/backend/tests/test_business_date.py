"""ANNAI-5: business dates must be reckoned in IST, not UTC.

These assert the conversion directly so they hold regardless of the wall clock
the suite happens to run at (the UTC-vs-IST bug only surfaces between IST
midnight and 05:30).
"""

from datetime import date, datetime, timezone

from app.services import attendance_service
from app.utils.time import business_date


def test_one_am_ist_maps_to_correct_business_day():
    # 2026-07-20 19:30 UTC == 2026-07-21 01:00 IST.
    dt = datetime(2026, 7, 20, 19, 30, tzinfo=timezone.utc)
    assert business_date(dt) == date(2026, 7, 21)


def test_utc_afternoon_stays_same_ist_day():
    # 2026-07-20 17:00 UTC == 2026-07-20 22:30 IST → still the 20th.
    dt = datetime(2026, 7, 20, 17, 0, tzinfo=timezone.utc)
    assert business_date(dt) == date(2026, 7, 20)


def test_naive_timestamp_treated_as_utc():
    # Naive datetimes (our DB columns) are UTC → same boundary behaviour.
    dt = datetime(2026, 7, 20, 20, 0)
    assert business_date(dt) == date(2026, 7, 21)


def test_ist_midnight_boundary():
    just_before = datetime(2026, 7, 20, 18, 29, 59, tzinfo=timezone.utc)
    at_midnight = datetime(2026, 7, 20, 18, 30, tzinfo=timezone.utc)

    assert business_date(just_before) == date(2026, 7, 20)
    assert business_date(at_midnight) == date(2026, 7, 21)


def test_check_in_at_one_am_ist_keeps_utc_timestamp_and_uses_ist_date(monkeypatch):
    checked_in_at_utc = datetime(2026, 7, 20, 19, 30)
    monkeypatch.setattr(attendance_service, "utcnow", lambda: checked_in_at_utc)

    attendance = attendance_service.build_checkin_attendance(
        assignment_id=1,
        worker_profile_id=2,
        marked_by_user_id=3,
    )

    assert attendance.check_in_time == checked_in_at_utc
    assert attendance.check_in_time.tzinfo is None
    assert attendance.attendance_date == date(2026, 7, 21)
