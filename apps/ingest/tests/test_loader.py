from datetime import datetime
from unittest.mock import MagicMock

import numpy as np
import pytest

from src.chunker import Chunk
from src.loader import load_startups_and_chunks
from src.schema import Startup

def _startup(name: str) -> Startup:
    return Startup(
        name=name,
        normalized_name=name,
        description=f"{name} description",
        founders=["Founder"],
        source_url="https://example.com",
        scraped_date=datetime.now(),
    )

def test_mismatch_raises():
    conn = MagicMock()
    cursor = MagicMock()
    cursor.fetchall.return_value = [(1, "x")]
    conn.cursor.return_value.__enter__ = MagicMock(return_value=cursor)
    conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

    s = _startup("x")
    chunks = [Chunk(text="a", source_url="https://a.com", startup_name="x", chunk_index=0)]
    embeddings = np.array([[1.0, 2.0], [3.0, 4.0]])

    with pytest.raises(ValueError, match="Mismatch"):
        load_startups_and_chunks(conn, [s], chunks, embeddings)

def test_unknown_startup_raises():
    conn = MagicMock()
    cursor = MagicMock()
    cursor.fetchall.return_value = [(1, "other")]
    conn.cursor.return_value.__enter__ = MagicMock(return_value=cursor)
    conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

    s = _startup("x")
    chunks = [Chunk(text="a", source_url="https://a.com", startup_name="x", chunk_index=0)]
    embeddings = np.zeros((1, 384))

    with pytest.raises(ValueError, match="unknown startup"):
        load_startups_and_chunks(conn, [s], chunks, embeddings)

def test_loads_startups_and_chunks():
    conn = MagicMock()
    cursor = MagicMock()
    cursor.fetchall.return_value = [(1, "x")]
    conn.cursor.return_value.__enter__ = MagicMock(return_value=cursor)
    conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

    s = _startup("x")
    chunks = [
        Chunk(text="a", source_url="https://a.com", startup_name="x", chunk_index=0),
        Chunk(text="b", source_url="https://a.com", startup_name="x", chunk_index=1),
    ]
    embeddings = np.zeros((2, 384))

    load_startups_and_chunks(conn, [s], chunks, embeddings)

    assert cursor.executemany.call_count == 2
    calls = cursor.executemany.call_args_list
    assert "INSERT INTO startups" in calls[0][0][0]
    assert "INSERT INTO chunks" in calls[1][0][0]
