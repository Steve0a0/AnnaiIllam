import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies.roles import require_role
from app.core.attendance_constants import AttendanceStatus
from app.core.roles import UserRole
from app.db.deps import get_db
from app.models.user import User
from app.repositories.assignment_repository import get_assignment_by_id
from app.repositories.attendance_repository import (
    get_attendance_by_id,
    get_attendance_for_assignment,
)
from app.repositories.payroll_repository import get_locked_payroll_run_for_assignment_date
from app.schemas.attendance import AttendanceCorrectionSchema
from app.utils.audit import audit_event
from app.utils.response import success_response

router = APIRouter(prefix="/admin/attendance", tags=["Admin Attendance"])
security_logger = logging.getLogger("annai_illam_security")


@router.get("/assignment/{assignment_id}")
def list_attendance_for_assignment(
    assignment_id: int,
    current_user: User = Depends(require_role(UserRole.ADMIN.value)),
    db: Session = Depends(get_db),
):
    assignment = get_assignment_by_id(db, assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    records = get_attendance_for_assignment(db, assignment_id)

    data = [
        {
            "id": item.id,
            "worker_profile_id": item.worker_profile_id,
            "attendance_date": str(item.attendance_date),
            "status": item.status,
            "check_in_time": item.check_in_time.isoformat() if item.check_in_time else None,
            "check_out_time": item.check_out_time.isoformat() if item.check_out_time else None,
            "notes": item.notes,
        }
        for item in records
    ]

    return success_response("Attendance records fetched successfully", data)


@router.patch("/{attendance_id}")
def correct_attendance_record(
    attendance_id: int,
    payload: AttendanceCorrectionSchema,
    current_user: User = Depends(require_role(UserRole.ADMIN.value)),
    db: Session = Depends(get_db),
):
    attendance = get_attendance_by_id(db, attendance_id)
    if not attendance:
        raise HTTPException(status_code=404, detail="Attendance record not found")

    locked_payroll_run = get_locked_payroll_run_for_assignment_date(
        db=db,
        assignment_id=attendance.assignment_id,
        attendance_date=attendance.attendance_date,
    )
    if locked_payroll_run:
        security_logger.warning(
            "Blocked attendance correction for locked payroll period | attendance_id=%s | payroll_run_id=%s | admin_user_id=%s",
            attendance.id,
            locked_payroll_run.id,
            current_user.id,
        )
        audit_event(
            "locked_payroll_attendance_correction_blocked",
            {
                "attendance_id": attendance.id,
                "assignment_id": attendance.assignment_id,
                "payroll_run_id": locked_payroll_run.id,
                "admin_user_id": current_user.id,
            },
        )
        raise HTTPException(status_code=400, detail="Attendance is inside a locked payroll period")

    allowed_statuses = {
        AttendanceStatus.PRESENT.value,
        AttendanceStatus.ABSENT.value,
        AttendanceStatus.HALF_DAY.value,
        AttendanceStatus.LATE.value,
        AttendanceStatus.APPROVED.value,
        AttendanceStatus.CORRECTED.value,
    }

    if payload.status not in allowed_statuses:
        raise HTTPException(status_code=400, detail="Invalid attendance status")

    old_status = attendance.status
    attendance.status = payload.status
    if payload.notes is not None:
        attendance.notes = payload.notes
    attendance.marked_by_user_id = current_user.id

    db.commit()

    audit_event(
        "attendance_corrected",
        {
            "attendance_id": attendance.id,
            "old_status": old_status,
            "new_status": attendance.status,
            "admin_user_id": current_user.id,
        },
    )

    return success_response(
        "Attendance corrected successfully",
        {
            "attendance_id": attendance.id,
            "status": attendance.status,
        },
    )
