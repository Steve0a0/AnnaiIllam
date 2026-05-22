from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies.roles import require_role
from app.core.roles import UserRole
from app.core.statuses import QuoteStatus, RequirementStatus
from app.db.deps import get_db
from app.models.user import User
from app.repositories.client_repository import get_client_profile_by_user_id
from app.repositories.assignment_repository import get_assignment_by_id, get_assignments_by_requirement_id
from app.repositories.attendance_repository import get_attendance_for_assignment
from app.repositories.payment_repository import get_client_payments_by_client_id
from app.repositories.profile_repository import get_worker_profile_by_id
from app.repositories.quote_repository import get_quote_by_requirement_id
from app.repositories.rating_repository import get_client_rating_for_requirement, upsert_client_rating
from app.repositories.requirement_repository import (
    create_requirement,
    get_requirement_by_id,
    get_requirements_by_client_id,
)
from app.schemas.quote import QuoteDecisionSchema
from app.schemas.rating import ClientRatingCreateSchema
from app.schemas.requirement import RequirementCreateSchema
from app.services.notification_service import queue_notification
from app.services.requirement_service import build_requirement_entity
from app.utils.audit import audit_event
from app.utils.response import success_response

router = APIRouter(prefix="/client/requirements", tags=["Client Requirements"])


@router.post("")
def create_client_requirement(
    payload: RequirementCreateSchema,
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

    return success_response(
        "Requirement created successfully",
        {
            "id": requirement.id,
            "status": requirement.status,
        },
    )


@router.get("")
def list_my_requirements(
    current_user: User = Depends(require_role(UserRole.CLIENT.value)),
    db: Session = Depends(get_db),
):
    client_profile = get_client_profile_by_user_id(db, current_user.id)
    if not client_profile:
        raise HTTPException(status_code=400, detail="Client profile not found")

    requirements = get_requirements_by_client_id(db, client_profile.id)

    data = [
        {
            "id": item.id,
            "category": item.category,
            "number_of_workers": item.number_of_workers,
            "city": item.city,
            "start_date": str(item.start_date),
            "status": item.status,
        }
        for item in requirements
    ]
    return success_response("Requirements fetched successfully", data)


@router.get("/summary")
def get_client_dashboard_summary(
    current_user: User = Depends(require_role(UserRole.CLIENT.value)),
    db: Session = Depends(get_db),
):
    client_profile = get_client_profile_by_user_id(db, current_user.id)
    if not client_profile:
        raise HTTPException(status_code=400, detail="Client profile not found")

    requirements = get_requirements_by_client_id(db, client_profile.id)
    payments = get_client_payments_by_client_id(db, client_profile.id)

    open_statuses = {
        RequirementStatus.SUBMITTED.value,
        RequirementStatus.UNDER_REVIEW.value,
        RequirementStatus.QUOTED.value,
        RequirementStatus.APPROVED.value,
        RequirementStatus.ASSIGNED.value,
        RequirementStatus.IN_PROGRESS.value,
    }
    pending_quote_statuses = {
        RequirementStatus.SUBMITTED.value,
        RequirementStatus.UNDER_REVIEW.value,
        RequirementStatus.QUOTED.value,
    }

    return success_response(
        "Client dashboard summary fetched successfully",
        {
            "total_requirements": len(requirements),
            "open_jobs": sum(1 for item in requirements if item.status in open_statuses),
            "pending_quotes": sum(1 for item in requirements if item.status in pending_quote_statuses),
            "completed_jobs": sum(1 for item in requirements if item.status == RequirementStatus.COMPLETED.value),
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
                "salary_amount": assignment.salary_amount,
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

    if payload.action == "approve":
        quote.status = QuoteStatus.APPROVED.value
        requirement.status = RequirementStatus.APPROVED.value
    else:
        quote.status = QuoteStatus.REJECTED.value
        requirement.status = RequirementStatus.REJECTED.value

    requirement.updated_by_user_id = current_user.id
    quote.updated_by_user_id = current_user.id
    db.commit()

    audit_event(
        "quote_decision_taken",
        {
            "requirement_id": requirement.id,
            "quote_id": quote.id,
            "action": payload.action,
            "client_user_id": current_user.id,
        },
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

    return success_response(
        f"Quote {payload.action}d successfully",
        {
            "requirement_id": requirement.id,
            "requirement_status": requirement.status,
            "quote_status": quote.status,
        },
    )
