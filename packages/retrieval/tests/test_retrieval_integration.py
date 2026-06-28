import os
from typing import Generator

import numpy as np
import psycopg
import pytest
from psycopg import Connection

from isra_retrieval.db import get_conn
from isra_retrieval.keyword_search import search_keyword
from isra_retrieval.models import Chunk
from isra_retrieval.pipeline import retrieve
from isra_retrieval.vector_search import vector_search

def _dsn() -> str:
    return os.environ.get(
        "DATABASE_URL", "postgresql://isra:isra@localhost:5432/isra"
    )

def _can_connect() -> bool:
    try:
        with psycopg.connect(_dsn(), connect_timeout=2):
            return True
    except Exception:
        return False

@pytest.fixture(scope="module")
def conn() -> Generator[Connection, None, None]:
    with get_conn() as c:
        yield c

@pytest.fixture(scope="function", autouse=True)
def clean_test_data(conn: Connection) -> Generator[None, None, None]:
    conn.execute("DELETE FROM chunks WHERE text LIKE '%%integration test%%'")
    conn.execute("DELETE FROM startups WHERE normalized_name = 'integration-test-co'")
    conn.commit()
    yield
    conn.execute("DELETE FROM chunks WHERE text LIKE '%%integration test%%'")
    conn.execute("DELETE FROM startups WHERE normalized_name = 'integration-test-co'")
    conn.commit()

@pytest.fixture
def sample_vector() -> np.ndarray:
    v = np.zeros(384, dtype=np.float32)
    v[0] = 1.0
    return v

@pytest.fixture
def seeded_chunk(conn: Connection, sample_vector: np.ndarray) -> Chunk:
    startup_id = conn.execute(
        """
        INSERT INTO startups (normalized_name, source_url, name, description)
        VALUES ('integration-test-co', 'https://example.com/it', 'Integration Test Co', 'A test startup')
        RETURNING id
        """
    ).fetchone()[0]

    chunk_id = conn.execute(
        """
        INSERT INTO chunks (startup_id, chunk_index, text, embedding)
        VALUES (%s, 0, 'integration test chunk about artificial intelligence funding', %s::vector)
        RETURNING id
        """,
        (startup_id, sample_vector.tolist()),
    ).fetchone()[0]
    conn.commit()

    return Chunk(
        id=chunk_id,
        startup_id=startup_id,
        startup_name="Integration Test Co",
        chunk_index=0,
        text="integration test chunk about artificial intelligence funding",
        source_url="https://example.com/it",
    )

@pytest.mark.skipif(not _can_connect(), reason="Postgres not available")
def test_vector_search_returns_chunk(
    conn: Connection, sample_vector: np.ndarray, seeded_chunk: Chunk
):
    results = vector_search(conn, sample_vector, top_k=5)
    ids = [c.id for c in results]
    assert seeded_chunk.id in ids
    match = next(c for c in results if c.id == seeded_chunk.id)
    assert match.score == pytest.approx(1.0, abs=1e-5)

@pytest.mark.skipif(not _can_connect(), reason="Postgres not available")
def test_keyword_search_returns_chunk(conn: Connection, seeded_chunk: Chunk):
    results = search_keyword(conn, "artificial intelligence funding", top_k=5)
    ids = [c.id for c in results]
    assert seeded_chunk.id in ids
    assert all(isinstance(c.score, float) for c in results)

@pytest.mark.skipif(not _can_connect(), reason="Postgres not available")
def test_retrieve_vector_mode(
    monkeypatch, seeded_chunk: Chunk, sample_vector: np.ndarray
):
    import isra_retrieval.pipeline as pipeline_mod

    monkeypatch.setattr(pipeline_mod, "embed_query", lambda _q: sample_vector)

    results = retrieve(seeded_chunk.text, top_k=5, mode="vector")
    assert seeded_chunk.id in [c.id for c in results]

@pytest.mark.skipif(not _can_connect(), reason="Postgres not available")
def test_retrieve_hybrid_mode(
    monkeypatch, seeded_chunk: Chunk, sample_vector: np.ndarray
):
    import isra_retrieval.pipeline as pipeline_mod

    monkeypatch.setattr(pipeline_mod, "embed_query", lambda _q: sample_vector)

    results = retrieve("artificial intelligence funding", top_k=5, mode="hybrid")
    assert seeded_chunk.id in [c.id for c in results]

@pytest.mark.skipif(not _can_connect(), reason="Postgres not available")
def test_retrieve_hybrid_rerank_mode(
    monkeypatch, seeded_chunk: Chunk, sample_vector: np.ndarray
):
    import isra_retrieval.pipeline as pipeline_mod

    monkeypatch.setattr(pipeline_mod, "embed_query", lambda _q: sample_vector)
    monkeypatch.setattr(
        pipeline_mod,
        "rerank",
        lambda _query, chunks, top_k: [c for c in chunks if c.id == seeded_chunk.id][:top_k],
    )

    results = retrieve("artificial intelligence funding", top_k=5, mode="hybrid+rerank")
    assert seeded_chunk.id in [c.id for c in results]
