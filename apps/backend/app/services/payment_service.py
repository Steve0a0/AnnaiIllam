from app.utils.time import utcnow

from app.core.payment_constants import ClientPaymentStatus, WorkerPayoutStatus
from app.models.client_payment import ClientPayment
from app.models.worker_payout import WorkerPayout


def build_client_gateway_payment(
    client_id: int,
    requirement_id: int,
    amount: int,
    payment_model: str,
    purpose: str,
    gateway_order_id: str,
    reference_note: str | None = None,
) -> ClientPayment:
    return ClientPayment(
        client_id=client_id,
        requirement_id=requirement_id,
        amount=amount,
        purpose=purpose,
        payment_model=payment_model,
        payment_mode="gateway",
        payment_status=ClientPaymentStatus.PENDING.value,
        gateway_order_id=gateway_order_id,
        reference_note=reference_note,
    )


def build_reference_client_payment(
    client_id: int,
    requirement_id: int,
    amount: int,
    payment_model: str,
    purpose: str,
    payment_mode: str,
    reference_note: str,
) -> ClientPayment:
    """Client submits a UTR/UPI ref after an out-of-app transfer. Status stays pending until admin verifies."""
    return ClientPayment(
        client_id=client_id,
        requirement_id=requirement_id,
        amount=amount,
        purpose=purpose,
        payment_model=payment_model,
        payment_mode=payment_mode,
        payment_status=ClientPaymentStatus.PENDING.value,
        reference_note=reference_note,
    )


def build_manual_client_payment(
    client_id: int,
    requirement_id: int,
    amount: int,
    payment_model: str,
    payment_mode: str,
    payment_status: str,
    purpose: str,
    recorded_by_user_id: int,
    reference_note: str | None = None,
) -> ClientPayment:
    return ClientPayment(
        client_id=client_id,
        requirement_id=requirement_id,
        amount=amount,
        purpose=purpose,
        payment_model=payment_model,
        payment_mode=payment_mode,
        payment_status=payment_status,
        reference_note=reference_note,
        recorded_by_user_id=recorded_by_user_id,
        paid_at=utcnow(),
    )


def mark_gateway_payment_success(
    payment,
    gateway_payment_id: str,
    gateway_signature: str | None,
) -> None:
    payment.gateway_payment_id = gateway_payment_id
    if gateway_signature:
        payment.gateway_signature = gateway_signature
    payment.payment_status = ClientPaymentStatus.PAID.value
    payment.paid_at = utcnow()


def build_worker_payout(
    payroll_item_id: int,
    worker_profile_id: int,
    amount: int,
    payout_mode: str,
    paid_by_user_id: int,
    transaction_reference: str | None = None,
    notes: str | None = None,
) -> WorkerPayout:
    return WorkerPayout(
        payroll_item_id=payroll_item_id,
        worker_profile_id=worker_profile_id,
        amount=amount,
        payout_mode=payout_mode,
        payout_status=WorkerPayoutStatus.PENDING.value,
        transaction_reference=transaction_reference,
        notes=notes,
        paid_by_user_id=paid_by_user_id,
    )
