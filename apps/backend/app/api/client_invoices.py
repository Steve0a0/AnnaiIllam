from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies.roles import require_role
from app.core.roles import UserRole
from app.db.deps import get_db
from app.models.invoice import Invoice
from app.models.user import User
from app.repositories.client_repository import get_client_profile_by_user_id
from app.services.gst_invoice_service import invoice_document_response, invoice_to_dict
from app.utils.pagination import PaginationParams, paginate, pagination_meta
from app.utils.response import success_response

router = APIRouter(prefix="/client/invoices", tags=["Client Invoices"])


def _owned_issued_invoice(db: Session, user_id: int, invoice_id: int) -> Invoice:
    profile = get_client_profile_by_user_id(db, user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Client profile not found")
    invoice = db.get(Invoice, invoice_id)
    if (
        not invoice
        or invoice.client_id != profile.id
        or invoice.status != "issued"
        or not invoice.rendered_html
        or not invoice.content_sha256
    ):
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice


@router.get("")
def list_my_invoices(pagination: PaginationParams = Depends(), current_user: User = Depends(require_role(UserRole.CLIENT.value)), db: Session = Depends(get_db)):
    profile = get_client_profile_by_user_id(db, current_user.id)
    if not profile:
        raise HTTPException(status_code=404, detail="Client profile not found")
    stmt = select(Invoice).where(
        Invoice.client_id == profile.id,
        Invoice.status == "issued",
        Invoice.rendered_html.is_not(None),
        Invoice.content_sha256.is_not(None),
    ).order_by(Invoice.invoice_date.desc(), Invoice.id.desc())
    items, total = paginate(stmt, db, pagination)
    return success_response("Invoices fetched successfully", {"invoices": [invoice_to_dict(item) for item in items], "meta": pagination_meta(pagination, total)})


@router.get("/{invoice_id}/document.html")
def get_my_invoice_document(invoice_id: int, current_user: User = Depends(require_role(UserRole.CLIENT.value)), db: Session = Depends(get_db)):
    return invoice_document_response(_owned_issued_invoice(db, current_user.id, invoice_id))


@router.get("/{invoice_id}")
def get_my_invoice(invoice_id: int, current_user: User = Depends(require_role(UserRole.CLIENT.value)), db: Session = Depends(get_db)):
    return success_response("Invoice fetched successfully", invoice_to_dict(_owned_issued_invoice(db, current_user.id, invoice_id)))
