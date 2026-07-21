from datetime import datetime
from app.utils.time import utcnow

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class ClientPayment(Base):
    __tablename__ = "client_payments"
    __table_args__ = (
        UniqueConstraint("gateway_order_id", name="uq_client_payments_gateway_order_id"),
        UniqueConstraint("gateway_payment_id", name="uq_client_payments_gateway_payment_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    client_id: Mapped[int] = mapped_column(
        ForeignKey("client_profiles.id", ondelete="CASCADE"),
        index=True,
    )
    requirement_id: Mapped[int] = mapped_column(
        ForeignKey("requirements.id", ondelete="CASCADE"),
        index=True,
    )

    amount: Mapped[int] = mapped_column(Integer)
    purpose: Mapped[str] = mapped_column(String(50), default="adjustment", index=True)
    payment_model: Mapped[str] = mapped_column(String(50), index=True)
    payment_mode: Mapped[str] = mapped_column(String(50), index=True)
    payment_status: Mapped[str] = mapped_column(String(50), default="pending", index=True)

    gateway_order_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    gateway_payment_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    gateway_signature: Mapped[str | None] = mapped_column(String(255), nullable=True)

    reference_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    recorded_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=True,
    )

    paid_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)
