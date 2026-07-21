from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user
from app.api.dependencies.roles import require_role
from app.core.roles import UserRole
from app.core.security import hash_password, verify_password
from app.db.deps import get_db
from app.models.legal_acceptance import LegalAcceptance
from app.models.privacy_request import PRIVACY_REQUEST_TYPES, PrivacyRequest
from app.models.user import User
from app.repositories.profile_repository import get_admin_profile_by_user_id, get_client_profile_by_user_id
from app.services.privacy_service import build_user_export
from app.services.legal_document_service import (
    CURRENT_LEGAL_EFFECTIVE_DATE,
    CURRENT_LEGAL_VERSION,
    required_documents_for_role,
)
from app.utils.audit import audit_event
from app.utils.response import success_response
from app.utils.time import utcnow

router = APIRouter(prefix="/me", tags=["Me"])


class ChangePasswordSchema(BaseModel):
    current_password: str = Field(min_length=1)
    new_password: str = Field(min_length=8, max_length=128)


class CreatePrivacyRequestSchema(BaseModel):
    request_type: str
    reason: str | None = Field(default=None, max_length=2000)


class AcceptLegalDocumentsSchema(BaseModel):
    version: str = Field(min_length=1, max_length=20)
    document_slugs: list[str] = Field(min_length=1, max_length=10)
    source: str = Field(min_length=1, max_length=50, pattern=r"^[a-z0-9_-]+$")


def _legal_acceptance_status(db: Session, current_user: User) -> dict:
    required = required_documents_for_role(current_user.role)
    accepted = {
        item.document_slug: item
        for item in db.scalars(
            select(LegalAcceptance).where(
                LegalAcceptance.user_id == current_user.id,
                LegalAcceptance.version == CURRENT_LEGAL_VERSION,
            )
        ).all()
    }
    documents = [
        {
            "slug": document.slug,
            "title": document.title,
            "url": document.url,
            "accepted_at": (
                accepted[document.slug].accepted_at.isoformat()
                if document.slug in accepted
                else None
            ),
        }
        for document in required
    ]
    return {
        "version": CURRENT_LEGAL_VERSION,
        "effective_date": CURRENT_LEGAL_EFFECTIVE_DATE,
        "role": current_user.role,
        "is_current": bool(documents)
        and all(document["accepted_at"] is not None for document in documents),
        "required_documents": documents,
    }


def _serialize_privacy_request(item: PrivacyRequest) -> dict:
    return {
        "id": item.id,
        "request_type": item.request_type,
        "status": item.status,
        "reason": item.reason,
        "resolution_notes": item.resolution_notes,
        "requested_at": item.requested_at.isoformat(),
        "resolved_at": item.resolved_at.isoformat() if item.resolved_at else None,
    }


@router.get("")
def me(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    payload: dict = {
        "id": current_user.id,
        "phone": current_user.phone,
        "email": current_user.email,
        "name": current_user.name,
        "role": current_user.role,
        "is_active": current_user.is_active,
    }

    if current_user.role == UserRole.ADMIN.value:
        admin_profile = get_admin_profile_by_user_id(db, current_user.id)
        payload["permission_group"] = admin_profile.permission_group if admin_profile else None

    if current_user.role == UserRole.CLIENT.value:
        profile = get_client_profile_by_user_id(db, current_user.id)
        payload["is_profile_complete"] = profile is not None
        if not payload["name"] and profile:
            payload["name"] = profile.contact_name

    return success_response("Current user fetched successfully", payload)


@router.get("/admin-only")
def admin_only(current_user: User = Depends(require_role(UserRole.ADMIN.value))):
    return success_response("Admin access granted", {"user_id": current_user.id})


@router.get("/client-only")
def client_only(current_user: User = Depends(require_role(UserRole.CLIENT.value))):
    return success_response("Client access granted", {"user_id": current_user.id})


@router.get("/worker-only")
def worker_only(current_user: User = Depends(require_role(UserRole.WORKER.value))):
    return success_response("Worker access granted", {"user_id": current_user.id})


@router.get("/legal-acceptances")
def get_my_legal_acceptances(
    current_user: User = Depends(
        require_role(UserRole.CLIENT.value, UserRole.WORKER.value)
    ),
    db: Session = Depends(get_db),
):
    return success_response(
        "Legal acceptance status fetched successfully",
        _legal_acceptance_status(db, current_user),
    )


@router.post("/legal-acceptances")
def accept_current_legal_documents(
    payload: AcceptLegalDocumentsSchema,
    current_user: User = Depends(
        require_role(UserRole.CLIENT.value, UserRole.WORKER.value)
    ),
    db: Session = Depends(get_db),
):
    required = required_documents_for_role(current_user.role)
    required_slugs = {document.slug for document in required}
    submitted_slugs = set(payload.document_slugs)
    if payload.version != CURRENT_LEGAL_VERSION:
        raise HTTPException(
            status_code=409,
            detail="The legal documents have changed. Review the current version before continuing.",
        )
    if len(payload.document_slugs) != len(submitted_slugs) or submitted_slugs != required_slugs:
        raise HTTPException(
            status_code=422,
            detail="All legal documents required for this role must be accepted together.",
        )

    existing_slugs = set(
        db.scalars(
            select(LegalAcceptance.document_slug).where(
                LegalAcceptance.user_id == current_user.id,
                LegalAcceptance.version == CURRENT_LEGAL_VERSION,
                LegalAcceptance.document_slug.in_(required_slugs),
            )
        ).all()
    )
    accepted_at = utcnow()
    for slug in required_slugs - existing_slugs:
        db.add(
            LegalAcceptance(
                user_id=current_user.id,
                role=current_user.role,
                document_slug=slug,
                version=CURRENT_LEGAL_VERSION,
                source=payload.source,
                accepted_at=accepted_at,
            )
        )
    try:
        db.commit()
    except IntegrityError:
        # A simultaneous retry may have inserted the same immutable records.
        db.rollback()

    audit_event(
        "legal_documents_accepted",
        {
            "user_id": current_user.id,
            "role": current_user.role,
            "version": CURRENT_LEGAL_VERSION,
            "document_slugs": sorted(required_slugs),
            "source": payload.source,
        },
        actor_user_id=current_user.id,
    )
    return success_response(
        "Legal documents accepted successfully",
        _legal_acceptance_status(db, current_user),
    )


@router.patch("/password")
def change_password(
    payload: ChangePasswordSchema,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Change the current user's password. Requires the existing password for verification."""
    if not current_user.password_hash:
        raise HTTPException(status_code=400, detail="Password login is not enabled for this account")

    if not verify_password(payload.current_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect")

    current_user.password_hash = hash_password(payload.new_password)
    db.commit()

    audit_event("password_changed", {"user_id": current_user.id})

    return success_response("Password changed successfully", {})


@router.post("/privacy-requests", status_code=status.HTTP_201_CREATED)
def create_privacy_request(
    payload: CreatePrivacyRequestSchema,
    current_user: User = Depends(
        require_role(UserRole.CLIENT.value, UserRole.WORKER.value)
    ),
    db: Session = Depends(get_db),
):
    if payload.request_type not in PRIVACY_REQUEST_TYPES:
        raise HTTPException(status_code=422, detail="Invalid privacy request type")

    existing = db.scalar(
        select(PrivacyRequest).where(
            PrivacyRequest.user_id == current_user.id,
            PrivacyRequest.request_type == payload.request_type,
            PrivacyRequest.status.in_(("pending", "in_review")),
        )
    )
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"An open {payload.request_type} request already exists",
        )

    item = PrivacyRequest(
        user_id=current_user.id,
        request_type=payload.request_type,
        reason=payload.reason,
    )
    db.add(item)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail=f"An open {payload.request_type} request already exists",
        ) from exc
    db.refresh(item)
    audit_event(
        "privacy_request_created",
        {
            "privacy_request_id": item.id,
            "request_type": item.request_type,
            "user_id": current_user.id,
        },
        actor_user_id=current_user.id,
    )
    return success_response(
        "Privacy request submitted successfully", _serialize_privacy_request(item)
    )


@router.get("/privacy-requests")
def list_my_privacy_requests(
    current_user: User = Depends(
        require_role(UserRole.CLIENT.value, UserRole.WORKER.value)
    ),
    db: Session = Depends(get_db),
):
    items = db.scalars(
        select(PrivacyRequest)
        .where(PrivacyRequest.user_id == current_user.id)
        .order_by(PrivacyRequest.requested_at.desc())
    ).all()
    return success_response(
        "Privacy requests fetched successfully",
        [_serialize_privacy_request(item) for item in items],
    )


@router.get("/privacy-requests/{request_id}/export")
def download_my_data_export(
    request_id: int,
    current_user: User = Depends(
        require_role(UserRole.CLIENT.value, UserRole.WORKER.value)
    ),
    db: Session = Depends(get_db),
):
    item = db.scalar(
        select(PrivacyRequest).where(
            PrivacyRequest.id == request_id,
            PrivacyRequest.user_id == current_user.id,
        )
    )
    if not item:
        raise HTTPException(status_code=404, detail="Privacy request not found")
    if item.request_type != "export" or item.status != "completed":
        raise HTTPException(status_code=409, detail="Data export is not ready")
    audit_event(
        "privacy_export_downloaded",
        {"privacy_request_id": item.id, "user_id": current_user.id},
        actor_user_id=current_user.id,
    )
    return success_response(
        "Data export generated successfully", build_user_export(db, current_user)
    )
