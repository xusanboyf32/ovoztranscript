from datetime import datetime, timezone, timedelta
from typing import Optional
import re

import dateparser


TASHKENT_TZ_OFFSET = timezone(timedelta(hours=5))

DEADLINE_KEYWORDS_HIGH = {
    "bugun", "today", "сегодня",
    "hozir", "now", "сейчас",
    "zudlik", "urgent", "срочно",
    "shoshilinch",
}

DEADLINE_KEYWORDS_LOW = {
    "keyinroq", "later", "позже",
    "vaqt bo'lganda", "when possible",
    "asta-sekin", "slowly",
    "bo'sh vaqtda",
}

DATEPARSER_SETTINGS = {
    "LANGUAGES": ["uz", "ru", "en"],
    "PREFER_DATES_FROM": "future",
    "RETURN_AS_TIMEZONE_AWARE": True,
    "PREFER_DAY_OF_MONTH": "first",
    "TIMEZONE": "Asia/Tashkent",
    "TO_TIMEZONE": "UTC",
    "PARSERS": [
        "absolute-time",
        "relative-time",
        "custom-formats",
    ],
}

CUSTOM_DATE_FORMATS = [
    "%d-%m-%Y",
    "%d.%m.%Y",
    "%d/%m/%Y",
    "%d-%m-%Y %H:%M",
    "%d.%m.%Y %H:%M",
    "%Y-%m-%d",
    "%Y-%m-%dT%H:%M:%S",
]


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def now_tashkent() -> datetime:
    return datetime.now(TASHKENT_TZ_OFFSET)


def to_tashkent(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(TASHKENT_TZ_OFFSET)


def to_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=TASHKENT_TZ_OFFSET)
    return dt.astimezone(timezone.utc)


def format_deadline(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    tashkent_dt = to_tashkent(dt)
    months_uz = {
        1: "yanvar", 2: "fevral", 3: "mart",
        4: "aprel", 5: "may", 6: "iyun",
        7: "iyul", 8: "avgust", 9: "sentabr",
        10: "oktabr", 11: "noyabr", 12: "dekabr",
    }
    month_name = months_uz[tashkent_dt.month]
    return (
        f"{tashkent_dt.day}-{month_name} "
        f"{tashkent_dt.year}, "
        f"{tashkent_dt.hour:02d}:{tashkent_dt.minute:02d}"
    )


def parse_deadline_text(text: str | None) -> datetime | None:
    if not text:
        return None

    text = text.strip().lower()

    # Aniq pattern lar avval tekshiriladi
    relative_patterns = {
        r"(\d+)\s*kun(dan)?\s*(keyin|o'tgach|so'ng)": lambda m: (
            now_utc() + timedelta(days=int(m.group(1)))
        ),
        r"(\d+)\s*soat(dan)?\s*(keyin|o'tgach|so'ng)": lambda m: (
            now_utc() + timedelta(hours=int(m.group(1)))
        ),
        r"(\d+)\s*hafta(dan)?\s*(keyin|o'tgach|so'ng)": lambda m: (
            now_utc() + timedelta(weeks=int(m.group(1)))
        ),
        r"(\d+)\s*oy(dan)?\s*(keyin|o'tgach|so'ng)": lambda m: (
            now_utc() + timedelta(days=int(m.group(1)) * 30)
        ),
        r"erta(ga)?": lambda m: (
            now_utc() + timedelta(days=1)
        ),
        r"ind?inga?": lambda m: (
            now_utc() + timedelta(days=2)
        ),
        r"bugun": lambda m: now_utc(),
    }

    for pattern, handler in relative_patterns.items():
        match = re.search(pattern, text)
        if match:
            result = handler(match)
            return result

    # Hafta kunlari
    weekdays_uz = {
        "dushanba": 0,
        "seshanba": 1,
        "chorshanba": 2,
        "payshanba": 3,
        "juma": 4,
        "shanba": 5,
        "yakshanba": 6,
    }
    for day_name, weekday in weekdays_uz.items():
        if day_name in text:
            today = now_utc()
            days_ahead = weekday - today.weekday()
            if days_ahead <= 0:
                days_ahead += 7
            return today + timedelta(days=days_ahead)

    # dateparser bilan universal parse
    try:
        parsed = dateparser.parse(text, settings=DATEPARSER_SETTINGS)
        if parsed:
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed
    except Exception:
        pass

    # Custom formatlar
    for fmt in CUSTOM_DATE_FORMATS:
        try:
            parsed = datetime.strptime(text, fmt)
            return parsed.replace(tzinfo=TASHKENT_TZ_OFFSET).astimezone(
                timezone.utc
            )
        except ValueError:
            continue

    return None


def is_overdue(deadline: datetime | None) -> bool:
    if deadline is None:
        return False
    if deadline.tzinfo is None:
        deadline = deadline.replace(tzinfo=timezone.utc)
    return deadline < now_utc()


def deadline_status(deadline: datetime | None) -> str:
    if deadline is None:
        return "no_deadline"
    if deadline.tzinfo is None:
        deadline = deadline.replace(tzinfo=timezone.utc)
    now = now_utc()
    diff = deadline - now
    if diff.total_seconds() < 0:
        return "overdue"
    elif diff.total_seconds() < 86400:
        return "today"
    elif diff.total_seconds() < 86400 * 3:
        return "upcoming"
    else:
        return "future"


def detect_priority_from_text(text: str) -> str:
    text_lower = text.lower()
    for keyword in DEADLINE_KEYWORDS_HIGH:
        if keyword in text_lower:
            return "high"
    for keyword in DEADLINE_KEYWORDS_LOW:
        if keyword in text_lower:
            return "low"
    return "medium"


def format_duration(seconds: int | None) -> str | None:
    if seconds is None:
        return None
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def get_date_range(
    days_back: int = 30,
) -> tuple[datetime, datetime]:
    end = now_utc()
    start = end - timedelta(days=days_back)
    return start, end
