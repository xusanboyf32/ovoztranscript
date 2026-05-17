import json
import logging
import time
from typing import Any

from groq import Groq

from app.core.config import settings
from app.utils.datetime_utils import parse_deadline_text, detect_priority_from_text
from app.utils.fuzzy_match import bulk_match_employees


logger = logging.getLogger(__name__)


TASK_EXTRACTION_SYSTEM_PROMPT = """
Siz O'zbek tilidagi yig'ilish transkripsiyasini tahlil qiluvchi 
AI assistantsiz. Sizning vazifangiz — matndan barcha topshiriqlar, 
vazifalar, to'lovlar, qarzlar va majburiyatlarni aniq ajratib olish.

QOIDALAR:
1. Faqat ANIQ topshiriqlarni ajrat — umumiy gaplarni emas
2. Bir xil topshiriq ikki marta aytilsa — faqat BIR MARTA yoz
3. Shaxs ismi tilga olingan bo'lsa — assigned_to_name ga yoz
4. Pul miqdori aytilgan bo'lsa — amount ga yoz
5. Vaqt yoki sana aytilgan bo'lsa — deadline_text ga yoz
6. FAQAT JSON massiv qaytarilsin — boshqa hech narsa yozilmasin
7. Topshiriq topilmasa — bo'sh massiv [] qaytarilsin

TASK TURLARI:
- "task"     → oddiy vazifa, topshiriq
- "payment"  → to'lov (kimgadir pul berish)
- "debt"     → qarz (kimdan pul olish)
- "general"  → umumiy, mas'ul aniq emas

PRIORITET QOIDALAR:
- "high"   → "bugun", "hozir", "zudlik", "shoshilinch", "tezda"
- "low"    → "keyinroq", "vaqt bo'lganda", "asta-sekin"
- "medium" → boshqa barcha holatlar

JAVOB FORMATI (faqat shu):
[
  {
    "title": "qisqa sarlavha (max 100 belgi)",
    "description": "to'liq tavsif",
    "task_type": "task|payment|debt|general",
    "assigned_to_name": "shaxs ismi yoki null",
    "deadline_text": "deadline iborasi yoki null",
    "priority": "high|medium|low",
    "amount": 500000,
    "currency": "UZS|USD|EUR"
  }
]
"""


TASK_EXTRACTION_USER_PROMPT = """
Quyidagi yig'ilish transkripsiyasidan barcha topshiriqlarni ajrat:

---
{transcript}
---

Eslatma: Faqat JSON massiv qaytarilsin.
"""


class LLMService:

    def __init__(self) -> None:
        self.client = Groq(api_key=settings.GROQ_API_KEY)
        self.model = "llama-3.3-70b-versatile"
        self.max_tokens = 4096
        self.temperature = 0.1    # Past temperature → aniqroq, kamroq kreativ

    async def extract_tasks(
        self,
        transcript: str,
    ) -> list[dict[str, Any]]:
        if not transcript or not transcript.strip():
            logger.warning("Bo'sh transcript keldi")
            return []

        logger.info(
            f"Task extraction boshlandi | "
            f"Transcript uzunligi: {len(transcript)} belgi"
        )
        start = time.time()

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": TASK_EXTRACTION_SYSTEM_PROMPT,
                    },
                    {
                        "role": "user",
                        "content": TASK_EXTRACTION_USER_PROMPT.format(
                            transcript=transcript
                        ),
                    },
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                response_format={"type": "json_object"},
            )

            elapsed = time.time() - start
            raw_content = response.choices[0].message.content or "[]"

            logger.info(
                f"LLM javob olindi: {elapsed:.2f}s | "
                f"Tokens: {response.usage.total_tokens}"
            )

            tasks = self._parse_response(raw_content)

            logger.info(
                f"Task extraction tugadi | "
                f"Ajratilgan tasklar: {len(tasks)}"
            )

            return tasks

        except Exception as e:
            logger.error(f"LLM xatosi: {str(e)}")
            return []

    def _parse_response(
        self,
        raw_content: str,
    ) -> list[dict[str, Any]]:
        try:
            raw_content = raw_content.strip()

            # JSON array yoki object bo'lishi mumkin
            parsed = json.loads(raw_content)

            # { "tasks": [...] } formatida kelishi mumkin
            if isinstance(parsed, dict):
                for key in ("tasks", "topshiriqlar", "items", "data"):
                    if key in parsed and isinstance(parsed[key], list):
                        parsed = parsed[key]
                        break

            if not isinstance(parsed, list):
                logger.warning(f"Kutilmagan format: {type(parsed)}")
                return []

            validated = []
            for item in parsed:
                task = self._validate_task(item)
                if task:
                    validated.append(task)

            return validated

        except json.JSONDecodeError as e:
            logger.error(f"JSON parse xatosi: {e} | Content: {raw_content[:200]}")
            return []

    def _validate_task(
        self,
        item: dict,
    ) -> dict | None:
        if not isinstance(item, dict):
            return None

        title = item.get("title", "").strip()
        if not title:
            return None

        task_type = item.get("task_type", "task")
        if task_type not in {"task", "payment", "debt", "general"}:
            task_type = "task"

        priority = item.get("priority", "medium")
        if priority not in {"high", "medium", "low"}:
            # Matndan priority aniqlash
            priority = detect_priority_from_text(
                item.get("description", "") or title
            )

        currency = item.get("currency", "UZS")
        if currency not in {"UZS", "USD", "EUR"}:
            currency = "UZS"

        amount = item.get("amount")
        if amount is not None:
            try:
                amount = float(amount)
                if amount < 0:
                    amount = None
            except (ValueError, TypeError):
                amount = None

        return {
            "title":              title[:500],
            "description":        (item.get("description") or "").strip()[:5000],
            "task_type":          task_type,
            "assigned_to_name":   item.get("assigned_to_name"),
            "deadline_text":      item.get("deadline_text"),
            "priority":           priority,
            "amount":             amount,
            "currency":           currency,
        }

    async def process_tasks_with_employees(
        self,
        raw_tasks: list[dict[str, Any]],
        employees: list,
    ) -> list[dict[str, Any]]:
        # Barcha ismlarni bir vaqtda match qilish
        names = [t.get("assigned_to_name") for t in raw_tasks]
        matched = bulk_match_employees(
            names=[n for n in names if n],
            employees=employees,
        )

        processed = []
        for i, task in enumerate(raw_tasks):
            name = task.get("assigned_to_name")
            employee = matched.get(name) if name else None

            deadline = parse_deadline_text(task.get("deadline_text"))

            processed.append({
                "title":        task["title"],
                "description":  task["description"],
                "task_type":    task["task_type"],
                "priority":     task["priority"],
                "amount":       task["amount"],
                "currency":     task["currency"],
                "assigned_to":  employee.id if employee else None,
                "deadline":     deadline,
                "order_index":  i,
                "status":       "pending",
                "is_edited":    False,
            })

        return processed

    async def summarize_meeting(
        self,
        transcript: str,
    ) -> str:
        if not transcript:
            return ""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Siz yig'ilish transkripsiyasini qisqa "
                            "xulosa qilib beruvchi assistantsiz. "
                            "O'zbek tilida 3-5 jumlada xulosa yoz."
                        ),
                    },
                    {
                        "role": "user",
                        "content": transcript,
                    },
                ],
                max_tokens=500,
                temperature=0.3,
            )
            return response.choices[0].message.content or ""

        except Exception as e:
            logger.error(f"Summarize xatosi: {e}")
            return ""


# Global instance
llm_service = LLMService()
