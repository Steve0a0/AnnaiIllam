"""Authoritative client-receivable calculations.

All values in this module are integer whole INR rupees. Razorpay is the only
boundary that converts these values to paise.
"""

from dataclasses import dataclass
from typing import Iterable

from app.core.payment_constants import (
    ClientPaymentStatus,
    PaymentModel,
    PaymentPurpose,
)
from app.core.statuses import RequirementStatus

CLIENT_LEDGER_UNIT = "INR_WHOLE_RUPEES"


class PaymentLedgerError(ValueError):
    """Raised when a requested ledger operation violates an invariant."""


@dataclass(frozen=True)
class PaymentLedgerSnapshot:
    quote_total: int
    required_advance: int
    gross_paid: int
    refunded_amount: int
    total_paid: int
    outstanding_balance: int
    overpaid_amount: int
    advance_due: int


@dataclass(frozen=True)
class PaymentIntent:
    amount: int
    payment_model: str
    purpose: str


def calculate_quote_total(
    rate_per_worker: int,
    number_of_workers: int,
    duration_days: int,
) -> int:
    values = (rate_per_worker, number_of_workers, duration_days)
    if any(value <= 0 for value in values):
        raise PaymentLedgerError("Quote rate, worker count, and duration must be positive")
    return rate_per_worker * number_of_workers * duration_days


def _validated_quote_amounts(quote) -> tuple[int, int]:
    if quote is None:
        raise PaymentLedgerError("An approved quote is required before collecting payment")
    quote_total = int(quote.quoted_amount or 0)
    required_advance = int(quote.advance_amount or 0)
    if quote_total <= 0:
        raise PaymentLedgerError("Quote total must be positive")
    if required_advance < 0 or required_advance > quote_total:
        raise PaymentLedgerError("Required advance must be between zero and the quote total")
    return quote_total, required_advance


def build_payment_ledger(quote, payments: Iterable) -> PaymentLedgerSnapshot:
    quote_total, required_advance = _validated_quote_amounts(quote)
    gross_paid = 0
    refunded_amount = 0

    for payment in payments:
        amount = int(payment.amount or 0)
        if amount < 0:
            raise PaymentLedgerError("Payment amounts cannot be negative")
        purpose = getattr(payment, "purpose", PaymentPurpose.ADJUSTMENT.value)
        status = payment.payment_status

        if purpose == PaymentPurpose.REFUND.value:
            if status in {
                ClientPaymentStatus.PAID.value,
                ClientPaymentStatus.REFUNDED.value,
            }:
                refunded_amount += amount
            continue

        if status in {
            ClientPaymentStatus.PAID.value,
            ClientPaymentStatus.REFUNDED.value,
        }:
            gross_paid += amount
        if status == ClientPaymentStatus.REFUNDED.value:
            # Legacy rows represented a refund by changing the original status.
            refunded_amount += amount

    total_paid = max(0, gross_paid - refunded_amount)
    outstanding_balance = max(0, quote_total - total_paid)
    overpaid_amount = max(0, total_paid - quote_total)
    advance_due = max(0, required_advance - total_paid)
    return PaymentLedgerSnapshot(
        quote_total=quote_total,
        required_advance=required_advance,
        gross_paid=gross_paid,
        refunded_amount=refunded_amount,
        total_paid=total_paid,
        outstanding_balance=outstanding_balance,
        overpaid_amount=overpaid_amount,
        advance_due=advance_due,
    )


def derive_client_payment_intent(requirement, quote, payments: Iterable) -> PaymentIntent:
    if quote is None:
        raise PaymentLedgerError("An approved quote is required before collecting payment")
    if quote.payment_model == PaymentModel.CLIENT_PAYS_WORKER_DIRECTLY.value:
        raise PaymentLedgerError("This quote does not collect payment through Annai Illam")

    ledger = build_payment_ledger(quote, payments)
    if ledger.outstanding_balance == 0:
        raise PaymentLedgerError("This quote has no outstanding balance")

    allowed_states = {
        RequirementStatus.APPROVED.value,
        RequirementStatus.WORKERS_ASSIGNED.value,
        RequirementStatus.IN_PROGRESS.value,
        RequirementStatus.COMPLETED.value,
    }
    if requirement.status not in allowed_states:
        raise PaymentLedgerError(
            f"Payments are not allowed while the requirement is '{requirement.status}'"
        )

    if ledger.advance_due > 0:
        if requirement.status != RequirementStatus.APPROVED.value:
            raise PaymentLedgerError("The required advance must be paid before assignment")
        return PaymentIntent(
            amount=ledger.advance_due,
            payment_model=quote.payment_model,
            purpose=PaymentPurpose.ADVANCE.value,
        )

    if (
        ledger.required_advance > 0
        and requirement.status == RequirementStatus.APPROVED.value
    ):
        raise PaymentLedgerError(
            "The advance is already paid; assign workers before collecting the balance"
        )

    return PaymentIntent(
        amount=ledger.outstanding_balance,
        payment_model=quote.payment_model,
        purpose=PaymentPurpose.BALANCE.value,
    )


def validate_manual_payment(
    requirement,
    quote,
    payments: Iterable,
    *,
    amount: int,
    purpose: str,
) -> None:
    if amount <= 0:
        raise PaymentLedgerError("Payment amount must be positive")

    valid_states = {
        PaymentPurpose.ADVANCE.value: {RequirementStatus.APPROVED.value},
        PaymentPurpose.BALANCE.value: {
            RequirementStatus.APPROVED.value,
            RequirementStatus.WORKERS_ASSIGNED.value,
            RequirementStatus.IN_PROGRESS.value,
            RequirementStatus.COMPLETED.value,
        },
        PaymentPurpose.ADJUSTMENT.value: {
            RequirementStatus.APPROVED.value,
            RequirementStatus.WORKERS_ASSIGNED.value,
            RequirementStatus.IN_PROGRESS.value,
            RequirementStatus.COMPLETED.value,
        },
        PaymentPurpose.REFUND.value: {
            RequirementStatus.APPROVED.value,
            RequirementStatus.WORKERS_ASSIGNED.value,
            RequirementStatus.IN_PROGRESS.value,
            RequirementStatus.COMPLETED.value,
            RequirementStatus.CANCELLED.value,
        },
    }
    if requirement.status not in valid_states[purpose]:
        raise PaymentLedgerError(
            f"Payment purpose '{purpose}' is invalid while the requirement is "
            f"'{requirement.status}'"
        )

    ledger = build_payment_ledger(quote, payments)
    if purpose == PaymentPurpose.REFUND.value:
        if amount > ledger.total_paid:
            raise PaymentLedgerError("Refund amount cannot exceed the net amount paid")
    elif amount > ledger.outstanding_balance:
        raise PaymentLedgerError("Payment would exceed the outstanding balance")


def validate_gateway_refund(
    requirement,
    quote,
    payments: Iterable,
    *,
    source_payment,
    amount: int,
) -> None:
    """Validate a gateway refund and reserve against pending refund attempts."""
    payment_rows = list(payments)
    if source_payment.requirement_id != requirement.id:
        raise PaymentLedgerError("Refund payment does not belong to this requirement")
    if source_payment.purpose == PaymentPurpose.REFUND.value:
        raise PaymentLedgerError("A refund row cannot be refunded")
    if source_payment.payment_mode != "gateway" or not source_payment.gateway_payment_id:
        raise PaymentLedgerError("Only a captured gateway payment can be refunded through Razorpay")
    if source_payment.payment_status != ClientPaymentStatus.PAID.value:
        raise PaymentLedgerError("Only a paid gateway payment can be refunded")

    validate_manual_payment(
        requirement,
        quote,
        payment_rows,
        amount=amount,
        purpose=PaymentPurpose.REFUND.value,
    )

    ledger = build_payment_ledger(quote, payment_rows)
    pending_refund_reservations = sum(
        int(payment.amount or 0)
        for payment in payment_rows
        if getattr(payment, "purpose", None) == PaymentPurpose.REFUND.value
        and payment.payment_status == ClientPaymentStatus.PENDING.value
    )
    if amount > ledger.total_paid - pending_refund_reservations:
        raise PaymentLedgerError(
            "Refund amount cannot exceed the unreserved refundable balance"
        )

    reserved_for_source = sum(
        int(payment.amount or 0)
        for payment in payment_rows
        if getattr(payment, "parent_payment_id", None) == source_payment.id
        and getattr(payment, "purpose", None) == PaymentPurpose.REFUND.value
        and payment.payment_status
        in {
            ClientPaymentStatus.PENDING.value,
            ClientPaymentStatus.PAID.value,
            ClientPaymentStatus.REFUNDED.value,
        }
    )
    if amount > int(source_payment.amount or 0) - reserved_for_source:
        raise PaymentLedgerError(
            "Refund amount cannot exceed this payment's remaining refundable balance"
        )


def has_required_advance(quote, payments: Iterable) -> bool:
    return build_payment_ledger(quote, payments).advance_due == 0
