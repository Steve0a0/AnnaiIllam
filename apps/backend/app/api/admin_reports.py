import csv
import io
from datetime import date, datetime, time, timedelta

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies.roles import require_role
from app.core.roles import UserRole
from app.db.deps import get_db
from app.models.assignment import Assignment
from app.models.complaint import Complaint
from app.models.requirement import Requirement
from app.models.user import User
from app.repositories.profile_repository import get_all_worker_profiles
from app.utils.response import success_response

router = APIRouter(prefix="/admin/reports", tags=["Admin Reports"])


def _csv_response(rows: list[dict], filename: str) -> StreamingResponse:
    if not rows:
        headers = []
    else:
        headers = list(rows[0].keys())
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=headers)
    writer.writeheader()
    writer.writerows(rows)
    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _start_of_day(value: date) -> datetime:
    return datetime.combine(value, time.min)


def _day_after(value: date) -> datetime:
    return datetime.combine(value + timedelta(days=1), time.min)


@router.get("/requirements")
def requirements_report(
    from_date: date | None = Query(None, description="Filter requirements created on or after this date (YYYY-MM-DD)"),
    to_date: date | None = Query(None, description="Filter requirements created on or before this date (YYYY-MM-DD)"),
    status: str | None = Query(None, description="Filter requirements by status"),
    format: str | None = Query(None, description="Set to 'csv' to download as CSV"),
    current_user: User = Depends(require_role(UserRole.ADMIN.value)),
    db: Session = Depends(get_db),
):
    stmt = select(Requirement).order_by(Requirement.created_at.desc())
    if from_date:
        stmt = stmt.where(Requirement.created_at >= _start_of_day(from_date))
    if to_date:
        stmt = stmt.where(Requirement.created_at < _day_after(to_date))
    if status:
        stmt = stmt.where(Requirement.status == status)
    requirements = list(db.execute(stmt).scalars().all())

    data = [
        {
            "id": item.id,
            "client_id": item.client_id,
            "category": item.category,
            "city": item.city,
            "number_of_workers": item.number_of_workers,
            "status": item.status,
            "start_date": str(item.start_date),
        }
        for item in requirements
    ]

    if format == "csv":
        return _csv_response(data, "requirements_report.csv")

    return success_response("Requirements report fetched successfully", data)


@router.get("/assignments")
def assignments_report(
    from_date: date | None = Query(None, description="Filter assignments from this date"),
    to_date: date | None = Query(None, description="Filter assignments to this date"),
    status: str | None = Query(None, description="Filter assignments by status"),
    format: str | None = Query(None, description="Set to 'csv' to download as CSV"),
    current_user: User = Depends(require_role(UserRole.ADMIN.value)),
    db: Session = Depends(get_db),
):
    stmt = select(Assignment).order_by(Assignment.assigned_at.desc())
    if from_date:
        stmt = stmt.where(Assignment.assigned_at >= _start_of_day(from_date))
    if to_date:
        stmt = stmt.where(Assignment.assigned_at < _day_after(to_date))
    if status:
        stmt = stmt.where(Assignment.status == status)
    assignments = list(db.execute(stmt).scalars().all())

    data = [
        {
            "id": item.id,
            "requirement_id": item.requirement_id,
            "worker_profile_id": item.worker_profile_id,
            "status": item.status,
            "assigned_role": item.assigned_role,
            "assigned_shift": item.assigned_shift,
            "salary_amount": item.salary_amount,
        }
        for item in assignments
    ]

    if format == "csv":
        return _csv_response(data, "assignments_report.csv")

    return success_response("Assignments report fetched successfully", data)


@router.get("/complaints")
def complaints_report(
    from_date: date | None = Query(None, description="Filter complaints from this date"),
    to_date: date | None = Query(None, description="Filter complaints to this date"),
    status: str | None = Query(None, description="Filter complaints by status"),
    format: str | None = Query(None, description="Set to 'csv' to download as CSV"),
    current_user: User = Depends(require_role(UserRole.ADMIN.value)),
    db: Session = Depends(get_db),
):
    stmt = select(Complaint).order_by(Complaint.created_at.desc())
    if from_date:
        stmt = stmt.where(Complaint.created_at >= _start_of_day(from_date))
    if to_date:
        stmt = stmt.where(Complaint.created_at < _day_after(to_date))
    if status:
        stmt = stmt.where(Complaint.status == status)
    complaints = list(db.execute(stmt).scalars().all())

    data = [
        {
            "id": item.id,
            "requirement_id": item.requirement_id,
            "assignment_id": item.assignment_id,
            "complaint_type": item.complaint_type,
            "severity": item.severity,
            "status": item.status,
            "created_at": item.created_at.isoformat(),
        }
        for item in complaints
    ]

    if format == "csv":
        return _csv_response(data, "complaints_report.csv")

    return success_response("Complaints report fetched successfully", data)


@router.get("/workers")
def workers_report(
    format: str | None = Query(None, description="Set to 'csv' to download as CSV"),
    current_user: User = Depends(require_role(UserRole.ADMIN.value)),
    db: Session = Depends(get_db),
):
    workers = get_all_worker_profiles(db)
    data = [
        {
            "id": item.id,
            "full_name": item.full_name,
            "category": item.category,
            "city": item.city,
            "state": item.state,
            "is_available": item.is_available,
            "verification_status": item.verification_status,
            "skills": item.skills,
        }
        for item in workers
    ]

    if format == "csv":
        return _csv_response(data, "workers_report.csv")

    return success_response("Workers report fetched successfully", data)
