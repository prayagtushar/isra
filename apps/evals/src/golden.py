import json
import re
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path

GOLDEN_PATH = Path(__file__).parent / "golden.jsonl"

_NON_ALNUM = re.compile(r"[^a-z0-9]")


@dataclass(frozen=True)
class GoldenItem:
    question: str
    # Startup identifiers that count as correct. Empty means the corpus cannot
    # answer the question at all — the right behaviour is to abstain.
    expected: tuple[str, ...] = field(default=())
    category: str = "direct"
    # "any": retrieving one acceptable answer is a hit (a question with several
    # equally valid answers). "all": every entity must be retrieved (multi-hop).
    match: str = "any"

    @property
    def answerable(self) -> bool:
        return bool(self.expected)


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


def matched_expected(item: GoldenItem, startup_names: Sequence[str]) -> set[str]:
    """Which of the item's expected entities appear among the retrieved names."""
    return {
        expected
        for expected in item.expected
        if any(matches(expected, name) for name in startup_names)
    }


def _as_tuple(raw) -> tuple[str, ...]:
    if raw is None:
        return ()
    if isinstance(raw, str):
        return (raw,)
    return tuple(raw)


def load_golden(path: Path = GOLDEN_PATH) -> list[GoldenItem]:
    items: list[GoldenItem] = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        obj = json.loads(line)
        items.append(
            GoldenItem(
                question=obj["question"],
                expected=_as_tuple(obj.get("expected")),
                category=obj.get("category", "direct"),
                match=obj.get("match", "any"),
            )
        )
    return items
