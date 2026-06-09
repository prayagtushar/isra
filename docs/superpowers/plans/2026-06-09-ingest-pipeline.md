# Ingest Pipeline Implementation Plan (Plan 1 of 6)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Scrape 50–100 Indian startups into a validated corpus, chunk and embed it, and load it into a local Postgres with both vector and full-text indexes — the data foundation every other subsystem reads from.

**Architecture:** Schema-first ingestion. A Pydantic `Startup` model is the only shape that leaves `apps/ingest`. Per-source scrapers fill it; records are deduped by `normalized_name`, chunked (naive + semantic variants), embedded with a local BGE model, and upserted into Postgres. The shared data layer (DB connection, table schema, chunk model) lives in `packages/retrieval` because both ingest and the API depend on it. Keyword search uses Postgres `tsvector` (single store does both halves of hybrid search).

**Tech Stack:** Python 3.11+ · uv workspace · httpx · BeautifulSoup/lxml · Pydantic v2 · sentence-transformers (BGE) · psycopg 3 · pgvector · Postgres 16 (Docker) · pytest

---

## Decomposition: the 6 plans (build order)

1. **Ingest pipeline** ← *this plan* (Tue) — corpus in Postgres
2. **Retrieval package** (Wed) — `retrieve(query, top_k, mode)`: vector → hybrid (RRF) → BGE rerank
3. **API** (Wed–Thu) — FastAPI `/search`, `/chat` (SSE), `/feedback`; Langfuse tracing
4. **Evals** (Thu) — Ragas runner, ~30-Q golden set, 2 experiments → `EVALUATION.md`
5. **Web UI** (Fri) — Next.js streaming chat with inline citations
6. **Deploy** (Fri) — Cloud Run + Supabase + Vercel; `ARCHITECTURE.md`

Each plan produces working, testable software on its own. Write the next plan when this one is green.

---

## File structure (this plan)

**Shared data layer — `packages/retrieval`:**
- Create `packages/retrieval/src/isra_retrieval/db.py` — psycopg connection helper, reads `DATABASE_URL`
- Create `packages/retrieval/src/isra_retrieval/models.py` — `Chunk` dataclass (the row shape shared with the API)
- Create `packages/retrieval/src/isra_retrieval/schema.sql` — `startups` + `chunks` tables, vector + tsvector + GIN/HNSW indexes
- Create `packages/retrieval/src/isra_retrieval/embeddings.py` — BGE embedder wrapper (lazy-loaded singleton)
- Create `packages/retrieval/tests/test_embeddings.py`, `packages/retrieval/tests/conftest.py`

**Ingest — `apps/ingest`:**
- Create `apps/ingest/src/schema.py` — `Startup` Pydantic model + normalization
- Create `apps/ingest/src/scrapers/__init__.py`, `apps/ingest/src/scrapers/wikipedia.py`
- Create `apps/ingest/src/dedup.py` — merge records by `normalized_name`
- Create `apps/ingest/src/chunking.py` — `chunk_startup(startup, strategy)` → list of chunk dicts
- Create `apps/ingest/src/load.py` — upsert startups + chunks into Postgres
- Create `apps/ingest/src/__main__.py` — wires scrape → dedup → chunk → embed → load, writes manifest
- Create `apps/ingest/tests/test_schema.py`, `test_dedup.py`, `test_chunking.py`

**Infra:**
- Create `infra/compose.yml` — Postgres 16 + pgvector
- Create `infra/init.sql` symlink/copy step (schema applied on boot)

**Config:**
- Modify `packages/retrieval/pyproject.toml` — drop `rank-bm25`, add `psycopg[binary]`, `pgvector`, `numpy`; add pytest to a dev group
- Modify `apps/ingest/pyproject.toml` — add `pydantic`, pytest dev group

---

## Decisions locked for this plan

- **Keyword search = Postgres `tsvector`**, not `rank-bm25`. Drop the unused dep. Single store is the stated interview point.
- **Embedding model = `BAAI/bge-small-en-v1.5`** (384-dim). Small enough for fast local + cheap Cloud Run memory; upgrade to `bge-base` only if evals demand it (post-MARB note).
- **First scraper = Wikipedia.** Most reliable, no anti-bot, structured infoboxes. YC/Inc42/DPIIT are added later in the same `scrapers/` pattern; Wikipedia alone clears the ≥50 bar via "List of Indian startups/unicorns" pages. The 1.5hr/source rule is law.
- **Embedding happens in `load.py`**, not chunking — chunking stays pure/testable (no model download in unit tests).

---

## Task 1: Postgres + pgvector via Docker

**Files:**
- Create: `infra/compose.yml`
- Create: `infra/init.sql`

- [ ] **Step 1: Write the compose file**

```yaml
# infra/compose.yml
services:
  db:
    image: pgvector/pgvector:pg16
    container_name: isra-db
    environment:
      POSTGRES_USER: isra
      POSTGRES_PASSWORD: isra
      POSTGRES_DB: isra
    ports:
      - "5432:5432"
    volumes:
      - isra-pgdata:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql:ro
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U isra"]
      interval: 5s
      timeout: 3s
      retries: 10
volumes:
  isra-pgdata:
```

- [ ] **Step 2: Write init.sql (just the extension; schema applied by app)**

```sql
-- infra/init.sql
CREATE EXTENSION IF NOT EXISTS vector;
```

- [ ] **Step 3: Bring it up and verify**

Run: `docker compose -f infra/compose.yml up -d && sleep 5 && docker exec isra-db psql -U isra -d isra -c "SELECT extname FROM pg_extension WHERE extname='vector';"`
Expected: a row containing `vector`.

- [ ] **Step 4: Commit**

```bash
git add infra/compose.yml infra/init.sql
git commit -m "infra: local Postgres with pgvector"
```

---

## Task 2: Retrieval package config + DB connection

**Files:**
- Modify: `packages/retrieval/pyproject.toml`
- Create: `packages/retrieval/src/isra_retrieval/db.py`
- Create: `packages/retrieval/tests/conftest.py`
- Test: `packages/retrieval/tests/test_db.py`

- [ ] **Step 1: Update pyproject deps**

Replace the `dependencies` array and add a dev group:

```toml
# packages/retrieval/pyproject.toml
[project]
name = "isra-retrieval"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "pgvector",
    "sentence-transformers",
    "psycopg[binary]",
    "numpy",
]

[dependency-groups]
dev = ["pytest"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/isra_retrieval"]
```

- [ ] **Step 2: Sync the workspace**

Run: `uv sync`
Expected: resolves without error; `rank-bm25` no longer installed.

- [ ] **Step 3: Write the failing test**

```python
# packages/retrieval/tests/test_db.py
from isra_retrieval.db import get_dsn

def test_get_dsn_defaults_to_local():
    dsn = get_dsn(env={})
    assert "isra" in dsn and "5432" in dsn

def test_get_dsn_prefers_env():
    dsn = get_dsn(env={"DATABASE_URL": "postgresql://x@host:5432/y"})
    assert dsn == "postgresql://x@host:5432/y"
```

- [ ] **Step 4: Run test to verify it fails**

Run: `uv run --directory packages/retrieval pytest tests/test_db.py -v`
Expected: FAIL — `ModuleNotFoundError` / `cannot import name 'get_dsn'`.

- [ ] **Step 5: Implement db.py**

```python
# packages/retrieval/src/isra_retrieval/db.py
import os
from contextlib import contextmanager

import psycopg

DEFAULT_DSN = "postgresql://isra:isra@localhost:5432/isra"


def get_dsn(env: dict | None = None) -> str:
    env = os.environ if env is None else env
    return env.get("DATABASE_URL", DEFAULT_DSN)


@contextmanager
def connect(dsn: str | None = None):
    conn = psycopg.connect(dsn or get_dsn())
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
```

- [ ] **Step 6: Run test to verify it passes**

Run: `uv run --directory packages/retrieval pytest tests/test_db.py -v`
Expected: PASS (2 passed).

- [ ] **Step 7: Commit**

```bash
git add packages/retrieval/pyproject.toml packages/retrieval/src/isra_retrieval/db.py packages/retrieval/tests/test_db.py
git commit -m "feat(retrieval): DSN resolution + connection helper"
```

---

## Task 3: Database schema (startups + chunks)

**Files:**
- Create: `packages/retrieval/src/isra_retrieval/schema.sql`
- Create: `packages/retrieval/src/isra_retrieval/migrate.py`
- Test: `packages/retrieval/tests/test_migrate.py`

- [ ] **Step 1: Write schema.sql**

`embedding vector(384)` matches `bge-small-en-v1.5`. The `tsv` column is generated from chunk text for keyword search.

```sql
-- packages/retrieval/src/isra_retrieval/schema.sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS startups (
    id              TEXT PRIMARY KEY,          -- normalized_name
    name            TEXT NOT NULL,
    one_liner       TEXT,
    description     TEXT NOT NULL,
    sectors         TEXT[] NOT NULL DEFAULT '{}',
    founded_year    INT,
    hq_city         TEXT,
    hq_state        TEXT,
    funding_stage   TEXT,
    total_funding_usd DOUBLE PRECISION,
    founders        TEXT[] NOT NULL DEFAULT '{}',
    website         TEXT,
    sources         JSONB NOT NULL DEFAULT '[]',  -- [{source, source_url, scraped_at}]
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS chunks (
    id              TEXT PRIMARY KEY,          -- f"{startup_id}:{strategy}:{idx}"
    startup_id      TEXT NOT NULL REFERENCES startups(id) ON DELETE CASCADE,
    strategy        TEXT NOT NULL,             -- 'naive' | 'semantic'
    idx             INT NOT NULL,
    text            TEXT NOT NULL,
    source_url      TEXT,
    embedding       vector(384),
    tsv             tsvector GENERATED ALWAYS AS (to_tsvector('english', text)) STORED
);

CREATE INDEX IF NOT EXISTS chunks_tsv_idx ON chunks USING GIN (tsv);
CREATE INDEX IF NOT EXISTS chunks_embedding_idx
    ON chunks USING hnsw (embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS chunks_strategy_idx ON chunks (strategy);
```

- [ ] **Step 2: Write the failing test**

```python
# packages/retrieval/tests/test_migrate.py
import os
import pytest
from isra_retrieval.db import connect
from isra_retrieval.migrate import apply_schema

pytestmark = pytest.mark.skipif(
    not os.environ.get("RUN_DB_TESTS"), reason="needs local Postgres"
)

def test_apply_schema_creates_tables():
    apply_schema()
    with connect() as conn:
        rows = conn.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema='public'"
        ).fetchall()
    names = {r[0] for r in rows}
    assert {"startups", "chunks"} <= names
```

- [ ] **Step 3: Run test to verify it fails**

Run: `RUN_DB_TESTS=1 uv run --directory packages/retrieval pytest tests/test_migrate.py -v`
Expected: FAIL — `cannot import name 'apply_schema'`.

- [ ] **Step 4: Implement migrate.py**

```python
# packages/retrieval/src/isra_retrieval/migrate.py
from importlib.resources import files

from .db import connect

def apply_schema(dsn: str | None = None) -> None:
    sql = files("isra_retrieval").joinpath("schema.sql").read_text()
    with connect(dsn) as conn:
        conn.execute(sql)


if __name__ == "__main__":
    apply_schema()
    print("schema applied")
```

- [ ] **Step 5: Ensure schema.sql ships in the wheel**

Add to `packages/retrieval/pyproject.toml` so the `.sql` is packaged:

```toml
[tool.hatch.build.targets.wheel.force-include]
"src/isra_retrieval/schema.sql" = "isra_retrieval/schema.sql"
```

Run: `uv sync`
Expected: resolves clean.

- [ ] **Step 6: Run test to verify it passes**

Run: `RUN_DB_TESTS=1 uv run --directory packages/retrieval pytest tests/test_migrate.py -v`
Expected: PASS (1 passed).

- [ ] **Step 7: Commit**

```bash
git add packages/retrieval/src/isra_retrieval/schema.sql packages/retrieval/src/isra_retrieval/migrate.py packages/retrieval/tests/test_migrate.py packages/retrieval/pyproject.toml
git commit -m "feat(retrieval): DB schema + migration runner"
```

---

## Task 4: Chunk model + BGE embedder

**Files:**
- Create: `packages/retrieval/src/isra_retrieval/models.py`
- Create: `packages/retrieval/src/isra_retrieval/embeddings.py`
- Test: `packages/retrieval/tests/test_embeddings.py`

- [ ] **Step 1: Write models.py**

```python
# packages/retrieval/src/isra_retrieval/models.py
from dataclasses import dataclass

@dataclass(frozen=True)
class Chunk:
    id: str
    startup_id: str
    strategy: str
    idx: int
    text: str
    source_url: str | None = None
```

- [ ] **Step 2: Write the failing test**

```python
# packages/retrieval/tests/test_embeddings.py
from isra_retrieval.embeddings import embed_texts, EMBED_DIM

def test_embed_returns_correct_dim():
    vecs = embed_texts(["Razorpay is a fintech company.", "Zomato delivers food."])
    assert len(vecs) == 2
    assert len(vecs[0]) == EMBED_DIM == 384

def test_embed_is_deterministic():
    a = embed_texts(["same text"])[0]
    b = embed_texts(["same text"])[0]
    assert a == b
```

- [ ] **Step 3: Run test to verify it fails**

Run: `uv run --directory packages/retrieval pytest tests/test_embeddings.py -v`
Expected: FAIL — `cannot import name 'embed_texts'`.

- [ ] **Step 4: Implement embeddings.py**

```python
# packages/retrieval/src/isra_retrieval/embeddings.py
from functools import lru_cache

EMBED_MODEL = "BAAI/bge-small-en-v1.5"
EMBED_DIM = 384

@lru_cache(maxsize=1)
def _model():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(EMBED_MODEL)

def embed_texts(texts: list[str]) -> list[list[float]]:
    vecs = _model().encode(texts, normalize_embeddings=True)
    return [v.tolist() for v in vecs]
```

- [ ] **Step 5: Run test to verify it passes**

Run: `uv run --directory packages/retrieval pytest tests/test_embeddings.py -v`
Expected: PASS (first run downloads the model, ~30s).

- [ ] **Step 6: Commit**

```bash
git add packages/retrieval/src/isra_retrieval/models.py packages/retrieval/src/isra_retrieval/embeddings.py packages/retrieval/tests/test_embeddings.py
git commit -m "feat(retrieval): Chunk model + BGE embedder"
```

---

## Task 5: Startup schema (the data contract)

**Files:**
- Modify: `apps/ingest/pyproject.toml`
- Create: `apps/ingest/src/schema.py`
- Test: `apps/ingest/tests/test_schema.py`

- [ ] **Step 1: Update ingest deps**

```toml
# apps/ingest/pyproject.toml
[project]
name = "isra-ingest"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "isra-retrieval",
    "httpx",
    "beautifulsoup4",
    "lxml",
    "pydantic>=2",
]

[dependency-groups]
dev = ["pytest"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src"]
```

Run: `uv sync`
Expected: clean resolve.

- [ ] **Step 2: Write the failing test**

```python
# apps/ingest/tests/test_schema.py
from datetime import datetime, timezone
from src.schema import Startup, normalize_name

def test_normalize_name_strips_suffix_and_punctuation():
    assert normalize_name("Razorpay Software Pvt. Ltd.") == "razorpay software"
    assert normalize_name("CRED!") == "cred"

def test_startup_computes_normalized_name():
    s = Startup(
        name="Razorpay",
        description="A fintech payments company based in Bangalore.",
        source="wikipedia",
        source_url="https://en.wikipedia.org/wiki/Razorpay",
        scraped_at=datetime.now(timezone.utc),
    )
    assert s.normalized_name == "razorpay"

def test_startup_requires_description():
    import pytest
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        Startup(
            name="X", description="", source="wikipedia",
            source_url="https://example.com", scraped_at=datetime.now(timezone.utc),
        )
```

- [ ] **Step 3: Run test to verify it fails**

Run: `uv run --directory apps/ingest pytest tests/test_schema.py -v`
Expected: FAIL — `No module named 'src.schema'`.

- [ ] **Step 4: Implement schema.py**

```python
# apps/ingest/src/schema.py
import re
from datetime import datetime

from pydantic import BaseModel, Field, field_validator, model_validator

_SUFFIXES = r"\b(pvt|private|ltd|limited|inc|llp|technologies|software)\b"

def normalize_name(name: str) -> str:
    s = name.lower()
    s = re.sub(r"[^\w\s]", "", s)          # drop punctuation
    s = re.sub(_SUFFIXES, "", s)           # drop legal/common suffixes
    s = re.sub(r"\s+", " ", s).strip()
    return s

class Startup(BaseModel):
    name: str
    normalized_name: str = ""
    description: str
    one_liner: str | None = None
    sectors: list[str] = Field(default_factory=list)
    founded_year: int | None = None
    hq_city: str | None = None
    hq_state: str | None = None
    funding_stage: str | None = None
    total_funding_usd: float | None = None
    founders: list[str] = Field(default_factory=list)
    website: str | None = None
    source: str
    source_url: str
    scraped_at: datetime

    @field_validator("description")
    @classmethod
    def _desc_nonempty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("description is required and non-empty")
        return v.strip()

    @model_validator(mode="after")
    def _fill_normalized(self):
        if not self.normalized_name:
            object.__setattr__(self, "normalized_name", normalize_name(self.name))
        return self
```

- [ ] **Step 5: Run test to verify it passes**

Run: `uv run --directory apps/ingest pytest tests/test_schema.py -v`
Expected: PASS (3 passed).

- [ ] **Step 6: Commit**

```bash
git add apps/ingest/pyproject.toml apps/ingest/src/schema.py apps/ingest/tests/test_schema.py
git commit -m "feat(ingest): Startup data contract + name normalization"
```

---

## Task 6: Dedup / merge

**Files:**
- Create: `apps/ingest/src/dedup.py`
- Test: `apps/ingest/tests/test_dedup.py`

- [ ] **Step 1: Write the failing test**

```python
# apps/ingest/tests/test_dedup.py
from datetime import datetime, timezone
from src.schema import Startup
from src.dedup import merge_startups

def _s(name, desc, source, **kw):
    return Startup(name=name, description=desc, source=source,
                   source_url=f"https://{source}.com/{name}",
                   scraped_at=datetime.now(timezone.utc), **kw)

def test_merge_combines_same_normalized_name():
    a = _s("Flipkart", "Ecommerce.", "yc", founded_year=2007)
    b = _s("Flipkart Pvt Ltd", "Online retailer.", "wikipedia", hq_city="Bangalore")
    out = merge_startups([a, b])
    assert len(out) == 1
    merged = out[0]
    assert merged.founded_year == 2007        # filled from a
    assert merged.hq_city == "Bangalore"      # filled from b
    assert len(merged.sources) == 2           # provenance preserved

def test_merge_keeps_distinct_companies():
    out = merge_startups([_s("Zomato", "Food.", "yc"), _s("Swiggy", "Food.", "yc")])
    assert len(out) == 2
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run --directory apps/ingest pytest tests/test_dedup.py -v`
Expected: FAIL — `No module named 'src.dedup'`.

- [ ] **Step 3: Implement dedup.py**

Output is a small `MergedStartup` carrying a `sources` list (matches the `startups.sources` JSONB column).

```python
# apps/ingest/src/dedup.py
from dataclasses import dataclass, field
from .schema import Startup

_SCALARS = ["one_liner", "founded_year", "hq_city", "hq_state",
            "funding_stage", "total_funding_usd", "website", "description"]
_LISTS = ["sectors", "founders"]

@dataclass
class MergedStartup:
    id: str
    name: str
    description: str
    one_liner: str | None = None
    sectors: list[str] = field(default_factory=list)
    founded_year: int | None = None
    hq_city: str | None = None
    hq_state: str | None = None
    funding_stage: str | None = None
    total_funding_usd: float | None = None
    founders: list[str] = field(default_factory=list)
    website: str | None = None
    sources: list[dict] = field(default_factory=list)

def merge_startups(items: list[Startup]) -> list[MergedStartup]:
    by_key: dict[str, MergedStartup] = {}
    for s in items:
        m = by_key.get(s.normalized_name)
        prov = {"source": s.source, "source_url": s.source_url,
                "scraped_at": s.scraped_at.isoformat()}
        if m is None:
            by_key[s.normalized_name] = MergedStartup(
                id=s.normalized_name, name=s.name, description=s.description,
                one_liner=s.one_liner, sectors=list(s.sectors),
                founded_year=s.founded_year, hq_city=s.hq_city, hq_state=s.hq_state,
                funding_stage=s.funding_stage, total_funding_usd=s.total_funding_usd,
                founders=list(s.founders), website=s.website, sources=[prov],
            )
            continue
        for attr in _SCALARS:                      # fill blanks only
            if getattr(m, attr) in (None, "") and getattr(s, attr) not in (None, ""):
                setattr(m, attr, getattr(s, attr))
        for attr in _LISTS:                        # union
            merged = list(dict.fromkeys(getattr(m, attr) + getattr(s, attr)))
            setattr(m, attr, merged)
        m.sources.append(prov)
    return list(by_key.values())
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run --directory apps/ingest pytest tests/test_dedup.py -v`
Expected: PASS (2 passed).

- [ ] **Step 5: Commit**

```bash
git add apps/ingest/src/dedup.py apps/ingest/tests/test_dedup.py
git commit -m "feat(ingest): merge/dedup startups by normalized name"
```

---

## Task 7: Chunking (naive + semantic)

**Files:**
- Create: `apps/ingest/src/chunking.py`
- Test: `apps/ingest/tests/test_chunking.py`

Both strategies produce chunk dicts from a `MergedStartup`. "Naive" = fixed-size word windows over the assembled document text. "Semantic" = split on sentence boundaries, then greedily pack sentences up to a token-ish budget (keeps related sentences together). Both prepend the startup name so a chunk is self-describing for retrieval.

- [ ] **Step 1: Write the failing test**

```python
# apps/ingest/tests/test_chunking.py
from src.dedup import MergedStartup
from src.chunking import chunk_startup, assemble_document

def _m():
    return MergedStartup(
        id="razorpay", name="Razorpay",
        description=("Razorpay is an Indian fintech company. "
                     "It provides payment gateway services. "
                     "It was founded in 2014 in Bangalore. "
                     "The founders are Harshil Mathur and Shashank Kumar."),
        sectors=["fintech", "payments"], founded_year=2014, hq_city="Bangalore",
        founders=["Harshil Mathur", "Shashank Kumar"],
        sources=[{"source": "wikipedia", "source_url": "https://en.wikipedia.org/wiki/Razorpay", "scraped_at": "2026-06-09T00:00:00+00:00"}],
    )

def test_naive_produces_indexed_chunks_with_name_prefix():
    chunks = chunk_startup(_m(), strategy="naive", size=12, overlap=2)
    assert len(chunks) >= 1
    assert all(c["strategy"] == "naive" for c in chunks)
    assert [c["idx"] for c in chunks] == list(range(len(chunks)))
    assert "Razorpay" in chunks[0]["text"]
    assert chunks[0]["source_url"] == "https://en.wikipedia.org/wiki/Razorpay"

def test_semantic_keeps_sentences_intact():
    chunks = chunk_startup(_m(), strategy="semantic", max_chars=120)
    assert all(c["strategy"] == "semantic" for c in chunks)
    # no chunk should split mid-sentence (each ends with terminal punctuation)
    assert all(c["text"].rstrip().endswith((".", "!", "?")) for c in chunks)

def test_assemble_document_includes_structured_facts():
    doc = assemble_document(_m())
    assert "Razorpay" in doc and "fintech" in doc and "2014" in doc
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run --directory apps/ingest pytest tests/test_chunking.py -v`
Expected: FAIL — `No module named 'src.chunking'`.

- [ ] **Step 3: Implement chunking.py**

```python
# apps/ingest/src/chunking.py
import re
from .dedup import MergedStartup

def assemble_document(m: MergedStartup) -> str:
    parts = [f"{m.name}."]
    if m.one_liner:
        parts.append(m.one_liner)
    parts.append(m.description)
    facts = []
    if m.sectors:
        facts.append(f"Sectors: {', '.join(m.sectors)}.")
    if m.founded_year:
        facts.append(f"Founded: {m.founded_year}.")
    if m.hq_city:
        facts.append(f"Headquarters: {m.hq_city}{', ' + m.hq_state if m.hq_state else ''}.")
    if m.funding_stage:
        facts.append(f"Funding stage: {m.funding_stage}.")
    if m.founders:
        facts.append(f"Founders: {', '.join(m.founders)}.")
    parts.extend(facts)
    return " ".join(parts)

def _source_url(m: MergedStartup) -> str | None:
    return m.sources[0]["source_url"] if m.sources else None

def _split_sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]

def _naive(doc: str, size: int, overlap: int) -> list[str]:
    words = doc.split()
    if not words:
        return []
    step = max(1, size - overlap)
    out = []
    for start in range(0, len(words), step):
        out.append(" ".join(words[start:start + size]))
        if start + size >= len(words):
            break
    return out

def _semantic(name: str, doc: str, max_chars: int) -> list[str]:
    sents, buf, out = _split_sentences(doc), "", []
    for s in sents:
        candidate = f"{buf} {s}".strip()
        if buf and len(candidate) > max_chars:
            out.append(buf)
            buf = s
        else:
            buf = candidate
    if buf:
        out.append(buf)
    return out

def chunk_startup(m: MergedStartup, strategy: str = "naive",
                  size: int = 120, overlap: int = 20, max_chars: int = 600) -> list[dict]:
    doc = assemble_document(m)
    if strategy == "naive":
        texts = _naive(doc, size, overlap)
    elif strategy == "semantic":
        texts = _semantic(m.name, doc, max_chars)
    else:
        raise ValueError(f"unknown strategy: {strategy}")
    url = _source_url(m)
    return [
        {"id": f"{m.id}:{strategy}:{i}", "startup_id": m.id, "strategy": strategy,
         "idx": i, "text": t, "source_url": url}
        for i, t in enumerate(texts)
    ]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run --directory apps/ingest pytest tests/test_chunking.py -v`
Expected: PASS (3 passed).

- [ ] **Step 5: Commit**

```bash
git add apps/ingest/src/chunking.py apps/ingest/tests/test_chunking.py
git commit -m "feat(ingest): naive + semantic chunking strategies"
```

---

## Task 8: Wikipedia scraper

**Files:**
- Create: `apps/ingest/src/scrapers/__init__.py`
- Create: `apps/ingest/src/scrapers/wikipedia.py`
- Test: `apps/ingest/tests/test_wikipedia.py`

Use the MediaWiki REST summary API (`/api/rest_v1/page/summary/{title}`) — stable JSON, no HTML parsing, no anti-bot. A curated title list of well-known Indian startups clears the ≥50 bar deterministically. httpx responses are cached to `data/cache/` so re-runs are free.

- [ ] **Step 1: Write the failing test (parser is pure, no network)**

```python
# apps/ingest/tests/test_wikipedia.py
from src.scrapers.wikipedia import parse_summary

SAMPLE = {
    "title": "Razorpay",
    "extract": "Razorpay is an Indian fintech company that provides payment gateway services. It was founded in 2014.",
    "content_urls": {"desktop": {"page": "https://en.wikipedia.org/wiki/Razorpay"}},
}

def test_parse_summary_builds_startup():
    s = parse_summary(SAMPLE)
    assert s.name == "Razorpay"
    assert "fintech" in s.description
    assert s.source == "wikipedia"
    assert str(s.source_url).endswith("/Razorpay")

def test_parse_summary_rejects_empty_extract():
    import pytest
    with pytest.raises(ValueError):
        parse_summary({"title": "X", "extract": "", "content_urls": {"desktop": {"page": "https://e.com"}}})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run --directory apps/ingest pytest tests/test_wikipedia.py -v`
Expected: FAIL — `No module named 'src.scrapers'`.

- [ ] **Step 3: Implement the scraper**

```python
# apps/ingest/src/scrapers/__init__.py
```

```python
# apps/ingest/src/scrapers/wikipedia.py
import json
from datetime import datetime, timezone
from pathlib import Path

import httpx
from src.schema import Startup

API = "https://en.wikipedia.org/api/rest_v1/page/summary/{title}"
CACHE = Path("data/cache/wikipedia")

# Curated seed — extend freely; ~60 keeps us above the MARB floor.
TITLES = [
    "Razorpay", "Flipkart", "Zomato", "Swiggy", "Paytm", "PhonePe", "CRED_(company)",
    "Ola_Cabs", "Oyo_Rooms", "Byju's", "Unacademy", "Zerodha", "Nykaa", "Meesho",
    "Groww", "PolicyBazaar", "Dream11", "BigBasket", "Lenskart", "Delhivery",
    "Freshworks", "Postman_(software)", "Zoho_Corporation", "InMobi", "Pine_Labs",
    "Udaan_(company)", "ShareChat", "Cars24", "Spinny", "Urban_Company", "Slice_(company)",
    "Razorpay", "Vedantu", "upGrad", "PharmEasy", "1mg", "Practo", "Cult.fit",
    "BookMyShow", "MakeMyTrip", "Snapdeal", " shaadi.com", "Naukri.com", "BharatPe",
    "Mamaearth", "boAt_(brand)", "Licious", "Rebel_Foods", "Zepto_(company)",
    "Blinkit", "Ather_Energy", "Ola_Electric", "Chargebee", "Browserstack",
    "Hasura", "Razorpay",  # dupes are harmless — dedup collapses them
]

def parse_summary(data: dict) -> Startup:
    extract = (data.get("extract") or "").strip()
    if not extract:
        raise ValueError(f"empty extract for {data.get('title')}")
    page = data["content_urls"]["desktop"]["page"]
    return Startup(
        name=data["title"].replace("_", " ").split(" (")[0],
        description=extract,
        source="wikipedia",
        source_url=page,
        scraped_at=datetime.now(timezone.utc),
    )

def _fetch(title: str, client: httpx.Client) -> dict | None:
    CACHE.mkdir(parents=True, exist_ok=True)
    cached = CACHE / f"{title}.json"
    if cached.exists():
        return json.loads(cached.read_text())
    r = client.get(API.format(title=title), timeout=20,
                   headers={"User-Agent": "isra-ingest/0.1 (learning project)"})
    if r.status_code != 200:
        return None
    cached.write_text(json.dumps(r.json()))
    return r.json()

def scrape() -> list[Startup]:
    out: list[Startup] = []
    with httpx.Client(follow_redirects=True) as client:
        for title in TITLES:
            data = _fetch(title.strip(), client)
            if not data:
                continue
            try:
                out.append(parse_summary(data))
            except ValueError:
                continue
    return out
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run --directory apps/ingest pytest tests/test_wikipedia.py -v`
Expected: PASS (2 passed).

- [ ] **Step 5: Smoke-test the live scrape (writes cache)**

Run: `uv run --directory apps/ingest python -c "from src.scrapers.wikipedia import scrape; print(len(scrape()))"`
Expected: a number ≥ 50.

- [ ] **Step 6: Commit**

```bash
git add apps/ingest/src/scrapers/ apps/ingest/tests/test_wikipedia.py
git commit -m "feat(ingest): Wikipedia scraper via MediaWiki summary API + cache"
```

---

## Task 9: Loader (embed + upsert into Postgres)

**Files:**
- Create: `apps/ingest/src/load.py`
- Test: `apps/ingest/tests/test_load.py`

- [ ] **Step 1: Write the failing test (DB-gated)**

```python
# apps/ingest/tests/test_load.py
import os
import pytest
from isra_retrieval.db import connect
from isra_retrieval.migrate import apply_schema
from src.dedup import MergedStartup
from src.load import load

pytestmark = pytest.mark.skipif(not os.environ.get("RUN_DB_TESTS"), reason="needs Postgres")

def test_load_inserts_startup_and_chunks():
    apply_schema()
    with connect() as conn:
        conn.execute("TRUNCATE startups CASCADE")
    m = MergedStartup(
        id="testco", name="TestCo",
        description="TestCo is a fintech company founded in 2020 in Pune.",
        sectors=["fintech"], founded_year=2020, hq_city="Pune",
        sources=[{"source": "wikipedia", "source_url": "https://e.com/TestCo", "scraped_at": "2026-06-09T00:00:00+00:00"}],
    )
    load([m], strategies=["naive", "semantic"])
    with connect() as conn:
        n_s = conn.execute("SELECT count(*) FROM startups").fetchone()[0]
        n_c = conn.execute("SELECT count(*) FROM chunks WHERE startup_id='testco'").fetchone()[0]
        embedded = conn.execute("SELECT count(*) FROM chunks WHERE embedding IS NOT NULL").fetchone()[0]
    assert n_s == 1 and n_c >= 2 and embedded == n_c
```

- [ ] **Step 2: Run test to verify it fails**

Run: `RUN_DB_TESTS=1 uv run --directory apps/ingest pytest tests/test_load.py -v`
Expected: FAIL — `No module named 'src.load'`.

- [ ] **Step 3: Implement load.py**

```python
# apps/ingest/src/load.py
import json

from isra_retrieval.db import connect
from isra_retrieval.embeddings import embed_texts
from .chunking import chunk_startup
from .dedup import MergedStartup

def load(startups: list[MergedStartup], strategies=("naive", "semantic"),
         dsn: str | None = None) -> dict:
    all_chunks = []
    for m in startups:
        for strat in strategies:
            all_chunks.extend(chunk_startup(m, strategy=strat))

    vectors = embed_texts([c["text"] for c in all_chunks]) if all_chunks else []

    with connect(dsn) as conn:
        for m in startups:
            conn.execute(
                """INSERT INTO startups (id,name,one_liner,description,sectors,
                       founded_year,hq_city,hq_state,funding_stage,total_funding_usd,
                       founders,website,sources)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                   ON CONFLICT (id) DO UPDATE SET
                       description=EXCLUDED.description, sources=EXCLUDED.sources""",
                (m.id, m.name, m.one_liner, m.description, m.sectors, m.founded_year,
                 m.hq_city, m.hq_state, m.funding_stage, m.total_funding_usd,
                 m.founders, m.website, json.dumps(m.sources)),
            )
        for c, vec in zip(all_chunks, vectors):
            conn.execute(
                """INSERT INTO chunks (id,startup_id,strategy,idx,text,source_url,embedding)
                   VALUES (%s,%s,%s,%s,%s,%s,%s)
                   ON CONFLICT (id) DO UPDATE SET
                       text=EXCLUDED.text, embedding=EXCLUDED.embedding""",
                (c["id"], c["startup_id"], c["strategy"], c["idx"], c["text"],
                 c["source_url"], str(vec)),
            )
    return {"startups": len(startups), "chunks": len(all_chunks)}
```

Note: pgvector accepts the `str(vec)` form `'[0.1,0.2,...]'`; register the type with `from pgvector.psycopg import register_vector` only when reading vectors back (done in the retrieval plan). For writes, the string cast is sufficient.

- [ ] **Step 4: Run test to verify it passes**

Run: `RUN_DB_TESTS=1 uv run --directory apps/ingest pytest tests/test_load.py -v`
Expected: PASS (1 passed).

- [ ] **Step 5: Commit**

```bash
git add apps/ingest/src/load.py apps/ingest/tests/test_load.py
git commit -m "feat(ingest): embed chunks and upsert startups+chunks into Postgres"
```

---

## Task 10: Pipeline entrypoint + manifest

**Files:**
- Create: `apps/ingest/src/__main__.py`
- Modify: `data/` (gitignored outputs)

- [ ] **Step 1: Implement __main__.py**

```python
# apps/ingest/src/__main__.py
import json
from datetime import datetime, timezone
from pathlib import Path

from isra_retrieval.migrate import apply_schema
from .scrapers import wikipedia
from .dedup import merge_startups
from .load import load

PROCESSED = Path("data/processed")

def main() -> None:
    apply_schema()
    raw = wikipedia.scrape()                      # add more scrapers here later
    merged = merge_startups(raw)

    PROCESSED.mkdir(parents=True, exist_ok=True)
    with (PROCESSED / "startups.jsonl").open("w") as f:
        for m in merged:
            f.write(json.dumps(m.__dict__, default=str) + "\n")

    stats = load(merged)

    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "sources": {"wikipedia": len(raw)},
        "merged_startups": len(merged),
        "chunks_loaded": stats["chunks"],
    }
    (PROCESSED / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print(f"done: {len(merged)} startups, {stats['chunks']} chunks")

if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run the full pipeline**

Run: `docker compose -f infra/compose.yml up -d && bun run ingest`
Expected: prints `done: N startups, M chunks` with N ≥ 50; `data/processed/startups.jsonl` and `manifest.json` exist.

- [ ] **Step 3: Verify the corpus landed in Postgres**

Run: `docker exec isra-db psql -U isra -d isra -c "SELECT count(*) FROM startups; SELECT count(*) FROM chunks; SELECT strategy, count(*) FROM chunks GROUP BY strategy;"`
Expected: startups ≥ 50; chunks split across `naive` and `semantic`; all with embeddings.

- [ ] **Step 4: Verify re-run is idempotent and cache-only**

Run: `bun run ingest`
Expected: same counts, no duplicate rows (ON CONFLICT upserts), no network calls for Wikipedia (cache hit).

- [ ] **Step 5: Confirm data/ is gitignored**

Run: `git status --porcelain data/`
Expected: empty output (data/ ignored). If not, add `data/processed/` and `data/cache/` to `.gitignore`.

- [ ] **Step 6: Commit**

```bash
git add apps/ingest/src/__main__.py
git commit -m "feat(ingest): pipeline entrypoint scrape→dedup→chunk→embed→load + manifest"
```

---

## Definition of done (this plan)

- [ ] `docker compose -f infra/compose.yml up -d` brings up Postgres with pgvector
- [ ] `bun run ingest` produces ≥50 startups, both chunk strategies, all embedded
- [ ] `data/processed/startups.jsonl` + `manifest.json` exist; every record has a `source_url`
- [ ] Re-run is idempotent and hits cache (no network)
- [ ] All unit tests pass: `uv run --directory apps/ingest pytest` and `uv run --directory packages/retrieval pytest`
- [ ] DB-gated tests pass with `RUN_DB_TESTS=1`

**Next:** write Plan 2 (Retrieval package) — `retrieve(query, top_k, mode)` reading the `chunks` table this plan populated.

## Self-review notes

- **Spec coverage:** ingest (scrapers, schema-first, dedup, manifest, cache) ✅; chunking naive+semantic (needed for the chunking experiment in evals) ✅; single Postgres with vector + tsvector ✅; BGE embeddings local ✅. Retrieval/API/UI/evals/deploy are out of scope by design (later plans).
- **Stub corrections folded in:** dropped `rank-bm25` from retrieval (tsvector chosen); `langchain-*` (api) and `deepeval` (evals) deps are removed in Plans 3 and 4 respectively.
- **Type consistency:** `MergedStartup` fields ↔ `startups` columns ↔ `load()` INSERT match; chunk dict keys (`id, startup_id, strategy, idx, text, source_url`) ↔ `chunks` columns ↔ `Chunk` dataclass match; `EMBED_DIM=384` ↔ `vector(384)` match.
