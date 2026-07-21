"""Periodic maintenance jobs for the standalone scheduler process.

The API never starts this loop. ``python -m app.scheduler_runner`` is the sole
runtime entry point and production must deploy exactly one scheduler replica.

Tasks registered here:
  - cleanup_expired_data  every 24 h  — purges expired OTPs and revoked tokens

Exceptions are caught and logged before the loop retries at the next interval.
"""

import asyncio
import logging
import re
from datetime import datetime, time, timedelta

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.assignment_constants import AssignmentStatus
from app.core.attendance_constants import AttendanceStatus
from app.core.roles import UserRole
from app.core.statuses import QuoteStatus, RequirementStatus, validate_requirement_transition
from app.db.session import SessionLocal
from app.models.assignment import Assignment
from app.models.attendance import Attendance
from app.models.admin_profile import AdminProfile
from app.models.client_profile import ClientProfile
from app.models.otp_code import OtpCode
from app.models.quote import Quote
from app.models.requirement import Requirement
from app.models.revoked_access_token import RevokedAccessToken
from app.models.user import User
from app.models.worker_profile import WorkerProfile
from app.services.notification_service import send_push_to_user
from app.utils.audit import audit_event
from app.utils.time import IST, business_date, business_now, utcnow
from app.core.config import settings

logger = logging.getLogger(__name__)

# How often to run cleanup (seconds).  24 h default; override in tests.
CLEANUP_INTERVAL_SECONDS = 24 * 60 * 60
NO_SHOW_ELIGIBLE_ASSIGNMENT_STATUSES = {
    AssignmentStatus.ACCEPTED.value,
    AssignmentStatus.ACTIVE.value,
}
_SHIFT_START_PATTERN = re.compile(r"(?<!\d)([01]?\d|2[0-3]):([0-5]\d)")

_last_run_at: datetime | None = None
_last_error: str | None = None


def expire_stale_quotes(db: Session) -> dict:
    """Expire all sent quotes whose valid_until date has passed.

    For each stale quote:
      - Sets quote.status = 'expired'
      - Reverts requirement.status to 'under_review' so admin can re-quote
      - Pushes a notification to the client and all active admins
      - Fires audit_event("quote_expired", ...)

    Takes a caller-supplied session so it can be called directly in tests.
    Returns {"expired_quotes": N}.
    """
    today = business_date()
    stale_quotes = db.execute(
        select(Quote)
        .where(Quote.status == QuoteStatus.SENT.value)
        .where(Quote.valid_until.is_not(None))
        .where(Quote.valid_until < today)
    ).scalars().all()

    if not stale_quotes:
        return {"expired_quotes": 0}

    admin_user_ids: list[int] = [
        row[0]
        for row in db.execute(
            select(User.id)
            .where(User.role == UserRole.ADMIN.value)
            .where(User.is_active == True)  # noqa: E712
        ).all()
    ]

    expired_count = 0
    for quote in stale_quotes:
        requirement = db.get(Requirement, quote.requirement_id)
        if not requirement:
            continue

        quote.status = QuoteStatus.EXPIRED.value

        try:
            validate_requirement_transition(requirement.status, RequirementStatus.UNDER_REVIEW.value)
            requirement.status = RequirementStatus.UNDER_REVIEW.value
        except ValueError:
            logger.warning(
                "Cannot revert requirement %d to under_review from '%s' during quote expiry",
                requirement.id,
                requirement.status,
            )

        db.flush()
        audit_event(
            "quote_expired",
            {"quote_id": quote.id, "requirement_id": requirement.id},
        )
        expired_count += 1

        # Notify client
        client_profile = db.execute(
            select(ClientProfile).where(ClientProfile.id == requirement.client_id)
        ).scalar_one_or_none()
        if client_profile:
            send_push_to_user(
                db,
                user_id=client_profile.user_id,
                title="Your quote has expired",
                body="Your quote has expired. A new quote will be sent shortly.",
                data={"screen": "JobsTab"},
            )

        # Notify all active admins
        for admin_id in admin_user_ids:
            send_push_to_user(
                db,
                user_id=admin_id,
                title="Quote expired",
                body=f"Quote for requirement REQ-{requirement.id} has expired. Please send a new quote.",
                data={"screen": "RequirementsTab"},
            )

    if expired_count > 0:
        db.commit()

    logger.info("Quote expiry task: expired %d quote(s)", expired_count)
    return {"expired_quotes": expired_count}


def check_sla_breaches(db: Session) -> dict:
    """Notify super admins of requirements that have exceeded their SLA review window.

    Scans requirements with status='submitted', sla_breach_notified_at IS NULL,
    and age > sla_hours. For each breach: sets sla_breach_notified_at, fires an
    audit event, and sends a push to every super_admin user.

    Takes a caller-supplied session so it can be called directly in tests.
    Returns {"sla_breaches": N}.
    """
    now = utcnow()
    candidates = db.execute(
        select(Requirement)
        .where(
            Requirement.status == RequirementStatus.SUBMITTED.value,
            Requirement.sla_breach_notified_at.is_(None),
        )
    ).scalars().all()

    if not candidates:
        return {"sla_breaches": 0}

    # Super admin user IDs
    super_admin_user_ids: list[int] = [
        row[0]
        for row in db.execute(
            select(User.id)
            .join(AdminProfile, AdminProfile.user_id == User.id)
            .where(
                User.role == UserRole.ADMIN.value,
                User.is_active == True,  # noqa: E712
                AdminProfile.permission_group == "super_admin",
            )
        ).all()
    ]

    breached_count = 0
    for requirement in candidates:
        age_hours = (now - requirement.created_at).total_seconds() / 3600
        if age_hours <= requirement.sla_hours:
            continue

        requirement.sla_breach_notified_at = now
        db.flush()

        audit_event(
            "sla_breach",
            {
                "requirement_id": requirement.id,
                "age_hours": round(age_hours, 1),
                "sla_hours": requirement.sla_hours,
            },
        )

        for admin_id in super_admin_user_ids:
            send_push_to_user(
                db,
                user_id=admin_id,
                title="SLA Breach",
                body=(
                    f"SLA breach: Requirement {requirement.id} has been waiting "
                    f"{int(age_hours)} hours for review"
                ),
                data={"type": "sla_breach", "requirement_id": str(requirement.id)},
            )

        breached_count += 1

    if breached_count > 0:
        db.commit()

    logger.info("SLA breach check: flagged %d requirement(s)", breached_count)
    return {"sla_breaches": breached_count}


def check_unclosed_checkins(db: Session) -> dict:
    """Alert admins about attendance records with check-in but no check-out
    after MAX_SHIFT_HOURS hours have elapsed.

    Only sends one alert per attendance record (tracked via last_alert_sent_at).
    Does NOT auto-close the shift — admin decides what to do.

    Takes a caller-supplied session so it can be called directly in tests.
    Returns {"unclosed_checkin_alerts": N}.
    """
    now = utcnow()
    today = business_date()
    cutoff = now - timedelta(hours=settings.max_shift_hours)

    candidates = db.execute(
        select(Attendance, WorkerProfile)
        .join(WorkerProfile, Attendance.worker_profile_id == WorkerProfile.id)
        .where(
            Attendance.check_in_time.is_not(None),
            Attendance.check_out_time.is_(None),
            Attendance.attendance_date == today,
            Attendance.check_in_time < cutoff,
            Attendance.last_alert_sent_at.is_(None),
        )
    ).all()

    if not candidates:
        return {"unclosed_checkin_alerts": 0}

    admin_user_ids: list[int] = [
        row[0]
        for row in db.execute(
            select(User.id)
            .where(User.role == UserRole.ADMIN.value)
            .where(User.is_active == True)  # noqa: E712
        ).all()
    ]

    alert_count = 0
    for attendance, worker_profile in candidates:
        hours_elapsed = (now - attendance.check_in_time).total_seconds() / 3600

        attendance.last_alert_sent_at = now
        db.flush()

        audit_event(
            "unclosed_checkin_alert",
            {
                "attendance_id": attendance.id,
                "worker_profile_id": attendance.worker_profile_id,
                "worker_name": worker_profile.full_name,
                "hours_elapsed": round(hours_elapsed, 1),
            },
        )

        for admin_id in admin_user_ids:
            send_push_to_user(
                db,
                user_id=admin_id,
                title="Open Shift Alert",
                body=(
                    f"Worker {worker_profile.full_name} checked in "
                    f"{int(hours_elapsed)} hours ago with no check-out recorded. "
                    "Please verify."
                ),
                data={"type": "unclosed_checkin", "attendance_id": str(attendance.id)},
            )

        alert_count += 1

    if alert_count > 0:
        db.commit()

    logger.info("Unclosed check-in check: alerted %d record(s)", alert_count)
    return {"unclosed_checkin_alerts": alert_count}


def _parse_shift_start(*shift_descriptions: str | None) -> time | None:
    """Extract the first 24-hour ``HH:MM`` value from assignment/requirement text."""
    for description in shift_descriptions:
        if not description:
            continue
        match = _SHIFT_START_PATTERN.search(description)
        if match:
            return time(hour=int(match.group(1)), minute=int(match.group(2)))
    return None


def flag_no_shows(db: Session, *, now: datetime | None = None) -> dict:
    """Create attendance records for workers who did not check in today.

    Scans all accepted/active assignments on in_progress requirements whose
    date window includes today. For each assignment with no attendance record
    for today, creates a no_show record and notifies all active admins.

    Takes a caller-supplied session so it can be called directly in tests.
    Returns {"flagged_no_shows": N}.
    """
    current_time = now or business_now()
    if current_time.tzinfo is None:
        current_time = current_time.replace(tzinfo=IST)
    else:
        current_time = current_time.astimezone(IST)
    today = business_date(current_time)

    # Load accepted/active assignments on in_progress requirements that include today.
    # End-date check is done in Python to stay DB-agnostic (no date arithmetic SQL).
    candidates = db.execute(
        select(Assignment, Requirement, WorkerProfile)
        .join(Requirement, Assignment.requirement_id == Requirement.id)
        .join(WorkerProfile, Assignment.worker_profile_id == WorkerProfile.id)
        .where(
            Assignment.status.in_(NO_SHOW_ELIGIBLE_ASSIGNMENT_STATUSES),
            Requirement.status == RequirementStatus.IN_PROGRESS.value,
            Requirement.start_date <= today,
        )
    ).all()

    admin_user_ids: list[int] = [
        row[0]
        for row in db.execute(
            select(User.id)
            .where(User.role == UserRole.ADMIN.value)
            .where(User.is_active == True)  # noqa: E712
        ).all()
    ]

    flagged_count = 0
    for assignment, requirement, worker_profile in candidates:
        # Respect assignment-specific dates when present, otherwise use the
        # requirement window. Cancelled/replaced assignments never enter the
        # eligible-status query above.
        assignment_start = assignment.start_date or requirement.start_date
        requirement_end = requirement.start_date + timedelta(
            days=requirement.duration_days - 1
        )
        assignment_end = assignment.end_date or requirement_end
        if today < assignment_start or today > assignment_end:
            continue

        shift_start = _parse_shift_start(
            assignment.assigned_shift,
            requirement.shift_details,
        )
        if shift_start is None:
            logger.warning(
                "Skipping no-show evaluation for assignment %d: no parseable shift start",
                assignment.id,
            )
            continue

        eligible_at = datetime.combine(today, shift_start, tzinfo=IST) + timedelta(
            minutes=settings.no_show_grace_period_minutes
        )
        if current_time < eligible_at:
            continue

        # Skip if an attendance record already exists for today (check-in or prior no_show)
        existing = db.execute(
            select(Attendance).where(
                Attendance.assignment_id == assignment.id,
                Attendance.attendance_date == today,
            )
        ).scalar_one_or_none()
        if existing:
            continue

        # Create no_show attendance record
        no_show = Attendance(
            assignment_id=assignment.id,
            worker_profile_id=assignment.worker_profile_id,
            attendance_date=today,
            status=AttendanceStatus.NO_SHOW.value,
            notes="Auto-flagged: no check-in recorded",
        )
        try:
            # The savepoint lets a concurrent/repeated run lose the unique-key
            # race without rolling back other scheduler work in this session.
            with db.begin_nested():
                db.add(no_show)
                db.flush()
        except IntegrityError:
            logger.info(
                "No-show already exists for assignment %d on %s",
                assignment.id,
                today,
            )
            continue

        audit_event(
            "worker_no_show_flagged",
            {
                "attendance_id": no_show.id,
                "assignment_id": assignment.id,
                "worker_profile_id": assignment.worker_profile_id,
                "requirement_id": requirement.id,
                "date": str(today),
            },
        )

        # Notify all active admins
        worker_name = worker_profile.full_name
        for admin_id in admin_user_ids:
            send_push_to_user(
                db,
                user_id=admin_id,
                title="Worker no-show",
                body=f"{worker_name} did not check in for requirement REQ-{requirement.id} today.",
                data={"screen": "AttendanceTab"},
            )

        flagged_count += 1

    if flagged_count > 0:
        db.commit()

    logger.info("No-show flagging task: flagged %d worker(s)", flagged_count)
    return {"flagged_no_shows": flagged_count}


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

    with SessionLocal() as db:
        expiry_counts = expire_stale_quotes(db)

    with SessionLocal() as db:
        no_show_counts = flag_no_shows(db)

    with SessionLocal() as db:
        sla_counts = check_sla_breaches(db)

    with SessionLocal() as db:
        unclosed_counts = check_unclosed_checkins(db)

    counts = {
        "deleted_otps": otp_result.rowcount,
        "deleted_revoked_tokens": token_result.rowcount,
        **expiry_counts,
        **no_show_counts,
        **sla_counts,
        **unclosed_counts,
    }
    audit_event("scheduled_cleanup", counts)
    _last_run_at = utcnow()
    _last_error = None
    logger.info(
        "Scheduled cleanup complete — deleted %d OTP(s), %d revoked token(s), "
        "%d expired quote(s), %d no-show(s) flagged",
        counts["deleted_otps"],
        counts["deleted_revoked_tokens"],
        counts.get("expired_quotes", 0),
        counts.get("flagged_no_shows", 0),
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


async def run_scheduler_forever() -> None:
    """Entry point for the dedicated standalone scheduler process.

    Runs the same cleanup loop the API would, but as its own process/container
    so exactly one scheduler runs regardless of API worker count.
    Blocks until cancelled (e.g. SIGTERM on `docker stop`).
    """
    await _cleanup_loop()
