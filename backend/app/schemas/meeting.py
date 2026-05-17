from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.auth import UserShort
from app.schemas.task import TaskOut


class MeetingListItem(BaseModel):
    id: UUID
    title: str | None
    status: str
    audio_duration: int | None
    meeting_date: datetime
    created_at: datetime
    task_count: int = 0

    model_config = {"from_attributes": True}


class MeetingOut(BaseModel):
    id: UUID
    title: str | None
    status: str
    audio_duration: int | None
    transcript: str | None
    edited_transcript: str | None
    meeting_date: datetime
    created_at: datetime
    updated_at: datetime
    creator: UserShort
    tasks: list[TaskOut] = []

    model_config = {"from_attributes": True}


class MeetingCreate(BaseModel):
    title: str | None = Field(
        default=None,
        max_length=500,
        description="Majlis nomi (ixtiyoriy)",
    )
    meeting_date: datetime | None = Field(
        default=None,
        description="Majlis sanasi, None bo'lsa hozirgi vaqt",
    )


class TranscriptUpdate(BaseModel):
    edited_transcript: str = Field(
        min_length=10,
        max_length=100000,
        description="Secretary tahrirlagan matn",
    )


class MeetingStatusUpdate(BaseModel):
    status: str = Field(
        description="processing | ready | distributing | distributed | confirmed | failed",
    )
