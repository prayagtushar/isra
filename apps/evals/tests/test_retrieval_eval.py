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

def test_rank_one_gives_perfect_scores():
    items = [GoldenItem("q", "paytm")]
    retrieve = make_retrieve({("q", "vector"): ["Paytm", "Zomato"]})
    (res,) = evaluate_modes(items, ["vector"], top_k=5, retrieve=retrieve)
    assert res.hit_at_k == 1.0
    assert res.mrr == 1.0
    assert res.n == 1

def test_rank_three_gives_reciprocal_third():
    items = [GoldenItem("q", "paytm")]
    retrieve = make_retrieve({("q", "vector"): ["A", "B", "Paytm"]})
    (res,) = evaluate_modes(items, ["vector"], top_k=5, retrieve=retrieve)
    assert res.hit_at_k == 1.0
    assert abs(res.mrr - (1 / 3)) < 1e-9

def test_absent_gives_zero():
    items = [GoldenItem("q", "paytm")]
    retrieve = make_retrieve({("q", "vector"): ["A", "B", "C"]})
    (res,) = evaluate_modes(items, ["vector"], top_k=5, retrieve=retrieve)
    assert res.hit_at_k == 0.0
    assert res.mrr == 0.0

def test_hit_at_k_excludes_beyond_k():
    items = [GoldenItem("q", "paytm")]
    retrieve = make_retrieve({("q", "vector"): ["A", "B", "C", "Paytm"]})
    (res,) = evaluate_modes(items, ["vector"], top_k=3, retrieve=retrieve)
    assert res.hit_at_k == 0.0  
    assert res.mrr == 0.0
