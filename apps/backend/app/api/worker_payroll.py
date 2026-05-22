from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies.roles import require_role
from app.core.roles import UserRole
from app.db.deps import get_db
from app.models.user import User
from app.repositories.payment_repository import get_worker_payouts_by_worker_profile_id
from app.repositories.payroll_repository import get_payroll_items_by_worker_profile_id, get_payroll_run_by_id
from app.repositories.profile_repository import get_worker_profile_by_user_id
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
