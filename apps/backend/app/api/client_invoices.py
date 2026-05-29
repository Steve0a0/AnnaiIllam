from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies.roles import require_role
from app.core.roles import UserRole
from app.db.deps import get_db
from app.models.invoice import Invoice
from app.models.user import User
from app.repositories.client_repository import get_client_profile_by_user_id
from app.utils.pagination import PaginationParams, paginate, pagination_meta
from app.utils.response import success_response


router = APIRouter(prefix="/client/invoices", tags=["Client Invoices"])


def _invoice_to_dict(invoice: Invoice) -> dict:
    return {
        "id": invoice.id,
        "invoice_number": invoice.invoice_number,
        "requirement_id": invoice.requirement_id,
        "subtotal": invoice.subtotal,
        "gst_rate": invoice.gst_rate,
        "gst_amount": invoice.gst_amount,
        "total_amount": invoice.total_amount,
        "status": invoice.status,
        "issued_at": invoice.issued_at.isoformat() if invoice.issued_at else None,
        "due_date": str(invoice.due_date) if invoice.due_date else None,
        "pdf_url": invoice.pdf_url,
        "created_at": invoice.created_at.isoformat(),
    }


@router.get("")
def list_my_invoices(
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(require_role(UserRole.CLIENT.value)),
    db: Session = Depends(get_db),
):
    client_profile = get_client_profile_by_user_id(db, current_user.id)
    if not client_profile:
        raise HTTPException(status_code=404, detail="Client profile not found")

    stmt = (
        select(Invoice)
        .where(Invoice.client_id == client_profile.id)
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


@router.get("/{invoice_id}")
def get_my_invoice(
    invoice_id: int,
    current_user: User = Depends(require_role(UserRole.CLIENT.value)),
    db: Session = Depends(get_db),
):
    client_profile = get_client_profile_by_user_id(db, current_user.id)
    if not client_profile:
        raise HTTPException(status_code=404, detail="Client profile not found")

    invoice = db.get(Invoice, invoice_id)
    if not invoice or invoice.client_id != client_profile.id:
        raise HTTPException(status_code=404, detail="Invoice not found")

    return success_response("Invoice fetched successfully", _invoice_to_dict(invoice))
