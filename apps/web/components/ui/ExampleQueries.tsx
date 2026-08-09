"use client";

/**
 * Queries a visitor can click instead of inventing one.
 *
 * An empty box asks the reader to guess what a 107-company corpus knows, and
 * most will guess wrong and conclude the retrieval is bad. Worse on /lab, whose
 * whole point is that the three modes disagree -- on most queries they return
 * the same chunks in the same order, so an arbitrary query makes the comparison
 * look pointless.
 *
 * The captions come from the eval set rather than from guesswork: hybrid fusion
 * loses direct lookups (hit@5 1.000 -> 0.833) and the cross-encoder wins
 * multi-hop questions (0.500 -> 0.625). Picking one of each shows the finding
 * the README reports, on a query where it is visible.
 */

export interface ExampleQuery {
  q: string;
  note: string;
}

export const LAB_EXAMPLES: ExampleQuery[] = [
  { q: "Which Indian startup builds electric scooters?", note: "fusion pushes the right chunk down" },
  { q: "Which companies offer payment gateways?", note: "needs several — rerank helps here" },
  { q: "cheap stock trading app", note: "no names, no keywords to match" },
];

export const SEARCH_EXAMPLES: ExampleQuery[] = [
  { q: "fintech unicorn payments", note: "crowded sector" },
  { q: "quick grocery delivery in ten minutes", note: "described, not named" },
  { q: "Flipkart valuation", note: "not in the corpus" },
];

export function ExampleQueries({
  examples,
  onPick,
}: {
  examples: ExampleQuery[];
  onPick: (q: string) => void;
}) {
  return (
    <div className="mt-6 w-full max-w-lg text-left">
      <p className="label mb-2 text-center">try one</p>
      <div className="grid gap-px border border-line bg-line">
        {examples.map(({ q, note }) => (
          <button
            key={q}
            type="button"
            onClick={() => onPick(q)}
            className="flex items-baseline justify-between gap-3 bg-panel px-3 py-2.5 text-left transition-colors hover:bg-panel-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus/40"
          >
            <span className="text-[13px] leading-snug text-ink">{q}</span>
            <span className="shrink-0 font-mono text-[10px] text-faint">{note}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
