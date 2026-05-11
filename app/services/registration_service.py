from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, ValidationError
from app.core.security import hash_password
from app.domain.constants import (
    DEFAULT_COMPANY_NAME,
    DEFAULT_MONTHLY_CAPACITY_HOURS,
    DEFAULT_WORKSPACE_NAME,
)
from app.models.user import User
from app.repositories.user import UserRepository
from app.repositories.workspace import WorkspaceRepository
from app.services.email_verification_service import EmailVerificationService

MIN_PASSWORD_LENGTH = 8


def validate_password_strength(password: str) -> None:
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValidationError("Password must be at least 8 characters long.")
    if password.strip() != password:
        raise ValidationError("Password must not start or end with whitespace.")
    if not any(character.isalpha() for character in password):
        raise ValidationError("Password must include at least one letter.")
    if not any(character.isdigit() for character in password):
        raise ValidationError("Password must include at least one number.")


class RegistrationService:
    __slots__ = ("db", "email_verification", "users", "workspaces")

    def __init__(self, db: Session) -> None:
        self.db = db
        self.users = UserRepository(db)
        self.workspaces = WorkspaceRepository(db)
        self.email_verification = EmailVerificationService(db)

    def register_user(self, *, email: str, password: str) -> User:
        normalized_email = email.strip().lower()
        if not normalized_email:
            raise ValidationError("Email is required.")
        if not password:
            raise ValidationError("Password is required.")
        validate_password_strength(password)

        existing = self.users.get_by_email(normalized_email)
        if existing is not None:
            raise ConflictError("A user with this email already exists.")

        user = self.users.add(
            email=normalized_email,
            password_hash=hash_password(password),
        )
        self.workspaces.add(
            user_id=user.id,
            name=DEFAULT_WORKSPACE_NAME,
            company_name=DEFAULT_COMPANY_NAME,
            monthly_capacity_hours=DEFAULT_MONTHLY_CAPACITY_HOURS,
        )
        self.email_verification.issue_verification_token(
            user_id=user.id,
            email=user.email,
        )

        self.db.commit()
        self.db.refresh(user)
        return user
