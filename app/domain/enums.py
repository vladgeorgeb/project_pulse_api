from __future__ import annotations

from enum import StrEnum


class ProjectStatus(StrEnum):
    PLANNED = "planned"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class ContractType(StrEnum):
    FIXED_PRICE = "fixed_price"
    HOURLY = "hourly"
    MONTHLY_RETAINER = "monthly_retainer"
    FULL_TIME_MONTHLY = "full_time_monthly"
    INTERNAL = "internal"


class BillingCycle(StrEnum):
    MONTHLY = "monthly"


class BillingStatus(StrEnum):
    NOT_BILLABLE = "not_billable"
    UNPAID = "unpaid"
    PARTIALLY_PAID = "partially_paid"
    PAID = "paid"
    OVERDUE = "overdue"


class PaymentStatus(StrEnum):
    NOT_STARTED = "not_started"
    PENDING = "pending"
    PAID = "paid"
    OVERDUE = "overdue"


class TaskStatus(StrEnum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    DONE = "done"


class Priority(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"
