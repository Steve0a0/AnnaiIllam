from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.complaint_constants import ComplaintStatus
from app.models.complaint import Complaint
from app.models.replacement import Replacement


def create_complaint(db: Session, complaint: Complaint) -> Complaint:
    db.add(complaint)
    db.flush()
    return complaint


def get_complaint_by_id(db: Session, complaint_id: int) -> Complaint | None:
    stmt = select(Complaint).where(Complaint.id == complaint_id)
    return db.execute(stmt).scalar_one_or_none()


def get_complaints_by_requirement_id(db: Session, requirement_id: int) -> list[Complaint]:
    stmt = (
        select(Complaint)
        .where(Complaint.requirement_id == requirement_id)
        .order_by(Complaint.created_at.desc())
    )
    return list(db.execute(stmt).scalars().all())


def get_all_complaints(db: Session) -> list[Complaint]:
    stmt = select(Complaint).order_by(Complaint.created_at.desc())
    return list(db.execute(stmt).scalars().all())


def get_complaints_paginated_stmt(status_filter: str | None = None):
    """Return a select statement for complaints, optionally filtered by status."""
    stmt = select(Complaint).order_by(Complaint.created_at.desc())
    if status_filter:
        stmt = stmt.where(Complaint.status == status_filter)
    return stmt


def create_replacement(db: Session, replacement: Replacement) -> Replacement:
    db.add(replacement)
    db.flush()
    return replacement


def get_replacement_by_id(db: Session, replacement_id: int) -> Replacement | None:
    stmt = select(Replacement).where(Replacement.id == replacement_id)
    return db.execute(stmt).scalar_one_or_none()


def get_replacements_by_complaint_id(db: Session, complaint_id: int) -> list[Replacement]:
    stmt = (
        select(Replacement)
        .where(Replacement.complaint_id == complaint_id)
        .order_by(Replacement.created_at.desc())
    )
    return list(db.execute(stmt).scalars().all())


def get_all_replacements_paginated_stmt(status_filter: str | None = None):
    """Return a select statement for replacements, optionally filtered by status."""
    stmt = select(Replacement).order_by(Replacement.created_at.desc())
    if status_filter:
        stmt = stmt.where(Replacement.status == status_filter)
    return stmt


def count_open_complaints(db: Session) -> int:
    stmt = select(func.count(Complaint.id)).where(
        Complaint.status.in_(
            [
                ComplaintStatus.OPEN.value,
                ComplaintStatus.UNDER_REVIEW.value,
            ]
        )
    )
    return db.execute(stmt).scalar_one()


def count_all_complaints(db: Session) -> int:
    stmt = select(func.count(Complaint.id))
    return db.execute(stmt).scalar_one()
