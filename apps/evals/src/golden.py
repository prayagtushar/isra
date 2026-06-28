import json
import re
from dataclasses import dataclass
from pathlib import Path

GOLDEN_PATH = Path(__file__).parent / "golden.jsonl"

_NON_ALNUM = re.compile(r"[^a-z0-9]")

@dataclass(frozen=True)
class GoldenItem:
    question: str
    expected: str

def normalize(name: str) -> str:
    return _NON_ALNUM.sub("", name.lower())

def matches(expected: str, startup_name: str) -> bool:
    expected_norm = normalize(expected)
    name_norm = normalize(startup_name)
    if expected_norm == name_norm:
        return True
    shorter, longer = sorted([expected_norm, name_norm], key=len)
    if len(shorter) >= 3 and shorter in longer:
        return True
    expected_tokens = {t for t in _NON_ALNUM.split(expected_norm) if len(t) >= 3}
    name_tokens = {t for t in _NON_ALNUM.split(name_norm) if len(t) >= 3}
    if expected_tokens and name_tokens and (expected_tokens & name_tokens):
        return True
    return False

def load_golden(path: Path = GOLDEN_PATH) -> list[GoldenItem]:
    items: list[GoldenItem] = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        obj = json.loads(line)
        items.append(GoldenItem(question=obj["question"], expected=obj["expected"]))
    return items
