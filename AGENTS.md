# AGENTS.md — Indian Startup Ecosystem RAG (ISRA)

> This file is written for AI coding agents. It assumes you know nothing about this project. Read it before modifying code, running commands, or generating files.

---

## Project overview

ISRA is a production-style RAG (Retrieval-Augmented Generation) system over Indian startup data. The stated goal is to demonstrate a hand-rolled retrieval pipeline — vector search + full-text search → RRF fusion → BGE rerank — backed by measured evals and a streaming Next.js chat UI.

**Current status (June 2026):** The repository is an active work in progress. The monorepo layout, local Postgres + pgvector infra, dependency wiring, and FastAPI skeleton are in place. The core ingest → retrieval → eval pipeline is still being built out. See [`docs/BUILD_TASKS.md`](docs/BUILD_TASKS.md) for the implementation checklist.

High-level flow (from the approved architecture spec):

```
scrapers → startups.jsonl → chunk → embed → Postgres (chunks + vectors + tsvector)
user query → /chat → retrieve(hybrid + rerank) → prompt → LLM (stream) → SSE → UI
                  └──────────────── Langfuse trace ─────────────────┘
golden set → evals runner → Ragas metrics → EVALUATION.md
```

Key product decisions (do not change without checking the architecture spec):

- **No LangChain** anywhere. The retrieval pipeline is intentionally hand-rolled.
- **No DeepEval**. Evals use Ragas only.
- **One Postgres** does both vector (`pgvector`) and keyword (`tsvector`) search.
- **Embedding model:** `BAAI/bge-small-en-v1.5` → 384-dimensional vectors.
- **Reranker:** BGE cross-encoder.
- **LLM:** hosted API (Claude / OpenAI); cheap model for dev, stronger model for final eval numbers.
- **Deployment target:** GCP Cloud Run (API), Vercel (web), Supabase (Postgres + pgvector).
- **Budget target:** $0/month infra, ~$5–15 total LLM eval spend.

---

## Repository structure

This is a **Turborepo + uv workspace monorepo**.

```
.
├── apps/
│   ├── api/              # FastAPI service
│   ├── evals/            # Ragas eval runner
│   ├── ingest/           # scrapers → chunks → embeddings → Postgres
│   └── web/              # Next.js 16 chat UI
├── packages/
│   ├── contracts/        # TypeScript API types generated from OpenAPI
│   └── retrieval/        # shared Python retrieval library + DB layer
├── data/                 # scraped corpus + cache (large files gitignored)
├── docs/                 # guides, build tasks, architecture specs, plans
├── infra/                # Docker compose + init scripts
├── notebooks/            # embedding experiments
├── pyproject.toml        # root uv workspace manifest
├── package.json          # root bun monorepo manifest
└── turbo.json            # Turborepo task graph
```

### `apps/api`

- **Stack:** FastAPI, SSE streaming, Langfuse, psycopg, pgvector, sentence-transformers, numpy.
- **Entry:** `apps/api/src/main.py`.
- **Current state:** only a `/health` endpoint exists. Planned endpoints:
  - `POST /search` — ranked chunks.
  - `POST /chat` — SSE streaming chat with sources + inline citations.
  - `POST /feedback` — thumbs up/down stored in Postgres.
- **Run locally:** `bun run dev:api` → `http://localhost:8000`.

### `apps/ingest`

- **Stack:** httpx, BeautifulSoup4, lxml, Pydantic v2.
- **Goal:** scrape 50–100 Indian startups, normalize into a `Startup` Pydantic model, dedupe, chunk (naive + semantic), embed, and load into Postgres.
- **Run:** `bun run ingest`.
- **Current state:** mostly empty; implementation plan is in `docs/superpowers/plans/2026-06-09-ingest-pipeline.md`.

### `apps/evals`

- **Stack:** Ragas, httpx.
- **Goal:** ~30-question golden set, two controlled experiments (retrieval mode + chunking strategy), output `EVALUATION.md`.
- **Run:** `bun run eval`.
- **Current state:** empty.

### `apps/web`

- **Stack:** Next.js 16.2.0, React 19.2.0, TypeScript 5.9.2, Bun.
- **Current state:** default Next.js app skeleton with a single landing page.
- **Planned:** streaming chat UI with progressive source cards and inline `[Source N]` citations.
- **Run:** `bun run dev:web` → `http://localhost:3000`.

### `packages/retrieval`

- **Stack:** pgvector, sentence-transformers, psycopg, numpy.
- **Responsibility:** shared data layer for the whole monorepo.
- **Planned contents:**
  - `db.py` — DSN helper + psycopg connection context manager.
  - `schema.sql` — `startups` + `chunks` tables with `vector(384)` and `tsvector` columns, HNSW + GIN indexes.
  - `embeddings.py` — lazy-loaded BGE embedder wrapper.
  - `models.py` — `Chunk` dataclass.
  - `retrieve.py` — public `retrieve(query, top_k, mode)` where `mode ∈ {vector, hybrid, hybrid+rerank}`.
- **Current state:** package config and empty `__init__.py` exist; implementation pending.

### `packages/contracts`

- **Stack:** TypeScript, `openapi-typescript`.
- **Purpose:** single source of truth for API request/response types used by the UI.
- **Regenerate:** `bun run gen:contracts` (requires API running on `localhost:8000`).
- **Current types are hand-written placeholders** for `SearchResponse`, `ChatRequest`, `ChatResponse`, `FeedbackRequest`.

---

## Technology stack

| Layer | Technology |
|-------|------------|
| Python package manager | uv |
| JS package manager | bun (1.3.14) |
| Monorepo orchestration | Turborepo |
| Python build backend | hatchling |
| Python | >=3.11 |
| Web framework | FastAPI |
| Frontend | Next.js 16, React 19, TypeScript 5.9 |
| Database | Postgres 16 + pgvector |
| Python DB driver | psycopg 3 |
| Embeddings | sentence-transformers (`BAAI/bge-small-en-v1.5`) |
| Reranker | BGE cross-encoder (sentence-transformers) |
| Scraping | httpx, BeautifulSoup4, lxml |
| Validation | Pydantic v2 |
| Evals | Ragas |
| Observability | Langfuse Cloud |
| Local infra | Docker Compose |
| Deployment | GCP Cloud Run, Vercel, Supabase |
| Testing | pytest (Python), no JS test runner yet |

---

## Build, install, and run commands

All commands below are run from the repository root unless noted.

### Install dependencies

```bash
# Python workspace (api, ingest, evals, retrieval)
uv sync

# JS workspace (web, contracts)
bun install
```

### Local infrastructure

```bash
# Start Postgres with pgvector
docker compose -f infra/compose.yml up -d

# Verify the vector extension is enabled
docker exec isra-db psql -U isra -d isra -c "SELECT extname FROM pg_extension WHERE extname='vector';"
```

Default local database URL: `postgresql://isra:isra@localhost:5432/isra`.
In production, set `DATABASE_URL`.

### Run the stack

```bash
# Run the ingest pipeline (scrape → chunk → embed → load)
bun run ingest

# Start the FastAPI server with hot reload
bun run dev:api

# Start the Next.js dev server
bun run dev:web
```

### Type generation

```bash
# Requires the API to be running on localhost:8000
bun run gen:contracts
```

### Evals

```bash
bun run eval
```

### Root package scripts (`package.json`)

| Script | Command |
|--------|---------|
| `dev` | `turbo dev` |
| `build` | `turbo build` |
| `lint` | `turbo lint` |
| `test` | `turbo test` |
| `ingest` | `uv run --directory apps/ingest python -m src` |
| `eval` | `uv run --directory apps/evals python -m src` |
| `gen:contracts` | `bun run --cwd packages/contracts gen` |
| `dev:api` | `uv run --directory apps/api uvicorn src.main:app --reload` |
| `dev:web` | `bun run --cwd apps/web dev` |

### Turborepo tasks (`turbo.json`)

- `dev` — persistent, not cached.
- `build` — depends on `^build`, outputs `.next/**` and `dist/**`.
- `lint` — no special config.
- `test` — no special config.
- `typecheck` — depends on `^build`.

---

## Code organization and conventions

### Package naming

- Python packages: `isra-retrieval`, `isra-ingest`, `isra-evals`, `isra-api`.
- JS packages: `web`, `@isra/contracts`.
- Import names:
  - `isra_retrieval.*` from `packages/retrieval/src/isra_retrieval/`
  - `src.*` from each app `src/` directory

### Python workspace

- Root `pyproject.toml` defines the uv workspace with members: `apps/api`, `apps/ingest`, `apps/evals`, `packages/retrieval`.
- Each Python package has its own `pyproject.toml`, uses `hatchling` build backend, and declares `packages = ["src"]` (or `"src/isra_retrieval"`).
- Each Python package declares `dev = ["pytest"]` dependency group.
- Shared local packages are referenced via workspace sources.

### Source layout

- `apps/<app>/src/` is the Python source root for each app.
- `packages/retrieval/src/isra_retrieval/` is the shared library source root.
- `apps/web/app/` is the Next.js App Router root.
- `packages/contracts/src/types.ts` exports the generated TypeScript contract types.

### Schema-first data model

- All scraped data must validate into the `Startup` Pydantic model in `apps/ingest/src/schema.py`.
- `normalized_name` is the deduplication key.
- Every record must have a `source_url` for citations.

### Retrieval API

- The public function is `retrieve(query, top_k, mode)`.
- `mode` must support `"vector"`, `"hybrid"`, and `"hybrid+rerank"` so evals can compare them.

### No LangChain / DeepEval

Do not add LangChain, LangChain Community, or DeepEval dependencies. The project intentionally avoids them.

---

## Testing strategy

- **Python:** pytest in each package.
- **Current state:** no test files exist yet; each package's `pyproject.toml` already declares `pytest` in the `dev` dependency group.
- **Planned tests:**
  - `packages/retrieval`: RRF fusion correctness, rank ordering, mode parity against a fixture DB.
  - `apps/ingest`: schema validation, dedup/merge logic, cached-run idempotency.
  - `apps/api`: endpoint tests with mocked LLM, SSE event-sequence tests.
- **Run Python tests:** `uv run --directory <package> pytest`.
- **Run all monorepo tasks:** `bun run test`.

---

## Environment variables and secrets

- `DATABASE_URL` — Postgres connection string. Falls back to local default.
- Langfuse keys will be needed for tracing (not yet configured).
- LLM API keys will be needed for `/chat` and evals.

All `.env*` files are gitignored. Do not commit secrets.

---

## Deployment

Target architecture:

- **API:** GCP Cloud Run (ships the BGE models; expect ~500MB image and cold starts on scale-to-zero).
- **Web:** Vercel.
- **Database:** Supabase Postgres with pgvector.

A Dockerfile for the API is planned but not yet present.

---

## Important files to read before changes

- [`README.md`](README.md) — high-level pitch and quickstart.
- [`docs/BUILD_TASKS.md`](docs/BUILD_TASKS.md) — implementation checklist, phases 0–6.
- [`docs/guides/phase-1-ingest-guide.md`](docs/guides/phase-1-ingest-guide.md) — detailed Phase 1 walkthrough.
- [`docs/superpowers/specs/2026-06-09-rag-architecture-design.md`](docs/superpowers/specs/2026-06-09-rag-architecture-design.md) — approved architecture, decisions, and build order.
- [`docs/superpowers/plans/2026-06-09-ingest-pipeline.md`](docs/superpowers/plans/2026-06-09-ingest-pipeline.md) — detailed ingest implementation plan.
- [`infra/compose.yml`](infra/compose.yml) and [`infra/init.sql`](infra/init.sql) — local database.

---

## Security considerations

- Do not commit `.env` files, API keys, or database credentials.
- Keep `DATABASE_URL` configurable via environment variable.
- The FastAPI server is intended to be called by the Next.js server-side route handler to avoid CORS and exposed secrets in the browser.
- LLM API keys must live server-side only.
- Docker Compose exposes Postgres on `localhost:5432` with weak local credentials (`isra:isra`); do not expose this to a network.

---

## Notes for agents

- The project uses **Bun** as the JS package manager, not npm/pnpm/yarn. Use `bun install` and `bun run <script>`.
- Use **uv** for all Python tasks. Prefer `uv run` over manual virtualenv activation.
- Many planned modules are currently empty stubs. Do not assume a feature exists; verify by reading the file.
- When implementing ingest/retrieval/eval tasks, follow the existing plans in `docs/superpowers/` and the checklist in `docs/BUILD_TASKS.md`.
- Update this `AGENTS.md` if you change the technology stack, package layout, build commands, or deployment strategy.
