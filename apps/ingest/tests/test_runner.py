import json
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.runner import _CHUNKERS, cache_path, run_ingest

def test_invalid_chunker_raises():
    with pytest.raises(ValueError, match="Unknown chunker"):
        run_ingest(chunker="unknown")

def test_uses_default_naive_chunker():
    assert "naive" in _CHUNKERS
    assert "semantic" in _CHUNKERS

@patch("src.runner.scrape_yc_startups")
@patch("src.runner.scrape_startups")
@patch("src.runner.sample_startups")
@patch("src.runner.merge_startups")
@patch("src.runner.embed_text")
@patch("src.runner.load_startups_and_chunks")
@patch("src.runner.psycopg.connect")
def test_run_ingest_no_cache(
    mock_connect, mock_load, mock_embed, mock_merge, mock_sample, mock_scrape, mock_yc
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
    mock_yc.return_value = []
    mock_sample.return_value = [s]
    mock_merge.return_value = [s]
    mock_embed.return_value = [[1.0] * 384]
    mock_conn = MagicMock()
    mock_connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
    mock_connect.return_value.__exit__ = MagicMock(return_value=False)

    if cache_path().exists():
        cache_path().unlink()

    with patch.dict(os.environ, {"DATABASE_URL": "postgresql://x"}):
        run_ingest(use_cache=False, chunker="naive")

    mock_scrape.assert_called_once()
    mock_yc.assert_called_once()
    mock_merge.assert_called_once()
    mock_load.assert_called_once()

def test_cache_path_is_redirected_away_from_the_real_one():
    """The isolation itself, asserted rather than assumed. Without it a test's
    fixture companies land in the file a real ingest reads, and get upserted
    over the live corpus -- which is how two production records came to say
    "We deliver groceries in 10 minutes through dark stores."."""
    resolved = cache_path()
    assert resolved != Path("data/cache/startups.jsonl")
    assert "startups.jsonl" in resolved.name

@patch("src.runner.scrape_yc_startups")
@patch("src.runner.scrape_startups")
@patch("src.runner.sample_startups")
@patch("src.runner.merge_startups")
@patch("src.runner.embed_text")
@patch("src.runner.load_startups_and_chunks")
@patch("src.runner.psycopg.connect")
def test_run_ingest_does_not_cache_a_partial_scrape(
    mock_connect, mock_load, mock_embed, mock_merge, mock_sample, mock_scrape, mock_yc
):
    """One source failing must not be written to the cache, or the next run
    loads the short corpus and never retries it. A truncated Y Combinator
    download produced 58 records this way where a full run gives 107."""
    from src.schema import Startup

    s = Startup(
        name="X",
        normalized_name="x",
        description="word " * 50,
        founders=["A"],
        source_url="https://x.com",
    )
    mock_scrape.return_value = [s]
    mock_yc.side_effect = RuntimeError("peer closed connection")
    mock_sample.return_value = [s]
    mock_merge.return_value = [s]
    mock_embed.return_value = [[1.0] * 384]
    mock_conn = MagicMock()
    mock_connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
    mock_connect.return_value.__exit__ = MagicMock(return_value=False)

    with patch.dict(os.environ, {"DATABASE_URL": "postgresql://x"}):
        run_ingest(use_cache=False, chunker="naive")

    # The run still loads what it got -- a partial corpus beats no corpus.
    assert mock_load.called
    # But it is not cached, so the next run scrapes again.
    assert not cache_path().exists()

@patch("src.runner.scrape_yc_startups")
@patch("src.runner.scrape_startups")
@patch("src.runner.sample_startups")
@patch("src.runner.merge_startups")
@patch("src.runner.embed_text")
@patch("src.runner.load_startups_and_chunks")
@patch("src.runner.psycopg.connect")
def test_run_ingest_cache_persists(
    mock_connect, mock_load, mock_embed, mock_merge, mock_sample, mock_scrape, mock_yc
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
    mock_yc.return_value = []
    mock_sample.return_value = [s]
    mock_merge.return_value = [s]
    mock_embed.return_value = [[1.0] * 384]
    mock_conn = MagicMock()
    mock_connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
    mock_connect.return_value.__exit__ = MagicMock(return_value=False)

    if cache_path().exists():
        cache_path().unlink()

    with patch.dict(os.environ, {"DATABASE_URL": "postgresql://x"}):
        run_ingest(use_cache=False, chunker="naive")
        assert cache_path().exists()

        mock_scrape.reset_mock()
        run_ingest(use_cache=True, chunker="naive")
        mock_scrape.assert_not_called()

    if cache_path().exists():
        cache_path().unlink()

@patch("src.runner.scrape_yc_startups")
@patch("src.runner.scrape_startups")
@patch("src.runner.sample_startups")
@patch("src.runner.merge_startups")
@patch("src.runner.embed_text")
@patch("src.runner.load_startups_and_chunks")
@patch("src.runner.psycopg.connect")
def test_run_ingest_prefixes_chunks_with_startup_name(
    mock_connect, mock_load, mock_embed, mock_merge, mock_sample, mock_scrape, mock_yc
):
    # YC-style descriptions are first-person ("We deliver groceries...") and
    # never mention the company, so name queries miss both FTS and the
    # embedding. Every chunk must carry the display name; chunks that already
    # mention it are left alone.
    from src.schema import Startup

    zepto = Startup(
        name="Zepto",
        normalized_name="zepto",
        description="We deliver groceries in 10 minutes through dark stores.",
        founders=["A"],
        source_url="https://zepto.com",
    )
    oyo = Startup(
        name="Oyo",
        normalized_name="oyo",
        description="Oyo Rooms is an Indian hospitality chain.",
        founders=["B"],
        source_url="https://oyo.com",
    )
    mock_scrape.return_value = [zepto, oyo]
    mock_yc.return_value = []
    mock_sample.return_value = [zepto, oyo]
    mock_merge.return_value = [zepto, oyo]
    mock_embed.side_effect = lambda texts: [[1.0] * 384 for _ in texts]
    mock_conn = MagicMock()
    mock_connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
    mock_connect.return_value.__exit__ = MagicMock(return_value=False)

    if cache_path().exists():
        cache_path().unlink()

    with patch.dict(os.environ, {"DATABASE_URL": "postgresql://x"}):
        run_ingest(use_cache=False, chunker="naive")

    chunks = mock_load.call_args[0][2]
    by_name = {c.startup_name: c for c in chunks}
    assert by_name["zepto"].text == (
        "Zepto: We deliver groceries in 10 minutes through dark stores."
    )
    assert by_name["oyo"].text == "Oyo Rooms is an Indian hospitality chain."
    # embeddings were computed on the prefixed text
    embedded_texts = mock_embed.call_args[0][0]
    assert embedded_texts[0].startswith("Zepto: ")
