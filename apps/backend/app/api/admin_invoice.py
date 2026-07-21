from datetime import timedelta

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.dependencies.roles import require_role
from app.core.roles import UserRole
from app.core.statuses import RequirementStatus
from app.db.deps import get_db
from app.models.client_profile import ClientProfile
from app.models.invoice import Invoice
from app.models.user import User
from app.repositories.quote_repository import get_quote_by_requirement_id
from app.repositories.requirement_repository import get_requirement_by_id
from app.services.notification_service import enqueue_push_to_user
from app.utils.audit import audit_event
from app.utils.pagination import PaginationParams, paginate, pagination_meta
from app.utils.response import success_response
from app.utils.time import business_date, utcnow

router = APIRouter(prefix="/admin/invoices", tags=["Admin Invoices"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _invoice_to_dict(invoice: Invoice) -> dict:
    return {
        "id": invoice.id,
        "invoice_number": invoice.invoice_number,
        "requirement_id": invoice.requirement_id,
        "client_id": invoice.client_id,
        "quote_id": invoice.quote_id,
        "subtotal": invoice.subtotal,
        "gst_rate": invoice.gst_rate,
        "gst_amount": invoice.gst_amount,
        "total_amount": invoice.total_amount,
        "status": invoice.status,
        "issued_at": invoice.issued_at.isoformat() if invoice.issued_at else None,
        "due_date": str(invoice.due_date) if invoice.due_date else None,
        "pdf_url": invoice.pdf_url,
        "created_by_user_id": invoice.created_by_user_id,
        "created_at": invoice.created_at.isoformat(),
        "updated_at": invoice.updated_at.isoformat(),
    }


def _next_invoice_number(db: Session) -> str:
    year = utcnow().year
    count: int = db.execute(
        select(func.count(Invoice.id)).where(
            Invoice.invoice_number.like(f"INV-{year}-%")
        )
    ).scalar_one()
    return f"INV-{year}-{count + 1:04d}"


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class GenerateInvoiceSchema(BaseModel):
    requirement_id: int
    gst_rate: float = 18.0


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.post("/generate")
def generate_invoice(
    payload: GenerateInvoiceSchema,
    current_user: User = Depends(require_role(UserRole.ADMIN.value)),
    db: Session = Depends(get_db),
):
    requirement = get_requirement_by_id(db, payload.requirement_id)
    if not requirement:
        raise HTTPException(status_code=404, detail="Requirement not found")

    if requirement.status != RequirementStatus.COMPLETED.value:
        raise HTTPException(
            status_code=400,
            detail="Invoice can only be generated for completed requirements",
        )

    quote = get_quote_by_requirement_id(db, payload.requirement_id)
    if not quote:
        raise HTTPException(status_code=400, detail="No quote found for this requirement")

    # Block duplicate non-cancelled invoices
    existing = db.execute(
        select(Invoice).where(
            Invoice.requirement_id == payload.requirement_id,
            Invoice.status != "cancelled",
        )
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Invoice {existing.invoice_number} already exists for this requirement",
        )

    invoice_number = _next_invoice_number(db)
    subtotal = quote.quoted_amount
    gst_rate = payload.gst_rate
    gst_amount = round(subtotal * gst_rate / 100)
    total_amount = subtotal + gst_amount
    due_date = business_date() + timedelta(days=30)

    invoice = Invoice(
        invoice_number=invoice_number,
        requirement_id=requirement.id,
        client_id=requirement.client_id,
        quote_id=quote.id,
        subtotal=subtotal,
        gst_rate=gst_rate,
        gst_amount=gst_amount,
        total_amount=total_amount,
        status="draft",
        due_date=due_date,
        created_by_user_id=current_user.id,
    )
    db.add(invoice)
    db.commit()
    db.refresh(invoice)

    audit_event(
        "invoice_generated",
        {
            "invoice_id": invoice.id,
            "invoice_number": invoice_number,
            "requirement_id": requirement.id,
            "subtotal": subtotal,
            "gst_amount": gst_amount,
            "total_amount": total_amount,
            "admin_user_id": current_user.id,
        },
    )

    return success_response("Invoice generated successfully", _invoice_to_dict(invoice))


@router.post("/{invoice_id}/issue")
def issue_invoice(
    invoice_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_role(UserRole.ADMIN.value)),
    db: Session = Depends(get_db),
):
    invoice = db.get(Invoice, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    if invoice.status != "draft":
        raise HTTPException(status_code=400, detail="Only draft invoices can be issued")

    invoice.status = "issued"
    invoice.issued_at = utcnow()
    db.commit()

    audit_event(
        "invoice_issued",
        {
            "invoice_id": invoice.id,
            "invoice_number": invoice.invoice_number,
            "requirement_id": invoice.requirement_id,
            "total_amount": invoice.total_amount,
            "admin_user_id": current_user.id,
        },
    )

    # Push notification to client
    client_profile = db.execute(
        select(ClientProfile).where(ClientProfile.id == invoice.client_id)
    ).scalar_one_or_none()
    if client_profile:
        enqueue_push_to_user(
            background_tasks,
            db,
            user_id=client_profile.user_id,
            title="Invoice Issued",
            body=(
                f"Invoice {invoice.invoice_number} for ₹{invoice.total_amount:,} "
                f"has been issued. Due date: {invoice.due_date}."
            ),
            data={
                "type": "invoice_issued",
                "invoice_id": invoice.id,
                "invoice_number": invoice.invoice_number,
                "screen": "JobsTab",
            },
        )

    return success_response("Invoice issued successfully", _invoice_to_dict(invoice))


@router.get("/requirement/{requirement_id}")
def list_invoices_for_requirement(
    requirement_id: int,
    current_user: User = Depends(require_role(UserRole.ADMIN.value)),
    db: Session = Depends(get_db),
):
    invoices = db.execute(
        select(Invoice)
        .where(Invoice.requirement_id == requirement_id)
        .order_by(Invoice.created_at.desc())
    ).scalars().all()

    return success_response(
        "Invoices fetched successfully",
        [_invoice_to_dict(inv) for inv in invoices],
    )


@router.get("/client/{client_id}")
def list_invoices_for_client(
    client_id: int,
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(require_role(UserRole.ADMIN.value)),
    db: Session = Depends(get_db),
):
    stmt = (
        select(Invoice)
        .where(Invoice.client_id == client_id)
        .order_by(Invoice.created_at.desc())
    )
    items, total = paginate(stmt, db, pagination)

    return success_response(
        "Invoices fetched successfully",
        {
            "invoices": [_invoice_to_dict(inv) for inv in items],
            "meta": pagination_meta(pagination, total),
        },
    )
