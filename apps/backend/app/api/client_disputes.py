from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies.roles import require_role
from app.core.roles import UserRole
from app.core.statuses import RequirementStatus
from app.db.deps import get_db
from app.models.dispute import Dispute
from app.models.user import User
from app.repositories.client_repository import get_client_profile_by_user_id
from app.repositories.requirement_repository import get_requirement_by_id
from app.services.notification_service import enqueue_push_to_user
from app.utils.audit import audit_event
from app.utils.response import success_response

router = APIRouter(prefix="/client/disputes", tags=["Client Disputes"])

_VALID_DISPUTE_TYPES = {"attendance", "quality", "billing", "other"}


class DisputeCreateSchema(BaseModel):
    requirement_id: int
    dispute_type: str
    description: str


@router.post("")
def raise_dispute(
    payload: DisputeCreateSchema,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_role(UserRole.CLIENT.value)),
    db: Session = Depends(get_db),
):
    if payload.dispute_type not in _VALID_DISPUTE_TYPES:
        raise HTTPException(status_code=400, detail="Invalid dispute type")

    if not payload.description or len(payload.description.strip()) < 1:
        raise HTTPException(status_code=400, detail="Description is required")

    client_profile = get_client_profile_by_user_id(db, current_user.id)
    if not client_profile:
        raise HTTPException(status_code=404, detail="Client profile not found")

    requirement = get_requirement_by_id(db, payload.requirement_id)
    if not requirement:
        raise HTTPException(status_code=404, detail="Requirement not found")

    if requirement.client_id != client_profile.id:
        raise HTTPException(status_code=403, detail="Not authorised to dispute this requirement")

    if requirement.status != RequirementStatus.COMPLETED.value:
        raise HTTPException(
            status_code=400,
            detail="Disputes can only be raised on completed requirements",
        )

    dispute = Dispute(
        requirement_id=requirement.id,
        raised_by_user_id=current_user.id,
        dispute_type=payload.dispute_type,
        description=payload.description.strip(),
        status="open",
    )
    db.add(dispute)
    db.commit()
    db.refresh(dispute)

    audit_event(
        "dispute_raised",
        {
            "dispute_id": dispute.id,
            "requirement_id": dispute.requirement_id,
            "client_user_id": current_user.id,
            "dispute_type": dispute.dispute_type,
        },
    )

    # Notify all admin users
    admin_users = db.execute(
        select(User).where(User.role == UserRole.ADMIN.value, User.is_active.is_(True))
    ).scalars().all()
    for admin in admin_users:
        enqueue_push_to_user(
            background_tasks,
            db,
            user_id=admin.id,
            title="New Dispute Raised",
            body=f"New dispute raised for requirement {requirement.id} — Type: {dispute.dispute_type}",
            data={"type": "dispute_raised", "dispute_id": str(dispute.id)},
        )

    return success_response(
        "Dispute raised successfully",
        {
            "id": dispute.id,
            "requirement_id": dispute.requirement_id,
            "dispute_type": dispute.dispute_type,
            "status": dispute.status,
            "created_at": dispute.created_at.isoformat(),
        },
    )
