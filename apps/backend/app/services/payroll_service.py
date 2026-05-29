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
        require_verified_attendance=payload.require_verified_attendance,
        created_by_user_id=admin_user_id,
    )


VERIFIED_STATUSES = {
    AttendanceStatus.APPROVED.value,
    AttendanceStatus.CORRECTED.value,
}

ALL_PRESENT_STATUSES = {
    AttendanceStatus.PRESENT.value,
    AttendanceStatus.LATE.value,
    AttendanceStatus.APPROVED.value,
    AttendanceStatus.CORRECTED.value,
}


def calculate_attendance_summary(
    attendance_records: list,
    strict_mode: bool = False,
) -> dict:
    """Tally attendance days.

    When strict_mode=True only approved/corrected records are counted as present;
    unverified present/late records are ignored (not added to absent_days either).
    When strict_mode=False the existing behavior is preserved.
    """
    attendance_days = 0
    half_days = 0
    absent_days = 0

    present_statuses = VERIFIED_STATUSES if strict_mode else ALL_PRESENT_STATUSES

    for record in attendance_records:
        if record.status in present_statuses:
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
    """salary_amount is stored as a daily rate (matches rate_per_worker in the quote)."""
    if not monthly_salary or monthly_salary <= 0:
        return 0

    daily_rate = monthly_salary  # salary_amount = per-day rate
    gross = (attendance_days * daily_rate) + (half_days * (daily_rate / 2))
    return int(round(gross))


def calculate_platform_margin(
    client_rate: int | None,
    worker_daily_rate: int | None,
    attendance_days: int,
    half_days: int,
) -> int | None:
    """Returns (client_rate - worker_daily_rate) × payable_days.
    Returns None when either rate is unavailable (e.g. no approved quote).
    Result may be negative if worker salary exceeds the client rate.
    """
    if client_rate is None or worker_daily_rate is None:
        return None
    payable_days = attendance_days + half_days * 0.5
    return int(round((client_rate - worker_daily_rate) * payable_days))


def build_payroll_item(
    payroll_run_id: int,
    assignment_id: int,
    worker_profile_id: int,
    gross_amount: int,
    attendance_days: int,
    half_days: int,
    absent_days: int,
    platform_margin: int | None = None,
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
        platform_margin=platform_margin,
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


def recalculate_payroll_item(item, deductions: list) -> bool:
    """Recalculates totals in-place. Returns True if total deductions exceed gross pay."""
    total_deduction = sum(d.amount for d in deductions)
    item.total_deduction_amount = total_deduction
    item.net_amount = max(item.gross_amount - total_deduction, 0)
    return total_deduction > item.gross_amount


def ensure_payroll_not_locked(payroll_run) -> None:
    if payroll_run.status == PayrollRunStatus.LOCKED.value:
        raise ValueError("Payroll run is locked")
