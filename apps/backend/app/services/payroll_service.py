from app.core.attendance_constants import AttendanceStatus
from app.core.payroll_constants import PayrollItemPaymentStatus, PayrollRunStatus
from app.models.payroll_item import PayrollItem
from app.models.payroll_run import PayrollRun
from app.models.worker_deduction import WorkerDeduction


def build_payroll_run(payload, admin_user_id: int) -> PayrollRun:
    return PayrollRun(
        period_start=payload.period_start,
        period_end=payload.period_end,
        status=PayrollRunStatus.DRAFT.value,
        notes=payload.notes,
        created_by_user_id=admin_user_id,
    )


def calculate_attendance_summary(attendance_records: list) -> dict:
    attendance_days = 0
    half_days = 0
    absent_days = 0

    for record in attendance_records:
        if record.status in {
            AttendanceStatus.PRESENT.value,
            AttendanceStatus.LATE.value,
            AttendanceStatus.APPROVED.value,
            AttendanceStatus.CORRECTED.value,
        }:
            attendance_days += 1
        elif record.status == AttendanceStatus.HALF_DAY.value:
            half_days += 1
        elif record.status == AttendanceStatus.ABSENT.value:
            absent_days += 1

    return {
        "attendance_days": attendance_days,
        "half_days": half_days,
        "absent_days": absent_days,
    }


def calculate_gross_amount(monthly_salary: int | None, attendance_days: int, half_days: int) -> int:
    if not monthly_salary or monthly_salary <= 0:
        return 0

    daily_rate = monthly_salary / 30
    gross = (attendance_days * daily_rate) + (half_days * (daily_rate / 2))
    return int(round(gross))


def build_payroll_item(
    payroll_run_id: int,
    assignment_id: int,
    worker_profile_id: int,
    gross_amount: int,
    attendance_days: int,
    half_days: int,
    absent_days: int,
) -> PayrollItem:
    return PayrollItem(
        payroll_run_id=payroll_run_id,
        assignment_id=assignment_id,
        worker_profile_id=worker_profile_id,
        gross_amount=gross_amount,
        total_deduction_amount=0,
        net_amount=gross_amount,
        attendance_days=attendance_days,
        half_days=half_days,
        absent_days=absent_days,
        payment_status=PayrollItemPaymentStatus.PENDING.value,
    )


def build_deduction(
    payroll_item_id: int,
    deduction_type: str,
    amount: int,
    created_by_user_id: int,
    reason: str | None = None,
) -> WorkerDeduction:
    return WorkerDeduction(
        payroll_item_id=payroll_item_id,
        deduction_type=deduction_type,
        amount=amount,
        reason=reason,
        created_by_user_id=created_by_user_id,
    )


def recalculate_payroll_item(item, deductions: list) -> None:
    total_deduction = sum(d.amount for d in deductions)
    item.total_deduction_amount = total_deduction
    item.net_amount = max(item.gross_amount - total_deduction, 0)


def ensure_payroll_not_locked(payroll_run) -> None:
    if payroll_run.status == PayrollRunStatus.LOCKED.value:
        raise ValueError("Payroll run is locked")
