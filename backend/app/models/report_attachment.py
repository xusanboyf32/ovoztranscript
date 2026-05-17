from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import String, BigInteger, Index, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDMixin

if TYPE_CHECKING:
    from app.models.task_report import TaskReport


class ReportAttachment(Base, UUIDMixin):
    __tablename__ = "report_attachments"

    file_path: Mapped[str] = mapped_column(
        String(1000),
        nullable=False,
        comment="Serverda saqlangan fayl yo'li",
    )
    file_name: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="Asl fayl nomi",
    )
    file_size: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
        comment="Fayl hajmi — byte",
    )
    file_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
        comment="image | video | document | audio",
    )
    mime_type: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="image/jpeg, video/mp4 kabi MIME turi",
    )
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        comment="Fayl yuklangan vaqt",
    )

    # Foreign key
    report_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("task_reports.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Relationship
    report: Mapped["TaskReport"] = relationship(
        "TaskReport",
        back_populates="attachments",
        lazy="selectin",
    )

    # Composite index
    __table_args__ = (
        Index("ix_report_attachments_report_type", "report_id", "file_type"),
    )

    def __repr__(self) -> str:
        return (
            f"<ReportAttachment id={self.id} "
            f"file_name={self.file_name} "
            f"file_type={self.file_type}>"
        )
