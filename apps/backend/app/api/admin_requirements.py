from datetime import timedelta
import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.dependencies.roles import require_role
from app.api.dependencies.scoping import get_accessible_client_ids
from app.core.assignment_constants import AssignmentStatus
from app.core.roles import UserRole
from app.core.statuses import QuoteStatus, RequirementStatus, validate_requirement_transition
from app.db.deps import get_db
from app.models.assignment import Assignment
from app.models.attendance import Attendance
from app.models.quote import Quote
from app.models.requirement import Requirement
from app.models.user import User
from app.models.worker_interest import WorkerInterest
from app.models.worker_profile import WorkerProfile
from app.repositories.assignment_repository import get_assignments_by_requirement_id
from app.repositories.profile_repository import get_client_profile_by_id
from app.repositories.profile_repository import get_worker_profile_by_id
from app.repositories.quote_repository import create_quote
from app.repositories.quote_repository import get_quote_by_requirement_id
from app.repositories.requirement_repository import (
    get_requirement_by_id,
    get_requirements_paginated_stmt,
)
from app.schemas.quote import QuoteCreateSchema
from app.services.notification_service import enqueue_push_to_user
from app.services.quote_service import build_quote_entity
from app.services.payment_ledger_service import calculate_quote_total
from app.utils.audit import audit_event
from app.utils.pagination import PaginationParams, paginate, pagination_meta
from app.utils.time import business_today
from app.utils.response import success_response

router = APIRouter(prefix="/admin/requirements", tags=["Admin Requirements"])

logger = logging.getLogger(__name__)


@router.get("")
def list_all_requirements(
    status: str | None = Query(None, description="Filter by status"),
    pg: PaginationParams = Depends(),
    current_user: User = Depends(require_role(UserRole.ADMIN.value)),
    accessible_client_ids: list[int] | None = Depends(get_accessible_client_ids),
    db: Session = Depends(get_db),
):
    stmt = get_requirements_paginated_stmt(status_filter=status)
    if accessible_client_ids is not None:
        if not accessible_client_ids:
            return success_response(
                "Admin requirements fetched successfully",
                {"items": [], **pagination_meta(pg, 0)},
            )
        stmt = stmt.where(Requirement.client_id.in_(accessible_client_ids))
    requirements, total = paginate(stmt, db, pg)

    data = [
        {
            "id": item.id,
            "category": item.category,
            "number_of_workers": item.number_of_workers,
            "city": item.city,
            "status": item.status,
            "start_date": str(item.start_date),
            "created_at": item.created_at.isoformat(),
            "sla_hours": item.sla_hours,
            "sla_breach_notified_at": item.sla_breach_notified_at.isoformat() if item.sla_breach_notified_at else None,
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
    accessible_client_ids: list[int] | None = Depends(get_accessible_client_ids),
    db: Session = Depends(get_db),
):
    requirement = get_requirement_by_id(db, requirement_id)
    if not requirement:
        raise HTTPException(status_code=404, detail="Requirement not found")
    if accessible_client_ids is not None and requirement.client_id not in accessible_client_ids:
        raise HTTPException(status_code=403, detail="Not authorised to access this requirement")

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
            "site_latitude": requirement.site_latitude,
            "site_longitude": requirement.site_longitude,
            "geofence_radius_meters": requirement.geofence_radius_meters,
            "require_geofence": requirement.require_geofence,
            "status": requirement.status,
            "rejection_reason": requirement.rejection_reason,
            "cancellation_reason": requirement.cancellation_reason,
            "quote": None
            if not quote
            else {
                "id": quote.id,
                "quoted_amount": quote.quoted_amount,
                "rate_per_worker": quote.rate_per_worker,
                "worker_daily_rate": quote.worker_daily_rate,
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
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_role(UserRole.ADMIN.value)),
    db: Session = Depends(get_db),
):
    requirement = get_requirement_by_id(db, requirement_id)
    if not requirement:
        raise HTTPException(status_code=404, detail="Requirement not found")

    try:
        validate_requirement_transition(requirement.status, RequirementStatus.UNDER_REVIEW.value)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    requirement.status = RequirementStatus.UNDER_REVIEW.value
    requirement.updated_by_user_id = current_user.id
    db.commit()

    audit_event(
        "requirement_marked_under_review",
        {"requirement_id": requirement.id, "admin_user_id": current_user.id},
    )

    # Notify client that their requirement is being reviewed
    client_profile = get_client_profile_by_id(db, requirement.client_id)
    if client_profile:
        enqueue_push_to_user(
            background_tasks,
            db,
            user_id=client_profile.user_id,
            title="Requirement under review",
            body="Your staffing request is being reviewed by our team. We will send you a quote shortly.",
            data={"screen": "JobsTab"},
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
    if existing_quote and existing_quote.status not in {
        QuoteStatus.REJECTED.value,
        QuoteStatus.EXPIRED.value,
    }:
        raise HTTPException(status_code=400, detail="A quote already exists for this requirement")

    try:
        validate_requirement_transition(requirement.status, RequirementStatus.QUOTED.value)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    quote: Quote = build_quote_entity(payload, current_user.id)

    # Server-side amount verification (Polish 8).
    # If rate_per_worker is supplied, recompute the expected total and override
    # any tampered or miscalculated quoted_amount the frontend may have sent.
    if payload.rate_per_worker:
        expected_amount = calculate_quote_total(
            payload.rate_per_worker,
            requirement.number_of_workers,
            requirement.duration_days,
        )
        if quote.quoted_amount != expected_amount:
            discrepancy_pct = (
                abs(quote.quoted_amount - expected_amount) / expected_amount * 100
            )
            if discrepancy_pct > 5:
                logger.warning(
                    "Quote amount mismatch for requirement %d: submitted %d, "
                    "expected %d (%.1f%% off) — overriding silently",
                    requirement.id,
                    quote.quoted_amount,
                    expected_amount,
                    discrepancy_pct,
                )
            quote.quoted_amount = expected_amount

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
            "quoted_amount": quote.quoted_amount,
        },
    )


@router.post("/{requirement_id}/complete")
def complete_requirement(
    requirement_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_role(UserRole.ADMIN.value)),
    db: Session = Depends(get_db),
):
    requirement = get_requirement_by_id(db, requirement_id)
    if not requirement:
        raise HTTPException(status_code=404, detail="Requirement not found")

    try:
        validate_requirement_transition(requirement.status, RequirementStatus.COMPLETED.value)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    # Block completion if any attendance records are still pending approval
    pending_count: int = db.execute(
        select(func.count(Attendance.id))
        .join(Assignment, Attendance.assignment_id == Assignment.id)
        .where(
            Assignment.requirement_id == requirement_id,
            Attendance.approval_status == "pending",
        )
    ).scalar_one()
    if pending_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot complete job — {pending_count} attendance record(s) are still pending approval",
        )

    requirement.status = RequirementStatus.COMPLETED.value
    requirement.updated_by_user_id = current_user.id

    # Cascade completion to all still-active assignments so the
    # Salary Disbursements section can create disbursements for them.
    _completable = {
        AssignmentStatus.ASSIGNED.value,
        AssignmentStatus.ACCEPTED.value,
        AssignmentStatus.ACTIVE.value,
    }
    active_assignments = db.execute(
        select(Assignment).where(
            Assignment.requirement_id == requirement_id,
            Assignment.status.in_(_completable),
        )
    ).scalars().all()
    for a in active_assignments:
        a.status = AssignmentStatus.COMPLETED.value

    db.commit()

    audit_event(
        "requirement_marked_complete",
        {"requirement_id": requirement.id, "admin_user_id": current_user.id},
    )

    # Notify client that job is complete and ask them to rate
    client_profile = get_client_profile_by_id(db, requirement.client_id)
    if client_profile:
        enqueue_push_to_user(
            background_tasks,
            db,
            user_id=client_profile.user_id,
            title="Your job is complete",
            body="Your staffing job has been completed. Please rate your workers to help us improve.",
            data={"screen": "JobsTab"},
        )

    return success_response(
        "Requirement marked as completed",
        {"id": requirement.id, "status": requirement.status},
    )


class RejectRequirementSchema(BaseModel):
    reason: str

    @field_validator("reason")
    @classmethod
    def reason_not_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Rejection reason must not be blank")
        return v


@router.post("/{requirement_id}/reject")
def reject_requirement(
    requirement_id: int,
    payload: RejectRequirementSchema,
    current_user: User = Depends(require_role(UserRole.ADMIN.value)),
    db: Session = Depends(get_db),
):
    requirement = get_requirement_by_id(db, requirement_id)
    if not requirement:
        raise HTTPException(status_code=404, detail="Requirement not found")

    try:
        validate_requirement_transition(requirement.status, RequirementStatus.REJECTED.value)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    requirement.status = RequirementStatus.REJECTED.value
    requirement.rejection_reason = payload.reason
    requirement.updated_by_user_id = current_user.id
    db.commit()

    audit_event(
        "requirement_rejected",
        {
            "requirement_id": requirement.id,
            "admin_user_id": current_user.id,
            "reason": payload.reason,
        },
    )

    return success_response(
        "Requirement rejected",
        {
            "id": requirement.id,
            "status": requirement.status,
            "rejection_reason": requirement.rejection_reason,
        },
    )


_CANCELLABLE_ASSIGNMENT_STATUSES = {
    AssignmentStatus.ASSIGNED.value,
    AssignmentStatus.ACCEPTED.value,
    AssignmentStatus.ACTIVE.value,
}


class CancelRequirementSchema(BaseModel):
    reason: str

    @field_validator("reason")
    @classmethod
    def reason_min_length(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 10:
            raise ValueError("Cancellation reason must be at least 10 characters")
        return v


@router.post("/{requirement_id}/cancel")
def cancel_requirement(
    requirement_id: int,
    payload: CancelRequirementSchema,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_role(UserRole.ADMIN.value)),
    db: Session = Depends(get_db),
):
    requirement = get_requirement_by_id(db, requirement_id)
    if not requirement:
        raise HTTPException(status_code=404, detail="Requirement not found")

    try:
        validate_requirement_transition(requirement.status, RequirementStatus.CANCELLED.value)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    # Cancel all active assignments and free workers
    assignments = get_assignments_by_requirement_id(db, requirement_id)
    cancelled_worker_user_ids: list[int] = []
    for assignment in assignments:
        if assignment.status in _CANCELLABLE_ASSIGNMENT_STATUSES:
            assignment.status = AssignmentStatus.CANCELLED.value
            worker_profile = get_worker_profile_by_id(db, assignment.worker_profile_id)
            if worker_profile:
                worker_profile.is_available = True
                if worker_profile.user_id:
                    cancelled_worker_user_ids.append(worker_profile.user_id)

    requirement.status = RequirementStatus.CANCELLED.value
    requirement.cancellation_reason = payload.reason
    requirement.updated_by_user_id = current_user.id
    db.commit()

    audit_event(
        "requirement_cancelled",
        {
            "requirement_id": requirement.id,
            "admin_user_id": current_user.id,
            "reason": payload.reason,
            "assignments_cancelled": len(cancelled_worker_user_ids),
        },
    )

    # Notify affected workers
    for worker_user_id in cancelled_worker_user_ids:
        enqueue_push_to_user(
            background_tasks,
            db,
            user_id=worker_user_id,
            title="Job cancelled",
            body="A job you were assigned to has been cancelled by the admin.",
            data={"screen": "JobsTab"},
        )

    # Notify client
    client_profile = get_client_profile_by_id(db, requirement.client_id)
    if client_profile:
        enqueue_push_to_user(
            background_tasks,
            db,
            user_id=client_profile.user_id,
            title="Your request has been cancelled",
            body=f"Requirement REQ-{requirement.id} has been cancelled. Reason: {payload.reason}",
            data={"screen": "JobsTab"},
        )

    return success_response(
        "Requirement cancelled",
        {
            "id": requirement.id,
            "status": requirement.status,
            "cancellation_reason": requirement.cancellation_reason,
        },
    )


_EXTENSION_ALLOWED_STATUSES = {
    RequirementStatus.IN_PROGRESS.value,
    RequirementStatus.WORKERS_ASSIGNED.value,
}


class RequestExtensionSchema(BaseModel):
    additional_days: int = Field(ge=1, description="Number of additional days to extend the job")
    new_rate_per_worker: int = Field(ge=1, description="Daily rate per worker in paise for the extension period")


@router.post("/{requirement_id}/request-extension")
def request_extension(
    requirement_id: int,
    payload: RequestExtensionSchema,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_role(UserRole.ADMIN.value)),
    db: Session = Depends(get_db),
):
    requirement = get_requirement_by_id(db, requirement_id)
    if not requirement:
        raise HTTPException(status_code=404, detail="Requirement not found")

    if requirement.status not in _EXTENSION_ALLOWED_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Extension can only be requested when requirement is in "
                f"{sorted(_EXTENSION_ALLOWED_STATUSES)}. Current status: '{requirement.status}'"
            ),
        )

    # Block duplicate pending extension quotes
    existing_extension = db.execute(
        select(Quote)
        .where(
            Quote.requirement_id == requirement_id,
            Quote.quote_type == "extension",
            Quote.status == QuoteStatus.SENT.value,
        )
    ).scalar_one_or_none()
    if existing_extension:
        raise HTTPException(
            status_code=400,
            detail="A pending extension quote already exists for this requirement",
        )

    # Derive payment_model from the original approved quote
    original_quote = get_quote_by_requirement_id(db, requirement_id)
    payment_model = original_quote.payment_model if original_quote else "client_pays_company"

    extension_amount = payload.new_rate_per_worker * requirement.number_of_workers * payload.additional_days

    extension_quote = Quote(
        requirement_id=requirement_id,
        quoted_amount=extension_amount,
        rate_per_worker=payload.new_rate_per_worker,
        total_worker_days=requirement.number_of_workers * payload.additional_days,
        payment_model=payment_model,
        quote_type="extension",
        extension_days=payload.additional_days,
        status=QuoteStatus.SENT.value,
        valid_until=business_today() + timedelta(days=7),
        created_by_user_id=current_user.id,
    )
    create_quote(db, extension_quote)
    db.commit()
    db.refresh(extension_quote)

    audit_event(
        "extension_quote_sent",
        {
            "requirement_id": requirement_id,
            "extension_quote_id": extension_quote.id,
            "additional_days": payload.additional_days,
            "extension_amount": extension_amount,
            "admin_user_id": current_user.id,
        },
    )

    client_profile = get_client_profile_by_id(db, requirement.client_id)
    if client_profile:
        enqueue_push_to_user(
            background_tasks,
            db,
            user_id=client_profile.user_id,
            title="Job extension quote sent",
            body=f"A quote for {payload.additional_days} additional days has been sent for your job.",
            data={"screen": "JobsTab"},
        )

    return success_response(
        "Extension quote sent successfully",
        {
            "extension_quote_id": extension_quote.id,
            "requirement_id": requirement_id,
            "additional_days": payload.additional_days,
            "extension_amount": extension_amount,
            "valid_until": str(extension_quote.valid_until),
            "quote_status": extension_quote.status,
        },
    )
