import json
import os
from dataclasses import replace
from pathlib import Path
from typing import List

import psycopg
from dotenv import load_dotenv

from src.chunker import naive_chunk, semantic_chunk
from src.embedder import embed_text
from src.loader import load_startups_and_chunks
from src.merge import merge_startups
from src.scraper import scrape_startups, seed_details
from src.yc_scraper import scrape_yc_startups
from src.schema import Startup

_DEFAULT_CACHE_PATH = Path("data/cache/startups.jsonl")

def cache_path() -> Path:
    """Where the scraped corpus is cached between runs.

    Read at call time, and overridable with ISRA_INGEST_CACHE, so a test can be
    pointed at a temporary file. It matters more than it looks: the path is
    relative to the working directory, and both pytest and `bun run ingest` run
    from apps/ingest -- so a test that exercised the cache wrote the same file a
    real ingest would later read, and a run without --no-cache would load two
    fixture companies and upsert them over the live corpus. That happened.

    tests/conftest.py redirects this for every test rather than per test, so a
    test added later cannot reintroduce it by forgetting.
    """
    override = os.environ.get("ISRA_INGEST_CACHE")
    return Path(override) if override else _DEFAULT_CACHE_PATH

# Default number of YC companies to pull (Wikipedia uses the caller's `limit`).
YC_DEFAULT_LIMIT = 50

load_dotenv()

def _load_cache() -> List[Startup]:
    path = cache_path()
    if not path.exists():
        return []

    with path.open("r", encoding="utf-8") as f:
        return [Startup.model_validate(json.loads(line)) for line in f if line.strip()]

def _save_cache(startups: List[Startup]) -> None:
    path = cache_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for s in startups:
            f.write(json.dumps(s.model_dump(mode="json")) + "\n")

_CHUNKERS = {"naive": naive_chunk, "semantic": semantic_chunk}

def _emit(progress: bool, event: dict) -> None:
    if progress:
        print(json.dumps(event), flush=True)

def _scrape_all(limit: int | None) -> tuple[List[Startup], List[str]]:
    """Scrape every source and concatenate (dedup happens later via merge).

    Returns the records and the names of any sources that failed. One source
    going down should not abort the run -- but the caller has to know, because a
    partial scrape must not be cached as if it were the whole corpus.
    """
    scraped: List[Startup] = []
    failed: List[str] = []

    try:
        scraped += scrape_startups(limit=limit)            # Wikipedia unicorns
    except Exception as exc:
        print(f"wikipedia scrape failed: {exc}")
        failed.append("wikipedia")

    try:
        yc_limit = limit if limit is not None else YC_DEFAULT_LIMIT
        scraped += scrape_yc_startups(limit=yc_limit)      # YC India companies
    except Exception as exc:
        print(f"yc scrape failed: {exc}")
        failed.append("yc")

    try:
        scraped += seed_details()                          # named companies the list misses
    except Exception as exc:
        print(f"notable scrape failed: {exc}")
        failed.append("notable")

    return scraped, failed

def run_ingest(
    use_cache: bool = True,
    chunker: str = "naive",
    progress: bool = False,
    limit: int | None = None,
) -> None:
    if chunker not in _CHUNKERS:
        raise ValueError(f"Unknown chunker: {chunker}. Choose from {list(_CHUNKERS)}")

    startup_cache: List[Startup] = []

    # discover: load any cached corpus
    _emit(progress, {"type": "stage", "stage": "discover", "status": "start"})
    if use_cache:
        startup_cache = _load_cache()
    cached = bool(startup_cache)
    _emit(progress, {"type": "stage", "stage": "discover", "status": "done",
                     "count": len(startup_cache), "cached": cached})

    # scrape: pull from all sources (Wikipedia + YC); fall back to sample data
    _emit(progress, {"type": "stage", "stage": "scrape", "status": "start"})
    if not startup_cache:
        scraped, failed = _scrape_all(limit)
        if not scraped:
            # Deliberately not falling back to sample_startups(). That fallback
            # put four hand-written records into the live corpus -- Paytm,
            # Zomato, Ola Electric, PharmEasy, with company homepages as their
            # sources -- where they sat indistinguishable from scraped ones
            # while the README said the corpus came from Wikipedia and Y
            # Combinator. Loading nothing is recoverable and obvious; fabricated
            # rows are neither. The fixtures remain in sample_data for tests.
            raise RuntimeError(
                "every source failed; refusing to seed the corpus with sample data"
            )
        startup_cache = merge_startups(scraped)   # dedupe across sources by normalized_name
        if failed:
            # Caching a partial scrape makes the gap permanent: the next run
            # loads the short corpus and never retries the source that failed.
            # A truncated Y Combinator download already produced a 58-record
            # corpus this way, where a full run gives 107.
            print(
                f"not caching: {', '.join(failed)} failed, so this corpus is "
                f"incomplete ({len(startup_cache)} records)"
            )
        else:
            _save_cache(startup_cache)
    _emit(progress, {"type": "stage", "stage": "scrape", "status": "done",
                     "count": len(startup_cache), "cached": cached})

    # embed: chunk + encode
    _emit(progress, {"type": "stage", "stage": "embed", "status": "start"})
    chunk_fn = _CHUNKERS[chunker]
    chunks = []
    for s in startup_cache:
        for c in chunk_fn(s.description, str(s.source_url), s.normalized_name):
            # YC-style descriptions are first-person and never name the
            # company, so name queries would miss both FTS and the embedding.
            if s.name.lower() not in c.text.lower():
                c = replace(c, text=f"{s.name}: {c.text}")
            chunks.append(c)

    embeddings = embed_text([c.text for c in chunks])
    _emit(progress, {"type": "stage", "stage": "embed", "status": "done", "chunks": len(chunks)})

    # load: upsert into Postgres
    _emit(progress, {"type": "stage", "stage": "load", "status": "start"})
    url = os.environ.get("DATABASE_URL")
    # prepare_threshold=None for transaction-mode pooler compatibility (Supabase 6543).
    with psycopg.connect(url, prepare_threshold=None) as conn:
        load_startups_and_chunks(conn, startup_cache, chunks, embeddings)
    _emit(progress, {"type": "stage", "stage": "load", "status": "done"})

    _emit(progress, {"type": "done", "startups": len(startup_cache), "chunks": len(chunks)})
    print(f"Loaded {len(startup_cache)} startups and {len(chunks)} chunks.")
