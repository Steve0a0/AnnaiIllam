from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies.roles import require_role
from app.core.roles import UserRole
from app.db.deps import get_db
from app.models.client_worker_blacklist import ClientWorkerBlacklist
from app.models.user import User
from app.repositories.profile_repository import get_client_profile_by_id, get_worker_profile_by_id
from app.utils.audit import audit_event
from app.utils.response import success_response

router = APIRouter(prefix="/admin/blacklist", tags=["Admin Blacklist"])


class BlacklistCreateSchema(BaseModel):
    client_profile_id: int
    worker_profile_id: int
    reason: str = Field(min_length=1)


@router.post("")
def blacklist_worker(
    payload: BlacklistCreateSchema,
    current_user: User = Depends(require_role(UserRole.ADMIN.value)),
    db: Session = Depends(get_db),
):
    # Verify both profiles exist
    client_profile = get_client_profile_by_id(db, payload.client_profile_id)
    if not client_profile:
        raise HTTPException(status_code=404, detail="Client profile not found")

    worker_profile = get_worker_profile_by_id(db, payload.worker_profile_id)
    if not worker_profile:
        raise HTTPException(status_code=404, detail="Worker profile not found")

    # Check not already blacklisted
    existing = db.execute(
        select(ClientWorkerBlacklist).where(
            ClientWorkerBlacklist.client_profile_id == payload.client_profile_id,
            ClientWorkerBlacklist.worker_profile_id == payload.worker_profile_id,
        )
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="Worker is already blacklisted for this client")

    entry = ClientWorkerBlacklist(
        client_profile_id=payload.client_profile_id,
        worker_profile_id=payload.worker_profile_id,
        reason=payload.reason,
        blacklisted_by_user_id=current_user.id,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)

    audit_event(
        "worker_blacklisted",
        {
            "blacklist_id": entry.id,
            "client_profile_id": payload.client_profile_id,
            "worker_profile_id": payload.worker_profile_id,
            "admin_user_id": current_user.id,
        },
    )

    return success_response(
        "Worker blacklisted successfully",
        {
            "id": entry.id,
            "client_profile_id": entry.client_profile_id,
            "worker_profile_id": entry.worker_profile_id,
            "reason": entry.reason,
        },
    )


@router.delete("/{blacklist_id}")
def remove_from_blacklist(
    blacklist_id: int,
    current_user: User = Depends(require_role(UserRole.ADMIN.value)),
    db: Session = Depends(get_db),
):
    entry = db.get(ClientWorkerBlacklist, blacklist_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Blacklist entry not found")

    client_profile_id = entry.client_profile_id
    worker_profile_id = entry.worker_profile_id

    db.delete(entry)
    db.commit()

    audit_event(
        "worker_unblacklisted",
        {
            "blacklist_id": blacklist_id,
            "client_profile_id": client_profile_id,
            "worker_profile_id": worker_profile_id,
            "admin_user_id": current_user.id,
        },
    )

    return success_response("Worker removed from blacklist", {"id": blacklist_id})


@router.get("/client/{client_profile_id}")
def get_blacklist_by_client(
    client_profile_id: int,
    current_user: User = Depends(require_role(UserRole.ADMIN.value)),
    db: Session = Depends(get_db),
):
    client_profile = get_client_profile_by_id(db, client_profile_id)
    if not client_profile:
        raise HTTPException(status_code=404, detail="Client profile not found")

    entries = db.execute(
        select(ClientWorkerBlacklist)
        .where(ClientWorkerBlacklist.client_profile_id == client_profile_id)
        .order_by(ClientWorkerBlacklist.created_at.desc())
    ).scalars().all()

    data = [
        {
            "id": entry.id,
            "worker_profile_id": entry.worker_profile_id,
            "reason": entry.reason,
            "blacklisted_by_user_id": entry.blacklisted_by_user_id,
            "created_at": entry.created_at.isoformat(),
        }
        for entry in entries
    ]

    return success_response("Blacklist fetched successfully", {"items": data, "total": len(data)})
