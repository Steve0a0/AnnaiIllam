from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies.roles import require_role
from app.core.roles import UserRole
from app.db.deps import get_db
from app.models.user import User
from app.repositories.profile_repository import create_admin_profile, get_admin_profile_by_user_id
from app.schemas.profile import AdminProfileCreateSchema, AdminProfileUpdateSchema
from app.services.profile_service import build_admin_profile
from app.utils.audit import audit_event
from app.utils.response import success_response

router = APIRouter(prefix="/admin/profile", tags=["Admin Profile"])


@router.post("")
def create_my_admin_profile(
    payload: AdminProfileCreateSchema,
    current_user: User = Depends(require_role(UserRole.ADMIN.value)),
    db: Session = Depends(get_db),
):
    existing = get_admin_profile_by_user_id(db, current_user.id)
    if existing:
        raise HTTPException(status_code=400, detail="Admin profile already exists")

    profile = build_admin_profile(payload, current_user.id)
    create_admin_profile(db, profile)
    db.commit()
    db.refresh(profile)

    audit_event("admin_profile_created", {"user_id": current_user.id, "profile_id": profile.id})

    return success_response("Admin profile created successfully", {"id": profile.id})


@router.get("")
def get_my_admin_profile(
    current_user: User = Depends(require_role(UserRole.ADMIN.value)),
    db: Session = Depends(get_db),
):
    profile = get_admin_profile_by_user_id(db, current_user.id)
    if not profile:
        raise HTTPException(status_code=404, detail="Admin profile not found")

    return success_response(
        "Admin profile fetched successfully",
        {
            "id": profile.id,
            "full_name": profile.full_name,
            "department": profile.department,
            "permission_group": profile.permission_group,
        },
    )


@router.patch("")
def update_my_admin_profile(
    payload: AdminProfileUpdateSchema,
    current_user: User = Depends(require_role(UserRole.ADMIN.value)),
    db: Session = Depends(get_db),
):
    profile = get_admin_profile_by_user_id(db, current_user.id)
    if not profile:
        raise HTTPException(status_code=404, detail="Admin profile not found")

    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(profile, key, value)

    db.commit()

    audit_event("admin_profile_updated", {"user_id": current_user.id, "profile_id": profile.id})

    return success_response("Admin profile updated successfully", {"id": profile.id})
