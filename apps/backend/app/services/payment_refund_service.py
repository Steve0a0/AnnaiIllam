"""Durable reconciliation for Razorpay refund API responses and webhooks."""

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.payment_constants import ClientPaymentStatus, PaymentPurpose
from app.models.client_payment import ClientPayment
from app.utils.time import utcnow


class RefundReconciliationError(ValueError):
    """Raised when Razorpay refund facts conflict with the local refund intent."""


class RefundIntentNotFoundError(RefundReconciliationError):
    """Raised when a refund event cannot be tied to a local refund intent."""


@dataclass(frozen=True)
class RefundReconciliationResult:
    payment: ClientPayment
    changed: bool


def _find_refund_for_update(
    db: Session,
    refund_entity: dict,
    refund_payment_id: int | None,
) -> ClientPayment:
    if refund_payment_id is not None:
        payment = db.execute(
            select(ClientPayment)
            .where(ClientPayment.id == refund_payment_id)
            .with_for_update()
        ).scalar_one_or_none()
    else:
        refund_id = refund_entity.get("id")
        payment = None
        if refund_id:
            payment = db.execute(
                select(ClientPayment)
                .where(ClientPayment.gateway_refund_id == refund_id)
                .with_for_update()
            ).scalar_one_or_none()

        if payment is None:
            notes = refund_entity.get("notes") or {}
            local_id = notes.get("refund_payment_id")
            if local_id is not None:
                try:
                    local_id = int(local_id)
                except (TypeError, ValueError):
                    local_id = None
            if local_id is not None:
                payment = db.execute(
                    select(ClientPayment)
                    .where(ClientPayment.id == local_id)
                    .with_for_update()
                ).scalar_one_or_none()

    if payment is None or payment.purpose != PaymentPurpose.REFUND.value:
        raise RefundIntentNotFoundError("Refund intent not found")
    return payment


def reconcile_gateway_refund(
    db: Session,
    refund_entity: dict,
    *,
    refund_payment_id: int | None = None,
) -> RefundReconciliationResult:
    """Apply authoritative Razorpay refund facts to one ledger refund row."""
    payment = _find_refund_for_update(db, refund_entity, refund_payment_id)
    source_payment = db.execute(
        select(ClientPayment)
        .where(ClientPayment.id == payment.parent_payment_id)
        .with_for_update()
    ).scalar_one_or_none()
    if source_payment is None or not source_payment.gateway_payment_id:
        raise RefundReconciliationError("Refund source payment not found")

    refund_id = refund_entity.get("id")
    gateway_payment_id = refund_entity.get("payment_id")
    currency = refund_entity.get("currency")
    amount_paise = refund_entity.get("amount")
    gateway_status = refund_entity.get("status")

    if not isinstance(refund_id, str) or not refund_id:
        raise RefundReconciliationError("Razorpay refund ID is missing")
    if gateway_payment_id != source_payment.gateway_payment_id:
        raise RefundReconciliationError("Razorpay refund payment ID does not match")
    if currency != "INR":
        raise RefundReconciliationError("Razorpay refund currency must be INR")
    if not isinstance(amount_paise, int) or amount_paise != payment.amount * 100:
        raise RefundReconciliationError("Razorpay refund amount does not match")
    if gateway_status not in {"pending", "processed", "failed"}:
        raise RefundReconciliationError("Razorpay refund status is invalid")
    if payment.gateway_refund_id and payment.gateway_refund_id != refund_id:
        raise RefundReconciliationError("Refund intent is already linked to another Razorpay refund")

    previous = (
        payment.gateway_refund_id,
        payment.gateway_refund_status,
        payment.payment_status,
    )
    payment.gateway_refund_id = refund_id
    payment.gateway_refund_status = gateway_status

    if gateway_status == "processed":
        payment.payment_status = ClientPaymentStatus.PAID.value
        payment.paid_at = payment.paid_at or utcnow()
    elif gateway_status == "failed" and payment.payment_status != ClientPaymentStatus.PAID.value:
        payment.payment_status = ClientPaymentStatus.FAILED.value
    elif payment.payment_status != ClientPaymentStatus.PAID.value:
        payment.payment_status = ClientPaymentStatus.PENDING.value

    current = (
        payment.gateway_refund_id,
        payment.gateway_refund_status,
        payment.payment_status,
    )
    return RefundReconciliationResult(payment=payment, changed=current != previous)
