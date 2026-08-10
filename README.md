# Indian Startup Ecosystem RAG (ISRA)

[![CI](https://github.com/prayagtushar/isra/actions/workflows/ci.yml/badge.svg)](https://github.com/prayagtushar/isra/actions/workflows/ci.yml)

**[Try the live demo →](https://isra.prayagtushar.xyz)** — there is no landing page and no account. The site opens straight into the chat; ask a question, or watch the pipeline resolve stage by stage in [`/lab`](https://isra.prayagtushar.xyz/lab) and browse [`/search`](https://isra.prayagtushar.xyz/search) and [`/startups`](https://isra.prayagtushar.xyz/startups). Only re-ingesting the corpus is gated, by a shared key.

A hand-rolled Retrieval-Augmented Generation (RAG) system over Indian startup data, built without LangChain so that ranking, fusion and citation behaviour stay under direct control. The full pipeline — vector search + Postgres full-text search → RRF fusion → BGE reranker → streaming generation — is implemented from primitives and measured by an evaluation harness that is also hand-rolled.

**Scope, stated honestly.** The corpus is 111 Indian startups scraped from Wikipedia's unicorn list and Y Combinator's directory — a deliberately small, verifiable dataset, not a web-scale index. At this size the interesting engineering is in *measuring* retrieval quality rather than in scaling it, and the numbers below are reported as measured, including where they contradict the design.

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
   - `/lab` streams the four pipeline stages as each completes.
   - `/search` and `/startups` provide search-explorer and startup-browser views.
   - Every retrieval surface is public, and so is `/chat` — the demo is meant to
     be used without signing up. LLM spend is bounded by a global daily ceiling
     rather than by a login. Only `/ingest` is gated, by a shared admin key,
     because it rewrites the corpus.

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
- **Retrieval lab** that streams each pipeline stage — vector search, keyword
  search, RRF fusion, cross-encoder rerank — as it finishes, with the measured
  cost of each and every chunk's movement between them. One run, not three: the
  columns are also what `vector`, `hybrid` and `hybrid+rerank` each return.
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
| `POST` | `/search/trace` | One SSE event per pipeline stage, sent as each completes |
| `POST` | `/chat` | Streaming chat over SSE |
| `POST` | `/feedback` | Store thumbs up/down feedback |
| `GET` | `/startups` | Paginated startup browser data |
| `POST` | `/ingest` | Stream ingest progress over SSE. Requires `X-ISRA-Admin-Key` |

### Abuse controls

`/chat` is open to anyone, so nothing stands between a stranger and the LLM bill
except server-side limits. There are four layers, in order of what they stop:

1. **A global daily ceiling** (`ISRA_DAILY_CHAT_LIMIT`, default 200 answers per
   UTC day) — the one that actually caps spend, because per-IP limits do nothing
   against a bot pool. When it is reached, `/chat` still returns retrieved
   sources but stops calling the model and says so. Set it to `0` to halt
   answering immediately without a redeploy; `-1` removes the cap.
2. **Per-IP rate limits** (below) — stop a single visitor hammering the demo.
3. **Bounded requests** — `question` and `query` ≤ 600 characters, ≤ 10 history
   turns, `top_k` ≤ 10, and `max_tokens=1024` on the completion, so no single
   call can run up an unbounded prompt or an unbounded rerank. The search
   endpoints enforce this too, which they did not originally: `/search` took an
   unbounded `top_k` and an empty query while this section claimed otherwise.
4. **The GCP billing budget** — the backstop, since the daily counter is held in
   process and a restart resets it.

Because the web app calls the API server-side, the API would otherwise see every
visitor as the same hosting egress IP and one person could exhaust everyone's
budget. The proxy forwards the caller's address, and the API trusts it only when
`ISRA_PROXY_SECRET` matches on both sides — **set it, or per-IP limits collapse
into a single shared bucket.**

### Rate limits

Every endpoint except `/health` is limited per client IP. Over-limit requests get
`429` with `Retry-After`; allowed requests carry `X-RateLimit-Limit` and
`X-RateLimit-Remaining`. Budgets are sized by what each call costs to serve:

| Endpoint | Limit |
|---|---|
| `/chat` | 15 / hour (spends LLM tokens) |
| `/ingest` | 3 / hour (writes, runs the scraper) |
| `/search` | 30 / min (runs the cross-encoder; `/search/trace` shares this budget) |
| `/feedback` | 20 / min |
| `/startups` | 60 / min |

Limits are held in process. That is accurate while the service runs with
`--max-instances 1`; scaling past one instance makes them per-instance and they
would need to move to a shared store.

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

Generated: 2026-08-08 · questions: 41 · top_k: 5 · judge model: `anthropic/claude-haiku-4.5`

The golden set has four question types, because a single "name the startup" phrasing
only measures one thing:

| Category | n | What it tests |
|---|---|---|
| `direct` | 12 | Plain entity lookup |
| `paraphrase` | 11 | Colloquial phrasing, misspellings, indirect description |
| `multi_hop` | 8 | Questions needing **every** one of several startups retrieved |
| `unanswerable` | 10 | Plausible questions the corpus cannot answer — the model must abstain |

### Retrieval mode comparison

Scored on answerable questions only. `hit@k` requires every expected entity on
multi-hop questions; `recall@k` gives partial credit.

| Mode | hit@5 | recall@5 | MRR |
|---|---|---|---|
| **vector** | **0.871** | **0.858** | **0.832** |
| hybrid | 0.774 | 0.777 | 0.667 |
| hybrid+rerank | 0.806 | 0.828 | 0.785 |

### By category (hit@5)

| Mode | direct | paraphrase | multi_hop |
|---|---|---|---|
| vector | 1.000 | 1.000 | 0.500 |
| hybrid | 0.833 | 1.000 | 0.375 |
| hybrid+rerank | 0.833 | 0.909 | **0.625** |

**What this changed.** On the larger question set plain vector search beats both
hybrid variants, so `vector` is now the **default retrieval mode** — the previous
default, `hybrid+rerank`, measured worse overall. The category split shows why:
RRF fusion is what costs accuracy (direct lookups drop 1.000 → 0.833) because
keyword hits displace the correct chunk on a corpus this small, and the
cross-encoder only partly recovers it. The reranker does earn its place on
multi-hop questions (0.500 → 0.625), which is the one case where re-scoring the
wider fused candidate list genuinely helps. All three modes remain selectable in
[`/lab`](https://isra.prayagtushar.xyz/lab).

Next step is tuning RRF weighting rather than removing it — the fusion is
under-tuned, not wrong in principle.

### Generation quality (`vector`, LLM-judge)

| Metric | Mean | Coverage |
|---|---|---|
| Faithfulness | 0.947 | 31/31 |
| Answer Relevancy | 0.724 | 31/31 |
| Context Precision | 0.385 | 31/31 |
| **Abstention** (unanswerable only) | **1.000** | 10/10 |

Abstention is the metric worth pointing at: on all 10 questions the corpus cannot
answer, the model declined instead of inventing a fact. Context precision remains
the weakest number and is the reason the fusion tuning above is the next task.

Eval code lives in `apps/evals`; `EVALUATION.md` and `evaluation.json` are
regenerated by `bun run eval`.

## Deployment

### Recommended target architecture

- **API:** GCP Cloud Run (ships the BGE models; image ~1.5 GB compressed, 4 vCPU
  so cross-encoder reranking returns in ~4.5s instead of ~20s).
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
| `ISRA_TRUSTED_PROXY_HOPS` | Proxy hops appended to `X-Forwarded-For` (default `1`, correct for Cloud Run). Set `0` when no proxy sits in front, or rate limits key on the proxy address instead of the caller |
| `ISRA_DAILY_CHAT_LIMIT` | Answers the open demo will generate per UTC day (default `200`). `0` stops answering; `-1` removes the cap |
| `ISRA_PROXY_SECRET` | Shared with the web app so the API can trust the forwarded caller address. **Must match `ISRA_PROXY_SECRET` on Vercel** or every visitor shares one rate-limit bucket |
| `ISRA_ADMIN_KEY` | Shared key required by `POST /ingest`. **Unset means /ingest is closed**, so a deployment that forgets it fails closed rather than open |
| `ISRA_LANGFUSE_PUBLIC_KEY` *(optional)* | Langfuse tracing |
| `ISRA_LANGFUSE_SECRET_KEY` *(optional)* | Langfuse tracing |
| `ISRA_LANGFUSE_HOST` *(optional)* | Langfuse host URL |

**Web / Vercel**

| Variable | Purpose |
|---|---|
| `API_URL` | Deployed FastAPI endpoint (required in production) |
| `ISRA_PROXY_SECRET` | Must match the API's value, so the API can trust the forwarded caller IP |

The web build fails loudly if `API_URL` is missing in production; locally it falls back to `http://localhost:8000`. There is no `AUTH_SECRET` — with accounts gone there are no sessions to sign.

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
uv sync --all-packages
uv run --directory packages/retrieval pytest
uv run --directory apps/api pytest
uv run --directory apps/ingest pytest
uv run --directory apps/evals pytest
```

### Continuous integration

[`.github/workflows/ci.yml`](.github/workflows/ci.yml) runs on every push and pull
request: the four Python suites against a real `pgvector` service container, plus
the web app's lint, unit tests and production build.

The retrieval integration tests bind to `ISRA_TEST_DATABASE_URL` (default
`postgresql://isra:isra@localhost:5432/isra`) and **deliberately ignore**
`DATABASE_URL`. They insert and delete rows, and `isra_retrieval.db` calls
`load_dotenv()` on import — so without that separation a local test run would
write to whatever database `.env` points at. They skip when no test database is
reachable.

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
