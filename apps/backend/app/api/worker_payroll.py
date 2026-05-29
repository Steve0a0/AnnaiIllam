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
