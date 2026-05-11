from __future__ import annotations

from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models.auth_token import AuthToken


class AuthTokenRepository:
    __slots__ = ("db",)

    def __init__(self, db: Session) -> None:
        self.db = db

    def add(
        self,
        *,
        user_id: int,
        purpose: str,
        token_hash: str,
        expires_at: datetime,
        created_at: datetime,
    ) -> AuthToken:
        token = AuthToken(
            user_id=user_id,
            purpose=purpose,
            token_hash=token_hash,
            expires_at=expires_at,
            created_at=created_at,
        )
        self.db.add(token)
        self.db.flush()
        return token

    def get_by_hash_and_purpose(
        self,
        *,
        token_hash: str,
        purpose: str,
    ) -> AuthToken | None:
        stmt = select(AuthToken).where(
            AuthToken.token_hash == token_hash,
            AuthToken.purpose == purpose,
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def consume_active_by_hash_and_purpose(
        self,
        *,
        token_hash: str,
        purpose: str,
        used_at: datetime,
    ) -> AuthToken | None:
        stmt = (
            update(AuthToken)
            .where(
                AuthToken.token_hash == token_hash,
                AuthToken.purpose == purpose,
                AuthToken.used_at.is_(None),
                AuthToken.expires_at > used_at,
            )
            .values(used_at=used_at)
            .execution_options(synchronize_session=False)
        )
        result = self.db.execute(stmt)
        self.db.flush()
        if result.rowcount != 1:
            return None
        return self.get_by_hash_and_purpose(
            token_hash=token_hash,
            purpose=purpose,
        )

    def mark_active_for_user_used(
        self,
        *,
        user_id: int,
        purpose: str,
        used_at: datetime,
    ) -> None:
        stmt = (
            update(AuthToken)
            .where(
                AuthToken.user_id == user_id,
                AuthToken.purpose == purpose,
                AuthToken.used_at.is_(None),
            )
            .values(used_at=used_at)
            .execution_options(synchronize_session=False)
        )
        self.db.execute(stmt)
        self.db.flush()

    def save(self, token: AuthToken) -> AuthToken:
        self.db.add(token)
        self.db.flush()
        return token
