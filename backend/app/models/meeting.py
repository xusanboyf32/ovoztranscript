from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import String, Text, Integer, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.task import Task


class Meeting(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "meetings"

    title: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
    audio_file_path: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
    )
    audio_duration: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Sekundda audio davomiyligi",
    )
    transcript: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Whisper STT natijasi",
    )
    edited_transcript: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Secretary tomonidan tahrirlangan matn",
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="processing",
        index=True,
        comment="processing|ready|distributing|distributed|confirmed|failed",
    )
    meeting_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        default=lambda: datetime.now(timezone.utc),
    )
    created_by: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    creator: Mapped["User"] = relationship(
        "User",
        foreign_keys=[created_by],
        lazy="selectin",
    )
    tasks: Mapped[list["Task"]] = relationship(
        "Task",
        back_populates="meeting",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Meeting id={self.id} status={self.status}>"

