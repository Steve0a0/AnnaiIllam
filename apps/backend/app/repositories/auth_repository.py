from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.roles import UserRole
from app.models.otp_code import OtpCode
from app.models.refresh_token import RefreshToken
from app.models.revoked_access_token import RevokedAccessToken
from app.models.user import User
from app.utils.time import utcnow


def get_user_by_phone(db: Session, phone: str) -> User | None:
    return db.execute(select(User).where(User.phone == phone)).scalar_one_or_none()


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.execute(select(User).where(User.email == email)).scalar_one_or_none()


def get_user_by_google_id(db: Session, google_id: str) -> User | None:
    return db.execute(select(User).where(User.google_id == google_id)).scalar_one_or_none()


def get_user_by_apple_id(db: Session, apple_id: str) -> User | None:
    return db.execute(select(User).where(User.apple_id == apple_id)).scalar_one_or_none()


def create_user(db: Session, phone: str, role: str) -> User:
    user = User(phone=phone, role=role, is_active=True, is_phone_verified=True)
    db.add(user)
    db.flush()
    return user


def create_admin_user(db: Session, email: str, name: str, password_hash: str) -> User:
    user = User(
        email=email,
        name=name,
        role=UserRole.ADMIN.value,
        password_hash=password_hash,
        is_active=True,
        is_email_verified=True,
    )
    db.add(user)
    db.flush()
    return user


def create_social_user(
    db: Session,
    email: str,
    name: str | None,
    role: str,
    google_id: str | None = None,
    apple_id: str | None = None,
) -> User:
    user = User(
        email=email,
        name=name,
        role=role,
        is_active=True,
        is_email_verified=True,
        google_id=google_id,
        apple_id=apple_id,
    )
    db.add(user)
    db.flush()
    return user


def create_otp_record(db: Session, phone: str, code_hash: str, purpose: str, expires_at: datetime) -> OtpCode:
    otp = OtpCode(
        phone=phone,
        code_hash=code_hash,
        purpose=purpose,
        expires_at=expires_at,
    )
    db.add(otp)
    db.flush()
    return otp


def invalidate_active_otps(db: Session, phone: str, purpose: str = "login") -> None:
    stmt = select(OtpCode).where(
        OtpCode.phone == phone,
        OtpCode.purpose == purpose,
        OtpCode.is_used == False,  # noqa: E712
    )
    for otp in db.execute(stmt).scalars():
        otp.is_used = True
    db.flush()


def get_latest_active_otp(db: Session, phone: str) -> OtpCode | None:
    stmt = (
        select(OtpCode)
        .where(OtpCode.phone == phone, OtpCode.is_used == False)  # noqa: E712
        .order_by(OtpCode.created_at.desc())
    )
    return db.execute(stmt).scalars().first()


def save_refresh_token(
    db: Session,
    user_id: int,
    token_hash: str,
    expires_at: datetime,
    family_id: str,
) -> RefreshToken:
    token = RefreshToken(
        user_id=user_id,
        token_hash=token_hash,
        family_id=family_id,
        expires_at=expires_at,
    )
    db.add(token)
    db.flush()
    return token


def get_refresh_token_record(
    db: Session,
    token_hash: str,
    *,
    include_revoked: bool = False,
    for_update: bool = False,
) -> RefreshToken | None:
    stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    if not include_revoked:
        stmt = stmt.where(RefreshToken.is_revoked == False)  # noqa: E712
    if for_update:
        stmt = stmt.with_for_update()
    return db.execute(stmt).scalar_one_or_none()


def revoke_refresh_token(
    db: Session,
    token_hash: str,
    *,
    reason: str = "logout",
    replaced_by_token_id: int | None = None,
) -> RefreshToken | None:
    token = get_refresh_token_record(db, token_hash, include_revoked=True, for_update=True)
    if token:
        if not token.is_revoked:
            token.is_revoked = True
            token.revoked_at = utcnow()
            token.revoke_reason = reason
        if replaced_by_token_id is not None:
            token.replaced_by_token_id = replaced_by_token_id
        db.flush()
    return token


def revoke_refresh_token_family(db: Session, family_id: str, *, reason: str) -> int:
    stmt = select(RefreshToken).where(
        RefreshToken.family_id == family_id,
        RefreshToken.is_revoked == False,  # noqa: E712
    ).with_for_update()
    tokens = list(db.execute(stmt).scalars())
    revoked_at = utcnow()
    for token in tokens:
        token.is_revoked = True
        token.revoked_at = revoked_at
        token.revoke_reason = reason
    db.flush()
    return len(tokens)


def revoke_access_token(db: Session, jti: str, expires_at: datetime) -> None:
    """Add an access token JTI to the blocklist. Idempotent if already present."""
    existing = db.get(RevokedAccessToken, jti)
    if existing is None:
        db.add(RevokedAccessToken(jti=jti, expires_at=expires_at))
        db.flush()


def is_access_token_revoked(db: Session, jti: str) -> bool:
    return db.get(RevokedAccessToken, jti) is not None
