from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.client_payment import ClientPayment
from app.models.worker_payout import WorkerPayout


def create_client_payment(db: Session, payment: ClientPayment) -> ClientPayment:
    db.add(payment)
    db.flush()
    return payment


def get_client_payment_by_id(db: Session, payment_id: int) -> ClientPayment | None:
    stmt = select(ClientPayment).where(ClientPayment.id == payment_id)
    return db.execute(stmt).scalar_one_or_none()


def get_client_payments_by_requirement_id(db: Session, requirement_id: int) -> list[ClientPayment]:
    stmt = (
        select(ClientPayment)
        .where(ClientPayment.requirement_id == requirement_id)
        .order_by(ClientPayment.created_at.desc())
    )
    return list(db.execute(stmt).scalars().all())


def get_client_payments_by_client_id(db: Session, client_id: int) -> list[ClientPayment]:
    stmt = (
        select(ClientPayment)
        .where(ClientPayment.client_id == client_id)
        .order_by(ClientPayment.created_at.desc())
    )
    return list(db.execute(stmt).scalars().all())


def get_client_payment_by_gateway_order_id(db: Session, gateway_order_id: str) -> ClientPayment | None:
    stmt = select(ClientPayment).where(ClientPayment.gateway_order_id == gateway_order_id)
    return db.execute(stmt).scalar_one_or_none()


def create_worker_payout(db: Session, payout: WorkerPayout) -> WorkerPayout:
    db.add(payout)
    db.flush()
    return payout


def get_worker_payout_by_id(db: Session, payout_id: int) -> WorkerPayout | None:
    stmt = select(WorkerPayout).where(WorkerPayout.id == payout_id)
    return db.execute(stmt).scalar_one_or_none()


def get_worker_payouts_by_payroll_item_id(db: Session, payroll_item_id: int) -> list[WorkerPayout]:
    stmt = (
        select(WorkerPayout)
        .where(WorkerPayout.payroll_item_id == payroll_item_id)
        .order_by(WorkerPayout.created_at.desc())
    )
    return list(db.execute(stmt).scalars().all())


def get_worker_payouts_by_worker_profile_id(db: Session, worker_profile_id: int) -> list[WorkerPayout]:
    stmt = (
        select(WorkerPayout)
        .where(WorkerPayout.worker_profile_id == worker_profile_id)
        .order_by(WorkerPayout.created_at.desc())
    )
    return list(db.execute(stmt).scalars().all())


def count_client_payments(db: Session) -> int:
    stmt = select(func.count(ClientPayment.id))
    return db.execute(stmt).scalar_one()


def count_worker_payouts(db: Session) -> int:
    stmt = select(func.count(WorkerPayout.id))
    return db.execute(stmt).scalar_one()


def sum_client_payments_paid(db: Session) -> int:
    stmt = select(func.coalesce(func.sum(ClientPayment.amount), 0)).where(
        ClientPayment.payment_status == "paid"
    )
    return db.execute(stmt).scalar_one()


def get_all_client_payments(
    db: Session,
    status: str | None = None,
    limit: int = 200,
) -> list[ClientPayment]:
    stmt = (
        select(ClientPayment)
        .order_by(ClientPayment.created_at.desc())
        .limit(limit)
    )
    if status:
        stmt = stmt.where(ClientPayment.payment_status == status)
    return list(db.execute(stmt).scalars().all())


def sum_worker_payouts_paid(db: Session) -> int:
    stmt = select(func.coalesce(func.sum(WorkerPayout.amount), 0)).where(
        WorkerPayout.payout_status == "paid"
    )
    return db.execute(stmt).scalar_one()
