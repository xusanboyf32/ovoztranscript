from celery import Celery
from app.core.config import settings


celery_app = Celery(
    "voicetask",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.workers.audio_worker"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Asia/Tashkent",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    result_expires=3600,
    task_soft_time_limit=3600,
    task_time_limit=7200,
    task_default_queue="default",
)
