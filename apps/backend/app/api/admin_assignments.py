from datetime import timedelta

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from app.utils.time import utcnow
from pydantic import BaseModel, field_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies.roles import require_role
from app.core.assignment_constants import AssignmentStatus, validate_assignment_transition
from app.core.payment_constants import ClientPaymentStatus
from app.core.roles import UserRole
from app.core.statuses import RequirementStatus, validate_requirement_transition
from app.db.deps import get_db
from app.models.assignment import Assignment
from app.models.requirement import Requirement
from app.models.user import User
from app.models.worker_interest import WorkerInterest
from app.models.worker_profile import WorkerProfile
from app.repositories.assignment_repository import (
    count_open_assignments_for_requirement,
    create_assignment,
    find_existing_assignment,
    get_assignment_by_id,
    get_assignments_by_requirement_id,
    get_assignments_paginated_stmt,
)
from app.repositories.attendance_repository import get_attendance_for_assignment
from app.repositories.payment_repository import get_client_payments_by_requirement_id
from app.repositories.profile_repository import get_worker_profile_by_id, get_client_profile_by_id
from app.repositories.quote_repository import get_quote_by_requirement_id
from app.repositories.requirement_repository import get_requirement_by_id
from app.schemas.assignment import AssignmentCreateSchema, AssignmentStatusUpdateSchema
from app.services.assignment_service import build_assignment_entity
from app.services.worker_matching_service import detect_worker_conflict, get_worker_matches, get_worker_schedule_mismatch
from app.services.worker_matching_service import ASSIGNABLE_VERIFICATION_STATUSES, get_expired_documents
from app.services.notification_service import enqueue_push_to_user, send_push_to_user
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
    skip_reason: str | None = Query(None, description="Required when skip_payment_check=true"),
    current_user: User = Depends(require_role(UserRole.ADMIN.value)),
    db: Session = Depends(get_db),
):
    # Lock the requirement row on PostgreSQL to prevent concurrent double-assignment.
    # SQLite (test suite) does not support SELECT FOR UPDATE — fall back to plain read.
    if db.bind.dialect.name != "sqlite":
        requirement = db.execute(
            select(Requirement).where(Requirement.id == payload.requirement_id).with_for_update()
        ).scalar_one_or_none()
    else:
        requirement = get_requirement_by_id(db, payload.requirement_id)
    if not requirement:
        raise HTTPException(status_code=404, detail="Requirement not found")

    if requirement.status not in {
        RequirementStatus.APPROVED.value,
        RequirementStatus.WORKERS_ASSIGNED.value,
    }:
        raise HTTPException(status_code=400, detail="Requirement must be approved by the client before assignment")

    # Dates guard: both fields must be set for conflict detection and date-window
    # validation to work safely.  The DB model enforces NOT NULL, but this guard
    # ensures the API fails explicitly if that contract is ever violated.
    if requirement.start_date is None or requirement.duration_days is None:
        raise HTTPException(
            status_code=400,
            detail="Requirement dates must be set before assigning workers",
        )

    # Payment gate: at least one PAID payment is required before assigning workers,
    # UNLESS the quote has no advance requirement (advance_amount is null or 0).
    quote = get_quote_by_requirement_id(db, payload.requirement_id)
    advance_required = quote is not None and (quote.advance_amount or 0) > 0
    if skip_payment_check:
        if not skip_reason or not skip_reason.strip():
            raise HTTPException(
                status_code=400,
                detail="skip_reason is required when skip_payment_check=true.",
            )
    elif advance_required:
        payments = get_client_payments_by_requirement_id(db, payload.requirement_id)
        has_paid = any(p.payment_status == ClientPaymentStatus.PAID.value for p in payments)
        if not has_paid:
            raise HTTPException(
                status_code=400,
                detail="Cannot assign workers — no confirmed advance payment for this requirement. "
                       "Use skip_payment_check=true to override.",
            )

    # Per-day capacity gate: no single day in the requested window may exceed number_of_workers
    req_end_date = requirement.start_date + timedelta(days=requirement.duration_days - 1)
    new_a_start = payload.start_date or requirement.start_date
    new_a_end = payload.end_date or req_end_date

    existing_active = [
        a for a in get_assignments_by_requirement_id(db, payload.requirement_id)
        if a.status in {
            AssignmentStatus.ASSIGNED.value,
            AssignmentStatus.ACCEPTED.value,
            AssignmentStatus.ACTIVE.value,
        }
    ]
    check_day = new_a_start
    while check_day <= new_a_end:
        day_count = sum(
            1 for a in existing_active
            if (a.start_date or requirement.start_date) <= check_day <= (a.end_date or req_end_date)
        )
        if day_count >= requirement.number_of_workers:
            raise HTTPException(
                status_code=400,
                detail=f"{check_day} is already fully staffed "
                       f"({day_count}/{requirement.number_of_workers} workers). "
                       f"Choose a different date range.",
            )
        check_day += timedelta(days=1)

    # Date window validation: assignment dates must not fall outside requirement window
    if payload.start_date is not None or payload.end_date is not None:
        if requirement.start_date is not None and requirement.duration_days is not None:
            req_end_date = requirement.start_date + timedelta(days=requirement.duration_days - 1)
            if payload.start_date is not None and payload.start_date < requirement.start_date:
                raise HTTPException(
                    status_code=400,
                    detail="Assignment start date cannot be before requirement start date",
                )
            if payload.end_date is not None and payload.end_date > req_end_date:
                raise HTTPException(
                    status_code=400,
                    detail="Assignment end date cannot be after requirement end date",
                )

    worker_profile = get_worker_profile_by_id(db, payload.worker_profile_id)
    if not worker_profile:
        raise HTTPException(status_code=404, detail="Worker profile not found")

    if worker_profile.verification_status not in ASSIGNABLE_VERIFICATION_STATUSES:
        raise HTTPException(status_code=400, detail="Only approved workers can be assigned")

    schedule_mismatch = get_worker_schedule_mismatch(worker_profile, requirement)
    if schedule_mismatch:
        raise HTTPException(status_code=400, detail=f"Worker is {schedule_mismatch}")

    # Per-day model: a worker may have multiple single-day assignments on the same
    # requirement.  Only block if they are already covering the exact requested day.
    req_end_date = requirement.start_date + timedelta(days=requirement.duration_days - 1)
    new_start = payload.start_date or requirement.start_date
    new_end = payload.end_date or req_end_date
    for existing in get_assignments_by_requirement_id(db, payload.requirement_id):
        if existing.worker_profile_id != payload.worker_profile_id:
            continue
        if existing.status in _EXCLUDED_STATUSES:
            continue
        ex_start = existing.start_date or requirement.start_date
        ex_end = existing.end_date or req_end_date
        if ex_start <= new_end and new_start <= ex_end:
            raise HTTPException(
                status_code=400,
                detail=f"Worker is already assigned for this date range on this requirement",
            )

    conflict = detect_worker_conflict(db, payload.worker_profile_id, requirement)
    if conflict:
        raise HTTPException(status_code=400, detail={"message": "Worker has an assignment conflict", "conflict": conflict})

    assignment = build_assignment_entity(payload, current_user.id)

    # Auto-set worker salary from quote.worker_daily_rate if not already specified
    if assignment.salary_amount is None and quote and quote.worker_daily_rate:
        assignment.salary_amount = quote.worker_daily_rate

    create_assignment(db, assignment)

    # Fix 15: sync WorkerInterest status so the interest panel reflects the assignment
    _interest = db.execute(
        select(WorkerInterest).where(
            WorkerInterest.worker_profile_id == payload.worker_profile_id,
            WorkerInterest.requirement_id == payload.requirement_id,
        )
    ).scalar_one_or_none()
    if _interest:
        _interest.status = "assigned"

    if requirement.status != RequirementStatus.WORKERS_ASSIGNED.value:
        try:
            validate_requirement_transition(requirement.status, RequirementStatus.WORKERS_ASSIGNED.value)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        requirement.status = RequirementStatus.WORKERS_ASSIGNED.value
    requirement.updated_by_user_id = current_user.id

    db.commit()
    db.refresh(assignment)

    if skip_payment_check:
        audit_event(
            "payment_gate_bypassed",
            {
                "assignment_id": assignment.id,
                "requirement_id": payload.requirement_id,
                "worker_profile_id": payload.worker_profile_id,
                "skip_reason": skip_reason.strip(),
            },
            actor_user_id=current_user.id,
        )

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

    # Notify client that workers have been assigned
    client_profile = get_client_profile_by_id(db, requirement.client_id)
    if client_profile:
        send_push_to_user(
            db,
            user_id=client_profile.user_id,
            title="Workers assigned to your job",
            body=f"Workers have been assigned to your staffing request in {requirement.city}.",
            data={"screen": "JobsTab"},
        )

    expired_docs = get_expired_documents(db, payload.worker_profile_id)
    warning = None
    if expired_docs:
        expired_types = ", ".join(d["document_type"] for d in expired_docs)
        warning = {
            "code": "document_expired",
            "message": f"Worker has expired document(s): {expired_types}. Verify or renew before the assignment begins.",
            "documents": expired_docs,
        }

    return success_response(
        "Worker assigned successfully",
        {
            "assignment_id": assignment.id,
            "status": assignment.status,
            "warning": warning,
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
            "start_date": str(item.start_date) if item.start_date else None,
            "end_date": str(item.end_date) if item.end_date else None,
            "response_deadline": item.response_deadline.isoformat() if item.response_deadline else None,
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
    try:
        validate_assignment_transition(old_status, payload.status)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    assignment.status = payload.status
    db.flush()

    requirement = get_requirement_by_id(db, assignment.requirement_id)
    if (
        requirement
        and payload.status == AssignmentStatus.DECLINED.value
        and count_open_assignments_for_requirement(db, requirement.id) == 0
    ):
        try:
            validate_requirement_transition(requirement.status, RequirementStatus.APPROVED.value)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
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


_EXCLUDED_STATUSES = {
    AssignmentStatus.DECLINED.value,
    AssignmentStatus.CANCELLED.value,
    AssignmentStatus.REPLACED.value,
}

_CONFIRMED_STATUSES = {
    AssignmentStatus.ACCEPTED.value,
    AssignmentStatus.ACTIVE.value,
    AssignmentStatus.COMPLETED.value,
}


@router.get("/requirement/{requirement_id}/coverage")
def get_coverage_calendar(
    requirement_id: int,
    current_user: User = Depends(require_role(UserRole.ADMIN.value)),
    db: Session = Depends(get_db),
):
    """Return a day-by-day coverage grid for a requirement.

    Each entry shows how many workers cover that day (by assignment window),
    how many have confirmed (accepted/active/completed), and how many actually
    checked in. Red = uncovered, yellow = partial, green = full coverage.
    """
    requirement = get_requirement_by_id(db, requirement_id)
    if not requirement:
        raise HTTPException(status_code=404, detail="Requirement not found")

    assignments = get_assignments_by_requirement_id(db, requirement_id)
    active_assignments = [a for a in assignments if a.status not in _EXCLUDED_STATUSES]

    # Fix 18: batch-load all worker profiles to avoid N+1 in the coverage loop
    _wp_ids = [a.worker_profile_id for a in active_assignments]
    _workers_cache: dict[int, str] = {}
    if _wp_ids:
        for _wp in db.execute(
            select(WorkerProfile).where(WorkerProfile.id.in_(_wp_ids))
        ).scalars().all():
            _workers_cache[_wp.id] = _wp.full_name

    # Pre-load attendance for all active assignments
    attendance_by_assignment: dict[int, set] = {}
    for assignment in active_assignments:
        records = get_attendance_for_assignment(db, assignment.id)
        attendance_by_assignment[assignment.id] = {
            str(r.attendance_date) for r in records
        }

    req_start = requirement.start_date
    req_end = req_start + timedelta(days=requirement.duration_days - 1)
    required = requirement.number_of_workers

    days = []
    current_day = req_start
    while current_day <= req_end:
        day_str = str(current_day)
        covering = []
        confirmed = []
        checked_in = []

        for assignment in active_assignments:
            # Determine if this assignment's window includes today
            a_start = assignment.start_date or req_start
            a_end = assignment.end_date or req_end
            if not (a_start <= current_day <= a_end):
                continue

            worker_name = _workers_cache.get(assignment.worker_profile_id, "Unknown")
            covering.append({
                "assignment_id": assignment.id,
                "worker_profile_id": assignment.worker_profile_id,
                "worker_name": worker_name,
                "status": assignment.status,
            })
            if assignment.status in _CONFIRMED_STATUSES:
                confirmed.append(assignment.id)
            if day_str in attendance_by_assignment.get(assignment.id, set()):
                checked_in.append(assignment.id)

        covering_count = len(covering)
        confirmed_count = len(confirmed)
        checked_in_count = len(checked_in)

        if covering_count >= required:
            coverage_status = "full"
        elif covering_count > 0:
            coverage_status = "partial"
        else:
            coverage_status = "uncovered"

        days.append({
            "date": day_str,
            "covering_count": covering_count,
            "confirmed_count": confirmed_count,
            "checked_in_count": checked_in_count,
            "required": required,
            "coverage_status": coverage_status,
            "workers": covering,
        })
        current_day += timedelta(days=1)

    return success_response(
        "Coverage calendar fetched successfully",
        {
            "requirement_id": requirement_id,
            "start_date": str(req_start),
            "end_date": str(req_end),
            "duration_days": requirement.duration_days,
            "required_per_day": required,
            "days": days,
        },
    )


# ---------------------------------------------------------------------------
# Worker replacement
# ---------------------------------------------------------------------------

_REPLACEABLE_STATUSES = {
    AssignmentStatus.ASSIGNED.value,
    AssignmentStatus.ACCEPTED.value,
    AssignmentStatus.ACTIVE.value,
}

_ACTIVE_STATUSES = {
    AssignmentStatus.ASSIGNED.value,
    AssignmentStatus.ACCEPTED.value,
    AssignmentStatus.ACTIVE.value,
}


class ReplaceWorkerSchema(BaseModel):
    new_worker_profile_id: int
    reason: str

    @field_validator("reason")
    @classmethod
    def reason_min_length(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Replacement reason is required")
        return v


@router.post("/{assignment_id}/replace")
def replace_worker(
    assignment_id: int,
    payload: ReplaceWorkerSchema,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_role(UserRole.ADMIN.value)),
    db: Session = Depends(get_db),
):
    """Atomically replace a deployed worker with a new one.

    Old assignment is set to 'replaced'; a new assignment is created for the
    replacement worker on the same requirement with the same role/shift/salary/dates.
    Both workers receive push notifications.
    """
    old_assignment = get_assignment_by_id(db, assignment_id)
    if not old_assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    if old_assignment.status not in _REPLACEABLE_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"Can only replace an assignment with status in "
                   f"{sorted(_REPLACEABLE_STATUSES)}, not '{old_assignment.status}'",
        )

    requirement = get_requirement_by_id(db, old_assignment.requirement_id)
    if not requirement:
        raise HTTPException(status_code=404, detail="Requirement not found")

    new_worker_profile = get_worker_profile_by_id(db, payload.new_worker_profile_id)
    if not new_worker_profile:
        raise HTTPException(status_code=404, detail="New worker profile not found")

    # Duplicate check: new worker must not already have an active assignment on this requirement.
    # Checked before availability so the error message is specific and actionable.
    existing = find_existing_assignment(db, requirement.id, payload.new_worker_profile_id)
    if existing and existing.status in _ACTIVE_STATUSES:
        raise HTTPException(
            status_code=400,
            detail="Replacement worker is already actively assigned to this requirement",
        )

    if not new_worker_profile.is_available:
        raise HTTPException(status_code=400, detail="Replacement worker is not available")

    if new_worker_profile.verification_status not in ASSIGNABLE_VERIFICATION_STATUSES:
        raise HTTPException(status_code=400, detail="Only approved workers can be assigned")

    # Duplicate check: new worker must not already have an active assignment on this requirement
    existing = find_existing_assignment(db, requirement.id, payload.new_worker_profile_id)
    if existing and existing.status in _ACTIVE_STATUSES:
        raise HTTPException(
            status_code=400,
            detail="Replacement worker is already actively assigned to this requirement",
        )

    # --- Begin atomic replacement ---

    # 1. Mark old assignment as replaced
    old_assignment.status = AssignmentStatus.REPLACED.value
    old_assignment.replacement_reason = payload.reason.strip()

    # 3. Create new assignment mirroring same role/shift/salary/dates
    new_assignment = Assignment(
        requirement_id=requirement.id,
        worker_profile_id=payload.new_worker_profile_id,
        assigned_by_user_id=current_user.id,
        status=AssignmentStatus.ASSIGNED.value,
        assigned_role=old_assignment.assigned_role,
        assigned_shift=old_assignment.assigned_shift,
        salary_amount=old_assignment.salary_amount,
        notes=old_assignment.notes,
        start_date=old_assignment.start_date,
        end_date=old_assignment.end_date,
        response_deadline=utcnow() + timedelta(hours=24),
    )
    db.add(new_assignment)
    db.flush()  # populate new_assignment.id

    # 4. Link old → new
    old_assignment.replaced_by_assignment_id = new_assignment.id

    # 5. Update WorkerInterest for new worker if present
    _interest = db.execute(
        select(WorkerInterest).where(
            WorkerInterest.worker_profile_id == payload.new_worker_profile_id,
            WorkerInterest.requirement_id == requirement.id,
        )
    ).scalar_one_or_none()
    if _interest:
        _interest.status = "assigned"

    db.commit()

    # Notifications (fire-and-forget)
    if old_worker_profile and old_worker_profile.user_id:
        enqueue_push_to_user(
            background_tasks,
            db,
            user_id=old_worker_profile.user_id,
            title="Assignment reassigned",
            body="Your assignment has been reassigned to another worker.",
            data={"screen": "HomeTab"},
        )

    enqueue_push_to_user(
        background_tasks,
        db,
        user_id=new_worker_profile.user_id,
        title="New job assigned",
        body=f"New job assigned for requirement #{requirement.id} — please acknowledge in the app.",
        data={"screen": "HomeTab"},
    )

    audit_event(
        "worker_replaced",
        {
            "old_assignment_id": assignment_id,
            "new_assignment_id": new_assignment.id,
            "requirement_id": requirement.id,
            "old_worker_profile_id": old_assignment.worker_profile_id,
            "new_worker_profile_id": payload.new_worker_profile_id,
            "reason": payload.reason.strip(),
            "admin_user_id": current_user.id,
        },
    )

    return success_response(
        "Worker replaced successfully",
        {
            "old_assignment_id": assignment_id,
            "old_assignment_status": old_assignment.status,
            "new_assignment_id": new_assignment.id,
            "new_assignment_status": new_assignment.status,
        },
    )
