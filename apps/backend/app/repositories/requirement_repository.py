from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.statuses import RequirementStatus
from app.models.requirement import Requirement


def create_requirement(db: Session, requirement: Requirement) -> Requirement:
    db.add(requirement)
    db.flush()
    return requirement


def get_requirement_by_id(db: Session, requirement_id: int) -> Requirement | None:
    stmt = select(Requirement).where(Requirement.id == requirement_id)
    return db.execute(stmt).scalar_one_or_none()


def get_requirements_by_client_id(db: Session, client_id: int) -> list[Requirement]:
    stmt = (
        select(Requirement)
        .where(Requirement.client_id == client_id)
        .order_by(Requirement.created_at.desc())
    )
    return list(db.execute(stmt).scalars().all())


def get_all_requirements(db: Session) -> list[Requirement]:
    stmt = select(Requirement).order_by(Requirement.created_at.desc())
    return list(db.execute(stmt).scalars().all())


def get_requirements_paginated_stmt(status_filter: str | None = None):
    """Return a select statement for requirements, optionally filtered by status."""
    stmt = select(Requirement).order_by(Requirement.created_at.desc())
    if status_filter:
        stmt = stmt.where(Requirement.status == status_filter)
    return stmt


def count_requirements(db: Session) -> int:
    stmt = select(func.count(Requirement.id))
    return db.execute(stmt).scalar_one()


def count_open_requirements(db: Session) -> int:
    stmt = select(func.count(Requirement.id)).where(
        Requirement.status.in_(
            [
                RequirementStatus.SUBMITTED.value,
                RequirementStatus.UNDER_REVIEW.value,
                RequirementStatus.QUOTED.value,
                RequirementStatus.APPROVED.value,
            ]
        )
    )
    return db.execute(stmt).scalar_one()
