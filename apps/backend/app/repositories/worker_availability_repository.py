from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.worker_availability import WorkerAvailability


def get_worker_availability(
    db: Session,
    worker_profile_id: int,
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[WorkerAvailability]:
    stmt = select(WorkerAvailability).where(WorkerAvailability.worker_profile_id == worker_profile_id)
    if start_date:
        stmt = stmt.where(WorkerAvailability.availability_date >= start_date)
    if end_date:
        stmt = stmt.where(WorkerAvailability.availability_date <= end_date)
    stmt = stmt.order_by(WorkerAvailability.availability_date.asc())
    return list(db.execute(stmt).scalars().all())


def get_worker_availability_for_date(
    db: Session,
    worker_profile_id: int,
    availability_date: date,
) -> WorkerAvailability | None:
    stmt = select(WorkerAvailability).where(
        WorkerAvailability.worker_profile_id == worker_profile_id,
        WorkerAvailability.availability_date == availability_date,
    )
    return db.execute(stmt).scalar_one_or_none()


def upsert_worker_availability(
    db: Session,
    worker_profile_id: int,
    availability_date: date,
    status: str,
    notes: str | None,
) -> WorkerAvailability:
    existing = get_worker_availability_for_date(db, worker_profile_id, availability_date)
    if existing:
        existing.status = status
        existing.notes = notes
        db.flush()
        return existing

    record = WorkerAvailability(
        worker_profile_id=worker_profile_id,
        availability_date=availability_date,
        status=status,
        notes=notes,
    )
    db.add(record)
    db.flush()
    return record
