# Indian Startup Ecosystem RAG (ISRA)

**[Try the live demo →](https://isra.prayagtushar.xyz/chat)**

A production-ready, hand-rolled Retrieval-Augmented Generation (RAG) system over Indian startup data. It demonstrates a complete retrieval pipeline — vector search + Postgres full-text search → RRF fusion → BGE reranker — served through a streaming FastAPI backend and a Next.js chat UI.

```mermaid
flowchart LR
    subgraph Ingest
        A[Scrapers] --> B[Startup Pydantic model]
        B --> C[Chunker]
        C --> D[Embedder]
        D --> E[(Postgres + pgvector + tsvector)]
    end

    subgraph Retrieval
        Q[User query] --> F[Vector search]
        Q --> G[Full-text search]
        F --> H[RRF fusion]
        G --> H
        H --> I[BGE reranker]
    end

    subgraph Generation
        I --> J[Prompt builder]
        J --> K[LLM streaming]
        K --> L[Next.js UI]
    end

    E --> F
    E --> G
```

## What this is

ISRA is an end-to-end RAG application built to answer questions about the Indian startup ecosystem using curated, citeable sources. Every answer is grounded in retrieved chunks, with inline `[N]` citations pointing back to the original source URLs.

Key design decisions:

- **No LangChain.** The retrieval pipeline is intentionally hand-rolled to keep full control over ranking, fusion, and citations.
- **No Ragas / DeepEval.** Evaluations use a hand-rolled LLM-judge via the OpenRouter API to avoid pulling in the LangChain dependency family.
- **One database.** Postgres 16 with `pgvector` stores vectors and `tsvector` handles keyword search in a single datastore.
- **Streaming UX.** The `/chat` endpoint streams Server-Sent Events (SSE) so sources appear progressively while the answer is generated.
- **Observability.** Optional Langfuse tracing is wired into `/search` and `/chat`.

## Tech stack

| Layer | Technology |
|---|---|
| Python package manager | uv |
| JS package manager | Bun 1.3.14 |
| Monorepo orchestration | Turborepo |
| Web framework | FastAPI |
| Frontend | Next.js 16, React 19, TypeScript 5.9, Tailwind CSS v4 |
| Database | Postgres 16 + pgvector |
| Python DB driver | psycopg 3 |
| Embeddings | sentence-transformers (`BAAI/bge-small-en-v1.5`, 384-dim) |
| Reranker | BGE cross-encoder (sentence-transformers) |
| LLM | Hosted API via OpenRouter (Claude / OpenAI models) |
| Validation | Pydantic v2 |
| Evals | Hand-rolled LLM-judge |
| Observability | Langfuse Cloud |
| Local infrastructure | Docker Compose |
| Deployment targets | GCP Cloud Run (API), Vercel (web), Supabase (Postgres) |

## Architecture

### Data flow

1. **Ingest** (`apps/ingest`)
   - Indian startups are scraped from two sources — Wikipedia's unicorn list and Y Combinator's company directory (filtered to India) — and merged.
   - Records validate into the `Startup` Pydantic model and are deduplicated by `normalized_name`.
   - Descriptions are chunked using either naive or semantic chunking.
   - Each chunk is embedded with `BAAI/bge-small-en-v1.5` and loaded into Postgres.

2. **Retrieval** (`packages/retrieval`)
   - `retrieve(query, top_k, mode)` is the public API.
   - Supported modes: `vector`, `hybrid`, `hybrid+rerank`.
   - Vector search uses cosine similarity over `pgvector` embeddings.
   - Keyword search uses Postgres `tsvector` / `tsquery` full-text search.
   - Reciprocal Rank Fusion (RRF) combines the two ranked lists.
   - A BGE cross-encoder reranks the fused results when `hybrid+rerank` is selected.

3. **Generation** (`apps/api`)
   - `/chat` builds a prompt from the retrieved chunks and conversation history.
   - The LLM streams tokens back over SSE.
   - The final `done` event contains the full answer and a validated `citations` array.

4. **UI** (`apps/web`)
   - Next.js App Router proxies `/api/*` requests to FastAPI to keep API keys server-side.
   - `/chat` shows progressive sources, inline citations, and 👍/👎 feedback.
   - `/lab` compares retrieval modes side-by-side.
   - `/search` and `/startups` provide search-explorer and startup-browser views.

### Monorepo layout

```
.
├── apps/
│   ├── api/              # FastAPI service
│   ├── evals/            # Golden-set eval runner + LLM-judge
│   ├── ingest/           # Scrapers → chunks → embeddings → Postgres
│   └── web/              # Next.js 16 chat UI
├── packages/
│   ├── contracts/        # TypeScript types generated from OpenAPI
│   └── retrieval/        # Shared retrieval library + DB layer
├── infra/                # Docker Compose + init scripts
├── data/                 # Scraped corpus (large files gitignored)
└── notebooks/            # Embedding experiments
```

## Features

- **Hybrid retrieval** with vector + full-text search.
- **RRF fusion** and optional **BGE reranker**.
- **Streaming chat** with memory, sources, and inline citations.
- **Retrieval lab** for comparing `vector`, `hybrid`, and `hybrid+rerank` on the same query.
- **Search explorer** for inspecting ranked chunks.
- **Startup browser** with sector filters and detail drawers.
- **Feedback capture** (thumbs up/down) stored in Postgres.
- **Offline-friendly eval runner** with hit@k, MRR, and LLM-judge generation metrics.
- **Optional Langfuse tracing** for `/search` and `/chat`.

## Quickstart

### Prerequisites

- Python >= 3.11
- uv
- Bun 1.3.14+
- Docker (for local Postgres)

### Install

```bash
uv sync          # Python workspace
bun install      # JS workspace
```

### Start local infrastructure

```bash
docker compose -f infra/compose.yml up -d
```

Default local database URL: `postgresql://isra:isra@localhost:5432/isra`

### Run the stack

```bash
bun run ingest     # scrape → chunk → embed → load
bun run dev:api    # FastAPI with hot reload on http://localhost:8000
bun run dev:web    # Next.js dev server on http://localhost:3000
```

### Regenerate TypeScript contracts

```bash
bun run dev:api    # API must be running
bun run gen:contracts
```

### Run evals

```bash
bun run eval                 # full pipeline
bun run eval -- --no-generation   # retrieval metrics only
```

## API reference

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Health check with database connectivity verification |
| `POST` | `/search` | Ranked retrieval results |
| `POST` | `/chat` | Streaming chat over SSE |
| `POST` | `/feedback` | Store thumbs up/down feedback |
| `GET` | `/startups` | Paginated startup browser data |
| `POST` | `/ingest` | Stream ingest progress over SSE |

### Example: `/chat`

```bash
curl -N -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Which Indian fintech unicorn was founded in 2014?",
    "top_k": 5,
    "mode": "hybrid+rerank"
  }'
```

SSE events:

- `sources` — retrieved chunks with scores and URLs.
- `token` — streamed answer tokens.
- `done` — full answer and validated citations.
- `error` — retrieval or generation failure message.

## Evaluation results

Generated: 2026-06-27 · questions: 12 · top_k: 5

### Retrieval mode comparison

| Mode | hit@k | MRR |
|---|---|---|
| vector | 0.833 | 0.688 |
| hybrid | 0.833 | 0.729 |
| hybrid+rerank | 0.750 | 0.750 |

### Generation quality (hybrid+rerank, LLM-judge)

| Metric | Mean | Coverage |
|---|---|---|
| Faithfulness | 0.942 | 12/12 |
| Answer Relevancy | 0.783 | 12/12 |
| Context Precision | 0.183 | 12/12 |

> The low context-precision score indicates room for improvement in reranker/fusion tuning. The retrieval and generation eval code is in `apps/evals`.

## Deployment

### Recommended target architecture

- **API:** GCP Cloud Run (ships the BGE models; image ~500 MB).
- **Web:** Vercel.
- **Database:** Supabase Postgres with `pgvector` enabled.

### Required environment variables

**API / Cloud Run**

| Variable | Purpose |
|---|---|
| `DATABASE_URL` or `ISRA_DATABASE_URL` | Postgres connection string |
| `OPENROUTER_API_KEY` | LLM access for `/chat` |
| `ISRA_OPENROUTER_API_KEY` | LLM access for evals |
| `ISRA_CORS_ORIGINS` | Comma-separated allowed origins for direct API calls (default `*`) |
| `ISRA_RESET_URL_BASE` | Base URL for password-reset emails (default `http://localhost:3000/reset-password`) |
| `ISRA_SMTP_HOST` *(optional)* | SMTP server for password-reset emails |
| `ISRA_SMTP_PORT` *(optional)* | SMTP port (default `587`) |
| `ISRA_SMTP_USER` *(optional)* | SMTP username |
| `ISRA_SMTP_PASS` *(optional)* | SMTP password |
| `ISRA_SMTP_FROM` *(optional)* | From address for reset emails |
| `ISRA_LANGFUSE_PUBLIC_KEY` *(optional)* | Langfuse tracing |
| `ISRA_LANGFUSE_SECRET_KEY` *(optional)* | Langfuse tracing |
| `ISRA_LANGFUSE_HOST` *(optional)* | Langfuse host URL |

**Web / Vercel**

| Variable | Purpose |
|---|---|
| `API_URL` | Deployed FastAPI endpoint (required in production) |
| `AUTH_SECRET` | Secret used to sign session cookies (≥32 chars, required in production) |

The web build fails loudly if `API_URL` is missing in production; locally it falls back to `http://localhost:8000`.

### First deploy checklist

1. Provision Postgres and enable the `pgvector` extension.
2. Run `packages/retrieval/src/isra_retrieval/schema.sql` to create tables.
3. Deploy the API and confirm `/health` returns `ok`.
4. Run ingest once against the deployed API or directly against the database.
5. Set `API_URL` to the live API endpoint and deploy the web app.

## Development workflow

```bash
bun run dev       # turbo dev — starts API + web concurrently
bun run build     # turbo build
bun run lint      # turbo lint
bun run test      # turborepo test task (web + contracts)
```

Run Python tests individually:

```bash
uv run --directory packages/retrieval pytest
uv run --directory apps/api pytest
uv run --directory apps/ingest pytest
uv run --directory apps/evals pytest
```

## Security notes

- `.env*` files are gitignored. Do not commit secrets.
- LLM API keys live server-side only; the Next.js UI proxies all API calls.
- Docker Compose exposes Postgres on `localhost:5432` with weak local credentials; do not expose it to a network.

## Project documentation

- [`AGENTS.md`](AGENTS.md) — onboarding reference for contributors and AI coding agents.
- [`EVALUATION.md`](EVALUATION.md) — latest retrieval and generation metrics.
- [`apps/web/README.md`](apps/web/README.md) — frontend-specific notes.

## License

MIT
