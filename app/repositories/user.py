from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User


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

    def add(
        self,
        *,
        email: str,
        password_hash: str,
        is_admin: bool = False,
    ) -> User:
        user = User(
            email=email,
            password_hash=password_hash,
            is_admin=is_admin,
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
