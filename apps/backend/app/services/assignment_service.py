from app.core.assignment_constants import AssignmentStatus
from app.models.assignment import Assignment


def build_assignment_entity(payload, admin_user_id: int) -> Assignment:
    return Assignment(
        requirement_id=payload.requirement_id,
        worker_profile_id=payload.worker_profile_id,
        assigned_by_user_id=admin_user_id,
        status=AssignmentStatus.ASSIGNED.value,
        assigned_role=payload.assigned_role,
        assigned_shift=payload.assigned_shift,
        salary_amount=payload.salary_amount,
        notes=payload.notes,
    )
