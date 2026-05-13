from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.domain.enums import PaymentMethod, PaymentRecordStatus

SUPPORTED_PAYMENT_CURRENCIES = frozenset({"USD", "EUR", "GBP", "RON"})


class PaymentRecordFields(BaseModel):
    amount_cents: int = Field(gt=0)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    status: PaymentRecordStatus = PaymentRecordStatus.PENDING
    method: PaymentMethod | None = None
    paid_at: datetime | None = None
    due_date: date | None = None
    period_start: date | None = None
    period_end: date | None = None
    notes: str | None = Field(default=None, max_length=2_000)

    @field_validator("currency", mode="before")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        return str(value).strip().upper()

    @model_validator(mode="after")
    def validate_payment_record(self) -> "PaymentRecordFields":
        if self.currency not in SUPPORTED_PAYMENT_CURRENCIES:
            raise ValueError("currency must be one of USD, EUR, GBP, or RON.")
        if self.status == PaymentRecordStatus.PENDING and self.due_date is None:
            raise ValueError("pending payments require due_date.")
        if (
            self.period_start is not None
            and self.period_end is not None
            and self.period_start > self.period_end
        ):
            raise ValueError("period_start cannot be later than period_end.")
        return self


class PaymentRecordCreateRequest(PaymentRecordFields):
    pass


class PaymentRecordUpdateRequest(BaseModel):
    amount_cents: int | None = Field(default=None, gt=0)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    status: PaymentRecordStatus | None = None
    method: PaymentMethod | None = None
    paid_at: datetime | None = None
    due_date: date | None = None
    period_start: date | None = None
    period_end: date | None = None
    notes: str | None = Field(default=None, max_length=2_000)

    @field_validator("currency", mode="before")
    @classmethod
    def normalize_currency(cls, value: str | None) -> str | None:
        return str(value).strip().upper() if value is not None else None

    @model_validator(mode="after")
    def validate_payment_record(self) -> "PaymentRecordUpdateRequest":
        if (
            self.currency is not None
            and self.currency not in SUPPORTED_PAYMENT_CURRENCIES
        ):
            raise ValueError("currency must be one of USD, EUR, GBP, or RON.")
        if (
            self.period_start is not None
            and self.period_end is not None
            and self.period_start > self.period_end
        ):
            raise ValueError("period_start cannot be later than period_end.")
        return self


class PaymentRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    amount_cents: int
    currency: str
    status: PaymentRecordStatus
    is_overdue: bool
    method: PaymentMethod | None
    paid_at: datetime | None
    due_date: date | None
    period_start: date | None
    period_end: date | None
    notes: str | None
    created_at: datetime
    updated_at: datetime
