from app.core.profile_constants import VerificationStatus
from app.models.admin_profile import AdminProfile
from app.models.client_profile import ClientProfile
from app.models.worker_document import WorkerDocument
from app.models.worker_profile import WorkerProfile


def build_client_profile(payload, user_id: int) -> ClientProfile:
    return ClientProfile(
        user_id=user_id,
        client_type=payload.client_type or "company",
        company_name=payload.company_name,
        contact_name=payload.contact_name,
        city=payload.city,
        state=payload.state,
        address=payload.address,
        gst_number=payload.gst_number,
        email=getattr(payload, 'email', None),
    )


def build_worker_profile(payload, user_id: int) -> WorkerProfile:
    return WorkerProfile(
        user_id=user_id,
        full_name=payload.full_name,
        category=payload.category,
        subcategory=payload.subcategory,
        city=payload.city,
        state=payload.state,
        address=payload.address,
        date_of_birth=payload.date_of_birth,
        skills=payload.skills,
        experience_notes=payload.experience_notes,
        verification_status=VerificationStatus.PENDING.value,
    )


def build_worker_document(payload, worker_profile_id: int) -> WorkerDocument:
    return WorkerDocument(
        worker_profile_id=worker_profile_id,
        document_type=payload.document_type,
        file_url=payload.file_url,
        verification_status=VerificationStatus.PENDING.value,
        expiry_date=payload.expiry_date,
        remarks=payload.remarks,
    )


def build_admin_profile(payload, user_id: int) -> AdminProfile:
    return AdminProfile(
        user_id=user_id,
        full_name=payload.full_name,
        department=payload.department,
        permission_group=getattr(payload, "permission_group", "ops_admin") or "ops_admin",
    )
