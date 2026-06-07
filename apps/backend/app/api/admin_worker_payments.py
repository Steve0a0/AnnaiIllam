from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies.roles import require_role
from app.core.payroll_constants import PayrollItemPaymentStatus, PayrollRunStatus
from app.core.roles import UserRole
from app.db.deps import get_db
from app.models.payroll_item import PayrollItem
from app.models.payroll_run import PayrollRun
from app.models.user import User
from app.models.worker_payout import WorkerPayout
from app.repositories.assignment_repository import get_assignments_by_requirement_id
from app.repositories.attendance_repository import get_attendance_for_assignment
from app.repositories.profile_repository import get_worker_profile_by_id
from app.repositories.requirement_repository import get_requirement_by_id
from app.services.payroll_service import (
    build_payroll_item,
    calculate_attendance_summary,
    calculate_gross_amount,
)
from app.utils.audit import audit_event
from app.utils.response import success_response
from app.utils.time import utcnow

router = APIRouter(prefix="/admin/requirements", tags=["Admin Worker Payments"])

ALLOWED_PAYOUT_MODES = {"upi", "bank_transfer", "cash"}


class WorkerPaymentRecordSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    assignment_id: int
    amount: int = Field(ge=0)
    payout_mode: str
    transaction_reference: str | None = Field(default=None, max_length=255)
    notes: str | None = Field(default=None, max_length=1000)

    @field_validator("payout_mode")
    @classmethod
    def validate_payout_mode(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in ALLOWED_PAYOUT_MODES:
            raise ValueError(
                f"payout_mode must be one of: {', '.join(sorted(ALLOWED_PAYOUT_MODES))}"
            )
        return normalized


def _auto_run_notes(requirement_id: int) -> str:
    return f"auto:req_{requirement_id}"


def _get_auto_payroll_run(db: Session, requirement_id: int) -> PayrollRun | None:
    return db.execute(
        select(PayrollRun).where(PayrollRun.notes == _auto_run_notes(requirement_id))
    ).scalar_one_or_none()


def _get_payroll_item_in_run(
    db: Session, payroll_run_id: int, assignment_id: int
) -> PayrollItem | None:
    return db.execute(
        select(PayrollItem).where(
            PayrollItem.payroll_run_id == payroll_run_id,
            PayrollItem.assignment_id == assignment_id,
        )
    ).scalar_one_or_none()


def _get_payout_by_item(db: Session, payroll_item_id: int) -> WorkerPayout | None:
    return db.execute(
        select(WorkerPayout).where(WorkerPayout.payroll_item_id == payroll_item_id)
    ).scalar_one_or_none()


@router.get("/{requirement_id}/worker-payments")
def get_worker_payments(
    requirement_id: int,
    current_user: User = Depends(require_role(UserRole.ADMIN.value)),
    db: Session = Depends(get_db),
):
    requirement = get_requirement_by_id(db, requirement_id)
    if not requirement:
        raise HTTPException(status_code=404, detail="Requirement not found")

    all_assignments = get_assignments_by_requirement_id(db, requirement_id)
    # Only show workers who are payable — exclude declined, cancelled, replaced
    assignments = [
        a for a in all_assignments
        if a.status not in {"declined", "cancelled", "replaced"}
    ]
    auto_run = _get_auto_payroll_run(db, requirement_id)

    # Group by worker so per-day assignments don't create duplicate rows
    from collections import defaultdict
    worker_map: dict[int, list] = defaultdict(list)
    for a in assignments:
        worker_map[a.worker_profile_id].append(a)

    result = []
    for worker_profile_id, worker_assignments in worker_map.items():
        worker = get_worker_profile_by_id(db, worker_profile_id)
        days_assigned = len(worker_assignments)

        total_att = 0
        total_half = 0
        total_absent = 0
        total_suggested = 0

        for a in worker_assignments:
            records = get_attendance_for_assignment(db, a.id)
            summary = calculate_attendance_summary(records)
            total_att += summary["attendance_days"]
            total_half += summary["half_days"]
            total_absent += summary["absent_days"]
            total_suggested += calculate_gross_amount(
                monthly_salary=a.salary_amount,
                attendance_days=summary["attendance_days"],
                half_days=summary["half_days"],
            )

        has_attendance = total_att > 0 or total_half > 0 or total_absent > 0
        # If no attendance has been recorded yet, use assigned days as the
        # day count and compute suggested amount from assigned day rate
        if not has_attendance:
            display_days = days_assigned
            total_suggested = sum((a.salary_amount or 0) for a in worker_assignments)
        else:
            display_days = total_att

        # Use first assignment as the representative for payout lookup
        first = worker_assignments[0]
        payout_data = None
        if auto_run:
            for a in worker_assignments:
                item = _get_payroll_item_in_run(db, auto_run.id, a.id)
                if item:
                    payout = _get_payout_by_item(db, item.id)
                    if payout:
                        payout_data = {
                            "id": payout.id,
                            "amount": payout.amount,
                            "payout_mode": payout.payout_mode,
                            "payout_status": payout.payout_status,
                            "transaction_reference": payout.transaction_reference,
                            "notes": payout.notes,
                            "paid_at": payout.paid_at.isoformat() if payout.paid_at else None,
                        }
                        break

        result.append(
            {
                "assignment_id": first.id,
                "worker_profile_id": worker_profile_id,
                "worker_name": worker.full_name if worker else "Unknown",
                "salary_amount": first.salary_amount,
                "attendance_days": display_days,
                "half_days": total_half,
                "absent_days": total_absent,
                "suggested_amount": total_suggested,
                "payout": payout_data,
            }
        )

    return success_response("Worker payments fetched successfully", result)


@router.post("/{requirement_id}/worker-payments")
def record_worker_payment(
    requirement_id: int,
    payload: WorkerPaymentRecordSchema,
    current_user: User = Depends(require_role(UserRole.ADMIN.value)),
    db: Session = Depends(get_db),
):
    requirement = get_requirement_by_id(db, requirement_id)
    if not requirement:
        raise HTTPException(status_code=404, detail="Requirement not found")

    all_assignments = get_assignments_by_requirement_id(db, requirement_id)
    payable_assignments = [
        a for a in all_assignments
        if a.status not in {"declined", "cancelled", "replaced"}
    ]
    assignment = next((a for a in payable_assignments if a.id == payload.assignment_id), None)
    if not assignment:
        raise HTTPException(
            status_code=404, detail="Assignment not found for this requirement"
        )

    # Find or create the auto PayrollRun for this requirement
    auto_run = _get_auto_payroll_run(db, requirement_id)
    if not auto_run:
        end_date = requirement.start_date + timedelta(
            days=max(requirement.duration_days - 1, 0)
        )
        auto_run = PayrollRun(
            period_start=requirement.start_date,
            period_end=end_date,
            status=PayrollRunStatus.GENERATED.value,
            notes=_auto_run_notes(requirement_id),
            created_by_user_id=current_user.id,
        )
        db.add(auto_run)
        db.flush()

    # Find or create the PayrollItem for this assignment
    payroll_item = _get_payroll_item_in_run(db, auto_run.id, assignment.id)
    if not payroll_item:
        attendance_records = get_attendance_for_assignment(db, assignment.id)
        summary = calculate_attendance_summary(attendance_records)
        gross_amount = calculate_gross_amount(
            monthly_salary=assignment.salary_amount,
            attendance_days=summary["attendance_days"],
            half_days=summary["half_days"],
        )
        payroll_item = build_payroll_item(
            payroll_run_id=auto_run.id,
            assignment_id=assignment.id,
            worker_profile_id=assignment.worker_profile_id,
            gross_amount=gross_amount,
            attendance_days=summary["attendance_days"],
            half_days=summary["half_days"],
            absent_days=summary["absent_days"],
        )
        db.add(payroll_item)
        db.flush()

    existing_payout = _get_payout_by_item(db, payroll_item.id)
    if existing_payout:
        raise HTTPException(
            status_code=400, detail="Payment already recorded for this worker"
        )

    payout = WorkerPayout(
        payroll_item_id=payroll_item.id,
        worker_profile_id=assignment.worker_profile_id,
        amount=payload.amount,
        payout_mode=payload.payout_mode,
        payout_status="completed",
        transaction_reference=payload.transaction_reference,
        notes=payload.notes,
        paid_by_user_id=current_user.id,
        paid_at=utcnow(),
    )
    db.add(payout)
    # Sync payroll item amounts to the admin-entered payment so the worker
    # sees the correct figure in the earnings screen.
    payroll_item.gross_amount = payload.amount
    payroll_item.net_amount = payload.amount
    payroll_item.payment_status = PayrollItemPaymentStatus.PAID.value
    db.commit()
    db.refresh(payout)

    audit_event(
        "worker_payment_recorded",
        {
            "requirement_id": requirement_id,
            "assignment_id": assignment.id,
            "worker_profile_id": assignment.worker_profile_id,
            "amount": payout.amount,
            "payout_mode": payout.payout_mode,
            "admin_user_id": current_user.id,
        },
    )

    return success_response(
        "Worker payment recorded successfully",
        {
            "payout_id": payout.id,
            "assignment_id": assignment.id,
            "worker_profile_id": assignment.worker_profile_id,
            "amount": payout.amount,
            "payout_mode": payout.payout_mode,
            "payout_status": payout.payout_status,
            "paid_at": payout.paid_at.isoformat() if payout.paid_at else None,
        },
    )
