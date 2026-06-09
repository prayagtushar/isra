# Indian Startup Ecosystem RAG — Architecture Design (Approach A, amended)

**Date:** 2026-06-09
**Status:** Approved direction; supersedes the stale README tech-stack/layout section.
**Context:** Project 1 of the 90-day AI Product Engineer plan (`ai-eng-private`). This is MARB week — live demo URL, streaming UI with citations, `EVALUATION.md`, `ARCHITECTURE.md`, Langfuse traces, and Loom due **Sunday Jun 14, 2026**. Applications start Monday Jun 15.

## Goals

- Hit every MARB checklist item with the leanest credible system.
- Maximize interview signal: hand-rolled retrieval (hybrid + rerank), measured evals, observable traces — not framework gluing.
- $0/month infra; ~$5–15 total LLM eval spend.

## Non-goals (post-launch polish, each a LinkedIn post)

- Corpus beyond 50–100 startups / ~1k chunks
- DeepEval / custom LLM-as-judge metrics
- 50+ question eval suite, top-K sweeps, prompt tuning experiments
- Redis caching, prompt versioning
- LangChain anywhere

## Decisions

| Decision | Choice | Why |
|---|---|---|
| Repo structure | Keep existing Turborepo monorepo (`apps/{api,ingest,evals,web}`, `packages/{retrieval,contracts}`), uv workspace for Python, bun for TS | Already built and committed; better than README's flat layout; demonstrates production engineering |
| Vector + keyword store | **One Postgres**: pgvector for vectors, `tsvector` FTS for BM25-style keyword search | Single store does both halves of hybrid search at this scale; "why pgvector over Pinecone" is an interview talking point |
| Orchestration | **No LangChain.** Hand-rolled pipeline in `packages/retrieval` | The pipeline IS the lesson and the interview story (~200 lines: embed → vector + FTS → RRF fusion → BGE rerank → prompt assembly) |
| Embeddings | BGE (sentence-transformers), local MPS in dev, CPU in the Cloud Run container | Free, pairs with BGE reranker, plan already budgets ~500MB memory for it |
| Reranker | BGE reranker (cross-encoder), same serving story | ~19% context-precision gain is the target headline metric |
| Generation LLM | Hosted API (Claude / OpenAI). Cheap model (Haiku / 4o-mini) during dev and as dev judge; strong model (Sonnet / 4o) only for final `EVALUATION.md` numbers | Cost discipline per week-04 plan |
| Evals | **Ragas only** for MARB: ~30-Q golden set (factual / comparison / multi-hop / negative), 4 core metrics, exactly 2 experiments | DeepEval explicitly deferred to post-launch by the plan |
| Observability | **Langfuse Cloud** (free tier, SDK key only) | Self-hosted v3 needs ClickHouse + Redis + MinIO — wrong complexity for this week; traces must exist by Loom-recording time |
| Deploy | API → **GCP Cloud Run**, UI → **Vercel**, Postgres → **Supabase** (pgvector preinstalled) | Plan's stack, all free tier; replaces README's Railway/Fly |
| Corpus | 50–100 startups via schema-first ingest playbook (YC, Wikipedia, Inc42, DPIIT); 1.5hr/source hard timebox | Scraping is plumbing; signal is retrieval + evals |

## Components

### `apps/ingest` — scrapers → corpus
Schema-first per the existing ingest playbook (`ai-eng-private/02-projects/project-1-rag-indian-startups/ingest/README.md`): Pydantic `Startup` schema is the only shape that leaves ingest. Per-source scrapers fill it; dedup by `normalized_name`; HTTP caching so re-runs are free. Outputs `data/processed/startups.jsonl` (≥50 records, every record with `source_url`) + `manifest.json`. Then chunking (naive + semantic variants — both needed for the chunking experiment) and embedding into Postgres.

### `packages/retrieval` — the hand-rolled pipeline
Pure Python library, no web framework. Public interface: `retrieve(query, top_k, mode)` where mode ∈ {vector, hybrid, hybrid+rerank} — modes are first-class because the retrieval experiment compares them. Internals: query embedding → parallel pgvector cosine + FTS queries → RRF fusion → BGE cross-encoder rerank → ranked chunks with provenance. Testable against a local DB without the API.

### `apps/api` — FastAPI
- `POST /search` — retrieval only, returns ranked chunks + scores (debug/demo surface)
- `POST /chat` — **SSE streaming**: emits sources event first, then token stream, then done event with citation map. Langfuse tracing spans the whole request (retrieval timing, rerank timing, LLM call)
- `POST /feedback` — thumbs up/down per answer, stored in Postgres
- Health endpoint for Cloud Run.

### `apps/web` — Next.js chat UI
Progressive rendering: "Searching sources…" immediately → source cards → streamed answer with inline `[Source N]` badges that highlight their card on click. Confidence badge (green/yellow/red from retrieval scores), empty state with 3 one-click sample queries. All API calls proxied through a Next.js route handler (server-side) to avoid the Vercel↔Cloud Run CORS pitfall.

### `packages/contracts`
TS types for API payloads (search/chat/feedback request-response, SSE event shapes), generated from the Pydantic models via the existing `gen:contracts` script. Single source of truth for the UI.

### `apps/evals`
Golden set (~30 Q&A, mixed types) as versioned JSONL. Ragas runner computing faithfulness, answer relevancy, context precision, context recall. Two experiments, one variable at a time:
1. Retrieval mode: vector vs hybrid vs hybrid+rerank
2. Chunking: naive vs semantic
Results land in `EVALUATION.md` (TL;DR, methodology, tables, analysis, final config, limitations).

## Data flow

```
scrapers → startups.jsonl → chunker → embedder → Postgres (chunks + vectors + tsvector)
user query → /chat → retrieve(hybrid+rerank) → prompt + chunks → LLM (stream) → SSE → UI
                └────────────── Langfuse trace ──────────────┘
feedback → /feedback → Postgres
golden set → evals runner → retrieve(mode=X) + LLM → Ragas → EVALUATION.md
```

## Error handling

- Ingest: per-source failures are logged and skipped, never abort the run; validation failures fail loudly per record; manifest records error counts.
- API: retrieval failure → 503 with a friendly SSE error event the UI renders; LLM stream interruption → partial-answer event + retry affordance in UI.
- Empty/low-confidence retrieval → answer refuses gracefully with red confidence badge (this is also a negative-question eval case).

## Testing

- `packages/retrieval`: unit tests for RRF fusion and rank-ordering against a fixture DB; mode parity tests (hybrid ⊇ signals of vector-only).
- `apps/ingest`: schema validator tests; dedup/merge tests on fixture records; cached-run test (second run makes zero network calls).
- `apps/api`: endpoint tests with mocked LLM (plan: "mock the LLM while debugging the pipeline"); SSE event-sequence test.
- Evals themselves are the system-level test.

## Build order (5 days to MARB)

1. **Tue:** ingest vertical slice → ≥50 startups in `startups.jsonl`; chunk + embed into local Postgres
2. **Wed:** retrieval package (vector → hybrid → rerank) + `/search`; Langfuse wired; start Ragas baseline
3. **Thu:** 2 experiments + `EVALUATION.md`; `/chat` SSE endpoint
4. **Fri:** Next.js UI (streaming + citations); deploy Cloud Run + Supabase + Vercel; `ARCHITECTURE.md`
5. **Sat/Sun:** materials (resume, LinkedIn, Loom, target list) per week-04 plan — outside this repo

Slippage rule: if Thursday ends without eval numbers, cut the chunking experiment (keep retrieval-mode experiment) — one credible experiment beats two rushed ones; the second becomes next week's post.

## README update

Rewrite the project README to match this design: monorepo layout table, Cloud Run/Vercel/Supabase deploy stack, no LangChain/DeepEval/Railway mentions, link to `ARCHITECTURE.md` + `EVALUATION.md` once they exist.
