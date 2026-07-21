from datetime import timedelta
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies.roles import require_permission_group, require_role
from app.core.roles import UserRole
from app.core.statuses import RequirementStatus
from app.db.deps import get_db
from app.models.client_profile import ClientProfile
from app.models.invoice import Invoice
from app.models.user import User
from app.repositories.quote_repository import get_quote_by_requirement_id
from app.repositories.requirement_repository import get_requirement_by_id
from app.services.email_service import send_tax_invoice
from app.services.gst_invoice_service import (
    allocate_invoice_number,
    build_invoice_snapshot,
    financial_year_for,
    freeze_rendered_document,
    invoice_document_response,
    invoice_to_dict,
)
from app.services.notification_service import enqueue_push_to_user
from app.utils.audit import audit_event
from app.utils.pagination import PaginationParams, paginate, pagination_meta
from app.utils.response import success_response
from app.utils.time import business_date, utcnow

router = APIRouter(prefix="/admin/invoices", tags=["Admin Invoices"])


class GenerateInvoiceSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    requirement_id: int


@router.post("/generate")
def generate_invoice(
    payload: GenerateInvoiceSchema,
    current_user: User = Depends(require_permission_group("finance_admin")),
    db: Session = Depends(get_db),
):
    requirement = get_requirement_by_id(db, payload.requirement_id)
    if not requirement:
        raise HTTPException(status_code=404, detail="Requirement not found")
    if requirement.status != RequirementStatus.COMPLETED.value:
        raise HTTPException(status_code=400, detail="Invoice can only be generated for completed requirements")
    quote = get_quote_by_requirement_id(db, payload.requirement_id)
    if not quote:
        raise HTTPException(status_code=400, detail="No quote found for this requirement")
    client = db.get(ClientProfile, requirement.client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client profile not found")
    existing = db.execute(select(Invoice).where(Invoice.requirement_id == payload.requirement_id, Invoice.status != "cancelled")).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail=f"Invoice {existing.invoice_number} already exists for this requirement")

    snapshot = build_invoice_snapshot(requirement=requirement, client=client, subtotal=quote.quoted_amount)
    invoice = Invoice(
        invoice_number=f"DRAFT-{uuid4().hex[:12].upper()}",
        requirement_id=requirement.id, client_id=requirement.client_id, quote_id=quote.id,
        status="draft", due_date=business_date() + timedelta(days=30),
        created_by_user_id=current_user.id, **snapshot,
    )
    db.add(invoice)
    db.commit()
    db.refresh(invoice)
    audit_event("invoice_generated", {"invoice_id": invoice.id, "requirement_id": requirement.id, "total_amount": invoice.total_amount, "admin_user_id": current_user.id})
    return success_response("Invoice generated successfully", invoice_to_dict(invoice))


@router.post("/{invoice_id}/issue")
def issue_invoice(
    invoice_id: int, background_tasks: BackgroundTasks,
    current_user: User = Depends(require_permission_group("finance_admin")),
    db: Session = Depends(get_db),
):
    invoice = db.execute(select(Invoice).where(Invoice.id == invoice_id).with_for_update()).scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    if invoice.status != "draft":
        raise HTTPException(status_code=400, detail="Only draft invoices can be issued")
    issue_date = business_date()
    invoice.financial_year = financial_year_for(issue_date)
    invoice.invoice_number, invoice.sequence_number = allocate_invoice_number(db, invoice.financial_year)
    invoice.invoice_date = issue_date
    invoice.status = "issued"
    invoice.issued_at = utcnow()
    invoice.issued_by_user_id = current_user.id
    freeze_rendered_document(invoice)
    db.commit()
    db.refresh(invoice)
    audit_event("invoice_issued", {"invoice_id": invoice.id, "invoice_number": invoice.invoice_number, "content_sha256": invoice.content_sha256, "requirement_id": invoice.requirement_id, "total_amount": invoice.total_amount, "admin_user_id": current_user.id})

    client_profile = db.get(ClientProfile, invoice.client_id)
    if client_profile:
        client_user = db.get(User, client_profile.user_id)
        enqueue_push_to_user(
            background_tasks, db, user_id=client_profile.user_id, title="Tax Invoice Issued",
            body=f"Invoice {invoice.invoice_number} for INR {invoice.total_amount:,} has been issued.",
            data={"type": "invoice_issued", "invoice_id": invoice.id, "invoice_number": invoice.invoice_number, "screen": "BillingOverview"},
        )
        if client_user and client_user.email and invoice.rendered_html:
            background_tasks.add_task(send_tax_invoice, to_email=client_user.email, client_name=invoice.recipient_legal_name or "Client", invoice_id=invoice.id, invoice_number=invoice.invoice_number, html=invoice.rendered_html)
    return success_response("Invoice issued successfully", invoice_to_dict(invoice))


@router.get("/{invoice_id}/document.html")
def get_invoice_document(invoice_id: int, _current_user: User = Depends(require_role(UserRole.ADMIN.value)), db: Session = Depends(get_db)):
    invoice = db.get(Invoice, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice_document_response(invoice)


@router.get("/requirement/{requirement_id}")
def list_invoices_for_requirement(requirement_id: int, _current_user: User = Depends(require_role(UserRole.ADMIN.value)), db: Session = Depends(get_db)):
    invoices = db.execute(select(Invoice).where(Invoice.requirement_id == requirement_id).order_by(Invoice.created_at.desc())).scalars().all()
    return success_response("Invoices fetched successfully", [invoice_to_dict(item) for item in invoices])


@router.get("/client/{client_id}")
def list_invoices_for_client(client_id: int, pagination: PaginationParams = Depends(), _current_user: User = Depends(require_role(UserRole.ADMIN.value)), db: Session = Depends(get_db)):
    items, total = paginate(select(Invoice).where(Invoice.client_id == client_id).order_by(Invoice.created_at.desc()), db, pagination)
    return success_response("Invoices fetched successfully", {"invoices": [invoice_to_dict(item) for item in items], "meta": pagination_meta(pagination, total)})
