"""
Lightweight in-process scheduler.

Runs periodic maintenance tasks in an asyncio background loop.
No external dependencies — uses only asyncio + SQLAlchemy.

Tasks registered here:
  - cleanup_expired_data  every 24 h  — purges expired OTPs and revoked tokens

Failure visibility:
  - Exceptions during cleanup are caught, logged, and exposed via get_scheduler_status().
  - If the background task dies unexpectedly it is automatically restarted and a
    CRITICAL log entry is emitted so alerts fire.
  - GET /api/v1/ready reports a "scheduler" entry when the task is not alive.

Note: This in-process scheduler is appropriate for single-process deployments.
For multi-process or distributed deployments, migrate to Celery + Redis beat
(see ROADMAP.md — post-MVP) to avoid duplicate runs and get distributed visibility.
"""

import asyncio
import logging
from datetime import datetime

from sqlalchemy import delete

from app.db.session import SessionLocal
from app.models.otp_code import OtpCode
from app.models.revoked_access_token import RevokedAccessToken
from app.utils.audit import audit_event
from app.utils.time import utcnow

logger = logging.getLogger(__name__)

# How often to run cleanup (seconds).  24 h default; override in tests.
CLEANUP_INTERVAL_SECONDS = 24 * 60 * 60

# --- in-process scheduler state (readable via get_scheduler_status) -----------
_last_run_at: datetime | None = None
_last_error: str | None = None
_cleanup_task: asyncio.Task | None = None


def _run_cleanup_sync() -> dict:
    """Execute the cleanup inside a short-lived DB session. Returns row counts."""
    global _last_run_at, _last_error
    now = utcnow()
    with SessionLocal() as db:
        otp_result = db.execute(
            delete(OtpCode).where(
                (OtpCode.expires_at < now) | (OtpCode.is_used == True)  # noqa: E712
            )
        )
        token_result = db.execute(
            delete(RevokedAccessToken).where(RevokedAccessToken.expires_at < now)
        )
        db.commit()

    counts = {
        "deleted_otps": otp_result.rowcount,
        "deleted_revoked_tokens": token_result.rowcount,
    }
    audit_event("scheduled_cleanup", counts)
    _last_run_at = utcnow()
    _last_error = None
    logger.info(
        "Scheduled cleanup complete — deleted %d OTP(s) and %d revoked token(s)",
        counts["deleted_otps"],
        counts["deleted_revoked_tokens"],
    )
    return counts


async def _cleanup_loop() -> None:
    """Run cleanup immediately on startup, then repeat every CLEANUP_INTERVAL_SECONDS."""
    global _last_error
    while True:
        try:
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, _run_cleanup_sync)
        except Exception as exc:  # noqa: BLE001
            _last_error = str(exc)
            logger.exception("Scheduled cleanup failed — will retry next interval")
        await asyncio.sleep(CLEANUP_INTERVAL_SECONDS)


def _on_task_done(task: asyncio.Task) -> None:
    """Called when the cleanup task finishes for any reason.

    Normal shutdown (cancelled via stop_scheduler) is ignored.
    Any unexpected exit triggers a CRITICAL log and an automatic restart so
    background tasks never fail silently.
    """
    if task.cancelled():
        return  # normal shutdown — do nothing

    exc = task.exception()
    if exc is not None:
        logger.critical(
            "Scheduler task died with an unhandled exception — restarting: %s",
            exc,
            exc_info=exc,
        )
    else:
        logger.critical(
            "Scheduler task exited unexpectedly without an exception — restarting"
        )

    # Auto-restart so cleanup keeps running even after an unexpected crash.
    _spawn_task()


def _spawn_task() -> None:
    global _cleanup_task
    _cleanup_task = asyncio.ensure_future(_cleanup_loop())
    _cleanup_task.add_done_callback(_on_task_done)


def start_scheduler() -> None:
    """Spawn the background cleanup loop.  Call once from the lifespan startup."""
    _spawn_task()
    logger.info("Scheduler started (cleanup interval: %ds)", CLEANUP_INTERVAL_SECONDS)


def stop_scheduler() -> None:
    """Cancel the background loop.  Call from the lifespan shutdown."""
    global _cleanup_task
    if _cleanup_task and not _cleanup_task.done():
        _cleanup_task.cancel()


def get_scheduler_status() -> dict:
    """Return a snapshot of scheduler health for the /ready endpoint.

    Returns:
        alive: True if the background task is currently running.
        last_run_at: ISO timestamp of the last successful cleanup run, or None.
        last_error: String message from the most recent cleanup failure, or None.
    """
    alive = _cleanup_task is not None and not _cleanup_task.done()
    return {
        "alive": alive,
        "last_run_at": _last_run_at.isoformat() if _last_run_at else None,
        "last_error": _last_error,
    }
