from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, ValidationError
from app.domain.enums import ContractType, PaymentCadence, ProjectStatus
from app.domain.project_rules import validate_project_completion
from app.models.project import Project
from app.models.user import User
from app.repositories.project import PaginatedProjects, ProjectRepository
from app.repositories.workspace import WorkspaceRepository


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
            project_id=project_id, workspace_id=workspace.id
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
        contract_type: str,
        billing_currency: str,
        hourly_rate_cents: int | None,
        expected_hours_per_week: Decimal | None,
        monthly_rate_cents: int | None,
        fixed_price_cents: int | None,
        start_date: date | None,
        estimated_end_date: date | None,
        deadline: date | None,
        payment_cadence: str,
        billing_notes: str | None,
    ) -> Project:
        workspace = self._workspace_for_user(user)
        self._validate_contract_fields(
            contract_type=contract_type,
            hourly_rate_cents=hourly_rate_cents,
            monthly_rate_cents=monthly_rate_cents,
            fixed_price_cents=fixed_price_cents,
            payment_cadence=payment_cadence,
            start_date=start_date,
            estimated_end_date=estimated_end_date,
        )

        now = datetime.now(UTC).replace(tzinfo=None)
        project = Project(
            workspace_id=workspace.id,
            title=title.strip(),
            client_name=client_name.strip(),
            description=description.strip() if description else None,
            status=status,
            priority=priority,
            contract_type=contract_type,
            billing_currency=billing_currency.strip().upper(),
            hourly_rate_cents=hourly_rate_cents,
            expected_hours_per_week=expected_hours_per_week,
            monthly_rate_cents=monthly_rate_cents,
            fixed_price_cents=fixed_price_cents,
            start_date=start_date,
            estimated_end_date=estimated_end_date,
            deadline=deadline,
            payment_cadence=payment_cadence,
            billing_notes=billing_notes.strip() if billing_notes else None,
            archived=status == ProjectStatus.ARCHIVED.value,
            created_at=now,
            updated_at=now,
        )
        self.projects.add(project)
        self.db.commit()
        self.db.refresh(project)
        return (
            self.projects.get_for_workspace(
                project_id=project.id, workspace_id=workspace.id
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
        contract_type: str | None,
        billing_currency: str | None,
        hourly_rate_cents: int | None,
        expected_hours_per_week: Decimal | None,
        expected_hours_per_week_provided: bool,
        monthly_rate_cents: int | None,
        monthly_rate_cents_provided: bool,
        fixed_price_cents: int | None,
        fixed_price_cents_provided: bool,
        start_date: date | None,
        start_date_provided: bool,
        estimated_end_date: date | None,
        estimated_end_date_provided: bool,
        deadline: date | None,
        payment_cadence: str | None,
        billing_notes: str | None,
        billing_notes_provided: bool,
        archived: bool | None,
    ) -> Project:
        workspace = self._workspace_for_user(user)
        project = self.projects.get_for_workspace(
            project_id=project_id, workspace_id=workspace.id
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
        if contract_type is not None:
            project.contract_type = contract_type
        if billing_currency is not None:
            project.billing_currency = billing_currency.strip().upper()
        if hourly_rate_cents is not None:
            project.hourly_rate_cents = hourly_rate_cents
        if expected_hours_per_week_provided:
            project.expected_hours_per_week = expected_hours_per_week
        if monthly_rate_cents_provided:
            project.monthly_rate_cents = monthly_rate_cents
        if fixed_price_cents_provided:
            project.fixed_price_cents = fixed_price_cents
        if start_date_provided:
            project.start_date = start_date
        if estimated_end_date_provided:
            project.estimated_end_date = estimated_end_date
        if deadline is not None:
            project.deadline = deadline
        if payment_cadence is not None:
            project.payment_cadence = payment_cadence
        if billing_notes_provided:
            project.billing_notes = billing_notes.strip() if billing_notes else None
        if archived is not None:
            project.archived = archived
            if archived:
                project.status = ProjectStatus.ARCHIVED.value

        self._validate_contract_fields(
            contract_type=project.contract_type,
            hourly_rate_cents=project.hourly_rate_cents,
            monthly_rate_cents=project.monthly_rate_cents,
            fixed_price_cents=project.fixed_price_cents,
            payment_cadence=project.payment_cadence,
            start_date=project.start_date,
            estimated_end_date=project.estimated_end_date,
        )

        project.updated_at = datetime.now(UTC).replace(tzinfo=None)

        self.projects.save(project)
        self.db.commit()
        self.db.expire_all()
        refreshed = self.projects.get_for_workspace(
            project_id=project_id, workspace_id=workspace.id
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
            project_id=project_id, workspace_id=workspace.id
        )
        if project is None:
            raise NotFoundError("Project not found.")
        validate_project_completion(task.status for task in project.tasks)
        project.status = ProjectStatus.COMPLETED.value
        project.archived = False
        project.updated_at = datetime.now(UTC).replace(tzinfo=None)
        self.projects.save(project)
        self.db.commit()
        self.db.expire_all()
        refreshed = self.projects.get_for_workspace(
            project_id=project_id, workspace_id=workspace.id
        )
        if refreshed is None:
            raise NotFoundError("Project not found.")
        return refreshed

    def _workspace_for_user(self, user: User):
        workspace = self.workspaces.get_by_user_id(user.id)
        if workspace is None:
            raise NotFoundError("Workspace not found.")
        return workspace

    def _validate_contract_fields(
        self,
        *,
        contract_type: str,
        hourly_rate_cents: int | None,
        monthly_rate_cents: int | None,
        fixed_price_cents: int | None,
        payment_cadence: str,
        start_date: date | None,
        estimated_end_date: date | None,
    ) -> None:
        if contract_type == ContractType.HOURLY.value and hourly_rate_cents is None:
            raise ValidationError("hourly contracts require hourly_rate_cents.")
        if (
            contract_type == ContractType.MONTHLY_RETAINER.value
            and monthly_rate_cents is None
        ):
            raise ValidationError(
                "monthly_retainer contracts require monthly_rate_cents."
            )
        if (
            contract_type == ContractType.FIXED_PRICE.value
            and fixed_price_cents is None
        ):
            raise ValidationError("fixed_price contracts require fixed_price_cents.")
        if (
            contract_type == ContractType.NON_BILLABLE.value
            and payment_cadence != PaymentCadence.NONE.value
        ):
            raise ValidationError(
                "non_billable contracts require payment_cadence 'none'."
            )
        if (
            contract_type != ContractType.NON_BILLABLE.value
            and payment_cadence == PaymentCadence.NONE.value
        ):
            raise ValidationError(
                "payment_cadence 'none' is only valid for non_billable contracts."
            )
        if (
            start_date is not None
            and estimated_end_date is not None
            and start_date > estimated_end_date
        ):
            raise ValidationError("start_date cannot be later than estimated_end_date.")
