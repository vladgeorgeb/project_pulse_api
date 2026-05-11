from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, ValidationError
from app.models.user import User
from app.models.workspace import Workspace
from app.repositories.workspace import WorkspaceRepository


class WorkspaceService:
    __slots__ = ("db", "workspaces")

    def __init__(self, db: Session) -> None:
        self.db = db
        self.workspaces = WorkspaceRepository(db)

    def get_workspace_for_user(self, user: User) -> Workspace:
        workspace = self.workspaces.get_by_user_id(user.id)
        if workspace is None:
            raise NotFoundError("Workspace not found.")
        return workspace

    def update_workspace_for_user(
        self,
        *,
        user: User,
        name: str,
        company_name: str,
        monthly_capacity_hours: int,
    ) -> Workspace:
        if monthly_capacity_hours <= 0:
            raise ValidationError("Monthly capacity must be greater than zero.")
        workspace = self.get_workspace_for_user(user)
        workspace.name = name.strip()
        workspace.company_name = company_name.strip()
        workspace.monthly_capacity_hours = monthly_capacity_hours
        self.workspaces.save(workspace)
        self.db.commit()
        self.db.refresh(workspace)
        return self.get_workspace_for_user(user)
