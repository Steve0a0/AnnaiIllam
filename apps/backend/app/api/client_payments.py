import logging

import httpx
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.api.dependencies.roles import require_role
from app.core.config import settings
from app.core.payment_constants import ClientPaymentStatus
from app.core.roles import UserRole
from app.db.deps import get_db
from app.models.user import User
from app.repositories.payment_repository import (
    create_client_payment,
    get_client_payment_by_id,
    get_client_payment_by_gateway_order_id,
    get_client_payments_by_client_id,
    get_client_payments_by_requirement_id,
)
from app.repositories.profile_repository import get_client_profile_by_user_id
from app.repositories.requirement_repository import get_requirement_by_id
from app.repositories.quote_repository import get_quote_by_requirement_id
from app.schemas.payment import CreateClientPaymentOrderSchema, VerifyRazorpayPaymentSchema, SubmitReferencePaymentSchema
from app.services.notification_service import queue_notification
from app.services.payment_service import (
    build_client_gateway_payment,
    build_reference_client_payment,
)
from app.services.payment_ledger_service import (
    PaymentLedgerError,
    derive_client_payment_intent,
)
from app.services.payment_reconciliation_service import (
    GatewayPaymentConflictError,
    InvalidCapturedPaymentError,
    PaymentOrderNotFoundError,
    reconcile_captured_gateway_payment,
)
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

    quote = get_quote_by_requirement_id(db, requirement.id)
    payments = get_client_payments_by_requirement_id(db, requirement.id)
    try:
        intent = derive_client_payment_intent(requirement, quote, payments)
    except PaymentLedgerError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    matching_pending = next(
        (
            payment
            for payment in payments
            if payment.payment_status == ClientPaymentStatus.PENDING.value
            and payment.payment_mode == "gateway"
            and payment.gateway_order_id
            and payment.amount == intent.amount
            and payment.purpose == intent.purpose
        ),
        None,
    )
    if matching_pending:
        return success_response(
            "Existing payment order fetched successfully",
            {
                "payment_id": matching_pending.id,
                "gateway_order_id": matching_pending.gateway_order_id,
                "amount": matching_pending.amount,
                "amount_paise": matching_pending.amount * 100,
                "currency": "INR",
                "razorpay_key_id": settings.razorpay_key_id,
                "status": matching_pending.payment_status,
                "purpose": matching_pending.purpose,
            },
        )
    if any(
        payment.payment_status == ClientPaymentStatus.PENDING.value
        and payment.amount == intent.amount
        and payment.purpose == intent.purpose
        for payment in payments
    ):
        raise HTTPException(
            status_code=409,
            detail="A matching payment is already pending verification",
        )

    receipt = f"pay_{payload.requirement_id}_{client_profile.id}"
    notes = {
        "requirement_id": str(payload.requirement_id),
        "client_user_id": str(current_user.id),
    }
    try:
        rz_order = razorpay_service.create_order(
            amount_rupees=intent.amount,
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
        amount=intent.amount,
        payment_model=intent.payment_model,
        purpose=intent.purpose,
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
            "purpose": payment.purpose,
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
            "purpose": payment.purpose,
        },
    )


@router.get("")
def list_all_my_payments(
    current_user: User = Depends(require_role(UserRole.CLIENT.value)),
    db: Session = Depends(get_db),
):
    """Return all payments for the current client, enriched with requirement info."""
    from sqlalchemy import select as _sel
    from app.models.requirement import Requirement

    client_profile = get_client_profile_by_user_id(db, current_user.id)
    if not client_profile:
        raise HTTPException(status_code=404, detail="Client profile not found")

    payments = get_client_payments_by_client_id(db, client_profile.id)

    req_ids = {p.requirement_id for p in payments}
    reqs: dict = {}
    if req_ids:
        for r in db.execute(
            _sel(Requirement).where(Requirement.id.in_(req_ids))
        ).scalars().all():
            reqs[r.id] = r

    data = []
    for p in payments:
        req = reqs.get(p.requirement_id)
        data.append({
            "id": p.id,
            "requirement_id": p.requirement_id,
            "job_name": req.category if req else None,
            "location": f"{req.city}, {req.state}" if req else None,
            "duration_days": req.duration_days if req else None,
            "amount": p.amount,
            "purpose": p.purpose,
            "payment_model": p.payment_model,
            "payment_mode": p.payment_mode,
            "payment_status": p.payment_status,
            "reference_note": p.reference_note,
            "paid_at": p.paid_at.isoformat() if p.paid_at else None,
            "created_at": p.created_at.isoformat(),
        })

    return success_response("Payments fetched successfully", data)


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
            "purpose": item.purpose,
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


@router.get("/{payment_id}/invoice.html")
def view_client_payment_invoice(
    payment_id: int,
    current_user: User = Depends(require_role(UserRole.CLIENT.value)),
    db: Session = Depends(get_db),
):
    """Return a styled HTML invoice for a confirmed payment (for in-app WebView)."""
    from app.services.email_service import _build_invoice_html, _format_date

    client_profile = get_client_profile_by_user_id(db, current_user.id)
    if not client_profile:
        raise HTTPException(status_code=404, detail="Client profile not found")

    payment = get_client_payment_by_id(db, payment_id)
    if not payment or payment.client_id != client_profile.id:
        raise HTTPException(status_code=404, detail="Payment not found")

    if payment.payment_status != "paid":
        raise HTTPException(status_code=404, detail="Invoice only available for confirmed payments")

    requirement = get_requirement_by_id(db, payment.requirement_id)
    if not requirement:
        raise HTTPException(status_code=404, detail="Requirement not found")

    client_name = (
        getattr(client_profile, "contact_name", None)
        or getattr(client_profile, "company_name", None)
        or current_user.phone
    )
    payment_date = (
        payment.paid_at.strftime("%d %b %Y")
        if payment.paid_at
        else payment.created_at.strftime("%d %b %Y")
    )
    start_date_str = _format_date(
        requirement.start_date.isoformat() if requirement.start_date else ""
    )

    html = _build_invoice_html(
        invoice_number=f"INV-{payment.id:05d}",
        payment_date=payment_date,
        client_name=client_name,
        requirement_category=requirement.category or "Service",
        requirement_subcategory=getattr(requirement, "subcategory", None),
        work_location=requirement.work_location or "",
        city=requirement.city or "",
        state=requirement.state or "",
        start_date=start_date_str,
        duration_days=requirement.duration_days,
        payment_model=payment.payment_model,
        amount=payment.amount,
        reference_note=payment.reference_note,
    )

    return Response(content=html, media_type="text/html")


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

    quote = get_quote_by_requirement_id(db, requirement.id)
    payments = get_client_payments_by_requirement_id(db, requirement.id)
    if any(
        payment.reference_note == payload.reference_note
        and payment.payment_mode == payload.payment_mode
        for payment in payments
    ):
        raise HTTPException(status_code=409, detail="This payment reference was already submitted")
    try:
        intent = derive_client_payment_intent(requirement, quote, payments)
    except PaymentLedgerError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if any(
        payment.payment_status == ClientPaymentStatus.PENDING.value
        and payment.amount == intent.amount
        and payment.purpose == intent.purpose
        for payment in payments
    ):
        raise HTTPException(
            status_code=409,
            detail="A matching payment is already pending verification",
        )

    payment = build_reference_client_payment(
        client_id=client_profile.id,
        requirement_id=payload.requirement_id,
        amount=intent.amount,
        payment_model=intent.payment_model,
        purpose=intent.purpose,
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
            "purpose": payment.purpose,
            "reference_note": payment.reference_note,
        },
    )


def _reconcile_checkout_callback(
    db: Session,
    payment,
    payload: VerifyRazorpayPaymentSchema,
):
    if payment.gateway_payment_id:
        return reconcile_captured_gateway_payment(
            db,
            gateway_order_id=payment.gateway_order_id,
            gateway_payment_id=payload.razorpay_payment_id,
            amount_paise=payment.amount * 100,
            currency="INR",
            status="captured",
            captured=True,
            checkout_signature=payload.razorpay_signature,
        )

    try:
        gateway_payment = razorpay_service.fetch_payment(
            payload.razorpay_payment_id
        )
    except (httpx.HTTPError, ValueError) as exc:
        logger.exception(
            "Unable to fetch Razorpay payment %s",
            payload.razorpay_payment_id,
        )
        raise HTTPException(
            status_code=502,
            detail="Unable to confirm captured payment with gateway",
        ) from exc

    if not isinstance(gateway_payment, dict):
        raise HTTPException(
            status_code=502,
            detail="Payment gateway returned an invalid response",
        )
    if gateway_payment.get("id") != payload.razorpay_payment_id:
        raise HTTPException(status_code=409, detail="Gateway payment identity mismatch")
    if gateway_payment.get("order_id") != payment.gateway_order_id:
        raise HTTPException(status_code=409, detail="Gateway order identity mismatch")

    return reconcile_captured_gateway_payment(
        db,
        gateway_order_id=payment.gateway_order_id,
        gateway_payment_id=payload.razorpay_payment_id,
        amount_paise=gateway_payment.get("amount"),
        currency=gateway_payment.get("currency"),
        status=gateway_payment.get("status"),
        captured=gateway_payment.get("captured"),
        checkout_signature=payload.razorpay_signature,
    )


def _reconcile_checkout_callback_or_http(
    db: Session,
    payment,
    payload: VerifyRazorpayPaymentSchema,
):
    try:
        return _reconcile_checkout_callback(db, payment, payload)
    except PaymentOrderNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except InvalidCapturedPaymentError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except GatewayPaymentConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/verify")
def verify_razorpay_payment(
    payload: VerifyRazorpayPaymentSchema,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_role(UserRole.CLIENT.value)),
    db: Session = Depends(get_db),
):
    """Verify a completed Razorpay checkout and mark the payment as PAID.

    Call this endpoint from the mobile app's Razorpay ``onSuccess`` callback.
    The three fields (``razorpay_order_id``, ``razorpay_payment_id``,
    ``razorpay_signature``) are passed verbatim from the SDK callback.
    """
    client_profile = get_client_profile_by_user_id(db, current_user.id)
    if not client_profile:
        raise HTTPException(status_code=404, detail="Client profile not found")

    payment = get_client_payment_by_gateway_order_id(db, payload.razorpay_order_id)
    if not payment or payment.client_id != client_profile.id:
        raise HTTPException(status_code=404, detail="Payment not found")

    if not razorpay_service.verify_payment_signature(
        payment.gateway_order_id,
        payload.razorpay_payment_id,
        payload.razorpay_signature,
    ):
        raise HTTPException(status_code=400, detail="Invalid payment signature")

    if (
        payment.payment_status == ClientPaymentStatus.PAID.value
        and payment.gateway_payment_id == payload.razorpay_payment_id
        and payment.gateway_signature
    ):
        # Idempotent — already processed (e.g. also captured via webhook)
        return success_response("Payment already verified", {"payment_id": payment.id})

    result = _reconcile_checkout_callback_or_http(db, payment, payload)
    payment = result.payment

    requirement = get_requirement_by_id(db, payment.requirement_id)

    db.commit()

    if not result.changed:
        return success_response(
            "Payment already verified",
            {"payment_id": payment.id, "status": payment.payment_status},
        )

    # Send invoice email in background
    try:
        from app.services.email_service import send_payment_invoice
        to_email = client_profile.email or current_user.email
        if to_email and requirement:
            client_name = client_profile.company_name or client_profile.contact_name or "Valued Client"
            background_tasks.add_task(
                send_payment_invoice,
                to_email=to_email,
                client_name=client_name,
                payment_id=payment.id,
                payment_date=payment.paid_at or payment.updated_at,
                payment_model=payment.payment_model,
                amount=payment.amount,
                reference_note=payment.reference_note,
                requirement_category=requirement.category,
                requirement_subcategory=requirement.subcategory,
                work_location=requirement.work_location,
                city=requirement.city,
                state=requirement.state,
                start_date=str(requirement.start_date) if requirement.start_date else "",
                duration_days=requirement.duration_days or 1,
            )
    except Exception:
        logger.exception("Failed to enqueue invoice email for payment #%s", payment.id)

    audit_event(
        "client_payment_verified",
        {
            "payment_id": payment.id,
            "razorpay_payment_id": payload.razorpay_payment_id,
            "client_user_id": current_user.id,
            "requirement_status_changed": False,
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
