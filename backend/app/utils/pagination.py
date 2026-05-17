from typing import TypeVar, Generic, Sequence
from math import ceil

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from app.schemas.common import PaginationParams, PaginatedResponse


T = TypeVar("T")


async def paginate_query(
    db: AsyncSession,
    query: Select,
    params: PaginationParams,
) -> tuple[Sequence, int]:
    # Jami son
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    # Sahifalash
    paginated_query = query.offset(params.offset).limit(params.limit)
    result = await db.execute(paginated_query)
    items = result.scalars().all()

    return items, total


def make_paginated_response(
    items: list,
    total: int,
    params: PaginationParams,
) -> dict:
    pages = ceil(total / params.size) if total > 0 else 1
    return {
        "items": items,
        "total": total,
        "page": params.page,
        "size": params.size,
        "pages": pages,
        "has_next": params.page < pages,
        "has_prev": params.page > 1,
    }


class Paginator(Generic[T]):

    def __init__(
        self,
        db: AsyncSession,
        query: Select,
        params: PaginationParams,
    ) -> None:
        self.db = db
        self.query = query
        self.params = params

    async def paginate(self) -> dict:
        items, total = await paginate_query(
            self.db,
            self.query,
            self.params,
        )
        return make_paginated_response(
            list(items),
            total,
            self.params,
        )


def get_pagination_params(
    page: int = 1,
    size: int = 20,
) -> PaginationParams:
    return PaginationParams(page=page, size=size)
