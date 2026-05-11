from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Workspace(Base):
    __tablename__ = "workspaces"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), unique=True, nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    company_name: Mapped[str] = mapped_column(String(100), nullable=False)
    monthly_capacity_hours: Mapped[int] = mapped_column(Integer, nullable=False)

    user = relationship("User", back_populates="workspace")
    projects = relationship(
        "Project",
        back_populates="workspace",
        cascade="all, delete-orphan",
        order_by="Project.id",
    )
