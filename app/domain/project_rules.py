from __future__ import annotations

from collections.abc import Iterable
from datetime import date

from app.core.exceptions import BusinessRuleError, ValidationError
from app.domain.enums import ContractType, PaymentCadence, ProjectStatus, TaskStatus

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


def validate_project_billing_and_dates(
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
        raise ValidationError("monthly_retainer contracts require monthly_rate_cents.")
    if contract_type == ContractType.FIXED_PRICE.value and fixed_price_cents is None:
        raise ValidationError("fixed_price contracts require fixed_price_cents.")
    if (
        contract_type == ContractType.NON_BILLABLE.value
        and payment_cadence != PaymentCadence.NONE.value
    ):
        raise ValidationError("non_billable contracts require payment_cadence 'none'.")
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
