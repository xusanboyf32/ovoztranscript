import uuid
from datetime import datetime, date

from sqlalchemy import String, Boolean, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UUIDMixin, TimestampMixin
from sqlalchemy import String, Boolean, Index, Date

class User(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,                    # login uchun tez qidiruv
    )
    password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    full_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,                    # role bo'yicha filter tez
    )
    position: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    department: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        index=True,                    # bo'lim bo'yicha filter
    )
    phone: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,                    # active userlar filtri tez
    )

    # +++++++++++++++++++++++++++++++++++++++
    first_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    last_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    email: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        unique=True,
        index=True,
    )
    birth_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )
    avatar_path: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
    # +++++++++++++++++++++++++++++++++++++++
    # Composite index — role + is_active birga ko'p ishlatiladi
    # "barcha active employee lar" → WHERE role='employee' AND is_active=true
    __table_args__ = (
        Index("ix_users_role_is_active", "role", "is_active"),
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} username={self.username} role={self.role}>"
