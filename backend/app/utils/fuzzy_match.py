import re
import unicodedata
from difflib import SequenceMatcher
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.user import User


# --- Normalizatsiya ---

def normalize_text(text: str) -> str:
    text = text.strip().lower()
    # Unicode normalizatsiya — harflar bir xil ko'rinishda
    text = unicodedata.normalize("NFKD", text)
    # Ortiqcha bo'shliqlarni olib tashlash
    text = re.sub(r"\s+", " ", text)
    return text


def transliterate_uz(text: str) -> str:
    # O'zbek lotin ↔ kirill o'girish
    latin_to_cyrillic = {
        "a": "а", "b": "б", "d": "д", "e": "е",
        "f": "ф", "g": "г", "h": "ҳ", "i": "и",
        "j": "ж", "k": "к", "l": "л", "m": "м",
        "n": "н", "o": "о", "p": "п", "q": "қ",
        "r": "р", "s": "с", "t": "т", "u": "у",
        "v": "в", "x": "х", "y": "й", "z": "з",
        "o'": "ў", "g'": "ғ", "sh": "ш", "ch": "ч",
        "ng": "нг", "ts": "тс",
    }
    result = text.lower()
    for latin, cyrillic in sorted(
        latin_to_cyrillic.items(),
        key=lambda x: -len(x[0])
    ):
        result = result.replace(latin, cyrillic)
    return result


def extract_name_parts(full_name: str) -> list[str]:
    normalized = normalize_text(full_name)
    parts = normalized.split()
    result = list(parts)
    # Qisqartmalar qo'shish — "Sardor Toshmatov" → ["sardor", "toshmatov", "s.t"]
    if len(parts) >= 2:
        initials = "".join(p[0] for p in parts)
        result.append(initials)
        result.append(f"{parts[0][0]}.{parts[1]}")
    return result


# --- Moslik hisoblash ---

def similarity_score(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()


def name_match_score(
    query: str,
    full_name: str,
) -> float:
    query_norm = normalize_text(query)
    name_norm = normalize_text(full_name)
    name_parts = extract_name_parts(full_name)

    scores = []

    # To'liq mos kelish
    if query_norm == name_norm:
        return 1.0

    # Qism sifatida mavjud
    if query_norm in name_norm:
        scores.append(0.95)

    # Ism qismlari bilan taqqoslash
    for part in name_parts:
        if query_norm == part:
            scores.append(0.90)
        elif query_norm in part or part in query_norm:
            scores.append(0.80)
        else:
            score = similarity_score(query_norm, part)
            scores.append(score * 0.75)

    # Transliteratsiya bilan taqqoslash
    query_cyrillic = transliterate_uz(query_norm)
    name_cyrillic = transliterate_uz(name_norm)
    if query_cyrillic in name_cyrillic:
        scores.append(0.85)
    else:
        scores.append(similarity_score(query_cyrillic, name_cyrillic) * 0.70)

    return max(scores) if scores else 0.0


# --- Asosiy funksiyalar ---

def find_employee_by_name(
    name: str | None,
    employees: list["User"],
    threshold: float = 0.65,
) -> "User | None":
    if not name or not employees:
        return None

    name = normalize_text(name)
    if not name:
        return None

    best_match: "User | None" = None
    best_score: float = 0.0

    for employee in employees:
        score = name_match_score(name, employee.full_name)
        if score > best_score:
            best_score = score
            best_match = employee

    if best_score >= threshold:
        return best_match

    return None


def find_employees_by_name(
    name: str | None,
    employees: list["User"],
    threshold: float = 0.65,
    limit: int = 3,
) -> list[tuple["User", float]]:
    if not name or not employees:
        return []

    name = normalize_text(name)
    results: list[tuple["User", float]] = []

    for employee in employees:
        score = name_match_score(name, employee.full_name)
        if score >= threshold:
            results.append((employee, score))

    results.sort(key=lambda x: x[1], reverse=True)
    return results[:limit]


def bulk_match_employees(
    names: list[str | None],
    employees: list["User"],
    threshold: float = 0.65,
) -> dict[str, "User | None"]:
    results: dict[str, "User | None"] = {}
    for name in names:
        if name:
            results[name] = find_employee_by_name(
                name, employees, threshold
            )
    return results
