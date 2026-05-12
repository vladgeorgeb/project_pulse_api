from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.project import Project
from app.models.workspace import Workspace


class WorkspaceRepository:
    __slots__ = ("db",)

    def __init__(self, db: Session) -> None:
        self.db = db

    def add(
        self,
        *,
        user_id: int,
        name: str,
        company_name: str,
        monthly_capacity_hours: int,
    ) -> Workspace:
        workspace = Workspace(
            user_id=user_id,
            name=name,
            company_name=company_name,
            monthly_capacity_hours=monthly_capacity_hours,
        )
        self.db.add(workspace)
        self.db.flush()
        return workspace

    def list_all(self) -> list[Workspace]:
        stmt = select(Workspace).order_by(Workspace.id)
        return list(self.db.execute(stmt).scalars().all())

    def get_by_id(self, workspace_id: int) -> Workspace | None:
        stmt = select(Workspace).where(Workspace.id == workspace_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_user_id(self, user_id: int) -> Workspace | None:
        stmt = (
            select(Workspace)
            .options(
                joinedload(Workspace.projects).joinedload(Project.tasks),
                joinedload(Workspace.projects).joinedload(Project.payment_records),
            )
            .where(Workspace.user_id == user_id)
            .execution_options(populate_existing=True)
        )
        return self.db.execute(stmt).unique().scalar_one_or_none()

    def save(self, workspace: Workspace) -> Workspace:
        self.db.add(workspace)
        self.db.flush()
        return workspace

    def delete(self, workspace: Workspace) -> None:
        self.db.delete(workspace)
        self.db.flush()
