from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.admin_profile import AdminProfile
from app.models.client_profile import ClientProfile
from app.models.worker_document import WorkerDocument
from app.models.worker_profile import WorkerProfile


def get_client_profile_by_user_id(db: Session, user_id: int) -> ClientProfile | None:
    stmt = select(ClientProfile).where(ClientProfile.user_id == user_id)
    return db.execute(stmt).scalar_one_or_none()


def get_client_profile_by_id(db: Session, profile_id: int) -> ClientProfile | None:
    stmt = select(ClientProfile).where(ClientProfile.id == profile_id)
    return db.execute(stmt).scalar_one_or_none()


def create_client_profile(db: Session, profile: ClientProfile) -> ClientProfile:
    db.add(profile)
    db.flush()
    return profile


def get_worker_profile_by_user_id(db: Session, user_id: int) -> WorkerProfile | None:
    stmt = select(WorkerProfile).where(WorkerProfile.user_id == user_id)
    return db.execute(stmt).scalar_one_or_none()


def get_worker_profile_by_id(db: Session, worker_profile_id: int) -> WorkerProfile | None:
    stmt = select(WorkerProfile).where(WorkerProfile.id == worker_profile_id)
    return db.execute(stmt).scalar_one_or_none()


def get_all_worker_profiles(db: Session) -> list[WorkerProfile]:
    stmt = select(WorkerProfile).order_by(WorkerProfile.created_at.desc())
    return list(db.execute(stmt).scalars().all())


def get_workers_paginated_stmt(
    verification_status: str | None = None,
    city: str | None = None,
    is_available: bool | None = None,
    category: str | None = None,
):
    """Return a select statement for worker profiles, with optional filters."""
    stmt = select(WorkerProfile).order_by(WorkerProfile.created_at.desc())
    if verification_status:
        stmt = stmt.where(WorkerProfile.verification_status == verification_status)
    if city:
        stmt = stmt.where(WorkerProfile.city.ilike(f"%{city}%"))
    if is_available is not None:
        stmt = stmt.where(WorkerProfile.is_available == is_available)
    if category:
        stmt = stmt.where(WorkerProfile.category.ilike(f"%{category}%"))
    return stmt


def get_all_client_profiles(db: Session) -> list[ClientProfile]:
    stmt = select(ClientProfile).order_by(ClientProfile.created_at.desc())
    return list(db.execute(stmt).scalars().all())


def get_clients_paginated_stmt():
    """Return a select statement for client profiles."""
    return select(ClientProfile).order_by(ClientProfile.created_at.desc())


def create_worker_profile(db: Session, profile: WorkerProfile) -> WorkerProfile:
    db.add(profile)
    db.flush()
    return profile


def create_worker_document(db: Session, document: WorkerDocument) -> WorkerDocument:
    db.add(document)
    db.flush()
    return document


def get_worker_documents_by_profile_id(db: Session, worker_profile_id: int) -> list[WorkerDocument]:
    stmt = select(WorkerDocument).where(WorkerDocument.worker_profile_id == worker_profile_id)
    return list(db.execute(stmt).scalars().all())


def get_admin_profile_by_user_id(db: Session, user_id: int) -> AdminProfile | None:
    stmt = select(AdminProfile).where(AdminProfile.user_id == user_id)
    return db.execute(stmt).scalar_one_or_none()


def create_admin_profile(db: Session, profile: AdminProfile) -> AdminProfile:
    db.add(profile)
    db.flush()
    return profile


def count_workers(db: Session) -> int:
    stmt = select(func.count(WorkerProfile.id))
    return db.execute(stmt).scalar_one()


def count_available_workers(db: Session) -> int:
    stmt = select(func.count(WorkerProfile.id)).where(WorkerProfile.is_available == True)  # noqa: E712
    return db.execute(stmt).scalar_one()
