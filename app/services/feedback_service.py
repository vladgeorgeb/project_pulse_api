from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.enums import FeedbackStatus
from app.models.feedback import Feedback
from app.models.user import User


class FeedbackService:
    __slots__ = ("db",)

    def __init__(self, db: Session) -> None:
        self.db = db

    def create_feedback(
        self,
        *,
        user: User,
        category: str,
        message: str,
        page_url: str | None,
        user_agent: str | None,
    ) -> Feedback:
        feedback = Feedback(
            user_id=user.id,
            category=category,
            message=message.strip(),
            page_url=page_url.strip() if page_url else None,
            user_agent=user_agent[:512] if user_agent else None,
            status=FeedbackStatus.NEW.value,
            created_at=datetime.now(UTC).replace(tzinfo=None),
        )
        self.db.add(feedback)
        self.db.commit()
        self.db.refresh(feedback)
        return feedback

    def list_feedback(self) -> list[Feedback]:
        return list(
            self.db.scalars(
                select(Feedback).order_by(
                    Feedback.created_at.desc(), Feedback.id.desc()
                )
            )
        )
