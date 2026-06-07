from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user
from app.api.dependencies.roles import require_role
from app.core.roles import UserRole
from app.core.security import hash_password, verify_password
from app.db.deps import get_db
from app.models.user import User
from app.repositories.profile_repository import get_admin_profile_by_user_id, get_client_profile_by_user_id
from app.utils.audit import audit_event
from app.utils.response import success_response

router = APIRouter(prefix="/me", tags=["Me"])


class ChangePasswordSchema(BaseModel):
    current_password: str = Field(min_length=1)
    new_password: str = Field(min_length=8, max_length=128)


@router.get("")
def me(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    payload: dict = {
        "id": current_user.id,
        "phone": current_user.phone,
        "email": current_user.email,
        "name": current_user.name,
        "role": current_user.role,
        "is_active": current_user.is_active,
    }

    if current_user.role == UserRole.ADMIN.value:
        admin_profile = get_admin_profile_by_user_id(db, current_user.id)
        payload["permission_group"] = admin_profile.permission_group if admin_profile else None

    if current_user.role == UserRole.CLIENT.value:
        profile = get_client_profile_by_user_id(db, current_user.id)
        payload["is_profile_complete"] = profile is not None
        if not payload["name"] and profile:
            payload["name"] = profile.contact_name

    return success_response("Current user fetched successfully", payload)


@router.get("/admin-only")
def admin_only(current_user: User = Depends(require_role(UserRole.ADMIN.value))):
    return success_response("Admin access granted", {"user_id": current_user.id})


@router.get("/client-only")
def client_only(current_user: User = Depends(require_role(UserRole.CLIENT.value))):
    return success_response("Client access granted", {"user_id": current_user.id})


@router.get("/worker-only")
def worker_only(current_user: User = Depends(require_role(UserRole.WORKER.value))):
    return success_response("Worker access granted", {"user_id": current_user.id})


@router.patch("/password")
def change_password(
    payload: ChangePasswordSchema,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Change the current user's password. Requires the existing password for verification."""
    if not current_user.password_hash:
        raise HTTPException(status_code=400, detail="Password login is not enabled for this account")

    if not verify_password(payload.current_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect")

    current_user.password_hash = hash_password(payload.new_password)
    db.commit()

    audit_event("password_changed", {"user_id": current_user.id})

    return success_response("Password changed successfully", {})
