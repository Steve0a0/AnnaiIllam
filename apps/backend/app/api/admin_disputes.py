from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies.roles import require_role
from app.api.dependencies.scoping import get_accessible_client_ids
from app.core.roles import UserRole
from app.db.deps import get_db
from app.models.dispute import Dispute, DisputeCreditNote
from app.models.client_profile import ClientProfile
from app.models.user import User
from app.services.notification_service import enqueue_push_to_user
from app.utils.audit import audit_event
from app.utils.pagination import PaginationParams, paginate, pagination_meta
from app.utils.response import success_response
from app.utils.time import utcnow

router = APIRouter(prefix="/admin/disputes", tags=["Admin Disputes"])

_VALID_STATUSES = {"open", "under_review", "resolved", "closed"}


def _dispute_detail(d: Dispute) -> dict:
    return {
        "id": d.id,
        "requirement_id": d.requirement_id,
        "raised_by_user_id": d.raised_by_user_id,
        "dispute_type": d.dispute_type,
        "description": d.description,
        "status": d.status,
        "resolution_notes": d.resolution_notes,
        "resolved_by_user_id": d.resolved_by_user_id,
        "resolved_at": d.resolved_at.isoformat() if d.resolved_at else None,
        "credit_amount": d.credit_amount,
        "created_at": d.created_at.isoformat(),
        "updated_at": d.updated_at.isoformat(),
    }


@router.get("")
def list_all_disputes(
    status: str | None = Query(None, description="Filter by status"),
    pg: PaginationParams = Depends(),
    current_user: User = Depends(require_role(UserRole.ADMIN.value)),
    accessible_client_ids: list[int] | None = Depends(get_accessible_client_ids),
    db: Session = Depends(get_db),
):
    from app.models.requirement import Requirement
    stmt = select(Dispute).order_by(Dispute.created_at.desc())
    if status:
        if status not in _VALID_STATUSES:
            raise HTTPException(status_code=400, detail="Invalid status filter")
        stmt = stmt.where(Dispute.status == status)
    if accessible_client_ids is not None:
        if not accessible_client_ids:
            return success_response(
                "Disputes fetched successfully",
                {"items": [], **pagination_meta(pg, 0)},
            )
        req_subq = select(Requirement.id).where(Requirement.client_id.in_(accessible_client_ids))
        stmt = stmt.where(Dispute.requirement_id.in_(req_subq))

    disputes, total = paginate(stmt, db, pg)
    return success_response(
        "Disputes fetched successfully",
        {"items": [_dispute_detail(d) for d in disputes], **pagination_meta(pg, total)},
    )


@router.get("/{dispute_id}")
def get_dispute_detail(
    dispute_id: int,
    current_user: User = Depends(require_role(UserRole.ADMIN.value)),
    db: Session = Depends(get_db),
):
    dispute = db.get(Dispute, dispute_id)
    if not dispute:
        raise HTTPException(status_code=404, detail="Dispute not found")
    return success_response("Dispute detail fetched successfully", _dispute_detail(dispute))


@router.patch("/{dispute_id}/review")
def review_dispute(
    dispute_id: int,
    current_user: User = Depends(require_role(UserRole.ADMIN.value)),
    db: Session = Depends(get_db),
):
    dispute = db.get(Dispute, dispute_id)
    if not dispute:
        raise HTTPException(status_code=404, detail="Dispute not found")
    if dispute.status != "open":
        raise HTTPException(status_code=400, detail="Only open disputes can be moved to under_review")

    dispute.status = "under_review"
    db.commit()
    db.refresh(dispute)

    audit_event(
        "dispute_under_review",
        {"dispute_id": dispute.id, "admin_user_id": current_user.id},
    )

    return success_response("Dispute marked as under review", _dispute_detail(dispute))


class ResolveDisputeSchema(BaseModel):
    resolution_notes: str
    credit_amount: int | None = None  # optional, in paise


@router.patch("/{dispute_id}/resolve")
def resolve_dispute(
    dispute_id: int,
    payload: ResolveDisputeSchema,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_role(UserRole.ADMIN.value)),
    db: Session = Depends(get_db),
):
    dispute = db.get(Dispute, dispute_id)
    if not dispute:
        raise HTTPException(status_code=404, detail="Dispute not found")
    if dispute.status not in {"open", "under_review"}:
        raise HTTPException(status_code=400, detail="Dispute cannot be resolved from its current status")

    dispute.status = "resolved"
    dispute.resolution_notes = payload.resolution_notes
    dispute.resolved_by_user_id = current_user.id
    dispute.resolved_at = utcnow()

    if payload.credit_amount and payload.credit_amount > 0:
        dispute.credit_amount = payload.credit_amount
        credit_note = DisputeCreditNote(
            dispute_id=dispute.id,
            amount=payload.credit_amount,
            created_by_user_id=current_user.id,
        )
        db.add(credit_note)

    db.commit()
    db.refresh(dispute)

    audit_event(
        "dispute_resolved",
        {
            "dispute_id": dispute.id,
            "admin_user_id": current_user.id,
            "credit_amount": dispute.credit_amount,
        },
    )

    # Notify client
    client_user_id = _get_client_user_id_by_requirement(db, dispute.requirement_id)
    if client_user_id:
        enqueue_push_to_user(
            background_tasks,
            db,
            user_id=client_user_id,
            title="Dispute Resolved",
            body=f"Your dispute has been resolved. {payload.resolution_notes}",
            data={"type": "dispute_resolved", "dispute_id": str(dispute.id), "screen": "ComplaintsTab"},
        )

    return success_response("Dispute resolved successfully", _dispute_detail(dispute))


@router.patch("/{dispute_id}/close")
def close_dispute(
    dispute_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_role(UserRole.ADMIN.value)),
    db: Session = Depends(get_db),
):
    dispute = db.get(Dispute, dispute_id)
    if not dispute:
        raise HTTPException(status_code=404, detail="Dispute not found")
    if dispute.status not in {"open", "under_review"}:
        raise HTTPException(status_code=400, detail="Dispute cannot be closed from its current status")

    dispute.status = "closed"
    db.commit()
    db.refresh(dispute)

    audit_event(
        "dispute_closed",
        {"dispute_id": dispute.id, "admin_user_id": current_user.id},
    )

    # Notify client
    client_user_id = _get_client_user_id_by_requirement(db, dispute.requirement_id)
    if client_user_id:
        enqueue_push_to_user(
            background_tasks,
            db,
            user_id=client_user_id,
            title="Dispute Closed",
            body="Your dispute has been closed. Please contact support if you have questions.",
            data={"type": "dispute_closed", "dispute_id": str(dispute.id), "screen": "ComplaintsTab"},
        )

    return success_response("Dispute closed successfully", _dispute_detail(dispute))


def _get_client_user_id_by_requirement(db: Session, requirement_id: int) -> int | None:
    from app.models.requirement import Requirement
    stmt = (
        select(ClientProfile.user_id)
        .join(Requirement, Requirement.client_id == ClientProfile.id)
        .where(Requirement.id == requirement_id)
    )
    return db.execute(stmt).scalar_one_or_none()
