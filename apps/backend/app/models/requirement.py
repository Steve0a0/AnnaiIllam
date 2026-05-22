from datetime import date, datetime
from app.utils.time import utcnow

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class Requirement(Base):
    __tablename__ = "requirements"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("client_profiles.id", ondelete="CASCADE"), index=True)

    category: Mapped[str] = mapped_column(String(100), index=True)
    subcategory: Mapped[str | None] = mapped_column(String(100), nullable=True)
    number_of_workers: Mapped[int] = mapped_column(Integer)
    work_location: Mapped[str] = mapped_column(String(255))
    city: Mapped[str] = mapped_column(String(100), index=True)
    state: Mapped[str] = mapped_column(String(100), index=True)

    start_date: Mapped[date] = mapped_column(Date)
    duration_days: Mapped[int] = mapped_column(Integer)
    shift_details: Mapped[str | None] = mapped_column(String(255), nullable=True)

    food_required: Mapped[bool] = mapped_column(Boolean, default=False)
    accommodation_required: Mapped[bool] = mapped_column(Boolean, default=False)

    budget_amount: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Geofence — when site_latitude and site_longitude are set, check-in is
    # validated against these coordinates.  geofence_radius_meters defaults to
    # 2 000 m (2 km); set to 0 or NULL to disable the radius check.
    site_latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    site_longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    geofence_radius_meters: Mapped[int | None] = mapped_column(Integer, nullable=True, default=2000)

    status: Mapped[str] = mapped_column(String(50), default="submitted", index=True)

    created_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), index=True)
    updated_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)
