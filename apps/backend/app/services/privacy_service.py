from datetime import date, datetime
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.admin_profile import AdminProfile
from app.models.assignment import Assignment
from app.models.attendance import Attendance
from app.models.audit_log import AuditLog
from app.models.client_payment import ClientPayment
from app.models.client_profile import ClientProfile
from app.models.invoice import Invoice
from app.models.legal_acceptance import LegalAcceptance
from app.models.otp_code import OtpCode
from app.models.payroll_item import PayrollItem
from app.models.payroll_run import PayrollRun
from app.models.privacy_request import PrivacyRequest
from app.models.push_token import PushToken
from app.models.refresh_token import RefreshToken
from app.models.requirement import Requirement
from app.models.user import User
from app.models.worker_document import WorkerDocument
from app.models.worker_availability import WorkerAvailability
from app.models.worker_interest import WorkerInterest
from app.models.worker_profile import WorkerProfile
from app.services.storage_service import delete_document_object
from app.utils.time import utcnow


def _json_value(value: Any) -> Any:
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return value


def _record(item: Any, fields: tuple[str, ...]) -> dict[str, Any]:
    return {field: _json_value(getattr(item, field)) for field in fields}


def _scrub_identifiers(value: Any, identifiers: set[str]) -> tuple[Any, bool]:
    if isinstance(value, dict):
        changed = False
        result = {}
        for key, child in value.items():
            result[key], child_changed = _scrub_identifiers(child, identifiers)
            changed = changed or child_changed
        return result, changed
    if isinstance(value, list):
        changed = False
        result = []
        for child in value:
            scrubbed, child_changed = _scrub_identifiers(child, identifiers)
            result.append(scrubbed)
            changed = changed or child_changed
        return result, changed
    if isinstance(value, str):
        scrubbed = value
        for identifier in identifiers:
            scrubbed = scrubbed.replace(identifier, "[ANONYMIZED]")
        return scrubbed, scrubbed != value
    return value, False


def build_user_export(db: Session, user: User) -> dict[str, Any]:
    """Build an on-demand export without persisting a second copy of personal data."""
    export: dict[str, Any] = {
        "generated_at": utcnow().isoformat(),
        "account": _record(
            user,
            (
                "id", "phone", "email", "name", "role", "is_active",
                "is_phone_verified", "is_email_verified", "onboarding_step",
                "created_at", "updated_at",
            ),
        ),
        "privacy_requests": [
            _record(
                item,
                (
                    "id", "request_type", "status", "reason",
                    "resolution_notes", "requested_at", "resolved_at",
                ),
            )
            for item in db.scalars(
                select(PrivacyRequest)
                .where(PrivacyRequest.user_id == user.id)
                .order_by(PrivacyRequest.requested_at)
            ).all()
        ],
        "legal_acceptances": [
            _record(
                item,
                (
                    "document_slug", "version", "role", "source", "accepted_at",
                ),
            )
            for item in db.scalars(
                select(LegalAcceptance)
                .where(LegalAcceptance.user_id == user.id)
                .order_by(LegalAcceptance.accepted_at, LegalAcceptance.document_slug)
            ).all()
        ],
    }

    if user.role == "client":
        profile = db.scalar(select(ClientProfile).where(ClientProfile.user_id == user.id))
        if profile:
            export["profile"] = _record(
                profile,
                (
                    "id", "client_type", "company_name", "contact_name", "city",
                    "state", "address", "gst_number", "industry", "email",
                    "default_job_category", "food_preference",
                    "accommodation_preference", "standing_notes", "created_at",
                    "updated_at",
                ),
            )
            export["requirements"] = [
                _record(
                    item,
                    (
                        "id", "category", "number_of_workers", "work_location",
                        "city", "state", "start_date", "duration_days",
                        "shift_details", "budget_amount", "status", "created_at",
                    ),
                )
                for item in db.scalars(
                    select(Requirement).where(Requirement.client_id == profile.id)
                ).all()
            ]
            export["payments"] = [
                _record(
                    item,
                    (
                        "id", "requirement_id", "amount", "purpose",
                        "payment_model", "payment_mode", "payment_status",
                        "paid_at", "created_at",
                    ),
                )
                for item in db.scalars(
                    select(ClientPayment).where(ClientPayment.client_id == profile.id)
                ).all()
            ]
            export["invoices"] = [
                _record(
                    item,
                    (
                        "id", "invoice_number", "requirement_id", "subtotal",
                        "gst_amount", "total_amount", "status", "invoice_date",
                        "issued_at", "due_date",
                    ),
                )
                for item in db.scalars(
                    select(Invoice).where(Invoice.client_id == profile.id)
                ).all()
            ]

    if user.role == "worker":
        profile = db.scalar(select(WorkerProfile).where(WorkerProfile.user_id == user.id))
        if profile:
            export["profile"] = _record(
                profile,
                (
                    "id", "full_name", "category", "subcategory", "city",
                    "state", "address", "date_of_birth", "skills",
                    "experience_years", "experience_notes", "available_days",
                    "available_shifts", "is_available", "verification_status",
                    "created_at", "updated_at",
                ),
            )
            export["assignments"] = [
                _record(
                    item,
                    (
                        "id", "requirement_id", "status", "assigned_role",
                        "assigned_shift", "salary_amount", "start_date", "end_date",
                        "assigned_at",
                    ),
                )
                for item in db.scalars(
                    select(Assignment).where(Assignment.worker_profile_id == profile.id)
                ).all()
            ]
            export["attendance"] = [
                _record(
                    item,
                    (
                        "id", "assignment_id", "attendance_date", "status",
                        "check_in_time", "check_out_time", "approval_status",
                        "approved_at",
                    ),
                )
                for item in db.scalars(
                    select(Attendance).where(Attendance.worker_profile_id == profile.id)
                ).all()
            ]
            payroll_items = db.scalars(
                select(PayrollItem).where(PayrollItem.worker_profile_id == profile.id)
            ).all()
            payroll_run_ids = {item.payroll_run_id for item in payroll_items}
            payroll_runs = (
                {
                    item.id: item
                    for item in db.scalars(
                        select(PayrollRun).where(PayrollRun.id.in_(payroll_run_ids))
                    ).all()
                }
                if payroll_run_ids
                else {}
            )
            export["payroll"] = [
                {
                    **_record(
                        item,
                        (
                            "id", "assignment_id", "gross_amount",
                            "total_deduction_amount", "net_amount",
                            "attendance_days", "half_days", "absent_days",
                            "payment_status", "created_at",
                        ),
                    ),
                    "period_start": _json_value(payroll_runs[item.payroll_run_id].period_start)
                    if item.payroll_run_id in payroll_runs
                    else None,
                    "period_end": _json_value(payroll_runs[item.payroll_run_id].period_end)
                    if item.payroll_run_id in payroll_runs
                    else None,
                }
                for item in payroll_items
            ]

    return export


def anonymize_user(db: Session, user: User) -> dict[str, int]:
    """Erase direct identifiers while retaining financial and payroll records."""
    old_phone = user.phone
    identifiers = {
        value
        for value in (user.phone, user.email, user.name, user.google_id, user.apple_id)
        if value and len(value) >= 4
    }
    counts = {
        "documents_removed": 0,
        "sessions_revoked": 0,
        "audit_logs_scrubbed": 0,
    }

    worker_profile = db.scalar(select(WorkerProfile).where(WorkerProfile.user_id == user.id))
    if worker_profile:
        documents = db.scalars(
            select(WorkerDocument).where(
                (WorkerDocument.user_id == user.id)
                | (WorkerDocument.worker_profile_id == worker_profile.id)
            )
        ).all()
        for document in documents:
            if document.s3_key:
                delete_document_object(document.s3_key)
            db.delete(document)
            counts["documents_removed"] += 1

        attendance_rows = db.scalars(
            select(Attendance).where(Attendance.worker_profile_id == worker_profile.id)
        ).all()
        for attendance in attendance_rows:
            attendance.check_in_latitude = None
            attendance.check_in_longitude = None
            attendance.check_out_latitude = None
            attendance.check_out_longitude = None
            attendance.check_in_selfie_url = None
            attendance.check_out_selfie_url = None
            attendance.qr_code = None
            attendance.notes = None

        worker_profile.full_name = f"Deleted worker {worker_profile.id}"
        worker_profile.category = "Deleted"
        worker_profile.subcategory = None
        worker_profile.city = "Deleted"
        worker_profile.state = "Deleted"
        worker_profile.address = None
        worker_profile.date_of_birth = None
        worker_profile.skills = []
        worker_profile.experience_years = None
        worker_profile.experience_notes = None
        worker_profile.available_days = []
        worker_profile.available_shifts = []
        worker_profile.is_available = False
        worker_profile.verification_status = "rejected"
        worker_profile.photo_url = None
        worker_profile.upi_id_enc = None
        worker_profile.bank_account_enc = None
        worker_profile.bank_ifsc_enc = None
        worker_profile.bank_holder_name = None
        db.execute(
            delete(WorkerAvailability).where(
                WorkerAvailability.worker_profile_id == worker_profile.id
            )
        )
        db.execute(
            delete(WorkerInterest).where(
                WorkerInterest.worker_profile_id == worker_profile.id
            )
        )

    client_profile = db.scalar(select(ClientProfile).where(ClientProfile.user_id == user.id))
    if client_profile:
        client_profile.company_name = None
        client_profile.contact_name = f"Deleted client {client_profile.id}"
        client_profile.city = "Deleted"
        client_profile.state = "Deleted"
        client_profile.address = None
        client_profile.gst_number = None
        client_profile.industry = None
        client_profile.email = None
        client_profile.default_job_category = None
        client_profile.food_preference = False
        client_profile.accommodation_preference = False
        client_profile.standing_notes = None

    admin_profile = db.scalar(select(AdminProfile).where(AdminProfile.user_id == user.id))
    if admin_profile:
        admin_profile.full_name = f"Deleted admin {admin_profile.id}"
        admin_profile.department = None
        admin_profile.permission_group = "viewer"

    counts["sessions_revoked"] += db.execute(
        delete(RefreshToken).where(RefreshToken.user_id == user.id)
    ).rowcount or 0
    counts["sessions_revoked"] += db.execute(
        delete(PushToken).where(PushToken.user_id == user.id)
    ).rowcount or 0
    if old_phone:
        db.execute(delete(OtpCode).where(OtpCode.phone == old_phone))

    for privacy_request in db.scalars(
        select(PrivacyRequest).where(PrivacyRequest.user_id == user.id)
    ).all():
        privacy_request.reason = None

    if identifiers:
        for audit_log in db.scalars(select(AuditLog)).all():
            scrubbed, changed = _scrub_identifiers(audit_log.details, identifiers)
            if changed:
                audit_log.details = scrubbed
                counts["audit_logs_scrubbed"] += 1

    user.phone = None
    user.email = None
    user.name = None
    user.password_hash = None
    user.google_id = None
    user.apple_id = None
    user.is_active = False
    user.is_phone_verified = False
    user.is_email_verified = False
    user.onboarding_step = None
    user.last_login_at = None
    return counts
