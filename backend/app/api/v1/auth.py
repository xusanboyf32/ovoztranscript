from fastapi import APIRouter, Depends, Response, Request, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.dependencies import CurrentUser
from app.core.security import decode_token, verify_token_type, create_access_token
from app.database import get_db
from app.repositories.user_repo import UserRepository
from app.schemas.auth import LoginRequest, LoginResponse, UserOut
from app.services.auth_service import AuthService


router = APIRouter(prefix="/auth", tags=["Auth"])

ROLE_REDIRECT_MAP = {
    "admin":     "/admin",
    "boss":      "/boss",
    "secretary": "/secretary",
    "employee":  "/employee/my-tasks",
}


def set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=not settings.DEBUG,
        samesite="strict",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=not settings.DEBUG,
        samesite="strict",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
    )


def clear_auth_cookies(response: Response) -> None:
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")


@router.post("/login", response_model=LoginResponse)
async def login(
    body: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> LoginResponse:
    service = AuthService(UserRepository(db))
    result = await service.login(body.username, body.password)

    set_auth_cookies(
        response,
        result["access_token"],
        result["refresh_token"],
    )

    user = result["user"]
    return LoginResponse(
        message="Muvaffaqiyatli kirildi",
        redirect=ROLE_REDIRECT_MAP.get(user.role, "/"),
        user=user,
    )


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    response: Response,
    _: CurrentUser,
) -> dict:
    clear_auth_cookies(response)
    return {"message": "Muvaffaqiyatli chiqildi"}


@router.post("/refresh", status_code=status.HTTP_200_OK)
async def refresh(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> dict:
    token = request.cookies.get("refresh_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token topilmadi",
        )

    payload = decode_token(token)
    verify_token_type(payload, "refresh")

    user_id: str | None = payload.get("sub")
    role: str | None = payload.get("role")

    if not user_id or not role:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token yaroqsiz",
        )

    # User hali ham aktiv ekanligini tekshirish
    repo = UserRepository(db)
    from uuid import UUID
    user = await repo.get_by_id(UUID(user_id))
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Foydalanuvchi topilmadi yoki bloklangan",
        )

    new_access_token = create_access_token(
        user_id=user_id,
        role=role,
    )

    response.set_cookie(
        key="access_token",
        value=new_access_token,
        httponly=True,
        secure=not settings.DEBUG,
        samesite="strict",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )

    return {"message": "Token yangilandi"}


@router.get("/me", response_model=UserOut)
async def me(current_user: CurrentUser) -> UserOut:
    return current_user
