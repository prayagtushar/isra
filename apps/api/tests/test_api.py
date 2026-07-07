import json
from contextlib import contextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)

def _make_chunk(chunk_id, text="text", score=0.9):
    from isra_retrieval.models import Chunk

    return Chunk(
        id=chunk_id,
        startup_id=1,
        startup_name="TestCo",
        chunk_index=0,
        text=text,
        source_url="https://example.com",
        score=score,
    )

@contextmanager
def _mock_conn():
    with patch("src.main.get_conn") as mock_get_conn:
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cur)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        mock_get_conn.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_get_conn.return_value.__exit__ = MagicMock(return_value=False)
        yield mock_get_conn, mock_conn, mock_cur

def _parse_sse(response):
    lines = [line for line in response.iter_lines() if line]
    events = []
    for line in lines:
        assert line.startswith("data: ")
        events.append(json.loads(line[6:]))
    return events

def test_health_ok():
    with _mock_conn():
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_health_db_down():
    with patch("src.main.get_conn") as mock_get_conn:
        mock_get_conn.side_effect = RuntimeError("connection refused")
        response = client.get("/health")
    assert response.status_code == 503
    assert response.json()["detail"] == "Database unavailable"

def test_search():
    chunk = _make_chunk(42, text="AI startup funding", score=0.95)
    with patch("src.main.retrieve", return_value=[chunk]) as mock_retrieve:
        response = client.post("/search", json={"query": "AI funding", "top_k": 3, "mode": "hybrid"})
    assert response.status_code == 200
    data = response.json()
    assert data["query"] == "AI funding"
    assert len(data["results"]) == 1
    assert data["results"][0]["id"] == 42
    mock_retrieve.assert_called_once_with("AI funding", 3, "hybrid")

def test_search_invalid_mode():
    response = client.post("/search", json={"query": "x", "top_k": 3, "mode": "invalid"})
    assert response.status_code == 422

def test_feedback():
    with _mock_conn() as (_, conn, cur):
        response = client.post("/feedback", json={"query": "q", "answer": "a", "thumbs": True})
    assert response.status_code == 200
    cur.execute.assert_called_once()
    conn.commit.assert_called_once()

def test_chat_sse():
    chunk = _make_chunk(1, text="context", score=0.9)

    async def _fake_stream(*_args, **_kwargs):
        yield "hello"
        yield " world"

    with patch("src.main.retrieve", return_value=[chunk]):
        with patch("src.main.stream_answer", new=_fake_stream):
            response = client.post(
                "/chat",
                json={"question": "hello", "top_k": 3, "mode": "hybrid"},
            )
    assert response.status_code == 200
    events = _parse_sse(response)
    types = [e["type"] for e in events]
    assert types == ["sources", "token", "token", "done"]
    done = events[-1]
    assert done["answer"] == "hello world"

def test_chat_sse_error_on_retrieve():
    with patch("src.main.retrieve", side_effect=RuntimeError("db down")):
        response = client.post(
            "/chat",
            json={"question": "hello", "top_k": 3, "mode": "hybrid"},
        )
    assert response.status_code == 200
    events = _parse_sse(response)
    assert events[0]["type"] == "error"
    assert "db down" in events[0]["message"]

def test_chat_sse_trace():
    chunk = _make_chunk(1, text="context", score=0.9)

    async def _fake_stream(*_args, **_kwargs):
        yield "hello"

    trace = {
        "mode": "hybrid",
        "latency_ms": 12.3,
        "stages": [
            {"name": "vector", "results": [chunk]},
            {"name": "keyword", "results": [chunk]},
            {"name": "fusion", "results": [chunk]},
        ],
    }

    with patch("src.main.settings.enable_retrieval_trace", True):
        with patch("src.main.retrieve_debug", return_value=trace):
            with patch("src.main.retrieve", return_value=[chunk]):
                with patch("src.main.stream_answer", new=_fake_stream):
                    response = client.post(
                        "/chat",
                        json={"question": "hello", "top_k": 3, "mode": "hybrid", "trace": True},
                    )
    assert response.status_code == 200
    events = _parse_sse(response)
    types = [e["type"] for e in events]
    assert types == ["trace", "sources", "token", "done"]
    assert events[0]["trace"]["mode"] == "hybrid"
    assert events[0]["trace"]["stages"][0]["name"] == "vector"
