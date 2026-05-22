from datetime import date, datetime
from app.utils.time import utcnow

from sqlalchemy import Date, DateTime, Float, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class Attendance(Base):
    __tablename__ = "attendance"
    __table_args__ = (
        UniqueConstraint("assignment_id", "attendance_date", name="uq_attendance_assignment_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    assignment_id: Mapped[int] = mapped_column(
        ForeignKey("assignments.id", ondelete="CASCADE"),
        index=True,
    )
    worker_profile_id: Mapped[int] = mapped_column(
        ForeignKey("worker_profiles.id", ondelete="CASCADE"),
        index=True,
    )

    attendance_date: Mapped[date] = mapped_column(Date, index=True)
    status: Mapped[str] = mapped_column(String(50), default="present", index=True)

    check_in_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    check_out_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    check_in_latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    check_in_longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    check_out_latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    check_out_longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    check_in_selfie_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    check_out_selfie_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    qr_code: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)

    marked_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=True,
    )

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)
