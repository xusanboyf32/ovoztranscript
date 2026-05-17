from uuid import UUID
from datetime import datetime

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.meeting import Meeting
from app.models.task import Task
from app.utils.pagination import PaginationParams, paginate_query


class MeetingRepository:

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(
        self,
        meeting_id: UUID,
        load_tasks: bool = True,
    ) -> Meeting | None:
        query = select(Meeting).where(Meeting.id == meeting_id)

        if load_tasks:
            query = query.options(
                selectinload(Meeting.tasks).selectinload(Task.assignee),
                selectinload(Meeting.tasks).selectinload(Task.report),
                selectinload(Meeting.creator),
            )

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_all(
        self,
        created_by: UUID | None = None,
        status: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        params: PaginationParams | None = None,
    ) -> tuple[list[Meeting], int]:
        query = (
            select(Meeting)
            .options(selectinload(Meeting.creator))
            .order_by(Meeting.meeting_date.desc())
        )

        # Filterlar
        filters = []
        if created_by:
            filters.append(Meeting.created_by == created_by)
        if status:
            filters.append(Meeting.status == status)
        if date_from:
            filters.append(Meeting.meeting_date >= date_from)
        if date_to:
            filters.append(Meeting.meeting_date <= date_to)
        if filters:
            query = query.where(and_(*filters))

        if params:
            return await paginate_query(self.db, query, params)

        result = await self.db.execute(query)
        items = list(result.scalars().all())
        return items, len(items)

    async def get_by_status(
        self,
        status: str | None = None,
        statuses: list[str] | None = None,
    ) -> list[Meeting]:
        query = select(Meeting).order_by(Meeting.meeting_date.desc())

        if status:
            query = query.where(Meeting.status == status)
        elif statuses:
            query = query.where(Meeting.status.in_(statuses))

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_with_task_count(
        self,
        created_by: UUID | None = None,
    ) -> list[dict]:
        query = (
            select(
                Meeting,
                func.count(Task.id).label("task_count"),
            )
            .outerjoin(Task, Task.meeting_id == Meeting.id)
            .group_by(Meeting.id)
            .order_by(Meeting.meeting_date.desc())
        )

        if created_by:
            query = query.where(Meeting.created_by == created_by)

        result = await self.db.execute(query)
        rows = result.all()

        return [
            {
                "meeting": row[0],
                "task_count": row[1],
            }
            for row in rows
        ]

    async def create(
        self,
        data: dict,
    ) -> Meeting:
        meeting = Meeting(**data)
        self.db.add(meeting)
        await self.db.flush()
        await self.db.refresh(meeting)
        return meeting

    async def update(
        self,
        meeting: Meeting,
        data: dict,
    ) -> Meeting:
        for key, value in data.items():
            if hasattr(meeting, key):
                setattr(meeting, key, value)
        await self.db.flush()
        await self.db.refresh(meeting)
        return meeting

    async def update_status(
        self,
        meeting: Meeting,
        status: str,
    ) -> Meeting:
        meeting.status = status
        await self.db.flush()
        await self.db.refresh(meeting)
        return meeting

    async def update_transcript(
        self,
        meeting: Meeting,
        transcript: str | None = None,
        edited_transcript: str | None = None,
    ) -> Meeting:
        if transcript is not None:
            meeting.transcript = transcript
        if edited_transcript is not None:
            meeting.edited_transcript = edited_transcript
        await self.db.flush()
        await self.db.refresh(meeting)
        return meeting

    async def delete(
        self,
        meeting: Meeting,
    ) -> None:
        await self.db.delete(meeting)
        await self.db.flush()

    async def count_by_status(
        self,
        created_by: UUID | None = None,
    ) -> dict[str, int]:
        query = select(
            Meeting.status,
            func.count(Meeting.id).label("count"),
        ).group_by(Meeting.status)

        if created_by:
            query = query.where(Meeting.created_by == created_by)

        result = await self.db.execute(query)
        rows = result.all()

        return {row[0]: row[1] for row in rows}

    async def get_recent(
        self,
        created_by: UUID | None = None,
        limit: int = 5,
    ) -> list[Meeting]:
        query = (
            select(Meeting)
            .options(selectinload(Meeting.creator))
            .order_by(Meeting.meeting_date.desc())
            .limit(limit)
        )

        if created_by:
            query = query.where(Meeting.created_by == created_by)

        result = await self.db.execute(query)
        return list(result.scalars().all())
