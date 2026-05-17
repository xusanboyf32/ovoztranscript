import logging
import os
from pathlib import Path

from celery import Task as CeleryTask
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


# --- Audio bo'laklash ---

def get_audio_size_mb(audio_path: str) -> float:
    return os.path.getsize(audio_path) / (1024 * 1024)


def split_audio_to_chunks(
    audio_path: str,
    chunk_minutes: int = 10,
) -> list[str]:
    from pydub import AudioSegment

    logger.info(
        f"Audio bo'laklanmoqda | "
        f"Fayl: {audio_path} | "
        f"Bo'lak: {chunk_minutes} daqiqa"
    )

    audio = AudioSegment.from_file(audio_path)
    chunk_ms = chunk_minutes * 60 * 1000
    total_duration_min = len(audio) / 60000
    chunks = []

    for i, start in enumerate(range(0, len(audio), chunk_ms)):
        chunk = audio[start:start + chunk_ms]
        chunk_path = f"{audio_path}_chunk_{i:03d}.mp3"
        chunk.export(chunk_path, format="mp3", bitrate="64k")
        chunks.append(chunk_path)
        logger.info(
            f"Bo'lak {i + 1} saqlandi: {chunk_path} | "
            f"Hajm: {get_audio_size_mb(chunk_path):.1f} MB"
        )

    logger.info(
        f"Bo'laklash tugadi | "
        f"Jami: {len(chunks)} bo'lak | "
        f"Davomiylik: {total_duration_min:.1f} daqiqa"
    )
    return chunks


def cleanup_chunks(chunks: list[str]) -> None:
    for chunk_path in chunks:
        try:
            if os.path.exists(chunk_path):
                os.remove(chunk_path)
        except Exception as e:
            logger.warning(f"Bo'lak o'chirilmadi: {chunk_path} | {e}")


# --- Groq STT ---

def transcribe_chunk(
    client,
    chunk_path: str,
    chunk_index: int,
    total_chunks: int,
) -> tuple[str, int]:
    logger.info(
        f"Transcribe | "
        f"Bo'lak {chunk_index + 1}/{total_chunks} | "
        f"Hajm: {get_audio_size_mb(chunk_path):.1f} MB"
    )
    with open(chunk_path, "rb") as f:
        result = client.audio.transcriptions.create(
            model="whisper-large-v3",
            file=f,
            language="uz",
            prompt=(
                "Ushbu audio to'liq o'zbek tilida. "
                "Faqat o'zbek tilida transkripsiya qil. "
                "Har bir so'zni aniq va to'liq yoz. "
                "Boshqa tillarga (rus, arab, turk, ingliz) tarjima qilma. "
                "Eshitilgan so'zlarni o'zgartirmay, aynan yoz. "
                "Noaniq so'zlarni ham o'zbek alifbosida yoz."
            ),
            response_format="verbose_json",
        )


    text = result.text or ""
    duration = int(result.duration) if result.duration else 0
    logger.info(
        f"Bo'lak {chunk_index + 1} tugadi | "
        f"Matn: {len(text)} belgi | "
        f"Davomiylik: {duration}s"
    )
    return text, duration


def run_stt_groq(audio_path: str) -> dict:
    from groq import Groq
    from app.core.config import settings

    client = Groq(api_key=settings.GROQ_API_KEY)
    file_size_mb = get_audio_size_mb(audio_path)

    logger.info(
        f"STT boshlandi | "
        f"Fayl: {audio_path} | "
        f"Hajm: {file_size_mb:.1f} MB"
    )

    # 24 MB dan kichik → to'g'ridan-to'g'ri
    if file_size_mb < 24.0:
        text, duration = transcribe_chunk(client, audio_path, 0, 1)
        return {"text": text, "duration": duration}

    # Katta fayl → bo'laklash
    chunks = split_audio_to_chunks(audio_path, chunk_minutes=10)
    transcripts = []
    total_duration = 0

    try:
        for i, chunk_path in enumerate(chunks):
            text, duration = transcribe_chunk(
                client, chunk_path, i, len(chunks)
            )
            transcripts.append(text)
            total_duration += duration
    finally:
        cleanup_chunks(chunks)

    full_transcript = " ".join(
        t.strip() for t in transcripts if t.strip()
    )

    logger.info(
        f"STT tugadi | "
        f"Jami transcript: {len(full_transcript)} belgi | "
        f"Jami davomiylik: {total_duration}s"
    )

    return {
        "text":     full_transcript,
        "duration": total_duration,
    }


# --- DB yangilash (sync) ---

def update_meeting_sync(meeting_id: str, data: dict) -> None:
    from sqlalchemy import create_engine, text
    from app.core.config import settings

    sync_url = settings.DATABASE_URL.replace(
        "postgresql+asyncpg://",
        "postgresql+psycopg2://",
    )
    engine = create_engine(sync_url)

    set_clause = ", ".join(
        [f"{k} = :{k}" for k in data.keys()]
    )
    query = text(
        f"UPDATE meetings SET {set_clause} WHERE id = :meeting_id"
    )

    with engine.connect() as conn:
        conn.execute(query, {**data, "meeting_id": meeting_id})
        conn.commit()

    engine.dispose()


# --- Celery Task ---

class AudioProcessingTask(CeleryTask):
    def after_return(
        self, status, retval, task_id, args, kwargs, einfo
    ):
        pass


@celery_app.task(
    bind=True,
    base=AudioProcessingTask,
    name="workers.process_audio",
    max_retries=3,
    default_retry_delay=60,
    acks_late=True,
    reject_on_worker_lost=True,
)
def process_audio_task(
    self,
    meeting_id: str,
    audio_path: str,
) -> dict:
    logger.info(
        f"Task boshlandi | Meeting: {meeting_id} | "
        f"Audio: {audio_path}"
    )

    try:
        # 1. Status → processing
        update_meeting_sync(meeting_id, {"status": "processing"})

        # 2. STT
        result = run_stt_groq(audio_path)
        transcript = result.get("text", "").strip()
        duration = result.get("duration", 0)

        logger.info(
            f"STT natija | "
            f"Meeting: {meeting_id} | "
            f"Transcript: {len(transcript)} belgi | "
            f"Duration: {duration}s"
        )

        # 3. Bo'sh transcript
        if not transcript:
            update_meeting_sync(meeting_id, {
                "status":         "failed",
                "audio_duration": 0,
            })
            logger.warning(
                f"Transcript bo'sh | Meeting: {meeting_id}"
            )
            return {
                "status": "failed",
                "reason": "empty_transcript",
            }

        # 4. Transcript saqlash → ready
        update_meeting_sync(meeting_id, {
            "transcript":     transcript,
            "audio_duration": duration,
            "status":         "ready",
        })

        logger.info(
            f"Task muvaffaqiyatli | Meeting: {meeting_id}"
        )

        return {
            "status":            "ready",
            "meeting_id":        meeting_id,
            "duration":          duration,
            "transcript_length": len(transcript),
        }

    except Exception as exc:
        logger.error(
            f"Audio processing xatosi | "
            f"Meeting: {meeting_id} | "
            f"Urinish: {self.request.retries + 1}/{self.max_retries} | "
            f"Xato: {str(exc)}"
        )
        try:
            update_meeting_sync(meeting_id, {"status": "failed"})
        except Exception:
            pass
        raise self.retry(exc=exc)
