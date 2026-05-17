import os
import uuid
import mimetypes
from datetime import datetime, timezone
from pathlib import Path

from fastapi import HTTPException, UploadFile, status

from app.core.config import settings


# --- Fayl turlari va limitlar ---

ALLOWED_FILE_TYPES: dict[str, dict] = {
    "image": {
        "mimes": {
            "image/jpeg",
            "image/png",
            "image/webp",
            "image/gif",
        },
        "extensions": {".jpg", ".jpeg", ".png", ".webp", ".gif"},
        "max_size": 10 * 1024 * 1024,       # 10 MB
        "max_size_label": "10 MB",
    },
    "video": {
        "mimes": {
            "video/mp4",
            "video/quicktime",
            "video/x-msvideo",
            "video/webm",
        },
        "extensions": {".mp4", ".mov", ".avi", ".webm"},
        "max_size": 200 * 1024 * 1024,      # 200 MB
        "max_size_label": "200 MB",
    },
    "document": {
        "mimes": {
            "application/pdf",
            "application/msword",
            "application/vnd.openxmlformats-officedocument"
            ".wordprocessingml.document",
            "application/vnd.ms-excel",
            "application/vnd.openxmlformats-officedocument"
            ".spreadsheetml.sheet",
        },
        "extensions": {".pdf", ".doc", ".docx", ".xls", ".xlsx"},
        "max_size": 20 * 1024 * 1024,       # 20 MB
        "max_size_label": "20 MB",
    },
    "audio": {
        "mimes": {
            "audio/mpeg",
            "audio/wav",
            "audio/ogg",
            "audio/webm",
            "audio/mp4",
            "audio/x-m4a",
        },
        "extensions": {".mp3", ".wav", ".ogg", ".webm", ".m4a"},
        "max_size": 500 * 1024 * 1024,      # 500 MB — rahbar soatlab yozadi
        "max_size_label": "500 MB",
    },
}

AUDIO_MEETING_MAX_SIZE = 2 * 1024 * 1024 * 1024   # 2 GB — majlis audio


# --- Yordamchi funksiyalar ---

def get_file_extension(filename: str) -> str:
    return Path(filename).suffix.lower()


def get_mime_type(filename: str) -> str:
    mime, _ = mimetypes.guess_type(filename)
    return mime or "application/octet-stream"


def detect_file_type(mime_type: str, extension: str) -> str | None:
    for file_type, config in ALLOWED_FILE_TYPES.items():
        if mime_type in config["mimes"] or extension in config["extensions"]:
            return file_type
    return None


def generate_unique_filename(original_filename: str) -> str:
    extension = get_file_extension(original_filename)
    unique_id = uuid.uuid4().hex
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    return f"{timestamp}_{unique_id}{extension}"


def build_file_url(file_path: str) -> str:
    normalized = file_path.replace("\\", "/")
    if normalized.startswith(settings.MEDIA_DIR):
        normalized = normalized[len(settings.MEDIA_DIR):]
    normalized = normalized.lstrip("/")
    return f"{settings.FRONTEND_URL}/media/{normalized}"


def get_media_path(*parts: str) -> Path:
    return Path(settings.MEDIA_DIR).joinpath(*parts)


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


# --- Validatsiya ---

def validate_upload_file(
    file: UploadFile,
    allowed_types: set[str] | None = None,
) -> tuple[str, str]:
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Fayl nomi bo'sh",
        )

    extension = get_file_extension(file.filename)
    mime_type = file.content_type or get_mime_type(file.filename)
    file_type = detect_file_type(mime_type, extension)

    if file_type is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Qo'llab-quvvatlanmaydigan fayl turi: {extension}. "
                f"Ruxsat etilgan: jpg, png, mp4, pdf, docx, mp3 va boshqalar"
            ),
        )

    if allowed_types and file_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Bu yerda faqat quyidagi fayl turlari ruxsat etilgan: "
                f"{', '.join(allowed_types)}"
            ),
        )

    return file_type, mime_type


async def validate_file_size(
    file: UploadFile,
    file_type: str,
    is_meeting_audio: bool = False,
) -> int:
    content = await file.read()
    file_size = len(content)
    await file.seek(0)

    if is_meeting_audio:
        max_size = AUDIO_MEETING_MAX_SIZE
        max_label = "2 GB"
    else:
        config = ALLOWED_FILE_TYPES.get(file_type, {})
        max_size = config.get("max_size", 10 * 1024 * 1024)
        max_label = config.get("max_size_label", "10 MB")

    if file_size > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=(
                f"Fayl hajmi juda katta. "
                f"Maksimal: {max_label}. "
                f"Yuklangan: {file_size / (1024 * 1024):.1f} MB"
            ),
        )

    return file_size


# --- Fayl saqlash ---

async def save_audio_file(
    file: UploadFile,
    meeting_id: str,
) -> tuple[str, int]:
    _, mime_type = validate_upload_file(
        file,
        allowed_types={"audio", "video"},
    )
    file_size = await validate_file_size(
        file,
        file_type="audio",
        is_meeting_audio=True,
    )

    save_dir = get_media_path("audio", meeting_id)
    ensure_dir(save_dir)

    unique_name = generate_unique_filename(file.filename or "audio.webm")
    file_path = save_dir / unique_name

    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    return str(file_path), file_size


async def save_report_file(
    file: UploadFile,
    task_id: str,
    employee_id: str,
) -> tuple[str, str, str, int]:
    file_type, mime_type = validate_upload_file(file)
    file_size = await validate_file_size(file, file_type)

    save_dir = get_media_path("reports", task_id, employee_id)
    ensure_dir(save_dir)

    unique_name = generate_unique_filename(file.filename or "file")
    file_path = save_dir / unique_name

    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    return str(file_path), file_type, mime_type, file_size


def delete_file(file_path: str) -> bool:
    try:
        path = Path(file_path)
        if path.exists():
            path.unlink()
            return True
        return False
    except Exception:
        return False


def delete_directory(dir_path: str) -> bool:
    import shutil
    try:
        path = Path(dir_path)
        if path.exists():
            shutil.rmtree(path)
            return True
        return False
    except Exception:
        return False


def get_file_size_label(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"
