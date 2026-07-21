from enum import Enum


class PaymentModel(str, Enum):
    CLIENT_PAYS_COMPANY = "client_pays_company"
    CLIENT_PAYS_WORKER_DIRECTLY = "client_pays_worker_directly"
    MIXED = "mixed"


class ClientPaymentStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"


class PaymentPurpose(str, Enum):
    ADVANCE = "advance"
    BALANCE = "balance"
    ADJUSTMENT = "adjustment"
    REFUND = "refund"


class WorkerPayoutStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    PAID = "paid"
    FAILED = "failed"
