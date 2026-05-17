from uuid import UUID
from pydantic import BaseModel, Field, field_validator


class LoginRequest(BaseModel):
    username: str = Field(
        min_length=3,
        max_length=100,
        description="Foydalanuvchi login nomi",
    )
    password: str = Field(
        min_length=6,
        max_length=255,
        description="Foydalanuvchi paroli",
    )

    @field_validator("username")
    @classmethod
    def username_strip(cls, v: str) -> str:
        return v.strip().lower()


class UserShort(BaseModel):
    id: UUID
    full_name: str
    role: str
    position: str | None

    model_config = {"from_attributes": True}


class UserOut(BaseModel):
    id: UUID
    username: str
    full_name: str
    role: str
    position: str | None
    department: str | None
    phone: str | None
    is_active: bool

    model_config = {"from_attributes": True}


class UserCreate(BaseModel):
    username: str = Field(
        min_length=3,
        max_length=100,
    )
    password: str = Field(
        min_length=6,
        max_length=255,
    )
    full_name: str = Field(
        min_length=2,
        max_length=255,
    )
    role: str = Field(
        description="admin | boss | secretary | employee",
    )
    position: str | None = Field(
        default=None,
        max_length=255,
    )
    department: str | None = Field(
        default=None,
        max_length=255,
    )
    phone: str | None = Field(
        default=None,
        max_length=30,
    )

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        allowed = {"admin", "boss", "secretary", "employee"}
        if v not in allowed:
            raise ValueError(
                f"Noto'g'ri rol. Ruxsat etilgan: {', '.join(allowed)}"
            )
        return v

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        v = v.strip().lower()
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError(
                "Username faqat harf, raqam, '_' va '-' dan iborat bo'lishi kerak"
            )
        return v

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str | None) -> str | None:
        if v is None:
            return v
        cleaned = v.replace(" ", "").replace("-", "")
        if not cleaned.startswith("+"):
            raise ValueError("Telefon raqam '+' bilan boshlanishi kerak")
        if not cleaned[1:].isdigit():
            raise ValueError("Telefon raqam faqat raqamlardan iborat bo'lishi kerak")
        return cleaned


class UserUpdate(BaseModel):
    full_name: str | None = Field(
        default=None,
        min_length=2,
        max_length=255,
    )
    password: str | None = Field(
        default=None,
        min_length=6,
        max_length=255,
    )
    role: str | None = None
    position: str | None = None
    department: str | None = None
    phone: str | None = None
    is_active: bool | None = None

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str | None) -> str | None:
        if v is None:
            return v
        allowed = {"admin", "boss", "secretary", "employee"}
        if v not in allowed:
            raise ValueError(
                f"Noto'g'ri rol. Ruxsat etilgan: {', '.join(allowed)}"
            )
        return v


class LoginResponse(BaseModel):
    message: str
    redirect: str
    user: UserShort
