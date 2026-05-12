from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import hash_password
from app.domain.constants import (
    DEFAULT_COMPANY_NAME,
    DEFAULT_MONTHLY_CAPACITY_HOURS,
    DEFAULT_WORKSPACE_NAME,
)
from app.repositories.user import UserRepository
from app.repositories.workspace import WorkspaceRepository
from app.services.auth_token_service import utc_now_naive
from app.services.registration_service import validate_password_strength


class BootstrapService:
    __slots__ = ("db", "users", "workspaces")

    def __init__(self, db: Session) -> None:
        self.db = db
        self.users = UserRepository(db)
        self.workspaces = WorkspaceRepository(db)

    def ensure_admin_user(self) -> None:
        settings = get_settings()
        admin_email = settings.admin_email.strip().lower()
        validate_password_strength(settings.admin_password)
        existing = self.users.get_by_email(admin_email)
        if existing is not None:
            changed = False
            if not existing.is_admin:
                existing.is_admin = True
                changed = True
            if not existing.email_verified:
                existing.email_verified = True
                existing.email_verified_at = utc_now_naive()
                changed = True
            if self.workspaces.get_by_user_id(existing.id) is None:
                self.workspaces.add(
                    user_id=existing.id,
                    name=DEFAULT_WORKSPACE_NAME,
                    company_name=DEFAULT_COMPANY_NAME,
                    monthly_capacity_hours=DEFAULT_MONTHLY_CAPACITY_HOURS,
                )
                changed = True
            if changed:
                self.users.save(existing)
                self.db.commit()
            return

        admin_user = self.users.add(
            email=admin_email,
            password_hash=hash_password(settings.admin_password),
            is_admin=True,
            email_verified=True,
            email_verified_at=utc_now_naive(),
        )
        self.workspaces.add(
            user_id=admin_user.id,
            name=DEFAULT_WORKSPACE_NAME,
            company_name=DEFAULT_COMPANY_NAME,
            monthly_capacity_hours=DEFAULT_MONTHLY_CAPACITY_HOURS,
        )
        self.db.commit()
