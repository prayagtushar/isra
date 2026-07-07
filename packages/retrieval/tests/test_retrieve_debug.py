from unittest.mock import patch

import numpy as np

from isra_retrieval.models import Chunk
from isra_retrieval.pipeline import retrieve_debug


def _chunk(chunk_id: int, score: float = 0.5) -> Chunk:
    return Chunk(
        id=chunk_id,
        startup_id=1,
        startup_name="TestCo",
        chunk_index=0,
        text="...",
        source_url="https://example.com",
        score=score,
    )


def test_retrieve_debug_vector_mode():
    vector_results = [_chunk(1, 0.9), _chunk(2, 0.8)]

    with patch("isra_retrieval.pipeline.embed_query", return_value=np.zeros(384)):
        with patch("isra_retrieval.pipeline.vector_search", return_value=vector_results):
            trace = retrieve_debug("query", top_k=2, mode="vector")

    assert trace["mode"] == "vector"
    assert len(trace["stages"]) == 1
    assert trace["stages"][0]["name"] == "vector"
    assert [c.id for c in trace["stages"][0]["results"]] == [1, 2]
    assert trace["latency_ms"] >= 0


def test_retrieve_debug_hybrid_mode():
    vector_results = [_chunk(1, 0.9), _chunk(2, 0.8)]
    keyword_results = [_chunk(3, 0.7)]

    def _fake_fusion(v, k, top_k):
        return [_chunk(1, 0.33), _chunk(3, 0.25)]

    with patch("isra_retrieval.pipeline.embed_query", return_value=np.zeros(384)):
        with patch("isra_retrieval.pipeline.vector_search", return_value=vector_results):
            with patch("isra_retrieval.pipeline.search_keyword", return_value=keyword_results):
                with patch("isra_retrieval.pipeline.rrf_fusion", side_effect=_fake_fusion):
                    trace = retrieve_debug("query", top_k=2, mode="hybrid")

    assert trace["mode"] == "hybrid"
    assert [s["name"] for s in trace["stages"]] == ["vector", "keyword", "fusion"]


def test_retrieve_debug_hybrid_rerank_mode():
    vector_results = [_chunk(1, 0.9)]
    keyword_results = [_chunk(2, 0.7)]

    def _fake_fusion(v, k, top_k):
        return [_chunk(1, 0.33), _chunk(2, 0.25)]

    def _fake_rerank(query, chunks, top_k, rerank_top_k=20):
        return [_chunk(2, 0.99), _chunk(1, 0.95)]

    with patch("isra_retrieval.pipeline.embed_query", return_value=np.zeros(384)):
        with patch("isra_retrieval.pipeline.vector_search", return_value=vector_results):
            with patch("isra_retrieval.pipeline.search_keyword", return_value=keyword_results):
                with patch("isra_retrieval.pipeline.rrf_fusion", side_effect=_fake_fusion):
                    with patch("isra_retrieval.pipeline.rerank", side_effect=_fake_rerank):
                        trace = retrieve_debug("query", top_k=2, mode="hybrid+rerank")

    assert trace["mode"] == "hybrid+rerank"
    assert [s["name"] for s in trace["stages"]] == ["vector", "keyword", "fusion", "rerank"]
    assert trace["stages"][3]["results"][0].id == 2


def test_retrieve_debug_hybrid_rerank_passes_rerank_top_k():
    vector_results = [_chunk(1, 0.9)]
    keyword_results = [_chunk(2, 0.7)]

    def _fake_fusion(v, k, top_k):
        return [_chunk(i, 0.1) for i in range(50)]

    captured = {}

    def _fake_rerank(query, chunks, top_k, rerank_top_k=20):
        captured["rerank_top_k"] = rerank_top_k
        captured["chunks_len"] = len(chunks)
        return chunks[:top_k]

    with patch("isra_retrieval.pipeline.embed_query", return_value=np.zeros(384)):
        with patch("isra_retrieval.pipeline.vector_search", return_value=vector_results):
            with patch("isra_retrieval.pipeline.search_keyword", return_value=keyword_results):
                with patch("isra_retrieval.pipeline.rrf_fusion", side_effect=_fake_fusion):
                    with patch("isra_retrieval.pipeline.rerank", side_effect=_fake_rerank):
                        retrieve_debug("query", top_k=5, mode="hybrid+rerank", rerank_top_k=15)

    assert captured["rerank_top_k"] == 15
    assert captured["chunks_len"] == 50
