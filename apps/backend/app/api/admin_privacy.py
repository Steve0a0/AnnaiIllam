from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies.roles import require_permission_group
from app.db.deps import get_db
from app.models.privacy_request import (
    PRIVACY_REQUEST_STATUSES,
    PRIVACY_REQUEST_TYPES,
    PrivacyRequest,
)
from app.models.user import User
from app.services.privacy_service import anonymize_user
from app.utils.audit import audit_event
from app.utils.pagination import PaginationParams, paginate, pagination_meta
from app.utils.response import success_response
from app.utils.time import utcnow

router = APIRouter(prefix="/admin/privacy-requests", tags=["Admin Privacy"])


class ResolvePrivacyRequestSchema(BaseModel):
    status: str
    resolution_notes: str | None = Field(default=None, max_length=2000)


def _serialize(item: PrivacyRequest, user: User) -> dict:
    return {
        "id": item.id,
        "user_id": item.user_id,
        "user_role": user.role,
        "user_name": user.name,
        "user_contact": user.email or user.phone,
        "request_type": item.request_type,
        "status": item.status,
        "reason": item.reason,
        "resolution_notes": item.resolution_notes,
        "requested_at": item.requested_at.isoformat(),
        "resolved_at": item.resolved_at.isoformat() if item.resolved_at else None,
        "resolved_by_user_id": item.resolved_by_user_id,
    }


@router.get("")
def list_privacy_requests(
    status: str | None = Query(default=None),
    request_type: str | None = Query(default=None),
    pg: PaginationParams = Depends(),
    _current_user: User = Depends(require_permission_group("super_admin")),
    db: Session = Depends(get_db),
):
    if status and status not in PRIVACY_REQUEST_STATUSES:
        raise HTTPException(status_code=422, detail="Invalid privacy request status")
    if request_type and request_type not in PRIVACY_REQUEST_TYPES:
        raise HTTPException(status_code=422, detail="Invalid privacy request type")

    stmt = select(PrivacyRequest).order_by(PrivacyRequest.requested_at.desc())
    if status:
        stmt = stmt.where(PrivacyRequest.status == status)
    if request_type:
        stmt = stmt.where(PrivacyRequest.request_type == request_type)
    items, total = paginate(stmt, db, pg)
    users = (
        {
            user.id: user
            for user in db.scalars(
                select(User).where(User.id.in_({item.user_id for item in items}))
            ).all()
        }
        if items
        else {}
    )
    return success_response(
        "Privacy requests fetched successfully",
        {
            "items": [_serialize(item, users[item.user_id]) for item in items],
            **pagination_meta(pg, total),
        },
    )


@router.patch("/{request_id}")
def resolve_privacy_request(
    request_id: int,
    payload: ResolvePrivacyRequestSchema,
    current_user: User = Depends(require_permission_group("super_admin")),
    db: Session = Depends(get_db),
):
    if payload.status not in {"in_review", "completed", "rejected"}:
        raise HTTPException(status_code=422, detail="Invalid privacy request transition")
    if payload.status in {"completed", "rejected"} and not payload.resolution_notes:
        raise HTTPException(status_code=422, detail="Resolution notes are required")

    item = db.scalar(
        select(PrivacyRequest)
        .where(PrivacyRequest.id == request_id)
        .with_for_update()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Privacy request not found")

    subject = db.get(User, item.user_id)
    if not subject:
        raise HTTPException(status_code=404, detail="Request user not found")

    if item.status in {"completed", "rejected"}:
        if item.status == payload.status:
            return success_response(
                "Privacy request was already resolved", _serialize(item, subject)
            )
        raise HTTPException(status_code=409, detail="Privacy request is already resolved")

    anonymization_counts: dict[str, int] | None = None
    if payload.status == "completed" and item.request_type == "deletion":
        anonymization_counts = anonymize_user(db, subject)

    item.status = payload.status
    item.resolution_notes = payload.resolution_notes
    if payload.status in {"completed", "rejected"}:
        item.resolved_at = utcnow()
        item.resolved_by_user_id = current_user.id
    db.commit()
    db.refresh(item)

    audit_event(
        "privacy_request_resolved",
        {
            "privacy_request_id": item.id,
            "subject_user_id": item.user_id,
            "request_type": item.request_type,
            "outcome": item.status,
            "anonymization_counts": anonymization_counts,
        },
        actor_user_id=current_user.id,
    )
    return success_response(
        "Privacy request updated successfully", _serialize(item, subject)
    )
