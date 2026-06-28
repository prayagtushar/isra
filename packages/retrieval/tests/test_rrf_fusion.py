from isra_retrieval.models import Chunk
from isra_retrieval.rrf_fusion import rrf_fusion

def _chunk(chunk_id: int) -> Chunk:
    return Chunk(
        id=chunk_id,
        startup_id=1,
        startup_name="TestCo",
        chunk_index=0,
        text="...",
        source_url="https://example.com",
    )

def test_rrf_fusion_with_empty_inputs():
    assert rrf_fusion([], [], top_k=5) == []

def test_rrf_fusion_prefers_chunks_in_both_lists():
    vector_results = [_chunk(10), _chunk(20), _chunk(30)]
    keyword_results = [_chunk(20), _chunk(10), _chunk(40)]

    fused = rrf_fusion(vector_results, keyword_results, top_k=2)

    assert [c.id for c in fused] == [10, 20]
    for chunk in fused:
        assert isinstance(chunk.score, float)
        assert chunk.score > 0

def test_rrf_fusion_top_k_truncates():
    vector_results = [_chunk(1)]
    keyword_results = [_chunk(2)]

    assert len(rrf_fusion(vector_results, keyword_results, top_k=1)) == 1
