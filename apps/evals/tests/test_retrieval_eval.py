from dataclasses import dataclass

from src.golden import GoldenItem
from src.retrieval_eval import evaluate_modes


@dataclass
class FakeChunk:
    startup_name: str


def make_retrieve(table):
    def _retrieve(query, top_k=5, mode="hybrid+rerank"):
        names = table[(query, mode)][:top_k]
        return [FakeChunk(startup_name=n) for n in names]

    return _retrieve


def item(question, expected, **kw):
    return GoldenItem(question=question, expected=tuple(expected), **kw)


def test_rank_one_gives_perfect_scores():
    items = [item("q", ["paytm"])]
    retrieve = make_retrieve({("q", "vector"): ["Paytm", "Zomato"]})
    (res,) = evaluate_modes(items, ["vector"], top_k=5, retrieve=retrieve)
    assert res.hit_at_k == 1.0
    assert res.mrr == 1.0
    assert res.n == 1


def test_rank_three_gives_reciprocal_third():
    items = [item("q", ["paytm"])]
    retrieve = make_retrieve({("q", "vector"): ["A", "B", "Paytm"]})
    (res,) = evaluate_modes(items, ["vector"], top_k=5, retrieve=retrieve)
    assert res.hit_at_k == 1.0
    assert abs(res.mrr - (1 / 3)) < 1e-9


def test_absent_gives_zero():
    items = [item("q", ["paytm"])]
    retrieve = make_retrieve({("q", "vector"): ["A", "B", "C"]})
    (res,) = evaluate_modes(items, ["vector"], top_k=5, retrieve=retrieve)
    assert res.hit_at_k == 0.0
    assert res.mrr == 0.0


def test_hit_at_k_excludes_beyond_k():
    items = [item("q", ["paytm"])]
    retrieve = make_retrieve({("q", "vector"): ["A", "B", "C", "Paytm"]})
    (res,) = evaluate_modes(items, ["vector"], top_k=3, retrieve=retrieve)
    assert res.hit_at_k == 0.0
    assert res.mrr == 0.0


def test_any_match_hits_when_one_acceptable_answer_is_retrieved():
    items = [item("q", ["zerodha", "groww"], match="any")]
    retrieve = make_retrieve({("q", "vector"): ["Groww", "Oyo"]})
    (res,) = evaluate_modes(items, ["vector"], top_k=5, retrieve=retrieve)
    assert res.hit_at_k == 1.0


def test_all_match_requires_every_expected_entity():
    items = [item("q", ["coindcx", "coinswitchkuber"], match="all")]
    retrieve = make_retrieve({("q", "vector"): ["CoinDCX", "Oyo"]})
    (res,) = evaluate_modes(items, ["vector"], top_k=5, retrieve=retrieve)
    assert res.hit_at_k == 0.0


def test_all_match_hits_when_every_expected_entity_is_retrieved():
    items = [item("q", ["coindcx", "coinswitchkuber"], match="all")]
    retrieve = make_retrieve(
        {("q", "vector"): ["CoinDCX", "Oyo", "CoinSwitch Kuber"]}
    )
    (res,) = evaluate_modes(items, ["vector"], top_k=5, retrieve=retrieve)
    assert res.hit_at_k == 1.0


def test_recall_gives_partial_credit_for_multi_entity_questions():
    items = [item("q", ["coindcx", "coinswitchkuber"], match="all")]
    retrieve = make_retrieve({("q", "vector"): ["CoinDCX", "Oyo"]})
    (res,) = evaluate_modes(items, ["vector"], top_k=5, retrieve=retrieve)
    assert res.recall_at_k == 0.5


def test_unanswerable_items_are_excluded_from_retrieval_metrics():
    # No document can be "correct" for a question the corpus cannot answer, so
    # scoring it would just dilute the retrieval numbers.
    items = [
        item("q", ["paytm"]),
        item("unanswerable", [], category="unanswerable"),
    ]
    retrieve = make_retrieve(
        {("q", "vector"): ["Paytm"], ("unanswerable", "vector"): ["Oyo"]}
    )
    (res,) = evaluate_modes(items, ["vector"], top_k=5, retrieve=retrieve)
    assert res.n == 1
    assert res.hit_at_k == 1.0


def test_per_category_breakdown_is_reported():
    items = [
        item("a", ["paytm"], category="direct"),
        item("b", ["zomato"], category="paraphrase"),
    ]
    retrieve = make_retrieve(
        {("a", "vector"): ["Paytm"], ("b", "vector"): ["Oyo"]}
    )
    (res,) = evaluate_modes(items, ["vector"], top_k=5, retrieve=retrieve)
    assert res.by_category["direct"].hit_at_k == 1.0
    assert res.by_category["paraphrase"].hit_at_k == 0.0
