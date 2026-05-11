from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import hash_password
from app.repositories.user import UserRepository


class BootstrapService:
    __slots__ = ("db", "users")

    def __init__(self, db: Session) -> None:
        self.db = db
        self.users = UserRepository(db)

    def ensure_admin_user(self) -> None:
        settings = get_settings()
        admin_email = settings.admin_email.strip().lower()
        existing = self.users.get_by_email(admin_email)
        if existing is not None:
            if not existing.is_admin:
                existing.is_admin = True
                self.users.save(existing)
                self.db.commit()
            return

        self.users.add(
            email=admin_email,
            password_hash=hash_password(settings.admin_password),
            is_admin=True,
        )
        self.db.commit()
