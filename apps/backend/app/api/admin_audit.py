from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies.roles import require_role
from app.core.roles import UserRole
from app.db.deps import get_db
from app.models.user import User
from app.repositories.audit_repository import get_recent_audit_logs
from app.utils.response import success_response

router = APIRouter(prefix="/admin/audit", tags=["Admin Audit"])


@router.get("")
def list_admin_audit_logs(
    limit: int = 100,
    current_user: User = Depends(require_role(UserRole.ADMIN.value)),
    db: Session = Depends(get_db),
):
    logs = get_recent_audit_logs(db, min(max(limit, 1), 500))
    data = [
        {
            "id": item.id,
            "action": item.action,
            "details": item.details,
            "created_at": item.created_at.isoformat(),
        }
        for item in logs
    ]
    return success_response("Audit logs fetched successfully", data)
