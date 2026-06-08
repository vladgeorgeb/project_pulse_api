from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.exceptions import NotFoundError
from app.models.user import User
from app.schemas.dashboard import DashboardSummaryResponse
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummaryResponse)
def get_dashboard_summary(
    month: str | None = Query(
        default=None,
        description="Selected month as YYYY-MM or any date within the month.",
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DashboardSummaryResponse:
    selected_month = _parse_month(month)
    try:
        summary = DashboardService(db).get_summary_for_user(
            current_user, selected_month=selected_month
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return DashboardSummaryResponse.model_validate(summary)


def _parse_month(value: str | None) -> date | None:
    if value is None or not value.strip():
        return None
    normalized = value.strip()
    try:
        if len(normalized) == 7:
            return date.fromisoformat(f"{normalized}-01")
        return date.fromisoformat(normalized).replace(day=1)
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail="month must use YYYY-MM or YYYY-MM-DD format.",
        ) from exc
