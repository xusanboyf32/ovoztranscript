from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String, Text, ForeignKey, Index, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.task import Task
    from app.models.user import User
    from app.models.report_attachment import ReportAttachment


class TaskReport(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "task_reports"

    report_text: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Xodim yozgan matnli hisobot",
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="submitted",
        index=True,
        comment="submitted | approved | rejected",
    )
    rejection_note: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Rad etilsa sababi",
    )
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        comment="Hisobot yuborilgan vaqt",
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Ko'rib chiqilgan vaqt",
    )

    # Foreign keys
    task_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,       # Bir task — bitta hisobot
        index=True,
    )
    employee_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    reviewed_by: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    task: Mapped["Task"] = relationship(
        "Task",
        back_populates="report",
        lazy="selectin",
    )
    employee: Mapped["User"] = relationship(
        "User",
        foreign_keys=[employee_id],
        lazy="selectin",
    )
    reviewer: Mapped["User | None"] = relationship(
        "User",
        foreign_keys=[reviewed_by],
        lazy="selectin",
    )
    attachments: Mapped[list["ReportAttachment"]] = relationship(
        "ReportAttachment",
        back_populates="report",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    # Composite indexes
    __table_args__ = (
        Index("ix_task_reports_employee_status", "employee_id", "status"),
        Index("ix_task_reports_task_employee", "task_id", "employee_id"),
    )

    def __repr__(self) -> str:
        return f"<TaskReport id={self.id} status={self.status}>"
