import logging
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.meeting import Meeting
from app.models.task import Task
from app.models.task_report import TaskReport
from app.models.user import User
from app.repositories.meeting_repo import MeetingRepository
from app.repositories.task_repo import TaskRepository
from app.repositories.report_repo import ReportRepository
from app.repositories.user_repo import UserRepository
from app.schemas.meeting import TranscriptUpdate
from app.schemas.task import TaskUpdate
from app.schemas.report import ReportReview
from app.services.llm_service import LLMService
from app.utils.file_utils import delete_file


logger = logging.getLogger(__name__)


class SecretaryService:

    def __init__(
        self,
        db: AsyncSession,
        meeting_repo: MeetingRepository,
        task_repo: TaskRepository,
        report_repo: ReportRepository,
        user_repo: UserRepository,
        llm_service: LLMService,
    ) -> None:
        self.db = db
        self.meeting_repo = meeting_repo
        self.task_repo = task_repo
        self.report_repo = report_repo
        self.user_repo = user_repo
        self.llm_service = llm_service

    # --- MAJLISLAR ---

    async def get_meetings(
        self,
        page: int = 1,
        size: int = 20,
    ) -> dict:
        from app.utils.pagination import PaginationParams
        params = PaginationParams(page=page, size=size)
        meetings_with_counts = await self.meeting_repo.get_with_task_count()

        items = []
        for row in meetings_with_counts:
            meeting = row["meeting"]
            items.append({
                "id":             meeting.id,
                "title":          meeting.title,
                "status":         meeting.status,
                "audio_duration": meeting.audio_duration,
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
        return meeting

    # --- TRANSCRIPT ---

    async def update_transcript(
        self,
        meeting_id: UUID,
        data: TranscriptUpdate,
        secretary: User,
    ) -> Meeting:
        meeting = await self.meeting_repo.get_by_id(
            meeting_id,
            load_tasks=False,
        )
        if not meeting:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Majlis topilmadi",
            )
        if meeting.status == "confirmed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tasdiqlangan majlis o'zgartirilmaydi",
            )

        logger.info(
            f"Transcript yangilandi | "
            f"Meeting: {meeting_id} | "
            f"Secretary: {secretary.id}"
        )

        return await self.meeting_repo.update_transcript(
            meeting,
            edited_transcript=data.edited_transcript,
        )

    # --- TAQSIMLASH ---

    async def distribute_tasks(
        self,
        meeting_id: UUID,
        secretary: User,
    ) -> list[Task]:
        meeting = await self.meeting_repo.get_by_id(
            meeting_id,
            load_tasks=False,
        )
        if not meeting:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Majlis topilmadi",
            )

        allowed_statuses = {"ready", "distributed"}
        if meeting.status not in allowed_statuses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Taqsimlash uchun majlis holati "
                    f"'ready' yoki 'distributed' bo'lishi kerak. "
                    f"Hozirgi holat: {meeting.status}"
                ),
            )

        # Qayta taqsimlash — eski pending tasklar o'chiriladi
        if meeting.status == "distributed":
            deleted = await self.task_repo.delete_pending_by_meeting(
                meeting_id
            )
            logger.info(
                f"Qayta taqsimlash | "
                f"O'chirilgan tasklar: {deleted} | "
                f"Meeting: {meeting_id}"
            )

        # Matn tanlash
        transcript = (
            meeting.edited_transcript
            if meeting.edited_transcript
            else meeting.transcript
        )

        if not transcript:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Majlisda transcript mavjud emas",
            )

        # LLM orqali tasklar ajratiladi
        await self.meeting_repo.update_status(meeting, "distributing")

        try:
            employees = await self.user_repo.get_employees()
            raw_tasks = await self.llm_service.extract_tasks(transcript)

            if not raw_tasks:
                await self.meeting_repo.update_status(meeting, "ready")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Transcriptdan topshiriq ajratib bo'lmadi",
                )

            processed_tasks = await self.llm_service.process_tasks_with_employees(
                raw_tasks=raw_tasks,
                employees=employees,
            )

            # Meeting ID qo'shish
            for task_data in processed_tasks:
                task_data["meeting_id"] = meeting_id

            tasks = await self.task_repo.create_bulk(processed_tasks)
            await self.meeting_repo.update_status(meeting, "distributed")

            logger.info(
                f"Taqsimlash tugadi | "
                f"Yaratilgan tasklar: {len(tasks)} | "
                f"Meeting: {meeting_id}"
            )

            return tasks

        except HTTPException:
            raise
        except Exception as e:
            await self.meeting_repo.update_status(meeting, "ready")
            logger.error(f"Taqsimlash xatosi: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Taqsimlash vaqtida xato yuz berdi",
            )

    # --- TASK EDIT ---

    async def update_task(
        self,
        task_id: UUID,
        data: TaskUpdate,
        secretary: User,
    ) -> Task:
        task = await self.task_repo.get_by_id(task_id)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Topshiriq topilmadi",
            )
        if task.meeting.status == "confirmed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tasdiqlangan majlis tasklari o'zgartirilmaydi",
            )
        if task.status != "pending":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Faqat pending tasklar tahrirlanadi",
            )

        update_data = data.model_dump(exclude_none=True)
        return await self.task_repo.update(task, update_data)

    async def delete_task(
        self,
        task_id: UUID,
        secretary: User,
    ) -> None:
        task = await self.task_repo.get_by_id(task_id)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Topshiriq topilmadi",
            )
        if task.status != "pending":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Faqat pending tasklar o'chiriladi",
            )

        await self.task_repo.delete(task)
        logger.info(
            f"Task o'chirildi | "
            f"Task: {task_id} | "
            f"Secretary: {secretary.id}"
        )

    # --- TASDIQLASH ---

    async def confirm_tasks(
        self,
        meeting_id: UUID,
        secretary: User,
    ) -> dict:
        meeting = await self.meeting_repo.get_by_id(
            meeting_id,
            load_tasks=False,
        )
        if not meeting:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Majlis topilmadi",
            )
        if meeting.status != "distributed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Tasdiqlash uchun majlis holati "
                    "'distributed' bo'lishi kerak"
                ),
            )

        pending_tasks = await self.task_repo.get_by_meeting(
            meeting_id,
            status="pending",
        )
        if not pending_tasks:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tasdiqlanadigan task yo'q",
            )

        # Unassigned tasklar haqida ogohlantirish
        unassigned = await self.task_repo.get_unassigned(meeting_id)
        unassigned_count = len(unassigned)

        confirmed_count = await self.task_repo.confirm_all(meeting_id)
        await self.meeting_repo.update_status(meeting, "confirmed")

        logger.info(
            f"Tasdiqlash tugadi | "
            f"Tasdiqlangan: {confirmed_count} | "
            f"Unassigned: {unassigned_count} | "
            f"Meeting: {meeting_id} | "
            f"Secretary: {secretary.id}"
        )

        return {
            "confirmed_count":  confirmed_count,
            "unassigned_count": unassigned_count,
            "message": (
                f"{confirmed_count} ta topshiriq xodimlarga yuborildi"
                + (
                    f" ({unassigned_count} ta mas'ul belgilanmagan)"
                    if unassigned_count > 0
                    else ""
                )
            ),
        }

    # --- HISOBOTLAR ---

    async def get_report(
        self,
        task_id: UUID,
    ) -> TaskReport | None:
        return await self.report_repo.get_by_task(task_id)

    async def get_meeting_reports(
        self,
        meeting_id: UUID,
    ) -> list[TaskReport]:
        return await self.report_repo.get_by_meeting(meeting_id)

    async def review_report(
        self,
        task_id: UUID,
        data: ReportReview,
        secretary: User,
    ) -> TaskReport:
        report = await self.report_repo.get_by_task(task_id)
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Hisobot topilmadi",
            )
        if report.status != "submitted":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Hisobot allaqachon ko'rib chiqilgan",
            )

        reviewed_report = await self.report_repo.update_status(
            report=report,
            action=data.action,
            reviewer_id=secretary.id,
            rejection_note=data.rejection_note,
        )

        # Task statusini yangilash
        task = await self.task_repo.get_by_id(task_id)
        if task:
            new_status = (
                "approved" if data.action == "approve" else "rejected"
            )
            await self.task_repo.update_status(task, new_status)

        logger.info(
            f"Hisobot ko'rib chiqildi | "
            f"Task: {task_id} | "
            f"Action: {data.action} | "
            f"Secretary: {secretary.id}"
        )

        return reviewed_report
