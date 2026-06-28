from collections.abc import Callable, Sequence
from dataclasses import dataclass

from isra_retrieval import retrieve as _default_retrieve

from src.golden import GoldenItem, matches

@dataclass
class ModeResult:
    mode: str
    hit_at_k: float
    mrr: float
    n: int

def _reciprocal_rank(item: GoldenItem, chunks: Sequence) -> float:
    for rank, chunk in enumerate(chunks, start=1):
        if matches(item.expected, chunk.startup_name):
            return 1.0 / rank
    return 0.0

def evaluate_modes(
    items: Sequence[GoldenItem],
    modes: Sequence[str],
    top_k: int = 5,
    retrieve: Callable = _default_retrieve,
) -> list[ModeResult]:
    results: list[ModeResult] = []
    n = len(items)
    for mode in modes:
        reciprocal_ranks = [
            _reciprocal_rank(item, retrieve(item.question, top_k=top_k, mode=mode))
            for item in items
        ]
        hits = sum(1 for rr in reciprocal_ranks if rr > 0)
        results.append(
            ModeResult(
                mode=mode,
                hit_at_k=hits / n if n else 0.0,
                mrr=sum(reciprocal_ranks) / n if n else 0.0,
                n=n,
            )
        )
    return results
