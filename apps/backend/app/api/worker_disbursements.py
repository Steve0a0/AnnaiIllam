from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies.roles import require_role
from app.api.admin_disbursements import _serialize
from app.core.roles import UserRole
from app.db.deps import get_db
from app.models.user import User
from app.models.worker_disbursement import WorkerDisbursement
from app.repositories.profile_repository import get_worker_profile_by_user_id
from app.utils.pagination import PaginationParams, paginate, pagination_meta
from app.utils.response import success_response

router = APIRouter(prefix="/worker/disbursements", tags=["Worker Disbursements"])


@router.get("")
def list_my_disbursements(
    pg: PaginationParams = Depends(),
    current_user: User = Depends(require_role(UserRole.WORKER.value)),
    db: Session = Depends(get_db),
):
    """Return paginated disbursements for the authenticated worker."""
    worker_profile = get_worker_profile_by_user_id(db, current_user.id)
    if not worker_profile:
        raise HTTPException(status_code=404, detail="Worker profile not found")

    stmt = (
        select(WorkerDisbursement)
        .where(WorkerDisbursement.worker_profile_id == worker_profile.id)
        .order_by(WorkerDisbursement.created_at.desc())
    )
    items, total = paginate(stmt, db, pg)

    return success_response(
        "Disbursements fetched successfully",
        {"items": [_serialize(d) for d in items], **pagination_meta(pg, total)},
    )
