from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    false,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.enums import (
    BillingCycle,
    BillingStatus,
    ContractType,
    Priority,
    ProjectStatus,
)
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
    budget_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    hourly_rate_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    contract_type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=ContractType.FIXED_PRICE.value,
        server_default=ContractType.FIXED_PRICE.value,
        index=True,
    )
    billing_status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=BillingStatus.UNPAID.value,
        server_default=BillingStatus.UNPAID.value,
        index=True,
    )
    billing_currency: Mapped[str] = mapped_column(
        String(3), nullable=False, default="USD", server_default="USD"
    )
    billing_cycle: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=BillingCycle.MONTHLY.value,
        server_default=BillingCycle.MONTHLY.value,
    )
    agreed_amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    monthly_rate: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    billing_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    deadline: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    archived: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=false(), index=True
    )
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
