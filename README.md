# Indian Startup Ecosystem RAG

Production RAG over Indian startup data (YC · Inc42 · Wikipedia · DPIIT). Hand-rolled hybrid search (vector + keyword) with BGE reranking, a measured eval suite, Langfuse tracing, and a streaming Next.js chat UI with inline citations — deployed end-to-end.

> The interview line this earns: *"I built the retrieval pipeline myself — embed → hybrid search → RRF fusion → rerank — and I can show you the eval numbers that prove each stage helps."*

## Tech stack

Python · FastAPI (SSE streaming) · pgvector + Postgres FTS · BGE embeddings + reranker (sentence-transformers) · Ragas · Langfuse Cloud · Next.js · uv + Turborepo monorepo · Docker · Cloud Run + Vercel + Supabase

No LangChain — the retrieval pipeline is hand-rolled, because that pipeline is the point.

## Architecture at a glance

```
scrapers → startups.jsonl → chunk → embed → Postgres (chunks · vectors · tsvector)
user query → /chat → retrieve(hybrid + rerank) → prompt → LLM (stream) → SSE → UI
                 └───────────────── Langfuse trace ─────────────────┘
golden set → evals runner → Ragas metrics → EVALUATION.md
```

A single Postgres holds both halves of hybrid search: pgvector for semantic similarity and `tsvector` full-text for keyword/BM25. Results are fused with Reciprocal Rank Fusion, then reranked by a BGE cross-encoder.

See [ARCHITECTURE.md](ARCHITECTURE.md) for design decisions and [EVALUATION.md](EVALUATION.md) for retrieval/answer metrics. Full spec: [docs/superpowers/specs/2026-06-09-rag-architecture-design.md](docs/superpowers/specs/2026-06-09-rag-architecture-design.md).

## Monorepo layout

| Path | What's inside |
|------|----------------|
| [apps/ingest/](apps/ingest/) | Schema-first scrapers, chunking, embedding pipeline → `data/processed/startups.jsonl` |
| [packages/retrieval/](packages/retrieval/) | Hand-rolled pipeline: vector + FTS → RRF fusion → BGE reranker |
| [apps/api/](apps/api/) | FastAPI service: `/search`, `/chat` (SSE), `/feedback` |
| [apps/web/](apps/web/) | Next.js chat UI — progressive sources→stream rendering, inline citations |
| [packages/contracts/](packages/contracts/) | TS types generated from the Pydantic models (`bun run gen:contracts`) |
| [apps/evals/](apps/evals/) | Ragas runner, golden Q&A set, experiment tables |
| [data/](data/) | Scraped corpus + manifest (large files gitignored) |
| [infra/](infra/) | Dockerfile, compose, deploy configs |
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

## Milestones

- [ ] Scrapers running, ~50–100 startups / ~1k chunks in pgvector, naive top-k retrieval
- [ ] Hybrid search + BGE reranking, Ragas baseline, Langfuse traces
- [ ] Next.js streaming UI, deployed live URL, `ARCHITECTURE.md` + `EVALUATION.md`, demo video

## Demo links

- Live: _TBD_
- Langfuse dashboard: _TBD_
- Loom walkthrough: _TBD_

## Deployment

API container → **GCP Cloud Run** · Frontend → **Vercel** · Postgres + pgvector → **Supabase**. All free tier. The Cloud Run container ships the BGE models (sentence-transformers, ~500MB) — concurrency is set low and cold starts are expected on scale-to-zero.
