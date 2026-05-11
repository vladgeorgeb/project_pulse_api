from __future__ import annotations

from datetime import date

from sqlalchemy import Select, and_, func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.domain.enums import ProjectStatus
from app.models.project import Project


class ProjectRepository:
    __slots__ = ("db",)

    def __init__(self, db: Session) -> None:
        self.db = db

    def add(self, project: Project) -> Project:
        self.db.add(project)
        self.db.flush()
        return project

    def list_all(self) -> list[Project]:
        stmt = (
            select(Project)
            .options(joinedload(Project.tasks))
            .order_by(Project.id)
            .execution_options(populate_existing=True)
        )
        return list(self.db.execute(stmt).unique().scalars().all())

    def get_by_id(self, project_id: int) -> Project | None:
        stmt = (
            select(Project)
            .options(joinedload(Project.tasks))
            .where(Project.id == project_id)
            .execution_options(populate_existing=True)
        )
        return self.db.execute(stmt).unique().scalar_one_or_none()

    def get_for_workspace(
        self,
        *,
        project_id: int,
        workspace_id: int,
    ) -> Project | None:
        stmt = (
            select(Project)
            .options(joinedload(Project.tasks))
            .where(Project.id == project_id, Project.workspace_id == workspace_id)
            .execution_options(populate_existing=True)
        )
        return self.db.execute(stmt).unique().scalar_one_or_none()

    def list_for_workspace(
        self,
        *,
        workspace_id: int,
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
        today: date | None = None,
    ) -> list[Project]:
        stmt: Select[tuple[Project]] = (
            select(Project)
            .options(joinedload(Project.tasks))
            .where(Project.workspace_id == workspace_id)
        )

        if not include_archived:
            stmt = stmt.where(Project.archived.is_(False))

        if status is not None:
            stmt = stmt.where(Project.status == status)

        if priority is not None:
            stmt = stmt.where(Project.priority == priority)

        if client_name is not None:
            pattern = f"%{client_name.strip().lower()}%"
            stmt = stmt.where(func.lower(Project.client_name).like(pattern))

        if search is not None:
            pattern = f"%{search.strip().lower()}%"
            stmt = stmt.where(
                or_(
                    func.lower(Project.title).like(pattern),
                    func.lower(Project.client_name).like(pattern),
                    func.lower(Project.description).like(pattern),
                )
            )

        if min_budget_cents is not None:
            stmt = stmt.where(Project.budget_cents >= min_budget_cents)

        if max_budget_cents is not None:
            stmt = stmt.where(Project.budget_cents <= max_budget_cents)

        if due_before is not None:
            stmt = stmt.where(Project.deadline <= due_before)

        if due_after is not None:
            stmt = stmt.where(Project.deadline >= due_after)

        if overdue_only:
            today = today or date.today()
            stmt = stmt.where(
                and_(
                    Project.deadline.is_not(None),
                    Project.deadline < today,
                    Project.status.notin_(
                        (ProjectStatus.COMPLETED.value, ProjectStatus.ARCHIVED.value)
                    ),
                )
            )

        stmt = stmt.order_by(Project.deadline.is_(None), Project.deadline, Project.id)
        return list(self.db.execute(stmt).unique().scalars().all())

    def save(self, project: Project) -> Project:
        self.db.add(project)
        self.db.flush()
        return project

    def delete(self, project: Project) -> None:
        self.db.delete(project)
        self.db.flush()
