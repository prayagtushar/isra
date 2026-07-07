# AGENTS.md — Indian Startup Ecosystem RAG (ISRA)

> Onboarding reference for AI coding agents working on this repo. Read this before modifying code or running commands.

---

## Project overview

ISRA is a RAG (Retrieval-Augmented Generation) system over Indian startup data. It demonstrates a hand-rolled retrieval pipeline: vector search + Postgres full-text search → RRF fusion → BGE rerank, backed by measured evals and a streaming Next.js chat UI.

```
scrapers → startups.jsonl → chunk → embed → Postgres (chunks + vectors + tsvector)
user query → /chat → retrieve(hybrid + rerank) → prompt → LLM (stream) → SSE → UI
                  └────────────── Langfuse trace ──────────────┘
golden set → evals runner → retrieval (hit@k/MRR) + LLM-judge metrics → EVALUATION.md
```

Key product decisions:

- **No LangChain.** The retrieval pipeline is intentionally hand-rolled.
- **No Ragas/DeepEval.** Evals use a hand-rolled LLM-judge — Ragas declares the LangChain family (langchain, langchain-community, langchain-openai) as core dependencies, which this repo bans.
- **One Postgres** handles both vector (`pgvector`) and keyword (`tsvector`) search.
- **Embedding model:** `BAAI/bge-small-en-v1.5` → 384-dimensional vectors.
- **Reranker:** BGE cross-encoder.
- **LLM:** hosted API (Claude / OpenAI).
- **Deployment target:** GCP Cloud Run (API), Vercel (web), Supabase (Postgres + pgvector).

---

## Repository structure

This is a **Turborepo + uv workspace** monorepo.

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
├── docs/                 # gitignored; private build plans and guides
├── infra/                # Docker compose + init scripts
├── notebooks/            # embedding experiments
├── pyproject.toml        # root uv workspace manifest
├── package.json          # root bun monorepo manifest
└── turbo.json            # Turborepo task graph
```

### `apps/api`

- **Stack:** FastAPI, SSE streaming, Langfuse, psycopg, pgvector, sentence-transformers, numpy, bcrypt.
- **Entry:** `apps/api/src/main.py`.
- **Endpoints:**
  - `GET /health`
  - `POST /search` — ranked chunks.
  - `POST /chat` — SSE streaming chat with sources + inline citations.
  - `POST /feedback` — thumbs up/down stored in Postgres.
  - `GET /startups` — paginated startup browser.
  - `POST /ingest` — SSE ingest progress.
  - `POST /auth/signup`, `POST /auth/signin`, `POST /auth/forgot-password`, `POST /auth/reset-password`, `GET /auth/me` — email/password auth.
- **CORS:** configurable via `ISRA_CORS_ORIGINS` (default `*` locally).
- **Run locally:** `bun run dev:api` → `http://localhost:8000`.

### `apps/ingest`

- **Stack:** httpx, BeautifulSoup4, lxml, Pydantic v2.
- **Goal:** scrape Indian startups, normalize into a `Startup` Pydantic model, dedupe, chunk (naive + semantic), embed, and load into Postgres.
- **Run:** `bun run ingest`.

### `apps/evals`

- **Stack:** `openai` SDK (→ OpenRouter), pydantic-settings; no external eval framework.
- **Goal:** golden-set evaluation — deterministic retrieval-mode comparison (hit@k / MRR across `vector`, `hybrid`, `hybrid+rerank`) plus reference-free generation metrics (faithfulness, answer relevancy, context precision) scored by a hand-rolled LLM-judge — outputting `EVALUATION.md` (+ `evaluation.json` sidecar).
- **Run:** `bun run eval` (add `-- --no-generation` for the retrieval-only, no-LLM path).

### `apps/web`

- **Stack:** Next.js 16.2.0, React 19.2.0, TypeScript 5.9.2, Bun, Tailwind CSS v4, GSAP, Radix Slot.
- **Public pages:** `/` landing page, `/login` sign-in, `/signup` registration, `/forgot-password`, `/reset-password`.
- **Protected pages:** `/chat`, `/search`, `/lab`, `/startups`, `/ingest`.
- **Auth:** email/password accounts backed by a `users` table in Postgres. Passwords are bcrypt-hashed by the FastAPI backend. Signed session cookies are managed by the Next.js app.
- **Run:** `bun run dev:web` → `http://localhost:3000`.

### Retrieval visualizer

- Enabled per-user via the sidebar toggle.
- Sends `trace: true` on `/chat` requests.
- FastAPI emits a `trace` SSE event with per-stage results (vector, keyword, RRF fusion, BGE rerank).
- Server-side kill switch: set `ISRA_ENABLE_RETRIEVAL_TRACE=false`.

### `packages/retrieval`

- **Stack:** pgvector, sentence-transformers, psycopg, numpy.
- **Responsibility:** shared data layer and retrieval logic.
- **Public API:** `retrieve(query, top_k, mode)` where `mode ∈ {vector, hybrid, hybrid+rerank}`.

### `packages/contracts`

- TypeScript API types used by the UI.
- **Regenerate:** `bun run gen:contracts` (requires API running on `localhost:8000`).

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
| Frontend animations | Framer Motion |
| Database | Postgres 16 + pgvector |
| Python DB driver | psycopg 3 |
| Embeddings | sentence-transformers (`BAAI/bge-small-en-v1.5`) |
| Reranker | BGE cross-encoder (sentence-transformers) |
| Scraping | httpx, BeautifulSoup4, lxml |
| Validation | Pydantic v2 |
| Evals | Hand-rolled LLM-judge (OpenRouter via `openai` SDK) |
| Observability | Langfuse Cloud |
| Local infra | Docker Compose |
| Deployment | GCP Cloud Run, Vercel, Supabase |
| Testing | pytest (Python) |

---

## Build, install, and run commands

Run all commands from the repository root unless noted.

### Install dependencies

```bash
uv sync       # Python workspace
bun install   # JS workspace
```

### Local infrastructure

```bash
docker compose -f infra/compose.yml up -d
```

Default local database URL: `postgresql://isra:isra@localhost:5432/isra`.
Set `DATABASE_URL` in production.

### Run the stack

```bash
bun run ingest    # scrape → chunk → embed → load
bun run dev:api   # FastAPI with hot reload
bun run dev:web   # Next.js dev server
```

### Type generation

```bash
bun run gen:contracts
```

### Evals

```bash
bun run eval
```

### Root package scripts

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
- Each Python package has its own `pyproject.toml`, uses `hatchling`, and declares `packages = ["src"]` (or `"src/isra_retrieval"`).
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
- `mode` must support `"vector"`, `"hybrid"`, and `"hybrid+rerank"`.

### No LangChain / DeepEval

Do not add LangChain, LangChain Community, or DeepEval dependencies.

---

## Testing strategy

- **Python:** pytest in each package.
- **Planned tests:**
  - `packages/retrieval`: RRF fusion correctness, rank ordering, mode parity against a fixture DB.
  - `apps/ingest`: schema validation, dedup/merge logic, cached-run idempotency.
  - `apps/api`: endpoint tests with mocked LLM, SSE event-sequence tests.
  - `apps/evals`: hit@k/MRR math with an injected `retrieve`, judge score-parsing/clamping, report rendering — all offline (no DB, no network).
- **Run Python tests:** `uv run --directory <package> pytest`.
- **Run all monorepo tasks:** `bun run test`.

---

## Environment variables and secrets

- `DATABASE_URL` — Postgres connection string.
- `AUTH_SECRET` — Secret used to sign web app session cookies (≥32 chars required in production).
- `ISRA_RESET_URL_BASE` — Base URL for password-reset links (default `http://localhost:3000/reset-password`).
- `ISRA_SMTP_HOST` / `ISRA_SMTP_PORT` / `ISRA_SMTP_USER` / `ISRA_SMTP_PASS` / `ISRA_SMTP_FROM` — Optional SMTP config for sending password-reset emails. Leave unset in development to log reset links.
- Langfuse keys for tracing.
- LLM API keys for `/chat` and evals.

All `.env*` files are gitignored. Do not commit secrets.

---

## Deployment

- **API:** GCP Cloud Run (ships the BGE models; ~500MB image).
- **Web:** Vercel.
- **Database:** Supabase Postgres with pgvector.

---

## Security considerations

- Do not commit `.env` files, API keys, or database credentials.
- Keep `DATABASE_URL` configurable via environment variable.
- The FastAPI server is intended to be called by the Next.js server-side route handler to avoid CORS and exposed secrets in the browser. Configure `ISRA_CORS_ORIGINS` if the API must also accept direct browser calls.
- Session cookies are signed with `AUTH_SECRET`. Use a cryptographically random secret of at least 32 characters in production and rotate it carefully — existing sessions will be invalidated.
- Password reset tokens expire after 1 hour and are single-use.
- LLM API keys must live server-side only.
- Docker Compose exposes Postgres on `localhost:5432` with weak local credentials (`isra:isra`); do not expose this to a network.

---

## Agent notes

- Use **Bun** for JS: `bun install`, `bun run <script>`.
- Use **uv** for Python: `uv sync`, `uv run`.
- Do not assume a feature exists; verify by reading the file.
- Update this `AGENTS.md` if you change the technology stack, package layout, build commands, or deployment strategy.
