from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.enums import ContractType, PaymentCadence, Priority, ProjectStatus
from app.models.base import Base


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    workspace_id: Mapped[int] = mapped_column(
        ForeignKey("workspaces.id"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    client_name: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default=ProjectStatus.PLANNED.value, index=True
    )
    priority: Mapped[str] = mapped_column(
        String(32), nullable=False, default=Priority.MEDIUM.value, index=True
    )
    contract_type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=ContractType.FIXED_PRICE.value,
        server_default=ContractType.FIXED_PRICE.value,
        index=True,
    )
    billing_currency: Mapped[str] = mapped_column(
        String(3), nullable=False, default="USD", server_default="USD"
    )
    hourly_rate_cents: Mapped[int | None] = mapped_column(Integer, nullable=True)
    expected_hours_per_week: Mapped[Decimal | None] = mapped_column(
        Numeric(7, 2), nullable=True
    )
    monthly_rate_cents: Mapped[int | None] = mapped_column(Integer, nullable=True)
    fixed_price_cents: Mapped[int | None] = mapped_column(Integer, nullable=True)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    estimated_end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    deadline: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    payment_cadence: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=PaymentCadence.MANUAL.value,
        server_default=PaymentCadence.MANUAL.value,
    )
    billing_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    workspace = relationship("Workspace", back_populates="projects")
    tasks = relationship(
        "Task",
        back_populates="project",
        cascade="all, delete-orphan",
        order_by="Task.id",
    )
    payment_records = relationship(
        "PaymentRecord",
        back_populates="project",
        cascade="all, delete-orphan",
        order_by="PaymentRecord.id",
    )
