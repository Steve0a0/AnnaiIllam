"""
Worker onboarding API.

Step-by-step flow:
  1. Phone OTP verified → user created, onboarding_step = None
  2. POST /worker/onboarding/upload-url   → get presigned S3 PUT URL per document
  3. Mobile uploads file directly to S3 via presigned URL
  4. POST /worker/onboarding/identity     → record document S3 keys, step = "identity_uploaded"
  5. POST /worker/onboarding/profile      → create worker profile + encrypted payment details,
                                            link documents, step = "profile_submitted"
  6. Admin reviews → step = "approved"
  7. GET  /worker/onboarding/status       → current step + what's still needed
"""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies.roles import require_role
from app.core.encryption import encrypt_optional
from app.core.roles import UserRole
from app.db.deps import get_db
from app.models.user import User
from app.models.worker_document import WorkerDocument
from app.models.worker_profile import WorkerProfile
from app.repositories.profile_repository import get_worker_profile_by_user_id
from app.services.storage_service import (
    build_public_s3_url,
    generate_upload_url,
    is_s3_configured,
    save_local_document,
)
from app.utils.audit import audit_event
from app.utils.response import success_response

router = APIRouter(prefix="/worker/onboarding", tags=["Worker Onboarding"])

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp", "application/pdf"}

ALLOWED_DOCUMENT_TYPES = {"govt_id", "selfie"}

EXPERIENCE_OPTIONS = {"< 1 year", "1–2 years", "3–5 years", "5+ years"}


# ── Schemas ──────────────────────────────────────────────────────────────────

class UploadUrlRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_type: str = Field(pattern=r"^(govt_id|selfie)$")
    content_type: str


class IdentitySubmitRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    govt_id_key: str = Field(min_length=1, max_length=1000)
    selfie_key: str = Field(min_length=1, max_length=1000)


class PaymentDetailsSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    upi_id: str | None = Field(default=None, max_length=100)
    bank_account_number: str | None = Field(default=None, max_length=50)
    bank_ifsc: str | None = Field(default=None, max_length=11)
    bank_holder_name: str | None = Field(default=None, max_length=255)

    @field_validator("bank_ifsc", mode="before")
    @classmethod
    def upper_ifsc(cls, v: str | None) -> str | None:
        return v.strip().upper() if v else None


class ProfileSubmitRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    full_name: str = Field(min_length=2, max_length=255)
    skills: list[str] = Field(min_length=1, max_length=20)
    experience_years: str
    available_days: list[str] = Field(min_length=1, max_length=7)
    available_shifts: list[str] = Field(min_length=1, max_length=4)
    city: str = Field(min_length=2, max_length=100)
    state: str = Field(min_length=2, max_length=100)
    payment: PaymentDetailsSchema

    @field_validator("experience_years")
    @classmethod
    def validate_experience(cls, v: str) -> str:
        if v not in EXPERIENCE_OPTIONS:
            raise ValueError(f"experience_years must be one of: {', '.join(EXPERIENCE_OPTIONS)}")
        return v


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/status")
def get_onboarding_status(
    current_user: User = Depends(require_role(UserRole.WORKER.value)),
    db: Session = Depends(get_db),
):
    """Returns the worker's current onboarding step and whether their profile exists."""
    profile = get_worker_profile_by_user_id(db, current_user.id)
    return success_response(
        "Onboarding status fetched",
        {
            "onboarding_step": current_user.onboarding_step,
            "has_profile": profile is not None,
            "verification_status": profile.verification_status if profile else None,
        },
    )


@router.post("/upload-url")
def get_upload_url(
    payload: UploadUrlRequest,
    current_user: User = Depends(require_role(UserRole.WORKER.value)),
):
    """
    Returns a presigned S3 PUT URL for direct document upload.
    If S3 is not configured (local dev), returns a placeholder instructing the
    client to pass the local URI directly to /identity.
    """
    if payload.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unsupported content type. Allowed: {', '.join(sorted(ALLOWED_CONTENT_TYPES))}",
        )

    if not is_s3_configured():
        # Local dev mode: mobile app will pass the local URI as the key
        return success_response(
            "S3 not configured — use local URI as key",
            {
                "upload_url": None,
                "s3_key": None,
                "dev_mode": True,
            },
        )

    upload_url, s3_key = generate_upload_url(
        user_id=current_user.id,
        document_type=payload.document_type,
        content_type=payload.content_type,
    )
    return success_response(
        "Presigned upload URL generated",
        {
            "upload_url": upload_url,
            "s3_key": s3_key,
            "expires_in_seconds": 300,
            "dev_mode": False,
        },
    )


@router.post("/local-upload")
async def upload_local_document(
    document_type: str,
    file: UploadFile = File(...),
    current_user: User = Depends(require_role(UserRole.WORKER.value)),
):
    """
    Free local-development document upload.
    Used only when S3 is not configured. Production must use S3 presigned URLs.
    """
    if is_s3_configured():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Local document upload is disabled when S3 is configured.",
        )

    if document_type not in ALLOWED_DOCUMENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"document_type must be one of: {', '.join(sorted(ALLOWED_DOCUMENT_TYPES))}",
        )

    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unsupported content type. Allowed: {', '.join(sorted(ALLOWED_CONTENT_TYPES))}",
        )

    content = await file.read()
    local_key, _path = save_local_document(
        user_id=current_user.id,
        document_type=document_type,
        filename=file.filename or f"{document_type}.bin",
        content=content,
    )
    return success_response("Document uploaded locally", {"local_key": local_key})


@router.post("/identity")
def submit_identity(
    payload: IdentitySubmitRequest,
    current_user: User = Depends(require_role(UserRole.WORKER.value)),
    db: Session = Depends(get_db),
):
    """
    Records the uploaded identity document references.
    Called AFTER the mobile app has uploaded files to S3 (or in dev, passes local URIs).
    Advances onboarding_step to "identity_uploaded".
    """
    # Remove any previously submitted (pending) docs for this user
    db.query(WorkerDocument).filter(
        WorkerDocument.user_id == current_user.id,
        WorkerDocument.worker_profile_id.is_(None),
    ).delete(synchronize_session="fetch")

    def _make_doc(doc_type: str, key: str) -> WorkerDocument:
        is_local = key.startswith("local:")
        is_s3 = is_s3_configured() and not is_local and not key.startswith("/") and not key.startswith("file://")
        return WorkerDocument(
            user_id=current_user.id,
            worker_profile_id=None,
            document_type=doc_type,
            s3_key=key if is_s3 else None,
            file_url=build_public_s3_url(key) if is_s3 else key,
            verification_status="pending",
        )

    db.add(_make_doc("govt_id", payload.govt_id_key))
    db.add(_make_doc("selfie", payload.selfie_key))

    current_user.onboarding_step = "identity_uploaded"
    db.commit()

    audit_event("worker_identity_submitted", {"user_id": current_user.id})

    return success_response("Identity documents recorded. Proceed to build your profile.", {})


@router.post("/profile")
def submit_profile(
    payload: ProfileSubmitRequest,
    current_user: User = Depends(require_role(UserRole.WORKER.value)),
    db: Session = Depends(get_db),
):
    """
    Creates (or updates) the worker profile with all details and encrypted payment fields.
    Links pending identity documents to the profile.
    Advances onboarding_step to "profile_submitted".
    """
    if current_user.onboarding_step not in ("identity_uploaded", "profile_submitted"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please complete identity verification before submitting your profile.",
        )

    existing = get_worker_profile_by_user_id(db, current_user.id)

    if existing:
        profile = existing
    else:
        profile = WorkerProfile(user_id=current_user.id)
        db.add(profile)

    profile.full_name = payload.full_name.strip()
    profile.skills = ",".join(payload.skills)
    profile.experience_years = payload.experience_years
    profile.available_days = ",".join(payload.available_days)
    profile.available_shifts = ",".join(payload.available_shifts)
    profile.city = payload.city.strip()
    profile.state = payload.state.strip()
    # category defaults to "general" until admin sets it during review
    if not profile.category:
        profile.category = "general"
    profile.verification_status = "under_review"

    # Encrypt sensitive payment fields before saving
    p = payload.payment
    profile.upi_id_enc = encrypt_optional(p.upi_id)
    profile.bank_account_enc = encrypt_optional(p.bank_account_number)
    profile.bank_ifsc_enc = encrypt_optional(p.bank_ifsc)
    profile.bank_holder_name = p.bank_holder_name.strip() if p.bank_holder_name else None

    db.flush()  # ensure profile.id is set before linking documents

    # Link pending identity documents to this profile
    db.query(WorkerDocument).filter(
        WorkerDocument.user_id == current_user.id,
        WorkerDocument.worker_profile_id.is_(None),
    ).update({"worker_profile_id": profile.id}, synchronize_session="fetch")

    # Derive profile photo from the selfie document
    selfie = db.execute(
        select(WorkerDocument).where(
            WorkerDocument.worker_profile_id == profile.id,
            WorkerDocument.document_type == "selfie",
        ).order_by(WorkerDocument.uploaded_at.desc())
    ).scalar_one_or_none()
    if selfie and not profile.photo_url:
        profile.photo_url = selfie.file_url

    current_user.onboarding_step = "profile_submitted"
    db.commit()

    audit_event(
        "worker_profile_submitted",
        {"user_id": current_user.id, "profile_id": profile.id},
    )

    return success_response(
        "Profile submitted for review. You will be notified once approved.",
        {"profile_id": profile.id},
    )
