from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies.roles import require_role
from app.core.roles import UserRole
from app.core.statuses import RequirementStatus
from app.db.deps import get_db
from app.models.quote import Quote
from app.models.user import User
from app.models.worker_interest import WorkerInterest
from app.models.worker_profile import WorkerProfile
from app.repositories.profile_repository import get_client_profile_by_id
from app.repositories.quote_repository import create_quote
from app.repositories.quote_repository import get_quote_by_requirement_id
from app.repositories.requirement_repository import (
    get_requirement_by_id,
    get_requirements_paginated_stmt,
)
from app.schemas.quote import QuoteCreateSchema
from app.services.notification_service import enqueue_push_to_user
from app.services.quote_service import build_quote_entity
from app.utils.audit import audit_event
from app.utils.pagination import PaginationParams, paginate, pagination_meta
from app.utils.response import success_response

router = APIRouter(prefix="/admin/requirements", tags=["Admin Requirements"])


@router.get("")
def list_all_requirements(
    status: str | None = Query(None, description="Filter by status"),
    pg: PaginationParams = Depends(),
    current_user: User = Depends(require_role(UserRole.ADMIN.value)),
    db: Session = Depends(get_db),
):
    stmt = get_requirements_paginated_stmt(status_filter=status)
    requirements, total = paginate(stmt, db, pg)

    data = [
        {
            "id": item.id,
            "category": item.category,
            "number_of_workers": item.number_of_workers,
            "city": item.city,
            "status": item.status,
            "start_date": str(item.start_date),
        }
        for item in requirements
    ]
    return success_response(
        "Admin requirements fetched successfully",
        {"items": data, **pagination_meta(pg, total)},
    )


@router.get("/{requirement_id}")
def admin_requirement_detail(
    requirement_id: int,
    current_user: User = Depends(require_role(UserRole.ADMIN.value)),
    db: Session = Depends(get_db),
):
    requirement = get_requirement_by_id(db, requirement_id)
    if not requirement:
        raise HTTPException(status_code=404, detail="Requirement not found")

    quote = get_quote_by_requirement_id(db, requirement.id)

    return success_response(
        "Requirement detail fetched successfully",
        {
            "id": requirement.id,
            "client_id": requirement.client_id,
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
                "internal_notes": quote.internal_notes,
                "status": quote.status,
            },
        },
    )


@router.get("/{requirement_id}/interests")
def list_requirement_interests(
    requirement_id: int,
    current_user: User = Depends(require_role(UserRole.ADMIN.value)),
    db: Session = Depends(get_db),
):
    """List all workers who have expressed interest in a requirement, with their profile info."""
    requirement = get_requirement_by_id(db, requirement_id)
    if not requirement:
        raise HTTPException(status_code=404, detail="Requirement not found")

    rows = db.execute(
        select(WorkerInterest, WorkerProfile)
        .join(WorkerProfile, WorkerProfile.id == WorkerInterest.worker_profile_id)
        .where(WorkerInterest.requirement_id == requirement_id)
        .order_by(WorkerInterest.expressed_at.asc())
    ).all()

    data = [
        {
            "interest_id": interest.id,
            "status": interest.status,
            "expressed_at": interest.expressed_at.isoformat(),
            "worker_profile_id": profile.id,
            "worker_user_id": profile.user_id,
            "full_name": profile.full_name,
            "city": profile.city,
            "category": profile.category,
            "subcategory": profile.subcategory,
            "verification_status": profile.verification_status,
            "is_available": profile.is_available,
        }
        for interest, profile in rows
    ]

    return success_response("Requirement interests fetched successfully", data)


@router.post("/{requirement_id}/mark-review")
def mark_requirement_under_review(
    requirement_id: int,
    current_user: User = Depends(require_role(UserRole.ADMIN.value)),
    db: Session = Depends(get_db),
):
    requirement = get_requirement_by_id(db, requirement_id)
    if not requirement:
        raise HTTPException(status_code=404, detail="Requirement not found")

    if requirement.status != RequirementStatus.SUBMITTED.value:
        raise HTTPException(status_code=400, detail="Only submitted requirements can be marked under review")

    requirement.status = RequirementStatus.UNDER_REVIEW.value
    requirement.updated_by_user_id = current_user.id
    db.commit()

    audit_event(
        "requirement_marked_under_review",
        {"requirement_id": requirement.id, "admin_user_id": current_user.id},
    )

    return success_response("Requirement marked under review", {"id": requirement.id, "status": requirement.status})


@router.post("/{requirement_id}/quote")
def create_admin_quote(
    requirement_id: int,
    payload: QuoteCreateSchema,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_role(UserRole.ADMIN.value)),
    db: Session = Depends(get_db),
):
    requirement = get_requirement_by_id(db, requirement_id)
    if not requirement:
        raise HTTPException(status_code=404, detail="Requirement not found")

    if payload.requirement_id != requirement_id:
        raise HTTPException(status_code=400, detail="Requirement ID mismatch")

    existing_quote = get_quote_by_requirement_id(db, requirement.id)
    if existing_quote:
        raise HTTPException(status_code=400, detail="A quote already exists for this requirement")

    if requirement.status != RequirementStatus.UNDER_REVIEW.value:
        raise HTTPException(status_code=400, detail="Requirement must be under review before creating a quote")

    quote: Quote = build_quote_entity(payload, current_user.id)
    create_quote(db, quote)

    requirement.status = RequirementStatus.QUOTED.value
    requirement.updated_by_user_id = current_user.id

    db.commit()
    db.refresh(quote)

    audit_event(
        "quote_created",
        {
            "quote_id": quote.id,
            "requirement_id": requirement.id,
            "admin_user_id": current_user.id,
        },
    )

    client_profile = get_client_profile_by_id(db, requirement.client_id)
    if client_profile:
        enqueue_push_to_user(
            background_tasks,
            db,
            user_id=client_profile.user_id,
            title="Quote ready for your request",
            body="Annai Illam has sent you a quote. Open the app to review and approve.",
            data={"screen": "JobsTab"},
        )

    return success_response(
        "Quote created successfully",
        {
            "quote_id": quote.id,
            "requirement_id": requirement.id,
            "quote_status": quote.status,
            "requirement_status": requirement.status,
        },
    )
