from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.roles import UserRole
from app.models.otp_code import OtpCode
from app.models.refresh_token import RefreshToken
from app.models.revoked_access_token import RevokedAccessToken
from app.models.user import User


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


def save_refresh_token(db: Session, user_id: int, token_hash: str, expires_at: datetime) -> RefreshToken:
    token = RefreshToken(
        user_id=user_id,
        token_hash=token_hash,
        expires_at=expires_at,
    )
    db.add(token)
    db.flush()
    return token


def get_refresh_token_record(db: Session, token_hash: str) -> RefreshToken | None:
    stmt = select(RefreshToken).where(
        RefreshToken.token_hash == token_hash,
        RefreshToken.is_revoked == False,  # noqa: E712
    )
    return db.execute(stmt).scalar_one_or_none()


def revoke_refresh_token(db: Session, token_hash: str) -> RefreshToken | None:
    token = get_refresh_token_record(db, token_hash)
    if token:
        token.is_revoked = True
        db.flush()
    return token


def revoke_access_token(db: Session, jti: str, expires_at: datetime) -> None:
    """Add an access token JTI to the blocklist. Idempotent if already present."""
    existing = db.get(RevokedAccessToken, jti)
    if existing is None:
        db.add(RevokedAccessToken(jti=jti, expires_at=expires_at))
        db.flush()


def is_access_token_revoked(db: Session, jti: str) -> bool:
    return db.get(RevokedAccessToken, jti) is not None
