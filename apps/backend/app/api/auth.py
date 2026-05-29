import logging
from datetime import datetime, timezone
from app.utils.time import utcnow

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.rate_limit import check_rate_limit
from app.core.roles import UserRole
from app.core.security import hash_value, verify_password, decode_token
from app.db.deps import get_db
from app.models.user import User
from app.repositories.auth_repository import (
    create_user,
    get_latest_active_otp,
    get_user_by_email,
    get_user_by_phone,
    revoke_access_token,
    revoke_refresh_token,
)
from app.schemas.auth import (
    AdminLoginSchema,
    OtpRequestSchema,
    OtpVerifySchema,
    PhoneOtpRequestSchema,
    PhoneOtpVerifySchema,
    RefreshTokenSchema,
)

from app.services.otp_service import issue_login_otp
from app.services.token_service import build_token_pair, rotate_refresh_token
from app.utils.audit import audit_event
from app.utils.response import success_response

router = APIRouter(prefix="/auth", tags=["Auth"])
logger = logging.getLogger(__name__)

_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/verify-otp", auto_error=False)


PUBLIC_OTP_ROLES = {UserRole.CLIENT.value, UserRole.WORKER.value}


def _request_otp_for_role(phone: str, role: str, db: Session):
    if role not in PUBLIC_OTP_ROLES:
        raise HTTPException(status_code=403, detail="This role cannot use public OTP login")

    check_rate_limit(f"otp_request:{phone}", limit=5, window_seconds=300)

    otp_code = issue_login_otp(db=db, phone=phone)
    db.commit()
    audit_event("otp_requested", {"phone": phone, "role": role})

    # Log OTP only in local development — never in staging or production.
    if settings.is_local:
        logger.debug("[DEV] OTP for %s: %s", phone, otp_code)

    response = {"phone": phone, "role": role}
    if settings.is_local:
        response["otp"] = otp_code

    return success_response("OTP sent successfully", response)


def _verify_otp_for_role(phone: str, code: str, role: str, db: Session):
    if role not in PUBLIC_OTP_ROLES:
        raise HTTPException(status_code=403, detail="This role cannot use public OTP login")

    check_rate_limit(f"otp_verify:{phone}", limit=10, window_seconds=300)

    otp_record = get_latest_active_otp(db, phone)
    if not otp_record:
        raise HTTPException(status_code=400, detail="OTP not found")

    if otp_record.is_used:
        raise HTTPException(status_code=400, detail="OTP already used")

    if otp_record.expires_at < utcnow():
        raise HTTPException(status_code=400, detail="OTP expired")

    if otp_record.attempts >= settings.otp_max_attempts:
        raise HTTPException(status_code=400, detail="OTP attempts exceeded")

    otp_record.attempts += 1

    if not verify_password(code, otp_record.code_hash):
        db.commit()
        raise HTTPException(status_code=400, detail="Invalid OTP")

    otp_record.is_used = True

    user = get_user_by_phone(db, phone)
    if not user:
        user = create_user(db=db, phone=phone, role=role)
    else:
        if user.role != role:
            audit_event("role_mismatch", {"phone": phone, "requested_role": role, "actual_role": user.role})
            raise HTTPException(status_code=400, detail="Role mismatch for this phone number")

    user.is_phone_verified = True
    user.last_login_at = utcnow()

    access_token, refresh_token = build_token_pair(
        db=db,
        user_id=user.id,
        subject=user.phone,
        role=user.role,
    )

    db.commit()
    audit_event("otp_verified", {"phone": phone, "role": role, "user_id": user.id})

    return success_response(
        "Login successful",
        {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "phone": user.phone,
                "role": user.role,
            },
        },
    )


@router.post("/client/request-otp")
def request_client_otp(payload: PhoneOtpRequestSchema, db: Session = Depends(get_db)):
    return _request_otp_for_role(payload.phone, UserRole.CLIENT.value, db)


@router.post("/client/verify-otp")
def verify_client_otp(payload: PhoneOtpVerifySchema, db: Session = Depends(get_db)):
    return _verify_otp_for_role(payload.phone, payload.code, UserRole.CLIENT.value, db)


@router.post("/worker/request-otp")
def request_worker_otp(payload: PhoneOtpRequestSchema, db: Session = Depends(get_db)):
    return _request_otp_for_role(payload.phone, UserRole.WORKER.value, db)


@router.post("/worker/verify-otp")
def verify_worker_otp(payload: PhoneOtpVerifySchema, db: Session = Depends(get_db)):
    return _verify_otp_for_role(payload.phone, payload.code, UserRole.WORKER.value, db)


@router.post("/request-otp")
def request_otp(payload: OtpRequestSchema, db: Session = Depends(get_db)):
    return _request_otp_for_role(payload.phone, payload.role, db)


@router.post("/verify-otp")
def verify_otp(payload: OtpVerifySchema, db: Session = Depends(get_db)):
    return _verify_otp_for_role(payload.phone, payload.code, payload.role, db)


@router.post("/admin/login")
def admin_login(payload: AdminLoginSchema, db: Session = Depends(get_db)):
    # 5 attempts per 5 minutes — stricter than OTP to protect the password-based admin login.
    check_rate_limit(f"admin_login:{payload.email}", limit=5, window_seconds=300)

    user = get_user_by_email(db, payload.email)
    # Generic error avoids leaking which emails have admin accounts
    if not user or user.role != UserRole.ADMIN.value:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is disabled")
    if not user.password_hash:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not verify_password(payload.password, user.password_hash):
        audit_event("admin_login_failed", {"email": payload.email})
        raise HTTPException(status_code=401, detail="Invalid credentials")

    user.last_login_at = utcnow()

    access_token, refresh_token = build_token_pair(
        db=db,
        user_id=user.id,
        subject=user.email,
        role=user.role,
    )

    db.commit()
    audit_event("admin_login_success", {"email": payload.email, "user_id": user.id})

    return success_response(
        "Login successful",
        {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "role": user.role,
            },
        },
    )


@router.post("/refresh")
def refresh_access_token(payload: RefreshTokenSchema, db: Session = Depends(get_db)):
    check_rate_limit(f"refresh:{hash_value(payload.refresh_token)}", limit=20, window_seconds=300)

    try:
        token_payload, access_token, refresh_token = rotate_refresh_token(db, payload.refresh_token)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    user = db.execute(select(User).where(User.id == token_payload["user_id"])).scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User inactive or not found")

    db.commit()
    audit_event("refresh_used", {"phone": user.phone, "role": user.role, "user_id": user.id})

    return success_response(
        "Token refreshed successfully",
        {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        },
    )


@router.post("/logout")
def logout(
    payload: RefreshTokenSchema,
    db: Session = Depends(get_db),
    access_token: str | None = Depends(_oauth2_scheme),
):
    # Revoke refresh token
    token_hash = hash_value(payload.refresh_token)
    revoked_token = revoke_refresh_token(db, token_hash)

    # Blocklist the access token so it cannot be reused during its remaining TTL
    if access_token:
        try:
            token_payload = decode_token(access_token)
            jti = token_payload.get("jti")
            exp = token_payload.get("exp")
            if jti and exp:
                expires_at = datetime.fromtimestamp(exp, tz=timezone.utc).replace(tzinfo=None)
                revoke_access_token(db, jti, expires_at)
        except Exception:
            # Expired or invalid access tokens are already harmless; continue anyway
            pass

    db.commit()

    audit_event(
        "logout",
        {
            "token_revoked": revoked_token is not None,
            "access_token_blocklisted": access_token is not None,
        },
    )

    return success_response("Logged out successfully", None)
