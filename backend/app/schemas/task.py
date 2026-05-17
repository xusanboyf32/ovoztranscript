from datetime import datetime
from decimal import Decimal
from uuid import UUID
from sqlalchemy import DateTime
from pydantic import BaseModel, Field, field_validator

from app.schemas.auth import UserShort


class TaskOut(BaseModel):
    id: UUID
    title: str
    description: str | None
    task_type: str
    priority: str
    status: str
    deadline: datetime | None
    amount: Decimal | None
    currency: str
    is_edited: bool
    order_index: int
    meeting_id: UUID
    assigned_to: UUID | None
    assignee: UserShort | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TaskCreate(BaseModel):
    title: str = Field(
        min_length=2,
        max_length=500,
    )
    description: str | None = Field(
        default=None,
        max_length=5000,
    )
    task_type: str = Field(
        default="task",
        description="task | payment | debt | general",
    )
    priority: str = Field(
        default="medium",
        description="high | medium | low",
    )
    assigned_to: UUID | None = Field(
        default=None,
    )
    deadline: datetime | None = Field(
        default=None,
    )
    amount: Decimal | None = Field(
        default=None,
        ge=0,
        description="Faqat payment va debt uchun",
    )
    currency: str = Field(
        default="UZS",
        max_length=10,
    )
    meeting_id: UUID

    @field_validator("task_type")
    @classmethod
    def validate_task_type(cls, v: str) -> str:
        allowed = {"task", "payment", "debt", "general"}
        if v not in allowed:
            raise ValueError(
                f"Noto'g'ri task turi. Ruxsat etilgan: {', '.join(allowed)}"
            )
        return v

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: str) -> str:
        allowed = {"high", "medium", "low"}
        if v not in allowed:
            raise ValueError(
                f"Noto'g'ri prioritet. Ruxsat etilgan: {', '.join(allowed)}"
            )
        return v

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        allowed = {"UZS", "USD", "EUR"}
        if v.upper() not in allowed:
            raise ValueError(
                f"Noto'g'ri valyuta. Ruxsat etilgan: {', '.join(allowed)}"
            )
        return v.upper()

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: Decimal | None) -> Decimal | None:
        if v is not None and v < 0:
            raise ValueError("Miqdor manfiy bo'lishi mumkin emas")
        return v

from datetime import datetime, date
from decimal import Decimal
from uuid import UUID
from typing import Union

from pydantic import BaseModel, Field, field_validator


class TaskUpdate(BaseModel):
    title: str | None = Field(
        default=None,
        min_length=2,
        max_length=500,
    )
    description: str | None = Field(
        default=None,
        max_length=5000,
    )
    task_type: str | None = None
    priority: str | None = None
    assigned_to: UUID | None = None
    deadline: datetime | date | str | None = None
    amount: Decimal | None = Field(
        default=None,
        ge=0,
    )
    currency: str | None = None

    @field_validator("deadline", mode="before")
    @classmethod
    def parse_deadline(cls, v):
        if v is None or v == '':
            return None
        if isinstance(v, datetime):
            return v
        if isinstance(v, date):
            return datetime(v.year, v.month, v.day)
        if isinstance(v, str):
            try:
                return datetime.fromisoformat(v)
            except ValueError:
                try:
                    d = date.fromisoformat(v)
                    return datetime(d.year, d.month, d.day)
                except ValueError:
                    raise ValueError(f"Noto'g'ri sana formati: {v}")
        return v

    @field_validator("task_type")
    @classmethod
    def validate_task_type(cls, v: str | None) -> str | None:
        if v is None:
            return v
        allowed = {"task", "payment", "debt", "general"}
        if v not in allowed:
            raise ValueError(
                f"Noto'g'ri task turi. Ruxsat etilgan: {', '.join(allowed)}"
            )
        return v

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: str | None) -> str | None:
        if v is None:
            return v
        allowed = {"high", "medium", "low"}
        if v not in allowed:
            raise ValueError(
                f"Noto'g'ri prioritet. Ruxsat etilgan: {', '.join(allowed)}"
            )
        return v


class TaskConfirmResponse(BaseModel):
    confirmed_count: int
    message: str


class TaskDistributeResponse(BaseModel):
    tasks: list[TaskOut]
    total: int
    message: str
