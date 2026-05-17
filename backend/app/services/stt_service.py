import asyncio
import logging
import time
from pathlib import Path
from typing import Optional

import torch

from app.core.config import settings


logger = logging.getLogger(__name__)


class STTService:

    _instance: Optional["STTService"] = None
    _pipeline = None

    def __new__(cls) -> "STTService":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        pass

    def _load_model(self) -> None:
        if self._pipeline is not None:
            return

        logger.info("HuggingFace O'zbek Whisper modeli yuklanmoqda...")
        start = time.time()

        try:
            from transformers import pipeline

            device = "cuda" if torch.cuda.is_available() else "cpu"
            torch_dtype = (
                torch.float16
                if torch.cuda.is_available()
                else torch.float32
            )

            logger.info(f"Device: {device}")

            Path(settings.WHISPER_DOWNLOAD_ROOT).mkdir(
                parents=True, exist_ok=True
            )

            self._pipeline = pipeline(
                task="automatic-speech-recognition",
                model="risqovfazliddin/whisper-large-v3-uz",
                torch_dtype=torch_dtype,
                device=device,
                model_kwargs={
                    "cache_dir": settings.WHISPER_DOWNLOAD_ROOT,
                },
            )

            elapsed = time.time() - start
            logger.info(
                f"Model yuklandi: {elapsed:.2f}s | "
                f"Device: {device} | "
                f"Joylashuv: {settings.WHISPER_DOWNLOAD_ROOT}"
            )

        except Exception as e:
            logger.error(f"Model yuklanmadi: {e}")
            self._pipeline = None
            raise

    def _run_pipeline(self, audio_path: str) -> dict:
        if self._pipeline is None:
            self._load_model()

        result = self._pipeline(
            audio_path,
            generate_kwargs={
                "language": "uzbek",
                "task":     "transcribe",
            },
            return_timestamps=True,
            chunk_length_s=30,
            stride_length_s=5,
        )
        return result

    async def transcribe(
        self,
        audio_path: str,
        language: str = "uz",
        task: str = "transcribe",
    ) -> dict:
        if not Path(audio_path).exists():
            raise FileNotFoundError(
                f"Audio fayl topilmadi: {audio_path}"
            )

        logger.info(f"Transcribe boshlandi: {audio_path}")
        start = time.time()

        try:
            # Pipeline sync — executor da ishlatamiz
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self._run_pipeline(audio_path),
            )

            elapsed = time.time() - start
            transcript = result.get("text", "").strip()

            logger.info(
                f"Transcribe tugadi: {elapsed:.2f}s | "
                f"Matn uzunligi: {len(transcript)} belgi"
            )

            return {
                "transcript":      transcript,
                "duration":        0,
                "segments":        result.get("chunks", []),
                "language":        "uz",
                "elapsed_seconds": round(elapsed, 2),
            }

        except Exception as e:
            logger.error(
                f"Transcribe xatosi: {audio_path} | Error: {str(e)}"
            )
            raise

    def transcribe_sync(self, audio_path: str) -> dict:
        if not Path(audio_path).exists():
            raise FileNotFoundError(
                f"Audio fayl topilmadi: {audio_path}"
            )

        logger.info(f"Transcribe boshlandi (sync): {audio_path}")
        start = time.time()

        try:
            result = self._run_pipeline(audio_path)
            elapsed = time.time() - start
            transcript = result.get("text", "").strip()

            logger.info(
                f"Transcribe tugadi: {elapsed:.2f}s | "
                f"Matn uzunligi: {len(transcript)} belgi"
            )

            return {
                "transcript":      transcript,
                "duration":        0,
                "segments":        result.get("chunks", []),
                "language":        "uz",
                "elapsed_seconds": round(elapsed, 2),
            }

        except Exception as e:
            logger.error(
                f"Transcribe xatosi: {audio_path} | Error: {str(e)}"
            )
            raise

    async def transcribe_with_fallback(
        self,
        audio_path: str,
    ) -> dict:
        try:
            return await self.transcribe(audio_path)
        except Exception as e:
            logger.error(f"Transcribe xatosi: {e}")
            raise

    def get_model_info(self) -> dict:
        if self._pipeline is None:
            return {"status": "not_loaded"}
        return {
            "model":         "risqovfazliddin/whisper-large-v3-uz",
            "device":        str(
                next(self._pipeline.model.parameters()).device
            ),
            "download_root": settings.WHISPER_DOWNLOAD_ROOT,
            "status":        "loaded",
        }


stt_service = STTService()
