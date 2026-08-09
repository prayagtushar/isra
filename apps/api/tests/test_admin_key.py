"""The only remaining gate: /ingest writes to the database and runs the scraper.

This replaces the hand-rolled account system. It is a shared key, not
authentication — enough to stop a passer-by triggering a re-ingest, and honest
about being nothing more than that.
"""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from src.main import app


@pytest.fixture
def client():
    # /ingest is rate limited to 3/hour, which this file would trip on its own.
    # Swap in a permissive limiter so these tests measure the key, not the limit.
    from src.rate_limit import RateLimiter, Rule

    permissive = RateLimiter(default=Rule(limit=1000, window_seconds=60.0))
    with patch("src.main._rate_limiter", permissive):
        yield TestClient(app)


def _ingest(client, key=None):
    headers = {"X-ISRA-Admin-Key": key} if key is not None else {}
    return client.post("/ingest", json={"limit": 1}, headers=headers)


def test_ingest_is_refused_without_a_key(client):
    with patch("src.main._ADMIN_KEY", "s3cret"):
        assert _ingest(client).status_code == 401


def test_ingest_is_refused_with_the_wrong_key(client):
    with patch("src.main._ADMIN_KEY", "s3cret"):
        assert _ingest(client, key="wrong").status_code == 401


def test_ingest_is_refused_when_no_key_is_configured(client):
    # An unset secret must not mean an open door — a deployment that forgot to
    # set the variable would otherwise expose the one write endpoint.
    with patch("src.main._ADMIN_KEY", None):
        assert _ingest(client, key="anything").status_code == 401


def test_ingest_proceeds_with_the_right_key(client):
    with patch("src.main._ADMIN_KEY", "s3cret"):
        with patch("src.main._ingest_stream", return_value=iter([])):
            assert _ingest(client, key="s3cret").status_code == 200


def test_refusal_explains_what_is_needed(client):
    with patch("src.main._ADMIN_KEY", "s3cret"):
        body = _ingest(client).json()
    assert "key" in body["detail"].lower()
