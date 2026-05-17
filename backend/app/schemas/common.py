from typing import Generic, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1, description="Sahifa raqami")
    size: int = Field(default=20, ge=1, le=100, description="Sahifadagi elementlar soni")

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.size

    @property
    def limit(self) -> int:
        return self.size


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    size: int
    pages: int

    @classmethod
    def create(
        cls,
        items: list[T],
        total: int,
        params: PaginationParams,
    ) -> "PaginatedResponse[T]":
        return cls(
            items=items,
            total=total,
            page=params.page,
            size=params.size,
            pages=(total + params.size - 1) // params.size,
        )


class SuccessResponse(BaseModel):
    message: str
    success: bool = True


class ErrorResponse(BaseModel):
    detail: str
    success: bool = False

