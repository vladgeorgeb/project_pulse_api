from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.domain.constants import MAX_TASK_ESTIMATE_MINUTES
from app.domain.enums import (
    ContractType,
    PaymentCadence,
    Priority,
    ProjectStatus,
    TaskStatus,
)
from app.schemas.payment_record import PaymentRecordResponse


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


class ProjectBillingFields(BaseModel):
    contract_type: ContractType = ContractType.FIXED_PRICE
    billing_currency: str = Field(default="USD", min_length=3, max_length=3)
    hourly_rate_cents: int | None = Field(default=None, ge=1, le=1_000_000)
    expected_hours_per_week: Decimal | None = Field(default=None, ge=0)
    monthly_rate_cents: int | None = Field(default=None, ge=1, le=100_000_000)
    fixed_price_cents: int | None = Field(default=None, ge=1, le=100_000_000)
    start_date: date | None = None
    estimated_end_date: date | None = None
    payment_cadence: PaymentCadence = PaymentCadence.MANUAL
    billing_notes: str | None = Field(default=None, max_length=2_000)

    @field_validator("billing_currency", mode="before")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        return str(value).strip().upper()

    @model_validator(mode="after")
    def validate_contract_fields(self) -> "ProjectBillingFields":
        if self.contract_type == ContractType.HOURLY and self.hourly_rate_cents is None:
            raise ValueError("hourly contracts require hourly_rate_cents.")
        if (
            self.contract_type == ContractType.MONTHLY_RETAINER
            and self.monthly_rate_cents is None
        ):
            raise ValueError("monthly_retainer contracts require monthly_rate_cents.")
        if (
            self.contract_type == ContractType.FIXED_PRICE
            and self.fixed_price_cents is None
        ):
            raise ValueError("fixed_price contracts require fixed_price_cents.")
        if (
            self.contract_type == ContractType.NON_BILLABLE
            and self.payment_cadence != PaymentCadence.NONE
        ):
            raise ValueError("non_billable contracts require payment_cadence 'none'.")
        if (
            self.contract_type != ContractType.NON_BILLABLE
            and self.payment_cadence == PaymentCadence.NONE
        ):
            raise ValueError(
                "payment_cadence 'none' is only valid for non_billable contracts."
            )
        if (
            self.start_date is not None
            and self.estimated_end_date is not None
            and self.start_date > self.estimated_end_date
        ):
            raise ValueError("start_date cannot be later than estimated_end_date.")
        return self


class ProjectCreateRequest(ProjectBillingFields):
    title: str = Field(min_length=1, max_length=120)
    client_name: str = Field(min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=4_000)
    status: ProjectStatus = ProjectStatus.PLANNED
    priority: Priority = Priority.MEDIUM
    deadline: date | None = None


class ProjectUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=120)
    client_name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=4_000)
    status: ProjectStatus | None = None
    priority: Priority | None = None
    contract_type: ContractType | None = None
    billing_currency: str | None = Field(default=None, min_length=3, max_length=3)
    hourly_rate_cents: int | None = Field(default=None, ge=1, le=1_000_000)
    expected_hours_per_week: Decimal | None = Field(default=None, ge=0)
    monthly_rate_cents: int | None = Field(default=None, ge=1, le=100_000_000)
    fixed_price_cents: int | None = Field(default=None, ge=1, le=100_000_000)
    start_date: date | None = None
    estimated_end_date: date | None = None
    deadline: date | None = None
    payment_cadence: PaymentCadence | None = None
    billing_notes: str | None = Field(default=None, max_length=2_000)

    @field_validator("billing_currency", mode="before")
    @classmethod
    def normalize_currency(cls, value: str | None) -> str | None:
        return str(value).strip().upper() if value is not None else None


class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    workspace_id: int
    title: str
    client_name: str
    description: str | None
    status: ProjectStatus
    priority: Priority
    contract_type: ContractType
    billing_currency: str
    hourly_rate_cents: int | None
    expected_hours_per_week: Decimal | None
    monthly_rate_cents: int | None
    fixed_price_cents: int | None
    start_date: date | None
    estimated_end_date: date | None
    deadline: date | None
    payment_cadence: PaymentCadence
    billing_notes: str | None
    created_at: datetime
    updated_at: datetime
    progress_percent: int
    estimated_hours: float
    actual_hours: float
    expected_weekly_income_cents: int | None
    expected_monthly_income_cents: int | None
    expected_total_contract_value_cents: int | None
    payment_records: list[PaymentRecordResponse]
    tasks: list[TaskResponse]


class ProjectQueryParams(BaseModel):
    status: ProjectStatus | None = None
    priority: Priority | None = None
    client_name: str | None = None
    search: str | None = None
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
        "contract_type",
        "deadline",
        "created_at",
        "updated_at",
    ] = "priority"
    sort_dir: Literal["asc", "desc"] = "asc"

    @model_validator(mode="after")
    def validate_ranges(self) -> "ProjectQueryParams":
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
