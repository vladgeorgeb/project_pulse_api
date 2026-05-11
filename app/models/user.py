from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, false
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(
        String(320), unique=True, index=True, nullable=False
    )
    password_hash: Mapped[str] = mapped_column(String(512), nullable=False)
    is_admin: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=false(),
    )
    email_verified: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=false(),
    )
    email_verified_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    workspace = relationship(
        "Workspace",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    feedback = relationship("Feedback", back_populates="user")
    auth_tokens = relationship(
        "AuthToken",
        back_populates="user",
        cascade="all, delete-orphan",
    )
