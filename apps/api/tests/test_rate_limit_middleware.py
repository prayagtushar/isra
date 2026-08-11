from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.main import app
from src.rate_limit import RateLimiter, Rule


@pytest.fixture
def strict_limiter():
    """Swap in a limiter that allows two requests, then blocks."""
    limiter = RateLimiter(default=Rule(limit=2, window_seconds=60.0))
    with patch("src.main._rate_limiter", limiter):
        yield limiter


@pytest.fixture
def client():
    return TestClient(app)


def _search(client):
    return client.post("/search", json={"query": "q", "top_k": 1, "mode": "vector"})


def test_requests_under_the_limit_reach_the_handler(strict_limiter, client):
    with patch("src.main.retrieve", return_value=[]):
        assert _search(client).status_code == 200
        assert _search(client).status_code == 200


def test_request_over_the_limit_gets_429(strict_limiter, client):
    with patch("src.main.retrieve", return_value=[]):
        _search(client)
        _search(client)
        response = _search(client)
    assert response.status_code == 429


def test_rejected_request_never_reaches_the_handler(strict_limiter, client):
    # The point of the limit is to not spend CPU or LLM tokens on the request.
    with patch("src.main.retrieve", return_value=[]) as mock_retrieve:
        _search(client)
        _search(client)
        _search(client)
    assert mock_retrieve.call_count == 2


def test_rejection_sets_retry_after_header(strict_limiter, client):
    with patch("src.main.retrieve", return_value=[]):
        _search(client)
        _search(client)
        response = _search(client)
    assert int(response.headers["retry-after"]) > 0


def test_rejection_body_explains_the_limit(strict_limiter, client):
    with patch("src.main.retrieve", return_value=[]):
        _search(client)
        _search(client)
        response = _search(client)
    assert "detail" in response.json()


def test_allowed_responses_advertise_remaining_budget(strict_limiter, client):
    with patch("src.main.retrieve", return_value=[]):
        response = _search(client)
    assert response.headers["x-ratelimit-limit"] == "2"
    assert response.headers["x-ratelimit-remaining"] == "1"


def test_health_is_not_rate_limited(strict_limiter, client):
    # Cloud Run's liveness probe would otherwise trip the limit and take the instance down.
    with patch("src.main.get_conn") as mock_get_conn:
        mock_conn = MagicMock()
        mock_get_conn.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_get_conn.return_value.__exit__ = MagicMock(return_value=False)
        for _ in range(5):
            assert client.get("/health").status_code == 200


# --- Open /chat safety ------------------------------------------------------


def _chat(client, question="which startup makes electric scooters?"):
    return client.post("/chat", json={"question": question, "top_k": 5, "mode": "vector"})


def test_chat_refuses_to_generate_once_the_daily_budget_is_spent(client):
    from src.budget import DailyBudget

    spent = DailyBudget(limit=0)
    with patch("src.main._daily_chat_budget", spent):
        with patch("src.main.retrieve", return_value=[]):
            with patch("src.main.stream_answer") as mock_stream:
                body = _chat(client).text
    assert "today's answer limit" in body
    # The point of the ceiling: the model is never called.
    mock_stream.assert_not_called()


def test_chat_still_returns_sources_when_the_budget_is_spent(client):
    from src.budget import DailyBudget

    with patch("src.main._daily_chat_budget", DailyBudget(limit=0)):
        with patch("src.main.retrieve", return_value=[]):
            body = _chat(client).text
    assert '"type": "sources"' in body


def test_chat_rejects_an_oversized_question(client):
    response = client.post(
        "/chat", json={"question": "x" * 5000, "top_k": 5, "mode": "vector"}
    )
    assert response.status_code == 422


def test_chat_rejects_an_oversized_top_k(client):
    response = client.post(
        "/chat", json={"question": "hi", "top_k": 500, "mode": "vector"}
    )
    assert response.status_code == 422


def test_chat_rejects_an_overlong_history(client):
    turns = [{"role": "user", "content": "hi"} for _ in range(50)]
    response = client.post(
        "/chat", json={"question": "hi", "history": turns, "mode": "vector"}
    )
    assert response.status_code == 422
