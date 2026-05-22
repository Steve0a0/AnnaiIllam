from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies.roles import require_role
from app.core.roles import UserRole
from app.db.deps import get_db
from app.models.user import User
from app.repositories.profile_repository import create_client_profile, get_client_profile_by_user_id
from app.schemas.profile import ClientProfileCreateSchema, ClientProfileUpdateSchema
from app.services.profile_service import build_client_profile
from app.utils.audit import audit_event
from app.utils.response import success_response

router = APIRouter(prefix="/client/profile", tags=["Client Profile"])


@router.post("")
def create_my_client_profile(
    payload: ClientProfileCreateSchema,
    current_user: User = Depends(require_role(UserRole.CLIENT.value)),
    db: Session = Depends(get_db),
):
    existing = get_client_profile_by_user_id(db, current_user.id)
    if existing:
        raise HTTPException(status_code=400, detail="Client profile already exists")

    profile = build_client_profile(payload, current_user.id)
    create_client_profile(db, profile)
    db.commit()
    db.refresh(profile)

    audit_event("client_profile_created", {"user_id": current_user.id, "profile_id": profile.id})

    return success_response("Client profile created successfully", {"id": profile.id})


@router.get("")
def get_my_client_profile(
    current_user: User = Depends(require_role(UserRole.CLIENT.value)),
    db: Session = Depends(get_db),
):
    profile = get_client_profile_by_user_id(db, current_user.id)
    if not profile:
        raise HTTPException(status_code=404, detail="Client profile not found")

    return success_response(
        "Client profile fetched successfully",
        {
            "id": profile.id,
            "client_type": profile.client_type or "company",
            "company_name": profile.company_name,
            "contact_name": profile.contact_name,
            "phone": current_user.phone,
            "city": profile.city,
            "state": profile.state,
            "address": profile.address,
            "gst_number": profile.gst_number,
            "industry": profile.industry,
            "email": profile.email or current_user.email,
            "default_job_category": profile.default_job_category,
            "food_preference": profile.food_preference,
            "accommodation_preference": profile.accommodation_preference,
            "standing_notes": profile.standing_notes,
        },
    )


@router.patch("")
def update_my_client_profile(
    payload: ClientProfileUpdateSchema,
    current_user: User = Depends(require_role(UserRole.CLIENT.value)),
    db: Session = Depends(get_db),
):
    profile = get_client_profile_by_user_id(db, current_user.id)
    if not profile:
        raise HTTPException(status_code=404, detail="Client profile not found")

    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(profile, key, value)

    db.commit()

    audit_event("client_profile_updated", {"user_id": current_user.id, "profile_id": profile.id})

    return success_response("Client profile updated successfully", {"id": profile.id})
