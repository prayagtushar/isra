"use client";

import { useState } from "react";
import { ArrowDown, ArrowUp, Columns3, TriangleAlert } from "lucide-react";
import { search } from "@/lib/api";
import { useSettings } from "@/lib/store/settings";
import { Button } from "@/components/ui/Button";
import { TopKControl } from "@/components/ui/TopKControl";
import { Spinner } from "@/components/ui/Spinner";
import { StateView } from "@/components/ui/StateView";
import { ExampleQueries, LAB_EXAMPLES } from "@/components/ui/ExampleQueries";
import { ScoreBar } from "@/components/ui/ScoreBar";
import { channelStyle, type Channel } from "@/lib/channels";
import { formatScore, truncate } from "@/lib/format";
import { RETRIEVAL_MODES, type RetrievalMode, type Source } from "@/lib/types";
import { cn } from "@/lib/cn";

const MODE_LABEL: Record<RetrievalMode, string> = {
  vector: "Vector",
  hybrid: "Hybrid",
  "hybrid+rerank": "Hybrid + Rerank",
};

const BASELINE: Record<RetrievalMode, RetrievalMode | null> = {
  vector: null,
  hybrid: "vector",
  "hybrid+rerank": "hybrid",
};

/**
 * Column colours, which deliberately differ from modeChannel.
 *
 * Elsewhere a hybrid result is drawn in ink, because on its own it is simply the
 * ranking that came out. Here the three columns are read left to right as one
 * pipeline, and what the middle column adds over the first is the keyword
 * channel -- so amber names its contribution. Reusing modeChannel would paint
 * hybrid and rerank the same ink and make two of the three columns
 * indistinguishable, which is the one comparison this page exists to support.
 */
const COLUMN_CHANNEL: Record<RetrievalMode, Channel> = {
  vector: "vector",
  hybrid: "keyword",
  "hybrid+rerank": "rerank",
};

type Results = Record<RetrievalMode, Source[]>;

const rankMap = (list: Source[]) => {
  const m = new Map<number, number>();
  list.forEach((s, i) => m.set(s.id, i + 1));
  return m;
};

export function LabView() {
  const { topK, setTopK } = useSettings();
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<Results | null>(null);
  const [ranQuery, setRanQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Accepts an override so an example can be run in one click. Without it the
  // click would only fill the box and the visitor would still have to press Run.
  const run = async (override?: string) => {
    const q = (override ?? query).trim();
    if (!q || loading) return;
    if (override) setQuery(override);
    setLoading(true);
    setError(null);
    try {
      const [v, h, r] = await Promise.all(
        RETRIEVAL_MODES.map((m) => search({ query: q, top_k: topK, mode: m })),
      );
      setResults({
        vector: v.results,
        hybrid: h.results,
        "hybrid+rerank": r.results,
      });
      setRanQuery(q);
    } catch (e) {
      setError((e as Error).message || "Lab run failed.");
      setResults(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-full flex-col">
      <div className="border-b border-line">
        <div className="mx-auto w-full max-w-6xl space-y-3 px-4 py-4">
          <div className="flex flex-wrap gap-2">
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && run()}
              placeholder="Run one query across all three retrieval modes…"
              className="h-10 min-w-0 flex-1 rounded-[3px] border border-line bg-panel px-3 text-sm text-ink placeholder:text-faint focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus/40"
            />
            <div className="flex items-center gap-2">
              <span className="label">Top K</span>
              <TopKControl value={topK} onChange={setTopK} />
            </div>
            <Button
              variant="primary"
              onClick={() => run()}
              disabled={!query.trim() || loading}
              className="min-w-[4.5rem]"
            >
              {loading ? <Spinner /> : "Run"}
            </Button>
          </div>
          <p className="text-[12px] leading-relaxed text-muted">
            Compare how{" "}
            <span className="font-mono text-faint">vector</span> →{" "}
            <span className="font-mono text-faint">hybrid</span> →{" "}
            <span className="font-mono text-faint">rerank</span>{" "}
            reorder the same query. Arrows show each chunk&rsquo;s movement
            against the previous mode.
          </p>
        </div>
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto">
        <div className="mx-auto w-full max-w-6xl px-4 py-6">
          {loading ? (
            <div className="flex items-center justify-center gap-2 py-20 text-faint">
              <Spinner />
              <span className="font-mono text-[11px] uppercase tracking-[0.14em]">
                Running 3 modes
              </span>
            </div>
          ) : error ? (
            <StateView
              icon={TriangleAlert}
              title="Lab run failed"
              hint={error}
              action={{ label: "Try again", onClick: () => run() }}
            />
          ) : !results ? (
            <StateView
              icon={Columns3}
              title="Compare retrieval modes side by side"
              hint="Run a query to see vector, hybrid, and rerank results next to each other — and exactly how rerank reorders them."
            >
              <ExampleQueries examples={LAB_EXAMPLES} onPick={(q) => run(q)} />
            </StateView>
          ) : (
            <>
              <p className="label mb-3">Query · “{ranQuery}”</p>
              <div className="grid gap-3 md:grid-cols-3">
                {RETRIEVAL_MODES.map((m) => (
                  <ModeColumn
                    key={m}
                    mode={m}
                    list={results[m]}
                    baseline={
                      BASELINE[m] ? rankMap(results[BASELINE[m]!]) : null
                    }
                  />
                ))}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

function ModeColumn({
  mode,
  list,
  baseline,
}: {
  mode: RetrievalMode;
  list: Source[];
  baseline: Map<number, number> | null;
}) {
  const channel = COLUMN_CHANNEL[mode];
  // Per column: RRF scores sit near 0.03 while cosine and cross-encoder scores
  // sit near 0.7, so a bar scaled across all three modes would flatten hybrid to
  // nothing. Within a column the bars compare the thing worth comparing --
  // how far each result trails the one above it.
  const maxScore = list.length > 0 ? Math.max(...list.map((s) => s.score)) : 0;

  return (
    <div className="overflow-hidden rounded-card border border-line bg-panel">
      <div
        className="h-0.5 w-full"
        style={channelStyle(channel)}
        aria-hidden
      />
      <div className="flex items-center justify-between border-b border-line px-3 py-2.5">
        <span className="flex items-center gap-1.5 font-mono text-[11px] uppercase tracking-[0.12em] text-ink">
          <span
            className="inline-block h-1.5 w-1.5 rounded-full"
            style={channelStyle(channel)}
            aria-hidden
          />
          {MODE_LABEL[mode]}
        </span>
        <span className="font-mono text-[10px] text-faint">
          {baseline ? "vs prev" : "baseline"}
        </span>
      </div>
      {list.length === 0 ? (
        <p className="px-3 py-6 text-center text-[12px] text-faint">No results.</p>
      ) : (
        <ol className="divide-y divide-line">
          {list.map((s, i) => (
            <li key={`${s.id}-${i}`} className="px-3 py-2.5">
              <div className="flex items-center gap-2">
                <span className="w-5 shrink-0 font-mono text-[11px] tabular-nums text-faint">
                  {i + 1}
                </span>
                <RankDelta
                  current={i + 1}
                  previous={baseline?.get(s.id)}
                  hasBaseline={baseline != null}
                />
                <span className="min-w-0 flex-1 truncate text-[13px] font-medium text-ink">
                  {s.startup_name}
                </span>
                <span className="shrink-0 font-mono text-[10px] tabular-nums text-muted">
                  {formatScore(s.score)}
                </span>
              </div>
              <ScoreBar
                score={s.score}
                maxScore={maxScore}
                channel={channel}
                className="mt-1.5"
              />
              <p className="mt-1.5 text-[12px] leading-snug text-muted">
                {truncate(s.text, 110)}
              </p>
            </li>
          ))}
        </ol>
      )}
    </div>
  );
}

function RankDelta({
  current,
  previous,
  hasBaseline,
}: {
  current: number;
  previous?: number;
  hasBaseline: boolean;
}) {
  if (!hasBaseline) return <span className="w-9 shrink-0" />;

  // This column's effect on the ranking is the finding the lab exists to show,
  // so it is the one thing here drawn in colour. Promotions and new entries are
  // what a stage contributes; demotions are what it takes away, and recede.
  if (previous == null) {
    return (
      <span className="inline-flex w-9 shrink-0 justify-start font-mono text-[9px] uppercase tracking-wider text-keyword">
        new
      </span>
    );
  }
  const delta = previous - current;
  if (delta === 0) {
    return (
      <span className="w-9 shrink-0 font-mono text-[10px] text-faint">—</span>
    );
  }
  const up = delta > 0;
  return (
    <span
      className={cn(
        "inline-flex w-9 shrink-0 items-center gap-0.5 font-mono text-[10px] font-medium tabular-nums",
        up ? "text-accent" : "text-faint",
      )}
      title={
        up
          ? `Promoted ${delta} place${delta > 1 ? "s" : ""} by this stage`
          : `Pushed down ${Math.abs(delta)} place${Math.abs(delta) > 1 ? "s" : ""} by this stage`
      }
    >
      {up ? <ArrowUp size={10} /> : <ArrowDown size={10} />}
      {Math.abs(delta)}
    </span>
  );
}
