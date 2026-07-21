import logging
from datetime import date as date_type

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from pydantic import BaseModel, field_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies.roles import require_permission_group, require_role
from app.core.attendance_constants import AttendanceApprovalStatus, AttendanceStatus
from app.core.roles import UserRole
from app.db.deps import get_db
from app.models.assignment import Assignment
from app.models.attendance import Attendance
from app.models.user import User
from app.models.worker_profile import WorkerProfile
from app.repositories.assignment_repository import get_assignment_by_id
from app.repositories.attendance_repository import (
    get_attendance_by_id,
    get_attendance_for_assignment,
)
from app.repositories.payroll_repository import (
    get_locked_payroll_run_for_assignment_date,
    get_payroll_items_for_assignment_in_period,
)
from app.schemas.attendance import AttendanceCorrectionSchema
from app.services.notification_service import enqueue_push_to_user
from app.utils.audit import audit_event
from app.utils.response import success_response
from app.utils.time import utcnow, business_today

router = APIRouter(prefix="/admin/attendance", tags=["Admin Attendance"])
security_logger = logging.getLogger("annai_illam_security")


@router.get("")
def list_all_attendance(
    date: str | None = Query(default=None, description="Filter by date YYYY-MM-DD (defaults to today)"),
    requirement_id: int | None = Query(default=None),
    status: str | None = Query(default=None),
    limit: int = Query(default=200, ge=1, le=500),
    current_user: User = Depends(require_role(UserRole.ADMIN.value)),
    db: Session = Depends(get_db),
):
    """Return attendance records filtered by date (defaults to today), requirement, or status."""
    # Default to today when no date supplied
    effective_date = date if date else str(business_today())

    stmt = (
        select(Attendance, Assignment.requirement_id.label("req_id"))
        .join(Assignment, Attendance.assignment_id == Assignment.id)
        .order_by(Attendance.attendance_date.desc(), Attendance.created_at.desc())
        .limit(limit)
    )

    stmt = stmt.where(Attendance.attendance_date == date_type.fromisoformat(effective_date))

    if requirement_id is not None:
        stmt = stmt.where(Assignment.requirement_id == requirement_id)
    if status is not None:
        stmt = stmt.where(Attendance.status == status)

    rows = db.execute(stmt).all()

    worker_profile_ids = {row[0].worker_profile_id for row in rows}
    workers: dict[int, WorkerProfile] = {}
    if worker_profile_ids:
        for wp in db.execute(
            select(WorkerProfile).where(WorkerProfile.id.in_(worker_profile_ids))
        ).scalars().all():
            workers[wp.id] = wp

    data = [
        {
            "id": item.id,
            "assignment_id": item.assignment_id,
            "requirement_id": req_id,
            "worker_profile_id": item.worker_profile_id,
            "worker_name": workers[item.worker_profile_id].full_name if item.worker_profile_id in workers else f"Worker #{item.worker_profile_id}",
            "attendance_date": str(item.attendance_date),
            "status": item.status,
            "check_in_time": item.check_in_time.isoformat() if item.check_in_time else None,
            "check_out_time": item.check_out_time.isoformat() if item.check_out_time else None,
            "notes": item.notes,
            "approval_status": item.approval_status,
            "approval_notes": item.approval_notes,
        }
        for item, req_id in rows
    ]

    return success_response("Attendance records fetched successfully", data)


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

    worker_profile_ids = {r.worker_profile_id for r in records}
    workers: dict[int, WorkerProfile] = {}
    if worker_profile_ids:
        for wp in db.execute(
            select(WorkerProfile).where(WorkerProfile.id.in_(worker_profile_ids))
        ).scalars().all():
            workers[wp.id] = wp

    data = [
        {
            "id": item.id,
            "assignment_id": item.assignment_id,
            "worker_profile_id": item.worker_profile_id,
            "worker_name": workers[item.worker_profile_id].full_name if item.worker_profile_id in workers else f"Worker #{item.worker_profile_id}",
            "attendance_date": str(item.attendance_date),
            "status": item.status,
            "check_in_time": item.check_in_time.isoformat() if item.check_in_time else None,
            "check_out_time": item.check_out_time.isoformat() if item.check_out_time else None,
            "notes": item.notes,
            "approval_status": item.approval_status,
            "approval_notes": item.approval_notes,
        }
        for item in records
    ]

    return success_response("Attendance records fetched successfully", data)


@router.patch("/{attendance_id}")
def correct_attendance_record(
    attendance_id: int,
    payload: AttendanceCorrectionSchema,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_permission_group("super_admin")),
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
        AttendanceStatus.NO_SHOW.value,
        AttendanceStatus.EXCUSED.value,
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

    # Mark any open payroll items for this assignment/period as stale
    stale_items = get_payroll_items_for_assignment_in_period(
        db=db,
        assignment_id=attendance.assignment_id,
        attendance_date=attendance.attendance_date,
    )
    if stale_items:
        for pi in stale_items:
            pi.is_stale = True
        db.commit()
        for pi in stale_items:
            audit_event(
                "payroll_marked_stale_due_to_attendance_correction",
                {
                    "payroll_item_id": pi.id,
                    "payroll_run_id": pi.payroll_run_id,
                    "assignment_id": attendance.assignment_id,
                    "attendance_id": attendance.id,
                    "payment_status": pi.payment_status,
                    "admin_user_id": current_user.id,
                },
            )

    # Notify worker when marked as no-show
    if attendance.status == AttendanceStatus.NO_SHOW.value:
        worker_profile = db.execute(
            select(WorkerProfile).where(WorkerProfile.id == attendance.worker_profile_id)
        ).scalar_one_or_none()
        if worker_profile:
            enqueue_push_to_user(
                background_tasks,
                db,
                user_id=worker_profile.user_id,
                title="Attendance marked as no-show",
                body=f"Your attendance for {attendance.attendance_date} has been marked as a no-show. Please contact your supervisor.",
                data={"type": "no_show", "attendance_id": attendance.id, "screen": "HomeTab"},
            )

    return success_response(
        "Attendance corrected successfully",
        {
            "attendance_id": attendance.id,
            "status": attendance.status,
            "stale_payroll_item_ids": [pi.id for pi in stale_items],
        },
    )


# ---------------------------------------------------------------------------
# Attendance Approval Workflow
# ---------------------------------------------------------------------------

@router.get("/requirement/{requirement_id}/pending")
def list_pending_attendance_for_requirement(
    requirement_id: int,
    current_user: User = Depends(require_role(UserRole.ADMIN.value)),
    db: Session = Depends(get_db),
):
    """Return all attendance records with approval_status='pending' for a requirement."""
    rows = db.execute(
        select(Attendance, Assignment.requirement_id)
        .join(Assignment, Attendance.assignment_id == Assignment.id)
        .where(
            Assignment.requirement_id == requirement_id,
            Attendance.approval_status == AttendanceApprovalStatus.PENDING.value,
        )
        .order_by(Attendance.attendance_date)
    ).all()

    worker_profile_ids = {r[0].worker_profile_id for r in rows}
    workers: dict[int, WorkerProfile] = {}
    if worker_profile_ids:
        for wp in db.execute(
            select(WorkerProfile).where(WorkerProfile.id.in_(worker_profile_ids))
        ).scalars().all():
            workers[wp.id] = wp

    data = [
        {
            "id": item.id,
            "assignment_id": item.assignment_id,
            "requirement_id": req_id,
            "worker_profile_id": item.worker_profile_id,
            "worker_name": workers[item.worker_profile_id].full_name if item.worker_profile_id in workers else f"Worker #{item.worker_profile_id}",
            "attendance_date": str(item.attendance_date),
            "status": item.status,
            "check_in_time": item.check_in_time.isoformat() if item.check_in_time else None,
            "check_out_time": item.check_out_time.isoformat() if item.check_out_time else None,
            "notes": item.notes,
            "approval_status": item.approval_status,
            "approval_notes": item.approval_notes,
        }
        for item, req_id in rows
    ]

    return success_response("Pending attendance records fetched successfully", data)


@router.post("/{attendance_id}/approve")
def approve_attendance(
    attendance_id: int,
    current_user: User = Depends(require_role(UserRole.ADMIN.value)),
    db: Session = Depends(get_db),
):
    attendance = get_attendance_by_id(db, attendance_id)
    if not attendance:
        raise HTTPException(status_code=404, detail="Attendance record not found")

    if attendance.approval_status == AttendanceApprovalStatus.APPROVED.value:
        raise HTTPException(status_code=400, detail="Attendance record is already approved")

    attendance.approval_status = AttendanceApprovalStatus.APPROVED.value
    attendance.approved_by_user_id = current_user.id
    attendance.approved_at = utcnow()
    db.commit()

    audit_event(
        "attendance_approved",
        {
            "attendance_id": attendance.id,
            "assignment_id": attendance.assignment_id,
            "attendance_date": str(attendance.attendance_date),
            "admin_user_id": current_user.id,
        },
    )

    return success_response(
        "Attendance approved successfully",
        {
            "attendance_id": attendance.id,
            "approval_status": attendance.approval_status,
            "approved_by_user_id": attendance.approved_by_user_id,
            "approved_at": attendance.approved_at.isoformat() if attendance.approved_at else None,
        },
    )


class CloseShiftSchema(BaseModel):
    notes: str | None = None


@router.post("/{attendance_id}/close-shift")
def close_shift(
    attendance_id: int,
    payload: CloseShiftSchema,
    current_user: User = Depends(require_role(UserRole.ADMIN.value)),
    db: Session = Depends(get_db),
):
    """Administratively close an unclosed check-in by setting check_out_time = now."""
    attendance = get_attendance_by_id(db, attendance_id)
    if not attendance:
        raise HTTPException(status_code=404, detail="Attendance record not found")

    if attendance.check_in_time is None:
        raise HTTPException(status_code=400, detail="Worker has not checked in")

    if attendance.check_out_time is not None:
        raise HTTPException(status_code=400, detail="Shift is already closed")

    attendance.check_out_time = utcnow()
    if payload.notes:
        attendance.notes = payload.notes
    db.commit()

    audit_event(
        "admin_close_shift",
        {
            "attendance_id": attendance.id,
            "assignment_id": attendance.assignment_id,
            "check_out_time": attendance.check_out_time.isoformat(),
            "admin_user_id": current_user.id,
        },
    )

    return success_response(
        "Shift closed successfully",
        {
            "attendance_id": attendance.id,
            "check_out_time": attendance.check_out_time.isoformat(),
        },
    )


class RejectAttendanceSchema(BaseModel):
    notes: str

    @field_validator("notes")
    @classmethod
    def notes_not_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Rejection notes must not be blank")
        return v


@router.post("/{attendance_id}/reject")
def reject_attendance(
    attendance_id: int,
    payload: RejectAttendanceSchema,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_role(UserRole.ADMIN.value)),
    db: Session = Depends(get_db),
):
    attendance = get_attendance_by_id(db, attendance_id)
    if not attendance:
        raise HTTPException(status_code=404, detail="Attendance record not found")

    if attendance.approval_status == AttendanceApprovalStatus.REJECTED.value:
        raise HTTPException(status_code=400, detail="Attendance record is already rejected")

    attendance.approval_status = AttendanceApprovalStatus.REJECTED.value
    attendance.approved_by_user_id = current_user.id
    attendance.approved_at = utcnow()
    attendance.approval_notes = payload.notes
    db.commit()

    audit_event(
        "attendance_rejected",
        {
            "attendance_id": attendance.id,
            "assignment_id": attendance.assignment_id,
            "attendance_date": str(attendance.attendance_date),
            "admin_user_id": current_user.id,
            "notes": payload.notes,
        },
    )

    # Notify the worker
    worker_profile = db.execute(
        select(WorkerProfile).where(WorkerProfile.id == attendance.worker_profile_id)
    ).scalar_one_or_none()
    if worker_profile:
        enqueue_push_to_user(
            background_tasks,
            db,
            user_id=worker_profile.user_id,
            title="Attendance Not Approved",
            body=f"Your attendance for {attendance.attendance_date} was not approved. Reason: {payload.notes}",
            data={"type": "attendance_rejected", "attendance_id": attendance.id, "screen": "AttendanceTab"},
        )

    return success_response(
        "Attendance rejected successfully",
        {
            "attendance_id": attendance.id,
            "approval_status": attendance.approval_status,
            "approval_notes": attendance.approval_notes,
        },
    )
