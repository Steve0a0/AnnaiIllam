from enum import Enum


class AssignmentStatus(str, Enum):
    ASSIGNED = "assigned"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    REPLACED = "replaced"
