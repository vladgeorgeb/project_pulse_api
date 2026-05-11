from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.core.exceptions import AuthenticationError, ConflictError, ValidationError
from app.core.rate_limit import auth_rate_limiter
from app.schemas.auth import (
    EmailConfirmationRequest,
    EmailVerificationRequiredResponse,
    MessageResponse,
    PasswordResetConfirmRequest,
    PasswordResetRequest,
    TokenResponse,
    UserRegisterRequest,
)
from app.services.account_recovery_service import AccountRecoveryService
from app.services.auth_service import AuthService
from app.services.email_verification_service import EmailVerificationService
from app.services.registration_service import RegistrationService

router = APIRouter(prefix="/auth", tags=["auth"])
PASSWORD_RESET_REQUEST_MESSAGE = (
    "If an account exists for that email, password reset instructions have been sent."
)
PASSWORD_RESET_CONFIRM_MESSAGE = "Password has been reset."
EMAIL_CONFIRMATION_MESSAGE = "Email address confirmed."
EMAIL_VERIFICATION_REQUIRED_MESSAGE = (
    "Email verification is required before login. Please check your email."
)


@router.post(
    "/register",
    response_model=TokenResponse | EmailVerificationRequiredResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_user(
    request: Request,
    payload: UserRegisterRequest,
    response: Response,
    db: Session = Depends(get_db),
) -> TokenResponse | EmailVerificationRequiredResponse:
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

    if get_settings().require_verified_email:
        response.status_code = status.HTTP_202_ACCEPTED
        return EmailVerificationRequiredResponse(
            message=EMAIL_VERIFICATION_REQUIRED_MESSAGE,
        )

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


@router.post(
    "/password-reset/request",
    response_model=MessageResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def request_password_reset(
    request: Request,
    payload: PasswordResetRequest,
    db: Session = Depends(get_db),
) -> MessageResponse:
    auth_rate_limiter.enforce(
        action="password_reset",
        request=request,
        identifier=str(payload.email),
    )
    service = AccountRecoveryService(db)
    service.request_password_reset(email=payload.email)
    return MessageResponse(message=PASSWORD_RESET_REQUEST_MESSAGE)


@router.post("/password-reset/confirm", response_model=MessageResponse)
def confirm_password_reset(
    payload: PasswordResetConfirmRequest,
    db: Session = Depends(get_db),
) -> MessageResponse:
    service = AccountRecoveryService(db)
    try:
        service.reset_password(
            token=payload.token,
            new_password=payload.new_password,
        )
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return MessageResponse(message=PASSWORD_RESET_CONFIRM_MESSAGE)


@router.post("/email/confirm", response_model=MessageResponse)
def confirm_email(
    payload: EmailConfirmationRequest,
    db: Session = Depends(get_db),
) -> MessageResponse:
    service = EmailVerificationService(db)
    try:
        service.confirm_email(token=payload.token)
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return MessageResponse(message=EMAIL_CONFIRMATION_MESSAGE)
