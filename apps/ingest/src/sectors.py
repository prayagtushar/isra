"""One vocabulary for sectors, across sources that disagree about it.

Wikipedia infoboxes say "Financial technology". Y Combinator says "Fintech".
Both end up in the same corpus, and nothing reconciled them, so the /startups
filter offered about sixty chips for 111 companies -- including "E-Commerce"
twice, and "Medical Device" next to "Medical Devices". Filtering on one of a
pair silently hid the companies filed under the other.

Two rules, and the second matters more than the first:

  * Merge only spelling. Different words for the same sector collapse; different
    sectors never do. "Financial Services" and "Financial Technology" stay
    apart, because a bank is not a payments startup and a tidier filter is not
    worth losing that.
  * Stay a fixup list, not an allowlist. A sector nobody anticipated passes
    through with its casing corrected, rather than being dropped or bucketed
    into "Other" -- the corpus grows by scraping, so the unanticipated case is
    the normal one.
"""

from typing import Iterable, Optional

# Spellings that mean the same sector, mapped onto the form to keep. Keys are
# compared case-insensitively with punctuation and spacing removed, so
# "E-commerce", "e commerce" and "ECOMMERCE" all reach the same entry.
_SYNONYMS = {
    "fintech": "Financial Technology",
    "financialtechnology": "Financial Technology",
    "ecommerce": "E-Commerce",
    "b2becommerce": "B2B E-Commerce",
    "healthtech": "Health Technology",
    "healthtechnology": "Health Technology",
    "edtech": "Educational Technology",
    "educationtechnology": "Educational Technology",
    "medicaldevice": "Medical Devices",
    "medicaldevices": "Medical Devices",
    "artificialintelligence": "Artificial Intelligence",
    "ai": "Artificial Intelligence",
    "saas": "SaaS",
    "softwareasaservice": "SaaS",
    "logistics": "Supply Chain and Logistics",
    "supplychainandlogistics": "Supply Chain and Logistics",
}

# Words whose casing Title Case gets wrong.
_CASING = {
    "ai": "AI",
    "gpt": "GPT",
    "b2b": "B2B",
    "b2c": "B2C",
    "saas": "SaaS",
    "iot": "IoT",
    "ar": "AR",
    "vr": "VR",
    "api": "API",
    "hr": "HR",
    "and": "and",
    "of": "of",
    "as": "as",
    "a": "a",
}

def _key(value: str) -> str:
    """Collapse a sector to its comparison key: letters and digits only."""
    return "".join(char for char in value.lower() if char.isalnum())

def _cap(piece: str) -> str:
    """Capitalize one word, leaving short all-caps tokens as acronyms.

    capitalize() alone would turn a scraped "HOSPITALITY" into "Hospitality"
    (wanted) and an acronym like "DPIIT" into "Dpiit" (not wanted). Length is
    the only signal available without an exhaustive list, and sector names are
    words while sector acronyms are short.
    """
    if piece.isupper() and len(piece) <= 5:
        return piece
    if "-" in piece:
        return "-".join(part.capitalize() for part in piece.split("-"))
    return piece.capitalize()

def _titlecase(value: str) -> str:
    """Title-case a sector without mangling acronyms or joining words.

    Each space- and slash-delimited piece is cased on its own, so "e-commerce"
    and "AI / GPT" keep their punctuation.
    """
    words = []
    for index, word in enumerate(value.split()):
        pieces = []
        for piece in word.replace("/", " / ").split(" "):
            if not piece:
                continue
            lowered = piece.lower()
            if lowered in _CASING and not (index == 0 and lowered in ("and", "of", "as", "a")):
                pieces.append(_CASING[lowered])
            else:
                pieces.append(_cap(piece))
        words.append(" ".join(pieces))
    return " ".join(words)

def normalize_sector(value: str) -> str:
    """Canonical form of a single sector name."""
    collapsed = " ".join(value.split())
    canonical = _SYNONYMS.get(_key(collapsed))
    return canonical if canonical else _titlecase(collapsed)

def normalize_sectors(values: Iterable[Optional[str]]) -> list[str]:
    """Canonicalize, drop blanks and duplicates, and sort.

    Sorted because the filter renders in this order, and an unstable order
    would reshuffle the chips on every ingest for no reason a reader could see.
    """
    seen: dict[str, str] = {}
    for value in values or []:
        if not value or not value.strip():
            continue
        canonical = normalize_sector(value)
        seen.setdefault(_key(canonical), canonical)
    return sorted(seen.values())
