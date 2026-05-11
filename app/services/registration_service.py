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


class RegistrationService:
    __slots__ = ("db", "users", "workspaces")

    def __init__(self, db: Session) -> None:
        self.db = db
        self.users = UserRepository(db)
        self.workspaces = WorkspaceRepository(db)

    def register_user(self, *, email: str, password: str) -> User:
        normalized_email = email.strip().lower()
        if not normalized_email:
            raise ValidationError("Email is required.")
        if not password:
            raise ValidationError("Password is required.")

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

        self.db.commit()
        self.db.refresh(user)
        return user
