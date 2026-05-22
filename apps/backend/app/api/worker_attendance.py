from app.utils.time import utcnow

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.dependencies.roles import require_role
from app.core.assignment_constants import AssignmentStatus
from app.core.attendance_constants import AttendanceStatus
from app.core.statuses import RequirementStatus
from app.core.roles import UserRole
from app.db.deps import get_db
from app.models.attendance import Attendance
from app.models.user import User
from app.repositories.assignment_repository import get_assignment_by_id
from app.repositories.attendance_repository import (
    create_attendance,
    get_attendance_for_assignment_on_date,
    get_open_attendance_for_assignment,
    get_attendance_for_worker,
)
from app.repositories.requirement_repository import get_requirement_by_id
from app.repositories.profile_repository import get_worker_profile_by_user_id
from app.schemas.attendance import CheckInSchema, CheckOutSchema
from app.services.attendance_service import build_checkin_attendance
from app.utils.audit import audit_event
from app.utils.geofence import haversine_distance_meters
from app.utils.response import success_response

router = APIRouter(prefix="/worker/attendance", tags=["Worker Attendance"])


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

    # ── Geofence check ──────────────────────────────────────────────────────
    # If the requirement has GPS coordinates set, validate that the worker is
    # within geofence_radius_meters (default 2 000 m) of the job site.
    requirement = get_requirement_by_id(db, assignment.requirement_id)
    if requirement and requirement.site_latitude is not None and requirement.site_longitude is not None:
        radius = (requirement.geofence_radius_meters or 0) if requirement.geofence_radius_meters is not None else 2000
        if radius > 0:
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
    # ────────────────────────────────────────────────────────────────────────

    existing = get_attendance_for_assignment_on_date(db, assignment.id, utcnow().date())
    if existing:
        raise HTTPException(status_code=400, detail="Attendance already marked for today")

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
        requirement = get_requirement_by_id(db, assignment.requirement_id)
        if requirement:
            requirement.status = RequirementStatus.IN_PROGRESS.value

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
    current_user: User = Depends(require_role(UserRole.WORKER.value)),
    db: Session = Depends(get_db),
):
    worker_profile = get_worker_profile_by_user_id(db, current_user.id)
    if not worker_profile:
        raise HTTPException(status_code=404, detail="Worker profile not found")

    records = get_attendance_for_worker(db, worker_profile.id)

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

    return success_response("Attendance records fetched successfully", data)


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
