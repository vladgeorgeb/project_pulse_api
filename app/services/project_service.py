from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.exceptions import (
    BusinessRuleError,
    NotFoundError,
)
from app.domain.enums import BillingStatus, ContractType, PaymentStatus, ProjectStatus
from app.domain.project_rules import validate_project_completion
from app.models.project import Project
from app.models.user import User
from app.repositories.project import PaginatedProjects, ProjectRepository
from app.repositories.workspace import WorkspaceRepository


def _billing_status_for_payment_status(payment_status: str) -> str:
    if payment_status == PaymentStatus.PAID.value:
        return BillingStatus.PAID.value
    if payment_status == PaymentStatus.OVERDUE.value:
        return BillingStatus.OVERDUE.value
    if payment_status == PaymentStatus.NOT_STARTED.value:
        return BillingStatus.NOT_BILLABLE.value
    return BillingStatus.UNPAID.value


def _payment_status_for_billing_status(billing_status: str) -> str:
    if billing_status == BillingStatus.PAID.value:
        return PaymentStatus.PAID.value
    if billing_status == BillingStatus.OVERDUE.value:
        return PaymentStatus.OVERDUE.value
    if billing_status == BillingStatus.NOT_BILLABLE.value:
        return PaymentStatus.NOT_STARTED.value
    return PaymentStatus.PENDING.value


class ProjectService:
    __slots__ = ("db", "projects", "workspaces")

    def __init__(self, db: Session) -> None:
        self.db = db
        self.projects = ProjectRepository(db)
        self.workspaces = WorkspaceRepository(db)

    def list_projects_for_user(
        self,
        *,
        user: User,
        status: str | None = None,
        priority: str | None = None,
        client_name: str | None = None,
        search: str | None = None,
        min_budget_cents: int | None = None,
        max_budget_cents: int | None = None,
        due_before: date | None = None,
        due_after: date | None = None,
        overdue_only: bool = False,
        include_archived: bool = False,
    ) -> list[Project]:
        workspace = self._workspace_for_user(user)
        return self.projects.list_for_workspace(
            workspace_id=workspace.id,
            status=status,
            priority=priority,
            client_name=client_name,
            search=search,
            min_budget_cents=min_budget_cents,
            max_budget_cents=max_budget_cents,
            due_before=due_before,
            due_after=due_after,
            overdue_only=overdue_only,
            include_archived=include_archived,
        )

    def paginate_projects_for_user(
        self,
        *,
        user: User,
        status: str | None = None,
        priority: str | None = None,
        client_name: str | None = None,
        search: str | None = None,
        min_budget_cents: int | None = None,
        max_budget_cents: int | None = None,
        due_before: date | None = None,
        due_after: date | None = None,
        overdue_only: bool = False,
        include_archived: bool = False,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "deadline",
        sort_dir: str = "asc",
    ) -> PaginatedProjects:
        workspace = self._workspace_for_user(user)
        return self.projects.paginate_for_workspace(
            workspace_id=workspace.id,
            status=status,
            priority=priority,
            client_name=client_name,
            search=search,
            min_budget_cents=min_budget_cents,
            max_budget_cents=max_budget_cents,
            due_before=due_before,
            due_after=due_after,
            overdue_only=overdue_only,
            include_archived=include_archived,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_dir=sort_dir,
        )

    def get_project_for_user(self, *, user: User, project_id: int) -> Project:
        workspace = self._workspace_for_user(user)
        project = self.projects.get_for_workspace(
            project_id=project_id,
            workspace_id=workspace.id,
        )
        if project is None:
            raise NotFoundError("Project not found.")
        return project

    def create_project(
        self,
        *,
        user: User,
        title: str,
        client_name: str,
        description: str | None,
        status: str,
        priority: str,
        budget_cents: int,
        hourly_rate_cents: int,
        contract_type: str,
        billing_cycle: str,
        billing_status: str,
        payment_status: str,
        billing_currency: str,
        agreed_amount: Decimal | None,
        monthly_rate: Decimal | None,
        monthly_amount: Decimal | None,
        payment_due_day: int | None,
        next_payment_due_date: date | None,
        paid_at: datetime | None,
        billing_notes: str | None,
        deadline: date | None,
    ) -> Project:
        workspace = self._workspace_for_user(user)
        if contract_type == ContractType.INTERNAL.value:
            billing_status = BillingStatus.NOT_BILLABLE.value
            payment_status = PaymentStatus.NOT_STARTED.value
        if payment_status == PaymentStatus.PAID.value and paid_at is None:
            paid_at = datetime.now(UTC).replace(tzinfo=None)
        now = datetime.now(UTC).replace(tzinfo=None)
        project = Project(
            workspace_id=workspace.id,
            title=title.strip(),
            client_name=client_name.strip(),
            description=description.strip() if description else None,
            status=status,
            priority=priority,
            budget_cents=budget_cents,
            hourly_rate_cents=hourly_rate_cents,
            contract_type=contract_type,
            billing_cycle=billing_cycle,
            billing_status=billing_status,
            payment_status=payment_status,
            billing_currency=billing_currency.strip().upper(),
            agreed_amount=agreed_amount,
            monthly_rate=monthly_rate if monthly_rate is not None else monthly_amount,
            monthly_amount=monthly_amount,
            payment_due_day=payment_due_day,
            next_payment_due_date=next_payment_due_date,
            paid_at=paid_at,
            billing_notes=billing_notes.strip() if billing_notes else None,
            deadline=deadline,
            archived=status == ProjectStatus.ARCHIVED.value,
            created_at=now,
            updated_at=now,
        )
        self.projects.add(project)
        self.db.commit()
        self.db.refresh(project)
        return (
            self.projects.get_for_workspace(
                project_id=project.id,
                workspace_id=workspace.id,
            )
            or project
        )

    def update_project(
        self,
        *,
        user: User,
        project_id: int,
        title: str | None,
        client_name: str | None,
        description: str | None,
        status: str | None,
        priority: str | None,
        budget_cents: int | None,
        hourly_rate_cents: int | None,
        contract_type: str | None,
        billing_cycle: str | None,
        billing_status: str | None,
        payment_status: str | None,
        billing_currency: str | None,
        agreed_amount: Decimal | None,
        agreed_amount_provided: bool,
        monthly_rate: Decimal | None,
        monthly_rate_provided: bool,
        monthly_amount: Decimal | None,
        monthly_amount_provided: bool,
        payment_due_day: int | None,
        payment_due_day_provided: bool,
        next_payment_due_date: date | None,
        next_payment_due_date_provided: bool,
        paid_at: datetime | None,
        paid_at_provided: bool,
        billing_notes: str | None,
        billing_notes_provided: bool,
        deadline: date | None,
        archived: bool | None,
    ) -> Project:
        workspace = self._workspace_for_user(user)
        project = self.projects.get_for_workspace(
            project_id=project_id,
            workspace_id=workspace.id,
        )
        if project is None:
            raise NotFoundError("Project not found.")

        if status == ProjectStatus.COMPLETED.value:
            validate_project_completion(task.status for task in project.tasks)

        if title is not None:
            project.title = title.strip()
        if client_name is not None:
            project.client_name = client_name.strip()
        if description is not None:
            project.description = description.strip() or None
        if status is not None:
            project.status = status
            if status == ProjectStatus.ARCHIVED.value:
                project.archived = True
        if priority is not None:
            project.priority = priority
        if budget_cents is not None:
            project.budget_cents = budget_cents
        if hourly_rate_cents is not None:
            project.hourly_rate_cents = hourly_rate_cents
        if contract_type is not None:
            project.contract_type = contract_type
            if contract_type == ContractType.INTERNAL.value:
                project.billing_status = BillingStatus.NOT_BILLABLE.value
                project.payment_status = PaymentStatus.NOT_STARTED.value
        if billing_cycle is not None:
            project.billing_cycle = billing_cycle
        if billing_status is not None:
            project.billing_status = billing_status
            if payment_status is None:
                project.payment_status = _payment_status_for_billing_status(
                    billing_status
                )
        if payment_status is not None:
            project.payment_status = payment_status
            project.billing_status = _billing_status_for_payment_status(payment_status)
            if payment_status == PaymentStatus.PAID.value and not paid_at_provided:
                project.paid_at = datetime.now(UTC).replace(tzinfo=None)
            elif payment_status != PaymentStatus.PAID.value and not paid_at_provided:
                project.paid_at = None
        if billing_currency is not None:
            project.billing_currency = billing_currency.strip().upper()
        if agreed_amount_provided:
            project.agreed_amount = agreed_amount
        if monthly_rate_provided:
            project.monthly_rate = monthly_rate
            if not monthly_amount_provided:
                project.monthly_amount = monthly_rate
        if monthly_amount_provided:
            project.monthly_amount = monthly_amount
            if not monthly_rate_provided:
                project.monthly_rate = monthly_amount
        if payment_due_day_provided:
            project.payment_due_day = payment_due_day
        if next_payment_due_date_provided:
            project.next_payment_due_date = next_payment_due_date
        if paid_at_provided:
            project.paid_at = paid_at
        if billing_notes_provided:
            project.billing_notes = billing_notes.strip() if billing_notes else None
        if deadline is not None:
            project.deadline = deadline
        if archived is not None:
            project.archived = archived
            if archived:
                project.status = ProjectStatus.ARCHIVED.value
        project.updated_at = datetime.now(UTC).replace(tzinfo=None)

        self.projects.save(project)
        self.db.commit()
        self.db.expire_all()
        refreshed = self.projects.get_for_workspace(
            project_id=project_id,
            workspace_id=workspace.id,
        )
        if refreshed is None:
            raise NotFoundError("Project not found.")
        return refreshed

    def delete_project(self, *, user: User, project_id: int) -> None:
        project = self.get_project_for_user(user=user, project_id=project_id)
        self.projects.delete(project)
        self.db.commit()

    def complete_project(self, *, user: User, project_id: int) -> Project:
        workspace = self._workspace_for_user(user)
        project = self.projects.get_for_workspace(
            project_id=project_id,
            workspace_id=workspace.id,
        )
        if project is None:
            raise NotFoundError("Project not found.")
        try:
            validate_project_completion(task.status for task in project.tasks)
        except BusinessRuleError:
            raise
        project.status = ProjectStatus.COMPLETED.value
        project.archived = False
        project.updated_at = datetime.now(UTC).replace(tzinfo=None)
        self.projects.save(project)
        self.db.commit()
        self.db.expire_all()
        refreshed = self.projects.get_for_workspace(
            project_id=project_id,
            workspace_id=workspace.id,
        )
        if refreshed is None:
            raise NotFoundError("Project not found.")
        return refreshed

    def _workspace_for_user(self, user: User):
        workspace = self.workspaces.get_by_user_id(user.id)
        if workspace is None:
            raise NotFoundError("Workspace not found.")
        return workspace
