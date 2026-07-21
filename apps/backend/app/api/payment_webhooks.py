import json
import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.payment_constants import ClientPaymentStatus
from app.core.rate_limit import check_rate_limit
from app.db.deps import get_db
from app.repositories.payment_repository import get_client_payment_by_gateway_order_id
from app.schemas.payment import PaymentWebhookSchema
from app.services import razorpay_service
from app.services.payment_service import mark_gateway_payment_success
from app.services.payment_reconciliation_service import (
    GatewayPaymentConflictError,
    InvalidCapturedPaymentError,
    PaymentOrderNotFoundError,
    reconcile_captured_gateway_payment,
)
from app.services.webhook_security import verify_webhook_signature
from app.utils.audit import audit_event
from app.utils.response import success_response

router = APIRouter(prefix="/payments", tags=["Payment Webhooks"])
security_logger = logging.getLogger("annai_illam_security")


@router.post("/webhook")
async def payment_webhook(
    request: Request,
    db: Session = Depends(get_db),
):
    # Legacy synthetic payload retained only for local regression tests. Real
    # environments must use /webhook/razorpay so captured status, amount, and
    # currency come from Razorpay's signed payment entity.
    if settings.app_env != "local":
        raise HTTPException(status_code=404, detail="Not found")

    client_host = request.client.host if request.client else "unknown"
    check_rate_limit(f"payment_webhook_ip:{client_host}", limit=60, window_seconds=60)

    body = await request.body()
    try:
        payload = PaymentWebhookSchema.model_validate_json(body)
    except ValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.errors()) from exc

    check_rate_limit(f"payment_webhook_order:{payload.gateway_order_id}", limit=10, window_seconds=300)

    header_signature = request.headers.get(settings.payment_webhook_signature_header)
    if settings.app_env != "local":
        if not settings.payment_webhook_secret:
            security_logger.error("Payment webhook secret is not configured")
            raise HTTPException(status_code=503, detail="Webhook verification is not configured")
        if not header_signature or not verify_webhook_signature(body, header_signature, settings.payment_webhook_secret):
            security_logger.warning("Invalid payment webhook signature | order=%s", payload.gateway_order_id)
            audit_event("invalid_payment_webhook_signature", {"gateway_order_id": payload.gateway_order_id})
            raise HTTPException(status_code=401, detail="Invalid webhook signature")
    elif settings.payment_webhook_secret and header_signature:
        if not verify_webhook_signature(body, header_signature, settings.payment_webhook_secret):
            security_logger.warning("Invalid local payment webhook signature | order=%s", payload.gateway_order_id)
            audit_event("invalid_payment_webhook_signature", {"gateway_order_id": payload.gateway_order_id})
            raise HTTPException(status_code=401, detail="Invalid webhook signature")

    payment = get_client_payment_by_gateway_order_id(db, payload.gateway_order_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment order not found")

    if payment.payment_status == ClientPaymentStatus.PAID.value:
        audit_event(
            "duplicate_payment_webhook_ignored",
            {
                "payment_id": payment.id,
                "gateway_order_id": payment.gateway_order_id,
            },
        )
        return success_response(
            "Payment already recorded",
            {
                "payment_id": payment.id,
                "status": payment.payment_status,
            },
        )

    mark_gateway_payment_success(
        payment=payment,
        gateway_payment_id=payload.gateway_payment_id,
        gateway_signature=payload.gateway_signature,
    )

    db.commit()

    audit_event(
        "client_payment_marked_paid",
        {
            "payment_id": payment.id,
            "gateway_order_id": payment.gateway_order_id,
            "gateway_payment_id": payment.gateway_payment_id,
            "amount": payment.amount,
        },
    )

    return success_response(
        "Payment recorded successfully",
        {
            "payment_id": payment.id,
            "status": payment.payment_status,
        },
    )


@router.post("/webhook/razorpay")
async def razorpay_webhook(
    request: Request,
    db: Session = Depends(get_db),
):
    """Razorpay server-side webhook endpoint.

    Configure this URL in the Razorpay Dashboard under Settings → Webhooks.
    Enable the ``payment.captured`` event. Set a webhook secret and store it
    as ``PAYMENT_WEBHOOK_SECRET`` in the environment.

    Signature verification uses HMAC-SHA256 of the raw body bytes with the
    webhook secret, compared against the ``X-Razorpay-Signature`` header.
    """
    client_host = request.client.host if request.client else "unknown"
    check_rate_limit(f"razorpay_webhook_ip:{client_host}", limit=120, window_seconds=60)

    body = await request.body()

    signature = request.headers.get("x-razorpay-signature", "")
    if settings.app_env != "local":
        if not settings.payment_webhook_secret:
            security_logger.error("PAYMENT_WEBHOOK_SECRET is not configured — cannot verify Razorpay webhook")
            raise HTTPException(status_code=503, detail="Webhook verification is not configured")
        if not signature or not razorpay_service.verify_webhook_signature(body, signature):
            security_logger.warning("Invalid Razorpay webhook signature from %s", client_host)
            audit_event("invalid_razorpay_webhook_signature", {"client_host": client_host})
            raise HTTPException(status_code=401, detail="Invalid webhook signature")
    elif settings.payment_webhook_secret and signature:
        if not razorpay_service.verify_webhook_signature(body, signature):
            security_logger.warning("Invalid local Razorpay webhook signature from %s", client_host)
            raise HTTPException(status_code=401, detail="Invalid webhook signature")

    try:
        event_data = json.loads(body)
    except (json.JSONDecodeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail="Invalid JSON body") from exc

    event_type = event_data.get("event")
    if event_type != "payment.captured":
        # Acknowledge unknown events without processing — prevents Razorpay retries.
        return success_response(f"Event '{event_type}' acknowledged but not processed", {})

    try:
        payment_entity = event_data["payload"]["payment"]["entity"]
        razorpay_order_id = payment_entity["order_id"]
        razorpay_payment_id = payment_entity["id"]
    except (KeyError, TypeError) as exc:
        security_logger.error("Malformed Razorpay webhook payload: %s", exc)
        raise HTTPException(status_code=400, detail="Malformed webhook payload") from exc

    check_rate_limit(f"razorpay_webhook_order:{razorpay_order_id}", limit=10, window_seconds=300)

    payment = get_client_payment_by_gateway_order_id(db, razorpay_order_id)
    if not payment:
        # Could be a test event or a stale retry — log and acknowledge.
        security_logger.warning("Razorpay webhook: order not found | order_id=%s", razorpay_order_id)
        audit_event("razorpay_webhook_order_not_found", {"razorpay_order_id": razorpay_order_id})
        raise HTTPException(status_code=404, detail="Payment order not found")

    if payment.payment_status == ClientPaymentStatus.PAID.value:
        audit_event(
            "razorpay_webhook_duplicate_ignored",
            {"payment_id": payment.id, "razorpay_order_id": razorpay_order_id},
        )
        return success_response("Payment already recorded", {"payment_id": payment.id})

    try:
        result = reconcile_captured_gateway_payment(
            db,
            gateway_order_id=razorpay_order_id,
            gateway_payment_id=razorpay_payment_id,
            amount_paise=payment_entity.get("amount"),
            currency=payment_entity.get("currency"),
            status=payment_entity.get("status"),
            captured=payment_entity.get("captured"),
        )
    except PaymentOrderNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except (InvalidCapturedPaymentError, GatewayPaymentConflictError) as exc:
        db.rollback()
        event_id = request.headers.get("x-razorpay-event-id")
        security_logger.error(
            "Razorpay capture not reconciled | event_id=%s order_id=%s payment_id=%s reason=%s",
            event_id,
            razorpay_order_id,
            razorpay_payment_id,
            exc,
        )
        audit_event(
            "razorpay_payment_capture_not_reconciled",
            {
                "event_id": event_id,
                "razorpay_order_id": razorpay_order_id,
                "razorpay_payment_id": razorpay_payment_id,
                "reason": str(exc),
            },
        )
        return success_response(
            "Webhook acknowledged without changing the ledger",
            {"payment_id": payment.id, "status": payment.payment_status},
        )

    db.commit()

    if not result.changed:
        audit_event(
            "razorpay_webhook_duplicate_ignored",
            {
                "event_id": request.headers.get("x-razorpay-event-id"),
                "payment_id": result.payment.id,
                "razorpay_order_id": razorpay_order_id,
                "razorpay_payment_id": razorpay_payment_id,
            },
        )
        return success_response(
            "Payment already recorded",
            {
                "payment_id": result.payment.id,
                "status": result.payment.payment_status,
            },
        )

    audit_event(
        "razorpay_payment_captured",
        {
            "event_id": request.headers.get("x-razorpay-event-id"),
            "payment_id": result.payment.id,
            "razorpay_order_id": razorpay_order_id,
            "razorpay_payment_id": razorpay_payment_id,
            "amount": payment.amount,
        },
    )

    return success_response(
        "Payment captured successfully",
        {
            "payment_id": result.payment.id,
            "status": result.payment.payment_status,
        },
    )
