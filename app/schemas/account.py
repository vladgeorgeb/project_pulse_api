from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, EmailStr, Field

from app.schemas.project import ProjectResponse, TaskResponse


class AccountExportAccount(BaseModel):
    id: int
    email: EmailStr
    is_admin: bool


class AccountExportBusinessProfile(BaseModel):
    workspace_id: int
    workspace_name: str
    company_name: str
    monthly_capacity_hours: int


class AccountExportClient(BaseModel):
    name: str
    project_ids: list[int]


class AccountExportPaymentRecord(BaseModel):
    project_id: int
    project_title: str
    client_name: str
    contract_type: str
    billing_cycle: str
    billing_status: str
    payment_status: str
    billing_currency: str
    agreed_amount: Decimal | None
    monthly_rate: Decimal | None
    monthly_amount: Decimal | None
    payment_due_day: int | None
    next_payment_due_date: date | None
    paid_at: datetime | None
    billing_notes: str | None


class AccountExportBillingData(BaseModel):
    project_payment_records: list[AccountExportPaymentRecord]
    invoices: list[dict[str, Any]] = Field(default_factory=list)


class AccountExportResponse(BaseModel):
    schema_version: int = 1
    exported_at: datetime
    account: AccountExportAccount
    business_profile: AccountExportBusinessProfile | None
    clients: list[AccountExportClient]
    projects: list[ProjectResponse]
    tasks: list[TaskResponse]
    billing: AccountExportBillingData


class AccountDeleteRequest(BaseModel):
    password: str = Field(min_length=1, max_length=128)
    confirm_admin_self_deletion: bool = False
