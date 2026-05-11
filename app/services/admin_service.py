from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.core.security import hash_password
from app.domain.enums import (
    BillingStatus,
    ContractType,
    PaymentStatus,
    ProjectStatus,
    TaskStatus,
)
from app.models.project import Project
from app.models.task import Task
from app.models.user import User
from app.models.workspace import Workspace
from app.repositories.project import ProjectRepository
from app.repositories.task import TaskRepository
from app.repositories.user import UserRepository
from app.repositories.workspace import WorkspaceRepository
from app.schemas.project import MONTHLY_AMOUNT_REQUIRED_MESSAGE
from app.services.auth_token_service import utc_now_naive
from app.services.registration_service import validate_password_strength


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


def _requires_monthly_amount(contract_type: str) -> bool:
    return contract_type in {
        ContractType.MONTHLY_RETAINER.value,
        ContractType.FULL_TIME_MONTHLY.value,
    }


class AdminService:
    __slots__ = ("db", "projects", "tasks", "users", "workspaces")

    def __init__(self, db: Session) -> None:
        self.db = db
        self.users = UserRepository(db)
        self.workspaces = WorkspaceRepository(db)
        self.projects = ProjectRepository(db)
        self.tasks = TaskRepository(db)

    def list_users(self) -> list[User]:
        return self.users.list_all()

    def get_user(self, user_id: int) -> User:
        user = self.users.get_by_id(user_id)
        if user is None:
            raise NotFoundError("User not found.")
        return user

    def create_user(self, *, email: str, password: str, is_admin: bool) -> User:
        normalized_email = email.strip().lower()
        if self.users.get_by_email(normalized_email) is not None:
            raise ConflictError("A user with this email already exists.")
        validate_password_strength(password)
        user = self.users.add(
            email=normalized_email,
            password_hash=hash_password(password),
            is_admin=is_admin,
            email_verified=True,
            email_verified_at=utc_now_naive(),
        )
        self.db.commit()
        self.db.refresh(user)
        return user

    def update_user(
        self,
        *,
        user_id: int,
        email: str | None,
        password: str | None,
        is_admin: bool | None,
    ) -> User:
        user = self.get_user(user_id)
        if email is not None:
            normalized_email = email.strip().lower()
            existing = self.users.get_by_email(normalized_email)
            if existing is not None and existing.id != user.id:
                raise ConflictError("A user with this email already exists.")
            user.email = normalized_email
            user.email_verified = True
            user.email_verified_at = utc_now_naive()
        if password is not None:
            validate_password_strength(password)
            user.password_hash = hash_password(password)
        if is_admin is not None:
            user.is_admin = is_admin
        self.users.save(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def delete_user(self, *, user_id: int) -> None:
        user = self.get_user(user_id)
        self.users.delete(user)
        self.db.commit()

    def list_workspaces(self) -> list[Workspace]:
        return self.workspaces.list_all()

    def get_workspace(self, workspace_id: int) -> Workspace:
        workspace = self.workspaces.get_by_id(workspace_id)
        if workspace is None:
            raise NotFoundError("Workspace not found.")
        return workspace

    def create_workspace(
        self,
        *,
        user_id: int,
        name: str,
        company_name: str,
        monthly_capacity_hours: int,
    ) -> Workspace:
        if monthly_capacity_hours <= 0:
            raise ValidationError("Monthly capacity must be greater than zero.")
        user = self.users.get_by_id(user_id)
        if user is None:
            raise NotFoundError("User not found.")
        if self.workspaces.get_by_user_id(user_id) is not None:
            raise ConflictError("User already has a workspace.")
        workspace = self.workspaces.add(
            user_id=user_id,
            name=name.strip(),
            company_name=company_name.strip(),
            monthly_capacity_hours=monthly_capacity_hours,
        )
        self.db.commit()
        self.db.refresh(workspace)
        return workspace

    def update_workspace(
        self,
        *,
        workspace_id: int,
        user_id: int | None,
        name: str | None,
        company_name: str | None,
        monthly_capacity_hours: int | None,
    ) -> Workspace:
        workspace = self.get_workspace(workspace_id)
        if user_id is not None and user_id != workspace.user_id:
            if self.users.get_by_id(user_id) is None:
                raise NotFoundError("User not found.")
            existing = self.workspaces.get_by_user_id(user_id)
            if existing is not None and existing.id != workspace.id:
                raise ConflictError("User already has a workspace.")
            workspace.user_id = user_id
        if name is not None:
            workspace.name = name.strip()
        if company_name is not None:
            workspace.company_name = company_name.strip()
        if monthly_capacity_hours is not None:
            if monthly_capacity_hours <= 0:
                raise ValidationError("Monthly capacity must be greater than zero.")
            workspace.monthly_capacity_hours = monthly_capacity_hours
        self.workspaces.save(workspace)
        self.db.commit()
        self.db.refresh(workspace)
        return workspace

    def delete_workspace(self, *, workspace_id: int) -> None:
        workspace = self.get_workspace(workspace_id)
        self.workspaces.delete(workspace)
        self.db.commit()

    def list_projects(self) -> list[Project]:
        return self.projects.list_all()

    def get_project(self, project_id: int) -> Project:
        project = self.projects.get_by_id(project_id)
        if project is None:
            raise NotFoundError("Project not found.")
        return project

    def create_project(
        self,
        *,
        workspace_id: int,
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
        if self.workspaces.get_by_id(workspace_id) is None:
            raise NotFoundError("Workspace not found.")
        if contract_type == ContractType.INTERNAL.value:
            billing_status = BillingStatus.NOT_BILLABLE.value
            payment_status = PaymentStatus.NOT_STARTED.value
        if _requires_monthly_amount(contract_type) and monthly_amount is None:
            raise ValidationError(MONTHLY_AMOUNT_REQUIRED_MESSAGE)
        if payment_status == PaymentStatus.PAID.value and paid_at is None:
            paid_at = datetime.now(UTC).replace(tzinfo=None)
        now = datetime.now(UTC).replace(tzinfo=None)
        project = Project(
            workspace_id=workspace_id,
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
        return project

    def update_project(
        self,
        *,
        project_id: int,
        workspace_id: int | None,
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
        project = self.get_project(project_id)
        if workspace_id is not None:
            if self.workspaces.get_by_id(workspace_id) is None:
                raise NotFoundError("Workspace not found.")
            project.workspace_id = workspace_id
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
        if (
            _requires_monthly_amount(project.contract_type)
            and project.monthly_amount is None
        ):
            raise ValidationError(MONTHLY_AMOUNT_REQUIRED_MESSAGE)
        project.updated_at = datetime.now(UTC).replace(tzinfo=None)
        self.projects.save(project)
        self.db.commit()
        self.db.refresh(project)
        return project

    def delete_project(self, *, project_id: int) -> None:
        project = self.get_project(project_id)
        self.projects.delete(project)
        self.db.commit()

    def list_tasks(self) -> list[Task]:
        return self.tasks.list_all()

    def get_task(self, task_id: int) -> Task:
        task = self.tasks.get_by_id(task_id)
        if task is None:
            raise NotFoundError("Task not found.")
        return task

    def create_task(
        self,
        *,
        project_id: int,
        title: str,
        description: str | None,
        status: str,
        priority: str,
        estimated_minutes: int,
        actual_minutes: int,
        due_date: date | None,
    ) -> Task:
        if self.projects.get_by_id(project_id) is None:
            raise NotFoundError("Project not found.")
        now = datetime.now(UTC).replace(tzinfo=None)
        task = Task(
            project_id=project_id,
            title=title.strip(),
            description=description.strip() if description else None,
            status=status,
            priority=priority,
            estimated_minutes=estimated_minutes,
            actual_minutes=actual_minutes,
            due_date=due_date,
            completed_at=now if status == TaskStatus.DONE.value else None,
            created_at=now,
            updated_at=now,
        )
        self.tasks.add(task)
        self.db.commit()
        self.db.refresh(task)
        return task

    def update_task(
        self,
        *,
        task_id: int,
        project_id: int | None,
        title: str | None,
        description: str | None,
        status: str | None,
        priority: str | None,
        estimated_minutes: int | None,
        actual_minutes: int | None,
        due_date: date | None,
    ) -> Task:
        task = self.get_task(task_id)
        now = datetime.now(UTC).replace(tzinfo=None)
        if project_id is not None:
            if self.projects.get_by_id(project_id) is None:
                raise NotFoundError("Project not found.")
            task.project_id = project_id
        if title is not None:
            task.title = title.strip()
        if description is not None:
            task.description = description.strip() or None
        if status is not None:
            task.status = status
            task.completed_at = now if status == TaskStatus.DONE.value else None
        if priority is not None:
            task.priority = priority
        if estimated_minutes is not None:
            task.estimated_minutes = estimated_minutes
        if actual_minutes is not None:
            task.actual_minutes = actual_minutes
        if due_date is not None:
            task.due_date = due_date
        task.updated_at = now
        self.tasks.save(task)
        self.db.commit()
        self.db.refresh(task)
        return task

    def delete_task(self, *, task_id: int) -> None:
        task = self.get_task(task_id)
        self.tasks.delete(task)
        self.db.commit()
