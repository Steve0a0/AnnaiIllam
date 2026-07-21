"""Authoritative GST tax-invoice snapshot, numbering, and rendering."""

from __future__ import annotations

from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
from html import escape
import re

from fastapi import HTTPException, Response
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.client_profile import ClientProfile
from app.models.invoice import Invoice, InvoiceNumberSequence
from app.models.requirement import Requirement


GSTIN_PATTERN = re.compile(r"^\d{2}[A-Z]{5}\d{4}[A-Z][1-9A-Z]Z[0-9A-Z]$")
SAC_PATTERN = re.compile(r"^\d{4}(?:\d{2})?(?:\d{2})?$")

GST_STATE_CODES = {
    "jammu and kashmir": "01", "himachal pradesh": "02", "punjab": "03",
    "chandigarh": "04", "uttarakhand": "05", "haryana": "06", "delhi": "07",
    "rajasthan": "08", "uttar pradesh": "09", "bihar": "10", "sikkim": "11",
    "arunachal pradesh": "12", "nagaland": "13", "manipur": "14", "mizoram": "15",
    "tripura": "16", "meghalaya": "17", "assam": "18", "west bengal": "19",
    "jharkhand": "20", "odisha": "21", "chhattisgarh": "22", "madhya pradesh": "23",
    "gujarat": "24", "dadra and nagar haveli and daman and diu": "26",
    "maharashtra": "27", "andhra pradesh": "37", "karnataka": "29", "goa": "30",
    "lakshadweep": "31", "kerala": "32", "tamil nadu": "33", "puducherry": "34",
    "andaman and nicobar islands": "35", "telangana": "36", "ladakh": "38",
    "other territory": "97", "centre jurisdiction": "99",
}


def financial_year_for(day: date) -> str:
    start = day.year if day.month >= 4 else day.year - 1
    return f"{start}-{str(start + 1)[-2:]}"


def state_code_for(state: str) -> str:
    code = GST_STATE_CODES.get(" ".join(state.strip().lower().split()))
    if not code:
        raise HTTPException(status_code=422, detail=f"Unsupported GST state/UT: {state}")
    return code


def _required_config() -> dict[str, str | float]:
    supplier_state_code = settings.invoice_supplier_state_code.strip()
    values: dict[str, str | float] = {
        "supplier_legal_name": settings.invoice_supplier_legal_name.strip(),
        "supplier_address": settings.invoice_supplier_address.strip(),
        "supplier_gstin": settings.invoice_supplier_gstin.strip().upper(),
        "supplier_state": settings.invoice_supplier_state.strip(),
        "supplier_state_code": supplier_state_code.zfill(2) if supplier_state_code else "",
        "sac_code": settings.invoice_default_sac_code.strip(),
        "gst_rate": settings.invoice_default_gst_rate,
        "authorised_signatory": settings.invoice_authorised_signatory.strip(),
    }
    missing = [key for key, value in values.items() if value == ""]
    if missing:
        raise HTTPException(
            status_code=503,
            detail="GST invoice configuration is incomplete: " + ", ".join(missing),
        )
    gstin = str(values["supplier_gstin"])
    state_code = str(values["supplier_state_code"])
    if not GSTIN_PATTERN.fullmatch(gstin):
        raise HTTPException(status_code=503, detail="Supplier GSTIN configuration is invalid")
    if gstin[:2] != state_code:
        raise HTTPException(status_code=503, detail="Supplier GSTIN and state code do not match")
    if state_code_for(str(values["supplier_state"])) != state_code:
        raise HTTPException(status_code=503, detail="Supplier state and state code do not match")
    if not SAC_PATTERN.fullmatch(str(values["sac_code"])):
        raise HTTPException(status_code=503, detail="Default SAC configuration is invalid")
    return values


def _round_rupees(amount: Decimal) -> int:
    return int(amount.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def build_invoice_snapshot(
    *, requirement: Requirement, client: ClientProfile, subtotal: int
) -> dict[str, object]:
    config = _required_config()
    recipient_name = (client.company_name or client.contact_name or "").strip()
    recipient_address = ", ".join(
        value.strip() for value in [client.address, client.city, client.state] if value and value.strip()
    )
    if not recipient_name or not recipient_address or not client.state:
        raise HTTPException(
            status_code=422,
            detail="Client legal name, address, and state are required before generating an invoice",
        )

    recipient_state_code = state_code_for(client.state)
    recipient_gstin = (client.gst_number or "").strip().upper() or None
    if recipient_gstin:
        if not GSTIN_PATTERN.fullmatch(recipient_gstin):
            raise HTTPException(status_code=422, detail="Client GSTIN is invalid")
        if recipient_gstin[:2] != recipient_state_code:
            raise HTTPException(status_code=422, detail="Client GSTIN and state do not match")

    place_of_supply = requirement.state.strip()
    place_of_supply_code = state_code_for(place_of_supply)
    rate = Decimal(str(config["gst_rate"]))
    taxable = Decimal(subtotal)
    if str(config["supplier_state_code"]) == place_of_supply_code:
        half_rate = rate / Decimal("2")
        cgst_amount = _round_rupees(taxable * half_rate / Decimal("100"))
        sgst_amount = _round_rupees(taxable * half_rate / Decimal("100"))
        igst_amount = 0
        cgst_rate = sgst_rate = float(half_rate)
        igst_rate = 0.0
    else:
        cgst_amount = sgst_amount = 0
        igst_amount = _round_rupees(taxable * rate / Decimal("100"))
        cgst_rate = sgst_rate = 0.0
        igst_rate = float(rate)
    gst_amount = cgst_amount + sgst_amount + igst_amount

    return {
        "subtotal": subtotal,
        "gst_rate": float(rate),
        "gst_amount": gst_amount,
        "total_amount": subtotal + gst_amount,
        "supplier_legal_name": config["supplier_legal_name"],
        "supplier_address": config["supplier_address"],
        "supplier_gstin": config["supplier_gstin"],
        "supplier_state": config["supplier_state"],
        "supplier_state_code": config["supplier_state_code"],
        "recipient_legal_name": recipient_name,
        "recipient_address": recipient_address,
        "recipient_gstin": recipient_gstin,
        "recipient_state": client.state.strip(),
        "recipient_state_code": recipient_state_code,
        "place_of_supply": place_of_supply,
        "place_of_supply_state_code": place_of_supply_code,
        "sac_code": config["sac_code"],
        "service_description": " - ".join(
            value for value in [requirement.category, requirement.subcategory] if value
        ),
        "cgst_rate": cgst_rate,
        "cgst_amount": cgst_amount,
        "sgst_rate": sgst_rate,
        "sgst_amount": sgst_amount,
        "igst_rate": igst_rate,
        "igst_amount": igst_amount,
        "reverse_charge": False,
        "authorised_signatory": config["authorised_signatory"],
    }


def allocate_invoice_number(db: Session, financial_year: str) -> tuple[str, int]:
    if db.bind is not None and db.bind.dialect.name == "postgresql":
        db.execute(
            pg_insert(InvoiceNumberSequence)
            .values(financial_year=financial_year, last_value=0)
            .on_conflict_do_nothing(index_elements=["financial_year"])
        )
    elif db.get(InvoiceNumberSequence, financial_year) is None:
        db.add(InvoiceNumberSequence(financial_year=financial_year, last_value=0))
        db.flush()

    sequence = db.execute(
        select(InvoiceNumberSequence)
        .where(InvoiceNumberSequence.financial_year == financial_year)
        .with_for_update()
    ).scalar_one()
    sequence.last_value += 1
    short_year = financial_year[2:]
    number = f"AI/{short_year}/{sequence.last_value:04d}"
    if len(number) > 16:
        raise RuntimeError("Generated GST invoice number exceeds 16 characters")
    return number, sequence.last_value


def invoice_to_dict(invoice: Invoice) -> dict[str, object]:
    return {
        "id": invoice.id, "invoice_number": invoice.invoice_number,
        "requirement_id": invoice.requirement_id, "client_id": invoice.client_id,
        "quote_id": invoice.quote_id, "financial_year": invoice.financial_year,
        "sequence_number": invoice.sequence_number,
        "invoice_date": str(invoice.invoice_date) if invoice.invoice_date else None,
        "subtotal": invoice.subtotal, "gst_rate": invoice.gst_rate,
        "gst_amount": invoice.gst_amount, "total_amount": invoice.total_amount,
        "cgst_rate": invoice.cgst_rate, "cgst_amount": invoice.cgst_amount,
        "sgst_rate": invoice.sgst_rate, "sgst_amount": invoice.sgst_amount,
        "igst_rate": invoice.igst_rate, "igst_amount": invoice.igst_amount,
        "place_of_supply": invoice.place_of_supply,
        "place_of_supply_state_code": invoice.place_of_supply_state_code,
        "sac_code": invoice.sac_code, "recipient_gstin": invoice.recipient_gstin,
        "status": invoice.status,
        "issued_at": invoice.issued_at.isoformat() if invoice.issued_at else None,
        "due_date": str(invoice.due_date) if invoice.due_date else None,
        "content_sha256": invoice.content_sha256,
        "created_by_user_id": invoice.created_by_user_id,
        "issued_by_user_id": invoice.issued_by_user_id,
        "created_at": invoice.created_at.isoformat(),
        "updated_at": invoice.updated_at.isoformat(),
    }


def render_tax_invoice_html(invoice: Invoice) -> str:
    if not invoice.invoice_date or not invoice.financial_year:
        raise ValueError("Invoice must be numbered and dated before rendering")
    def e(value: object) -> str:
        return escape(str(value or ""))
    tax_rows = ""
    if invoice.igst_amount:
        tax_rows = f"<tr><td>IGST @ {invoice.igst_rate:g}%</td><td class='num'>&#8377;{invoice.igst_amount:,}</td></tr>"
    else:
        tax_rows = (
            f"<tr><td>CGST @ {invoice.cgst_rate:g}%</td><td class='num'>&#8377;{invoice.cgst_amount:,}</td></tr>"
            f"<tr><td>SGST @ {invoice.sgst_rate:g}%</td><td class='num'>&#8377;{invoice.sgst_amount:,}</td></tr>"
        )
    recipient_gstin = e(invoice.recipient_gstin) if invoice.recipient_gstin else "Unregistered"
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>Tax Invoice {e(invoice.invoice_number)}</title><style>
body{{font:14px Arial,sans-serif;color:#1c1917;margin:0;background:#f5f5f4}}main{{max-width:760px;margin:24px auto;background:#fff;padding:36px}}
h1{{margin:0;color:#0d2e1e}}.top,.parties{{display:flex;justify-content:space-between;gap:32px}}.top{{border-bottom:2px solid #0d2e1e;padding-bottom:20px}}
.parties>section{{width:50%}}table{{width:100%;border-collapse:collapse;margin-top:24px}}th,td{{padding:10px;border:1px solid #d6d3d1;text-align:left}}th{{background:#f5f5f4}}.num{{text-align:right}}.totals{{margin-left:auto;width:48%}}
.note{{margin-top:28px;font-size:12px;color:#57534e}}@media print{{body{{background:#fff}}main{{margin:0;max-width:none}}}}
</style></head><body><main>
<div class="top"><section><h1>TAX INVOICE</h1><p><strong>{e(invoice.supplier_legal_name)}</strong><br>{e(invoice.supplier_address)}<br>GSTIN: {e(invoice.supplier_gstin)}<br>{e(invoice.supplier_state)} ({e(invoice.supplier_state_code)})</p></section>
<section><p><strong>Invoice:</strong> {e(invoice.invoice_number)}<br><strong>Date:</strong> {invoice.invoice_date.strftime('%d %b %Y')}<br><strong>Financial year:</strong> {e(invoice.financial_year)}<br><strong>Reverse charge:</strong> {'Yes' if invoice.reverse_charge else 'No'}</p></section></div>
<div class="parties"><section><h3>Bill to</h3><p><strong>{e(invoice.recipient_legal_name)}</strong><br>{e(invoice.recipient_address)}<br>GSTIN: {recipient_gstin}<br>{e(invoice.recipient_state)} ({e(invoice.recipient_state_code)})</p></section>
<section><h3>Place of supply</h3><p>{e(invoice.place_of_supply)} ({e(invoice.place_of_supply_state_code)})</p></section></div>
<table><thead><tr><th>Description of service</th><th>SAC</th><th class="num">Taxable value</th></tr></thead><tbody><tr><td>{e(invoice.service_description)}</td><td>{e(invoice.sac_code)}</td><td class="num">&#8377;{invoice.subtotal:,}</td></tr></tbody></table>
<table class="totals"><tbody><tr><td>Taxable value</td><td class="num">&#8377;{invoice.subtotal:,}</td></tr>{tax_rows}<tr><th>Total tax</th><th class="num">&#8377;{invoice.gst_amount:,}</th></tr><tr><th>Invoice total</th><th class="num">&#8377;{invoice.total_amount:,}</th></tr></tbody></table>
<p class="note">Authorised signatory: {e(invoice.authorised_signatory)}<br>This issued invoice is an immutable electronic record. Document SHA-256: {e(invoice.content_sha256) or 'assigned on issue'}</p>
</main></body></html>"""


def freeze_rendered_document(invoice: Invoice) -> None:
    # The hash is over the stable document without a self-referential hash value.
    html = render_tax_invoice_html(invoice)
    digest = sha256(html.encode("utf-8")).hexdigest()
    invoice.rendered_html = html
    invoice.content_sha256 = digest


def invoice_document_response(invoice: Invoice) -> Response:
    if invoice.status != "issued" or not invoice.rendered_html or not invoice.content_sha256:
        raise HTTPException(status_code=409, detail="Issued GST invoice document is unavailable")
    return Response(
        content=invoice.rendered_html,
        media_type="text/html",
        headers={
            "ETag": f'"{invoice.content_sha256}"',
            "Cache-Control": "private, max-age=31536000, immutable",
            "Content-Disposition": f'inline; filename="{invoice.invoice_number.replace("/", "-")}.html"',
        },
    )
