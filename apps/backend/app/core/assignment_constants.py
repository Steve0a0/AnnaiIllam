from enum import Enum


class AssignmentStatus(str, Enum):
    ASSIGNED = "assigned"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    REPLACED = "replaced"


# ---------------------------------------------------------------------------
# Assignment state machine
# ---------------------------------------------------------------------------

ASSIGNMENT_TRANSITIONS: dict[str, set[str]] = {
    AssignmentStatus.ASSIGNED.value: {
        AssignmentStatus.ACCEPTED.value,
        AssignmentStatus.DECLINED.value,
        AssignmentStatus.CANCELLED.value,
        AssignmentStatus.REPLACED.value,
    },
    AssignmentStatus.ACCEPTED.value: {
        AssignmentStatus.ACTIVE.value,
        AssignmentStatus.CANCELLED.value,
        AssignmentStatus.REPLACED.value,
    },
    AssignmentStatus.ACTIVE.value: {
        AssignmentStatus.COMPLETED.value,
        AssignmentStatus.CANCELLED.value,
        AssignmentStatus.REPLACED.value,
    },
    AssignmentStatus.DECLINED.value:  set(),
    AssignmentStatus.COMPLETED.value: set(),
    AssignmentStatus.CANCELLED.value: set(),
    AssignmentStatus.REPLACED.value:  set(),
}


def validate_assignment_transition(current: str, next_status: str) -> None:
    """Raise ValueError if the assignment status transition is not permitted."""
    allowed = ASSIGNMENT_TRANSITIONS.get(current, set())
    if next_status not in allowed:
        readable = sorted(allowed) if allowed else ["none — terminal state"]
        raise ValueError(
            f"Cannot transition assignment from '{current}' to '{next_status}'. "
            f"Allowed next statuses: {readable}"
        )
