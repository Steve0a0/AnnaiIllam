from enum import Enum


class PayrollRunStatus(str, Enum):
    DRAFT = "draft"
    GENERATED = "generated"
    APPROVED = "approved"
    PAID = "paid"
    LOCKED = "locked"


class PayrollItemPaymentStatus(str, Enum):
    PENDING = "pending"
    PARTIALLY_PAID = "partially_paid"
    PAID = "paid"


class DeductionType(str, Enum):
    FOOD = "food"
    ACCOMMODATION = "accommodation"
    ADVANCE = "advance"
    MANUAL = "manual"
