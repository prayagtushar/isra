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
    return normalize(expected) == normalize(startup_name)


def load_golden(path: Path = GOLDEN_PATH) -> list[GoldenItem]:
    items: list[GoldenItem] = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        obj = json.loads(line)
        items.append(GoldenItem(question=obj["question"], expected=obj["expected"]))
    return items
