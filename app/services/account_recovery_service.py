from __future__ import annotations

import logging
from datetime import timedelta

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import ValidationError
from app.core.security import hash_password
from app.repositories.user import UserRepository
from app.services.auth_token_service import (
    PASSWORD_RESET_PURPOSE,
    AuthTokenService,
)
from app.services.email_service import EmailService
from app.services.registration_service import validate_password_strength

logger = logging.getLogger(__name__)


class AccountRecoveryService:
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

    def request_password_reset(self, *, email: str) -> None:
        normalized_email = email.strip().lower()
        user = self.users.get_by_email(normalized_email)
        if user is None:
            return

        settings = get_settings()
        token = self.tokens.issue_token(
            user_id=user.id,
            purpose=PASSWORD_RESET_PURPOSE,
            expires_delta=timedelta(
                minutes=settings.password_reset_token_expire_minutes
            ),
        )
        self.db.commit()
        try:
            self.email_service.send_password_reset_email(
                to_email=user.email,
                token=token,
            )
        except Exception:
            logger.exception("Password reset email delivery failed.")

    def reset_password(self, *, token: str, new_password: str) -> None:
        if not token.strip():
            raise ValidationError("Token is required.")
        validate_password_strength(new_password)
        auth_token = self.tokens.consume_token(
            raw_token=token,
            purpose=PASSWORD_RESET_PURPOSE,
        )
        user = self.users.get_by_id(auth_token.user_id)
        if user is None:
            raise ValidationError("Invalid or expired token.")

        user.password_hash = hash_password(new_password)
        self.users.save(user)
        self.tokens.mark_active_for_user_used(
            user_id=user.id,
            purpose=PASSWORD_RESET_PURPOSE,
        )
        self.db.commit()
