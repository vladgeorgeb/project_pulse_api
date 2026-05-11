from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.domain.enums import ContractType, PaymentStatus, ProjectStatus, TaskStatus
from app.domain.project_rules import is_project_open
from app.models.user import User
from app.repositories.project import ProjectRepository
from app.repositories.task import TaskRepository
from app.repositories.workspace import WorkspaceRepository


@dataclass(frozen=True, slots=True)
class DashboardSummary:
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
    pending_payment_amount: float
    overdue_payment_amount: float
    active_monthly_contracts: int


class DashboardService:
    __slots__ = ("projects", "tasks", "workspaces")

    def __init__(self, db: Session) -> None:
        self.projects = ProjectRepository(db)
        self.tasks = TaskRepository(db)
        self.workspaces = WorkspaceRepository(db)

    def get_summary_for_user(self, user: User) -> DashboardSummary:
        workspace = self.workspaces.get_by_user_id(user.id)
        if workspace is None:
            raise NotFoundError("Workspace not found.")

        projects = self.projects.list_for_workspace(
            workspace_id=workspace.id,
            include_archived=True,
        )
        project_ids = [project.id for project in projects]
        overdue_tasks = self.tasks.list_overdue_for_projects(project_ids, date.today())

        all_tasks = [task for project in projects for task in project.tasks]
        open_tasks = sum(
            1 for task in all_tasks if task.status != TaskStatus.DONE.value
        )
        completed_tasks = sum(
            1 for task in all_tasks if task.status == TaskStatus.DONE.value
        )
        estimated_minutes = sum(task.estimated_minutes for task in all_tasks)
        actual_minutes = sum(task.actual_minutes for task in all_tasks)
        billable_value_cents = sum(
            (task.actual_minutes * project.hourly_rate_cents) // 60
            for project in projects
            for task in project.tasks
        )
        capacity_minutes = workspace.monthly_capacity_hours * 60
        capacity_used_percent = (
            min(100, actual_minutes * 100 // capacity_minutes)
            if capacity_minutes > 0
            else 0
        )
        active_billable_projects = sum(
            1
            for project in projects
            if not project.archived
            and is_project_open(project.status)
            and project.payment_status != PaymentStatus.NOT_STARTED.value
        )
        unpaid_projects = sum(
            1
            for project in projects
            if not project.archived
            and project.payment_status == PaymentStatus.PENDING.value
        )
        overdue_payments = sum(
            1
            for project in projects
            if not project.archived
            and project.payment_status == PaymentStatus.OVERDUE.value
        )
        paid_projects = sum(
            1
            for project in projects
            if not project.archived
            and project.payment_status == PaymentStatus.PAID.value
        )
        monthly_contract_projects = [
            project
            for project in projects
            if not project.archived
            and is_project_open(project.status)
            and project.contract_type
            in {
                ContractType.MONTHLY_RETAINER.value,
                ContractType.FULL_TIME_MONTHLY.value,
            }
            and project.payment_status != PaymentStatus.NOT_STARTED.value
        ]
        current_month = date.today().replace(day=1)
        monthly_amounts = [
            (project, project.monthly_amount or project.monthly_rate or Decimal("0"))
            for project in monthly_contract_projects
        ]
        total_monthly_recurring_amount = sum(
            (amount for _, amount in monthly_amounts),
            Decimal("0"),
        )
        paid_this_month_amount = sum(
            amount
            for project, amount in monthly_amounts
            if project.payment_status == PaymentStatus.PAID.value
            and project.paid_at is not None
            and project.paid_at.date().replace(day=1) == current_month
        )
        pending_payment_amount = sum(
            amount
            for project, amount in monthly_amounts
            if project.payment_status == PaymentStatus.PENDING.value
        )
        overdue_payment_amount = sum(
            amount
            for project, amount in monthly_amounts
            if project.payment_status == PaymentStatus.OVERDUE.value
        )

        return DashboardSummary(
            workspace_id=workspace.id,
            total_projects=len(projects),
            active_projects=sum(
                1 for project in projects if is_project_open(project.status)
            ),
            completed_projects=sum(
                1
                for project in projects
                if project.status == ProjectStatus.COMPLETED.value
            ),
            archived_projects=sum(1 for project in projects if project.archived),
            open_tasks=open_tasks,
            completed_tasks=completed_tasks,
            overdue_tasks=len(overdue_tasks),
            estimated_hours=round(estimated_minutes / 60, 2),
            actual_hours=round(actual_minutes / 60, 2),
            billable_value_cents=billable_value_cents,
            capacity_used_percent=capacity_used_percent,
            active_billable_projects=active_billable_projects,
            unpaid_projects=unpaid_projects,
            overdue_payments=overdue_payments,
            paid_projects=paid_projects,
            monthly_contract_revenue_estimate=round(
                float(total_monthly_recurring_amount),
                2,
            ),
            total_monthly_recurring_amount=round(
                float(total_monthly_recurring_amount),
                2,
            ),
            paid_this_month_amount=round(float(paid_this_month_amount), 2),
            pending_payment_amount=round(float(pending_payment_amount), 2),
            overdue_payment_amount=round(float(overdue_payment_amount), 2),
            active_monthly_contracts=len(monthly_contract_projects),
        )
