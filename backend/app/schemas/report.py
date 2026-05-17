from datetime import datetime
from uuid import UUID
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from app.schemas.auth import UserShort


class AttachmentOut(BaseModel):
    id: UUID
    file_name: str
    file_type: str
    file_size: int | None
    mime_type: str | None
    file_url: str
    uploaded_at: datetime

    model_config = {"from_attributes": True}


class ReportOut(BaseModel):
    id: UUID
    task_id: UUID
    report_text: str | None
    status: str
    rejection_note: str | None
    submitted_at: datetime
    reviewed_at: datetime | None
    employee: UserShort
    reviewer: UserShort | None
    attachments: list[AttachmentOut] = []

    model_config = {"from_attributes": True}


class ReportCreate(BaseModel):
    report_text: str | None = Field(
        default=None,
        max_length=10000,
        description="Matnli hisobot (ixtiyoriy, fayl bo'lsa ham bo'ladi)",
    )

    @model_validator(mode="after")
    def validate_report_content(self) -> "ReportCreate":
        if not self.report_text:
            # Fayl yuklash multipart orqali keladi
            # Matn bo'lmasa fayl bo'lishi kerak — bu tekshiruv service da
            pass
        return self


class ReportReview(BaseModel):
    action: Literal["approve", "reject"] = Field(
        description="approve — tasdiqlash | reject — qaytarish",
    )
    rejection_note: str | None = Field(
        default=None,
        max_length=1000,
        description="Rad etish sababi — reject da majburiy",
    )

    @model_validator(mode="after")
    def validate_rejection_note(self) -> "ReportReview":
        if self.action == "reject" and not self.rejection_note:
            raise ValueError(
                "Rad etish sababi kiritilishi shart"
            )
        if self.action == "approve" and self.rejection_note:
            self.rejection_note = None
        return self


class ReportStatusOut(BaseModel):
    task_id: UUID
    has_report: bool
    status: str | None
    submitted_at: datetime | None

    model_config = {"from_attributes": True}


class AttachmentCreate(BaseModel):
    file_name: str = Field(max_length=500)
    file_type: str = Field(max_length=20)
    file_size: int | None = None
    mime_type: str | None = Field(default=None, max_length=100)
    file_path: str = Field(max_length=1000)

    @field_validator("file_type")
    @classmethod
    def validate_file_type(cls, v: str) -> str:
        allowed = {"image", "video", "document", "audio"}
        if v not in allowed:
            raise ValueError(
                f"Noto'g'ri fayl turi. Ruxsat etilgan: {', '.join(allowed)}"
            )
        return v

    @field_validator("file_size")
    @classmethod
    def validate_file_size(cls, v: int | None) -> int | None:
        if v is None:
            return v
        limits = {
            "image":    10 * 1024 * 1024,    # 10 MB
            "video":    200 * 1024 * 1024,   # 200 MB
            "document": 20 * 1024 * 1024,    # 20 MB
            "audio":    50 * 1024 * 1024,    # 50 MB
        }
        return v
