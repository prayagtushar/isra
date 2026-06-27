# Evaluation — Indian Startup Ecosystem RAG

Generated: 2026-06-27T07:29:04+00:00 · questions: 12 · top_k: 5 · model: `anthropic/claude-haiku-4.5`

## Retrieval mode comparison

| Mode | hit@k | MRR |
|------|-------|-----|
| vector | 0.833 | 0.688 |
| hybrid | 0.833 | 0.729 |
| hybrid+rerank | 0.750 | 0.750 |

## Generation quality

Scored on mode `hybrid+rerank` with a reference-free LLM-judge.

| Metric | Mean | Coverage |
|--------|------|----------|
| Faithfulness | 0.942 | 12/12 |
| Answer Relevancy | 0.783 | 12/12 |
| Context Precision | 0.183 | 12/12 |
