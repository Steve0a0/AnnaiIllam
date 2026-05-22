from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.dependencies.roles import require_role
from app.core.assignment_constants import AssignmentStatus
from app.core.complaint_constants import ReplacementStatus
from app.core.roles import UserRole
from app.db.deps import get_db
from app.models.user import User
from app.repositories.assignment_repository import (
    create_assignment,
    find_existing_assignment,
    get_assignment_by_id,
)
from app.repositories.complaint_repository import (
    create_replacement,
    get_all_replacements_paginated_stmt,
    get_complaint_by_id,
    get_replacement_by_id,
)
from app.repositories.profile_repository import get_worker_profile_by_id
from app.schemas.assignment import AssignmentCreateSchema
from app.schemas.complaint import ReplacementCreateSchema, ReplacementStatusUpdateSchema
from app.services.assignment_service import build_assignment_entity
from app.services.complaint_service import build_replacement_entity
from app.services.notification_service import enqueue_push_to_user
from app.utils.audit import audit_event
from app.utils.pagination import PaginationParams, paginate, pagination_meta
from app.utils.response import success_response

router = APIRouter(prefix="/admin/replacements", tags=["Admin Replacements"])


@router.get("")
def list_all_replacements(
    status: str | None = Query(None, description="Filter by replacement status"),
    pg: PaginationParams = Depends(),
    current_user: User = Depends(require_role(UserRole.ADMIN.value)),
    db: Session = Depends(get_db),
):
    stmt = get_all_replacements_paginated_stmt(status_filter=status)
    replacements, total = paginate(stmt, db, pg)

    data = [
        {
            "id": item.id,
            "complaint_id": item.complaint_id,
            "old_assignment_id": item.old_assignment_id,
            "new_assignment_id": item.new_assignment_id,
            "old_worker_profile_id": item.old_worker_profile_id,
            "new_worker_profile_id": item.new_worker_profile_id,
            "reason": item.reason,
            "status": item.status,
            "created_by_user_id": item.created_by_user_id,
            "created_at": item.created_at.isoformat(),
        }
        for item in replacements
    ]

    return success_response(
        "Replacements fetched successfully",
        {"items": data, **pagination_meta(pg, total)},
    )


@router.post("")
def create_replacement_for_assignment(
    payload: ReplacementCreateSchema,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_role(UserRole.ADMIN.value)),
    db: Session = Depends(get_db),
):
    complaint = get_complaint_by_id(db, payload.complaint_id)
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    old_assignment = get_assignment_by_id(db, payload.old_assignment_id)
    if not old_assignment:
        raise HTTPException(status_code=404, detail="Old assignment not found")

    if old_assignment.requirement_id != complaint.requirement_id:
        raise HTTPException(status_code=400, detail="Old assignment does not belong to complaint requirement")

    if complaint.assignment_id is not None and complaint.assignment_id != old_assignment.id:
        raise HTTPException(status_code=400, detail="Old assignment does not match complaint assignment")

    new_worker_profile = get_worker_profile_by_id(db, payload.new_worker_profile_id)
    if not new_worker_profile:
        raise HTTPException(status_code=404, detail="New worker profile not found")

    if not new_worker_profile.is_available:
        raise HTTPException(status_code=400, detail="New worker is not available")

    existing = find_existing_assignment(db, old_assignment.requirement_id, payload.new_worker_profile_id)
    if existing:
        raise HTTPException(status_code=400, detail="New worker is already assigned to this requirement")

    assignment_payload = AssignmentCreateSchema(
        requirement_id=old_assignment.requirement_id,
        worker_profile_id=payload.new_worker_profile_id,
        assigned_role=old_assignment.assigned_role,
        assigned_shift=old_assignment.assigned_shift,
        salary_amount=old_assignment.salary_amount,
        notes=f"Replacement for assignment {old_assignment.id}",
    )

    new_assignment = build_assignment_entity(assignment_payload, current_user.id)
    create_assignment(db, new_assignment)
    db.flush()

    old_assignment.status = AssignmentStatus.REPLACED.value

    replacement = build_replacement_entity(
        complaint_id=complaint.id,
        old_assignment_id=old_assignment.id,
        old_worker_profile_id=old_assignment.worker_profile_id,
        new_worker_profile_id=payload.new_worker_profile_id,
        new_assignment_id=new_assignment.id,
        created_by_user_id=current_user.id,
        reason=payload.reason,
    )
    create_replacement(db, replacement)

    db.commit()
    db.refresh(replacement)

    # Look up user_ids for the old and new workers to send push notifications
    old_worker_profile = get_worker_profile_by_id(db, old_assignment.worker_profile_id)
    if old_worker_profile and old_worker_profile.user_id:
        enqueue_push_to_user(
            background_tasks,
            db,
            user_id=old_worker_profile.user_id,
            title="Assignment Update",
            body="You have been replaced on one of your assignments. Please contact admin for details.",
            data={"type": "worker_replaced", "assignment_id": old_assignment.id},
        )

    if new_worker_profile and new_worker_profile.user_id:
        enqueue_push_to_user(
            background_tasks,
            db,
            user_id=new_worker_profile.user_id,
            title="New Assignment",
            body="You have been assigned to a new job. Please check your assignments for details.",
            data={"type": "new_assignment", "assignment_id": new_assignment.id},
        )

    audit_event(
        "worker_replaced",
        {
            "replacement_id": replacement.id,
            "complaint_id": complaint.id,
            "old_assignment_id": old_assignment.id,
            "new_assignment_id": new_assignment.id,
            "admin_user_id": current_user.id,
        },
    )

    return success_response(
        "Replacement created successfully",
        {
            "replacement_id": replacement.id,
            "old_assignment_id": old_assignment.id,
            "new_assignment_id": new_assignment.id,
            "status": replacement.status,
        },
    )


@router.patch("/{replacement_id}/status")
def update_replacement_status(
    replacement_id: int,
    payload: ReplacementStatusUpdateSchema,
    current_user: User = Depends(require_role(UserRole.ADMIN.value)),
    db: Session = Depends(get_db),
):
    replacement = get_replacement_by_id(db, replacement_id)
    if not replacement:
        raise HTTPException(status_code=404, detail="Replacement not found")

    allowed_statuses = {item.value for item in ReplacementStatus}
    if payload.status not in allowed_statuses:
        raise HTTPException(status_code=400, detail="Invalid replacement status")

    old_status = replacement.status
    replacement.status = payload.status
    db.commit()

    audit_event(
        "replacement_status_updated",
        {
            "replacement_id": replacement.id,
            "old_status": old_status,
            "new_status": replacement.status,
            "admin_user_id": current_user.id,
        },
    )

    return success_response(
        "Replacement status updated successfully",
        {
            "replacement_id": replacement.id,
            "status": replacement.status,
        },
    )
