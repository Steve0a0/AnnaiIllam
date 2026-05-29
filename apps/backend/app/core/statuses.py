from enum import Enum


class RequirementStatus(str, Enum):
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    QUOTED = "quoted"
    APPROVED = "approved"
    REJECTED = "rejected"
    WORKERS_ASSIGNED = "workers_assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class QuoteStatus(str, Enum):
    DRAFT = "draft"
    SENT = "sent"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


# ---------------------------------------------------------------------------
# Requirement state machine
# ---------------------------------------------------------------------------

REQUIREMENT_TRANSITIONS: dict[str, set[str]] = {
    RequirementStatus.SUBMITTED.value: {
        RequirementStatus.UNDER_REVIEW.value,
        RequirementStatus.REJECTED.value,
        RequirementStatus.CANCELLED.value,
    },
    RequirementStatus.UNDER_REVIEW.value: {
        RequirementStatus.QUOTED.value,
        RequirementStatus.REJECTED.value,
        RequirementStatus.CANCELLED.value,
    },
    RequirementStatus.QUOTED.value: {
        RequirementStatus.APPROVED.value,
        RequirementStatus.REJECTED.value,
        RequirementStatus.UNDER_REVIEW.value,   # quote rejected by client → admin can revise
        RequirementStatus.CANCELLED.value,
    },
    RequirementStatus.APPROVED.value: {
        RequirementStatus.WORKERS_ASSIGNED.value,
        RequirementStatus.CANCELLED.value,
    },
    RequirementStatus.WORKERS_ASSIGNED.value: {
        RequirementStatus.IN_PROGRESS.value,
        RequirementStatus.APPROVED.value,   # all workers declined → revert
        RequirementStatus.CANCELLED.value,
    },
    RequirementStatus.IN_PROGRESS.value: {
        RequirementStatus.COMPLETED.value,
        RequirementStatus.CANCELLED.value,
    },
    RequirementStatus.COMPLETED.value: set(),
    RequirementStatus.REJECTED.value: set(),
    RequirementStatus.CANCELLED.value: set(),
}


def validate_requirement_transition(current: str, next_status: str) -> None:
    """Raise ValueError if the status transition is not permitted."""
    allowed = REQUIREMENT_TRANSITIONS.get(current, set())
    if next_status not in allowed:
        readable = sorted(allowed) if allowed else ["none — terminal state"]
        raise ValueError(
            f"Cannot transition requirement from '{current}' to '{next_status}'. "
            f"Allowed next statuses: {readable}"
        )
