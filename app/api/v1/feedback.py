from __future__ import annotations

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.observability import log_business_event
from app.models.user import User
from app.schemas.feedback import FeedbackCreateRequest, FeedbackResponse
from app.services.feedback_service import FeedbackService

router = APIRouter(prefix="/feedback", tags=["feedback"])


@router.post(
    "",
    response_model=FeedbackResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_feedback(
    payload: FeedbackCreateRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FeedbackResponse:
    feedback = FeedbackService(db).create_feedback(
        user=current_user,
        category=payload.category.value,
        message=payload.message,
        page_url=payload.page_url,
        user_agent=request.headers.get("user-agent"),
    )
    log_business_event(
        "feedback_submitted",
        request=request,
        user_id=current_user.id,
        feedback_id=feedback.id,
        category=feedback.category,
    )
    return FeedbackResponse.model_validate(feedback)
