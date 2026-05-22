from app.utils.time import utcnow
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.core.rate_limit import check_rate_limit
from app.core.roles import UserRole
from app.db.deps import get_db
from app.repositories.auth_repository import (
    create_social_user,
    get_user_by_apple_id,
    get_user_by_email,
    get_user_by_google_id,
)
from app.repositories.profile_repository import get_client_profile_by_user_id
from app.services.social_auth_service import verify_apple_token, verify_google_token
from app.services.token_service import build_token_pair
from app.utils.audit import audit_event
from app.utils.response import success_response

router = APIRouter(prefix="/auth/client", tags=["Client Social Auth"])


class ClientSocialAuthSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider: Literal["google", "apple"]
    id_token: str = Field(min_length=10, max_length=4096)
    # Apple returns the user's full name only on the first sign-in; client passes it here
    name: str | None = Field(default=None, max_length=255)


@router.post("/social")
async def client_social_auth(payload: ClientSocialAuthSchema, db: Session = Depends(get_db)):
    check_rate_limit(f"social_auth:{payload.provider}:{payload.id_token[:32]}", limit=10, window_seconds=60)

    try:
        if payload.provider == "google":
            identity = await verify_google_token(payload.id_token)
        else:
            identity = await verify_apple_token(payload.id_token)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    # Resolve or create user — prefer provider ID lookup, fall back to email
    if identity.provider == "google":
        user = get_user_by_google_id(db, identity.provider_id)
    else:
        user = get_user_by_apple_id(db, identity.provider_id)

    if not user:
        user = get_user_by_email(db, identity.email)

    is_new_user = user is None

    if is_new_user:
        display_name = payload.name or identity.name
        user = create_social_user(
            db=db,
            email=identity.email,
            name=display_name,
            role=UserRole.CLIENT.value,
            google_id=identity.provider_id if identity.provider == "google" else None,
            apple_id=identity.provider_id if identity.provider == "apple" else None,
        )
    else:
        if user.role != UserRole.CLIENT.value:
            raise HTTPException(status_code=403, detail="This account is not registered as a client")
        if not user.is_active:
            raise HTTPException(status_code=403, detail="Account is disabled")

        # Link provider ID if not already linked
        if identity.provider == "google" and not user.google_id:
            user.google_id = identity.provider_id
        if identity.provider == "apple" and not user.apple_id:
            user.apple_id = identity.provider_id

        # Update name if we now have one and didn't before
        if not user.name and (payload.name or identity.name):
            user.name = payload.name or identity.name

    user.is_email_verified = True
    user.last_login_at = utcnow()

    access_token, refresh_token = build_token_pair(
        db=db,
        user_id=user.id,
        subject=user.phone or user.email,
        role=user.role,
    )

    db.commit()
    audit_event(
        "social_auth_success",
        {"provider": identity.provider, "user_id": user.id, "is_new_user": is_new_user},
    )

    profile = get_client_profile_by_user_id(db, user.id)
    is_profile_complete = profile is not None

    return success_response(
        "Login successful",
        {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "is_profile_complete": is_profile_complete,
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "role": user.role,
            },
        },
    )
