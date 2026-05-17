import logging
from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task
from app.models.task_report import TaskReport
from app.models.user import User
from app.repositories.report_repo import ReportRepository
from app.repositories.task_repo import TaskRepository
from app.utils.datetime_utils import deadline_status, format_deadline
from app.utils.file_utils import (
    build_file_url,
    delete_file,
    save_report_file,
)


logger = logging.getLogger(__name__)


class EmployeeService:

    def __init__(
        self,
        db: AsyncSession,
        task_repo: TaskRepository,
        report_repo: ReportRepository,
    ) -> None:
        self.db = db
        self.task_repo = task_repo
        self.report_repo = report_repo

    # --- TASKLAR ---

    async def get_my_tasks(
        self,
        employee: User,
        status_filter: str | None = None,
    ) -> dict:

        statuses_map = {
            "confirmed": ["confirmed"],
            "submitted": ["submitted"],
            "approved": ["approved"],
            "all": None,
        }

        statuses = None
        overdue_only = False

        if status_filter == "overdue":
            overdue_only = True
        elif status_filter == "all" or status_filter is None:
            statuses = None
        elif status_filter in statuses_map:
            statuses = statuses_map[status_filter]
        else:
            statuses = None

        print(f"DEBUG: status_filter={status_filter}, statuses={statuses}")  # qo'shing

        if overdue_only:
            tasks = await self.task_repo.get_overdue(employee_id=employee.id)
            total = len(tasks)
        else:
            tasks, total = await self.task_repo.get_by_employee(
                employee_id=employee.id,
                statuses=statuses,
                order_by_desc=True,
            )

        status_counts = await self.task_repo.count_by_status(
            employee_id=employee.id,
        )

        overdue = await self.task_repo.get_overdue(
            employee_id=employee.id,
        )

        tasks_data = []
        for task in tasks:
            tasks_data.append(
                self._format_task(task)
            )

        return {
            "tasks":          tasks_data,
            "total":          total,
            "status_counts":  status_counts,
            "overdue_count":  len(overdue),
        }

    async def get_task_detail(
        self,
        task_id: UUID,
        employee: User,
    ) -> dict:
        task = await self.task_repo.get_by_id(
            task_id,
            load_report=True,
        )
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Topshiriq topilmadi",
            )
        if task.assigned_to != employee.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bu topshiriq sizga tegishli emas",
            )

        task_data = self._format_task(task)

        # Report ma'lumotlari
        if task.report:
            task_data["report"] = self._format_report(task.report)
        else:
            task_data["report"] = None

        return task_data

    def _format_task(self, task: Task) -> dict:
        return {
            "id":              task.id,
            "title":           task.title,
            "description":     task.description,
            "task_type":       task.task_type,
            "priority":        task.priority,
            "status":          task.status,
            "deadline":        format_deadline(task.deadline),
            "deadline_raw":    task.deadline,
            "deadline_status": deadline_status(task.deadline),
            "amount":          task.amount,
            "currency":        task.currency,
            "meeting_title":   task.meeting.title if task.meeting else None,
            "meeting_date":    task.meeting.meeting_date if task.meeting else None,
            "has_report":      task.report is not None,
            "report_status":   task.report.status if task.report else None,
            "created_at":      task.created_at,
        }

    def _format_report(self, report: TaskReport) -> dict:
        attachments = []
        for attachment in report.attachments:
            attachments.append({
                "id":          attachment.id,
                "file_name":   attachment.file_name,
                "file_type":   attachment.file_type,
                "file_size":   attachment.file_size,
                "mime_type":   attachment.mime_type,
                "file_url":    build_file_url(attachment.file_path),
                "uploaded_at": attachment.uploaded_at,
            })

        return {
            "id":             report.id,
            "report_text":    report.report_text,
            "status":         report.status,
            "rejection_note": report.rejection_note,
            "submitted_at":   report.submitted_at,
            "reviewed_at":    report.reviewed_at,
            "attachments":    attachments,
        }

    # --- HISOBOT ---

    async def submit_report(
        self,
        task_id: UUID,
        employee: User,
        report_text: str | None,
        files: list[UploadFile],
    ) -> TaskReport:
        task = await self.task_repo.get_by_id(task_id)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Topshiriq topilmadi",
            )
        if task.assigned_to != employee.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bu topshiriq sizga tegishli emas",
            )

        allowed_statuses = {"confirmed", "in_progress", "rejected"}
        if task.status not in allowed_statuses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Bu topshiriq uchun hisobot topshirib bo'lmaydi. "
                    f"Holat: {task.status}"
                ),
            )

        # Matn ham, fayl ham yo'q bo'lsa xato
        if not report_text and not files:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Hisobot matni yoki fayl kiritilishi shart",
            )

        # Mavjud hisobot tekshirish
        existing_report = await self.report_repo.get_by_task(task_id)

        saved_files = []
        try:
            # Fayllarni saqlash
            for file in files:
                if file.filename:
                    file_path, file_type, mime_type, file_size = (
                        await save_report_file(
                            file=file,
                            task_id=str(task_id),
                            employee_id=str(employee.id),
                        )
                    )
                    saved_files.append({
                        "file_path":  file_path,
                        "file_name":  file.filename,
                        "file_type":  file_type,
                        "mime_type":  mime_type,
                        "file_size":  file_size,
                    })

            # Hisobot yaratish yoki qayta yuborish
            if existing_report and existing_report.status == "rejected":
                report = await self.report_repo.resubmit(
                    report=existing_report,
                    report_text=report_text,
                )
            elif existing_report:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Bu topshiriq uchun hisobot allaqachon yuborilgan",
                )
            else:
                report = await self.report_repo.create(
                    task_id=task_id,
                    employee_id=employee.id,
                    report_text=report_text,
                )

            # Fayllarni DB ga saqlash
            for file_data in saved_files:
                await self.report_repo.add_attachment(
                    report_id=report.id,
                    **file_data,
                )

            # Task statusini yangilash
            await self.task_repo.update_status(task, "submitted")

            logger.info(
                f"Hisobot yuborildi | "
                f"Task: {task_id} | "
                f"Employee: {employee.id} | "
                f"Fayllar: {len(saved_files)}"
            )

            return report

        except HTTPException:
            # Xato bo'lsa saqlangan fayllarni o'chirish
            for file_data in saved_files:
                delete_file(file_data["file_path"])
            raise

        except Exception as e:
            for file_data in saved_files:
                delete_file(file_data["file_path"])
            logger.error(f"Hisobot yuborishda xato: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Hisobot yuborishda xato yuz berdi",
            )

    async def delete_attachment(
        self,
        attachment_id: UUID,
        employee: User,
    ) -> None:
        attachments = await self.report_repo.get_attachments_by_report(
            report_id=attachment_id,
        )
        if not attachments:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Fayl topilmadi",
            )

        attachment = await self.report_repo.delete_attachment(attachment_id)
        if attachment:
            delete_file(attachment.file_path)
            logger.info(
                f"Fayl o'chirildi | "
                f"Attachment: {attachment_id} | "
                f"Employee: {employee.id}"
            )


