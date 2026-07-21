from datetime import timedelta
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, field_validator
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.dependencies.roles import require_role
from app.core.roles import UserRole
from app.core.statuses import QuoteStatus, RequirementStatus, validate_requirement_transition
from app.db.deps import get_db
from app.models.requirement import Requirement
from app.models.user import User
from app.repositories.client_repository import get_client_profile_by_user_id
from app.repositories.assignment_repository import get_assignment_by_id, get_assignments_by_requirement_id
from app.repositories.attendance_repository import get_attendance_for_assignment
from app.models.client_payment import ClientPayment
from app.models.client_rating import ClientRating
from app.models.quote import Quote
from app.repositories.payment_repository import get_client_payments_by_client_id
from app.repositories.profile_repository import get_worker_profile_by_id
from app.repositories.quote_repository import get_quote_by_requirement_id
from app.repositories.rating_repository import get_client_rating_for_requirement, upsert_client_rating
from app.repositories.requirement_repository import (
    create_requirement,
    get_requirement_by_id,
    get_requirements_by_client_id_paginated_stmt,
)
from app.utils.pagination import PaginationParams, paginate, pagination_meta
from app.schemas.quote import QuoteDecisionSchema
from app.schemas.rating import ClientRatingCreateSchema
from app.schemas.requirement import RequirementCreateSchema
from app.services.notification_service import enqueue_push_to_user, queue_notification
from app.services.payment_ledger_service import build_payment_ledger
from app.services.requirement_service import build_requirement_entity
from app.utils.audit import audit_event
from app.utils.time import business_today
from app.utils.response import success_response

router = APIRouter(prefix="/client/requirements", tags=["Client Requirements"])


@router.post("")
def create_client_requirement(
    payload: RequirementCreateSchema,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_role(UserRole.CLIENT.value)),
    db: Session = Depends(get_db),
):
    client_profile = get_client_profile_by_user_id(db, current_user.id)
    if not client_profile:
        raise HTTPException(status_code=400, detail="Client profile not found")

    requirement = build_requirement_entity(
        payload=payload,
        client_id=client_profile.id,
        user_id=current_user.id,
    )
    create_requirement(db, requirement)
    db.commit()
    db.refresh(requirement)

    audit_event(
        "requirement_created",
        {
            "requirement_id": requirement.id,
            "client_user_id": current_user.id,
        },
    )
    queue_notification(
        channel="sms",
        recipient=current_user.phone,
        template="requirement_created",
        context={"requirement_id": requirement.id, "status": requirement.status},
    )

    # Notify all admins about the new requirement
    client_name = client_profile.company_name or client_profile.contact_name or "A client"
    admin_users = db.execute(
        select(User).where(User.role == UserRole.ADMIN.value, User.is_active.is_(True))
    ).scalars().all()
    for admin in admin_users:
        enqueue_push_to_user(
            background_tasks,
            db,
            user_id=admin.id,
            title="New requirement submitted",
            body=f"New staffing requirement from {client_name}.",
            data={"type": "new_requirement", "requirement_id": str(requirement.id)},
        )

    return success_response(
        "Requirement created successfully",
        {
            "id": requirement.id,
            "status": requirement.status,
        },
    )


@router.get("")
def list_my_requirements(
    pg: PaginationParams = Depends(),
    current_user: User = Depends(require_role(UserRole.CLIENT.value)),
    db: Session = Depends(get_db),
):
    client_profile = get_client_profile_by_user_id(db, current_user.id)
    if not client_profile:
        raise HTTPException(status_code=400, detail="Client profile not found")

    stmt = get_requirements_by_client_id_paginated_stmt(client_profile.id)
    requirements, total = paginate(stmt, db, pg)

    req_ids = [r.id for r in requirements]

    # Batch-fetch quotes, paid payments, and ratings — no N+1 queries
    quotes: dict[int, Quote] = {}
    payments_by_requirement: dict[int, list[ClientPayment]] = {}
    rated_req_ids: set[int] = set()
    if req_ids:
        for q in db.execute(select(Quote).where(Quote.requirement_id.in_(req_ids))).scalars().all():
            quotes[q.requirement_id] = q
        for p in db.execute(
            select(ClientPayment).where(ClientPayment.requirement_id.in_(req_ids))
        ).scalars().all():
            payments_by_requirement.setdefault(p.requirement_id, []).append(p)
        for cr in db.execute(
            select(ClientRating).where(
                ClientRating.requirement_id.in_(req_ids),
                ClientRating.rated_by_user_id == current_user.id,
            )
        ).scalars().all():
            rated_req_ids.add(cr.requirement_id)

    def pending_balance(item) -> int | None:
        if item.status != RequirementStatus.IN_PROGRESS.value:
            return None
        quote = quotes.get(item.id)
        if not quote or quote.payment_model == "client_pays_worker_directly":
            return None
        balance = build_payment_ledger(
            quote,
            payments_by_requirement.get(item.id, []),
        ).outstanding_balance
        return balance if balance > 0 else None

    data = [
        {
            "id": item.id,
            "category": item.category,
            "number_of_workers": item.number_of_workers,
            "city": item.city,
            "start_date": str(item.start_date),
            "status": item.status,
            "pending_balance_amount": pending_balance(item),
            "has_rated": item.id in rated_req_ids,
        }
        for item in requirements
    ]
    return success_response("Requirements fetched successfully", {"items": data, **pagination_meta(pg, total)})


@router.get("/summary")
def get_client_dashboard_summary(
    current_user: User = Depends(require_role(UserRole.CLIENT.value)),
    db: Session = Depends(get_db),
):
    client_profile = get_client_profile_by_user_id(db, current_user.id)
    if not client_profile:
        raise HTTPException(status_code=400, detail="Client profile not found")

    payments = get_client_payments_by_client_id(db, client_profile.id)

    open_statuses = [
        RequirementStatus.SUBMITTED.value,
        RequirementStatus.UNDER_REVIEW.value,
        RequirementStatus.QUOTED.value,
        RequirementStatus.APPROVED.value,
        RequirementStatus.WORKERS_ASSIGNED.value,
        RequirementStatus.IN_PROGRESS.value,
    ]
    pending_quote_statuses = [
        RequirementStatus.SUBMITTED.value,
        RequirementStatus.UNDER_REVIEW.value,
        RequirementStatus.QUOTED.value,
    ]

    # Fix 19: replace per-requirement iteration with aggregate COUNT queries
    def _count(statuses=None, exact=None):
        stmt = select(func.count(Requirement.id)).where(Requirement.client_id == client_profile.id)
        if statuses is not None:
            stmt = stmt.where(Requirement.status.in_(statuses))
        elif exact is not None:
            stmt = stmt.where(Requirement.status == exact)
        return db.execute(stmt).scalar_one()

    return success_response(
        "Client dashboard summary fetched successfully",
        {
            "total_requirements": _count(),
            "open_jobs": _count(statuses=open_statuses),
            "pending_quotes": _count(statuses=pending_quote_statuses),
            "completed_jobs": _count(exact=RequirementStatus.COMPLETED.value),
            "paid_spend": sum(item.amount for item in payments if item.payment_status == "paid"),
            "pending_payments": sum(item.amount for item in payments if item.payment_status != "paid"),
        },
    )


@router.get("/{requirement_id}")
def get_my_requirement_detail(
    requirement_id: int,
    current_user: User = Depends(require_role(UserRole.CLIENT.value)),
    db: Session = Depends(get_db),
):
    client_profile = get_client_profile_by_user_id(db, current_user.id)
    if not client_profile:
        raise HTTPException(status_code=400, detail="Client profile not found")

    requirement = get_requirement_by_id(db, requirement_id)
    if not requirement or requirement.client_id != client_profile.id:
        raise HTTPException(status_code=404, detail="Requirement not found")

    quote = get_quote_by_requirement_id(db, requirement.id)
    assignments = get_assignments_by_requirement_id(db, requirement.id)
    rating = get_client_rating_for_requirement(db, requirement.id, current_user.id)

    assignment_data = []
    for assignment in assignments:
        worker_profile = get_worker_profile_by_id(db, assignment.worker_profile_id)
        attendance_records = get_attendance_for_assignment(db, assignment.id)
        assignment_data.append(
            {
                "id": assignment.id,
                "worker_profile_id": assignment.worker_profile_id,
                "worker_name": worker_profile.full_name if worker_profile else "Worker",
                "worker_city": worker_profile.city if worker_profile else None,
                "worker_category": worker_profile.category if worker_profile else None,
                "status": assignment.status,
                "assigned_role": assignment.assigned_role,
                "assigned_shift": assignment.assigned_shift,
                "assigned_at": assignment.assigned_at.isoformat(),
                "attendance": [
                    {
                        "id": item.id,
                        "attendance_date": str(item.attendance_date),
                        "status": item.status,
                        "check_in_time": item.check_in_time.isoformat() if item.check_in_time else None,
                        "check_out_time": item.check_out_time.isoformat() if item.check_out_time else None,
                        "notes": item.notes,
                    }
                    for item in attendance_records
                ],
            }
        )

    return success_response(
        "Requirement detail fetched successfully",
        {
            "id": requirement.id,
            "category": requirement.category,
            "subcategory": requirement.subcategory,
            "number_of_workers": requirement.number_of_workers,
            "work_location": requirement.work_location,
            "city": requirement.city,
            "state": requirement.state,
            "start_date": str(requirement.start_date),
            "duration_days": requirement.duration_days,
            "shift_details": requirement.shift_details,
            "food_required": requirement.food_required,
            "accommodation_required": requirement.accommodation_required,
            "budget_amount": requirement.budget_amount,
            "notes": requirement.notes,
            "status": requirement.status,
            "rejection_reason": requirement.rejection_reason,
            "cancellation_reason": requirement.cancellation_reason,
            "assignments": assignment_data,
            "rating": None
            if not rating
            else {
                "id": rating.id,
                "assignment_id": rating.assignment_id,
                "worker_profile_id": rating.worker_profile_id,
                "rating": rating.rating,
                "comments": rating.comments,
                "created_at": rating.created_at.isoformat(),
                "updated_at": rating.updated_at.isoformat(),
            },
            "quote": None
            if not quote
            else {
                "id": quote.id,
                "quoted_amount": quote.quoted_amount,
                "rate_per_worker": quote.rate_per_worker,
                "total_worker_days": quote.total_worker_days,
                "advance_amount": quote.advance_amount,
                "payment_model": quote.payment_model,
                "valid_until": None if not quote.valid_until else str(quote.valid_until),
                "terms_notes": quote.terms_notes,
                "status": quote.status,
            },
        },
    )


@router.post("/{requirement_id}/rating")
def rate_completed_requirement(
    requirement_id: int,
    payload: ClientRatingCreateSchema,
    current_user: User = Depends(require_role(UserRole.CLIENT.value)),
    db: Session = Depends(get_db),
):
    client_profile = get_client_profile_by_user_id(db, current_user.id)
    if not client_profile:
        raise HTTPException(status_code=400, detail="Client profile not found")

    requirement = get_requirement_by_id(db, requirement_id)
    if not requirement or requirement.client_id != client_profile.id:
        raise HTTPException(status_code=404, detail="Requirement not found")

    if requirement.status != RequirementStatus.COMPLETED.value:
        raise HTTPException(status_code=400, detail="Only completed requirements can be rated")

    worker_profile_id = None
    if payload.assignment_id is not None:
        assignment = get_assignment_by_id(db, payload.assignment_id)
        if not assignment or assignment.requirement_id != requirement.id:
            raise HTTPException(status_code=404, detail="Assignment not found")
        worker_profile_id = assignment.worker_profile_id

    rating = upsert_client_rating(
        db,
        requirement_id=requirement.id,
        rated_by_user_id=current_user.id,
        assignment_id=payload.assignment_id,
        worker_profile_id=worker_profile_id,
        rating=payload.rating,
        comments=payload.comments,
    )
    db.commit()
    db.refresh(rating)

    audit_event(
        "client_requirement_rated",
        {
            "requirement_id": requirement.id,
            "rating_id": rating.id,
            "rating": rating.rating,
            "client_user_id": current_user.id,
        },
    )

    return success_response(
        "Rating saved successfully",
        {
            "id": rating.id,
            "requirement_id": rating.requirement_id,
            "assignment_id": rating.assignment_id,
            "worker_profile_id": rating.worker_profile_id,
            "rating": rating.rating,
            "comments": rating.comments,
        },
    )


@router.post("/{requirement_id}/quote-decision")
def decide_quote(
    requirement_id: int,
    payload: QuoteDecisionSchema,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_role(UserRole.CLIENT.value)),
    db: Session = Depends(get_db),
):
    client_profile = get_client_profile_by_user_id(db, current_user.id)
    if not client_profile:
        raise HTTPException(status_code=400, detail="Client profile not found")

    requirement = get_requirement_by_id(db, requirement_id)
    if not requirement or requirement.client_id != client_profile.id:
        raise HTTPException(status_code=404, detail="Requirement not found")

    quote = get_quote_by_requirement_id(db, requirement.id)
    if not quote:
        raise HTTPException(status_code=400, detail="Quote not found")

    if quote.status != QuoteStatus.SENT.value:
        raise HTTPException(status_code=400, detail="Quote is not in decision state")

    # Inline expiry: only the approve action is blocked when the quote has passed valid_until.
    # The reject action is still allowed so the client can signal they don't want the expired quote.
    if payload.action == "approve" and quote.valid_until is not None and business_today() > quote.valid_until:
        quote.status = QuoteStatus.EXPIRED.value
        quote.updated_by_user_id = current_user.id
        try:
            validate_requirement_transition(requirement.status, RequirementStatus.UNDER_REVIEW.value)
            requirement.status = RequirementStatus.UNDER_REVIEW.value
            requirement.updated_by_user_id = current_user.id
        except ValueError:
            pass
        db.commit()
        audit_event(
            "quote_expired_inline",
            {"quote_id": quote.id, "requirement_id": requirement.id, "client_user_id": current_user.id},
        )
        raise HTTPException(
            status_code=400,
            detail="This quote has expired. Please wait for a new quote.",
        )

    # Extension quotes do not change the requirement status.
    # Approving one extends duration_days and all active assignment end_dates.
    if quote.quote_type == "extension":
        extra_days = quote.extension_days or 0
        if payload.action == "approve":
            requirement.duration_days += extra_days
            quote.status = QuoteStatus.APPROVED.value
            quote.updated_by_user_id = current_user.id
            requirement.updated_by_user_id = current_user.id
            _active_statuses = {"assigned", "accepted", "active"}
            for assignment in get_assignments_by_requirement_id(db, requirement_id):
                if assignment.status in _active_statuses and assignment.end_date is not None:
                    assignment.end_date += timedelta(days=extra_days)
            db.commit()
            audit_event(
                "extension_approved",
                {
                    "requirement_id": requirement_id,
                    "extension_quote_id": quote.id,
                    "additional_days": extra_days,
                    "new_duration_days": requirement.duration_days,
                    "client_user_id": current_user.id,
                },
            )
            # Notify workers on active assignments about the extension
            _active_statuses_notify = {"assigned", "accepted", "active"}
            for _asgn in get_assignments_by_requirement_id(db, requirement_id):
                if _asgn.status in _active_statuses_notify:
                    _wp = get_worker_profile_by_id(db, _asgn.worker_profile_id)
                    if _wp and _wp.user_id:
                        enqueue_push_to_user(
                            background_tasks,
                            db,
                            user_id=_wp.user_id,
                            title="Assignment extended",
                            body=f"Your assignment has been extended by {extra_days} day(s).",
                            data={"type": "extension_approved", "requirement_id": str(requirement_id), "screen": "JobsTab"},
                        )
        else:  # reject
            quote.status = QuoteStatus.REJECTED.value
            quote.updated_by_user_id = current_user.id
            db.commit()
            audit_event(
                "extension_rejected",
                {
                    "requirement_id": requirement_id,
                    "extension_quote_id": quote.id,
                    "client_user_id": current_user.id,
                },
            )
        return success_response(
            f"Extension quote {payload.action}d successfully",
            {
                "requirement_id": requirement_id,
                "requirement_status": requirement.status,
                "quote_status": quote.status,
            },
        )

    if payload.action == "approve":
        try:
            validate_requirement_transition(requirement.status, RequirementStatus.APPROVED.value)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        quote.status = QuoteStatus.APPROVED.value
        requirement.status = RequirementStatus.APPROVED.value
    else:
        try:
            validate_requirement_transition(requirement.status, RequirementStatus.UNDER_REVIEW.value)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        quote.status = QuoteStatus.REJECTED.value
        requirement.status = RequirementStatus.UNDER_REVIEW.value

    requirement.updated_by_user_id = current_user.id
    quote.updated_by_user_id = current_user.id
    db.commit()

    if payload.action == "approve":
        audit_event(
            "quote_decision_taken",
            {
                "requirement_id": requirement.id,
                "quote_id": quote.id,
                "action": payload.action,
                "client_user_id": current_user.id,
            },
        )
    else:
        audit_event(
            "quote_rejected_by_client",
            {
                "requirement_id": requirement.id,
                "quote_id": quote.id,
                "requirement_reverted_to": RequirementStatus.UNDER_REVIEW.value,
            },
            actor_user_id=current_user.id,
        )
    queue_notification(
        channel="sms",
        recipient=current_user.phone,
        template="quote_decision_taken",
        context={
            "requirement_id": requirement.id,
            "quote_id": quote.id,
            "action": payload.action,
            "requirement_status": requirement.status,
        },
    )

    # Notify all admins about the quote decision
    _action_label = "approved" if payload.action == "approve" else "rejected"
    _admin_body = (
        f"Client {_action_label} quote for requirement #{requirement.id}."
    )
    _admin_users = db.execute(
        select(User).where(User.role == UserRole.ADMIN.value, User.is_active.is_(True))
    ).scalars().all()
    for _admin in _admin_users:
        enqueue_push_to_user(
            background_tasks,
            db,
            user_id=_admin.id,
            title=f"Quote {_action_label} by client",
            body=_admin_body,
            data={"type": "quote_decision", "requirement_id": str(requirement.id)},
        )

    return success_response(
        f"Quote {payload.action}d successfully",
        {
            "requirement_id": requirement.id,
            "requirement_status": requirement.status,
            "quote_status": quote.status,
        },
    )


_CLIENT_CANCELLABLE_STATUSES = {
    RequirementStatus.SUBMITTED.value,
    RequirementStatus.QUOTED.value,
}


class ClientCancelRequirementSchema(BaseModel):
    reason: str

    @field_validator("reason")
    @classmethod
    def reason_min_length(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 10:
            raise ValueError("Cancellation reason must be at least 10 characters")
        return v


@router.post("/{requirement_id}/cancel")
def client_cancel_requirement(
    requirement_id: int,
    payload: ClientCancelRequirementSchema,
    current_user: User = Depends(require_role(UserRole.CLIENT.value)),
    db: Session = Depends(get_db),
):
    client_profile = get_client_profile_by_user_id(db, current_user.id)
    if not client_profile:
        raise HTTPException(status_code=400, detail="Client profile not found")

    requirement = get_requirement_by_id(db, requirement_id)
    if not requirement or requirement.client_id != client_profile.id:
        raise HTTPException(status_code=404, detail="Requirement not found")

    if requirement.status not in _CLIENT_CANCELLABLE_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel a requirement in '{requirement.status}' status. "
                   "Client cancellation is only allowed from 'submitted' or 'quoted'.",
        )

    try:
        validate_requirement_transition(requirement.status, RequirementStatus.CANCELLED.value)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    requirement.status = RequirementStatus.CANCELLED.value
    requirement.cancellation_reason = payload.reason
    requirement.updated_by_user_id = current_user.id
    db.commit()

    audit_event(
        "requirement_cancelled_by_client",
        {
            "requirement_id": requirement.id,
            "client_user_id": current_user.id,
            "reason": payload.reason,
        },
    )

    return success_response(
        "Requirement cancelled",
        {
            "id": requirement.id,
            "status": requirement.status,
            "cancellation_reason": requirement.cancellation_reason,
        },
    )
