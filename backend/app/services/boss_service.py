import logging
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.meeting import Meeting
from app.models.user import User
from app.repositories.meeting_repo import MeetingRepository
from app.repositories.task_repo import TaskRepository
from app.repositories.user_repo import UserRepository
from app.utils.datetime_utils import (
    deadline_status,
    format_deadline,
    format_duration,
    get_date_range,
)


logger = logging.getLogger(__name__)


class BossService:

    def __init__(
        self,
        db: AsyncSession,
        meeting_repo: MeetingRepository,
        task_repo: TaskRepository,
        user_repo: UserRepository,
    ) -> None:
        self.db = db
        self.meeting_repo = meeting_repo
        self.task_repo = task_repo
        self.user_repo = user_repo

    # --- MAJLISLAR ---

    async def get_meetings(
        self,
        boss: User,
        page: int = 1,
        size: int = 20,
    ) -> dict:
        meetings_with_counts = await self.meeting_repo.get_with_task_count(
            created_by=boss.id,
        )

        items = []
        for row in meetings_with_counts:
            meeting = row["meeting"]
            items.append({
                "id":             meeting.id,
                "title":          meeting.title,
                "status":         meeting.status,
                "audio_duration": format_duration(meeting.audio_duration),
                "meeting_date":   meeting.meeting_date,
                "created_at":     meeting.created_at,
                "task_count":     row["task_count"],
            })

        return {
            "items": items,
            "total": len(items),
        }

    async def get_meeting_detail(
        self,
        meeting_id: UUID,
        boss: User,
    ) -> Meeting:
        meeting = await self.meeting_repo.get_by_id(
            meeting_id,
            load_tasks=True,
        )
        if not meeting:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Majlis topilmadi",
            )
        if meeting.created_by != boss.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bu majlis sizga tegishli emas",
            )
        return meeting

    # --- UMUMIY HOLAT PANELI ---

    async def get_overview(self) -> dict:
        employees = await self.user_repo.get_employees()
        stats = await self.task_repo.get_stats_for_boss()
        overdue_tasks = await self.task_repo.get_overdue()

        employee_data = []
        for employee in employees:
            tasks, _ = await self.task_repo.get_by_employee(
                employee_id=employee.id,
                statuses=["confirmed", "in_progress", "submitted"],
            )

            task_list = []
            for task in tasks:
                task_list.append({
                    "id":             task.id,
                    "title":          task.title,
                    "task_type":      task.task_type,
                    "priority":       task.priority,
                    "status":         task.status,
                    "deadline":       format_deadline(task.deadline),
                    "deadline_status": deadline_status(task.deadline),
                    "amount":         task.amount,
                    "currency":       task.currency,
                    "has_report":     task.report is not None,
                })

            employee_data.append({
                "id":           employee.id,
                "full_name":    employee.full_name,
                "position":     employee.position,
                "department":   employee.department,
                "active_tasks": len(task_list),
                "tasks":        task_list,
            })

        return {
            "stats":     stats,
            "employees": employee_data,
            "overdue_count": len(overdue_tasks),
        }

    # --- XODIM BO'YICHA ---

    async def get_employee_tasks(
        self,
        employee_id: UUID,
    ) -> dict:
        employee = await self.user_repo.get_by_id(employee_id)
        if not employee or employee.role != "employee":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Xodim topilmadi",
            )

        all_tasks, total = await self.task_repo.get_by_employee(
            employee_id=employee_id,
        )
        status_counts = await self.task_repo.count_by_status(
            employee_id=employee_id,
        )
        overdue = await self.task_repo.get_overdue(
            employee_id=employee_id,
        )

        tasks_data = []
        for task in all_tasks:
            tasks_data.append({
                "id":              task.id,
                "title":           task.title,
                "task_type":       task.task_type,
                "priority":        task.priority,
                "status":          task.status,
                "deadline":        format_deadline(task.deadline),
                "deadline_status": deadline_status(task.deadline),
                "amount":          task.amount,
                "currency":        task.currency,
                "meeting_title":   task.meeting.title if task.meeting else None,
                "has_report":      task.report is not None,
                "report_status":   task.report.status if task.report else None,
            })

        return {
            "employee": {
                "id":         employee.id,
                "full_name":  employee.full_name,
                "position":   employee.position,
                "department": employee.department,
            },
            "tasks":          tasks_data,
            "total":          total,
            "status_counts":  status_counts,
            "overdue_count":  len(overdue),
            "completion_rate": (
                round(
                    status_counts.get("approved", 0) / total * 100, 1
                )
                if total > 0 else 0
            ),
        }

    # --- STATISTIKA ---

    async def get_stats(self) -> dict:
        task_stats = await self.task_repo.get_stats_for_boss()
        status_counts = await self.meeting_repo.count_by_status()
        employees = await self.user_repo.get_employees()

        start_date, end_date = get_date_range(days_back=30)
        recent_meetings, recent_total = await self.meeting_repo.get_all(
            date_from=start_date,
            date_to=end_date,
        )

        top_employees = []
        for employee in employees:
            emp_status_counts = await self.task_repo.count_by_status(
                employee_id=employee.id,
            )
            total = sum(emp_status_counts.values())
            approved = emp_status_counts.get("approved", 0)
            top_employees.append({
                "id":              employee.id,
                "full_name":       employee.full_name,
                "position":        employee.position,
                "total_tasks":     total,
                "approved_tasks":  approved,
                "completion_rate": (
                    round(approved / total * 100, 1)
                    if total > 0 else 0
                ),
            })

        top_employees.sort(
            key=lambda x: x["completion_rate"],
            reverse=True,
        )

        return {
            "task_stats": task_stats,
            "meeting_stats": {
                "total":       sum(status_counts.values()),
                "processing":  status_counts.get("processing", 0),
                "ready":       status_counts.get("ready", 0),
                "distributed": status_counts.get("distributed", 0),
                "confirmed":   status_counts.get("confirmed", 0),
            },
            "recent_meetings_count": recent_total,
            "total_employees":       len(employees),
            "top_employees":         top_employees[:5],
        }
