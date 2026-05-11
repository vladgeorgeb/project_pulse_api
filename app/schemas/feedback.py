from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.domain.enums import FeedbackCategory, FeedbackStatus


class FeedbackCreateRequest(BaseModel):
    category: FeedbackCategory
    message: str = Field(min_length=10, max_length=2_000)
    page_url: str | None = Field(default=None, max_length=2_048)

    @field_validator("message")
    @classmethod
    def normalize_message(cls, value: str) -> str:
        message = value.strip()
        if len(message) < 10:
            raise ValueError("Feedback message must be at least 10 characters.")
        return message

    @field_validator("page_url")
    @classmethod
    def normalize_page_url(cls, value: str | None) -> str | None:
        if value is None:
            return None
        page_url = value.strip()
        return page_url or None


class FeedbackResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    category: FeedbackCategory
    message: str
    page_url: str | None
    status: FeedbackStatus
    created_at: datetime


class AdminFeedbackResponse(FeedbackResponse):
    user_id: int | None
    user_agent: str | None
