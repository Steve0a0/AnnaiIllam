import secrets
from urllib.parse import urlparse

from app.utils.time import utcnow

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.dependencies.roles import require_role
from app.core.assignment_constants import AssignmentStatus
from app.core.attendance_constants import AttendanceStatus
from app.core.rate_limit import redis_client
from app.core.statuses import RequirementStatus, validate_requirement_transition
from app.core.roles import UserRole
from app.db.deps import get_db
from app.models.attendance import Attendance
from app.models.user import User
from app.repositories.assignment_repository import get_assignment_by_id
from app.repositories.attendance_repository import (
    create_attendance,
    get_attendance_for_assignment_on_date,
    get_open_attendance_for_assignment,
    get_attendance_for_worker_paginated,
)
from app.repositories.requirement_repository import get_requirement_by_id
from app.repositories.profile_repository import get_client_profile_by_id
from app.repositories.profile_repository import get_worker_profile_by_user_id
from app.schemas.attendance import CheckInSchema, CheckOutSchema
from app.services.attendance_service import build_checkin_attendance
from app.services.notification_service import send_push_to_user
from app.utils.audit import audit_event
from app.utils.geofence import haversine_distance_meters
from app.utils.response import success_response

router = APIRouter(prefix="/worker/attendance", tags=["Worker Attendance"])

_SELFIE_TOKEN_TTL = 600  # 10 minutes


def _selfie_bucket_domain() -> str:
    """Returns the configured selfie bucket domain. Extracted for easy test patching."""
    from app.core.config import settings
    return settings.selfie_bucket_domain


def _validate_selfie(selfie_token: str | None, selfie_url: str | None, worker_user_id: int) -> None:
    """Validate selfie token and URL when SELFIE_BUCKET_DOMAIN is configured.

    Raises HTTPException 422 when token is missing, 400 when invalid/expired/wrong domain.
    Is a no-op when selfie_bucket_domain is empty (dev / tests that don't need this).
    """
    bucket_domain = _selfie_bucket_domain()
    if not bucket_domain:
        return  # validation disabled

    if not selfie_token:
        raise HTTPException(status_code=422, detail="selfie_token is required")

    # Validate selfie_url domain
    _INVALID_SELFIE_MSG = "Invalid or expired selfie. Please retake your photo."
    if not selfie_url or not selfie_url.startswith("https://"):
        raise HTTPException(status_code=400, detail=_INVALID_SELFIE_MSG)
    try:
        if urlparse(selfie_url).netloc != bucket_domain:
            raise HTTPException(status_code=400, detail=_INVALID_SELFIE_MSG)
    except Exception:
        raise HTTPException(status_code=400, detail=_INVALID_SELFIE_MSG)

    # Validate and consume token from Redis (one-time use)
    key = f"selfie_token:{selfie_token}"
    stored = redis_client.get(key)
    if stored is None:
        raise HTTPException(status_code=400, detail=_INVALID_SELFIE_MSG)
    try:
        if int(stored) != worker_user_id:
            raise HTTPException(status_code=400, detail=_INVALID_SELFIE_MSG)
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail=_INVALID_SELFIE_MSG)
    redis_client.delete(key)


@router.post("/selfie-token")
def issue_selfie_token(
    current_user: User = Depends(require_role(UserRole.WORKER.value)),
):
    """Issue a one-time selfie token valid for 10 minutes.

    The worker must include this token when submitting a check-in so the backend
    can verify the selfie was captured moments before check-in (not replayed).
    """
    token = secrets.token_urlsafe(32)
    redis_client.set(f"selfie_token:{token}", str(current_user.id), ex=_SELFIE_TOKEN_TTL)
    return success_response(
        "Selfie token issued",
        {"selfie_token": token, "expires_in_seconds": _SELFIE_TOKEN_TTL},
    )


def _enforce_geofence_radius(requirement, payload) -> None:
    """Raise 422 if worker coordinates are missing or outside the job-site radius."""
    radius = requirement.geofence_radius_meters if requirement.geofence_radius_meters is not None else 2000
    if radius <= 0:
        return
    if payload.latitude is None or payload.longitude is None:
        raise HTTPException(
            status_code=422,
            detail="Location is required for this job. Please enable GPS and try again.",
        )
    distance = haversine_distance_meters(
        requirement.site_latitude,
        requirement.site_longitude,
        payload.latitude,
        payload.longitude,
    )
    if distance > radius:
        raise HTTPException(
            status_code=422,
            detail=(
                f"You are {int(distance):,}m from the job site. "
                f"Check-in is only allowed within {radius:,}m."
            ),
        )


class HalfDaySchema(BaseModel):
    assignment_id: int
    notes: str | None = None


@router.post("/check-in")
def worker_check_in(
    payload: CheckInSchema,
    current_user: User = Depends(require_role(UserRole.WORKER.value)),
    db: Session = Depends(get_db),
):
    worker_profile = get_worker_profile_by_user_id(db, current_user.id)
    if not worker_profile:
        raise HTTPException(status_code=404, detail="Worker profile not found")

    assignment = get_assignment_by_id(db, payload.assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    if assignment.worker_profile_id != worker_profile.id:
        raise HTTPException(status_code=403, detail="You cannot check in for this assignment")

    if assignment.status not in {
        AssignmentStatus.ASSIGNED.value,
        AssignmentStatus.ACCEPTED.value,
        AssignmentStatus.ACTIVE.value,
    }:
        raise HTTPException(status_code=400, detail="Assignment is not active for attendance")

    # ── Date window check ────────────────────────────────────────────────────
    today = utcnow().date()
    if assignment.start_date and today < assignment.start_date:
        raise HTTPException(
            status_code=400,
            detail=f"Assignment hasn't started yet — your shift begins on {assignment.start_date}.",
        )
    if assignment.end_date and today > assignment.end_date:
        raise HTTPException(
            status_code=400,
            detail=f"Assignment period has ended — your last day was {assignment.end_date}.",
        )
    # ────────────────────────────────────────────────────────────────────────

    # ── Geofence check ──────────────────────────────────────────────────────
    # require_geofence=True  → geofence is mandatory.
    #   · If site coordinates are missing: block with a configuration error
    #     so admins know they must set them before workers can check in.
    #   · If site coordinates are set: enforce the radius as usual.
    # require_geofence=False → legacy soft-geofence behaviour:
    #   · If site coordinates are set: still validate (existing behaviour).
    #   · If site coordinates are missing: allow check-in (no change).
    requirement = get_requirement_by_id(db, assignment.requirement_id)
    if requirement:
        if requirement.require_geofence:
            if requirement.site_latitude is None or requirement.site_longitude is None:
                raise HTTPException(
                    status_code=400,
                    detail="Job site coordinates not configured, contact your admin",
                )
            # Coords are present — fall through to shared radius enforcement below
            _enforce_geofence_radius(requirement, payload)
        else:
            # Legacy: only validate when coordinates have been set
            if requirement.site_latitude is not None and requirement.site_longitude is not None:
                _enforce_geofence_radius(requirement, payload)
    # ────────────────────────────────────────────────────────────────────────

    # ── Selfie / liveness validation ────────────────────────────────────────
    _validate_selfie(payload.selfie_token, payload.selfie_url, current_user.id)
    # ────────────────────────────────────────────────────────────────────────

    existing = get_attendance_for_assignment_on_date(db, assignment.id, today)
    if existing:
        raise HTTPException(status_code=400, detail="Attendance already marked for today")

    # Guard: first check-in activates the requirement lifecycle.
    # Validate the state-machine transition before creating any attendance records.
    if assignment.status in {AssignmentStatus.ASSIGNED.value, AssignmentStatus.ACCEPTED.value}:
        if requirement and requirement.status != RequirementStatus.IN_PROGRESS.value:
            try:
                validate_requirement_transition(
                    requirement.status, RequirementStatus.IN_PROGRESS.value
                )
            except ValueError as exc:
                raise HTTPException(
                    status_code=400,
                    detail=f"Cannot check in: {exc}",
                ) from exc

    attendance = build_checkin_attendance(
        assignment_id=assignment.id,
        worker_profile_id=worker_profile.id,
        marked_by_user_id=current_user.id,
        notes=payload.notes,
        latitude=payload.latitude,
        longitude=payload.longitude,
        selfie_url=payload.selfie_url,
        qr_code=payload.qr_code,
    )
    create_attendance(db, attendance)

    if assignment.status in {AssignmentStatus.ASSIGNED.value, AssignmentStatus.ACCEPTED.value}:
        assignment.status = AssignmentStatus.ACTIVE.value
        # requirement is already in scope from the geofence check above.
        if requirement and requirement.status != RequirementStatus.IN_PROGRESS.value:
            requirement.status = RequirementStatus.IN_PROGRESS.value
            # Notify client that their job has started
            client_profile = get_client_profile_by_id(db, requirement.client_id)
            if client_profile:
                send_push_to_user(
                    db,
                    user_id=client_profile.user_id,
                    title="Your job has started",
                    body="Workers have checked in and your staffing job is now in progress.",
                    data={"screen": "JobsTab"},
                )

    db.commit()
    db.refresh(attendance)

    audit_event(
        "attendance_checked_in",
        {
            "id": attendance.id,
            "attendance_id": attendance.id,
            "assignment_id": assignment.id,
            "worker_profile_id": worker_profile.id,
            "user_id": current_user.id,
        },
    )

    return success_response(
        "Check-in successful",
        {
            "id": attendance.id,
            "attendance_id": attendance.id,
            "assignment_id": assignment.id,
            "attendance_date": str(attendance.attendance_date),
            "status": attendance.status,
            "check_in_time": attendance.check_in_time.isoformat() if attendance.check_in_time else None,
            "check_in_latitude": attendance.check_in_latitude,
            "check_in_longitude": attendance.check_in_longitude,
            "check_in_selfie_url": attendance.check_in_selfie_url,
            "qr_code": attendance.qr_code,
        },
    )


@router.post("/check-out")
def worker_check_out(
    payload: CheckOutSchema,
    current_user: User = Depends(require_role(UserRole.WORKER.value)),
    db: Session = Depends(get_db),
):
    worker_profile = get_worker_profile_by_user_id(db, current_user.id)
    if not worker_profile:
        raise HTTPException(status_code=404, detail="Worker profile not found")

    assignment = get_assignment_by_id(db, payload.assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    if assignment.worker_profile_id != worker_profile.id:
        raise HTTPException(status_code=403, detail="You cannot check out for this assignment")

    if assignment.status != AssignmentStatus.ACTIVE.value:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot check out: assignment must be active (current status: '{assignment.status}')",
        )

    attendance = get_open_attendance_for_assignment(db, assignment.id)
    if not attendance:
        raise HTTPException(status_code=400, detail="No open check-in found for this assignment")

    if attendance.check_out_time:
        raise HTTPException(status_code=400, detail="Check-out already completed")

    attendance.check_out_time = utcnow()
    attendance.check_out_latitude = payload.latitude
    attendance.check_out_longitude = payload.longitude
    attendance.check_out_selfie_url = payload.selfie_url
    if payload.notes:
        attendance.notes = payload.notes

    db.commit()

    audit_event(
        "attendance_checked_out",
        {
            "attendance_id": attendance.id,
            "assignment_id": assignment.id,
            "worker_profile_id": worker_profile.id,
            "user_id": current_user.id,
        },
    )

    return success_response(
        "Check-out successful",
        {
            "attendance_id": attendance.id,
            "assignment_id": assignment.id,
            "attendance_date": str(attendance.attendance_date),
            "check_out_time": attendance.check_out_time.isoformat() if attendance.check_out_time else None,
            "check_out_latitude": attendance.check_out_latitude,
            "check_out_longitude": attendance.check_out_longitude,
            "check_out_selfie_url": attendance.check_out_selfie_url,
        },
    )


@router.get("")
def list_my_attendance(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(require_role(UserRole.WORKER.value)),
    db: Session = Depends(get_db),
):
    worker_profile = get_worker_profile_by_user_id(db, current_user.id)
    if not worker_profile:
        raise HTTPException(status_code=404, detail="Worker profile not found")

    records, total = get_attendance_for_worker_paginated(db, worker_profile.id, page, limit)

    data = [
        {
            "id": item.id,
            "assignment_id": item.assignment_id,
            "attendance_date": str(item.attendance_date),
            "status": item.status,
            "check_in_time": item.check_in_time.isoformat() if item.check_in_time else None,
            "check_out_time": item.check_out_time.isoformat() if item.check_out_time else None,
            "check_in_latitude": item.check_in_latitude,
            "check_in_longitude": item.check_in_longitude,
            "check_out_latitude": item.check_out_latitude,
            "check_out_longitude": item.check_out_longitude,
            "check_in_selfie_url": item.check_in_selfie_url,
            "check_out_selfie_url": item.check_out_selfie_url,
            "qr_code": item.qr_code,
            "notes": item.notes,
        }
        for item in records
    ]

    return success_response(
        "Attendance records fetched successfully",
        {
            "items": data,
            "total": total,
            "page": page,
            "limit": limit,
            "pages": (total + limit - 1) // limit,
        },
    )


@router.post("/half-day")
def worker_report_half_day(
    payload: HalfDaySchema,
    current_user: User = Depends(require_role(UserRole.WORKER.value)),
    db: Session = Depends(get_db),
):
    """Self-report a half-day for an assignment. Creates an attendance record with HALF_DAY status."""
    worker_profile = get_worker_profile_by_user_id(db, current_user.id)
    if not worker_profile:
        raise HTTPException(status_code=404, detail="Worker profile not found")

    assignment = get_assignment_by_id(db, payload.assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    if assignment.worker_profile_id != worker_profile.id:
        raise HTTPException(status_code=403, detail="You cannot report attendance for this assignment")

    today = utcnow().date()
    existing = get_attendance_for_assignment_on_date(db, assignment.id, today)
    if existing:
        raise HTTPException(status_code=400, detail="Attendance already recorded for today")

    attendance = Attendance(
        assignment_id=assignment.id,
        worker_profile_id=worker_profile.id,
        attendance_date=today,
        status=AttendanceStatus.HALF_DAY.value,
        marked_by_user_id=current_user.id,
        notes=payload.notes,
    )
    db.add(attendance)

    # Mirror the same lifecycle transition that check-in performs:
    # first half-day activates the assignment and moves the requirement to in_progress.
    if assignment.status in {AssignmentStatus.ASSIGNED.value, AssignmentStatus.ACCEPTED.value}:
        assignment.status = AssignmentStatus.ACTIVE.value
        requirement = get_requirement_by_id(db, assignment.requirement_id)
        if requirement and requirement.status == RequirementStatus.WORKERS_ASSIGNED.value:
            requirement.status = RequirementStatus.IN_PROGRESS.value

    db.commit()
    db.refresh(attendance)

    audit_event(
        "attendance_half_day",
        {
            "attendance_id": attendance.id,
            "assignment_id": assignment.id,
            "worker_profile_id": worker_profile.id,
        },
    )

    return success_response(
        "Half-day recorded successfully",
        {
            "id": attendance.id,
            "assignment_id": attendance.assignment_id,
            "attendance_date": str(attendance.attendance_date),
            "status": attendance.status,
        },
    )
