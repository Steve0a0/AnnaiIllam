from fastapi import APIRouter, Depends
from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.api.dependencies.roles import require_permission_group
from app.db.deps import get_db
from app.models.otp_code import OtpCode
from app.models.revoked_access_token import RevokedAccessToken
from app.models.user import User
from app.utils.audit import audit_event
from app.utils.response import success_response
from app.utils.time import utcnow

router = APIRouter(prefix="/admin/maintenance", tags=["Admin Maintenance"])


@router.post("/cleanup")
def run_cleanup(
    current_user: User = Depends(require_permission_group("super_admin")),
    db: Session = Depends(get_db),
):
    """Delete expired and used OTP codes and expired revoked token records."""
    now = utcnow()

    otp_result = db.execute(
        delete(OtpCode).where(
            (OtpCode.expires_at < now) | (OtpCode.is_used == True)  # noqa: E712
        )
    )
    token_result = db.execute(
        delete(RevokedAccessToken).where(RevokedAccessToken.expires_at < now)
    )
    db.commit()

    deleted_otps = otp_result.rowcount
    deleted_tokens = token_result.rowcount

    audit_event(
        "maintenance_cleanup",
        {
            "deleted_otps": deleted_otps,
            "deleted_revoked_tokens": deleted_tokens,
            "triggered_by_user_id": current_user.id,
        },
    )

    return success_response(
        "Cleanup completed",
        {
            "deleted_otps": deleted_otps,
            "deleted_revoked_tokens": deleted_tokens,
        },
    )
