"""The streaming pipeline: stage order, timing, and that nothing runs after a consumer stops."""

from contextlib import contextmanager
from unittest.mock import patch

import numpy as np
import pytest

from isra_retrieval.models import Chunk
from isra_retrieval.pipeline import TRACE_STAGE_LIMIT, retrieve_stages


@pytest.fixture(autouse=True)
def no_database():
    """Stub the connection the pipeline opens, which load_dotenv() makes the deployed database."""

    @contextmanager
    def _fake_conn():
        yield object()

    with patch("isra_retrieval.pipeline.get_conn", _fake_conn):
        yield


def _chunk(chunk_id: int, score: float = 0.5) -> Chunk:
    return Chunk(
        id=chunk_id,
        startup_id=1,
        startup_name=f"Co{chunk_id}",
        chunk_index=0,
        text="...",
        source_url="https://example.com",
        score=score,
    )


@contextmanager
def _patched(vector, keyword, fused, reranked):
    with (
        patch("isra_retrieval.pipeline.embed_query", return_value=np.zeros(384)),
        patch("isra_retrieval.pipeline.vector_search", return_value=vector),
        patch("isra_retrieval.pipeline.search_keyword", return_value=keyword),
        patch("isra_retrieval.pipeline.rrf_fusion", return_value=fused),
        patch("isra_retrieval.pipeline.rerank", return_value=reranked) as mock_rerank,
    ):
        yield mock_rerank


def test_stages_arrive_in_pipeline_order():
    with _patched([_chunk(1)], [_chunk(2)], [_chunk(1), _chunk(2)], [_chunk(2)]):
        names = [e["name"] for e in retrieve_stages("q", top_k=5, mode="hybrid+rerank")]

    assert names == ["vector", "keyword", "fusion", "rerank"]


def test_vector_mode_yields_only_its_own_stage():
    with _patched([_chunk(1)], [], [], []):
        names = [e["name"] for e in retrieve_stages("q", mode="vector")]
    assert names == ["vector"]


def test_hybrid_mode_stops_before_the_reranker():
    with _patched([_chunk(1)], [_chunk(2)], [_chunk(1)], [_chunk(1)]) as mock_rerank:
        names = [e["name"] for e in retrieve_stages("q", mode="hybrid")]

    assert names == ["vector", "keyword", "fusion"]
    mock_rerank.assert_not_called()


def test_the_reranker_does_not_run_until_its_stage_is_requested():
    """The reason for streaming: pulling three stages must not have paid for the fourth."""
    with _patched([_chunk(1)], [_chunk(2)], [_chunk(1)], [_chunk(1)]) as mock_rerank:
        stages = retrieve_stages("q", mode="hybrid+rerank")
        for _ in range(3):
            next(stages)
        assert mock_rerank.call_count == 0

        next(stages)
        assert mock_rerank.call_count == 1


def test_a_consumer_that_stops_early_stops_the_pipeline():
    """A closed generator must not go on to rerank for a client that has disconnected."""
    with _patched([_chunk(1)], [_chunk(2)], [_chunk(1)], [_chunk(1)]) as mock_rerank:
        stages = retrieve_stages("q", mode="hybrid+rerank")
        next(stages)
        stages.close()

    mock_rerank.assert_not_called()


def test_each_stage_reports_how_many_candidates_it_produced():
    """results is truncated for display, so without the total the funnel reads backwards."""
    vector = [_chunk(i) for i in range(50)]
    keyword = [_chunk(i) for i in range(12)]
    fused = [_chunk(i) for i in range(50)]
    reranked = [_chunk(i) for i in range(5)]

    with _patched(vector, keyword, fused, reranked):
        events = {e["name"]: e for e in retrieve_stages("q", top_k=5, mode="hybrid+rerank")}

    assert events["vector"]["total"] == 50
    assert events["keyword"]["total"] == 12
    assert events["rerank"]["total"] == 5
    # And the payload itself stays small.
    assert len(events["vector"]["results"]) == TRACE_STAGE_LIMIT


def test_elapsed_time_never_goes_backwards():
    with _patched([_chunk(1)], [_chunk(2)], [_chunk(1)], [_chunk(1)]):
        elapsed = [e["elapsed_ms"] for e in retrieve_stages("q", mode="hybrid+rerank")]

    assert elapsed == sorted(elapsed)
    assert elapsed[0] >= 0


def test_an_unknown_mode_is_rejected_before_any_work():
    with pytest.raises(ValueError, match="not supported"):
        list(retrieve_stages("q", mode="semantic"))
