import mimetypes

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies.roles import require_permission_group, require_role
from app.core.roles import UserRole
from app.core.security import hash_password
from app.db.deps import get_db
from app.models.admin_profile import AdminProfile, ALLOWED_PERMISSION_GROUPS
from app.models.client_profile import ClientProfile
from app.models.user import User
from app.models.worker_document import WorkerDocument
from app.models.worker_profile import WorkerProfile
from app.repositories.auth_repository import create_admin_user, get_user_by_email, get_user_by_phone
from app.repositories.profile_repository import (
    create_admin_profile,
    create_worker_profile,
    get_clients_paginated_stmt,
    get_workers_paginated_stmt,
)
from app.repositories.requirement_repository import get_requirements_by_client_id
from app.schemas.auth import AdminUserCreateSchema
from app.schemas.profile import WorkerBulkImportSchema, WorkerProfileCreateSchema, WorkerRejectSchema
from app.services.notification_service import enqueue_push_to_user
from app.services.profile_service import build_worker_profile
from app.services.storage_service import generate_download_url, is_s3_configured, resolve_local_document_path
from app.utils.audit import audit_event
from app.utils.pagination import PaginationParams, paginate, pagination_meta
from app.utils.response import success_response


class WorkerAvailabilityToggleSchema(BaseModel):
    is_available: bool


class AdminWorkerUpdateSchema(BaseModel):
    city: str | None = Field(default=None, min_length=2, max_length=100)
    state: str | None = Field(default=None, min_length=2, max_length=100)
    skills: list[str] | None = None
    available_days: list[str] | None = None
    available_shifts: list[str] | None = None
    is_available: bool | None = None
    phone: str | None = Field(default=None, max_length=20)
    email: str | None = Field(default=None, max_length=255)


class AdminClientCreateSchema(BaseModel):
    phone: str = Field(min_length=5, max_length=20)
    client_type: str = Field(default="company", max_length=20)  # 'individual' | 'company'
    company_name: str | None = Field(default=None, min_length=2, max_length=255)
    contact_name: str = Field(min_length=2, max_length=255)
    city: str = Field(min_length=2, max_length=100)
    state: str = Field(min_length=2, max_length=100)
    gst_number: str | None = Field(default=None, max_length=50)


class AdminClientUpdateSchema(BaseModel):
    client_type: str | None = Field(default=None, max_length=20)
    company_name: str | None = Field(default=None, min_length=2, max_length=255)
    contact_name: str = Field(min_length=2, max_length=255)
    city: str = Field(min_length=2, max_length=100)
    state: str = Field(min_length=2, max_length=100)
    gst_number: str | None = Field(default=None, max_length=50)


router = APIRouter(prefix="/admin/people", tags=["Admin People"])


@router.get("/clients")
def list_admin_clients(
    pg: PaginationParams = Depends(),
    current_user: User = Depends(require_role(UserRole.ADMIN.value)),
    db: Session = Depends(get_db),
):
    stmt = get_clients_paginated_stmt()
    clients, total = paginate(stmt, db, pg)
    user_ids = [c.user_id for c in clients]
    users_by_id: dict[int, User] = {}
    if user_ids:
        users = db.execute(select(User).where(User.id.in_(user_ids))).scalars().all()
        users_by_id = {u.id: u for u in users}
    data = [
        {
            "id": item.id,
            "user_id": item.user_id,
            "phone": users_by_id[item.user_id].phone if item.user_id in users_by_id else None,
            "client_type": item.client_type or "company",
            "company_name": item.company_name,
            "contact_name": item.contact_name,
            "city": item.city,
            "state": item.state,
            "gst_number": item.gst_number,
            "is_active": users_by_id[item.user_id].is_active if item.user_id in users_by_id else True,
        }
        for item in clients
    ]
    return success_response(
        "Clients fetched successfully",
        {"items": data, **pagination_meta(pg, total)},
    )


@router.get("/clients/{client_profile_id}")
def get_admin_client_detail(
    client_profile_id: int,
    current_user: User = Depends(require_role(UserRole.ADMIN.value)),
    db: Session = Depends(get_db),
):
    profile = db.get(ClientProfile, client_profile_id)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found.")

    user = db.get(User, profile.user_id)
    requirements = get_requirements_by_client_id(db, profile.id)

    return success_response(
        "Client detail fetched successfully",
        {
            "id": profile.id,
            "user_id": profile.user_id,
            "phone": user.phone if user else None,
            "client_type": profile.client_type or "company",
            "company_name": profile.company_name,
            "contact_name": profile.contact_name,
            "city": profile.city,
            "state": profile.state,
            "gst_number": profile.gst_number,
            "is_active": user.is_active if user else True,
            "requirements": [
                {
                    "id": r.id,
                    "category": r.category,
                    "subcategory": r.subcategory,
                    "number_of_workers": r.number_of_workers,
                    "city": r.city,
                    "state": r.state,
                    "start_date": str(r.start_date),
                    "duration_days": r.duration_days,
                    "status": r.status,
                    "created_at": r.created_at.isoformat(),
                }
                for r in requirements
            ],
        },
    )


@router.post("/clients")
def create_admin_client(
    payload: AdminClientCreateSchema,
    current_user: User = Depends(require_role(UserRole.ADMIN.value)),
    db: Session = Depends(get_db),
):
    existing = db.execute(select(User).where(User.phone == payload.phone)).scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this phone number already exists.",
        )

    user = User(
        phone=payload.phone,
        role=UserRole.CLIENT.value,
        is_active=True,
        is_phone_verified=False,
    )
    db.add(user)
    db.flush()

    profile = ClientProfile(
        user_id=user.id,
        client_type=payload.client_type,
        company_name=payload.company_name or None,
        contact_name=payload.contact_name,
        city=payload.city,
        state=payload.state,
        gst_number=payload.gst_number or None,
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)

    audit_event(
        "client_created_by_admin",
        {"client_user_id": user.id, "admin_user_id": current_user.id},
    )

    return success_response(
        "Client created successfully",
        {
            "id": profile.id,
            "user_id": user.id,
            "phone": user.phone,
            "client_type": profile.client_type or "company",
            "company_name": profile.company_name,
            "contact_name": profile.contact_name,
            "city": profile.city,
            "state": profile.state,
            "gst_number": profile.gst_number,
            "is_active": user.is_active,
        },
    )


@router.patch("/clients/{client_profile_id}")
def update_admin_client(
    client_profile_id: int,
    payload: AdminClientUpdateSchema,
    current_user: User = Depends(require_role(UserRole.ADMIN.value)),
    db: Session = Depends(get_db),
):
    profile = db.get(ClientProfile, client_profile_id)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found.")

    if payload.client_type is not None:
        profile.client_type = payload.client_type
    profile.company_name = payload.company_name or None
    profile.contact_name = payload.contact_name
    profile.city = payload.city
    profile.state = payload.state
    profile.gst_number = payload.gst_number or None
    db.commit()
    db.refresh(profile)

    user = db.get(User, profile.user_id)

    audit_event(
        "client_updated_by_admin",
        {"client_profile_id": client_profile_id, "admin_user_id": current_user.id},
    )

    return success_response(
        "Client updated successfully",
        {
            "id": profile.id,
            "user_id": profile.user_id,
            "phone": user.phone if user else None,
            "client_type": profile.client_type or "company",
            "company_name": profile.company_name,
            "contact_name": profile.contact_name,
            "city": profile.city,
            "state": profile.state,
            "gst_number": profile.gst_number,
            "is_active": user.is_active if user else True,
        },
    )


@router.post("/clients/{client_profile_id}/deactivate")
def deactivate_admin_client(
    client_profile_id: int,
    current_user: User = Depends(require_role(UserRole.ADMIN.value)),
    db: Session = Depends(get_db),
):
    profile = db.get(ClientProfile, client_profile_id)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found.")

    user = db.get(User, profile.user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client user not found.")

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Client is already deactivated.",
        )

    user.is_active = False
    db.commit()

    audit_event(
        "client_deactivated_by_admin",
        {"client_user_id": user.id, "admin_user_id": current_user.id},
    )

    return success_response(
        "Client deactivated successfully",
        {"user_id": user.id, "is_active": False},
    )


@router.get("/workers")
def list_admin_workers(
    verification_status: str | None = Query(None, description="Filter by verification_status"),
    city: str | None = Query(None, description="Filter by city (partial match)"),
    is_available: bool | None = Query(None, description="Filter by availability"),
    category: str | None = Query(None, description="Filter by category (partial match)"),
    pg: PaginationParams = Depends(),
    current_user: User = Depends(require_role(UserRole.ADMIN.value)),
    db: Session = Depends(get_db),
):
    stmt = get_workers_paginated_stmt(
        verification_status=verification_status,
        city=city,
        is_available=is_available,
        category=category,
    )
    workers, total = paginate(stmt, db, pg)
    user_ids = [item.user_id for item in workers]
    users_by_id = {}
    documents_by_user_id: dict[int, list[WorkerDocument]] = {user_id: [] for user_id in user_ids}

    if user_ids:
        users = db.execute(select(User).where(User.id.in_(user_ids))).scalars().all()
        users_by_id = {item.id: item for item in users}

        documents = db.execute(
            select(WorkerDocument).where(WorkerDocument.user_id.in_(user_ids))
        ).scalars().all()
        for document in documents:
            if document.user_id is not None:
                documents_by_user_id.setdefault(document.user_id, []).append(document)

    data = [
        {
            "id": item.id,
            "user_id": item.user_id,
            "phone": users_by_id[item.user_id].phone if item.user_id in users_by_id else None,
            "email": users_by_id[item.user_id].email if item.user_id in users_by_id else None,
            "onboarding_step": users_by_id[item.user_id].onboarding_step if item.user_id in users_by_id else None,
            "full_name": item.full_name,
            "category": item.category,
            "subcategory": item.subcategory,
            "city": item.city,
            "state": item.state,
            "address": item.address,
            "date_of_birth": item.date_of_birth.isoformat() if item.date_of_birth else None,
            "skills": item.skills,
            "experience_years": item.experience_years,
            "experience_notes": item.experience_notes,
            "available_days": item.available_days,
            "available_shifts": item.available_shifts,
            "is_available": item.is_available,
            "verification_status": item.verification_status,
            "submitted_at": item.updated_at.isoformat() if item.updated_at else None,
            "photo_url": item.photo_url,
            "documents": [
                {
                    "id": document.id,
                    "document_type": document.document_type,
                    "file_url": document.file_url,
                    "verification_status": document.verification_status,
                    "remarks": document.remarks,
                    "uploaded_at": document.uploaded_at.isoformat() if document.uploaded_at else None,
                }
                for document in documents_by_user_id.get(item.user_id, [])
            ],
        }
        for item in workers
    ]
    return success_response(
        "Workers fetched successfully",
        {"items": data, **pagination_meta(pg, total)},
    )


@router.get("/worker-documents/{document_id}/view-url")
def get_worker_document_view_url(
    document_id: int,
    current_user: User = Depends(require_role(UserRole.ADMIN.value)),
    db: Session = Depends(get_db),
):
    document = db.get(WorkerDocument, document_id)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Worker document not found")

    audit_event(
        "worker_document_view_requested",
        {"document_id": document_id, "admin_user_id": current_user.id},
    )

    if document.s3_key and is_s3_configured():
        return success_response(
            "Document view URL generated",
            {"mode": "s3", "url": generate_download_url(document.s3_key)},
        )

    return success_response(
        "Document should be fetched from local backend storage",
        {"mode": "local", "url": None},
    )


@router.get("/worker-documents/{document_id}/content")
def get_worker_document_content(
    document_id: int,
    current_user: User = Depends(require_role(UserRole.ADMIN.value)),
    db: Session = Depends(get_db),
):
    document = db.get(WorkerDocument, document_id)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Worker document not found")

    if document.s3_key and is_s3_configured():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Use the presigned document URL for S3 documents.",
        )

    try:
        path = resolve_local_document_path(document.file_url)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid document path") from exc

    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document file not found")

    audit_event(
        "worker_document_content_opened",
        {"document_id": document_id, "admin_user_id": current_user.id},
    )

    media_type = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
    return FileResponse(path, media_type=media_type, filename=path.name)


@router.post("/workers/import")
def bulk_import_workers(
    payload: WorkerBulkImportSchema,
    current_user: User = Depends(require_role(UserRole.ADMIN.value)),
    db: Session = Depends(get_db),
):
    created = []
    skipped = []

    for item in payload.workers:
        existing_user = db.execute(select(User).where(User.phone == item.phone)).scalar_one_or_none()
        if existing_user:
            skipped.append({"phone": item.phone, "reason": "phone already exists"})
            continue

        user = User(
            phone=item.phone,
            email=item.email,
            role=UserRole.WORKER.value,
            is_active=True,
            is_phone_verified=False,
        )
        db.add(user)
        db.flush()

        profile_payload = WorkerProfileCreateSchema(
            full_name=item.full_name,
            category=item.category,
            subcategory=item.subcategory,
            city=item.city,
            state=item.state,
            address=item.address,
            date_of_birth=item.date_of_birth,
            skills=item.skills,
            experience_notes=item.experience_notes,
        )
        profile = build_worker_profile(profile_payload, user.id)
        create_worker_profile(db, profile)
        db.flush()
        created.append({"phone": user.phone, "user_id": user.id, "worker_profile_id": profile.id})

    db.commit()

    audit_event(
        "workers_bulk_imported",
        {
            "created_count": len(created),
            "skipped_count": len(skipped),
            "admin_user_id": current_user.id,
        },
    )

    return success_response(
        "Worker import completed",
        {
            "created_count": len(created),
            "skipped_count": len(skipped),
            "created": created,
            "skipped": skipped,
        },
    )


@router.post("/workers/{user_id}/approve")
def approve_worker(
    user_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_role(UserRole.ADMIN.value)),
    db: Session = Depends(get_db),
):
    """
    Approve a worker after document and profile review.
    Sets onboarding_step = 'approved' on the user and marks the worker profile
    as verified. The mobile app will gate-show BiometricCheck on next login.
    """
    worker = db.execute(select(User).where(User.id == user_id, User.role == UserRole.WORKER.value)).scalar_one_or_none()
    if not worker:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Worker not found")

    if worker.onboarding_step != "profile_submitted":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Worker is not in profile_submitted state (current: {worker.onboarding_step})",
        )

    worker.onboarding_step = "approved"

    profile = db.execute(
        select(WorkerProfile).where(WorkerProfile.user_id == user_id)
    ).scalar_one_or_none()
    if profile:
        profile.verification_status = "approved"

    # Mark all pending documents as verified
    pending_docs = db.execute(
        select(WorkerDocument).where(
            WorkerDocument.user_id == user_id,
            WorkerDocument.verification_status == "pending",
        )
    ).scalars().all()
    for doc in pending_docs:
        doc.verification_status = "verified"

    db.commit()

    audit_event(
        "worker_approved",
        {"worker_user_id": user_id, "admin_user_id": current_user.id},
    )

    enqueue_push_to_user(
        background_tasks,
        db,
        user_id=user_id,
        title="Profile Approved!",
        body="Congratulations! Your profile has been approved. Please complete biometric setup to start working.",
        data={"type": "worker_approved", "screen": "HomeTab"},
    )

    return success_response("Worker approved", {"user_id": user_id, "onboarding_step": "approved"})


@router.post("/workers/{user_id}/reject")
def reject_worker(
    user_id: int,
    payload: WorkerRejectSchema,
    current_user: User = Depends(require_role(UserRole.ADMIN.value)),
    db: Session = Depends(get_db),
):
    """
    Reject a worker profile after document and profile review.
    The worker remains out of the dashboard flow until they resubmit corrected
    profile details or documents.
    """
    worker = db.execute(select(User).where(User.id == user_id, User.role == UserRole.WORKER.value)).scalar_one_or_none()
    if not worker:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Worker not found")

    if worker.onboarding_step != "profile_submitted":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Worker is not in profile_submitted state (current: {worker.onboarding_step})",
        )

    worker.onboarding_step = "identity_uploaded"

    profile = db.execute(
        select(WorkerProfile).where(WorkerProfile.user_id == user_id)
    ).scalar_one_or_none()
    if profile:
        profile.verification_status = "rejected"

    pending_docs = db.execute(
        select(WorkerDocument).where(
            WorkerDocument.user_id == user_id,
            WorkerDocument.verification_status == "pending",
        )
    ).scalars().all()
    for doc in pending_docs:
        doc.verification_status = "rejected"
        doc.remarks = payload.reason

    db.commit()

    audit_event(
        "worker_rejected",
        {
            "worker_user_id": user_id,
            "admin_user_id": current_user.id,
            "reason": payload.reason,
        },
    )

    return success_response(
        "Worker rejected",
        {"user_id": user_id, "onboarding_step": "identity_uploaded"},
    )


@router.patch("/workers/{user_id}/availability")
def set_worker_availability(
    user_id: int,
    payload: WorkerAvailabilityToggleSchema,
    current_user: User = Depends(require_role(UserRole.ADMIN.value)),
    db: Session = Depends(get_db),
):
    """
    Admin quick-toggle to mark a worker as available or on leave.
    Only updates the is_available flag on the worker profile.
    Worker must be in an approved state to be eligible for assignment regardless.
    """
    worker = db.execute(
        select(User).where(User.id == user_id, User.role == UserRole.WORKER.value)
    ).scalar_one_or_none()
    if not worker:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Worker not found")

    profile = db.execute(
        select(WorkerProfile).where(WorkerProfile.user_id == user_id)
    ).scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Worker profile not found")

    profile.is_available = payload.is_available
    db.commit()

    audit_event(
        "worker_availability_set_by_admin",
        {
            "worker_user_id": user_id,
            "admin_user_id": current_user.id,
            "is_available": payload.is_available,
        },
    )

    label = "available" if payload.is_available else "on leave"
    return success_response(
        f"Worker marked as {label}",
        {"user_id": user_id, "is_available": payload.is_available},
    )


@router.get("/workers/{worker_profile_id}")
def get_admin_worker_detail(
    worker_profile_id: int,
    current_user: User = Depends(require_role(UserRole.ADMIN.value)),
    db: Session = Depends(get_db),
):
    from app.repositories.assignment_repository import get_assignments_by_worker_profile_id
    from app.repositories.payroll_repository import get_payroll_items_by_worker_profile_id

    profile = db.get(WorkerProfile, worker_profile_id)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Worker not found")

    user = db.get(User, profile.user_id)
    documents = db.execute(
        select(WorkerDocument).where(WorkerDocument.user_id == profile.user_id)
    ).scalars().all()

    assignments = get_assignments_by_worker_profile_id(db, worker_profile_id)
    payroll_items = get_payroll_items_by_worker_profile_id(db, worker_profile_id)

    return success_response(
        "Worker fetched successfully",
        {
            "id": profile.id,
            "user_id": profile.user_id,
            "phone": user.phone if user else None,
            "email": user.email if user else None,
            "onboarding_step": user.onboarding_step if user else None,
            "full_name": profile.full_name,
            "category": profile.category,
            "subcategory": profile.subcategory,
            "city": profile.city,
            "state": profile.state,
            "address": profile.address,
            "date_of_birth": profile.date_of_birth.isoformat() if profile.date_of_birth else None,
            "skills": profile.skills,
            "experience_years": profile.experience_years,
            "experience_notes": profile.experience_notes,
            "available_days": profile.available_days,
            "available_shifts": profile.available_shifts,
            "is_available": profile.is_available,
            "verification_status": profile.verification_status,
            "submitted_at": profile.updated_at.isoformat() if profile.updated_at else None,
            "photo_url": profile.photo_url,
            "documents": [
                {
                    "id": doc.id,
                    "document_type": doc.document_type,
                    "file_url": doc.file_url,
                    "verification_status": doc.verification_status,
                    "remarks": doc.remarks,
                    "uploaded_at": doc.uploaded_at.isoformat() if doc.uploaded_at else None,
                }
                for doc in documents
            ],
            "assignments": [
                {
                    "id": a.id,
                    "requirement_id": a.requirement_id,
                    "assigned_role": a.assigned_role,
                    "assigned_shift": a.assigned_shift,
                    "salary_amount": a.salary_amount,
                    "status": a.status,
                    "assigned_at": a.assigned_at.isoformat() if a.assigned_at else None,
                }
                for a in assignments
            ],
            "payroll_items": [
                {
                    "id": pi.id,
                    "payroll_run_id": pi.payroll_run_id,
                    "assignment_id": pi.assignment_id,
                    "gross_amount": pi.gross_amount,
                    "total_deduction_amount": pi.total_deduction_amount,
                    "net_amount": pi.net_amount,
                    "attendance_days": pi.attendance_days,
                    "payment_status": pi.payment_status,
                }
                for pi in payroll_items
            ],
        },
    )


@router.patch("/workers/{worker_profile_id}")
def update_admin_worker(
    worker_profile_id: int,
    payload: AdminWorkerUpdateSchema,
    current_user: User = Depends(require_role(UserRole.ADMIN.value)),
    db: Session = Depends(get_db),
):
    profile = db.get(WorkerProfile, worker_profile_id)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Worker not found")

    user = db.get(User, profile.user_id)

    if payload.city is not None:
        profile.city = payload.city
    if payload.state is not None:
        profile.state = payload.state
    if payload.skills is not None:
        profile.skills = payload.skills
    if payload.available_days is not None:
        profile.available_days = payload.available_days
    if payload.available_shifts is not None:
        profile.available_shifts = payload.available_shifts
    if payload.is_available is not None:
        profile.is_available = payload.is_available
    if user:
        if payload.phone is not None:
            normalized_phone = payload.phone.strip()
            if normalized_phone != user.phone:
                existing = get_user_by_phone(db, normalized_phone)
                if existing:
                    raise HTTPException(
                        status_code=409,
                        detail="Phone number is already in use by another account",
                    )
            user.phone = normalized_phone
        if payload.email is not None:
            user.email = payload.email

    db.commit()

    audit_event(
        "worker_profile_updated_by_admin",
        {"worker_profile_id": worker_profile_id, "admin_user_id": current_user.id},
    )

    return success_response("Worker updated", {"worker_profile_id": worker_profile_id})


@router.get("/admin-users")
def list_admin_users(
    current_user: User = Depends(require_role(UserRole.ADMIN.value)),
    db: Session = Depends(get_db),
):
    users = db.execute(
        select(User).where(User.role == UserRole.ADMIN.value).order_by(User.created_at)
    ).scalars().all()
    user_ids = [u.id for u in users]
    profiles_by_user_id: dict[int, AdminProfile] = {}
    if user_ids:
        profiles = db.execute(
            select(AdminProfile).where(AdminProfile.user_id.in_(user_ids))
        ).scalars().all()
        profiles_by_user_id = {p.user_id: p for p in profiles}
    return success_response(
        "Admin users fetched successfully",
        [
            {
                "id": u.id,
                "email": u.email,
                "name": u.name,
                "is_active": u.is_active,
                "created_at": u.created_at.isoformat(),
                "permission_group": profiles_by_user_id[u.id].permission_group
                if u.id in profiles_by_user_id
                else None,
            }
            for u in users
        ],
    )


class AdminUserCreateWithGroupSchema(AdminUserCreateSchema):
    permission_group: str = "ops_admin"


@router.post("/admin-users", status_code=status.HTTP_201_CREATED)
def create_admin_user_endpoint(
    payload: AdminUserCreateWithGroupSchema,
    current_user: User = Depends(require_permission_group("super_admin")),
    db: Session = Depends(get_db),
):
    normalized_group = payload.permission_group.strip().lower()
    if normalized_group not in ALLOWED_PERMISSION_GROUPS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"permission_group must be one of: {', '.join(sorted(ALLOWED_PERMISSION_GROUPS))}",
        )

    existing = get_user_by_email(db, payload.email)
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already in use")

    user = create_admin_user(
        db=db,
        email=payload.email,
        name=payload.name,
        password_hash=hash_password(payload.password),
    )
    db.flush()

    profile = AdminProfile(
        user_id=user.id,
        full_name=payload.name,
        permission_group=normalized_group,
    )
    create_admin_profile(db, profile)
    db.commit()

    audit_event("admin_user_created", {"new_user_id": user.id, "created_by": current_user.id})

    return success_response(
        "Admin user created",
        {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "is_active": user.is_active,
            "permission_group": normalized_group,
        },
    )
