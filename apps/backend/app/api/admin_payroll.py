import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies.roles import require_permission_group, require_role
from app.core.payroll_constants import DeductionType, PayrollItemPaymentStatus, PayrollRunStatus
from app.core.rate_limit import check_rate_limit
from app.core.roles import UserRole
from app.db.deps import get_db
from app.models.user import User
from app.repositories.assignment_repository import get_active_assignments
from app.repositories.attendance_repository import get_attendance_for_assignment_between_dates
from app.repositories.payroll_repository import (
    create_deduction,
    create_payroll_item,
    create_payroll_run,
    get_all_payroll_runs,
    get_deductions_by_payroll_item_id,
    get_payroll_item_by_id,
    get_payroll_items_by_run_id,
    get_payroll_run_by_id,
)
from app.schemas.payroll import (
    PayrollDeductionAddSchema,
    PayrollRunCreateSchema,
    PayrollRunStatusUpdateSchema,
)
from app.services.payroll_service import (
    build_deduction,
    build_payroll_item,
    build_payroll_run,
    calculate_attendance_summary,
    calculate_gross_amount,
    calculate_platform_margin,
    ensure_payroll_not_locked,
    recalculate_payroll_item,
)
from app.utils.audit import audit_event
from app.utils.response import success_response

router = APIRouter(prefix="/admin/payroll", tags=["Admin Payroll"])
security_logger = logging.getLogger("annai_illam_security")


def serialize_payroll_item(item, deductions=None) -> dict:
    return {
        "id": item.id,
        "payroll_run_id": item.payroll_run_id,
        "assignment_id": item.assignment_id,
        "worker_profile_id": item.worker_profile_id,
        "gross_amount": item.gross_amount,
        "total_deduction_amount": item.total_deduction_amount,
        "net_amount": item.net_amount,
        "attendance_days": item.attendance_days,
        "half_days": item.half_days,
        "absent_days": item.absent_days,
        "payment_status": item.payment_status,
        "platform_margin": item.platform_margin,
        "is_stale": item.is_stale,
        "deductions": [
            {
                "id": deduction.id,
                "deduction_type": deduction.deduction_type,
                "amount": deduction.amount,
                "reason": deduction.reason,
            }
            for deduction in (deductions or [])
        ],
    }


@router.get("/runs")
def list_admin_payroll_runs(
    current_user: User = Depends(require_role(UserRole.ADMIN.value)),
    db: Session = Depends(get_db),
):
    runs = get_all_payroll_runs(db)
    return success_response(
        "Payroll runs fetched successfully",
        [
            {
                "id": run.id,
                "period_start": str(run.period_start),
                "period_end": str(run.period_end),
                "status": run.status,
                "notes": run.notes,
                "require_verified_attendance": run.require_verified_attendance,
                "created_at": run.created_at.isoformat(),
            }
            for run in runs
        ],
    )


@router.post("/runs")
def create_payroll_run_draft(
    payload: PayrollRunCreateSchema,
    current_user: User = Depends(require_permission_group("finance_admin")),
    db: Session = Depends(get_db),
):
    """Create a payroll run in DRAFT status.

    Call POST /runs/{id}/generate next to calculate attendance and build payroll items.
    Two-step flow lets the admin confirm the period before generating.
    """
    if payload.period_end < payload.period_start:
        raise HTTPException(status_code=400, detail="Invalid payroll period")

    payroll_run = build_payroll_run(payload, current_user.id)
    create_payroll_run(db, payroll_run)
    db.commit()
    db.refresh(payroll_run)

    audit_event(
        "payroll_run_created",
        {
            "payroll_run_id": payroll_run.id,
            "admin_user_id": current_user.id,
            "period_start": str(payroll_run.period_start),
            "period_end": str(payroll_run.period_end),
        },
    )

    return success_response(
        "Payroll run created",
        {
            "payroll_run_id": payroll_run.id,
            "status": payroll_run.status,
        },
    )


@router.get("/runs/{payroll_run_id}")
def get_admin_payroll_run(
    payroll_run_id: int,
    current_user: User = Depends(require_role(UserRole.ADMIN.value)),
    db: Session = Depends(get_db),
):
    payroll_run = get_payroll_run_by_id(db, payroll_run_id)
    if not payroll_run:
        raise HTTPException(status_code=404, detail="Payroll run not found")

    items = get_payroll_items_by_run_id(db, payroll_run.id)
    data = [
        serialize_payroll_item(item, get_deductions_by_payroll_item_id(db, item.id))
        for item in items
    ]

    return success_response(
        "Payroll run fetched successfully",
        {
            "payroll_run": {
                "id": payroll_run.id,
                "period_start": str(payroll_run.period_start),
                "period_end": str(payroll_run.period_end),
                "status": payroll_run.status,
                "notes": payroll_run.notes,
                "require_verified_attendance": payroll_run.require_verified_attendance,
            },
            "items": data,
        },
    )


@router.post("/runs/{payroll_run_id}/generate")
def generate_admin_payroll_run(
    payroll_run_id: int,
    current_user: User = Depends(require_permission_group("finance_admin")),
    db: Session = Depends(get_db),
):
    check_rate_limit(f"payroll_generate:{current_user.id}", limit=20, window_seconds=300)

    payroll_run = get_payroll_run_by_id(db, payroll_run_id)
    if not payroll_run:
        raise HTTPException(status_code=404, detail="Payroll run not found")

    try:
        ensure_payroll_not_locked(payroll_run)
    except ValueError:
        security_logger.warning(
            "Blocked payroll generation for locked run | payroll_run_id=%s | admin_user_id=%s",
            payroll_run.id,
            current_user.id,
        )
        audit_event(
            "locked_payroll_edit_blocked",
            {
                "payroll_run_id": payroll_run.id,
                "admin_user_id": current_user.id,
                "attempted_action": "generate",
            },
        )
        raise HTTPException(status_code=400, detail="Payroll run is locked")

    existing_items = get_payroll_items_by_run_id(db, payroll_run.id)
    if existing_items:
        raise HTTPException(status_code=400, detail="Payroll run already generated")

    from sqlalchemy import select as sa_select
    from app.models.quote import Quote

    assignments = list(get_active_assignments(db))
    requirement_ids = {a.requirement_id for a in assignments}
    quotes_by_req: dict[int, Quote] = {}
    if requirement_ids:
        for q in db.execute(
            sa_select(Quote).where(Quote.requirement_id.in_(requirement_ids))
        ).scalars().all():
            quotes_by_req[q.requirement_id] = q

    created_items = []
    for assignment in assignments:
        attendance_records = get_attendance_for_assignment_between_dates(
            db=db,
            assignment_id=assignment.id,
            start_date=payroll_run.period_start,
            end_date=payroll_run.period_end,
        )
        summary = calculate_attendance_summary(
            attendance_records,
            strict_mode=payroll_run.require_verified_attendance,
        )
        gross_amount = calculate_gross_amount(
            monthly_salary=assignment.salary_amount,
            attendance_days=summary["attendance_days"],
            half_days=summary["half_days"],
        )
        quote = quotes_by_req.get(assignment.requirement_id)
        margin = calculate_platform_margin(
            client_rate=quote.rate_per_worker if quote else None,
            worker_daily_rate=assignment.salary_amount,
            attendance_days=summary["attendance_days"],
            half_days=summary["half_days"],
        )
        payroll_item = build_payroll_item(
            payroll_run_id=payroll_run.id,
            assignment_id=assignment.id,
            worker_profile_id=assignment.worker_profile_id,
            gross_amount=gross_amount,
            attendance_days=summary["attendance_days"],
            half_days=summary["half_days"],
            absent_days=summary["absent_days"],
            platform_margin=margin,
        )
        create_payroll_item(db, payroll_item)
        created_items.append(payroll_item)

    payroll_run.status = PayrollRunStatus.GENERATED.value
    payroll_run.updated_by_user_id = current_user.id
    db.commit()

    audit_event(
        "payroll_run_generated",
        {
            "payroll_run_id": payroll_run.id,
            "admin_user_id": current_user.id,
            "items_created": len(created_items),
        },
    )

    return success_response(
        "Payroll generated successfully",
        {
            "payroll_run_id": payroll_run.id,
            "status": payroll_run.status,
            "items_created": len(created_items),
        },
    )


@router.get("/runs/{payroll_run_id}/items")
def list_admin_payroll_items(
    payroll_run_id: int,
    current_user: User = Depends(require_role(UserRole.ADMIN.value)),
    db: Session = Depends(get_db),
):
    payroll_run = get_payroll_run_by_id(db, payroll_run_id)
    if not payroll_run:
        raise HTTPException(status_code=404, detail="Payroll run not found")

    items = get_payroll_items_by_run_id(db, payroll_run_id)
    data = [
        serialize_payroll_item(item, get_deductions_by_payroll_item_id(db, item.id))
        for item in items
    ]
    return success_response("Payroll items fetched successfully", data)


@router.post("/deductions")
def add_admin_payroll_deduction(
    payload: PayrollDeductionAddSchema,
    current_user: User = Depends(require_permission_group("finance_admin")),
    db: Session = Depends(get_db),
):
    payroll_item = get_payroll_item_by_id(db, payload.payroll_item_id)
    if not payroll_item:
        raise HTTPException(status_code=404, detail="Payroll item not found")

    payroll_run = get_payroll_run_by_id(db, payroll_item.payroll_run_id)
    if not payroll_run:
        raise HTTPException(status_code=404, detail="Payroll run not found")

    try:
        ensure_payroll_not_locked(payroll_run)
    except ValueError:
        security_logger.warning(
            "Blocked deduction on locked payroll run | payroll_run_id=%s | payroll_item_id=%s | admin_user_id=%s",
            payroll_run.id,
            payroll_item.id,
            current_user.id,
        )
        audit_event(
            "locked_payroll_edit_blocked",
            {
                "payroll_run_id": payroll_run.id,
                "payroll_item_id": payroll_item.id,
                "admin_user_id": current_user.id,
                "attempted_action": "add_deduction",
            },
        )
        raise HTTPException(status_code=400, detail="Payroll run is locked")

    allowed_deductions = {item.value for item in DeductionType}
    if payload.deduction_type not in allowed_deductions:
        raise HTTPException(status_code=400, detail="Invalid deduction type")

    deduction = build_deduction(
        payroll_item_id=payroll_item.id,
        deduction_type=payload.deduction_type,
        amount=payload.amount,
        created_by_user_id=current_user.id,
        reason=payload.reason,
    )
    create_deduction(db, deduction)
    deductions = get_deductions_by_payroll_item_id(db, payroll_item.id)
    deductions_exceed_gross = recalculate_payroll_item(payroll_item, deductions)
    payroll_run.updated_by_user_id = current_user.id

    db.commit()
    db.refresh(deduction)

    audit_event(
        "payroll_deduction_added",
        {
            "payroll_run_id": payroll_run.id,
            "payroll_item_id": payroll_item.id,
            "deduction_id": deduction.id,
            "deduction_type": deduction.deduction_type,
            "amount": deduction.amount,
            "admin_user_id": current_user.id,
        },
    )

    warning = (
        {
            "code": "deductions_exceed_gross",
            "message": "Total deductions exceed gross pay. Net pay has been set to 0.",
        }
        if deductions_exceed_gross
        else None
    )

    return success_response(
        "Deduction added successfully",
        {
            "deduction_id": deduction.id,
            "payroll_item_id": payroll_item.id,
            "total_deduction_amount": payroll_item.total_deduction_amount,
            "net_amount": payroll_item.net_amount,
            "warning": warning,
        },
    )


@router.patch("/runs/{payroll_run_id}/status")
def update_admin_payroll_run_status(
    payroll_run_id: int,
    payload: PayrollRunStatusUpdateSchema,
    current_user: User = Depends(require_permission_group("finance_admin")),
    db: Session = Depends(get_db),
):
    payroll_run = get_payroll_run_by_id(db, payroll_run_id)
    if not payroll_run:
        raise HTTPException(status_code=404, detail="Payroll run not found")

    allowed_statuses = {item.value for item in PayrollRunStatus}
    if payload.status not in allowed_statuses:
        raise HTTPException(status_code=400, detail="Invalid payroll status")

    if payroll_run.status == PayrollRunStatus.LOCKED.value and payload.status != PayrollRunStatus.LOCKED.value:
        security_logger.warning(
            "Blocked status change on locked payroll run | payroll_run_id=%s | attempted_status=%s | admin_user_id=%s",
            payroll_run.id,
            payload.status,
            current_user.id,
        )
        audit_event(
            "locked_payroll_edit_blocked",
            {
                "payroll_run_id": payroll_run.id,
                "admin_user_id": current_user.id,
                "attempted_action": "status_change",
                "attempted_status": payload.status,
            },
        )
        raise HTTPException(status_code=400, detail="Payroll run is locked")

    old_status = payroll_run.status
    payroll_run.status = payload.status
    payroll_run.updated_by_user_id = current_user.id
    db.commit()

    audit_event(
        "payroll_run_status_updated",
        {
            "payroll_run_id": payroll_run.id,
            "old_status": old_status,
            "new_status": payroll_run.status,
            "admin_user_id": current_user.id,
        },
    )

    return success_response(
        "Payroll run status updated successfully",
        {
            "payroll_run_id": payroll_run.id,
            "status": payroll_run.status,
        },
    )


@router.post("/items/{payroll_item_id}/recalculate")
def recalculate_stale_payroll_item(
    payroll_item_id: int,
    current_user: User = Depends(require_permission_group("finance_admin")),
    db: Session = Depends(get_db),
):
    """Recalculate attendance counts and gross/net amounts for a stale, unpaid payroll item."""
    from app.repositories.assignment_repository import get_assignment_by_id

    item = get_payroll_item_by_id(db, payroll_item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Payroll item not found")

    if not item.is_stale:
        raise HTTPException(status_code=400, detail="Payroll item is not stale — no recalculation needed")

    if item.payment_status == PayrollItemPaymentStatus.PAID.value:
        raise HTTPException(status_code=400, detail="Cannot recalculate a paid payroll item")

    payroll_run = get_payroll_run_by_id(db, item.payroll_run_id)
    if not payroll_run:
        raise HTTPException(status_code=404, detail="Payroll run not found")

    try:
        ensure_payroll_not_locked(payroll_run)
    except ValueError:
        raise HTTPException(status_code=400, detail="Cannot recalculate — payroll run is locked")

    assignment = get_assignment_by_id(db, item.assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    attendance_records = get_attendance_for_assignment_between_dates(
        db=db,
        assignment_id=item.assignment_id,
        start_date=payroll_run.period_start,
        end_date=payroll_run.period_end,
    )
    summary = calculate_attendance_summary(
        attendance_records,
        strict_mode=payroll_run.require_verified_attendance,
    )
    gross_amount = calculate_gross_amount(
        monthly_salary=assignment.salary_amount,
        attendance_days=summary["attendance_days"],
        half_days=summary["half_days"],
    )

    deductions = get_deductions_by_payroll_item_id(db, item.id)
    total_deduction = sum(d.amount for d in deductions)

    item.attendance_days = summary["attendance_days"]
    item.half_days = summary["half_days"]
    item.absent_days = summary["absent_days"]
    item.gross_amount = gross_amount
    item.total_deduction_amount = total_deduction
    item.net_amount = max(gross_amount - total_deduction, 0)
    item.is_stale = False

    db.commit()

    audit_event(
        "payroll_item_recalculated",
        {
            "payroll_item_id": item.id,
            "payroll_run_id": item.payroll_run_id,
            "assignment_id": item.assignment_id,
            "admin_user_id": current_user.id,
            "new_gross_amount": item.gross_amount,
            "new_attendance_days": item.attendance_days,
        },
    )

    return success_response(
        "Payroll item recalculated successfully",
        serialize_payroll_item(item, deductions),
    )
