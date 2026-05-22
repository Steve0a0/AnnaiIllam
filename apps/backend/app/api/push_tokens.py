from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user
from app.db.deps import get_db
from app.models.user import User
from app.repositories.push_token_repository import deactivate_user_push_tokens, upsert_push_token
from app.schemas.push_token import PushTokenRegisterSchema
from app.utils.audit import audit_event
from app.utils.response import success_response

router = APIRouter(prefix="/push-tokens", tags=["Push Tokens"])


@router.post("")
def register_push_token(
    payload: PushTokenRegisterSchema,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    token = upsert_push_token(
        db,
        user_id=current_user.id,
        token=payload.token,
        platform=payload.platform,
        app_variant=payload.app_variant,
    )
    db.commit()
    db.refresh(token)

    audit_event(
        "push_token_registered",
        {
            "user_id": current_user.id,
            "platform": payload.platform,
            "app_variant": payload.app_variant,
        },
    )

    return success_response("Push token registered successfully", {"id": token.id})


@router.delete("")
def deactivate_push_tokens(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    count = deactivate_user_push_tokens(db, current_user.id)
    db.commit()

    audit_event("push_tokens_deactivated", {"user_id": current_user.id, "count": count})

    return success_response("Push tokens deactivated successfully", {"count": count})
