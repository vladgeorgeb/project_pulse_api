from __future__ import annotations

import pytest

from app.core.exceptions import BusinessRuleError
from app.domain.project_rules import (
    calculate_progress_percent,
    validate_project_completion,
    validate_task_status_transition,
)


def test_calculate_progress_percent_handles_empty_and_partial_tasks() -> None:
    assert calculate_progress_percent(()) == 0
    assert calculate_progress_percent(("done", "todo", "done")) == 66


def test_project_completion_requires_all_tasks_done() -> None:
    validate_project_completion(("done", "done"))

    with pytest.raises(BusinessRuleError):
        validate_project_completion(("done", "in_progress"))


def test_done_task_cannot_be_reopened() -> None:
    with pytest.raises(BusinessRuleError):
        validate_task_status_transition("done", "todo")
