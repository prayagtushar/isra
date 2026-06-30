import json
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.runner import CACHE_PATH, _CHUNKERS, run_ingest

def test_invalid_chunker_raises():
    with pytest.raises(ValueError, match="Unknown chunker"):
        run_ingest(chunker="unknown")

def test_uses_default_naive_chunker():
    assert "naive" in _CHUNKERS
    assert "semantic" in _CHUNKERS

@patch("src.runner.scrape_startups")
@patch("src.runner.sample_startups")
@patch("src.runner.merge_startups")
@patch("src.runner.embed_text")
@patch("src.runner.load_startups_and_chunks")
@patch("src.runner.psycopg.connect")
def test_run_ingest_no_cache(
    mock_connect, mock_load, mock_embed, mock_merge, mock_sample, mock_scrape
):
    from src.schema import Startup

    s = Startup(
        name="X",
        normalized_name="x",
        description="word " * 50,
        founders=["A"],
        source_url="https://x.com",
    )
    mock_scrape.return_value = [s]
    mock_sample.return_value = [s]
    mock_merge.return_value = [s]
    mock_embed.return_value = [[1.0] * 384]
    mock_conn = MagicMock()
    mock_connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
    mock_connect.return_value.__exit__ = MagicMock(return_value=False)

    if CACHE_PATH.exists():
        CACHE_PATH.unlink()

    with patch.dict(os.environ, {"DATABASE_URL": "postgresql://x"}):
        run_ingest(use_cache=False, chunker="naive")

    mock_scrape.assert_called_once()
    mock_merge.assert_called_once()
    mock_load.assert_called_once()

@patch("src.runner.scrape_startups")
@patch("src.runner.sample_startups")
@patch("src.runner.merge_startups")
@patch("src.runner.embed_text")
@patch("src.runner.load_startups_and_chunks")
@patch("src.runner.psycopg.connect")
def test_run_ingest_cache_persists(
    mock_connect, mock_load, mock_embed, mock_merge, mock_sample, mock_scrape
):
    from src.schema import Startup

    s = Startup(
        name="X",
        normalized_name="x",
        description="word " * 50,
        founders=["A"],
        source_url="https://x.com",
    )
    mock_scrape.return_value = [s]
    mock_sample.return_value = [s]
    mock_merge.return_value = [s]
    mock_embed.return_value = [[1.0] * 384]
    mock_conn = MagicMock()
    mock_connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
    mock_connect.return_value.__exit__ = MagicMock(return_value=False)

    if CACHE_PATH.exists():
        CACHE_PATH.unlink()

    with patch.dict(os.environ, {"DATABASE_URL": "postgresql://x"}):
        run_ingest(use_cache=False, chunker="naive")
        assert CACHE_PATH.exists()

        mock_scrape.reset_mock()
        run_ingest(use_cache=True, chunker="naive")
        mock_scrape.assert_not_called()

    if CACHE_PATH.exists():
        CACHE_PATH.unlink()
