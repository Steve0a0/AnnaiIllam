import logging
from datetime import timedelta
from app.utils.time import utcnow

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import generate_numeric_otp, hash_password
from app.repositories.auth_repository import create_otp_record, invalidate_active_otps
from app.services.sms_service import send_otp_sms

logger = logging.getLogger(__name__)


def issue_login_otp(db: Session, phone: str) -> str:
    code = generate_numeric_otp(settings.otp_length)
    code_hash = hash_password(code)
    expires_at = utcnow() + timedelta(minutes=settings.otp_expire_minutes)

    invalidate_active_otps(db=db, phone=phone, purpose="login")
    create_otp_record(
        db=db,
        phone=phone,
        code_hash=code_hash,
        purpose="login",
        expires_at=expires_at,
    )

    if not settings.is_local:
        send_otp_sms(phone, code)

    return code
