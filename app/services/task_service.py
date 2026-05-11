from __future__ import annotations

from datetime import UTC, date, datetime

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.domain.enums import TaskStatus
from app.domain.project_rules import validate_task_status_transition
from app.models.task import Task
from app.models.user import User
from app.repositories.project import ProjectRepository
from app.repositories.task import TaskRepository
from app.repositories.workspace import WorkspaceRepository


class TaskService:
    __slots__ = ("db", "projects", "tasks", "workspaces")

    def __init__(self, db: Session) -> None:
        self.db = db
        self.projects = ProjectRepository(db)
        self.tasks = TaskRepository(db)
        self.workspaces = WorkspaceRepository(db)

    def create_task(
        self,
        *,
        user: User,
        project_id: int,
        title: str,
        description: str | None,
        status: str,
        priority: str,
        estimated_minutes: int,
        actual_minutes: int,
        due_date: date | None,
    ) -> Task:
        project = self._get_project_for_user(user=user, project_id=project_id)
        now = datetime.now(UTC).replace(tzinfo=None)
        task = Task(
            project_id=project.id,
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
        user: User,
        task_id: int,
        title: str | None,
        description: str | None,
        status: str | None,
        priority: str | None,
        estimated_minutes: int | None,
        actual_minutes: int | None,
        due_date: date | None,
    ) -> Task:
        task = self.get_task_for_user(user=user, task_id=task_id)
        now = datetime.now(UTC).replace(tzinfo=None)

        if status is not None and status != task.status:
            validate_task_status_transition(task.status, status)
            task.status = status
            task.completed_at = now if status == TaskStatus.DONE.value else None

        if title is not None:
            task.title = title.strip()
        if description is not None:
            task.description = description.strip() or None
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

    def complete_task(
        self,
        *,
        user: User,
        task_id: int,
        actual_minutes: int | None = None,
    ) -> Task:
        task = self.get_task_for_user(user=user, task_id=task_id)
        if task.status != TaskStatus.DONE.value:
            validate_task_status_transition(task.status, TaskStatus.DONE.value)
            task.status = TaskStatus.DONE.value
        if actual_minutes is not None:
            task.actual_minutes = actual_minutes
        now = datetime.now(UTC).replace(tzinfo=None)
        task.completed_at = now
        task.updated_at = now
        self.tasks.save(task)
        self.db.commit()
        self.db.refresh(task)
        return task

    def get_task_for_user(self, *, user: User, task_id: int) -> Task:
        workspace = self.workspaces.get_by_user_id(user.id)
        if workspace is None:
            raise NotFoundError("Workspace not found.")
        task = self.tasks.get_for_workspace(
            task_id=task_id,
            workspace_id=workspace.id,
        )
        if task is None:
            raise NotFoundError("Task not found.")
        return task

    def delete_task(self, *, user: User, task_id: int) -> None:
        task = self.get_task_for_user(user=user, task_id=task_id)
        self.tasks.delete(task)
        self.db.commit()

    def _get_project_for_user(self, *, user: User, project_id: int):
        workspace = self.workspaces.get_by_user_id(user.id)
        if workspace is None:
            raise NotFoundError("Workspace not found.")
        project = self.projects.get_for_workspace(
            project_id=project_id,
            workspace_id=workspace.id,
        )
        if project is None:
            raise NotFoundError("Project not found.")
        return project
