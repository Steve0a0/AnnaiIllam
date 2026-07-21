"""ANNAI-5: business dates must be reckoned in IST, not UTC.

These assert the conversion directly so they hold regardless of the wall clock
the suite happens to run at (the UTC-vs-IST bug only surfaces between IST
midnight and 05:30).
"""

from datetime import datetime, timezone

from app.utils.time import to_business_date


def test_utc_evening_maps_to_next_ist_day():
    # 2026-07-20 20:00 UTC == 2026-07-21 01:30 IST → business date is the 21st.
    dt = datetime(2026, 7, 20, 20, 0, tzinfo=timezone.utc)
    assert to_business_date(dt).isoformat() == "2026-07-21"


def test_utc_afternoon_stays_same_ist_day():
    # 2026-07-20 17:00 UTC == 2026-07-20 22:30 IST → still the 20th.
    dt = datetime(2026, 7, 20, 17, 0, tzinfo=timezone.utc)
    assert to_business_date(dt).isoformat() == "2026-07-20"


def test_naive_timestamp_treated_as_utc():
    # Naive datetimes (our DB columns) are UTC → same boundary behaviour.
    dt = datetime(2026, 7, 20, 20, 0)
    assert to_business_date(dt).isoformat() == "2026-07-21"
