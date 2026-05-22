from datetime import date, datetime
from app.utils.time import utcnow

from sqlalchemy import Date, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class WorkerDocument(Base):
    __tablename__ = "worker_documents"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    # user_id allows storing docs before the WorkerProfile is created (onboarding step 2)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    worker_profile_id: Mapped[int | None] = mapped_column(ForeignKey("worker_profiles.id", ondelete="CASCADE"), nullable=True, index=True)

    document_type: Mapped[str] = mapped_column(String(50), index=True)  # "govt_id" | "selfie"
    # s3_key: the S3 object key; generate signed download URLs from this, never expose the raw key
    s3_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_url: Mapped[str] = mapped_column(Text)  # kept for backwards compat; in S3 mode = reference URL
    verification_status: Mapped[str] = mapped_column(String(50), default="pending", index=True)
    expiry_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)

    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)
