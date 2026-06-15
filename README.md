# Indian Startup Ecosystem RAG

A production-grade RAG system over Indian startup data. It demonstrates a hand-rolled retrieval pipeline: vector search + Postgres full-text search → RRF fusion → BGE rerank, backed by measured evals and a streaming Next.js chat UI.

```
scrapers → startups.jsonl → chunk → embed → Postgres (chunks + vectors + tsvector)
user query → /chat → retrieve(hybrid + rerank) → prompt → LLM (stream) → SSE → UI
                  └────────────── Langfuse trace ──────────────┘
golden set → evals runner → Ragas metrics → EVALUATION.md
```

## What this is

- **No LangChain.** The retrieval pipeline is intentionally hand-rolled.
- **One Postgres** handles both vector (`pgvector`) and keyword (`tsvector`) search.
- **Embedding model:** `BAAI/bge-small-en-v1.5` → 384-dimensional vectors.
- **Reranker:** BGE cross-encoder.
- **LLM:** hosted API (Claude / OpenAI).

## Tech stack

Python · FastAPI (SSE streaming) · pgvector + Postgres FTS · BGE embeddings + reranker (sentence-transformers) · Ragas · Langfuse Cloud · Next.js · uv + Turborepo monorepo · Docker · Cloud Run + Vercel + Supabase

## Monorepo layout

| Path | What's inside |
|------|---------------|
| [apps/ingest/](apps/ingest/) | Schema-first scrapers, chunking, embedding pipeline |
| [packages/retrieval/](packages/retrieval/) | Hand-rolled pipeline: vector + FTS → RRF fusion → BGE reranker |
| [apps/api/](apps/api/) | FastAPI service: `/search`, `/chat` (SSE), `/feedback` |
| [apps/web/](apps/web/) | Next.js chat UI — progressive sources → stream rendering, inline citations |
| [packages/contracts/](packages/contracts/) | TS types generated from the OpenAPI spec (`bun run gen:contracts`) |
| [apps/evals/](apps/evals/) | Ragas runner, golden Q&A set, experiment tables |
| [data/](data/) | Scraped corpus + manifest (large files gitignored) |
| [infra/](infra/) | Docker Compose, deploy configs |
| [notebooks/](notebooks/) | Chunking experiments, ablations |

## Quickstart

```bash
# install
uv sync                      # Python workspace (api, ingest, evals, retrieval)
bun install                  # JS workspace (web, contracts)

# bring up local Postgres (pgvector)
docker compose -f infra/compose.yml up -d

# build the corpus, then run the stack
bun run ingest               # scrape → chunk → embed into Postgres
bun run dev:api              # FastAPI on :8000
bun run dev:web              # Next.js on :3000

# evals
bun run eval                 # Ragas metrics → EVALUATION.md
```

## Project docs

- [`AGENTS.md`](AGENTS.md) — onboarding reference for contributors and AI coding agents.
- [`EVALUATION.md`](EVALUATION.md) — retrieval and answer-quality metrics (added once the eval suite runs).

## Deployment

- **API:** GCP Cloud Run (ships the BGE models; ~500MB image).
- **Web:** Vercel.
- **Database:** Supabase Postgres with pgvector.

See [`AGENTS.md`](AGENTS.md) for environment variables, security notes, and conventions.
