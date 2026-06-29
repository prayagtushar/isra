"use client";

import { cn } from "@/lib/cn";
import { RETRIEVAL_MODES, type RetrievalMode } from "@/lib/types";

const SHORT: Record<RetrievalMode, string> = {
  vector: "Vector",
  hybrid: "Hybrid",
  "hybrid+rerank": "Rerank",
};

const FULL: Record<RetrievalMode, string> = {
  vector: "Vector search only",
  hybrid: "Vector + keyword, RRF-fused",
  "hybrid+rerank": "Hybrid, then BGE rerank",
};

export function ModeSelector({
  value,
  onChange,
  className,
}: {
  value: RetrievalMode;
  onChange: (mode: RetrievalMode) => void;
  className?: string;
}) {
  return (
    <div
      role="radiogroup"
      aria-label="Retrieval mode"
      className={cn(
        "flex gap-0.5 rounded-lg border border-line bg-panel p-0.5",
        className,
      )}
    >
      {RETRIEVAL_MODES.map((mode) => {
        const active = value === mode;
        return (
          <button
            key={mode}
            type="button"
            role="radio"
            aria-checked={active}
            title={FULL[mode]}
            onClick={() => onChange(mode)}
            className={cn(
              "flex-1 rounded-md px-2 py-1 font-mono text-[10.5px] uppercase tracking-[0.12em] transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus/40",
              active
                ? "bg-ink text-base"
                : "text-faint hover:text-ink",
            )}
          >
            {SHORT[mode]}
          </button>
        );
      })}
    </div>
  );
}
