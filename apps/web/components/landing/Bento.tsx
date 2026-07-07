"use client";

import { Zap, Search, Quote, BarChart3, FlaskConical, Gauge } from "lucide-react";

const CARDS = [
  {
    icon: Zap,
    title: "No LangChain",
    description:
      "The entire pipeline is hand-rolled: embeddings, keyword search, RRF fusion, reranker, and prompt builder. Full control over ranking and citations.",
  },
  {
    icon: Search,
    title: "Hybrid Retrieval",
    description:
      "Vector similarity plus Postgres full-text search. Switch between vector, hybrid, and hybrid+rerank in the retrieval lab.",
  },
  {
    icon: Quote,
    title: "Inline Citations",
    description:
      "Every chunk carries its source_url. The model cites [Source N] inline, and the chat UI renders clickable citation chips back to the original page.",
  },
  {
    icon: BarChart3,
    title: "Production Observability",
    description:
      "Langfuse traces capture the full retrieval-to-generation flow for /search and /chat when keys are configured.",
  },
  {
    icon: FlaskConical,
    title: "Evaluation Suite",
    description:
      "A golden set of 12 questions measures hit@k, MRR, faithfulness, answer relevancy, and context precision with a custom LLM-judge.",
  },
  {
    icon: Gauge,
    title: "Sub-Second Responses",
    description:
      "Postgres 16 + pgvector stores vectors and text in one datastore. One database, no sync lag, fast retrieval.",
  },
];

export function Bento() {
  return (
    <section id="architecture" className="border-b border-line px-4 py-20 sm:px-6 lg:py-28">
      <div className="mx-auto max-w-7xl">
        <div className="mb-12 text-center">
          <p className="label mb-3">Why ISRA</p>
          <h2 className="text-3xl font-semibold tracking-tight sm:text-4xl">
            Built for builders who want control.
          </h2>
        </div>

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {CARDS.map((card) => {
            const Icon = card.icon;
            return (
              <div
                key={card.title}
                className="group rounded-2xl border border-line bg-panel p-6 transition-all hover:-translate-y-0.5 hover:border-[accent]/30 hover:shadow-[var(--shadow-panel)]"
              >
                <div className="mb-4 inline-flex h-9 w-9 items-center justify-center rounded-lg border border-line bg-base text-ink transition-colors group-hover:border-[accent]/30"
                >
                  <Icon size={18} />
                </div>
                <h3 className="font-semibold tracking-tight">{card.title}</h3>
                <p className="mt-1.5 text-sm text-muted">{card.description}</p>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
