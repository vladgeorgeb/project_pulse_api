from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import AuthenticationError, ConflictError, ValidationError
from app.core.rate_limit import auth_rate_limiter
from app.schemas.auth import TokenResponse, UserRegisterRequest
from app.services.auth_service import AuthService
from app.services.registration_service import RegistrationService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_user(
    request: Request,
    payload: UserRegisterRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    auth_rate_limiter.enforce(
        action="register",
        request=request,
        identifier=str(payload.email),
    )
    registration_service = RegistrationService(db)
    auth_service = AuthService(db)

    try:
        user = registration_service.register_user(
            email=payload.email,
            password=payload.password,
        )
    except ConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    token = auth_service.issue_access_token(user)
    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse)
def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> TokenResponse:
    auth_rate_limiter.enforce(
        action="login",
        request=request,
        identifier=form_data.username,
    )
    service = AuthService(db)
    try:
        user = service.authenticate(
            email=form_data.username,
            password=form_data.password,
        )
    except AuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    token = service.issue_access_token(user)
    return TokenResponse(access_token=token)
