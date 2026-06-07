## Tech stack
Python · FastAPI · pgvector (Postgres) · BGE reranker · LangChain (light) · Langfuse · Ragas · Next.js · Docker · Railway/Fly.io

## Folder layout

| Folder | What goes here |
|--------|----------------|
| [data/](data/) | Raw scraped datasets (gitignored if large) + manifest |
| [ingest/](ingest/) | Scrapers, chunking, embedding scripts |
| [retrieval/](retrieval/) | Hybrid search (BM25 + vector), reranker |
| [api/](api/) | FastAPI service: `/search`, `/chat`, `/feedback` |
| [ui/](ui/) | Next.js chat UI |
| [evals/](evals/) | Ragas + DeepEval pipelines, golden Q&A set |
| [infra/](infra/) | Dockerfile, compose, deploy configs |
| [notebooks/](notebooks/) | Exploration, ablations, chunking experiments |
