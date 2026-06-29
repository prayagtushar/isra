import { ExternalLink } from "lucide-react";
import { formatScore, hostname, truncate } from "@/lib/format";
import type { Source } from "@/lib/types";

export function ResultRow({
  rank,
  source,
  maxScore,
}: {
  rank: number;
  source: Source;
  maxScore: number;
}) {
  const pct = maxScore > 0 ? Math.round((source.score / maxScore) * 100) : 0;
  return (
    <li className="rounded-card border border-line bg-panel p-4">
      <div className="flex items-start gap-3">
        <span className="w-6 shrink-0 pt-0.5 font-mono text-[11px] tabular-nums text-faint">
          {String(rank).padStart(2, "0")}
        </span>
        <div className="min-w-0 flex-1">
          <div className="flex items-center justify-between gap-3">
            <span className="truncate text-[14px] font-medium text-ink">
              {source.startup_name}
            </span>
            <span
              title="Retrieval score"
              className="shrink-0 font-mono text-[10px] tabular-nums text-muted"
            >
              {formatScore(source.score)}
            </span>
          </div>
          <div className="mt-1.5 h-1 w-full overflow-hidden rounded-full bg-panel-2">
            <div className="h-full bg-ink/70" style={{ width: `${pct}%` }} />
          </div>
          <p className="mt-2 text-[13px] leading-relaxed text-muted">
            {truncate(source.text, 280)}
          </p>
          <div className="mt-2 flex items-center gap-3">
            <a
              href={source.source_url}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-1 font-mono text-[10px] uppercase tracking-[0.12em] text-faint transition-colors hover:text-ink"
            >
              <ExternalLink size={11} />
              {hostname(source.source_url)}
            </a>
            <span className="font-mono text-[10px] text-faint">
              chunk #{source.chunk_index}
            </span>
          </div>
        </div>
      </div>
    </li>
  );
}
