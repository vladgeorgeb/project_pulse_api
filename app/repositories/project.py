from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from sqlalchemy import Select, and_, case, func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.domain.enums import ProjectStatus
from app.models.project import Project


@dataclass(frozen=True)
class PaginatedProjects:
    items: list[Project]
    total: int


PROJECT_SORT_COLUMNS = {
    "id": Project.id,
    "title": Project.title,
    "client_name": Project.client_name,
    "status": Project.status,
    "priority": case(
        (Project.priority == "urgent", 0),
        (Project.priority == "high", 1),
        (Project.priority == "medium", 2),
        (Project.priority == "low", 3),
        else_=4,
    ),
    "budget_cents": Project.budget_cents,
    "hourly_rate_cents": Project.hourly_rate_cents,
    "deadline": Project.deadline,
    "created_at": Project.created_at,
    "updated_at": Project.updated_at,
}


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
            .options(joinedload(Project.tasks), joinedload(Project.payment_records))
            .order_by(Project.id)
            .execution_options(populate_existing=True)
        )
        return list(self.db.execute(stmt).unique().scalars().all())

    def get_by_id(self, project_id: int) -> Project | None:
        stmt = (
            select(Project)
            .options(joinedload(Project.tasks), joinedload(Project.payment_records))
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
            .options(joinedload(Project.tasks), joinedload(Project.payment_records))
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
        return self.paginate_for_workspace(
            workspace_id=workspace_id,
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
            today=today,
            page=1,
            page_size=100_000,
            sort_by="priority",
            sort_dir="asc",
        ).items

    def paginate_for_workspace(
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
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "priority",
        sort_dir: str = "asc",
    ) -> PaginatedProjects:
        stmt: Select[tuple[Project]] = (
            select(Project)
            .options(joinedload(Project.tasks), joinedload(Project.payment_records))
            .where(Project.workspace_id == workspace_id)
        )
        count_stmt = select(func.count(Project.id)).where(
            Project.workspace_id == workspace_id
        )

        if not include_archived:
            stmt = stmt.where(Project.archived.is_(False))
            count_stmt = count_stmt.where(Project.archived.is_(False))

        if status is not None:
            stmt = stmt.where(Project.status == status)
            count_stmt = count_stmt.where(Project.status == status)

        if priority is not None:
            stmt = stmt.where(Project.priority == priority)
            count_stmt = count_stmt.where(Project.priority == priority)

        if client_name is not None:
            pattern = f"%{client_name.strip().lower()}%"
            stmt = stmt.where(func.lower(Project.client_name).like(pattern))
            count_stmt = count_stmt.where(func.lower(Project.client_name).like(pattern))

        if search is not None:
            pattern = f"%{search.strip().lower()}%"
            search_filter = or_(
                func.lower(Project.title).like(pattern),
                func.lower(Project.client_name).like(pattern),
                func.lower(Project.description).like(pattern),
            )
            stmt = stmt.where(search_filter)
            count_stmt = count_stmt.where(search_filter)

        if min_budget_cents is not None:
            stmt = stmt.where(Project.budget_cents >= min_budget_cents)
            count_stmt = count_stmt.where(Project.budget_cents >= min_budget_cents)

        if max_budget_cents is not None:
            stmt = stmt.where(Project.budget_cents <= max_budget_cents)
            count_stmt = count_stmt.where(Project.budget_cents <= max_budget_cents)

        if due_before is not None:
            stmt = stmt.where(Project.deadline <= due_before)
            count_stmt = count_stmt.where(Project.deadline <= due_before)

        if due_after is not None:
            stmt = stmt.where(Project.deadline >= due_after)
            count_stmt = count_stmt.where(Project.deadline >= due_after)

        if overdue_only:
            today = today or date.today()
            overdue_filter = and_(
                Project.deadline.is_not(None),
                Project.deadline < today,
                Project.status.notin_(
                    (ProjectStatus.COMPLETED.value, ProjectStatus.ARCHIVED.value)
                ),
            )
            stmt = stmt.where(overdue_filter)
            count_stmt = count_stmt.where(overdue_filter)

        sort_column = PROJECT_SORT_COLUMNS[sort_by]
        sorted_column = sort_column.asc() if sort_dir == "asc" else sort_column.desc()
        sort_order = [sort_column.is_(None), sorted_column]
        if sort_by == "priority":
            sort_order.append(Project.deadline.is_(None))
            sort_order.append(Project.deadline)
        sort_order.append(Project.id)
        stmt = (
            stmt.order_by(*sort_order).offset((page - 1) * page_size).limit(page_size)
        )

        total = self.db.execute(count_stmt).scalar_one()
        items = list(self.db.execute(stmt).unique().scalars().all())
        return PaginatedProjects(items=items, total=total)

    def save(self, project: Project) -> Project:
        self.db.add(project)
        self.db.flush()
        return project

    def delete(self, project: Project) -> None:
        self.db.delete(project)
        self.db.flush()
