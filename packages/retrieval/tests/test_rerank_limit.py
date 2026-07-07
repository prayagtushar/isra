from unittest.mock import patch
from isra_retrieval.models import Chunk
from isra_retrieval.reranker import rerank

def _chunk(i: int) -> Chunk:
    return Chunk(
        id=i,
        startup_id=1,
        startup_name="TestCo",
        chunk_index=0,
        text=f"chunk {i}",
        source_url="https://example.com",
        score=0.5,
    )

def test_rerank_only_processes_limited_input():
    """rerank() should score only the top rerank_top_k chunks, not all 100."""
    chunks = [_chunk(i) for i in range(100)]

    def fake_predict(pairs):
        # pairs should be limited, not 100
        assert len(pairs) <= 20, f"Expected <=20 pairs, got {len(pairs)}"
        return [0.9 - i * 0.01 for i in range(len(pairs))]

    with patch("isra_retrieval.reranker._reranker") as mock_reranker:
        mock_reranker.return_value.predict = fake_predict
        results = rerank("query", chunks, top_k=5, rerank_top_k=20)

    assert len(results) == 5
