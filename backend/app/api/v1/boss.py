from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import RequireBoss
from app.database import get_db
from app.repositories.meeting_repo import MeetingRepository
from app.repositories.task_repo import TaskRepository
from app.repositories.user_repo import UserRepository
from app.services.boss_service import BossService
from app.utils.file_utils import save_audio_file
from app.utils.datetime_utils import now_utc


router = APIRouter(prefix="/boss", tags=["Boss"])


def get_boss_service(
    db: AsyncSession = Depends(get_db),
) -> BossService:
    return BossService(
        db=db,
        meeting_repo=MeetingRepository(db),
        task_repo=TaskRepository(db),
        user_repo=UserRepository(db),
    )


# --- AUDIO YUKLASH ---

@router.post(
    "/meetings/upload-audio",
    status_code=status.HTTP_201_CREATED,
)
async def upload_audio(
    boss: RequireBoss,
    audio: UploadFile = File(..., description="Audio fayl (webm, mp4, mp3)"),
    title: str | None = Form(default=None, max_length=500),
    db: AsyncSession = Depends(get_db),
) -> dict:
    from app.models.meeting import Meeting
    from app.workers.audio_worker import process_audio_task

    # Audio faylni vaqtinchalik ID bilan saqlash
    import uuid
    temp_meeting_id = str(uuid.uuid4())

    file_path, file_size = await save_audio_file(
        file=audio,
        meeting_id=temp_meeting_id,
    )

    # Meeting yaratish
    meeting_repo = MeetingRepository(db)
    meeting = await meeting_repo.create({
        "title":          title or f"Majlis — {now_utc().strftime('%d.%m.%Y %H:%M')}",
        "audio_file_path": file_path,
        "status":         "processing",
        "created_by":     boss.id,
        "meeting_date":   now_utc(),
    })

    # Celery worker ishga tushirish
    process_audio_task.delay(
        meeting_id=str(meeting.id),
        audio_path=file_path,
    )

    return {
        "message":    "Audio yuklandi, qayta ishlanmoqda",
        "meeting_id": meeting.id,
        "status":     "processing",
    }


# --- MAJLISLAR ---

@router.get("/meetings")
async def get_meetings(
    boss: RequireBoss,
    service: BossService = Depends(get_boss_service),
) -> dict:
    return await service.get_meetings(boss=boss)


@router.get("/meetings/{meeting_id}")
async def get_meeting_detail(
    meeting_id: UUID,
    boss: RequireBoss,
    service: BossService = Depends(get_boss_service),
) -> dict:
    meeting = await service.get_meeting_detail(
        meeting_id=meeting_id,
        boss=boss,
    )

    return {
        "id": meeting.id,
        "title": meeting.title,
        "status": meeting.status,
        "audio_duration": meeting.audio_duration,
        "audio_file_path": meeting.audio_file_path,
        "transcript": meeting.transcript,
        "edited_transcript": meeting.edited_transcript,
        "meeting_date": meeting.meeting_date,
        "created_at": meeting.created_at,
        "tasks": [
            {
                "id": task.id,
                "title": task.title,
                "description": task.description,
                "task_type": task.task_type,
                "priority": task.priority,
                "status": task.status,
                "deadline": task.deadline,
                "amount": task.amount,
                "currency": task.currency,
                "assignee": {
                    "id": task.assignee.id,
                    "full_name": task.assignee.full_name,
                    "position": task.assignee.position,
                } if task.assignee else None,
                "report": {
                    "id": task.report.id,
                    "status": task.report.status,
                    "report_text": task.report.report_text,
                    "submitted_at": task.report.submitted_at,
                    "reviewed_at": task.report.reviewed_at,
                    "rejection_note": task.report.rejection_note,
                    "employee": {
                        "id": task.report.employee.id,
                        "full_name": task.report.employee.full_name,
                        "position": task.report.employee.position,
                    } if task.report.employee else None,
                    "attachments": [
                        {
                            "id": a.id,
                            "file_name": a.file_name,
                            "file_type": a.file_type,
                            "file_size": a.file_size,
                            "mime_type": a.mime_type,
                            "file_url": f"/media/{a.file_path.replace(chr(92), '/').lstrip('media/').lstrip('/')}",
                        }
                        for a in task.report.attachments
                    ],
                } if task.report else None,
            }
            for task in meeting.tasks
        ],
    }


# --- OVERVIEW ---

@router.get("/overview")
async def get_overview(
    boss: RequireBoss,
    service: BossService = Depends(get_boss_service),
) -> dict:
    return await service.get_overview()


# --- STATISTIKA ---

@router.get("/stats")
async def get_stats(
    boss: RequireBoss,
    service: BossService = Depends(get_boss_service),
) -> dict:
    return await service.get_stats()


# --- XODIM BO'YICHA ---

@router.get("/employees/{employee_id}/tasks")
async def get_employee_tasks(
    employee_id: UUID,
    boss: RequireBoss,
    service: BossService = Depends(get_boss_service),
) -> dict:
    return await service.get_employee_tasks(
        employee_id=employee_id,
    )


# --- MEETING STATUS POLLING ---

@router.get("/meetings/{meeting_id}/status")
async def get_meeting_status(
    meeting_id: UUID,
    boss: RequireBoss,
    db: AsyncSession = Depends(get_db),
) -> dict:
    meeting_repo = MeetingRepository(db)
    meeting = await meeting_repo.get_by_id(
        meeting_id,
        load_tasks=False,
    )
    if not meeting:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Majlis topilmadi",
        )
    if meeting.created_by != boss.id:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu majlis sizga tegishli emas",
        )

    return {
        "meeting_id": meeting.id,
        "status":     meeting.status,
        "title":      meeting.title,
    }
