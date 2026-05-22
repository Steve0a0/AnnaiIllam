from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.assignment_constants import AssignmentStatus
from app.models.assignment import Assignment


def create_assignment(db: Session, assignment: Assignment) -> Assignment:
    db.add(assignment)
    db.flush()
    return assignment


def get_assignment_by_id(db: Session, assignment_id: int) -> Assignment | None:
    stmt = select(Assignment).where(Assignment.id == assignment_id)
    return db.execute(stmt).scalar_one_or_none()


def get_all_assignments(db: Session) -> list[Assignment]:
    stmt = select(Assignment).order_by(Assignment.assigned_at.desc())
    return list(db.execute(stmt).scalars().all())


def get_assignments_paginated_stmt(requirement_id: int | None = None, status_filter: str | None = None):
    """Return a select statement for assignments with optional filters."""
    stmt = select(Assignment).order_by(Assignment.assigned_at.desc())
    if requirement_id:
        stmt = stmt.where(Assignment.requirement_id == requirement_id)
    if status_filter:
        stmt = stmt.where(Assignment.status == status_filter)
    return stmt


def get_assignments_by_requirement_id(db: Session, requirement_id: int) -> list[Assignment]:
    stmt = (
        select(Assignment)
        .where(Assignment.requirement_id == requirement_id)
        .order_by(Assignment.assigned_at.desc())
    )
    return list(db.execute(stmt).scalars().all())


def get_assignments_by_worker_profile_id(db: Session, worker_profile_id: int) -> list[Assignment]:
    stmt = (
        select(Assignment)
        .where(Assignment.worker_profile_id == worker_profile_id)
        .order_by(Assignment.assigned_at.desc())
    )
    return list(db.execute(stmt).scalars().all())


def get_active_assignments_by_worker_profile_id(db: Session, worker_profile_id: int) -> list[Assignment]:
    stmt = (
        select(Assignment)
        .where(
            Assignment.worker_profile_id == worker_profile_id,
            Assignment.status.in_(
                [
                    AssignmentStatus.ASSIGNED.value,
                    AssignmentStatus.ACCEPTED.value,
                    AssignmentStatus.ACTIVE.value,
                ]
            ),
        )
        .order_by(Assignment.assigned_at.desc())
    )
    return list(db.execute(stmt).scalars().all())


def find_existing_assignment(
    db: Session,
    requirement_id: int,
    worker_profile_id: int,
) -> Assignment | None:
    stmt = select(Assignment).where(
        Assignment.requirement_id == requirement_id,
        Assignment.worker_profile_id == worker_profile_id,
    )
    return db.execute(stmt).scalar_one_or_none()


def count_open_assignments_for_requirement(db: Session, requirement_id: int) -> int:
    stmt = select(func.count(Assignment.id)).where(
        Assignment.requirement_id == requirement_id,
        Assignment.status.in_(
            [
                AssignmentStatus.ASSIGNED.value,
                AssignmentStatus.ACCEPTED.value,
                AssignmentStatus.ACTIVE.value,
            ]
        ),
    )
    return db.execute(stmt).scalar_one()


def get_active_assignments(db: Session) -> list[Assignment]:
    stmt = select(Assignment).where(
        Assignment.status.in_(
            [
                AssignmentStatus.ASSIGNED.value,
                AssignmentStatus.ACCEPTED.value,
                AssignmentStatus.ACTIVE.value,
                AssignmentStatus.COMPLETED.value,
            ]
        )
    )
    return list(db.execute(stmt).scalars().all())


def count_assignments(db: Session) -> int:
    stmt = select(func.count(Assignment.id))
    return db.execute(stmt).scalar_one()


def count_active_assignments(db: Session) -> int:
    stmt = select(func.count(Assignment.id)).where(
        Assignment.status.in_(
            [
                AssignmentStatus.ASSIGNED.value,
                AssignmentStatus.ACCEPTED.value,
                AssignmentStatus.ACTIVE.value,
            ]
        )
    )
    return db.execute(stmt).scalar_one()
