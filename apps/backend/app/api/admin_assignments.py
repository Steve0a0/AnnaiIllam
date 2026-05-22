from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.dependencies.roles import require_role
from app.core.assignment_constants import AssignmentStatus
from app.core.payment_constants import ClientPaymentStatus
from app.core.roles import UserRole
from app.core.statuses import RequirementStatus
from app.db.deps import get_db
from app.models.user import User
from app.repositories.assignment_repository import (
    count_open_assignments_for_requirement,
    create_assignment,
    find_existing_assignment,
    get_assignment_by_id,
    get_assignments_by_requirement_id,
    get_assignments_paginated_stmt,
)
from app.repositories.payment_repository import get_client_payments_by_requirement_id
from app.repositories.profile_repository import get_worker_profile_by_id
from app.repositories.requirement_repository import get_requirement_by_id
from app.schemas.assignment import AssignmentCreateSchema, AssignmentStatusUpdateSchema
from app.services.assignment_service import build_assignment_entity
from app.services.worker_matching_service import detect_worker_conflict, get_worker_matches, get_worker_schedule_mismatch
from app.services.worker_matching_service import ASSIGNABLE_VERIFICATION_STATUSES
from app.services.notification_service import send_push_to_user
from app.utils.audit import audit_event
from app.utils.pagination import PaginationParams, paginate, pagination_meta
from app.utils.response import success_response

router = APIRouter(prefix="/admin/assignments", tags=["Admin Assignments"])


@router.get("")
def list_all_assignments(
    requirement_id: int | None = Query(None, description="Filter by requirement"),
    status: str | None = Query(None, description="Filter by status"),
    pg: PaginationParams = Depends(),
    current_user: User = Depends(require_role(UserRole.ADMIN.value)),
    db: Session = Depends(get_db),
):
    stmt = get_assignments_paginated_stmt(requirement_id=requirement_id, status_filter=status)
    assignments, total = paginate(stmt, db, pg)

    requirement_ids = list({a.requirement_id for a in assignments})
    worker_profile_ids = list({a.worker_profile_id for a in assignments})

    from sqlalchemy import select as sa_select
    from app.models.requirement import Requirement
    from app.models.worker_profile import WorkerProfile

    requirements_map = {}
    if requirement_ids:
        rows = db.execute(sa_select(Requirement).where(Requirement.id.in_(requirement_ids))).scalars().all()
        requirements_map = {r.id: r for r in rows}

    workers_map = {}
    if worker_profile_ids:
        rows = db.execute(sa_select(WorkerProfile).where(WorkerProfile.id.in_(worker_profile_ids))).scalars().all()
        workers_map = {w.id: w for w in rows}

    data = []
    for item in assignments:
        req = requirements_map.get(item.requirement_id)
        worker = workers_map.get(item.worker_profile_id)
        data.append({
            "id": item.id,
            "requirement_id": item.requirement_id,
            "requirement_category": req.category if req else None,
            "requirement_city": req.city if req else None,
            "requirement_status": req.status if req else None,
            "worker_profile_id": item.worker_profile_id,
            "worker_name": worker.full_name if worker else "Worker",
            "worker_city": worker.city if worker else None,
            "status": item.status,
            "assigned_role": item.assigned_role,
            "assigned_shift": item.assigned_shift,
            "salary_amount": item.salary_amount,
            "assigned_at": item.assigned_at.isoformat() if item.assigned_at else None,
        })

    return success_response(
        "Assignments fetched successfully",
        {"items": data, **pagination_meta(pg, total)},
    )


@router.post("")
def create_admin_assignment(
    payload: AssignmentCreateSchema,
    skip_payment_check: bool = Query(False, description="Skip the payment verification gate (admin override)"),
    current_user: User = Depends(require_role(UserRole.ADMIN.value)),
    db: Session = Depends(get_db),
):
    requirement = get_requirement_by_id(db, payload.requirement_id)
    if not requirement:
        raise HTTPException(status_code=404, detail="Requirement not found")

    if requirement.status not in {
        RequirementStatus.APPROVED.value,
        RequirementStatus.ASSIGNED.value,
    }:
        raise HTTPException(status_code=400, detail="Requirement must be approved by the client before assignment")

    # Payment gate: at least one PAID payment is required before assigning workers
    if not skip_payment_check:
        payments = get_client_payments_by_requirement_id(db, payload.requirement_id)
        has_paid = any(p.payment_status == ClientPaymentStatus.PAID.value for p in payments)
        if not has_paid:
            raise HTTPException(
                status_code=400,
                detail="Cannot assign workers — no confirmed payment for this requirement. "
                       "Use skip_payment_check=true to override.",
            )

    worker_profile = get_worker_profile_by_id(db, payload.worker_profile_id)
    if not worker_profile:
        raise HTTPException(status_code=404, detail="Worker profile not found")

    if not worker_profile.is_available:
        raise HTTPException(status_code=400, detail="Worker is not available")

    if worker_profile.verification_status not in ASSIGNABLE_VERIFICATION_STATUSES:
        raise HTTPException(status_code=400, detail="Only approved workers can be assigned")

    schedule_mismatch = get_worker_schedule_mismatch(worker_profile, requirement)
    if schedule_mismatch:
        raise HTTPException(status_code=400, detail=f"Worker is {schedule_mismatch}")

    existing = find_existing_assignment(db, payload.requirement_id, payload.worker_profile_id)
    if existing and existing.status != AssignmentStatus.DECLINED.value:
        raise HTTPException(status_code=400, detail="Worker is already assigned to this requirement")

    conflict = detect_worker_conflict(db, payload.worker_profile_id, requirement)
    if conflict:
        raise HTTPException(status_code=400, detail={"message": "Worker has an assignment conflict", "conflict": conflict})

    assignment = build_assignment_entity(payload, current_user.id)
    create_assignment(db, assignment)

    requirement.status = RequirementStatus.ASSIGNED.value
    requirement.updated_by_user_id = current_user.id

    db.commit()
    db.refresh(assignment)

    audit_event(
        "assignment_created",
        {
            "assignment_id": assignment.id,
            "requirement_id": assignment.requirement_id,
            "worker_profile_id": assignment.worker_profile_id,
            "admin_user_id": current_user.id,
        },
    )

    send_push_to_user(
        db,
        user_id=worker_profile.user_id,
        title="New job assigned",
        body=f"You have been assigned to a new job in {requirement.city}. Open the app to accept or decline.",
        data={"screen": "HomeTab"},
    )

    return success_response(
        "Worker assigned successfully",
        {
            "assignment_id": assignment.id,
            "status": assignment.status,
        },
    )


@router.get("/requirement/{requirement_id}/matches")
def list_worker_matches_for_requirement(
    requirement_id: int,
    current_user: User = Depends(require_role(UserRole.ADMIN.value)),
    db: Session = Depends(get_db),
):
    requirement = get_requirement_by_id(db, requirement_id)
    if not requirement:
        raise HTTPException(status_code=404, detail="Requirement not found")

    return success_response("Worker matches fetched successfully", get_worker_matches(db, requirement))


@router.get("/worker/{worker_profile_id}/conflicts")
def list_worker_assignment_conflicts(
    worker_profile_id: int,
    requirement_id: int,
    current_user: User = Depends(require_role(UserRole.ADMIN.value)),
    db: Session = Depends(get_db),
):
    requirement = get_requirement_by_id(db, requirement_id)
    if not requirement:
        raise HTTPException(status_code=404, detail="Requirement not found")

    conflict = detect_worker_conflict(db, worker_profile_id, requirement)
    return success_response("Worker conflict check completed", {"has_conflict": conflict is not None, "conflict": conflict})


@router.get("/requirement/{requirement_id}")
def list_assignments_for_requirement(
    requirement_id: int,
    current_user: User = Depends(require_role(UserRole.ADMIN.value)),
    db: Session = Depends(get_db),
):
    requirement = get_requirement_by_id(db, requirement_id)
    if not requirement:
        raise HTTPException(status_code=404, detail="Requirement not found")

    assignments = get_assignments_by_requirement_id(db, requirement_id)

    data = []
    for item in assignments:
        worker_profile = get_worker_profile_by_id(db, item.worker_profile_id)
        data.append(
            {
            "id": item.id,
            "worker_profile_id": item.worker_profile_id,
            "worker_name": worker_profile.full_name if worker_profile else "Worker",
            "worker_city": worker_profile.city if worker_profile else None,
            "worker_category": worker_profile.category if worker_profile else None,
            "status": item.status,
            "assigned_role": item.assigned_role,
            "assigned_shift": item.assigned_shift,
            "salary_amount": item.salary_amount,
            "notes": item.notes,
            }
        )

    return success_response("Assignments fetched successfully", data)


@router.patch("/{assignment_id}/status")
def update_assignment_status(
    assignment_id: int,
    payload: AssignmentStatusUpdateSchema,
    current_user: User = Depends(require_role(UserRole.ADMIN.value)),
    db: Session = Depends(get_db),
):
    assignment = get_assignment_by_id(db, assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    allowed_statuses = {
        AssignmentStatus.ASSIGNED.value,
        AssignmentStatus.ACCEPTED.value,
        AssignmentStatus.DECLINED.value,
        AssignmentStatus.ACTIVE.value,
        AssignmentStatus.COMPLETED.value,
        AssignmentStatus.CANCELLED.value,
        AssignmentStatus.REPLACED.value,
    }

    if payload.status not in allowed_statuses:
        raise HTTPException(status_code=400, detail="Invalid assignment status")

    old_status = assignment.status
    assignment.status = payload.status
    db.flush()

    requirement = get_requirement_by_id(db, assignment.requirement_id)
    if (
        requirement
        and payload.status == AssignmentStatus.DECLINED.value
        and count_open_assignments_for_requirement(db, requirement.id) == 0
    ):
        requirement.status = RequirementStatus.APPROVED.value
        requirement.updated_by_user_id = current_user.id

    db.commit()

    audit_event(
        "assignment_status_changed",
        {
            "assignment_id": assignment.id,
            "old_status": old_status,
            "new_status": assignment.status,
            "admin_user_id": current_user.id,
        },
    )

    _STATUS_MESSAGES = {
        AssignmentStatus.CANCELLED.value: ("Assignment cancelled", "Your assignment has been cancelled by the admin."),
        AssignmentStatus.ACTIVE.value:    ("Assignment started", "Your assignment is now active. Good luck!"),
        AssignmentStatus.COMPLETED.value: ("Assignment completed", "Your assignment has been marked as completed."),
        AssignmentStatus.REPLACED.value:  ("Assignment replaced", "You have been replaced on this assignment."),
    }
    if assignment.status in _STATUS_MESSAGES:
        worker_profile = get_worker_profile_by_id(db, assignment.worker_profile_id)
        if worker_profile:
            push_title, push_body = _STATUS_MESSAGES[assignment.status]
            send_push_to_user(
                db,
                user_id=worker_profile.user_id,
                title=push_title,
                body=push_body,
                data={"screen": "HomeTab"},
            )

    return success_response(
        "Assignment status updated successfully",
        {
            "assignment_id": assignment.id,
            "status": assignment.status,
        },
    )
