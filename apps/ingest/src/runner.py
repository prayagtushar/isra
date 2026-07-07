import json
import os
from pathlib import Path
from typing import List

import psycopg
from dotenv import load_dotenv

from src.chunker import naive_chunk, semantic_chunk
from src.embedder import embed_text
from src.loader import load_startups_and_chunks
from src.merge import merge_startups
from src.sample_data import sample_startups
from src.scraper import scrape_startups
from src.yc_scraper import scrape_yc_startups
from src.schema import Startup

CACHE_PATH = Path("data/cache/startups.jsonl")

# Default number of YC companies to pull (Wikipedia uses the caller's `limit`).
YC_DEFAULT_LIMIT = 50

load_dotenv()

def _load_cache() -> List[Startup]:
    if not CACHE_PATH.exists():
        return []

    with CACHE_PATH.open("r", encoding="utf-8") as f:
        return [Startup.model_validate(json.loads(line)) for line in f if line.strip()]

def _save_cache(startups: List[Startup]) -> None:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CACHE_PATH.open("w", encoding="utf-8") as f:
        for s in startups:
            f.write(json.dumps(s.model_dump(mode="json")) + "\n")

_CHUNKERS = {"naive": naive_chunk, "semantic": semantic_chunk}

def _emit(progress: bool, event: dict) -> None:
    if progress:
        print(json.dumps(event), flush=True)

def _scrape_all(limit: int | None) -> List[Startup]:
    """Scrape every source and concatenate (dedup happens later via merge)."""
    scraped: List[Startup] = []

    try:
        scraped += scrape_startups(limit=limit)            # Wikipedia unicorns
    except Exception as exc:
        print(f"wikipedia scrape failed: {exc}")

    try:
        yc_limit = limit if limit is not None else YC_DEFAULT_LIMIT
        scraped += scrape_yc_startups(limit=yc_limit)      # YC India companies
    except Exception as exc:
        print(f"yc scrape failed: {exc}")

    return scraped

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
        scraped = _scrape_all(limit)
        if not scraped:
            scraped = sample_startups()
        startup_cache = merge_startups(scraped)   # dedupe across sources by normalized_name
        _save_cache(startup_cache)
    _emit(progress, {"type": "stage", "stage": "scrape", "status": "done",
                     "count": len(startup_cache), "cached": cached})

    # embed: chunk + encode
    _emit(progress, {"type": "stage", "stage": "embed", "status": "start"})
    chunk_fn = _CHUNKERS[chunker]
    chunks = []
    for s in startup_cache:
        chunks.extend(chunk_fn(s.description, str(s.source_url), s.normalized_name))

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
