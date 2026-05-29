from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.attendance import Attendance


def create_attendance(db: Session, attendance: Attendance) -> Attendance:
    db.add(attendance)
    db.flush()
    return attendance


def get_attendance_by_id(db: Session, attendance_id: int) -> Attendance | None:
    stmt = select(Attendance).where(Attendance.id == attendance_id)
    return db.execute(stmt).scalar_one_or_none()


def get_attendance_for_assignment_on_date(
    db: Session,
    assignment_id: int,
    attendance_date: date,
) -> Attendance | None:
    stmt = select(Attendance).where(
        Attendance.assignment_id == assignment_id,
        Attendance.attendance_date == attendance_date,
    )
    return db.execute(stmt).scalar_one_or_none()


def get_open_attendance_for_assignment(
    db: Session,
    assignment_id: int,
) -> Attendance | None:
    """Return the most recent attendance record that has been checked in but not yet checked out.

    This handles night shifts that span midnight, where attendance_date may be
    the previous calendar day.
    """
    stmt = (
        select(Attendance)
        .where(
            Attendance.assignment_id == assignment_id,
            Attendance.check_in_time.is_not(None),
            Attendance.check_out_time.is_(None),
        )
        .order_by(Attendance.check_in_time.desc())
        .limit(1)
    )
    return db.execute(stmt).scalar_one_or_none()


def get_attendance_for_worker(
    db: Session,
    worker_profile_id: int,
) -> list[Attendance]:
    stmt = (
        select(Attendance)
        .where(Attendance.worker_profile_id == worker_profile_id)
        .order_by(Attendance.attendance_date.desc())
    )
    return list(db.execute(stmt).scalars().all())


def get_attendance_for_worker_paginated(
    db: Session,
    worker_profile_id: int,
    page: int,
    limit: int,
) -> tuple[list[Attendance], int]:
    """Returns (records, total_count) for the given page."""
    base = select(Attendance).where(Attendance.worker_profile_id == worker_profile_id)
    total = db.execute(select(func.count()).select_from(base.subquery())).scalar_one()
    records = list(
        db.execute(
            base.order_by(Attendance.attendance_date.desc())
            .offset((page - 1) * limit)
            .limit(limit)
        )
        .scalars()
        .all()
    )
    return records, total


def get_attendance_for_assignment(
    db: Session,
    assignment_id: int,
) -> list[Attendance]:
    stmt = (
        select(Attendance)
        .where(Attendance.assignment_id == assignment_id)
        .order_by(Attendance.attendance_date.desc())
    )
    return list(db.execute(stmt).scalars().all())


def get_attendance_for_assignment_between_dates(
    db: Session,
    assignment_id: int,
    start_date: date,
    end_date: date,
) -> list[Attendance]:
    stmt = (
        select(Attendance)
        .where(
            Attendance.assignment_id == assignment_id,
            Attendance.attendance_date >= start_date,
            Attendance.attendance_date <= end_date,
        )
        .order_by(Attendance.attendance_date.asc())
    )
    return list(db.execute(stmt).scalars().all())


def count_attendance_records(db: Session) -> int:
    stmt = select(func.count(Attendance.id))
    return db.execute(stmt).scalar_one()


def count_present_attendance(db: Session) -> int:
    stmt = select(func.count(Attendance.id)).where(Attendance.status == "present")
    return db.execute(stmt).scalar_one()


def count_absent_attendance(db: Session) -> int:
    stmt = select(func.count(Attendance.id)).where(Attendance.status == "absent")
    return db.execute(stmt).scalar_one()
