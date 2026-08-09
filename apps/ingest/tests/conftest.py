"""Keep the tests off the paths a real ingest uses.

The ingest cache is relative to the working directory, and both pytest and
`bun run ingest` run from apps/ingest -- so a test that exercised the cache
wrote the very file a later run would read. It happened: a test's two fixture
companies were cached, a run without --no-cache loaded them, and they were
upserted over the live corpus, replacing two real records with
"We deliver groceries in 10 minutes through dark stores."

Redirecting the path here rather than in each test means a test added later
cannot reintroduce the problem by forgetting to.
"""

import pytest

@pytest.fixture(autouse=True)
def isolated_ingest_cache(tmp_path, monkeypatch):
    monkeypatch.setenv("ISRA_INGEST_CACHE", str(tmp_path / "startups.jsonl"))
