from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

from app.domain.constants import MAX_PROJECT_BUDGET_CENTS, MAX_TASK_ESTIMATE_MINUTES
from app.domain.enums import (
    BillingCycle,
    BillingStatus,
    ContractType,
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
    budget_cents: int
    hourly_rate_cents: int
    contract_type: ContractType
    billing_cycle: BillingCycle
    billing_status: BillingStatus
    billing_currency: str
    agreed_amount: Decimal | None
    monthly_rate: Decimal | None
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
    budget_cents: int = Field(default=0, ge=0, le=MAX_PROJECT_BUDGET_CENTS)
    hourly_rate_cents: int = Field(default=0, ge=0, le=1_000_000)
    contract_type: ContractType = ContractType.FIXED_PRICE
    billing_cycle: BillingCycle = BillingCycle.MONTHLY
    billing_status: BillingStatus = BillingStatus.UNPAID
    billing_currency: str = Field(default="USD", min_length=3, max_length=3)
    agreed_amount: Decimal | None = Field(default=None, ge=0)
    monthly_rate: Decimal | None = Field(default=None, ge=0)
    billing_notes: str | None = Field(default=None, max_length=2_000)
    deadline: date | None = None

    @model_validator(mode="after")
    def normalize_billing(self) -> "AdminProjectCreateRequest":
        self.billing_currency = self.billing_currency.upper()
        if self.contract_type == ContractType.INTERNAL:
            self.billing_status = BillingStatus.NOT_BILLABLE
        return self


class AdminProjectUpdateRequest(BaseModel):
    workspace_id: int | None = None
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
    agreed_amount: Decimal | None = Field(default=None, ge=0)
    monthly_rate: Decimal | None = Field(default=None, ge=0)
    billing_notes: str | None = Field(default=None, max_length=2_000)
    deadline: date | None = None
    archived: bool | None = None

    @model_validator(mode="after")
    def normalize_billing(self) -> "AdminProjectUpdateRequest":
        if self.billing_currency is not None:
            self.billing_currency = self.billing_currency.upper()
        if self.contract_type == ContractType.INTERNAL:
            self.billing_status = BillingStatus.NOT_BILLABLE
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
