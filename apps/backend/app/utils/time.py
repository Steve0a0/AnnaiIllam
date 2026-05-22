from datetime import datetime, timezone


def utcnow() -> datetime:
    """Return the current UTC time as a naive datetime.

    Preferred over datetime.utcnow() which is deprecated in Python 3.12+.
    Returns a naive datetime (no tzinfo) for compatibility with the existing
    schema that uses timezone-unaware DateTime columns.
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)
