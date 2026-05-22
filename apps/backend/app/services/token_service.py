from datetime import timedelta
from app.utils.time import utcnow

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_value,
)
from app.repositories.auth_repository import get_refresh_token_record, save_refresh_token
from app.repositories.auth_repository import revoke_refresh_token


def build_token_pair(db: Session, user_id: int, subject: str, role: str) -> tuple[str, str]:
    access_token = create_access_token(subject=subject, role=role, user_id=user_id)
    refresh_token = create_refresh_token(subject=subject, role=role, user_id=user_id)

    save_refresh_token(
        db=db,
        user_id=user_id,
        token_hash=hash_value(refresh_token),
        expires_at=utcnow() + timedelta(days=settings.refresh_token_expire_days),
    )
    return access_token, refresh_token


def validate_refresh_token(db: Session, refresh_token: str) -> dict:
    payload = decode_token(refresh_token)
    if payload.get("type") != "refresh":
        raise ValueError("Invalid token type")

    token_record = get_refresh_token_record(db, hash_value(refresh_token))
    if not token_record:
        raise ValueError("Refresh token not found or revoked")

    if token_record.expires_at < utcnow():
        raise ValueError("Refresh token expired")

    return payload


def rotate_refresh_token(db: Session, refresh_token: str) -> tuple[dict, str, str]:
    payload = validate_refresh_token(db, refresh_token)
    revoke_refresh_token(db, hash_value(refresh_token))

    access_token, new_refresh_token = build_token_pair(
        db=db,
        user_id=payload["user_id"],
        subject=payload["sub"],
        role=payload["role"],
    )
    return payload, access_token, new_refresh_token
