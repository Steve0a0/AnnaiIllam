from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

# The business operates in India — all "what day is it" decisions (attendance,
# no-show, payroll periods, quote expiry) must be reckoned in IST, NOT UTC.
# Reckoning in UTC flips the date at 05:30 IST, so between IST-midnight and
# 05:30 a check-in / no-show / expiry lands on the wrong calendar day.
IST = ZoneInfo("Asia/Kolkata")


def utcnow() -> datetime:
    """Return the current UTC time as a naive datetime.

    Preferred over datetime.utcnow() which is deprecated in Python 3.12+.
    Returns a naive datetime (no tzinfo) for compatibility with the existing
    schema that uses timezone-unaware DateTime columns.
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)


def business_now() -> datetime:
    """Current time in the business timezone (IST), tz-aware."""
    return datetime.now(IST)


def business_today() -> date:
    """Current business date (IST).

    Use this instead of ``date.today()`` or ``utcnow().date()`` for any
    business-day decision so the day does not flip at UTC midnight.
    """
    return business_now().date()


def to_business_date(dt: datetime) -> date:
    """Convert a UTC timestamp (naive treated as UTC) to its IST calendar date."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(IST).date()
