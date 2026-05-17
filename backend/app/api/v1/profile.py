import os
import uuid
from pathlib import Path
from datetime import date

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.dependencies import get_current_user
from app.database import get_db
from app.models.user import User
from app.repositories.user_repo import UserRepository

router = APIRouter(prefix="/profile", tags=["Profile"])


class ProfileUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    phone: str | None = None
    birth_date: date | None = None
    position: str | None = None
    department: str | None = None


class ProfileOut(BaseModel):
    id: str
    username: str
    full_name: str
    first_name: str | None
    last_name: str | None
    email: str | None
    phone: str | None
    birth_date: date | None
    position: str | None
    department: str | None
    role: str
    avatar_url: str | None
    is_active: bool

    class Config:
        from_attributes = True


@router.get("", response_model=ProfileOut)
async def get_profile(
    current_user: User = Depends(get_current_user),
):
    avatar_url = None
    if current_user.avatar_path:
        avatar_url = f"/media/{current_user.avatar_path}"

    return ProfileOut(
        id=str(current_user.id),
        username=current_user.username,
        full_name=current_user.full_name,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        email=current_user.email,
        phone=current_user.phone,
        birth_date=current_user.birth_date,
        position=current_user.position,
        department=current_user.department,
        role=current_user.role,
        avatar_url=avatar_url,
        is_active=current_user.is_active,
    )


@router.patch("", response_model=ProfileOut)
async def update_profile(
    data: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user_repo = UserRepository(db)

    update_data = data.model_dump(exclude_none=True)
    for key, value in update_data.items():
        setattr(current_user, key, value)

    await db.commit()
    await db.refresh(current_user)

    avatar_url = None
    if current_user.avatar_path:
        avatar_url = f"/media/{current_user.avatar_path}"

    return ProfileOut(
        id=str(current_user.id),
        username=current_user.username,
        full_name=current_user.full_name,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        email=current_user.email,
        phone=current_user.phone,
        birth_date=current_user.birth_date,
        position=current_user.position,
        department=current_user.department,
        role=current_user.role,
        avatar_url=avatar_url,
        is_active=current_user.is_active,
    )


@router.post("/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Fayl turi tekshirish
    allowed = {'image/jpeg', 'image/png', 'image/webp'}
    if file.content_type not in allowed:
        raise HTTPException(
            status_code=400,
            detail="Faqat JPG, PNG, WEBP formatlar qabul qilinadi",
        )

    # Fayl hajmi tekshirish (5MB)
    content = await file.read()
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail="Fayl hajmi 5MB dan oshmasligi kerak",
        )

    # Saqlash
    ext = file.filename.split('.')[-1]
    filename = f"avatars/{current_user.id}.{ext}"
    save_path = Path("media") / filename
    save_path.parent.mkdir(parents=True, exist_ok=True)

    with open(save_path, "wb") as f:
        f.write(content)

    # DB yangilash
    current_user.avatar_path = filename
    await db.commit()

    return {
        "message": "Avatar yuklandi",
        "avatar_url": f"/media/{filename}",
    }
