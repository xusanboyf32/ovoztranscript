import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqladmin import Admin, ModelView
from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request

from app.core.config import settings
from app.core.security import hash_password
from app.database import engine
from app.models.user import User
from app.models.meeting import Meeting
from app.models.task import Task
from app.models.task_report import TaskReport
from app.models.report_attachment import ReportAttachment
from app.api.v1.auth import router as auth_router
from app.api.v1.boss import router as boss_router
from app.api.v1.secretary import router as secretary_router
from app.api.v1.employee import router as employee_router

from app.api.v1.profile import router as profile_router

from fastapi.staticfiles import StaticFiles



logger = logging.getLogger(__name__)


# --- Lifespan ---

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"{settings.APP_NAME} ishga tushmoqda...")

    # Media papkalar yaratish
    media_dirs = [
        Path(settings.MEDIA_DIR) / "audio",
        Path(settings.MEDIA_DIR) / "reports",
    ]
    for directory in media_dirs:
        directory.mkdir(parents=True, exist_ok=True)
        logger.info(f"Media papka tayyor: {directory}")

    # Whisper modelini oldindan yuklash
    try:
        from app.services.stt_service import stt_service
        info = stt_service.get_model_info()
        logger.info(f"Whisper model: {info}")
    except Exception as e:
        logger.warning(f"Whisper yuklanmadi: {e}")

    logger.info(f"{settings.APP_NAME} tayyor!")

    yield

    # Shutdown
    logger.info(f"{settings.APP_NAME} to'xtatilmoqda...")
    await engine.dispose()
    logger.info("DB ulanish yopildi")


# --- FastAPI App ---

app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "Rahbarning og'zaki topshiriqlarini avtomatik "
        "raqamlashtiruvchi tizim"
    ),
    version="1.0.0",
    debug=settings.DEBUG,
    lifespan=lifespan,
    docs_url="/api/docs" if settings.DEBUG else None,
    redoc_url="/api/redoc" if settings.DEBUG else None,
    openapi_url="/api/openapi.json" if settings.DEBUG else None,
)


# --- CORS ---

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Static files ---

Path(settings.MEDIA_DIR).mkdir(parents=True, exist_ok=True)

app.mount(
    "/media",
    StaticFiles(directory=settings.MEDIA_DIR),
    name="media",
)


# --- Routers ---

app.include_router(auth_router,      prefix="/api/v1")
app.include_router(boss_router,      prefix="/api/v1")
app.include_router(secretary_router, prefix="/api/v1")
app.include_router(employee_router,  prefix="/api/v1")
app.include_router(profile_router, prefix="/api/v1")


# --- SQLAdmin Auth ---

class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        form = await request.form()
        username = form.get("username")
        password = form.get("password")

        if (
            username == settings.ADMIN_USERNAME
            and password == settings.ADMIN_PASSWORD
        ):
            request.session.update({"admin": "authenticated"})
            return True

        logger.warning(
            f"Admin login urinishi muvaffaqiyatsiz | "
            f"Username: {username}"
        )
        return False

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        return request.session.get("admin") == "authenticated"


# --- SQLAdmin Views ---
from wtforms import SelectField

class UserAdmin(ModelView, model=User):
    name = "Foydalanuvchi"
    name_plural = "Foydalanuvchilar"
    icon = "fa-solid fa-users"
    column_list = [
        User.id,
        User.username,
        User.full_name,
        User.role,
        User.department,
        User.position,
        User.phone,
        User.is_active,
        User.created_at,
    ]
    column_searchable_list = [
        User.username,
        User.full_name,
        User.department,
    ]
    column_sortable_list = [
        User.role,
        User.is_active,
        User.created_at,
    ]
    form_excluded_columns = [
        User.created_at,
        User.updated_at,
    ]
    column_details_exclude_list = [User.password]
    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True
    page_size = 50

    # Role uchun select
    form_overrides = {
        "role": SelectField,
    }
    form_args = {
        "role": {
            "choices": [
                ("admin",     "Admin"),
                ("boss",      "Boss — Rahbar"),
                ("secretary", "Secretary — Kotiba"),
                ("employee",  "Employee — Xodim"),
            ],
            "coerce": str,
        },
    }

    async def on_model_change(
        self,
        data: dict,
        model: User,
        is_created: bool,
        request: Request,
    ) -> None:
        if "password" in data and data["password"]:
            data["password"] = hash_password(data["password"])


class MeetingAdmin(ModelView, model=Meeting):
    name = "Majlis"
    name_plural = "Majlislar"
    icon = "fa-solid fa-microphone"
    column_list = [
        Meeting.id,
        Meeting.title,
        Meeting.status,
        Meeting.audio_duration,
        Meeting.meeting_date,
        Meeting.created_at,
    ]
    column_searchable_list = [Meeting.title]
    column_sortable_list = [
        Meeting.status,
        Meeting.meeting_date,
        Meeting.created_at,
    ]
    can_create = False
    can_edit = False
    can_delete = True
    can_view_details = True
    page_size = 50


class TaskAdmin(ModelView, model=Task):
    name = "Topshiriq"
    name_plural = "Topshiriqlar"
    icon = "fa-solid fa-list-check"
    column_list = [
        Task.id,
        Task.title,
        Task.task_type,
        Task.status,
        Task.priority,
        Task.deadline,
        Task.amount,
        Task.currency,
        Task.created_at,
    ]
    column_searchable_list = [Task.title]
    column_sortable_list = [
        Task.status,
        Task.priority,
        Task.deadline,
        Task.created_at,
    ]
    can_create = False
    can_edit = False
    can_delete = True
    can_view_details = True
    page_size = 50


class TaskReportAdmin(ModelView, model=TaskReport):
    name = "Hisobot"
    name_plural = "Hisobotlar"
    icon = "fa-solid fa-file-lines"
    column_list = [
        TaskReport.id,
        TaskReport.status,
        TaskReport.submitted_at,
        TaskReport.reviewed_at,
    ]
    column_sortable_list = [
        TaskReport.status,
        TaskReport.submitted_at,
    ]
    can_create = False
    can_edit = False
    can_delete = True
    can_view_details = True
    page_size = 50


class ReportAttachmentAdmin(ModelView, model=ReportAttachment):
    name = "Fayl"
    name_plural = "Fayllar"
    icon = "fa-solid fa-paperclip"
    column_list = [
        ReportAttachment.id,
        ReportAttachment.file_name,
        ReportAttachment.file_type,
        ReportAttachment.file_size,
        ReportAttachment.uploaded_at,
    ]
    column_sortable_list = [
        ReportAttachment.file_type,
        ReportAttachment.uploaded_at,
    ]
    can_create = False
    can_edit = False
    can_delete = True
    can_view_details = True
    page_size = 50


# --- SQLAdmin Setup ---
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.sessions import SessionMiddleware


admin = Admin(
    app=app,
    engine=engine,
    authentication_backend=AdminAuth(
        secret_key=settings.ADMIN_SECRET_KEY,
    ),
    base_url="/admin",
    title=f"{settings.APP_NAME} | Admin",
)

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.ADMIN_SECRET_KEY,
    https_only=True,
    same_site="lax",
)


admin.add_view(UserAdmin)
admin.add_view(MeetingAdmin)
admin.add_view(TaskAdmin)
admin.add_view(TaskReportAdmin)
admin.add_view(ReportAttachmentAdmin)


# --- Health check ---

@app.get("/health", tags=["Health"])
async def health() -> dict:
    from sqlalchemy import text
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception:
        db_status = "error"

    return {
        "status":   "ok",
        "app":      settings.APP_NAME,
        "version":  "1.0.0",
        "database": db_status,
        "debug":    settings.DEBUG,
    }
