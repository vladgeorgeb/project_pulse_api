from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.enums import PaymentRecordStatus
from app.models.base import Base


class PaymentRecord(Base):
    __tablename__ = "payment_records"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    invoice_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(
        String(3), nullable=False, default="USD", server_default="USD"
    )
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=PaymentRecordStatus.PENDING.value,
        server_default=PaymentRecordStatus.PENDING.value,
        index=True,
    )
    method: Mapped[str | None] = mapped_column(String(80), nullable=True)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    period_start: Mapped[date | None] = mapped_column(Date, nullable=True)
    period_end: Mapped[date | None] = mapped_column(Date, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    project = relationship("Project", back_populates="payment_records")

    @property
    def is_overdue(self) -> bool:
        return (
            self.due_date is not None
            and self.due_date < date.today()
            and self.status
            not in {
                PaymentRecordStatus.PAID.value,
                PaymentRecordStatus.CANCELLED.value,
            }
        )
