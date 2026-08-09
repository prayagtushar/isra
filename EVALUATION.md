# Evaluation — Indian Startup Ecosystem RAG

Generated: 2026-08-08T09:17:11+00:00 · questions: 41 · top_k: 5 · model: `anthropic/claude-haiku-4.5`

## Retrieval mode comparison

Scored on answerable questions only. `hit@k` requires every expected entity for multi-hop questions; `recall@k` gives partial credit.

| Mode | hit@k | recall@k | MRR |
|------|-------|----------|-----|
| vector | 0.871 | 0.858 | 0.832 |
| hybrid | 0.774 | 0.777 | 0.667 |
| hybrid+rerank | 0.806 | 0.828 | 0.785 |

### By question category

| Mode | direct | multi_hop | paraphrase |
|------|------|------|------|
| vector | 1.000 (n=12) | 0.500 (n=8) | 1.000 (n=11) |
| hybrid | 0.833 (n=12) | 0.375 (n=8) | 1.000 (n=11) |
| hybrid+rerank | 0.833 (n=12) | 0.625 (n=8) | 0.909 (n=11) |

## Generation quality

Scored on mode `vector` with a reference-free LLM-judge.

| Metric | Mean | Coverage |
|--------|------|----------|
| Faithfulness | 0.947 | 31/31 |
| Answer Relevancy | 0.724 | 31/31 |
| Context Precision | 0.385 | 31/31 |
| Abstention (unanswerable only) | 1.000 | 10/10 |
