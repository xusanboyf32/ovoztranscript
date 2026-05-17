from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str
    DB_NAME: str = "voicechataidb"
    DB_USER: str = "voicechatai"
    DB_PASSWORD: str = "voicechatai"

    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    OPENAI_API_KEY: str = ""
    # Redis
    REDIS_URL: str = "redis://localhost:6379"

    # Media
    MEDIA_DIR: str = "media"

    # App
    APP_NAME: str = "VoiceTask AI"
    DEBUG: bool = False
    FRONTEND_URL: str = "http://localhost:5173"

    # Groq
    GROQ_API_KEY: str

    # Whisper
    WHISPER_MODEL: str = "large-v3"

    # SQLAdmin
    ADMIN_USERNAME: str
    ADMIN_PASSWORD: str
    ADMIN_SECRET_KEY: str

    WHISPER_DOWNLOAD_ROOT: str = "/app/whisper_models"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "allow"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
