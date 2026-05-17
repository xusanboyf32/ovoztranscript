from uuid import UUID

from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import RequireSecretary
from app.database import get_db
from app.repositories.meeting_repo import MeetingRepository
from app.repositories.task_repo import TaskRepository
from app.repositories.report_repo import ReportRepository
from app.repositories.user_repo import UserRepository
from app.schemas.meeting import TranscriptUpdate
from app.schemas.task import TaskUpdate
from app.schemas.report import ReportReview
from app.services.llm_service import llm_service
from app.services.secretary_service import SecretaryService


router = APIRouter(prefix="/secretary", tags=["Secretary"])


def get_secretary_service(
    db: AsyncSession = Depends(get_db),
) -> SecretaryService:
    return SecretaryService(
        db=db,
        meeting_repo=MeetingRepository(db),
        task_repo=TaskRepository(db),
        report_repo=ReportRepository(db),
        user_repo=UserRepository(db),
        llm_service=llm_service,
    )


# --- MAJLISLAR ---

@router.get("/meetings")
async def get_meetings(
    secretary: RequireSecretary,
    page: int = 1,
    size: int = 20,
    service: SecretaryService = Depends(get_secretary_service),
) -> dict:
    return await service.get_meetings(
        page=page,
        size=size,
    )


@router.get("/meetings/{meeting_id}")
async def get_meeting_detail(
    meeting_id: UUID,
    secretary: RequireSecretary,
    service: SecretaryService = Depends(get_secretary_service),
) -> dict:
    meeting = await service.get_meeting_detail(meeting_id)
    return {
        "id":                meeting.id,
        "title":             meeting.title,
        "status":            meeting.status,
        "audio_duration":    meeting.audio_duration,
        "transcript":        meeting.transcript,
        "edited_transcript": meeting.edited_transcript,
        "meeting_date":      meeting.meeting_date,
        "created_at":        meeting.created_at,
        "updated_at":        meeting.updated_at,
        "creator": {
            "id":        meeting.creator.id,
            "full_name": meeting.creator.full_name,
        } if meeting.creator else None,
        "tasks": [
            {
                "id":          task.id,
                "title":       task.title,
                "description": task.description,
                "task_type":   task.task_type,
                "priority":    task.priority,
                "status":      task.status,
                "deadline":    task.deadline,
                "amount":      task.amount,
                "currency":    task.currency,
                "is_edited":   task.is_edited,
                "order_index": task.order_index,
                "assignee": {
                    "id":        task.assignee.id,
                    "full_name": task.assignee.full_name,
                    "position":  task.assignee.position,
                } if task.assignee else None,
                "report": {
                    "id":          task.report.id,
                    "status":      task.report.status,
                    "submitted_at": task.report.submitted_at,
                } if task.report else None,
            }
            for task in meeting.tasks
        ],
    }


# --- TRANSCRIPT ---

@router.patch("/meetings/{meeting_id}/transcript")
async def update_transcript(
    meeting_id: UUID,
    body: TranscriptUpdate,
    secretary: RequireSecretary,
    service: SecretaryService = Depends(get_secretary_service),
) -> dict:
    meeting = await service.update_transcript(
        meeting_id=meeting_id,
        data=body,
        secretary=secretary,
    )
    return {
        "message":           "Transcript yangilandi",
        "edited_transcript": meeting.edited_transcript,
    }


# --- TAQSIMLASH ---

@router.post("/meetings/{meeting_id}/distribute")
async def distribute_tasks(
    meeting_id: UUID,
    secretary: RequireSecretary,
    service: SecretaryService = Depends(get_secretary_service),
) -> dict:
    tasks = await service.distribute_tasks(
        meeting_id=meeting_id,
        secretary=secretary,
    )
    return {
        "message": f"{len(tasks)} ta topshiriq ajratildi",
        "total":   len(tasks),
        "tasks": [
            {
                "id":          task.id,
                "title":       task.title,
                "task_type":   task.task_type,
                "priority":    task.priority,
                "status":      task.status,
                "deadline":    task.deadline,
                "amount":      task.amount,
                "currency":    task.currency,
                "order_index": task.order_index,
                "assignee": {
                    "id":        task.assignee.id,
                    "full_name": task.assignee.full_name,
                } if task.assignee else None,
            }
            for task in tasks
        ],
    }


# --- TASK CRUD ---

@router.patch("/tasks/{task_id}")
async def update_task(
    task_id: UUID,
    body: TaskUpdate,
    secretary: RequireSecretary,
    service: SecretaryService = Depends(get_secretary_service),
) -> dict:
    task = await service.update_task(
        task_id=task_id,
        data=body,
        secretary=secretary,
    )
    return {
        "message": "Topshiriq yangilandi",
        "task": {
            "id":          task.id,
            "title":       task.title,
            "description": task.description,
            "task_type":   task.task_type,
            "priority":    task.priority,
            "status":      task.status,
            "deadline":    task.deadline,
            "amount":      task.amount,
            "currency":    task.currency,
            "is_edited":   task.is_edited,
            "assignee": {
                "id":        task.assignee.id,
                "full_name": task.assignee.full_name,
            } if task.assignee else None,
        },
    }


@router.delete(
    "/tasks/{task_id}",
    status_code=status.HTTP_200_OK,
)
async def delete_task(
    task_id: UUID,
    secretary: RequireSecretary,
    service: SecretaryService = Depends(get_secretary_service),
) -> dict:
    await service.delete_task(
        task_id=task_id,
        secretary=secretary,
    )
    return {"message": "Topshiriq o'chirildi"}


# --- TASDIQLASH ---

@router.post("/meetings/{meeting_id}/confirm")
async def confirm_tasks(
    meeting_id: UUID,
    secretary: RequireSecretary,
    service: SecretaryService = Depends(get_secretary_service),
) -> dict:
    return await service.confirm_tasks(
        meeting_id=meeting_id,
        secretary=secretary,
    )


# --- HISOBOTLAR ---

@router.get("/tasks/{task_id}/report")
async def get_report(
    task_id: UUID,
    secretary: RequireSecretary,
    service: SecretaryService = Depends(get_secretary_service),
) -> dict | None:
    report = await service.get_report(task_id)
    if not report:
        return None

    return {
        "id":             report.id,
        "task_id":        report.task_id,
        "report_text":    report.report_text,
        "status":         report.status,
        "rejection_note": report.rejection_note,
        "submitted_at":   report.submitted_at,
        "reviewed_at":    report.reviewed_at,
        "employee": {
            "id":        report.employee.id,
            "full_name": report.employee.full_name,
            "position":  report.employee.position,
        },
        "reviewer": {
            "id":        report.reviewer.id,
            "full_name": report.reviewer.full_name,
        } if report.reviewer else None,
        "attachments": [
            {
                "id":          a.id,
                "file_name":   a.file_name,
                "file_type":   a.file_type,
                "file_size":   a.file_size,
                "mime_type":   a.mime_type,
                "uploaded_at": a.uploaded_at,
                "file_url": f"/media/{a.file_path.replace(chr(92), '/').lstrip('media/').lstrip('/')}",

            }
            for a in report.attachments
        ],
    }


@router.get("/meetings/{meeting_id}/reports")
async def get_meeting_reports(
    meeting_id: UUID,
    secretary: RequireSecretary,
    service: SecretaryService = Depends(get_secretary_service),
) -> dict:
    reports = await service.get_meeting_reports(meeting_id)
    return {
        "total":   len(reports),
        "reports": [
            {
                "id":           r.id,
                "task_id":      r.task_id,
                "status":       r.status,
                "submitted_at": r.submitted_at,
                "employee": {
                    "id":        r.employee.id,
                    "full_name": r.employee.full_name,
                },
            }
            for r in reports
        ],
    }


@router.post("/tasks/{task_id}/report/review")
async def review_report(
    task_id: UUID,
    body: ReportReview,
    secretary: RequireSecretary,
    service: SecretaryService = Depends(get_secretary_service),
) -> dict:
    report = await service.review_report(
        task_id=task_id,
        data=body,
        secretary=secretary,
    )
    return {
        "message": (
            "Hisobot tasdiqlandi"
            if body.action == "approve"
            else "Hisobot qaytarildi"
        ),
        "report": {
            "id":             report.id,
            "status":         report.status,
            "rejection_note": report.rejection_note,
            "reviewed_at":    report.reviewed_at,
        },
    }


# --- XODIMLAR ---
@router.get("/employees")
async def get_employees(
    secretary: RequireSecretary,
    db: AsyncSession = Depends(get_db),
) -> dict:
    user_repo = UserRepository(db)
    employees = await user_repo.get_employees()
    return {
        "employees": [
            {
                "id":         str(emp.id),
                "full_name":  emp.full_name,
                "position":   emp.position,
                "department": emp.department,
            }
            for emp in employees
        ]
    }



