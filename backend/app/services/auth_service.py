from uuid import UUID

from fastapi import HTTPException, status

from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
)
from app.models.user import User
from app.repositories.user_repo import UserRepository
from app.schemas.auth import UserCreate, UserUpdate


class AuthService:

    def __init__(self, repo: UserRepository) -> None:
        self.repo = repo

    async def login(
        self,
        username: str,
        password: str,
    ) -> dict:
        user = await self.repo.get_by_username(username)

        # Xavfsizlik: username yoki parol xato bo'lsa bir xil xabar
        # Ikki xil xabar bo'lsa attacker username mavjudligini biladi
        if not user or not verify_password(password, user.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Username yoki parol noto'g'ri",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Foydalanuvchi bloklangan",
            )

        access_token = create_access_token(
            user_id=str(user.id),
            role=user.role,
        )
        refresh_token = create_refresh_token(
            user_id=str(user.id),
            role=user.role,
        )

        return {
            "access_token":  access_token,
            "refresh_token": refresh_token,
            "user":          user,
        }

    async def create_user(self, data: UserCreate) -> User:
        exists = await self.repo.exists_by_username(data.username)
        if exists:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Bu username band",
            )

        user_dict = data.model_dump()
        user_dict["password"] = hash_password(data.password)

        return await self.repo.create(user_dict)

    async def update_user(
        self,
        user_id: UUID,
        data: UserUpdate,
    ) -> User:
        user = await self.repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Foydalanuvchi topilmadi",
            )

        update_data = data.model_dump(exclude_none=True)

        if "password" in update_data:
            update_data["password"] = hash_password(update_data["password"])

        # Username o'zgartirilsa band emasligini tekshirish
        if "username" in update_data:
            exists = await self.repo.exists_by_username(update_data["username"])
            if exists and update_data["username"] != user.username:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Bu username band",
                )

        return await self.repo.update(user, update_data)

    async def delete_user(self, user_id: UUID) -> None:
        user = await self.repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Foydalanuvchi topilmadi",
            )
        await self.repo.delete(user)

    async def block_user(self, user_id: UUID) -> User:
        user = await self.repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Foydalanuvchi topilmadi",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Foydalanuvchi allaqachon bloklangan",
            )

        return await self.repo.soft_delete(user)

    async def unblock_user(self, user_id: UUID) -> User:
        user = await self.repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Foydalanuvchi topilmadi",
            )

        if user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Foydalanuvchi allaqachon faol",
            )

        return await self.repo.update(user, {"is_active": True})
