import logging
from app.utils.time import utcnow

from app.db.session import SessionLocal
from app.models.audit_log import AuditLog

audit_logger = logging.getLogger("annai_illam_audit")

SENSITIVE_KEY_PARTS = {
    "secret",
    "token",
    "password",
    "signature",
    "key",
    "authorization",
}


def _redact_value(key: str, value):
    normalized_key = key.lower()
    if any(part in normalized_key for part in SENSITIVE_KEY_PARTS):
        return "[REDACTED]"
    if isinstance(value, dict):
        return _redact_details(value)
    if isinstance(value, list):
        return [_redact_value(key, item) for item in value]
    return value


def _redact_details(details: dict) -> dict:
    return {key: _redact_value(key, value) for key, value in details.items()}


def audit_event(action: str, details: dict, *, actor_user_id: int | None = None) -> None:
    """
    Persist an audit log entry.

    Args:
        action: Short machine-readable event name, e.g. "worker_approved".
        details: Arbitrary context dict. Sensitive values are auto-redacted.
        actor_user_id: The user who performed the action (if known). Always
            pass this from route handlers so the audit trail is traceable.
    """
    if actor_user_id is not None:
        details = {**details, "actor_user_id": actor_user_id}

    redacted_details = _redact_details(details)
    audit_logger.info(
        "AUDIT | timestamp=%s | action=%s | details=%s",
        utcnow().isoformat(),
        action,
        redacted_details,
    )
    try:
        db = SessionLocal()
        db.add(AuditLog(action=action, details=redacted_details))
        db.commit()
    except Exception:
        audit_logger.exception("Failed to persist audit event")
    finally:
        try:
            db.close()
        except Exception:
            pass
