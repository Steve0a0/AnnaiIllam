from datetime import datetime
from app.utils.time import utcnow

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class ComplaintSlaPolicy(Base):
    __tablename__ = "complaint_sla_policies"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    severity: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    response_hours: Mapped[int] = mapped_column(Integer)
    resolution_hours: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)
