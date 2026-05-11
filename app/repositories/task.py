from __future__ import annotations

from datetime import date

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.domain.enums import TaskStatus
from app.models.project import Project
from app.models.task import Task


class TaskRepository:
    __slots__ = ("db",)

    def __init__(self, db: Session) -> None:
        self.db = db

    def add(self, task: Task) -> Task:
        self.db.add(task)
        self.db.flush()
        return task

    def list_all(self) -> list[Task]:
        stmt = select(Task).order_by(Task.id)
        return list(self.db.execute(stmt).scalars().all())

    def list_by_project_id(self, project_id: int) -> list[Task]:
        stmt = select(Task).where(Task.project_id == project_id).order_by(Task.id)
        return list(self.db.execute(stmt).scalars().all())

    def list_overdue_for_projects(
        self,
        project_ids: list[int],
        today: date,
    ) -> list[Task]:
        if not project_ids:
            return []
        stmt = select(Task).where(
            and_(
                Task.project_id.in_(project_ids),
                Task.due_date.is_not(None),
                Task.due_date < today,
                Task.status != TaskStatus.DONE.value,
            )
        )
        return list(self.db.execute(stmt).scalars().all())

    def get_by_id(self, task_id: int) -> Task | None:
        stmt = select(Task).where(Task.id == task_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_for_workspace(self, *, task_id: int, workspace_id: int) -> Task | None:
        stmt = (
            select(Task)
            .join(Project, Task.project_id == Project.id)
            .where(Task.id == task_id, Project.workspace_id == workspace_id)
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def save(self, task: Task) -> Task:
        self.db.add(task)
        self.db.flush()
        return task

    def delete(self, task: Task) -> None:
        self.db.delete(task)
        self.db.flush()
