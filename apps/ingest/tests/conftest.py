"""Keep tests off the paths a real ingest uses; the cache is relative to the working directory."""

import pytest

@pytest.fixture(autouse=True)
def isolated_ingest_cache(tmp_path, monkeypatch):
    monkeypatch.setenv("ISRA_INGEST_CACHE", str(tmp_path / "startups.jsonl"))
