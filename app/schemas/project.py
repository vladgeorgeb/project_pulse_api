from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.domain.constants import MAX_PROJECT_BUDGET_CENTS, MAX_TASK_ESTIMATE_MINUTES
from app.domain.enums import (
    BillingCycle,
    BillingStatus,
    ContractType,
    PaymentStatus,
    Priority,
    ProjectStatus,
    TaskStatus,
)

MONTHLY_AMOUNT_REQUIRED_MESSAGE = (
    "monthly_amount is required for monthly_retainer and full_time_monthly projects."
)


def payment_status_to_billing_status(status: PaymentStatus) -> BillingStatus:
    if status == PaymentStatus.PAID:
        return BillingStatus.PAID
    if status == PaymentStatus.OVERDUE:
        return BillingStatus.OVERDUE
    if status == PaymentStatus.NOT_STARTED:
        return BillingStatus.NOT_BILLABLE
    return BillingStatus.UNPAID


def billing_status_to_payment_status(status: BillingStatus) -> PaymentStatus:
    if status == BillingStatus.PAID:
        return PaymentStatus.PAID
    if status == BillingStatus.OVERDUE:
        return PaymentStatus.OVERDUE
    if status == BillingStatus.NOT_BILLABLE:
        return PaymentStatus.NOT_STARTED
    return PaymentStatus.PENDING


class ProjectBillingFields(BaseModel):
    contract_type: ContractType = ContractType.FIXED_PRICE
    billing_cycle: BillingCycle = BillingCycle.MONTHLY
    billing_status: BillingStatus | None = None
    payment_status: PaymentStatus | None = None
    billing_currency: str = Field(default="USD", min_length=3, max_length=3)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    agreed_amount: Decimal | None = Field(default=None, ge=0)
    monthly_rate: Decimal | None = Field(default=None, ge=0)
    monthly_amount: Decimal | None = Field(default=None, ge=0)
    payment_due_day: int | None = Field(default=None, ge=1, le=31)
    next_payment_due_date: date | None = None
    paid_at: datetime | None = None
    billing_notes: str | None = Field(default=None, max_length=2_000)

    @model_validator(mode="after")
    def normalize_billing(self) -> "ProjectBillingFields":
        currency = self.currency or self.billing_currency
        self.currency = currency.upper()
        self.billing_currency = self.currency
        amount = (
            self.monthly_amount
            if self.monthly_amount is not None
            else self.monthly_rate
        )
        self.monthly_amount = amount
        self.monthly_rate = amount
        if self.contract_type == ContractType.INTERNAL:
            self.billing_status = BillingStatus.NOT_BILLABLE
            self.payment_status = PaymentStatus.NOT_STARTED
        elif self.payment_status is not None:
            self.billing_status = payment_status_to_billing_status(self.payment_status)
        elif self.billing_status is None:
            self.billing_status = BillingStatus.UNPAID
            self.payment_status = PaymentStatus.PENDING
        else:
            self.payment_status = billing_status_to_payment_status(self.billing_status)
        if (
            self.contract_type
            in {ContractType.MONTHLY_RETAINER, ContractType.FULL_TIME_MONTHLY}
            and self.monthly_amount is None
        ):
            raise ValueError(MONTHLY_AMOUNT_REQUIRED_MESSAGE)
        return self


class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    title: str
    description: str | None
    status: TaskStatus
    priority: Priority
    estimated_minutes: int
    actual_minutes: int
    due_date: date | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime


class TaskCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    description: str | None = Field(default=None, max_length=2_000)
    status: TaskStatus = TaskStatus.TODO
    priority: Priority = Priority.MEDIUM
    estimated_minutes: int = Field(default=0, ge=0, le=MAX_TASK_ESTIMATE_MINUTES)
    actual_minutes: int = Field(default=0, ge=0, le=MAX_TASK_ESTIMATE_MINUTES)
    due_date: date | None = None


class TaskUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=160)
    description: str | None = Field(default=None, max_length=2_000)
    status: TaskStatus | None = None
    priority: Priority | None = None
    estimated_minutes: int | None = Field(
        default=None, ge=0, le=MAX_TASK_ESTIMATE_MINUTES
    )
    actual_minutes: int | None = Field(default=None, ge=0, le=MAX_TASK_ESTIMATE_MINUTES)
    due_date: date | None = None


class TaskCompleteRequest(BaseModel):
    actual_minutes: int | None = Field(default=None, ge=0, le=MAX_TASK_ESTIMATE_MINUTES)


class ProjectCreateRequest(ProjectBillingFields):
    title: str = Field(min_length=1, max_length=120)
    client_name: str = Field(min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=4_000)
    status: ProjectStatus = ProjectStatus.PLANNED
    priority: Priority = Priority.MEDIUM
    budget_cents: int = Field(default=0, ge=0, le=MAX_PROJECT_BUDGET_CENTS)
    hourly_rate_cents: int = Field(default=0, ge=0, le=1_000_000)
    deadline: date | None = None


class ProjectUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=120)
    client_name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=4_000)
    status: ProjectStatus | None = None
    priority: Priority | None = None
    budget_cents: int | None = Field(default=None, ge=0, le=MAX_PROJECT_BUDGET_CENTS)
    hourly_rate_cents: int | None = Field(default=None, ge=0, le=1_000_000)
    contract_type: ContractType | None = None
    billing_cycle: BillingCycle | None = None
    billing_status: BillingStatus | None = None
    payment_status: PaymentStatus | None = None
    billing_currency: str | None = Field(default=None, min_length=3, max_length=3)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    agreed_amount: Decimal | None = Field(default=None, ge=0)
    monthly_rate: Decimal | None = Field(default=None, ge=0)
    monthly_amount: Decimal | None = Field(default=None, ge=0)
    payment_due_day: int | None = Field(default=None, ge=1, le=31)
    next_payment_due_date: date | None = None
    paid_at: datetime | None = None
    billing_notes: str | None = Field(default=None, max_length=2_000)
    deadline: date | None = None
    archived: bool | None = None

    @model_validator(mode="after")
    def normalize_billing(self) -> "ProjectUpdateRequest":
        currency = self.currency or self.billing_currency
        if currency is not None:
            self.currency = currency.upper()
            self.billing_currency = self.currency
        amount = (
            self.monthly_amount
            if self.monthly_amount is not None
            else self.monthly_rate
        )
        if amount is not None:
            self.monthly_amount = amount
            self.monthly_rate = amount
        if self.contract_type == ContractType.INTERNAL:
            self.billing_status = BillingStatus.NOT_BILLABLE
            self.payment_status = PaymentStatus.NOT_STARTED
        elif self.payment_status is not None:
            self.billing_status = payment_status_to_billing_status(self.payment_status)
        return self


class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    workspace_id: int
    title: str
    client_name: str
    description: str | None
    status: ProjectStatus
    priority: Priority
    budget_cents: int
    hourly_rate_cents: int
    contract_type: ContractType
    billing_cycle: BillingCycle
    billing_status: BillingStatus
    payment_status: PaymentStatus
    billing_currency: str
    currency: str
    agreed_amount: Decimal | None
    monthly_rate: Decimal | None
    monthly_amount: Decimal | None
    payment_due_day: int | None
    next_payment_due_date: date | None
    paid_at: datetime | None
    billing_notes: str | None
    deadline: date | None
    archived: bool
    created_at: datetime
    updated_at: datetime
    progress_percent: int
    estimated_hours: float
    actual_hours: float
    tasks: list[TaskResponse]


class ProjectQueryParams(BaseModel):
    status: ProjectStatus | None = None
    priority: Priority | None = None
    client_name: str | None = None
    search: str | None = None
    min_budget_cents: int | None = Field(default=None, ge=0)
    max_budget_cents: int | None = Field(default=None, ge=0)
    due_before: date | None = None
    due_after: date | None = None
    overdue_only: bool = False
    include_archived: bool = False

    @model_validator(mode="after")
    def validate_ranges(self) -> "ProjectQueryParams":
        if (
            self.min_budget_cents is not None
            and self.max_budget_cents is not None
            and self.min_budget_cents > self.max_budget_cents
        ):
            raise ValueError("min_budget_cents cannot exceed max_budget_cents.")
        if (
            self.due_after is not None
            and self.due_before is not None
            and self.due_after > self.due_before
        ):
            raise ValueError("due_after cannot be later than due_before.")
        return self


class ProjectActionResponse(BaseModel):
    message: str
    project: ProjectResponse
