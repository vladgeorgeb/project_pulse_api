from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.domain.constants import MAX_PROJECT_BUDGET_CENTS, MAX_TASK_ESTIMATE_MINUTES
from app.domain.enums import (
    BillingCycle,
    BillingStatus,
    ContractType,
    PaymentRecordStatus,
    Priority,
    ProjectStatus,
    TaskStatus,
)

SUPPORTED_PAYMENT_CURRENCIES = frozenset({"USD", "EUR", "GBP", "RON"})


class ProjectBillingFields(BaseModel):
    contract_type: ContractType = ContractType.FIXED_PRICE
    billing_cycle: BillingCycle = BillingCycle.MONTHLY
    billing_status: BillingStatus = BillingStatus.UNPAID
    billing_currency: str = Field(default="USD", min_length=3, max_length=3)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    agreed_amount: Decimal | None = Field(default=None, ge=0)
    monthly_rate: Decimal | None = Field(default=None, ge=0)
    billing_notes: str | None = Field(default=None, max_length=2_000)

    @model_validator(mode="after")
    def normalize_billing(self) -> "ProjectBillingFields":
        currency = self.currency or self.billing_currency
        self.currency = currency.upper()
        self.billing_currency = self.currency
        if self.contract_type == ContractType.INTERNAL:
            self.billing_status = BillingStatus.NOT_BILLABLE
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


class PaymentRecordFields(BaseModel):
    amount: Decimal = Field(gt=0)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    status: PaymentRecordStatus = PaymentRecordStatus.PENDING
    method: str | None = Field(default=None, max_length=80)
    paid_at: datetime | None = None
    due_date: date | None = None
    period_start: date | None = None
    period_end: date | None = None
    notes: str | None = Field(default=None, max_length=2_000)
    invoice_id: int | None = Field(default=None, ge=1)

    @field_validator("currency", mode="before")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        return str(value).strip().upper()

    @model_validator(mode="after")
    def normalize_payment_record(self) -> "PaymentRecordFields":
        if self.currency not in SUPPORTED_PAYMENT_CURRENCIES:
            raise ValueError("currency must be one of USD, EUR, GBP, or RON.")
        if (
            self.period_start is not None
            and self.period_end is not None
            and self.period_start > self.period_end
        ):
            raise ValueError("period_start cannot be later than period_end.")
        return self


class PaymentRecordCreateRequest(PaymentRecordFields):
    pass


class PaymentRecordUpdateRequest(BaseModel):
    amount: Decimal | None = Field(default=None, gt=0)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    status: PaymentRecordStatus | None = None
    method: str | None = Field(default=None, max_length=80)
    paid_at: datetime | None = None
    due_date: date | None = None
    period_start: date | None = None
    period_end: date | None = None
    notes: str | None = Field(default=None, max_length=2_000)
    invoice_id: int | None = Field(default=None, ge=1)

    @field_validator("currency", mode="before")
    @classmethod
    def normalize_currency(cls, value: str | None) -> str | None:
        return str(value).strip().upper() if value is not None else None

    @model_validator(mode="after")
    def normalize_payment_record_update(self) -> "PaymentRecordUpdateRequest":
        if self.currency is not None:
            if self.currency not in SUPPORTED_PAYMENT_CURRENCIES:
                raise ValueError("currency must be one of USD, EUR, GBP, or RON.")
        if (
            self.period_start is not None
            and self.period_end is not None
            and self.period_start > self.period_end
        ):
            raise ValueError("period_start cannot be later than period_end.")
        return self


class PaymentRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    invoice_id: int | None
    amount: Decimal
    currency: str
    status: PaymentRecordStatus
    is_overdue: bool
    method: str | None
    paid_at: datetime | None
    due_date: date | None
    period_start: date | None
    period_end: date | None
    notes: str | None
    created_at: datetime
    updated_at: datetime


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
    billing_currency: str | None = Field(default=None, min_length=3, max_length=3)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    agreed_amount: Decimal | None = Field(default=None, ge=0)
    monthly_rate: Decimal | None = Field(default=None, ge=0)
    billing_notes: str | None = Field(default=None, max_length=2_000)
    deadline: date | None = None
    archived: bool | None = None

    @model_validator(mode="after")
    def normalize_billing(self) -> "ProjectUpdateRequest":
        currency = self.currency or self.billing_currency
        if currency is not None:
            self.currency = currency.upper()
            self.billing_currency = self.currency
        if self.contract_type == ContractType.INTERNAL:
            self.billing_status = BillingStatus.NOT_BILLABLE
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
    billing_currency: str
    currency: str
    agreed_amount: Decimal | None
    monthly_rate: Decimal | None
    billing_notes: str | None
    deadline: date | None
    archived: bool
    created_at: datetime
    updated_at: datetime
    progress_percent: int
    estimated_hours: float
    actual_hours: float
    payment_records: list[PaymentRecordResponse]
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
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    sort_by: Literal[
        "id",
        "title",
        "client_name",
        "status",
        "priority",
        "budget_cents",
        "hourly_rate_cents",
        "deadline",
        "created_at",
        "updated_at",
    ] = "priority"
    sort_dir: Literal["asc", "desc"] = "asc"

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


class ProjectListResponse(BaseModel):
    items: list[ProjectResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class ProjectActionResponse(BaseModel):
    message: str
    project: ProjectResponse
