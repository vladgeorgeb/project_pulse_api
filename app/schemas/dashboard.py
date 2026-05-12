from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict


class DashboardSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    workspace_id: int
    total_projects: int
    active_projects: int
    completed_projects: int
    archived_projects: int
    open_tasks: int
    completed_tasks: int
    overdue_tasks: int
    estimated_hours: float
    actual_hours: float
    billable_value_cents: int
    capacity_used_percent: int
    active_billable_projects: int
    unpaid_projects: int
    overdue_payments: int
    paid_projects: int
    monthly_contract_revenue_estimate: float
    total_monthly_recurring_amount: float
    paid_this_month_amount: float
    total_paid_amount: float
    pending_payment_amount: float
    overdue_payment_amount: float
    next_payment_due_date: date | None
    next_payment_due_amount: float | None
    next_payment_due_currency: str | None
    payment_summary_currency: str | None
    has_mixed_payment_currencies: bool
    active_monthly_contracts: int
