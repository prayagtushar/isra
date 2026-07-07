"use client";

import { Search, GitMerge, MessageSquare, LineChart } from "lucide-react";

const FEATURES = [
  {
    icon: Search,
    label: "Hybrid Search",
    title: "Vector ∥ keyword over Postgres",
    description:
      "Cosine similarity through pgvector runs alongside tsvector / tsquery full-text search. Two signals, one query, no Elasticsearch.",
    detail: "Modes: vector · hybrid · hybrid+rerank",
  },
  {
    icon: GitMerge,
    label: "RRF Fusion + Rerank",
    title: "Fuse, then rerank",
    description:
      "Reciprocal Rank Fusion (K = 60) combines the ranked lists, then a BGE cross-encoder reranks the fused top-k for sharper relevance.",
    detail: "Eval result: hybrid+rerank MRR 0.750",
  },
  {
    icon: MessageSquare,
    label: "Streaming Chat",
    title: "Cited answers, streamed",
    description:
      "Sources arrive first, then tokens stream over SSE. The model is instructed to cite with [Source N], and the UI links every citation back to its URL.",
    detail: "Faithfulness: 0.942 on 12 eval questions",
  },
  {
    icon: LineChart,
    label: "Observability",
    title: "Traces and a hand-rolled judge",
    description:
      "Optional Langfuse traces for /search and /chat. Evals are scored by a custom LLM-judge via OpenRouter — no Ragas, no DeepEval, no LangChain.",
    detail: "Golden set: 12 questions · top_k = 5",
  },
];

export function Features() {
  return (
    <section id="features" className="border-b border-line px-4 py-20 sm:px-6 lg:py-28">
      <div className="mx-auto max-w-7xl">
        <div className="mb-12 max-w-2xl">
          <p className="label mb-3">Product</p>
          <h2 className="text-3xl font-semibold tracking-tight sm:text-4xl">
            Everything the pipeline does, visible.
          </h2>
          <p className="mt-3 text-muted">
            A purpose-built retrieval stack for startup data: short descriptions,
            proper nouns, and sparse facts.
          </p>
        </div>

        <div className="grid gap-px bg-line md:grid-cols-2">
          {FEATURES.map((feature) => {
            const Icon = feature.icon;
            return (
              <div
                key={feature.title}
                className="group bg-base p-6 transition-colors hover:bg-panel sm:p-10"
              >
                <div className="mb-5 flex h-10 w-10 items-center justify-center rounded-xl border border-line bg-panel text-ink transition-colors group-hover:border-[accent]/30"
                >
                  <Icon size={20} />
                </div>
                <p className="label mb-2">{feature.label}</p>
                <h3 className="text-xl font-semibold tracking-tight">{feature.title}</h3>
                <p className="mt-2 text-muted">{feature.description}</p>
                <p className="mt-4 font-mono text-[12px] text-[accent]">{feature.detail}</p>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
