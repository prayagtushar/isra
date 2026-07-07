"use client";

import { useMemo } from "react";
import { motion } from "framer-motion";
import { formatScore, hostname, truncate } from "@/lib/format";
import type { RetrievalTrace, Source, TraceStage } from "@/lib/types";
import { cn } from "@/lib/cn";

const STAGE_LABELS: Record<TraceStage["name"], string> = {
  vector: "Vector search",
  keyword: "Keyword search",
  fusion: "RRF fusion",
  rerank: "BGE rerank",
};

function ScoreBar({ score, maxScore }: { score: number; maxScore: number }) {
  const pct = maxScore > 0 ? Math.round((score / maxScore) * 100) : 0;
  return (
    <div className="mt-1.5 h-1 w-full overflow-hidden rounded-full bg-panel-2">
      <motion.div
        className="h-full bg-ink/70"
        initial={{ width: 0 }}
        animate={{ width: `${pct}%` }}
        transition={{ duration: 0.6, ease: "easeOut" }}
      />
    </div>
  );
}

function StageCard({
  rank,
  source,
  maxScore,
}: {
  rank: number;
  source: Source;
  maxScore: number;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
      className="rounded-lg border border-line bg-panel p-2.5"
    >
      <div className="flex items-start gap-2">
        <span className="w-4 shrink-0 pt-0.5 font-mono text-[10px] tabular-nums text-faint">
          {String(rank).padStart(2, "0")}
        </span>
        <div className="min-w-0 flex-1">
          <div className="flex items-center justify-between gap-2">
            <span className="truncate text-[12px] font-medium text-ink">
              {source.startup_name}
            </span>
            <span className="shrink-0 font-mono text-[9px] tabular-nums text-muted">
              {formatScore(source.score)}
            </span>
          </div>
          <ScoreBar score={source.score} maxScore={maxScore} />
          <p className="mt-1.5 text-[11px] leading-relaxed text-muted">
            {truncate(source.text, 120)}
          </p>
          <div className="mt-1.5 flex items-center gap-2">
            <span className="font-mono text-[9px] text-faint">
              {hostname(source.source_url)}
            </span>
            <span className="font-mono text-[9px] text-faint">
              #{source.chunk_index}
            </span>
          </div>
        </div>
      </div>
    </motion.div>
  );
}

function StageSection({ stage, index }: { stage: TraceStage; index: number }) {
  const maxScore = useMemo(
    () => Math.max(...stage.results.map((r) => r.score), 0),
    [stage.results],
  );

  return (
    <motion.section
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: index * 0.06 }}
      className="border-b border-line last:border-b-0"
    >
      <div className="flex items-center justify-between px-3 py-2">
        <h3 className="font-mono text-[10px] uppercase tracking-[0.14em] text-ink">
          {STAGE_LABELS[stage.name]}
        </h3>
        <span className="font-mono text-[9px] tabular-nums text-faint">
          {stage.results.length}
        </span>
      </div>
      <div className="space-y-2 px-3 pb-3">
        {stage.results.map((source, i) => (
          <StageCard
            key={`${stage.name}-${source.id}-${i}`}
            rank={i + 1}
            source={source}
            maxScore={maxScore}
          />
        ))}
      </div>
    </motion.section>
  );
}

export function RetrievalTrace({
  trace,
  className,
  hideHeader = false,
}: {
  trace: RetrievalTrace;
  className?: string;
  hideHeader?: boolean;
}) {
  return (
    <div className={cn("h-full overflow-y-auto", className)}>
      {!hideHeader && (
        <div className="flex items-center justify-between border-b border-line px-3 py-2.5">
          <h2 className="font-mono text-[11px] uppercase tracking-[0.14em] text-ink">
            Retrieval trace
          </h2>
          <span className="font-mono text-[10px] tabular-nums text-faint">
            {trace.latency_ms.toFixed(1)}ms
          </span>
        </div>
      )}
      <div>
        {trace.stages.map((stage, i) => (
          <StageSection key={stage.name} stage={stage} index={i} />
        ))}
      </div>
    </div>
  );
}
