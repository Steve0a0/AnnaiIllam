from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.payment_constants import (
    ClientPaymentStatus,
    PaymentModel,
    PaymentPurpose,
    WorkerPayoutStatus,
)
from app.utils.validators import strip_optional_text, strip_text


class CreateClientPaymentOrderSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    requirement_id: int
    # Deprecated compatibility hints. The server calculates the authoritative
    # amount and payment model from the approved quote.
    amount: int | None = Field(default=None, ge=1)
    payment_model: str | None = None
    reference_note: str | None = Field(default=None, max_length=1000)

    @field_validator("payment_model")
    @classmethod
    def validate_payment_model(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip().lower()
        if normalized not in {item.value for item in PaymentModel}:
            raise ValueError("Invalid payment model")
        return normalized

    @field_validator("reference_note")
    @classmethod
    def clean_reference_note(cls, value: str | None) -> str | None:
        return strip_optional_text(value)


class RecordManualClientPaymentSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    requirement_id: int
    amount: int = Field(ge=1)
    payment_model: str
    payment_mode: str = Field(min_length=2, max_length=50)
    payment_status: str
    purpose: str = PaymentPurpose.ADJUSTMENT.value
    reference_note: str | None = Field(default=None, max_length=1000)

    @field_validator("payment_model")
    @classmethod
    def validate_payment_model(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in {item.value for item in PaymentModel}:
            raise ValueError("Invalid payment model")
        return normalized

    @field_validator("payment_status")
    @classmethod
    def validate_payment_status(cls, value: str) -> str:
        normalized = value.strip().lower()
        allowed_statuses = {
            ClientPaymentStatus.PENDING.value,
            ClientPaymentStatus.PAID.value,
            ClientPaymentStatus.FAILED.value,
            ClientPaymentStatus.REFUNDED.value,
        }
        if normalized not in allowed_statuses:
            raise ValueError("Invalid payment status")
        return normalized

    @field_validator("purpose")
    @classmethod
    def validate_purpose(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in {item.value for item in PaymentPurpose}:
            raise ValueError("Invalid payment purpose")
        return normalized

    @field_validator("payment_mode")
    @classmethod
    def clean_payment_mode(cls, value: str) -> str:
        return strip_text(value).lower()

    @field_validator("reference_note")
    @classmethod
    def clean_reference_note(cls, value: str | None) -> str | None:
        return strip_optional_text(value)


class CreateGatewayRefundSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    amount: int = Field(ge=1)
    idempotency_key: str = Field(
        min_length=10,
        max_length=255,
        pattern=r"^[A-Za-z0-9_-]+$",
    )
    reason: str = Field(min_length=3, max_length=500)

    @field_validator("idempotency_key", "reason")
    @classmethod
    def clean_refund_fields(cls, value: str) -> str:
        return strip_text(value)


class SubmitReferencePaymentSchema(BaseModel):
    """Client submits a manual UTR / UPI reference after making an out-of-app transfer."""

    model_config = ConfigDict(extra="forbid")

    requirement_id: int
    # Deprecated compatibility hints; ignored by the server.
    amount: int | None = Field(default=None, ge=1)
    payment_model: str | None = None
    payment_mode: str = Field(min_length=2, max_length=50)
    reference_note: str = Field(min_length=3, max_length=500)

    @field_validator("payment_model")
    @classmethod
    def validate_payment_model(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip().lower()
        if normalized not in {item.value for item in PaymentModel}:
            raise ValueError("Invalid payment model")
        return normalized

    @field_validator("payment_mode")
    @classmethod
    def clean_payment_mode(cls, value: str) -> str:
        return strip_text(value).lower()

    @field_validator("reference_note")
    @classmethod
    def clean_reference_note(cls, value: str) -> str:
        return strip_text(value)


class PaymentWebhookSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    gateway_order_id: str = Field(min_length=3, max_length=255)
    gateway_payment_id: str = Field(min_length=3, max_length=255)
    gateway_signature: str = Field(min_length=3, max_length=255)

    @field_validator("gateway_order_id", "gateway_payment_id", "gateway_signature")
    @classmethod
    def clean_gateway_fields(cls, value: str) -> str:
        return strip_text(value)


class VerifyRazorpayPaymentSchema(BaseModel):
    """Body sent by the mobile app after Razorpay checkout succeeds.

    The three fields are passed verbatim from the Razorpay SDK's onSuccess callback.
    """

    model_config = ConfigDict(extra="forbid")

    razorpay_order_id: str = Field(min_length=3, max_length=255)
    razorpay_payment_id: str = Field(min_length=3, max_length=255)
    razorpay_signature: str = Field(min_length=3, max_length=255)

    @field_validator("razorpay_order_id", "razorpay_payment_id", "razorpay_signature")
    @classmethod
    def clean_fields(cls, value: str) -> str:
        return strip_text(value)


class CreateWorkerPayoutSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    payroll_item_id: int
    amount: int = Field(ge=0)
    payout_mode: str = Field(min_length=2, max_length=50)
    transaction_reference: str | None = Field(default=None, max_length=255)
    notes: str | None = Field(default=None, max_length=1000)

    @field_validator("payout_mode")
    @classmethod
    def clean_payout_mode(cls, value: str) -> str:
        return strip_text(value).lower()

    @field_validator("transaction_reference", "notes")
    @classmethod
    def clean_optional_text(cls, value: str | None) -> str | None:
        return strip_optional_text(value)


class UpdateWorkerPayoutStatusSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    payout_status: str

    @field_validator("payout_status")
    @classmethod
    def validate_payout_status(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in {item.value for item in WorkerPayoutStatus}:
            raise ValueError("Invalid payout status")
        return normalized


class MarkRunPaidSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    payout_mode: str = Field(min_length=2, max_length=50)

    @field_validator("payout_mode")
    @classmethod
    def clean_payout_mode(cls, value: str) -> str:
        return strip_text(value).lower()


class UpdateClientPaymentStatusSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    payment_status: str

    @field_validator("payment_status")
    @classmethod
    def validate_payment_status(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in {item.value for item in ClientPaymentStatus}:
            raise ValueError("Invalid payment status")
        return normalized
