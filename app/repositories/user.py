from __future__ import annotations

from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.orm import Session, selectinload

from app.models.feedback import Feedback
from app.models.project import Project
from app.models.user import User
from app.models.workspace import Workspace


class UserRepository:
    __slots__ = ("db",)

    def __init__(self, db: Session) -> None:
        self.db = db

    def list_all(self) -> list[User]:
        stmt = select(User).order_by(User.id)
        return list(self.db.execute(stmt).scalars().all())

    def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_id(self, user_id: int) -> User | None:
        stmt = select(User).where(User.id == user_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_with_owned_data(self, user_id: int) -> User | None:
        stmt = (
            select(User)
            .options(
                selectinload(User.workspace)
                .selectinload(Workspace.projects)
                .selectinload(Project.tasks),
                selectinload(User.workspace)
                .selectinload(Workspace.projects)
                .selectinload(Project.payment_records),
            )
            .where(User.id == user_id)
            .execution_options(populate_existing=True)
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def add(
        self,
        *,
        email: str,
        password_hash: str,
        is_admin: bool = False,
        email_verified: bool = False,
        email_verified_at: datetime | None = None,
    ) -> User:
        user = User(
            email=email,
            password_hash=password_hash,
            is_admin=is_admin,
            email_verified=email_verified,
            email_verified_at=email_verified_at,
        )
        self.db.add(user)
        self.db.flush()
        return user

    def save(self, user: User) -> User:
        self.db.add(user)
        self.db.flush()
        return user

    def delete(self, user: User) -> None:
        self.db.delete(user)
        self.db.flush()

    def detach_feedback(self, user_id: int) -> None:
        stmt = (
            update(Feedback)
            .where(Feedback.user_id == user_id)
            .values(user_id=None)
            .execution_options(synchronize_session=False)
        )
        self.db.execute(stmt)
        self.db.flush()
