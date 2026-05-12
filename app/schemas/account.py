from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, EmailStr, Field

from app.schemas.project import PaymentRecordResponse, ProjectResponse, TaskResponse


class AccountExportAccount(BaseModel):
    id: int
    email: EmailStr
    is_admin: bool
    email_verified: bool
    email_verified_at: datetime | None


class AccountExportBusinessProfile(BaseModel):
    workspace_id: int
    workspace_name: str
    company_name: str
    monthly_capacity_hours: int


class AccountExportClient(BaseModel):
    name: str
    project_ids: list[int]


class AccountExportBillingData(BaseModel):
    payment_records: list[PaymentRecordResponse] = Field(default_factory=list)
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
