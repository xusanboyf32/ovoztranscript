from uuid import UUID
from typing import List

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import RequireEmployee
from app.database import get_db
from app.repositories.report_repo import ReportRepository
from app.repositories.task_repo import TaskRepository
from app.services.employee_service import EmployeeService


router = APIRouter(prefix="/employee", tags=["Employee"])


def get_employee_service(
    db: AsyncSession = Depends(get_db),
) -> EmployeeService:
    return EmployeeService(
        db=db,
        task_repo=TaskRepository(db),
        report_repo=ReportRepository(db),
    )


# --- TASKLAR ---

@router.get("/my-tasks")
async def get_my_tasks(
    employee: RequireEmployee,
    status_filter: str | None = None,
    service: EmployeeService = Depends(get_employee_service),
) -> dict:
    return await service.get_my_tasks(
        employee=employee,
        status_filter=status_filter,
    )


@router.get("/my-tasks/{task_id}")
async def get_task_detail(
    task_id: UUID,
    employee: RequireEmployee,
    service: EmployeeService = Depends(get_employee_service),
) -> dict:
    return await service.get_task_detail(
        task_id=task_id,
        employee=employee,
    )


# --- HISOBOT ---

@router.post(
    "/tasks/{task_id}/report",
    status_code=status.HTTP_201_CREATED,
)
async def submit_report(
    task_id: UUID,
    employee: RequireEmployee,
    report_text: str | None = Form(
        default=None,
        max_length=10000,
        description="Matnli hisobot",
    ),
    files: List[UploadFile] = File(
        default=[],
        description="Rasm, video, hujjat yoki audio fayllar",
    ),
    service: EmployeeService = Depends(get_employee_service),
) -> dict:
    report = await service.submit_report(
        task_id=task_id,
        employee=employee,
        report_text=report_text,
        files=[f for f in files if f.filename],
    )
    return {
        "message":    "Hisobot muvaffaqiyatli yuborildi",
        "report_id":  report.id,
        "status":     report.status,
        "submitted_at": report.submitted_at,
    }


@router.get("/tasks/{task_id}/report")
async def get_my_report(
    task_id: UUID,
    employee: RequireEmployee,
    service: EmployeeService = Depends(get_employee_service),
) -> dict:
    task = await service.get_task_detail(
        task_id=task_id,
        employee=employee,
    )
    report = task.get("report")
    if not report:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hisobot topilmadi",
        )
    return report


@router.delete(
    "/tasks/{task_id}/report/attachments/{attachment_id}",
    status_code=status.HTTP_200_OK,
)
async def delete_attachment(
    task_id: UUID,
    attachment_id: UUID,
    employee: RequireEmployee,
    service: EmployeeService = Depends(get_employee_service),
) -> dict:
    await service.delete_attachment(
        attachment_id=attachment_id,
        employee=employee,
    )
    return {"message": "Fayl o'chirildi"}


# --- PROFIL ---

@router.get("/profile")
async def get_profile(
    employee: RequireEmployee,
) -> dict:
    return {
        "id":         employee.id,
        "username":   employee.username,
        "full_name":  employee.full_name,
        "position":   employee.position,
        "department": employee.department,
        "phone":      employee.phone,
        "role":       employee.role,
    }


# --- STATISTIKA ---

@router.get("/my-stats")
async def get_my_stats(
    employee: RequireEmployee,
    db: AsyncSession = Depends(get_db),
) -> dict:
    task_repo = TaskRepository(db)

    status_counts = await task_repo.count_by_status(
        employee_id=employee.id,
    )
    overdue = await task_repo.get_overdue(
        employee_id=employee.id,
    )

    total = sum(status_counts.values())
    approved = status_counts.get("approved", 0)

    return {
        "total":           total,
        "status_counts":   status_counts,
        "overdue_count":   len(overdue),
        "completion_rate": (
            round(approved / total * 100, 1)
            if total > 0 else 0
        ),
    }

