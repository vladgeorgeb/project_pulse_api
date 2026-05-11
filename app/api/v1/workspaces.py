from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.serializers import to_workspace_response
from app.core.database import get_db
from app.core.exceptions import NotFoundError, ValidationError
from app.models.user import User
from app.schemas.workspace import WorkspaceResponse, WorkspaceUpdateRequest
from app.services.workspace_service import WorkspaceService

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


@router.get("/me", response_model=WorkspaceResponse)
def get_my_workspace(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> WorkspaceResponse:
    service = WorkspaceService(db)
    try:
        workspace = service.get_workspace_for_user(current_user)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return to_workspace_response(workspace)


@router.put("/me", response_model=WorkspaceResponse)
def update_my_workspace(
    payload: WorkspaceUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> WorkspaceResponse:
    service = WorkspaceService(db)
    try:
        workspace = service.update_workspace_for_user(
            user=current_user,
            name=payload.name,
            company_name=payload.company_name,
            monthly_capacity_hours=payload.monthly_capacity_hours,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return to_workspace_response(workspace)
