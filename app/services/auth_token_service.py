from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.core.exceptions import ValidationError
from app.core.security import generate_secure_token, hash_auth_token
from app.models.auth_token import AuthToken
from app.repositories.auth_token import AuthTokenRepository

PASSWORD_RESET_PURPOSE = "password_reset"
EMAIL_VERIFICATION_PURPOSE = "email_verification"
INVALID_TOKEN_MESSAGE = "Invalid or expired token."


def utc_now_naive() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class AuthTokenService:
    __slots__ = ("tokens",)

    def __init__(self, db: Session) -> None:
        self.tokens = AuthTokenRepository(db)

    def issue_token(
        self,
        *,
        user_id: int,
        purpose: str,
        expires_delta: timedelta,
    ) -> str:
        now = utc_now_naive()
        self.tokens.mark_active_for_user_used(
            user_id=user_id,
            purpose=purpose,
            used_at=now,
        )
        raw_token = generate_secure_token()
        self.tokens.add(
            user_id=user_id,
            purpose=purpose,
            token_hash=hash_auth_token(raw_token, purpose=purpose),
            expires_at=now + expires_delta,
            created_at=now,
        )
        return raw_token

    def consume_token(self, *, raw_token: str, purpose: str) -> AuthToken:
        token_hash = hash_auth_token(raw_token.strip(), purpose=purpose)
        now = utc_now_naive()
        token = self.tokens.consume_active_by_hash_and_purpose(
            token_hash=token_hash,
            purpose=purpose,
            used_at=now,
        )
        if token is None:
            raise ValidationError(INVALID_TOKEN_MESSAGE)
        return token

    def get_token(self, *, raw_token: str, purpose: str) -> AuthToken | None:
        return self.tokens.get_by_hash_and_purpose(
            token_hash=hash_auth_token(raw_token.strip(), purpose=purpose),
            purpose=purpose,
        )

    def mark_active_for_user_used(
        self,
        *,
        user_id: int,
        purpose: str,
    ) -> None:
        self.tokens.mark_active_for_user_used(
            user_id=user_id,
            purpose=purpose,
            used_at=utc_now_naive(),
        )
