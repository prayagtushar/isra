"""One sector vocabulary across sources that disagree. Merge spelling only, never distinct sectors."""

from typing import Iterable, Optional

# Spellings that mean one sector. Keys compare case- and punctuation-insensitively.
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
    # The two sources describe the same sector at different lengths.
    "socialnetwork": "Social Network",
    "socialnetworkservice": "Social Network",
    "socialnetworkingservice": "Social Network",
    "informationtechnology": "Information Technology",
    "informationaltechnology": "Information Technology",  # as spelled on the source page
    "healthcare": "Healthcare",
    "healthcareservices": "Healthcare",
    "paymentgateway": "Payments",
    "payments": "Payments",
    "humanresources": "Human Resources",
    "recruitingandtalent": "Human Resources",
    "jobandcareerservices": "Human Resources",
    "foodandbeverage": "Food and Beverage",
    "foodindustry": "Food and Beverage",
    "restaurants": "Food and Beverage",
    "realestate": "Real Estate",
    "housingandrealestate": "Real Estate",
    "realestateandconstruction": "Real Estate",
    "manufacturing": "Manufacturing",
    "manufacturingandrobotics": "Manufacturing",
    "softwareandservices": "Software and Services",
    "softwarecompany": "Software and Services",
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
    """Capitalize one word, leaving short all-caps tokens as acronyms."""
    if piece.isupper() and len(piece) <= 5:
        return piece
    if "-" in piece:
        return "-".join(part.capitalize() for part in piece.split("-"))
    return piece.capitalize()

def _titlecase(value: str) -> str:
    """Title-case a sector without mangling acronyms or joining words."""
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
    """Canonicalize, drop blanks and duplicates, and sort so the chips render in a stable order."""
    seen: dict[str, str] = {}
    for value in values or []:
        if not value or not value.strip():
            continue
        canonical = normalize_sector(value)
        seen.setdefault(_key(canonical), canonical)
    return sorted(seen.values())
