"""Transactional reconciliation for captured client gateway payments."""

from dataclasses import dataclass

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.payment_constants import ClientPaymentStatus
from app.models.client_payment import ClientPayment
from app.repositories.payment_repository import (
    get_client_payment_by_gateway_order_id_for_update,
    get_client_payment_by_gateway_payment_id_for_update,
)
from app.services.payment_service import mark_gateway_payment_success


class PaymentReconciliationError(ValueError):
    """Base class for a gateway event that cannot be reconciled."""


class PaymentOrderNotFoundError(PaymentReconciliationError):
    """The gateway order is not present in the local ledger."""


class GatewayPaymentConflictError(PaymentReconciliationError):
    """A gateway order or payment ID is already bound incompatibly."""


class InvalidCapturedPaymentError(PaymentReconciliationError):
    """Gateway facts do not match the authoritative local payment intent."""


@dataclass(frozen=True)
class PaymentReconciliationResult:
    payment: ClientPayment
    changed: bool


def _validate_captured_gateway_facts(
    *,
    payment: ClientPayment,
    gateway_payment_id: str,
    amount_paise: int,
    currency: str,
    status: str,
    captured: bool,
) -> None:
    if not gateway_payment_id:
        raise InvalidCapturedPaymentError("Gateway payment ID is missing")
    if isinstance(amount_paise, bool) or not isinstance(amount_paise, int):
        raise InvalidCapturedPaymentError("Gateway amount is invalid")
    if amount_paise != payment.amount * 100:
        raise InvalidCapturedPaymentError("Gateway amount does not match payment intent")
    if not isinstance(currency, str):
        raise InvalidCapturedPaymentError("Gateway currency is invalid")
    if currency.upper() != "INR":
        raise InvalidCapturedPaymentError("Gateway currency does not match payment intent")
    if not isinstance(status, str) or not isinstance(captured, bool):
        raise InvalidCapturedPaymentError("Gateway capture status is invalid")
    if status != "captured" or captured is not True:
        raise InvalidCapturedPaymentError("Gateway payment is not captured")


def reconcile_captured_gateway_payment(
    db: Session,
    *,
    gateway_order_id: str,
    gateway_payment_id: str,
    amount_paise: int,
    currency: str,
    status: str,
    captured: bool,
    checkout_signature: str | None = None,
) -> PaymentReconciliationResult:
    """Reconcile one captured gateway payment under database row locks.

    The order row is locked before its status is inspected. The global unique
    payment-ID constraint remains the final defence against concurrent attempts
    that target different orders.
    """
    try:
        with db.begin_nested():
            payment = get_client_payment_by_gateway_order_id_for_update(
                db,
                gateway_order_id,
            )
            if not payment:
                raise PaymentOrderNotFoundError("Payment order not found")

            _validate_captured_gateway_facts(
                payment=payment,
                gateway_payment_id=gateway_payment_id,
                amount_paise=amount_paise,
                currency=currency,
                status=status,
                captured=captured,
            )

            existing = get_client_payment_by_gateway_payment_id_for_update(
                db,
                gateway_payment_id,
            )
            if existing and existing.id != payment.id:
                raise GatewayPaymentConflictError(
                    "Gateway payment ID is already reconciled to another order"
                )

            if (
                payment.gateway_payment_id
                and payment.gateway_payment_id != gateway_payment_id
            ):
                raise GatewayPaymentConflictError(
                    "Gateway order is already reconciled to another payment"
                )

            if payment.gateway_payment_id and payment.payment_status in {
                ClientPaymentStatus.PAID.value,
                ClientPaymentStatus.REFUNDED.value,
            }:
                if checkout_signature and not payment.gateway_signature:
                    payment.gateway_signature = checkout_signature
                    db.flush()
                return PaymentReconciliationResult(payment=payment, changed=False)

            if payment.payment_status not in {
                ClientPaymentStatus.PENDING.value,
                ClientPaymentStatus.FAILED.value,
            }:
                raise GatewayPaymentConflictError(
                    f"Payment cannot be captured from status '{payment.payment_status}'"
                )

            mark_gateway_payment_success(
                payment,
                gateway_payment_id=gateway_payment_id,
                gateway_signature=checkout_signature,
            )
            db.flush()
            return PaymentReconciliationResult(payment=payment, changed=True)
    except IntegrityError as exc:
        raise GatewayPaymentConflictError(
            "Gateway payment ID was reconciled concurrently"
        ) from exc
