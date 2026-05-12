from __future__ import annotations

from enum import StrEnum


class ProjectStatus(StrEnum):
    PLANNED = "planned"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class ContractType(StrEnum):
    HOURLY = "hourly"
    MONTHLY_RETAINER = "monthly_retainer"
    FIXED_PRICE = "fixed_price"
    NON_BILLABLE = "non_billable"


class PaymentCadence(StrEnum):
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"
    MILESTONE = "milestone"
    MANUAL = "manual"
    NONE = "none"


class PaymentRecordStatus(StrEnum):
    PENDING = "pending"
    PAID = "paid"
    CANCELLED = "cancelled"


class PaymentMethod(StrEnum):
    WIRE = "wire"
    BANK_TRANSFER = "bank_transfer"
    CARD = "card"
    CASH = "cash"
    OTHER = "other"


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


class FeedbackCategory(StrEnum):
    BUG = "bug"
    IDEA = "idea"
    QUESTION = "question"
    OTHER = "other"


class FeedbackStatus(StrEnum):
    NEW = "new"
    REVIEWED = "reviewed"
