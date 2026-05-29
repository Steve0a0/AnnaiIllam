from datetime import date

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies.roles import require_role
from app.core.assignment_constants import AssignmentStatus
from app.core.roles import UserRole
from app.db.deps import get_db
from app.models.assignment import Assignment
from app.models.user import User
from app.models.worker_disbursement import WorkerDisbursement
from app.repositories.assignment_repository import get_assignment_by_id
from app.repositories.profile_repository import get_worker_profile_by_id
from app.services.notification_service import enqueue_push_to_user
from app.utils.audit import audit_event
from app.utils.pagination import PaginationParams, paginate, pagination_meta
from app.utils.response import success_response
from app.utils.time import utcnow

router = APIRouter(prefix="/admin/disbursements", tags=["Admin Disbursements"])


def _rupees(paise: int) -> str:
    """Format paise as human-readable rupee string."""
    rupees = paise // 100
    paise_part = paise % 100
    if paise_part:
        return f"₹{rupees}.{paise_part:02d}"
    return f"₹{rupees}"


def _serialize(d: WorkerDisbursement) -> dict:
    return {
        "id": d.id,
        "assignment_id": d.assignment_id,
        "worker_profile_id": d.worker_profile_id,
        "amount": d.amount,
        "disbursement_status": d.disbursement_status,
        "scheduled_date": str(d.scheduled_date),
        "paid_at": d.paid_at.isoformat() if d.paid_at else None,
        "payment_reference": d.payment_reference,
        "notes": d.notes,
        "created_by_user_id": d.created_by_user_id,
        "created_at": d.created_at.isoformat(),
        "updated_at": d.updated_at.isoformat(),
    }


class DisbursementCreateSchema(BaseModel):
    assignment_id: int
    amount: int = Field(ge=1)  # paise
    scheduled_date: date


class MarkPaidSchema(BaseModel):
    payment_reference: str = Field(min_length=1)


class MarkFailedSchema(BaseModel):
    notes: str = Field(min_length=1)


@router.post("")
def create_disbursement(
    payload: DisbursementCreateSchema,
    current_user: User = Depends(require_role(UserRole.ADMIN.value)),
    db: Session = Depends(get_db),
):
    assignment = get_assignment_by_id(db, payload.assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    if assignment.status != AssignmentStatus.COMPLETED.value:
        raise HTTPException(
            status_code=400,
            detail="Disbursement can only be created for completed assignments",
        )

    existing = db.execute(
        select(WorkerDisbursement).where(
            WorkerDisbursement.assignment_id == payload.assignment_id
        )
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=409,
            detail="A disbursement already exists for this assignment",
        )

    disbursement = WorkerDisbursement(
        assignment_id=payload.assignment_id,
        worker_profile_id=assignment.worker_profile_id,
        amount=payload.amount,
        disbursement_status="pending",
        scheduled_date=payload.scheduled_date,
        created_by_user_id=current_user.id,
    )
    db.add(disbursement)
    db.commit()
    db.refresh(disbursement)

    audit_event(
        "disbursement_created",
        {
            "disbursement_id": disbursement.id,
            "assignment_id": disbursement.assignment_id,
            "worker_profile_id": disbursement.worker_profile_id,
            "amount": disbursement.amount,
            "admin_user_id": current_user.id,
        },
    )

    return success_response("Disbursement created successfully", _serialize(disbursement))


@router.patch("/{disbursement_id}/paid")
def mark_disbursement_paid(
    disbursement_id: int,
    payload: MarkPaidSchema,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_role(UserRole.ADMIN.value)),
    db: Session = Depends(get_db),
):
    disbursement = db.get(WorkerDisbursement, disbursement_id)
    if not disbursement:
        raise HTTPException(status_code=404, detail="Disbursement not found")

    if disbursement.disbursement_status == "paid":
        raise HTTPException(status_code=400, detail="Disbursement is already marked as paid")

    disbursement.disbursement_status = "paid"
    disbursement.paid_at = utcnow()
    disbursement.payment_reference = payload.payment_reference
    db.commit()

    audit_event(
        "disbursement_paid",
        {
            "disbursement_id": disbursement.id,
            "assignment_id": disbursement.assignment_id,
            "payment_reference": payload.payment_reference,
            "admin_user_id": current_user.id,
        },
    )

    worker_profile = get_worker_profile_by_id(db, disbursement.worker_profile_id)
    if worker_profile:
        enqueue_push_to_user(
            background_tasks,
            db,
            user_id=worker_profile.user_id,
            title="Payment Processed",
            body=(
                f"Your payment of {_rupees(disbursement.amount)} has been processed. "
                f"Ref: {payload.payment_reference}"
            ),
            data={"type": "disbursement_paid", "disbursement_id": disbursement.id, "screen": "EarningsTab"},
        )

    return success_response("Disbursement marked as paid", _serialize(disbursement))


@router.patch("/{disbursement_id}/failed")
def mark_disbursement_failed(
    disbursement_id: int,
    payload: MarkFailedSchema,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_role(UserRole.ADMIN.value)),
    db: Session = Depends(get_db),
):
    disbursement = db.get(WorkerDisbursement, disbursement_id)
    if not disbursement:
        raise HTTPException(status_code=404, detail="Disbursement not found")

    if disbursement.disbursement_status == "failed":
        raise HTTPException(status_code=400, detail="Disbursement is already marked as failed")

    disbursement.disbursement_status = "failed"
    disbursement.notes = payload.notes
    db.commit()

    audit_event(
        "disbursement_failed",
        {
            "disbursement_id": disbursement.id,
            "assignment_id": disbursement.assignment_id,
            "notes": payload.notes,
            "admin_user_id": current_user.id,
        },
    )

    worker_profile = get_worker_profile_by_id(db, disbursement.worker_profile_id)
    if worker_profile:
        enqueue_push_to_user(
            background_tasks,
            db,
            user_id=worker_profile.user_id,
            title="Payment Issue",
            body="There was an issue processing your payment. Please contact support.",
            data={"type": "disbursement_failed", "disbursement_id": disbursement.id, "screen": "EarningsTab"},
        )

    return success_response("Disbursement marked as failed", _serialize(disbursement))


@router.get("/requirement/{requirement_id}")
def list_disbursements_by_requirement(
    requirement_id: int,
    current_user: User = Depends(require_role(UserRole.ADMIN.value)),
    db: Session = Depends(get_db),
):
    rows = db.execute(
        select(WorkerDisbursement)
        .join(Assignment, WorkerDisbursement.assignment_id == Assignment.id)
        .where(Assignment.requirement_id == requirement_id)
        .order_by(WorkerDisbursement.created_at.desc())
    ).scalars().all()

    return success_response(
        "Disbursements fetched successfully",
        [_serialize(d) for d in rows],
    )


@router.get("/worker/{worker_profile_id}")
def list_disbursements_by_worker(
    worker_profile_id: int,
    pg: PaginationParams = Depends(),
    current_user: User = Depends(require_role(UserRole.ADMIN.value)),
    db: Session = Depends(get_db),
):
    stmt = (
        select(WorkerDisbursement)
        .where(WorkerDisbursement.worker_profile_id == worker_profile_id)
        .order_by(WorkerDisbursement.created_at.desc())
    )
    items, total = paginate(stmt, db, pg)

    return success_response(
        "Disbursements fetched successfully",
        {"items": [_serialize(d) for d in items], **pagination_meta(pg, total)},
    )
