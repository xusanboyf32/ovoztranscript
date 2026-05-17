from uuid import UUID
from datetime import datetime, timezone

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.task_report import TaskReport
from app.models.report_attachment import ReportAttachment
from app.models.task import Task


class ReportRepository:

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(
        self,
        report_id: UUID,
    ) -> TaskReport | None:
        result = await self.db.execute(
            select(TaskReport)
            .where(TaskReport.id == report_id)
            .options(
                selectinload(TaskReport.attachments),
                selectinload(TaskReport.employee),
                selectinload(TaskReport.reviewer),
                selectinload(TaskReport.task),
            )
        )
        return result.scalar_one_or_none()

    async def get_by_task(
        self,
        task_id: UUID,
    ) -> TaskReport | None:
        result = await self.db.execute(
            select(TaskReport)
            .where(TaskReport.task_id == task_id)
            .options(
                selectinload(TaskReport.attachments),
                selectinload(TaskReport.employee),
                selectinload(TaskReport.reviewer),
            )
        )
        return result.scalar_one_or_none()

    async def get_by_employee(
        self,
        employee_id: UUID,
        status: str | None = None,
    ) -> list[TaskReport]:
        query = (
            select(TaskReport)
            .where(TaskReport.employee_id == employee_id)
            .options(
                selectinload(TaskReport.attachments),
                selectinload(TaskReport.task),
            )
            .order_by(TaskReport.submitted_at.desc())
        )

        if status:
            query = query.where(TaskReport.status == status)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_by_meeting(
        self,
        meeting_id: UUID,
    ) -> list[TaskReport]:
        result = await self.db.execute(
            select(TaskReport)
            .join(Task, Task.id == TaskReport.task_id)
            .where(Task.meeting_id == meeting_id)
            .options(
                selectinload(TaskReport.attachments),
                selectinload(TaskReport.employee),
                selectinload(TaskReport.task),
                selectinload(TaskReport.reviewer),
            )
            .order_by(TaskReport.submitted_at.desc())
        )
        return list(result.scalars().all())

    async def create(
        self,
        task_id: UUID,
        employee_id: UUID,
        report_text: str | None,
    ) -> TaskReport:
        report = TaskReport(
            task_id=task_id,
            employee_id=employee_id,
            report_text=report_text,
            status="submitted",
            submitted_at=datetime.now(timezone.utc),
        )
        self.db.add(report)
        await self.db.flush()
        await self.db.refresh(report)
        return report

    async def update_status(
        self,
        report: TaskReport,
        action: str,
        reviewer_id: UUID,
        rejection_note: str | None = None,
    ) -> TaskReport:
        if action == "approve":
            report.status = "approved"
            report.rejection_note = None
        elif action == "reject":
            report.status = "rejected"
            report.rejection_note = rejection_note

        report.reviewed_at = datetime.now(timezone.utc)
        report.reviewed_by = reviewer_id

        await self.db.flush()
        await self.db.refresh(report)
        return report

    async def resubmit(
        self,
        report: TaskReport,
        report_text: str | None,
    ) -> TaskReport:
        report.status = "submitted"
        report.report_text = report_text
        report.submitted_at = datetime.now(timezone.utc)
        report.reviewed_at = None
        report.reviewed_by = None
        report.rejection_note = None
        await self.db.flush()
        await self.db.refresh(report)
        return report

    async def delete(self, report: TaskReport) -> None:
        await self.db.delete(report)
        await self.db.flush()

    # --- Attachments ---

    async def add_attachment(
        self,
        report_id: UUID,
        file_path: str,
        file_name: str,
        file_type: str,
        mime_type: str | None,
        file_size: int | None,
    ) -> ReportAttachment:
        attachment = ReportAttachment(
            report_id=report_id,
            file_path=file_path,
            file_name=file_name,
            file_type=file_type,
            mime_type=mime_type,
            file_size=file_size,
        )
        self.db.add(attachment)
        await self.db.flush()
        await self.db.refresh(attachment)
        return attachment

    async def delete_attachment(
        self,
        attachment_id: UUID,
    ) -> ReportAttachment | None:
        result = await self.db.execute(
            select(ReportAttachment)
            .where(ReportAttachment.id == attachment_id)
        )
        attachment = result.scalar_one_or_none()
        if attachment:
            await self.db.delete(attachment)
            await self.db.flush()
        return attachment

    async def get_attachments_by_report(
        self,
        report_id: UUID,
    ) -> list[ReportAttachment]:
        result = await self.db.execute(
            select(ReportAttachment)
            .where(ReportAttachment.report_id == report_id)
            .order_by(ReportAttachment.uploaded_at.asc())
        )
        return list(result.scalars().all())

    # --- Statistika ---

    async def count_by_status(
        self,
        employee_id: UUID | None = None,
    ) -> dict[str, int]:
        query = select(
            TaskReport.status,
            func.count(TaskReport.id).label("count"),
        ).group_by(TaskReport.status)

        if employee_id:
            query = query.where(TaskReport.employee_id == employee_id)

        result = await self.db.execute(query)
        return {row[0]: row[1] for row in result.all()}

    async def get_pending_reviews(self) -> list[TaskReport]:
        result = await self.db.execute(
            select(TaskReport)
            .where(TaskReport.status == "submitted")
            .options(
                selectinload(TaskReport.employee),
                selectinload(TaskReport.task),
                selectinload(TaskReport.attachments),
            )
            .order_by(TaskReport.submitted_at.asc())
        )
        return list(result.scalars().all())
