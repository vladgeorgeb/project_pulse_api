from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.exceptions import AuthenticationError, NotFoundError, ValidationError
from app.models.user import User
from app.schemas.account import AccountDeleteRequest, AccountExportResponse
from app.services.account_service import AccountService

router = APIRouter(prefix="/account", tags=["account"])


@router.get("/export", response_model=AccountExportResponse)
def export_account(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AccountExportResponse:
    service = AccountService(db)
    try:
        return service.export_user_data(user=current_user)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(
    payload: AccountDeleteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    service = AccountService(db)
    try:
        service.delete_own_account(
            user=current_user,
            password=payload.password,
            confirm_admin_self_deletion=payload.confirm_admin_self_deletion,
        )
    except AuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
