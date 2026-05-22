from enum import Enum


class WorkerDocumentType(str, Enum):
    ID_PROOF = "id_proof"
    ADDRESS_PROOF = "address_proof"
    BANK_PROOF = "bank_proof"
    EXPERIENCE_PROOF = "experience_proof"
    OTHER = "other"


class VerificationStatus(str, Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"
