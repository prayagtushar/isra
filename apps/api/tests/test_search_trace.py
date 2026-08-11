"""POST /search/trace: one event per stage, errors reported, and the rate limit shared with /search."""

import json

import pytest
from fastapi.testclient import TestClient

from src.main import app


def _events(body: str) -> list[dict]:
    return [
        json.loads(line[len("data:") :].strip())
        for line in body.splitlines()
        if line.startswith("data:")
    ]


def _stage(name: str, elapsed: float, total: int = 3):
    return {
        "name": name,
        "elapsed_ms": elapsed,
        "total": total,
        "results": [
            type(
                "C",
                (),
                {
                    "id": 1,
                    "startup_name": "TestCo",
                    "chunk_index": 0,
                    "text": "...",
                    "source_url": "https://example.com",
                    "score": 0.5,
                },
            )()
        ],
    }


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def test_emits_one_event_per_stage_then_done(client, monkeypatch):
    def fake_stages(query, top_k=5, mode="hybrid+rerank"):
        yield _stage("vector", 20.0)
        yield _stage("keyword", 24.0)
        yield _stage("fusion", 25.0)
        yield _stage("rerank", 700.0)

    monkeypatch.setattr("src.main.retrieve_stages", fake_stages)

    res = client.post("/search/trace", json={"query": "payments", "top_k": 5})
    assert res.status_code == 200
    assert res.headers["content-type"].startswith("text/event-stream")

    events = _events(res.text)
    assert [e.get("name") for e in events if e["type"] == "stage"] == [
        "vector",
        "keyword",
        "fusion",
        "rerank",
    ]
    assert events[-1] == {
        "type": "done",
        "stages": ["vector", "keyword", "fusion", "rerank"],
    }


def test_each_event_carries_the_timing_and_the_candidate_count(client, monkeypatch):
    """Elapsed time justifies streaming; the total stops the last column reading as a loss."""

    def fake_stages(query, top_k=5, mode="hybrid+rerank"):
        yield _stage("vector", 21.456, total=100)

    monkeypatch.setattr("src.main.retrieve_stages", fake_stages)

    stage = _events(client.post("/search/trace", json={"query": "q"}).text)[0]
    assert stage["elapsed_ms"] == 21.5  # rounded, not truncated to an int
    assert stage["total"] == 100
    assert stage["results"][0]["startup_name"] == "TestCo"


def test_a_failure_midway_is_reported_rather_than_silently_truncating(client, monkeypatch):
    """Three stages then a dropped connection is indistinguishable from a three-stage mode."""

    def fake_stages(query, top_k=5, mode="hybrid+rerank"):
        yield _stage("vector", 20.0)
        raise RuntimeError("reranker died")

    monkeypatch.setattr("src.main.retrieve_stages", fake_stages)

    events = _events(client.post("/search/trace", json={"query": "q"}).text)
    assert events[0]["type"] == "stage"
    assert events[-1]["type"] == "error"
    assert "reranker died" in events[-1]["message"]


@pytest.mark.parametrize(
    "body",
    [
        {"query": ""},
        {"query": "x" * 601},
        {"query": "payments", "top_k": 0},
        {"query": "payments", "top_k": 50},
    ],
)
def test_rejects_requests_the_reranker_should_not_be_asked_to_serve(client, body):
    """Both search endpoints are public and both run the cross-encoder, so bound the request."""
    assert client.post("/search/trace", json=body).status_code == 422


def test_shares_the_search_rate_limit():
    """Same cross-encoder as /search, so it must not get its own separate budget."""
    from src.rate_limit import rule_for_path

    assert rule_for_path("/search/trace") == rule_for_path("/search")
    assert rule_for_path("/search") is not None
