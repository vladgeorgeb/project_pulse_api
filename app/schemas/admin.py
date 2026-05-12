from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

from app.domain.constants import MAX_TASK_ESTIMATE_MINUTES
from app.domain.enums import (
    ContractType,
    PaymentCadence,
    Priority,
    ProjectStatus,
    TaskStatus,
)


class AdminUserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    is_admin: bool
    email_verified: bool
    email_verified_at: datetime | None


class AdminUserCreateRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    is_admin: bool = False


class AdminUserUpdateRequest(BaseModel):
    email: EmailStr | None = None
    password: str | None = Field(default=None, min_length=8, max_length=128)
    is_admin: bool | None = None


class AdminWorkspaceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    name: str
    company_name: str
    monthly_capacity_hours: int


class AdminWorkspaceCreateRequest(BaseModel):
    user_id: int
    name: str = Field(min_length=1, max_length=100)
    company_name: str = Field(min_length=1, max_length=100)
    monthly_capacity_hours: int = Field(gt=0, le=744)


class AdminWorkspaceUpdateRequest(BaseModel):
    user_id: int | None = None
    name: str | None = Field(default=None, min_length=1, max_length=100)
    company_name: str | None = Field(default=None, min_length=1, max_length=100)
    monthly_capacity_hours: int | None = Field(default=None, gt=0, le=744)


class AdminProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    workspace_id: int
    title: str
    client_name: str
    description: str | None
    status: ProjectStatus
    priority: Priority
    hourly_rate_cents: int | None
    expected_hours_per_week: Decimal | None
    monthly_rate_cents: int | None
    fixed_price_cents: int | None
    contract_type: ContractType
    billing_currency: str
    start_date: date | None
    estimated_end_date: date | None
    payment_cadence: PaymentCadence
    billing_notes: str | None
    deadline: date | None
    archived: bool
    created_at: datetime
    updated_at: datetime


class AdminProjectCreateRequest(BaseModel):
    workspace_id: int
    title: str = Field(min_length=1, max_length=120)
    client_name: str = Field(min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=4_000)
    status: ProjectStatus = ProjectStatus.PLANNED
    priority: Priority = Priority.MEDIUM
    hourly_rate_cents: int | None = Field(default=None, ge=1, le=1_000_000)
    expected_hours_per_week: Decimal | None = Field(default=None, ge=0)
    monthly_rate_cents: int | None = Field(default=None, ge=1)
    fixed_price_cents: int | None = Field(default=None, ge=1)
    contract_type: ContractType = ContractType.FIXED_PRICE
    billing_currency: str = Field(default="USD", min_length=3, max_length=3)
    start_date: date | None = None
    estimated_end_date: date | None = None
    payment_cadence: PaymentCadence = PaymentCadence.MANUAL
    billing_notes: str | None = Field(default=None, max_length=2_000)
    deadline: date | None = None

    @model_validator(mode="after")
    def normalize_billing(self) -> "AdminProjectCreateRequest":
        self.billing_currency = self.billing_currency.upper()
        return self


class AdminProjectUpdateRequest(BaseModel):
    workspace_id: int | None = None
    title: str | None = Field(default=None, min_length=1, max_length=120)
    client_name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=4_000)
    status: ProjectStatus | None = None
    priority: Priority | None = None
    hourly_rate_cents: int | None = Field(default=None, ge=1, le=1_000_000)
    expected_hours_per_week: Decimal | None = Field(default=None, ge=0)
    monthly_rate_cents: int | None = Field(default=None, ge=1)
    fixed_price_cents: int | None = Field(default=None, ge=1)
    contract_type: ContractType | None = None
    billing_currency: str | None = Field(default=None, min_length=3, max_length=3)
    start_date: date | None = None
    estimated_end_date: date | None = None
    payment_cadence: PaymentCadence | None = None
    billing_notes: str | None = Field(default=None, max_length=2_000)
    deadline: date | None = None
    archived: bool | None = None

    @model_validator(mode="after")
    def normalize_billing(self) -> "AdminProjectUpdateRequest":
        if self.billing_currency is not None:
            self.billing_currency = self.billing_currency.upper()
        return self


class AdminTaskResponse(BaseModel):
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


class AdminTaskCreateRequest(BaseModel):
    project_id: int
    title: str = Field(min_length=1, max_length=160)
    description: str | None = Field(default=None, max_length=2_000)
    status: TaskStatus = TaskStatus.TODO
    priority: Priority = Priority.MEDIUM
    estimated_minutes: int = Field(default=0, ge=0, le=MAX_TASK_ESTIMATE_MINUTES)
    actual_minutes: int = Field(default=0, ge=0, le=MAX_TASK_ESTIMATE_MINUTES)
    due_date: date | None = None


class AdminTaskUpdateRequest(BaseModel):
    project_id: int | None = None
    title: str | None = Field(default=None, min_length=1, max_length=160)
    description: str | None = Field(default=None, max_length=2_000)
    status: TaskStatus | None = None
    priority: Priority | None = None
    estimated_minutes: int | None = Field(
        default=None, ge=0, le=MAX_TASK_ESTIMATE_MINUTES
    )
    actual_minutes: int | None = Field(default=None, ge=0, le=MAX_TASK_ESTIMATE_MINUTES)
    due_date: date | None = None
