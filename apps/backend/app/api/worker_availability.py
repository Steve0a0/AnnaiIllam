from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.dependencies.roles import require_role
from app.core.roles import UserRole
from app.db.deps import get_db
from app.models.user import User
from app.repositories.profile_repository import get_worker_profile_by_user_id
from app.repositories.worker_availability_repository import (
    get_worker_availability,
    upsert_worker_availability,
)
from app.schemas.worker_availability import WorkerAvailabilityUpsertSchema
from app.utils.audit import audit_event
from app.utils.response import success_response

router = APIRouter(prefix="/worker/availability", tags=["Worker Availability"])


@router.get("")
def list_my_availability(
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    current_user: User = Depends(require_role(UserRole.WORKER.value)),
    db: Session = Depends(get_db),
):
    profile = get_worker_profile_by_user_id(db, current_user.id)
    if not profile:
        raise HTTPException(status_code=404, detail="Worker profile not found")

    records = get_worker_availability(db, profile.id, start_date=start_date, end_date=end_date)
    data = [
        {
            "id": record.id,
            "availability_date": str(record.availability_date),
            "status": record.status,
            "notes": record.notes,
        }
        for record in records
    ]
    return success_response("Worker availability fetched successfully", data)


@router.put("")
def set_my_availability(
    payload: WorkerAvailabilityUpsertSchema,
    current_user: User = Depends(require_role(UserRole.WORKER.value)),
    db: Session = Depends(get_db),
):
    profile = get_worker_profile_by_user_id(db, current_user.id)
    if not profile:
        raise HTTPException(status_code=404, detail="Worker profile not found")

    record = upsert_worker_availability(
        db,
        worker_profile_id=profile.id,
        availability_date=payload.availability_date,
        status=payload.status,
        notes=payload.notes,
    )
    profile.is_available = payload.status == "available"
    db.commit()
    db.refresh(record)

    audit_event(
        "worker_availability_updated",
        {
            "user_id": current_user.id,
            "profile_id": profile.id,
            "availability_date": str(record.availability_date),
            "status": record.status,
        },
    )

    return success_response(
        "Worker availability updated successfully",
        {
            "id": record.id,
            "availability_date": str(record.availability_date),
            "status": record.status,
            "notes": record.notes,
        },
    )
