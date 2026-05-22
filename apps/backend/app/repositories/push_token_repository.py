from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.push_token import PushToken


def upsert_push_token(
    db: Session,
    user_id: int,
    token: str,
    platform: str,
    app_variant: str,
) -> PushToken:
    stmt = select(PushToken).where(PushToken.token == token)
    existing = db.execute(stmt).scalar_one_or_none()
    if existing:
        existing.user_id = user_id
        existing.platform = platform
        existing.app_variant = app_variant
        existing.is_active = True
        db.flush()
        return existing

    push_token = PushToken(
        user_id=user_id,
        token=token,
        platform=platform,
        app_variant=app_variant,
        is_active=True,
    )
    db.add(push_token)
    db.flush()
    return push_token


def deactivate_user_push_tokens(db: Session, user_id: int) -> int:
    stmt = select(PushToken).where(PushToken.user_id == user_id, PushToken.is_active == True)  # noqa: E712
    tokens = list(db.execute(stmt).scalars().all())
    for token in tokens:
        token.is_active = False
    db.flush()
    return len(tokens)


def get_active_push_tokens_for_user(db: Session, user_id: int) -> list[str]:
    """Return all active Expo push token strings for a user."""
    stmt = select(PushToken.token).where(
        PushToken.user_id == user_id,
        PushToken.is_active == True,  # noqa: E712
    )
    return list(db.execute(stmt).scalars().all())
