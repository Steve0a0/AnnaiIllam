from app.core.complaint_constants import ComplaintStatus, ReplacementStatus
from app.models.complaint import Complaint
from app.models.replacement import Replacement


def build_complaint_entity(payload, raised_by_user_id: int) -> Complaint:
    return Complaint(
        requirement_id=payload.requirement_id,
        assignment_id=payload.assignment_id,
        raised_by_user_id=raised_by_user_id,
        complaint_type=payload.complaint_type,
        severity=payload.severity,
        description=payload.description,
        status=ComplaintStatus.OPEN.value,
    )


def build_replacement_entity(
    complaint_id: int,
    old_assignment_id: int,
    old_worker_profile_id: int,
    new_worker_profile_id: int,
    new_assignment_id: int,
    created_by_user_id: int,
    reason: str | None = None,
) -> Replacement:
    return Replacement(
        complaint_id=complaint_id,
        old_assignment_id=old_assignment_id,
        new_assignment_id=new_assignment_id,
        old_worker_profile_id=old_worker_profile_id,
        new_worker_profile_id=new_worker_profile_id,
        reason=reason,
        status=ReplacementStatus.COMPLETED.value,
        created_by_user_id=created_by_user_id,
    )
