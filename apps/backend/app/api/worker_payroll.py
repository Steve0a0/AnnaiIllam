from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.api.dependencies.roles import require_role
from app.core.roles import UserRole
from app.db.deps import get_db
from app.models.user import User
from app.repositories.assignment_repository import get_assignment_by_id
from app.repositories.payment_repository import get_worker_payouts_by_worker_profile_id
from app.repositories.payroll_repository import (
    get_deductions_by_payroll_item_id,
    get_payroll_item_by_id,
    get_payroll_items_by_worker_profile_id,
    get_payroll_run_by_id,
)
from app.repositories.profile_repository import get_worker_profile_by_user_id
from app.repositories.requirement_repository import get_requirement_by_id
from app.utils.response import success_response

router = APIRouter(prefix="/worker/payroll", tags=["Worker Payroll"])


@router.get("")
def list_my_payroll(
    current_user: User = Depends(require_role(UserRole.WORKER.value)),
    db: Session = Depends(get_db),
):
    worker_profile = get_worker_profile_by_user_id(db, current_user.id)
    if not worker_profile:
        raise HTTPException(status_code=404, detail="Worker profile not found")

    items = get_payroll_items_by_worker_profile_id(db, worker_profile.id)
    data = []
    for item in items:
        run = get_payroll_run_by_id(db, item.payroll_run_id)
        data.append(
            {
                "id": item.id,
                "payroll_run_id": item.payroll_run_id,
                "assignment_id": item.assignment_id,
                "gross_amount": item.gross_amount,
                "total_deduction_amount": item.total_deduction_amount,
                "net_amount": item.net_amount,
                "attendance_days": item.attendance_days,
                "half_days": item.half_days,
                "absent_days": item.absent_days,
                "payment_status": item.payment_status,
                "period_start": str(run.period_start) if run else None,
                "period_end": str(run.period_end) if run else None,
                "run_status": run.status if run else None,
            }
        )

    return success_response("Worker payroll fetched successfully", data)


@router.get("/payouts")
def list_my_payouts(
    current_user: User = Depends(require_role(UserRole.WORKER.value)),
    db: Session = Depends(get_db),
):
    worker_profile = get_worker_profile_by_user_id(db, current_user.id)
    if not worker_profile:
        raise HTTPException(status_code=404, detail="Worker profile not found")

    payouts = get_worker_payouts_by_worker_profile_id(db, worker_profile.id)
    data = [
        {
            "id": item.id,
            "payroll_item_id": item.payroll_item_id,
            "amount": item.amount,
            "payout_mode": item.payout_mode,
            "payout_status": item.payout_status,
            "transaction_reference": item.transaction_reference,
            "notes": item.notes,
            "paid_at": item.paid_at.isoformat() if item.paid_at else None,
            "created_at": item.created_at.isoformat(),
        }
        for item in payouts
    ]
    return success_response("Worker payouts fetched successfully", data)


@router.get("/{payroll_item_id}/payslip")
def download_payslip(
    payroll_item_id: int,
    current_user: User = Depends(require_role(UserRole.WORKER.value)),
    db: Session = Depends(get_db),
):
    worker_profile = get_worker_profile_by_user_id(db, current_user.id)
    if not worker_profile:
        raise HTTPException(status_code=404, detail="Worker profile not found")

    item = get_payroll_item_by_id(db, payroll_item_id)
    if not item or item.worker_profile_id != worker_profile.id:
        raise HTTPException(status_code=404, detail="Payroll record not found")

    run = get_payroll_run_by_id(db, item.payroll_run_id)
    deductions = get_deductions_by_payroll_item_id(db, item.id)

    # Resolve payout (first paid one for this item)
    all_payouts = get_worker_payouts_by_worker_profile_id(db, worker_profile.id)
    payout = next((p for p in all_payouts if p.payroll_item_id == item.id), None)

    # Resolve job name via assignment → requirement
    job_name = "–"
    if item.assignment_id:
        assignment = get_assignment_by_id(db, item.assignment_id)
        if assignment and assignment.requirement_id:
            requirement = get_requirement_by_id(db, assignment.requirement_id)
            if requirement:
                job_name = f"{requirement.category} – {requirement.city}"

    period = (
        f"{run.period_start} to {run.period_end}" if run else "–"
    )
    paid_on = payout.paid_at.strftime("%d %b %Y") if payout and payout.paid_at else "Pending"
    txn_ref = payout.transaction_reference if payout and payout.transaction_reference else "–"

    sep = "-" * 44
    lines = [
        "ANNAI ILLAM – WORKER PAYSLIP",
        sep,
        f"Worker     : {worker_profile.full_name}",
        f"Phone      : {current_user.phone}",
        f"Job        : {job_name}",
        f"Period     : {period}",
        sep,
        "ATTENDANCE",
        f"  Days worked  : {item.attendance_days}",
        f"  Half days    : {item.half_days}",
        f"  Absent days  : {item.absent_days}",
        sep,
        "EARNINGS",
        f"  Gross pay    : Rs. {item.gross_amount:,.0f}",
    ]

    if deductions:
        lines.append("DEDUCTIONS")
        for d in deductions:
            lines.append(f"  {d.deduction_type:<14}: Rs. {d.amount:,.0f}"
                         + (f"  ({d.reason})" if d.reason else ""))
        lines.append(f"  {'Total':<14}: Rs. {item.total_deduction_amount:,.0f}")

    lines += [
        sep,
        f"  NET PAY      : Rs. {item.net_amount:,.0f}",
        sep,
        "PAYMENT",
        f"  Status       : {'Paid' if item.payment_status == 'paid' else 'Pending'}",
        f"  Paid on      : {paid_on}",
        f"  Reference    : {txn_ref}",
        sep,
        "This is a system-generated payslip.",
        "Annai Illam Staffing Platform",
    ]

    content = "\n".join(lines)
    filename = f"payslip-{worker_profile.full_name.replace(' ', '_')}-{period.replace(' ', '')}.txt"
    return Response(
        content=content,
        media_type="text/plain; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _safe(text: str) -> str:
    """Replace Unicode chars outside latin-1 with ASCII equivalents so
    fpdf2's built-in Helvetica font doesn't raise FPDFUnicodeEncodingException."""
    return (
        text
        .replace("\u2013", "-")   # en dash  –
        .replace("\u2014", "-")   # em dash  —
        .replace("\u2018", "'")   # left single quote
        .replace("\u2019", "'")   # right single quote
        .replace("\u201c", '"')   # left double quote
        .replace("\u201d", '"')   # right double quote
        .replace("\u20b9", "Rs.") # ₹ rupee sign
        .encode("latin-1", errors="replace").decode("latin-1")
    )


def _build_payslip_pdf(
    worker_name: str,
    phone: str,
    job_name: str,
    period: str,
    attendance_days: int,
    half_days: int,
    absent_days: int,
    gross_amount: int,
    total_deduction_amount: int,
    net_amount: int,
    deductions: list,
    payment_status: str,
    paid_on: str,
    txn_ref: str,
) -> bytes:
    from fpdf import FPDF

    # Sanitise all user-supplied strings to latin-1 safe equivalents
    worker_name = _safe(worker_name)
    phone       = _safe(phone)
    job_name    = _safe(job_name)
    period      = _safe(period)
    paid_on     = _safe(paid_on)
    txn_ref     = _safe(txn_ref)

    GREEN = (26, 102, 64)    # #1A6640
    WHITE = (255, 255, 255)
    LIGHT = (237, 250, 243)  # #EDFAF3
    INK   = (28, 25, 23)     # #1C1917
    MUTED = (120, 113, 108)  # #78716C

    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=False)
    pdf.add_page()
    pdf.set_margins(0, 0, 0)

    # ── Dark green header ────────────────────────────────────────────────
    pdf.set_fill_color(*GREEN)
    pdf.rect(0, 0, 210, 42, style="F")

    pdf.set_xy(14, 10)
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(*WHITE)
    pdf.cell(0, 8, "ANNAI ILLAM", ln=True)

    pdf.set_x(14)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(200, 230, 210)
    pdf.cell(0, 6, "Worker Payslip", ln=True)

    # ── Pale green info band ─────────────────────────────────────────────
    pdf.set_fill_color(*LIGHT)
    pdf.rect(0, 42, 210, 26, style="F")

    col_w = 62
    info_y = 47
    info = [
        ("Worker", worker_name),
        ("Phone", phone),
        ("Job", job_name),
        ("Period", period),
    ]
    for i, (label, value) in enumerate(info):
        col = i % 3
        row = i // 3
        x = 14 + col * col_w
        y = info_y + row * 9
        pdf.set_xy(x, y)
        pdf.set_font("Helvetica", "", 7)
        pdf.set_text_color(*MUTED)
        pdf.cell(col_w - 2, 4, label.upper(), ln=False)
        pdf.set_xy(x, y + 4)
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(*INK)
        pdf.cell(col_w - 2, 4, value[:36], ln=False)

    # ── Section helper ───────────────────────────────────────────────────
    def section_header(y: float, title: str) -> float:
        pdf.set_xy(14, y)
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_text_color(*GREEN)
        pdf.cell(0, 5, title.upper(), ln=True)
        pdf.set_draw_color(*GREEN)
        pdf.set_line_width(0.3)
        pdf.line(14, y + 5, 196, y + 5)
        return y + 8

    def row(y: float, label: str, value: str, bold_value: bool = False) -> float:
        pdf.set_xy(14, y)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*MUTED)
        pdf.cell(70, 5.5, label)
        pdf.set_xy(84, y)
        pdf.set_font("Helvetica", "B" if bold_value else "", 9)
        pdf.set_text_color(*INK)
        pdf.cell(0, 5.5, value)
        return y + 6

    # ── Attendance ───────────────────────────────────────────────────────
    y = section_header(74, "Attendance")
    y = row(y, "Days worked", str(attendance_days))
    y = row(y, "Half days", str(half_days))
    y = row(y, "Absent days", str(absent_days))

    # ── Earnings ─────────────────────────────────────────────────────────
    y += 4
    y = section_header(y, "Earnings")
    y = row(y, "Gross pay", f"Rs. {gross_amount:,.0f}")

    # ── Deductions ───────────────────────────────────────────────────────
    if deductions:
        y += 4
        y = section_header(y, "Deductions")
        for d in deductions:
            label = _safe(d.deduction_type.replace("_", " ").title())
            suffix = f"  ({_safe(d.reason)})" if d.reason else ""
            y = row(y, label + suffix, f"Rs. {d.amount:,.0f}")
        y = row(y, "Total deductions", f"Rs. {total_deduction_amount:,.0f}")

    # ── Net pay box ──────────────────────────────────────────────────────
    y += 6
    pdf.set_fill_color(*GREEN)
    pdf.rect(14, y, 182, 12, style="F")
    pdf.set_xy(18, y + 2)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(*WHITE)
    pdf.cell(80, 8, "NET PAY")
    pdf.set_xy(100, y + 2)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, f"Rs. {net_amount:,.0f}")

    # ── Payment ──────────────────────────────────────────────────────────
    y += 20
    y = section_header(y, "Payment Details")
    status_label = "Paid" if payment_status == "paid" else "Pending"
    y = row(y, "Status", status_label, bold_value=True)
    y = row(y, "Paid on", paid_on)
    y = row(y, "Transaction reference", txn_ref)

    # ── Footer ───────────────────────────────────────────────────────────
    pdf.set_fill_color(*GREEN)
    pdf.rect(0, 277, 210, 20, style="F")
    pdf.set_xy(14, 281)
    pdf.set_font("Helvetica", "", 7)
    pdf.set_text_color(*WHITE)
    pdf.cell(0, 4, "This is a system-generated payslip. | Annai Illam Staffing Platform")

    return bytes(pdf.output())


@router.get("/{payroll_item_id}/payslip.pdf")
def download_payslip_pdf(
    payroll_item_id: int,
    current_user: User = Depends(require_role(UserRole.WORKER.value)),
    db: Session = Depends(get_db),
):
    worker_profile = get_worker_profile_by_user_id(db, current_user.id)
    if not worker_profile:
        raise HTTPException(status_code=404, detail="Worker profile not found")

    item = get_payroll_item_by_id(db, payroll_item_id)
    if not item or item.worker_profile_id != worker_profile.id:
        raise HTTPException(status_code=404, detail="Payroll record not found")

    run = get_payroll_run_by_id(db, item.payroll_run_id)
    deductions = get_deductions_by_payroll_item_id(db, item.id)

    all_payouts = get_worker_payouts_by_worker_profile_id(db, worker_profile.id)
    payout = next((p for p in all_payouts if p.payroll_item_id == item.id), None)

    job_name = "–"
    if item.assignment_id:
        assignment = get_assignment_by_id(db, item.assignment_id)
        if assignment and assignment.requirement_id:
            requirement = get_requirement_by_id(db, assignment.requirement_id)
            if requirement:
                job_name = f"{requirement.category} – {requirement.city}"

    period = f"{run.period_start} to {run.period_end}" if run else "–"
    paid_on = payout.paid_at.strftime("%d %b %Y") if payout and payout.paid_at else "Pending"
    txn_ref = payout.transaction_reference if payout and payout.transaction_reference else "–"

    pdf_bytes = _build_payslip_pdf(
        worker_name=worker_profile.full_name,
        phone=current_user.phone,
        job_name=job_name,
        period=period,
        attendance_days=item.attendance_days,
        half_days=item.half_days,
        absent_days=item.absent_days,
        gross_amount=item.gross_amount,
        total_deduction_amount=item.total_deduction_amount,
        net_amount=item.net_amount,
        deductions=deductions,
        payment_status=item.payment_status,
        paid_on=paid_on,
        txn_ref=txn_ref,
    )

    safe_name = worker_profile.full_name.replace(" ", "_")
    safe_period = period.replace(" ", "").replace("/", "-")
    filename = f"payslip-{safe_name}-{safe_period}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
