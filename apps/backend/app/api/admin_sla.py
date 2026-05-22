from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies.roles import require_role
from app.core.roles import UserRole
from app.db.deps import get_db
from app.models.user import User
from app.repositories.sla_repository import get_sla_policies, upsert_sla_policy
from app.schemas.sla import ComplaintSlaPolicyUpdateSchema
from app.utils.audit import audit_event
from app.utils.response import success_response

router = APIRouter(prefix="/admin/sla", tags=["Admin SLA"])


@router.get("/complaints")
def list_complaint_sla_policies(
    current_user: User = Depends(require_role(UserRole.ADMIN.value)),
    db: Session = Depends(get_db),
):
    policies = get_sla_policies(db)
    data = [
        {
            "id": item.id,
            "severity": item.severity,
            "response_hours": item.response_hours,
            "resolution_hours": item.resolution_hours,
        }
        for item in policies
    ]
    return success_response("Complaint SLA policies fetched successfully", data)


@router.put("/complaints")
def update_complaint_sla_policy(
    payload: ComplaintSlaPolicyUpdateSchema,
    current_user: User = Depends(require_role(UserRole.ADMIN.value)),
    db: Session = Depends(get_db),
):
    policy = upsert_sla_policy(
        db,
        severity=payload.severity,
        response_hours=payload.response_hours,
        resolution_hours=payload.resolution_hours,
    )
    db.commit()
    db.refresh(policy)
    audit_event(
        "complaint_sla_policy_updated",
        {
            "severity": policy.severity,
            "response_hours": policy.response_hours,
            "resolution_hours": policy.resolution_hours,
            "admin_user_id": current_user.id,
        },
    )
    return success_response(
        "Complaint SLA policy updated successfully",
        {
            "id": policy.id,
            "severity": policy.severity,
            "response_hours": policy.response_hours,
            "resolution_hours": policy.resolution_hours,
        },
    )
