from enum import Enum


class ComplaintStatus(str, Enum):
    OPEN = "open"
    UNDER_REVIEW = "under_review"
    RESOLVED = "resolved"
    CLOSED = "closed"


class ComplaintSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class ComplaintType(str, Enum):
    ABSENT = "absent"
    BEHAVIOR = "behavior"
    PERFORMANCE = "performance"
    PAYMENT = "payment"
    REPLACEMENT_REQUEST = "replacement_request"
    OTHER = "other"


class ReplacementStatus(str, Enum):
    CREATED = "created"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
