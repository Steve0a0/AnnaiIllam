from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies.roles import require_role
from app.core.config import settings
from app.core.rate_limit import check_rate_limit
from app.core.roles import UserRole
from app.core.security import verify_password
from app.db.deps import get_db
from app.models.user import User
from app.repositories.auth_repository import get_latest_active_otp, get_user_by_phone
from app.schemas.auth import PhoneOtpRequestSchema, PhoneOtpVerifySchema
from app.services.otp_service import issue_login_otp
from app.utils.audit import audit_event
from app.utils.response import success_response
from app.utils.time import utcnow

router = APIRouter(prefix="/client/phone", tags=["Client Phone"])


@router.post("/request-otp")
def request_phone_link_otp(
    payload: PhoneOtpRequestSchema,
    current_user: User = Depends(require_role(UserRole.CLIENT.value)),
    db: Session = Depends(get_db),
):
    if current_user.phone:
        raise HTTPException(
            status_code=400,
            detail="A phone number is already linked. Contact support to change it.",
        )

    existing = get_user_by_phone(db, payload.phone)
    if existing and existing.id != current_user.id:
        raise HTTPException(
            status_code=409,
            detail="This phone number is already registered to another account.",
        )

    check_rate_limit(f"otp_request:{payload.phone}", limit=5, window_seconds=300)

    otp_code = issue_login_otp(db=db, phone=payload.phone)
    db.commit()

    audit_event("phone_link_otp_requested", {"user_id": current_user.id, "phone": payload.phone})

    response: dict = {"phone": payload.phone}
    if settings.is_local:
        response["otp"] = otp_code

    return success_response("OTP sent successfully", response)


@router.post("/verify")
def verify_phone_link_otp(
    payload: PhoneOtpVerifySchema,
    current_user: User = Depends(require_role(UserRole.CLIENT.value)),
    db: Session = Depends(get_db),
):
    if current_user.phone:
        raise HTTPException(
            status_code=400,
            detail="A phone number is already linked to this account.",
        )

    existing = get_user_by_phone(db, payload.phone)
    if existing and existing.id != current_user.id:
        raise HTTPException(
            status_code=409,
            detail="This phone number is already registered to another account.",
        )

    check_rate_limit(f"otp_verify:{payload.phone}", limit=10, window_seconds=300)

    otp_record = get_latest_active_otp(db, payload.phone)
    if not otp_record:
        raise HTTPException(status_code=400, detail="OTP not found. Request a new code.")

    if otp_record.is_used:
        raise HTTPException(status_code=400, detail="OTP already used.")

    if otp_record.expires_at < utcnow():
        raise HTTPException(status_code=400, detail="OTP expired. Request a new code.")

    if otp_record.attempts >= settings.otp_max_attempts:
        raise HTTPException(status_code=400, detail="Too many attempts. Request a new code.")

    otp_record.attempts += 1

    if not verify_password(payload.code, otp_record.code_hash):
        db.commit()
        raise HTTPException(status_code=400, detail="Invalid OTP.")

    otp_record.is_used = True
    current_user.phone = payload.phone
    current_user.is_phone_verified = True

    db.commit()

    audit_event("phone_linked", {"user_id": current_user.id, "phone": payload.phone})

    return success_response("Phone number linked successfully", {"phone": payload.phone})
