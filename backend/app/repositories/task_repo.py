from uuid import UUID
from datetime import datetime

from sqlalchemy import select, func, and_, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.task import Task
from app.models.task_report import TaskReport
from app.utils.pagination import PaginationParams, paginate_query


class TaskRepository:

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(
        self,
        task_id: UUID,
        load_report: bool = True,
    ) -> Task | None:
        query = (
            select(Task)
            .where(Task.id == task_id)
            .options(
                selectinload(Task.assignee),
                selectinload(Task.meeting),
            )
        )

        if load_report:
            query = query.options(
                selectinload(Task.report).selectinload(
                    TaskReport.attachments
                )
            )

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_meeting(
        self,
        meeting_id: UUID,
        status: str | None = None,
    ) -> list[Task]:
        query = (
            select(Task)
            .where(Task.meeting_id == meeting_id)
            .options(
                selectinload(Task.assignee),
                selectinload(Task.report),
            )
            .order_by(Task.order_index)
        )

        if status:
            query = query.where(Task.status == status)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_by_employee(
            self,
            employee_id: UUID,
            status: str | None = None,
            statuses: list[str] | None = None,
            params: PaginationParams | None = None,
            order_by_desc: bool = False,
    ) -> tuple[list[Task], int]:
        print(f"DEBUG get_by_employee: statuses={statuses}")
        query = (
            select(Task)
            .where(Task.assigned_to == employee_id)
            .options(
                selectinload(Task.meeting),
                selectinload(Task.report).selectinload(
                    TaskReport.attachments
                ),
            )
        )

        if status:
            query = query.where(Task.status == status)
        elif statuses:
            query = query.where(Task.status.in_(statuses))

        if order_by_desc:
            query = query.order_by(Task.created_at.desc())
        else:
            query = query.order_by(Task.deadline.asc().nulls_last())

        if params:
            return await paginate_query(self.db, query, params)

        result = await self.db.execute(query)
        items = list(result.scalars().all())
        return items, len(items)



    async def get_overdue(
        self,
        employee_id: UUID | None = None,
    ) -> list[Task]:
        query = (
            select(Task)
            .where(
                and_(
                    Task.deadline < datetime.utcnow(),
                    Task.status.not_in(["approved"]),
                    Task.deadline.isnot(None),
                )
            )
            .options(
                selectinload(Task.assignee),
                selectinload(Task.meeting),
            )
            .order_by(Task.deadline.asc())
        )

        if employee_id:
            query = query.where(Task.assigned_to == employee_id)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_unassigned(
        self,
        meeting_id: UUID,
    ) -> list[Task]:
        result = await self.db.execute(
            select(Task)
            .where(
                and_(
                    Task.meeting_id == meeting_id,
                    Task.assigned_to.is_(None),
                    Task.status == "pending",
                )
            )
            .order_by(Task.order_index)
        )
        return list(result.scalars().all())

    async def create(self, data: dict) -> Task:
        task = Task(**data)
        self.db.add(task)
        await self.db.flush()
        await self.db.refresh(task)
        return task

    async def create_bulk(
        self,
        tasks_data: list[dict],
    ) -> list[Task]:
        tasks = [Task(**data) for data in tasks_data]
        self.db.add_all(tasks)
        await self.db.flush()
        for task in tasks:
            await self.db.refresh(task)
        return tasks

    async def update(
        self,
        task: Task,
        data: dict,
    ) -> Task:
        for key, value in data.items():
            if hasattr(task, key):
                setattr(task, key, value)
        task.is_edited = True
        await self.db.flush()
        await self.db.refresh(task)
        return task

    async def update_status(
        self,
        task: Task,
        status: str,
    ) -> Task:
        task.status = status
        await self.db.flush()
        await self.db.refresh(task)
        return task

    async def confirm_all(
        self,
        meeting_id: UUID,
    ) -> int:
        result = await self.db.execute(
            update(Task)
            .where(
                and_(
                    Task.meeting_id == meeting_id,
                    Task.status == "pending",
                )
            )
            .values(status="confirmed")
            .returning(Task.id)
        )
        await self.db.flush()
        confirmed_ids = result.fetchall()
        return len(confirmed_ids)

    async def delete_pending_by_meeting(
        self,
        meeting_id: UUID,
    ) -> int:
        tasks = await self.get_by_meeting(meeting_id, status="pending")
        count = len(tasks)
        for task in tasks:
            await self.db.delete(task)
        await self.db.flush()
        return count

    async def delete(self, task: Task) -> None:
        await self.db.delete(task)
        await self.db.flush()

    async def count_by_status(
        self,
        meeting_id: UUID | None = None,
        employee_id: UUID | None = None,
    ) -> dict[str, int]:
        query = select(
            Task.status,
            func.count(Task.id).label("count"),
        ).group_by(Task.status)

        if meeting_id:
            query = query.where(Task.meeting_id == meeting_id)
        if employee_id:
            query = query.where(Task.assigned_to == employee_id)

        result = await self.db.execute(query)
        return {row[0]: row[1] for row in result.all()}

    async def count_by_type(
        self,
        meeting_id: UUID | None = None,
    ) -> dict[str, int]:
        query = select(
            Task.task_type,
            func.count(Task.id).label("count"),
        ).group_by(Task.task_type)

        if meeting_id:
            query = query.where(Task.meeting_id == meeting_id)

        result = await self.db.execute(query)
        return {row[0]: row[1] for row in result.all()}

    async def get_stats_for_boss(self) -> dict:
        total_result = await self.db.execute(
            select(func.count(Task.id))
        )
        total = total_result.scalar_one()

        status_counts = await self.count_by_status()

        overdue = await self.get_overdue()

        return {
            "total":       total,
            "pending":     status_counts.get("pending", 0),
            "confirmed":   status_counts.get("confirmed", 0),
            "in_progress": status_counts.get("in_progress", 0),
            "submitted":   status_counts.get("submitted", 0),
            "approved":    status_counts.get("approved", 0),
            "rejected":    status_counts.get("rejected", 0),
            "overdue":     len(overdue),
        }
