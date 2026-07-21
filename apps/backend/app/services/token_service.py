from datetime import timedelta
from uuid import uuid4

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.roles import UserRole
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_value,
)
from app.models.refresh_token import RefreshToken
from app.repositories.auth_repository import (
    get_refresh_token_record,
    revoke_refresh_token,
    revoke_refresh_token_family,
    save_refresh_token,
)
from app.utils.time import utcnow


class RefreshTokenReuseError(ValueError):
    """Raised after a rotated token is replayed and its family is revoked."""

    def __init__(self, family_id: str):
        super().__init__("Refresh token reuse detected")
        self.family_id = family_id


def _access_token(subject: str, role: str, user_id: int) -> str:
    expires_minutes = (
        settings.admin_access_token_expire_minutes
        if role == UserRole.ADMIN.value
        else settings.access_token_expire_minutes
    )
    return create_access_token(
        subject=subject,
        role=role,
        user_id=user_id,
        expires_minutes=expires_minutes,
    )


def build_token_pair(
    db: Session,
    user_id: int,
    subject: str,
    role: str,
    *,
    family_id: str | None = None,
) -> tuple[str, str]:
    access_token = _access_token(subject, role, user_id)
    refresh_token = create_refresh_token(subject=subject, role=role, user_id=user_id)

    save_refresh_token(
        db=db,
        user_id=user_id,
        token_hash=hash_value(refresh_token),
        expires_at=utcnow() + timedelta(days=settings.refresh_token_expire_days),
        family_id=family_id or uuid4().hex,
    )
    return access_token, refresh_token


def validate_refresh_token(
    db: Session,
    refresh_token: str,
    *,
    for_update: bool = False,
) -> tuple[dict, RefreshToken]:
    payload = decode_token(refresh_token)
    if payload.get("type") != "refresh":
        raise ValueError("Invalid token type")

    token_record = get_refresh_token_record(
        db,
        hash_value(refresh_token),
        include_revoked=True,
        for_update=for_update,
    )
    if not token_record:
        raise ValueError("Refresh token not found")

    if token_record.is_revoked:
        # A token rotated out of use must never appear again. Revoke every live
        # descendant so a stolen replacement cannot continue the session.
        if token_record.replaced_by_token_id or token_record.revoke_reason == "rotated":
            revoke_refresh_token_family(
                db,
                token_record.family_id,
                reason="reuse_detected",
            )
            raise RefreshTokenReuseError(token_record.family_id)
        raise ValueError("Refresh token revoked")

    if token_record.expires_at < utcnow():
        revoke_refresh_token(db, token_record.token_hash, reason="expired")
        raise ValueError("Refresh token expired")

    return payload, token_record


def rotate_refresh_token(db: Session, refresh_token: str) -> tuple[dict, str, str]:
    payload, token_record = validate_refresh_token(db, refresh_token, for_update=True)

    access_token = _access_token(payload["sub"], payload["role"], payload["user_id"])
    new_refresh_token = create_refresh_token(
        subject=payload["sub"],
        role=payload["role"],
        user_id=payload["user_id"],
    )
    new_record = save_refresh_token(
        db=db,
        user_id=payload["user_id"],
        token_hash=hash_value(new_refresh_token),
        expires_at=utcnow() + timedelta(days=settings.refresh_token_expire_days),
        family_id=token_record.family_id,
    )
    revoke_refresh_token(
        db,
        token_record.token_hash,
        reason="rotated",
        replaced_by_token_id=new_record.id,
    )
    return payload, access_token, new_refresh_token
