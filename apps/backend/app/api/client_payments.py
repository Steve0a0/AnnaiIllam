import logging

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.api.dependencies.roles import require_role
from app.core.config import settings
from app.core.payment_constants import ClientPaymentStatus, PaymentModel
from app.core.roles import UserRole
from app.db.deps import get_db
from app.models.user import User
from app.repositories.payment_repository import (
    create_client_payment,
    get_client_payment_by_id,
    get_client_payment_by_gateway_order_id,
    get_client_payments_by_requirement_id,
)
from app.repositories.profile_repository import get_client_profile_by_user_id
from app.repositories.requirement_repository import get_requirement_by_id
from app.repositories.quote_repository import get_quote_by_requirement_id
from app.core.statuses import RequirementStatus
from app.schemas.payment import CreateClientPaymentOrderSchema, VerifyRazorpayPaymentSchema, SubmitReferencePaymentSchema
from app.services.notification_service import queue_notification
from app.services.payment_service import build_client_gateway_payment, build_reference_client_payment, mark_gateway_payment_success
from app.services import razorpay_service
from app.utils.audit import audit_event
from app.utils.response import success_response

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/client/payments", tags=["Client Payments"])


def _escape_pdf_text(value: str) -> str:
    return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _build_receipt_pdf(lines: list[str]) -> bytes:
    text_commands = ["BT", "/F1 14 Tf", "50 780 Td"]
    for index, line in enumerate(lines):
        if index > 0:
            text_commands.append("0 -22 Td")
        text_commands.append(f"({_escape_pdf_text(line)}) Tj")
    text_commands.append("ET")
    stream = "\n".join(text_commands).encode("latin-1", errors="replace")

    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n" + stream + b"\nendstream",
    ]

    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for number, obj in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{number} 0 obj\n".encode("ascii"))
        pdf.extend(obj)
        pdf.extend(b"\nendobj\n")

    xref_offset = len(pdf)
    pdf.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    pdf.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    pdf.extend(
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode(
            "ascii"
        )
    )
    return bytes(pdf)


def _receipt_lines(payment, requirement) -> list[str]:
    return [
        "Annai Illam Payment Receipt",
        f"Receipt ID: AI-RCPT-{payment.id}",
        f"Requirement ID: {payment.requirement_id}",
        f"Requirement: {requirement.category if requirement else 'Requirement'}",
        f"Amount: INR {payment.amount}",
        f"Payment model: {payment.payment_model}",
        f"Payment mode: {payment.payment_mode}",
        f"Status: {payment.payment_status}",
        f"Gateway order: {payment.gateway_order_id or '-'}",
        f"Gateway payment: {payment.gateway_payment_id or '-'}",
        f"Paid at: {payment.paid_at.isoformat() if payment.paid_at else '-'}",
        f"Created at: {payment.created_at.isoformat()}",
    ]


@router.post("/create-order")
def create_client_payment_order(
    payload: CreateClientPaymentOrderSchema,
    current_user: User = Depends(require_role(UserRole.CLIENT.value)),
    db: Session = Depends(get_db),
):
    client_profile = get_client_profile_by_user_id(db, current_user.id)
    if not client_profile:
        raise HTTPException(status_code=404, detail="Client profile not found")

    requirement = get_requirement_by_id(db, payload.requirement_id)
    if not requirement or requirement.client_id != client_profile.id:
        raise HTTPException(status_code=404, detail="Requirement not found")

    allowed_models = {item.value for item in PaymentModel}
    if payload.payment_model not in allowed_models:
        raise HTTPException(status_code=400, detail="Invalid payment model")

    receipt = f"pay_{payload.requirement_id}_{client_profile.id}"
    notes = {
        "requirement_id": str(payload.requirement_id),
        "client_user_id": str(current_user.id),
    }
    try:
        rz_order = razorpay_service.create_order(
            amount_rupees=payload.amount,
            receipt=receipt,
            notes=notes,
        )
    except Exception as exc:
        logger.exception("Razorpay order creation failed: %s", exc)
        raise HTTPException(
            status_code=502,
            detail="Payment gateway unavailable. Please try again.",
        ) from exc

    gateway_order_id = rz_order["id"]  # e.g. "order_XXXXXXXXXXXXXXXX"

    payment = build_client_gateway_payment(
        client_id=client_profile.id,
        requirement_id=payload.requirement_id,
        amount=payload.amount,
        payment_model=payload.payment_model,
        gateway_order_id=gateway_order_id,
        reference_note=payload.reference_note,
    )
    create_client_payment(db, payment)
    db.commit()
    db.refresh(payment)

    audit_event(
        "client_payment_order_created",
        {
            "payment_id": payment.id,
            "requirement_id": payment.requirement_id,
            "client_user_id": current_user.id,
            "amount": payment.amount,
        },
    )
    queue_notification(
        channel="sms",
        recipient=current_user.phone,
        template="payment_order_created",
        context={
            "payment_id": payment.id,
            "requirement_id": payment.requirement_id,
            "amount": payment.amount,
            "status": payment.payment_status,
        },
    )

    return success_response(
        "Payment order created successfully",
        {
            "payment_id": payment.id,
            "gateway_order_id": payment.gateway_order_id,
            "amount": payment.amount,
            "amount_paise": payment.amount * 100,
            "currency": "INR",
            "razorpay_key_id": settings.razorpay_key_id,
            "status": payment.payment_status,
        },
    )


@router.get("/requirement/{requirement_id}")
def list_client_payments_for_requirement(
    requirement_id: int,
    current_user: User = Depends(require_role(UserRole.CLIENT.value)),
    db: Session = Depends(get_db),
):
    client_profile = get_client_profile_by_user_id(db, current_user.id)
    if not client_profile:
        raise HTTPException(status_code=404, detail="Client profile not found")

    requirement = get_requirement_by_id(db, requirement_id)
    if not requirement or requirement.client_id != client_profile.id:
        raise HTTPException(status_code=404, detail="Requirement not found")

    payments = get_client_payments_by_requirement_id(db, requirement_id)

    data = [
        {
            "id": item.id,
            "amount": item.amount,
            "payment_model": item.payment_model,
            "payment_mode": item.payment_mode,
            "payment_status": item.payment_status,
            "gateway_order_id": item.gateway_order_id,
            "gateway_payment_id": item.gateway_payment_id,
            "reference_note": item.reference_note,
            "paid_at": item.paid_at.isoformat() if item.paid_at else None,
            "created_at": item.created_at.isoformat(),
        }
        for item in payments
    ]

    return success_response("Client payments fetched successfully", data)


@router.get("/{payment_id}/receipt")
def download_client_payment_receipt(
    payment_id: int,
    current_user: User = Depends(require_role(UserRole.CLIENT.value)),
    db: Session = Depends(get_db),
):
    client_profile = get_client_profile_by_user_id(db, current_user.id)
    if not client_profile:
        raise HTTPException(status_code=404, detail="Client profile not found")

    payment = get_client_payment_by_id(db, payment_id)
    if not payment or payment.client_id != client_profile.id:
        raise HTTPException(status_code=404, detail="Payment not found")

    requirement = get_requirement_by_id(db, payment.requirement_id)
    receipt = "\n".join(_receipt_lines(payment, requirement))

    return Response(
        content=receipt,
        media_type="text/plain",
        headers={"Content-Disposition": f'attachment; filename="annai-illam-receipt-{payment.id}.txt"'},
    )


@router.get("/{payment_id}/receipt.pdf")
def download_client_payment_receipt_pdf(
    payment_id: int,
    current_user: User = Depends(require_role(UserRole.CLIENT.value)),
    db: Session = Depends(get_db),
):
    client_profile = get_client_profile_by_user_id(db, current_user.id)
    if not client_profile:
        raise HTTPException(status_code=404, detail="Client profile not found")

    payment = get_client_payment_by_id(db, payment_id)
    if not payment or payment.client_id != client_profile.id:
        raise HTTPException(status_code=404, detail="Payment not found")

    requirement = get_requirement_by_id(db, payment.requirement_id)
    return Response(
        content=_build_receipt_pdf(_receipt_lines(payment, requirement)),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="annai-illam-receipt-{payment.id}.pdf"'},
    )


@router.post("/submit-reference")
def submit_reference_payment(
    payload: SubmitReferencePaymentSchema,
    current_user: User = Depends(require_role(UserRole.CLIENT.value)),
    db: Session = Depends(get_db),
):
    """Client records an out-of-app UPI/NEFT transfer by submitting the transaction reference.
    Creates a pending payment that admin can verify and mark as paid."""
    client_profile = get_client_profile_by_user_id(db, current_user.id)
    if not client_profile:
        raise HTTPException(status_code=404, detail="Client profile not found")

    requirement = get_requirement_by_id(db, payload.requirement_id)
    if not requirement or requirement.client_id != client_profile.id:
        raise HTTPException(status_code=404, detail="Requirement not found")

    payment = build_reference_client_payment(
        client_id=client_profile.id,
        requirement_id=payload.requirement_id,
        amount=payload.amount,
        payment_model=payload.payment_model,
        payment_mode=payload.payment_mode,
        reference_note=payload.reference_note,
    )
    create_client_payment(db, payment)
    db.commit()
    db.refresh(payment)

    audit_event(
        "client_payment_reference_submitted",
        {
            "payment_id": payment.id,
            "requirement_id": payment.requirement_id,
            "client_user_id": current_user.id,
            "amount": payment.amount,
            "payment_mode": payment.payment_mode,
        },
    )
    queue_notification(
        channel="sms",
        recipient=current_user.phone,
        template="payment_reference_submitted",
        context={
            "payment_id": payment.id,
            "requirement_id": payment.requirement_id,
            "amount": payment.amount,
            "reference": payload.reference_note,
        },
    )

    return success_response(
        "Payment reference submitted. Admin will verify and confirm within a few hours.",
        {
            "payment_id": payment.id,
            "requirement_id": payment.requirement_id,
            "amount": payment.amount,
            "payment_mode": payment.payment_mode,
            "payment_status": payment.payment_status,
            "reference_note": payment.reference_note,
        },
    )


@router.post("/verify")
def verify_razorpay_payment(
    payload: VerifyRazorpayPaymentSchema,
    current_user: User = Depends(require_role(UserRole.CLIENT.value)),
    db: Session = Depends(get_db),
):
    """Verify a completed Razorpay checkout and mark the payment as PAID.

    Call this endpoint from the mobile app's Razorpay ``onSuccess`` callback.
    The three fields (``razorpay_order_id``, ``razorpay_payment_id``,
    ``razorpay_signature``) are passed verbatim from the SDK callback.
    """
    if not razorpay_service.verify_payment_signature(
        payload.razorpay_order_id,
        payload.razorpay_payment_id,
        payload.razorpay_signature,
    ):
        raise HTTPException(status_code=400, detail="Invalid payment signature")

    # Look up the payment by gateway_order_id so we only mark payments that
    # belong to the authenticated client.
    client_profile = get_client_profile_by_user_id(db, current_user.id)
    if not client_profile:
        raise HTTPException(status_code=404, detail="Client profile not found")

    payment = get_client_payment_by_gateway_order_id(db, payload.razorpay_order_id)
    if not payment or payment.client_id != client_profile.id:
        raise HTTPException(status_code=404, detail="Payment not found")

    if payment.payment_status == ClientPaymentStatus.PAID.value:
        # Idempotent — already processed (e.g. also captured via webhook)
        return success_response("Payment already verified", {"payment_id": payment.id})

    mark_gateway_payment_success(
        payment,
        gateway_payment_id=payload.razorpay_payment_id,
        gateway_signature=payload.razorpay_signature,
    )

    # Auto-complete requirement for full (non-advance) gateway payments.
    # Advance payments still need admin confirmation before deployment.
    requirement = get_requirement_by_id(db, payment.requirement_id)
    is_advance = False
    if requirement:
        quote = get_quote_by_requirement_id(db, requirement.id)
        if quote and quote.advance_amount:
            # This payment is an advance only if no prior paid advance exists yet.
            # If a paid payment already exists for this requirement, the current
            # payment is the remaining balance — even if the amounts match.
            prior_payments = get_client_payments_by_requirement_id(db, requirement.id)
            already_has_paid_advance = any(
                p.id != payment.id
                and p.payment_status == ClientPaymentStatus.PAID.value
                for p in prior_payments
            )
            if not already_has_paid_advance and payment.amount <= quote.advance_amount:
                is_advance = True
        if not is_advance and requirement.status not in (
            RequirementStatus.COMPLETED.value,
            RequirementStatus.CANCELLED.value,
        ):
            requirement.status = RequirementStatus.COMPLETED.value

    db.commit()

    audit_event(
        "client_payment_verified",
        {
            "payment_id": payment.id,
            "razorpay_payment_id": payload.razorpay_payment_id,
            "client_user_id": current_user.id,
            "auto_completed": not is_advance,
        },
    )
    queue_notification(
        channel="sms",
        recipient=current_user.phone,
        template="payment_confirmed",
        context={
            "payment_id": payment.id,
            "amount": payment.amount,
        },
    )

    return success_response("Payment verified successfully", {"payment_id": payment.id})
