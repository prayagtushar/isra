import json
import os
from pathlib import Path
from typing import List

import psycopg
from dotenv import load_dotenv

from src.chunker import naive_chunk
from src.embedder import embed_text
from src.loader import load_startups_and_chunks
from src.merge import merge_startup
from src.sample_data import sample_startup
from src.schema import Startup


CACHE_PATH = Path("data/cache/startus.jsonl")

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


def run_ingest(use_cache: bool = True) -> None:

    startup_cache: List[Startup] = []

    if use_cache:
        startup_cache = _load_cache()

    if not startup_cache:
        startup_cache = sample_startup()
        startup_cache = merge_startup(startup_cache)
        _save_cache(startup_cache)

    chunks = []
    for s in startup_cache:
        chunks.extend(naive_chunk(s.description, str(s.source_url), s.normalized_name))

    embeddings = embed_text([c.text for c in chunks])

    url = os.environ.get("DATABASE_URL")
    with psycopg.connect(url) as conn:
        load_startups_and_chunks(conn, startup_cache, chunks, embeddings)

    print(f"Loaded {len(startup_cache)} startups and {len(chunks)} chunks.")
