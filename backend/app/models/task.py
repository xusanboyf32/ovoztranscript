from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import String, Text, Integer, ForeignKey, Numeric, Index, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.meeting import Meeting
    from app.models.task_report import TaskReport


class Task(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "tasks"

    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    task_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="task",
        index=True,
        comment="task | payment | debt | general",
    )
    priority: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="medium",
        index=True,
        comment="high | medium | low",
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
        index=True,
        comment="pending | confirmed | in_progress | submitted | approved | rejected",
    )

    deadline: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
        comment="Topshiriq muddati",
    )

    amount: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 2),
        nullable=True,
        comment="To'lov yoki qarz miqdori",
    )
    currency: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="UZS",
        comment="UZS | USD | EUR",
    )
    is_edited: Mapped[bool] = mapped_column(
        nullable=False,
        default=False,
        comment="Secretary tomonidan tahrirlangan",
    )
    order_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Transcript dagi tartib raqami",
    )

    # Foreign keys
    meeting_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("meetings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    assigned_to: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Relationships
    meeting: Mapped["Meeting"] = relationship(
        "Meeting",
        back_populates="tasks",
        lazy="selectin",
    )
    assignee: Mapped["User | None"] = relationship(
        "User",
        foreign_keys=[assigned_to],
        lazy="selectin",
    )
    report: Mapped["TaskReport | None"] = relationship(
        "TaskReport",
        back_populates="task",
        lazy="selectin",
        cascade="all, delete-orphan",
        uselist=False,
    )

    # Composite indexes
    __table_args__ = (
        Index("ix_tasks_meeting_status", "meeting_id", "status"),
        Index("ix_tasks_assigned_status", "assigned_to", "status"),
        Index("ix_tasks_deadline_status", "deadline", "status"),
    )

    def __repr__(self) -> str:
        return f"<Task id={self.id} type={self.task_type} status={self.status}>"
