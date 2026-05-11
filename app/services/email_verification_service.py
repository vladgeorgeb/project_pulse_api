from __future__ import annotations

from datetime import timedelta

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import ValidationError
from app.repositories.user import UserRepository
from app.services.auth_token_service import (
    EMAIL_VERIFICATION_PURPOSE,
    AuthTokenService,
    utc_now_naive,
)
from app.services.email_service import EmailService


class EmailVerificationService:
    __slots__ = ("db", "email_service", "tokens", "users")

    def __init__(
        self,
        db: Session,
        email_service: EmailService | None = None,
    ) -> None:
        self.db = db
        self.users = UserRepository(db)
        self.tokens = AuthTokenService(db)
        self.email_service = email_service or EmailService()

    def issue_verification_token(self, *, user_id: int, email: str) -> None:
        settings = get_settings()
        token = self.tokens.issue_token(
            user_id=user_id,
            purpose=EMAIL_VERIFICATION_PURPOSE,
            expires_delta=timedelta(
                minutes=settings.email_verification_token_expire_minutes
            ),
        )
        self.email_service.send_email_confirmation_email(
            to_email=email,
            token=token,
        )

    def confirm_email(self, *, token: str) -> None:
        if not token.strip():
            raise ValidationError("Token is required.")
        try:
            auth_token = self.tokens.consume_token(
                raw_token=token,
                purpose=EMAIL_VERIFICATION_PURPOSE,
            )
        except ValidationError:
            existing_token = self.tokens.get_token(
                raw_token=token,
                purpose=EMAIL_VERIFICATION_PURPOSE,
            )
            if existing_token is not None and existing_token.used_at is not None:
                existing_user = self.users.get_by_id(existing_token.user_id)
                if existing_user is not None and existing_user.email_verified:
                    return
            raise

        user = self.users.get_by_id(auth_token.user_id)
        if user is None:
            raise ValidationError("Invalid or expired token.")

        if not user.email_verified:
            user.email_verified = True
            user.email_verified_at = utc_now_naive()
            self.users.save(user)
        self.tokens.mark_active_for_user_used(
            user_id=user.id,
            purpose=EMAIL_VERIFICATION_PURPOSE,
        )
        self.db.commit()
