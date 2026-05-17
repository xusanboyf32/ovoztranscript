from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_token, verify_token_type
from app.database import get_db
from app.models.user import User
from app.repositories.user_repo import UserRepository


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User:
    token = request.cookies.get("access_token")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tizimga kirilmagan",
        )

    payload = decode_token(token)
    verify_token_type(payload, "access")

    user_id: str | None = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token yaroqsiz",
        )

    repo = UserRepository(db)
    user = await repo.get_by_id(UUID(user_id))

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Foydalanuvchi topilmadi",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Foydalanuvchi bloklangan",
        )

    return user


def require_role(*roles: str):
    async def checker(
        user: User = Depends(get_current_user),
    ) -> User:
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Ruxsat yo'q",
            )
        return user
    return checker


# --- Tayyor Depends o'zgaruvchilar ---

CurrentUser = Annotated[User, Depends(get_current_user)]

RequireAdmin    = Annotated[User, Depends(require_role("admin"))]
RequireBoss     = Annotated[User, Depends(require_role("boss"))]
RequireSecretary = Annotated[User, Depends(require_role("secretary"))]
RequireEmployee  = Annotated[User, Depends(require_role("employee"))]

RequireBossOrSecretary = Annotated[
    User,
    Depends(require_role("boss", "secretary"))
]
