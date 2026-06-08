from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.domain.enums import (
    ContractType,
    PaymentRecordStatus,
    ProjectStatus,
    TaskStatus,
)
from app.domain.project_rules import is_project_open
from app.models.user import User
from app.repositories.project import ProjectRepository
from app.repositories.task import TaskRepository
from app.repositories.workspace import WorkspaceRepository


@dataclass(frozen=True, slots=True)
class DashboardSummary:
    workspace_id: int
    selected_month: date
    total_projects: int
    active_projects: int
    completed_projects: int
    archived_projects: int
    open_tasks: int
    completed_tasks: int
    overdue_tasks: int
    estimated_hours: float
    actual_hours: float
    committed_hours: float
    billable_value_cents: int
    capacity_used_percent: int
    active_billable_projects: int
    unpaid_projects: int
    overdue_payments: int
    paid_projects: int
    monthly_contract_revenue_estimate: float
    total_monthly_recurring_amount: float
    paid_this_month_amount: float
    expected_this_month_amount: float
    received_this_month_amount: float
    outstanding_income_amount: float
    total_paid_amount: float
    pending_payment_amount: float
    overdue_payment_amount: float
    next_payment_due_date: date | None
    next_payment_due_amount: float | None
    next_payment_due_currency: str | None
    payment_summary_currency: str | None
    has_mixed_payment_currencies: bool
    active_monthly_contracts: int


class DashboardService:
    __slots__ = ("projects", "tasks", "workspaces")

    def __init__(self, db: Session) -> None:
        self.projects = ProjectRepository(db)
        self.tasks = TaskRepository(db)
        self.workspaces = WorkspaceRepository(db)

    def get_summary_for_user(
        self, user: User, selected_month: date | None = None
    ) -> DashboardSummary:
        workspace = self.workspaces.get_by_user_id(user.id)
        if workspace is None:
            raise NotFoundError("Workspace not found.")
        today = date.today()
        month_start = (selected_month or today).replace(day=1)
        month_end = self._month_end(month_start)

        projects = self.projects.list_for_workspace(
            workspace_id=workspace.id, include_archived=True
        )
        project_ids = [project.id for project in projects]
        overdue_tasks = self.tasks.list_overdue_for_projects(project_ids, today)

        month_tasks = [
            task
            for project in projects
            if project.status != ProjectStatus.ARCHIVED.value
            for task in project.tasks
            if self._task_overlaps_month(task, month_start, month_end)
        ]
        open_tasks = sum(
            1 for task in month_tasks if task.status != TaskStatus.DONE.value
        )
        completed_tasks = sum(
            1 for task in month_tasks if task.status == TaskStatus.DONE.value
        )
        estimated_minutes = self._committed_minutes_for_month(
            projects, month_start, month_end
        )
        actual_minutes = sum(
            task.actual_minutes
            for task in month_tasks
            if self._task_actuals_belong_to_month(task, month_start, month_end)
        )
        billable_value_cents = sum(
            (task.actual_minutes * (project.hourly_rate_cents or 0)) // 60
            for project in projects
            for task in month_tasks
            if project.status != ProjectStatus.ARCHIVED.value
            and self._task_actuals_belong_to_month(task, month_start, month_end)
        )
        capacity_minutes = workspace.monthly_capacity_hours * 60
        capacity_used_percent = (
            min(100, estimated_minutes * 100 // capacity_minutes)
            if capacity_minutes > 0
            else 0
        )

        active_billable_projects = sum(
            1
            for project in projects
            if project.status != ProjectStatus.ARCHIVED.value
            and is_project_open(project.status)
            and project.contract_type != ContractType.NON_BILLABLE.value
        )

        monthly_contract_revenue_estimate_cents = 0
        total_monthly_recurring_amount_cents = 0
        active_monthly_contracts = 0
        for project in projects:
            if project.status == ProjectStatus.ARCHIVED.value or not is_project_open(
                project.status
            ):
                continue
            if project.contract_type == ContractType.HOURLY.value:
                if (
                    project.hourly_rate_cents is not None
                    and project.expected_hours_per_week is not None
                ):
                    monthly_contract_revenue_estimate_cents += int(
                        (
                            Decimal(project.hourly_rate_cents)
                            * project.expected_hours_per_week
                            * Decimal("4.33")
                        ).quantize(Decimal("1"))
                    )
            elif project.contract_type == ContractType.MONTHLY_RETAINER.value:
                if project.monthly_rate_cents is not None:
                    monthly_contract_revenue_estimate_cents += (
                        project.monthly_rate_cents
                    )
                    total_monthly_recurring_amount_cents += project.monthly_rate_cents
                    active_monthly_contracts += 1

        payment_record_entries = [
            (project, payment_record)
            for project in projects
            if project.status != ProjectStatus.ARCHIVED.value
            for payment_record in project.payment_records
        ]
        payment_currencies = {
            payment_record.currency for _, payment_record in payment_record_entries
        }
        has_mixed_payment_currencies = len(payment_currencies) > 1
        payment_summary_currency = (
            next(iter(payment_currencies)) if len(payment_currencies) == 1 else None
        )

        if has_mixed_payment_currencies:
            total_paid_amount = Decimal("0")
            paid_this_month_amount = Decimal("0")
            pending_payment_amount = Decimal("0")
            overdue_payment_amount = Decimal("0")
            next_due_amount: Decimal | None = None
        else:
            total_paid_amount = sum(
                (
                    Decimal(payment_record.amount_cents) / Decimal("100")
                    for _, payment_record in payment_record_entries
                    if payment_record.status == PaymentRecordStatus.PAID.value
                ),
                Decimal("0"),
            )
            paid_this_month_amount = sum(
                (
                    Decimal(payment_record.amount_cents) / Decimal("100")
                    for _, payment_record in payment_record_entries
                    if payment_record.status == PaymentRecordStatus.PAID.value
                    and payment_record.paid_at is not None
                    and month_start <= payment_record.paid_at.date() <= month_end
                ),
                Decimal("0"),
            )
            expected_this_month_amount = sum(
                (
                    Decimal(payment_record.amount_cents) / Decimal("100")
                    for _, payment_record in payment_record_entries
                    if payment_record.status != PaymentRecordStatus.CANCELLED.value
                    and payment_record.due_date is not None
                    and month_start <= payment_record.due_date <= month_end
                ),
                Decimal("0"),
            )
            received_this_month_amount = paid_this_month_amount
            pending_payment_amount = sum(
                (
                    Decimal(payment_record.amount_cents) / Decimal("100")
                    for _, payment_record in payment_record_entries
                    if payment_record.status == PaymentRecordStatus.PENDING.value
                    and not self._is_payment_record_overdue(payment_record, today)
                ),
                Decimal("0"),
            )
            overdue_payment_amount = sum(
                (
                    Decimal(payment_record.amount_cents) / Decimal("100")
                    for _, payment_record in payment_record_entries
                    if self._is_payment_record_overdue(payment_record, today)
                ),
                Decimal("0"),
            )
            outstanding_income_amount = pending_payment_amount + overdue_payment_amount
            next_due_amount = None
        if has_mixed_payment_currencies:
            expected_this_month_amount = Decimal("0")
            received_this_month_amount = Decimal("0")
            outstanding_income_amount = Decimal("0")

        record_due_candidates = [
            (
                payment_record.due_date,
                payment_record.id,
                payment_record.amount_cents,
                payment_record.currency,
            )
            for _, payment_record in payment_record_entries
            if payment_record.due_date is not None
            and payment_record.due_date >= today
            and payment_record.status == PaymentRecordStatus.PENDING.value
        ]
        next_due = min(record_due_candidates, default=None)
        if next_due is not None and not has_mixed_payment_currencies:
            next_due_amount = Decimal(next_due[2]) / Decimal("100")

        overdue_payments = sum(
            1
            for _, payment_record in payment_record_entries
            if self._is_payment_record_overdue(payment_record, today)
        )
        unpaid_projects = sum(
            1
            for project in projects
            if project.status != ProjectStatus.ARCHIVED.value
            and any(
                payment_record.status == PaymentRecordStatus.PENDING.value
                and not self._is_payment_record_overdue(payment_record, today)
                for payment_record in project.payment_records
            )
        )
        paid_projects = sum(
            1
            for project in projects
            if project.status != ProjectStatus.ARCHIVED.value
            and any(
                payment_record.status == PaymentRecordStatus.PAID.value
                for payment_record in project.payment_records
            )
        )

        return DashboardSummary(
            workspace_id=workspace.id,
            selected_month=month_start,
            total_projects=len(projects),
            active_projects=sum(
                1 for project in projects if is_project_open(project.status)
            ),
            completed_projects=sum(
                1
                for project in projects
                if project.status == ProjectStatus.COMPLETED.value
            ),
            archived_projects=sum(
                1
                for project in projects
                if project.status == ProjectStatus.ARCHIVED.value
            ),
            open_tasks=open_tasks,
            completed_tasks=completed_tasks,
            overdue_tasks=len(overdue_tasks),
            estimated_hours=round(estimated_minutes / 60, 2),
            actual_hours=round(actual_minutes / 60, 2),
            committed_hours=round(estimated_minutes / 60, 2),
            billable_value_cents=billable_value_cents,
            capacity_used_percent=capacity_used_percent,
            active_billable_projects=active_billable_projects,
            unpaid_projects=unpaid_projects,
            overdue_payments=overdue_payments,
            paid_projects=paid_projects,
            monthly_contract_revenue_estimate=round(
                monthly_contract_revenue_estimate_cents / 100, 2
            ),
            total_monthly_recurring_amount=round(
                total_monthly_recurring_amount_cents / 100, 2
            ),
            paid_this_month_amount=round(float(paid_this_month_amount), 2),
            expected_this_month_amount=round(float(expected_this_month_amount), 2),
            received_this_month_amount=round(float(received_this_month_amount), 2),
            outstanding_income_amount=round(float(outstanding_income_amount), 2),
            total_paid_amount=round(float(total_paid_amount), 2),
            pending_payment_amount=round(float(pending_payment_amount), 2),
            overdue_payment_amount=round(float(overdue_payment_amount), 2),
            next_payment_due_date=next_due[0] if next_due is not None else None,
            next_payment_due_amount=(
                round(float(next_due_amount), 2)
                if next_due_amount is not None
                else None
            ),
            next_payment_due_currency=next_due[3] if next_due is not None else None,
            payment_summary_currency=payment_summary_currency,
            has_mixed_payment_currencies=has_mixed_payment_currencies,
            active_monthly_contracts=active_monthly_contracts,
        )

    def _is_payment_record_overdue(self, payment_record, today: date) -> bool:
        return (
            payment_record.due_date is not None
            and payment_record.due_date < today
            and payment_record.status == PaymentRecordStatus.PENDING.value
        )

    def _month_end(self, month_start: date) -> date:
        if month_start.month == 12:
            next_month = date(month_start.year + 1, 1, 1)
        else:
            next_month = date(month_start.year, month_start.month + 1, 1)
        return next_month - timedelta(days=1)

    def _task_overlaps_month(self, task, month_start: date, month_end: date) -> bool:
        if task.due_date is None:
            return (
                task.status != TaskStatus.DONE.value
                and month_start == date.today().replace(day=1)
            )
        return task.due_date is not None and month_start <= task.due_date <= month_end

    def _task_actuals_belong_to_month(
        self, task, month_start: date, month_end: date
    ) -> bool:
        if task.completed_at is not None:
            return month_start <= task.completed_at.date() <= month_end
        return self._task_overlaps_month(task, month_start, month_end)

    def _committed_minutes_for_month(
        self, projects, month_start: date, month_end: date
    ) -> int:
        total = Decimal("0")
        for project in projects:
            if project.status == ProjectStatus.ARCHIVED.value or not is_project_open(
                project.status
            ):
                continue
            if (
                project.monthly_commitment_hours is not None
                and project.monthly_commitment_hours > 0
            ):
                total += Decimal(project.monthly_commitment_hours) * Decimal("60")
                continue
            total += sum(
                Decimal(task.estimated_minutes)
                for task in project.tasks
                if self._task_overlaps_month(task, month_start, month_end)
            )
        return int(total)
