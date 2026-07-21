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


def business_date(at: datetime | None = None) -> date:
    """Return the Asia/Kolkata calendar date for a UTC timestamp.

    With no argument, returns the current business date. Naive timestamps are
    treated as UTC because application DateTime columns store naive UTC.
    """
    if at is None:
        return business_now().date()
    if at.tzinfo is None:
        at = at.replace(tzinfo=timezone.utc)
    return at.astimezone(IST).date()
