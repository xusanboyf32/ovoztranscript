from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserRepository:

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, user_id: UUID) -> User | None:
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> User | None:
        result = await self.db.execute(
            select(User).where(User.username == username.strip().lower())
        )
        return result.scalar_one_or_none()

    async def get_all(
        self,
        role: str | None = None,
        is_active: bool | None = None,
        department: str | None = None,
    ) -> list[User]:
        query = select(User).order_by(User.created_at.desc())

        if role is not None:
            query = query.where(User.role == role)

        if is_active is not None:
            query = query.where(User.is_active == is_active)

        if department is not None:
            query = query.where(User.department == department)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_employees(self) -> list[User]:
        result = await self.db.execute(
            select(User)
            .where(User.role == "employee")
            .where(User.is_active == True)
            .order_by(User.full_name)
        )
        return list(result.scalars().all())

    async def count_by_role(self, role: str) -> int:
        result = await self.db.execute(
            select(func.count()).where(User.role == role)
        )
        return result.scalar_one()

    async def exists_by_username(self, username: str) -> bool:
        result = await self.db.execute(
            select(func.count())
            .where(User.username == username.strip().lower())
        )
        count = result.scalar_one()
        return count > 0

    async def create(self, data: dict) -> User:
        user = User(**data)
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def update(self, user: User, data: dict) -> User:
        for key, value in data.items():
            if hasattr(user, key):
                setattr(user, key, value)
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def delete(self, user: User) -> None:
        await self.db.delete(user)
        await self.db.flush()

    async def soft_delete(self, user: User) -> User:
        user.is_active = False
        await self.db.flush()
        await self.db.refresh(user)
        return user
