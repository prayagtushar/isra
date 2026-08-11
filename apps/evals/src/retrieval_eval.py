from collections.abc import Callable, Sequence
from dataclasses import dataclass, field

from isra_retrieval import retrieve as _default_retrieve

from src.golden import GoldenItem, matched_expected, matches


@dataclass
class CategoryResult:
    category: str
    hit_at_k: float
    recall_at_k: float
    mrr: float
    n: int


@dataclass
class ModeResult:
    mode: str
    hit_at_k: float
    recall_at_k: float
    mrr: float
    n: int
    by_category: dict[str, CategoryResult] = field(default_factory=dict)


@dataclass
class _ItemScore:
    category: str
    hit: float
    recall: float
    reciprocal_rank: float


def _reciprocal_rank(item: GoldenItem, chunks: Sequence) -> float:
    for rank, chunk in enumerate(chunks, start=1):
        if any(matches(e, chunk.startup_name) for e in item.expected):
            return 1.0 / rank
    return 0.0


def _score_item(item: GoldenItem, chunks: Sequence) -> _ItemScore:
    names = [c.startup_name for c in chunks]
    found = matched_expected(item, names)
    recall = len(found) / len(item.expected)
    # "all" needs every expected entity present; "any" needs one.
    hit = 1.0 if (recall == 1.0 if item.match == "all" else bool(found)) else 0.0
    return _ItemScore(
        category=item.category,
        hit=hit,
        recall=recall,
        reciprocal_rank=_reciprocal_rank(item, chunks),
    )


def _aggregate(scores: Sequence[_ItemScore]) -> tuple[float, float, float, int]:
    n = len(scores)
    if not n:
        return 0.0, 0.0, 0.0, 0
    return (
        sum(s.hit for s in scores) / n,
        sum(s.recall for s in scores) / n,
        sum(s.reciprocal_rank for s in scores) / n,
        n,
    )


def evaluate_modes(
    items: Sequence[GoldenItem],
    modes: Sequence[str],
    top_k: int = 5,
    retrieve: Callable = _default_retrieve,
) -> list[ModeResult]:
    # Unanswerable items have nothing correct to retrieve; they are scored on abstention.
    answerable = [i for i in items if i.answerable]

    results: list[ModeResult] = []
    for mode in modes:
        scores = [
            _score_item(item, retrieve(item.question, top_k=top_k, mode=mode))
            for item in answerable
        ]
        hit, recall, mrr, n = _aggregate(scores)

        by_category: dict[str, CategoryResult] = {}
        for category in sorted({s.category for s in scores}):
            subset = [s for s in scores if s.category == category]
            c_hit, c_recall, c_mrr, c_n = _aggregate(subset)
            by_category[category] = CategoryResult(
                category=category,
                hit_at_k=c_hit,
                recall_at_k=c_recall,
                mrr=c_mrr,
                n=c_n,
            )

        results.append(
            ModeResult(
                mode=mode,
                hit_at_k=hit,
                recall_at_k=recall,
                mrr=mrr,
                n=n,
                by_category=by_category,
            )
        )
    return results
