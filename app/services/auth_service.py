from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import AuthenticationError
from app.core.security import create_access_token, verify_password
from app.models.user import User
from app.repositories.user import UserRepository


class AuthService:
    __slots__ = ("users",)

    def __init__(self, db: Session) -> None:
        self.users = UserRepository(db)

    def authenticate(self, *, email: str, password: str) -> User:
        user = self.users.get_by_email(email.strip().lower())
        if user is None or not verify_password(password, user.password_hash):
            raise AuthenticationError("Invalid email or password.")
        if get_settings().require_verified_email and not user.email_verified:
            raise AuthenticationError("Email address must be verified before login.")
        return user

    def issue_access_token(self, user: User) -> str:
        return create_access_token(subject=str(user.id))
