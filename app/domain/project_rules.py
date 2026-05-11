from __future__ import annotations

from collections.abc import Iterable

from app.core.exceptions import BusinessRuleError, ValidationError
from app.domain.enums import ProjectStatus, TaskStatus

_OPEN_TASK_STATUSES = {
    TaskStatus.TODO.value,
    TaskStatus.IN_PROGRESS.value,
    TaskStatus.BLOCKED.value,
}
_ALLOWED_TASK_TRANSITIONS: dict[str, set[str]] = {
    TaskStatus.TODO.value: {
        TaskStatus.TODO.value,
        TaskStatus.IN_PROGRESS.value,
        TaskStatus.BLOCKED.value,
        TaskStatus.DONE.value,
    },
    TaskStatus.IN_PROGRESS.value: {
        TaskStatus.TODO.value,
        TaskStatus.IN_PROGRESS.value,
        TaskStatus.BLOCKED.value,
        TaskStatus.DONE.value,
    },
    TaskStatus.BLOCKED.value: {
        TaskStatus.TODO.value,
        TaskStatus.IN_PROGRESS.value,
        TaskStatus.BLOCKED.value,
    },
    TaskStatus.DONE.value: {TaskStatus.DONE.value},
}


def validate_project_completion(task_statuses: Iterable[str]) -> None:
    """Require all project tasks to be done before completing a project."""
    if any(status in _OPEN_TASK_STATUSES for status in task_statuses):
        raise BusinessRuleError("All project tasks must be done before completion.")


def validate_task_status_transition(current_status: str, next_status: str) -> None:
    """Validate a task status change against allowed workflow transitions."""
    allowed = _ALLOWED_TASK_TRANSITIONS.get(current_status)
    if allowed is None:
        raise ValidationError(f"Unknown current task status: {current_status}.")
    if next_status not in allowed:
        raise BusinessRuleError(
            f"Cannot move task from '{current_status}' to '{next_status}'."
        )


def calculate_progress_percent(task_statuses: Iterable[str]) -> int:
    """Return completion percentage as an integer from 0 to 100."""
    statuses = tuple(task_statuses)
    if not statuses:
        return 0
    completed = sum(1 for status in statuses if status == TaskStatus.DONE.value)
    return completed * 100 // len(statuses)


def is_project_open(status: str) -> bool:
    return status not in {ProjectStatus.COMPLETED.value, ProjectStatus.ARCHIVED.value}
