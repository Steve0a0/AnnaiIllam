from enum import Enum


class AttendanceStatus(str, Enum):
    PRESENT = "present"
    ABSENT = "absent"
    HALF_DAY = "half_day"
    LATE = "late"
    APPROVED = "approved"
    CORRECTED = "corrected"
    NO_SHOW = "no_show"
    EXCUSED = "excused"


class AttendanceApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
