"use client";

import { useState } from "react";
import { Plus, Minus } from "lucide-react";

const ITEMS = [
  {
    question: "How does hybrid search work?",
    answer:
      "ISRA runs pgvector cosine-similarity search and Postgres tsvector full-text search in parallel, fuses the rankings with Reciprocal Rank Fusion (K = 60), then reranks the fused results with a BGE cross-encoder when you select hybrid+rerank.",
  },
  {
    question: "What data sources are included?",
    answer:
      "Currently Y Combinator's company directory (filtered to India) and Wikipedia's list of Indian unicorns. Records are deduplicated by normalized_name and stored in the Startup Pydantic model.",
  },
  {
    question: "Can I self-host ISRA?",
    answer:
      "Yes. The stack is Docker Compose-friendly: Postgres 16 + pgvector, FastAPI, and the Next.js frontend. Deployment targets are GCP Cloud Run for the API, Vercel for the web app, and Supabase for Postgres.",
  },
  {
    question: "How are citations generated?",
    answer:
      "Every retrieved chunk stores a source_url. The chat prompt instructs the model to cite using [Source N]. The UI parses those markers and renders clickable citation chips.",
  },
  {
    question: "What embedding and reranker models are used?",
    answer:
      "Both use the BGE family via sentence-transformers: BAAI/bge-small-en-v1.5 for 384-dimensional embeddings and a BGE cross-encoder for reranking.",
  },
  {
    question: "How is the project evaluated?",
    answer:
      "A 12-question golden set measures hit@k and MRR across vector, hybrid, and hybrid+rerank. Generation is scored by a hand-rolled LLM-judge via OpenRouter for faithfulness, answer relevancy, and context precision.",
  },
  {
    question: "How do I contribute?",
    answer:
      "ISRA is open source under MIT. Open an issue or pull request on GitHub — evals, scrapers, frontend views, and retrieval tuning are all welcome.",
  },
];

export function FAQ() {
  const [open, setOpen] = useState<number | null>(null);

  return (
    <section className="border-b border-line px-4 py-20 sm:px-6 lg:py-28">
      <div className="mx-auto max-w-3xl">
        <p className="label mb-3 text-center">FAQ</p>
        <h2 className="mb-10 text-center text-3xl font-semibold tracking-tight sm:text-4xl">
          Frequently asked questions
        </h2>

        <div className="space-y-3">
          {ITEMS.map((item, i) => {
            const isOpen = open === i;
            return (
              <div
                key={item.question}
                className="rounded-2xl border border-line bg-panel p-1"
              >
                <button
                  type="button"
                  onClick={() => setOpen(isOpen ? null : i)}
                  className="flex w-full items-center justify-between gap-4 rounded-xl px-4 py-4 text-left transition-colors hover:bg-base"
                >
                  <span className="font-medium">{item.question}</span>
                  <span className="shrink-0 text-faint">
                    {isOpen ? <Minus size={16} /> : <Plus size={16} />}
                  </span>
                </button>
                {isOpen && (
                  <div className="px-4 pb-4 text-sm text-muted">
                    {item.answer}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
