from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.dependencies.roles import require_role
from app.core.roles import UserRole
from app.db.deps import get_db
from app.models.user import User
from app.repositories.profile_repository import (
    create_worker_document,
    create_worker_profile,
    get_worker_documents_by_profile_id,
    get_worker_profile_by_user_id,
)
from app.schemas.profile import (
    WorkerDocumentCreateSchema,
    WorkerProfileCreateSchema,
    WorkerProfileUpdateSchema,
)
from app.services.profile_service import build_worker_document, build_worker_profile
from app.utils.audit import audit_event
from app.utils.response import success_response
from app.utils.time import business_date

router = APIRouter(prefix="/worker/profile", tags=["Worker Profile"])


@router.post("")
def create_my_worker_profile(
    payload: WorkerProfileCreateSchema,
    current_user: User = Depends(require_role(UserRole.WORKER.value)),
    db: Session = Depends(get_db),
):
    existing = get_worker_profile_by_user_id(db, current_user.id)
    if existing:
        raise HTTPException(status_code=400, detail="Worker profile already exists")

    profile = build_worker_profile(payload, current_user.id)
    create_worker_profile(db, profile)
    db.commit()
    db.refresh(profile)

    audit_event("worker_profile_created", {"user_id": current_user.id, "profile_id": profile.id})

    return success_response("Worker profile created successfully", {"id": profile.id})


@router.get("")
def get_my_worker_profile(
    current_user: User = Depends(require_role(UserRole.WORKER.value)),
    db: Session = Depends(get_db),
):
    profile = get_worker_profile_by_user_id(db, current_user.id)
    if not profile:
        raise HTTPException(status_code=404, detail="Worker profile not found")

    documents = get_worker_documents_by_profile_id(db, profile.id)

    return success_response(
        "Worker profile fetched successfully",
        {
            "id": profile.id,
            "full_name": profile.full_name,
            "category": profile.category,
            "subcategory": profile.subcategory,
            "city": profile.city,
            "state": profile.state,
            "address": profile.address,
            "date_of_birth": None if not profile.date_of_birth else str(profile.date_of_birth),
            "skills": profile.skills,
            "experience_notes": profile.experience_notes,
            "available_days": profile.available_days,
            "available_shifts": profile.available_shifts,
            "is_available": profile.is_available,
            "verification_status": profile.verification_status,
            "documents": [
                {
                    "id": document.id,
                    "document_type": document.document_type,
                    "file_url": document.file_url,
                    "verification_status": document.verification_status,
                    "expiry_date": str(document.expiry_date) if document.expiry_date else None,
                    "remarks": document.remarks,
                }
                for document in documents
            ],
        },
    )


@router.patch("")
def update_my_worker_profile(
    payload: WorkerProfileUpdateSchema,
    current_user: User = Depends(require_role(UserRole.WORKER.value)),
    db: Session = Depends(get_db),
):
    profile = get_worker_profile_by_user_id(db, current_user.id)
    if not profile:
        raise HTTPException(status_code=404, detail="Worker profile not found")

    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(profile, key, value)

    db.commit()

    audit_event("worker_profile_updated", {"user_id": current_user.id, "profile_id": profile.id})

    return success_response(
        "Worker profile updated successfully",
        {
            "id": profile.id,
            "is_available": profile.is_available,
            "available_days": profile.available_days,
            "available_shifts": profile.available_shifts,
        },
    )


@router.post("/documents")
def add_my_worker_document(
    payload: WorkerDocumentCreateSchema,
    current_user: User = Depends(require_role(UserRole.WORKER.value)),
    db: Session = Depends(get_db),
):
    profile = get_worker_profile_by_user_id(db, current_user.id)
    if not profile:
        raise HTTPException(status_code=404, detail="Worker profile not found")

    document = build_worker_document(payload, profile.id)
    create_worker_document(db, document)
    db.commit()
    db.refresh(document)

    audit_event(
        "worker_document_added",
        {"user_id": current_user.id, "profile_id": profile.id, "document_id": document.id},
    )

    return success_response("Worker document added successfully", {"id": document.id})


@router.get("/documents")
def list_my_worker_documents(
    current_user: User = Depends(require_role(UserRole.WORKER.value)),
    db: Session = Depends(get_db),
):
    profile = get_worker_profile_by_user_id(db, current_user.id)
    if not profile:
        raise HTTPException(status_code=404, detail="Worker profile not found")

    documents = get_worker_documents_by_profile_id(db, profile.id)
    data = [
        {
            "id": document.id,
            "document_type": document.document_type,
            "file_url": document.file_url,
            "verification_status": document.verification_status,
            "expiry_date": str(document.expiry_date) if document.expiry_date else None,
            "remarks": document.remarks,
        }
        for document in documents
    ]
    return success_response("Worker documents fetched successfully", data)


@router.get("/documents/reminders")
def list_my_document_reminders(
    days: int = Query(default=30, ge=1, le=180),
    current_user: User = Depends(require_role(UserRole.WORKER.value)),
    db: Session = Depends(get_db),
):
    profile = get_worker_profile_by_user_id(db, current_user.id)
    if not profile:
        raise HTTPException(status_code=404, detail="Worker profile not found")

    today = business_date()
    threshold = today + timedelta(days=days)
    documents = get_worker_documents_by_profile_id(db, profile.id)

    reminders = []
    for document in documents:
        if not document.expiry_date or document.expiry_date > threshold:
            continue

        state = "expired" if document.expiry_date < today else "expiring_soon"
        reminders.append(
            {
                "id": document.id,
                "document_type": document.document_type,
                "expiry_date": str(document.expiry_date),
                "state": state,
                "days_remaining": (document.expiry_date - today).days,
            }
        )

    reminders.sort(key=lambda item: item["days_remaining"])
    return success_response("Worker document reminders fetched successfully", reminders)
