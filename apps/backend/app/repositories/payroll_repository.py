from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.payroll_constants import PayrollRunStatus
from app.models.payroll_item import PayrollItem
from app.models.payroll_run import PayrollRun
from app.models.worker_deduction import WorkerDeduction


def create_payroll_run(db: Session, payroll_run: PayrollRun) -> PayrollRun:
    db.add(payroll_run)
    db.flush()
    return payroll_run


def get_payroll_run_by_id(db: Session, payroll_run_id: int) -> PayrollRun | None:
    stmt = select(PayrollRun).where(PayrollRun.id == payroll_run_id)
    return db.execute(stmt).scalar_one_or_none()


def create_payroll_item(db: Session, payroll_item: PayrollItem) -> PayrollItem:
    db.add(payroll_item)
    db.flush()
    return payroll_item


def get_payroll_items_by_run_id(db: Session, payroll_run_id: int) -> list[PayrollItem]:
    stmt = (
        select(PayrollItem)
        .where(PayrollItem.payroll_run_id == payroll_run_id)
        .order_by(PayrollItem.id.asc())
    )
    return list(db.execute(stmt).scalars().all())


def get_payroll_item_by_id(db: Session, payroll_item_id: int) -> PayrollItem | None:
    stmt = select(PayrollItem).where(PayrollItem.id == payroll_item_id)
    return db.execute(stmt).scalar_one_or_none()


def get_payroll_items_by_worker_profile_id(db: Session, worker_profile_id: int) -> list[PayrollItem]:
    stmt = (
        select(PayrollItem)
        .where(PayrollItem.worker_profile_id == worker_profile_id)
        .order_by(PayrollItem.created_at.desc())
    )
    return list(db.execute(stmt).scalars().all())


def create_deduction(db: Session, deduction: WorkerDeduction) -> WorkerDeduction:
    db.add(deduction)
    db.flush()
    return deduction


def get_deductions_by_payroll_item_id(db: Session, payroll_item_id: int) -> list[WorkerDeduction]:
    stmt = select(WorkerDeduction).where(WorkerDeduction.payroll_item_id == payroll_item_id)
    return list(db.execute(stmt).scalars().all())


def get_all_payroll_runs(db: Session) -> list[PayrollRun]:
    stmt = select(PayrollRun).order_by(PayrollRun.created_at.desc())
    return list(db.execute(stmt).scalars().all())


def count_payroll_runs(db: Session) -> int:
    stmt = select(func.count(PayrollRun.id))
    return db.execute(stmt).scalar_one()


def count_payroll_items(db: Session) -> int:
    stmt = select(func.count(PayrollItem.id))
    return db.execute(stmt).scalar_one()


def get_locked_payroll_run_for_assignment_date(
    db: Session,
    assignment_id: int,
    attendance_date,
) -> PayrollRun | None:
    stmt = (
        select(PayrollRun)
        .join(PayrollItem, PayrollItem.payroll_run_id == PayrollRun.id)
        .where(
            PayrollItem.assignment_id == assignment_id,
            PayrollRun.status == PayrollRunStatus.LOCKED.value,
            PayrollRun.period_start <= attendance_date,
            PayrollRun.period_end >= attendance_date,
        )
        .order_by(PayrollRun.created_at.desc())
    )
    return db.execute(stmt).scalars().first()
