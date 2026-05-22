from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.dependencies.roles import require_role
from app.core.complaint_constants import ComplaintStatus
from app.core.roles import UserRole
from app.db.deps import get_db
from app.models.user import User
from app.repositories.complaint_repository import (
    get_complaint_by_id,
    get_complaints_paginated_stmt,
    get_replacements_by_complaint_id,
)
from app.repositories.sla_repository import get_sla_policy_map
from app.schemas.complaint import ComplaintStatusUpdateSchema
from app.services.notification_service import enqueue_push_to_user
from app.utils.audit import audit_event
from app.utils.pagination import PaginationParams, paginate, pagination_meta
from app.utils.response import success_response
from app.utils.time import utcnow

router = APIRouter(prefix="/admin/complaints", tags=["Admin Complaints"])

_OPEN_STATUSES = {ComplaintStatus.OPEN.value, ComplaintStatus.UNDER_REVIEW.value}


def _sla_breach_info(complaint, sla_map: dict) -> dict:
    """Return SLA breach status for a complaint based on its severity and age."""
    policy = sla_map.get(complaint.severity, {})
    response_hours = policy.get("response_hours")
    resolution_hours = policy.get("resolution_hours")
    age_hours = (utcnow() - complaint.created_at).total_seconds() / 3600

    is_open = complaint.status in _OPEN_STATUSES
    response_breached = is_open and response_hours is not None and age_hours > response_hours
    resolution_breached = is_open and resolution_hours is not None and age_hours > resolution_hours

    return {
        "age_hours": round(age_hours, 1),
        "response_hours_limit": response_hours,
        "resolution_hours_limit": resolution_hours,
        "response_breached": response_breached,
        "resolution_breached": resolution_breached,
    }


@router.get("")
def list_all_complaints(
    status: str | None = Query(None, description="Filter by status"),
    pg: PaginationParams = Depends(),
    current_user: User = Depends(require_role(UserRole.ADMIN.value)),
    db: Session = Depends(get_db),
):
    stmt = get_complaints_paginated_stmt(status_filter=status)
    complaints, total = paginate(stmt, db, pg)
    sla_map = get_sla_policy_map(db)

    data = [
        {
            "id": item.id,
            "requirement_id": item.requirement_id,
            "assignment_id": item.assignment_id,
            "complaint_type": item.complaint_type,
            "severity": item.severity,
            "status": item.status,
            "created_at": item.created_at.isoformat(),
            "sla": _sla_breach_info(item, sla_map),
        }
        for item in complaints
    ]

    return success_response(
        "Complaints fetched successfully",
        {"items": data, **pagination_meta(pg, total)},
    )


@router.get("/{complaint_id}")
def get_admin_complaint_detail(
    complaint_id: int,
    current_user: User = Depends(require_role(UserRole.ADMIN.value)),
    db: Session = Depends(get_db),
):
    complaint = get_complaint_by_id(db, complaint_id)
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    replacements = get_replacements_by_complaint_id(db, complaint.id)
    sla_map = get_sla_policy_map(db)

    return success_response(
        "Complaint detail fetched successfully",
        {
            "id": complaint.id,
            "requirement_id": complaint.requirement_id,
            "assignment_id": complaint.assignment_id,
            "raised_by_user_id": complaint.raised_by_user_id,
            "complaint_type": complaint.complaint_type,
            "severity": complaint.severity,
            "description": complaint.description,
            "status": complaint.status,
            "resolution_notes": complaint.resolution_notes,
            "resolved_by_user_id": complaint.resolved_by_user_id,
            "created_at": complaint.created_at.isoformat(),
            "updated_at": complaint.updated_at.isoformat(),
            "sla": _sla_breach_info(complaint, sla_map),
            "replacements": [
                {
                    "id": replacement.id,
                    "old_assignment_id": replacement.old_assignment_id,
                    "new_assignment_id": replacement.new_assignment_id,
                    "old_worker_profile_id": replacement.old_worker_profile_id,
                    "new_worker_profile_id": replacement.new_worker_profile_id,
                    "status": replacement.status,
                    "reason": replacement.reason,
                }
                for replacement in replacements
            ],
        },
    )


@router.patch("/{complaint_id}/status")
def update_complaint_status(
    complaint_id: int,
    payload: ComplaintStatusUpdateSchema,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_role(UserRole.ADMIN.value)),
    db: Session = Depends(get_db),
):
    complaint = get_complaint_by_id(db, complaint_id)
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    allowed_statuses = {item.value for item in ComplaintStatus}
    if payload.status not in allowed_statuses:
        raise HTTPException(status_code=400, detail="Invalid complaint status")

    old_status = complaint.status
    complaint.status = payload.status
    complaint.resolution_notes = payload.resolution_notes
    complaint.resolved_by_user_id = current_user.id

    db.commit()

    audit_event(
        "complaint_status_updated",
        {
            "complaint_id": complaint.id,
            "old_status": old_status,
            "new_status": complaint.status,
            "admin_user_id": current_user.id,
        },
    )

    if complaint.status == ComplaintStatus.RESOLVED.value and complaint.raised_by_user_id:
        enqueue_push_to_user(
            background_tasks,
            db,
            user_id=complaint.raised_by_user_id,
            title="Your complaint has been resolved",
            body="Annai Illam has resolved your complaint. Open the app to view the resolution.",
            data={"screen": "ComplaintsTab"},
        )

    return success_response(
        "Complaint status updated successfully",
        {
            "complaint_id": complaint.id,
            "status": complaint.status,
        },
    )
