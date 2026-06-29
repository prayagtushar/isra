"use client";

const EXAMPLES = [
  "What does Ola Electric do?",
  "Who founded Razorpay, and what do they build?",
  "Which fintech startups are in the dataset?",
  "Compare Zomato and Zerodha's business models.",
];

export function EmptyState({ onPick }: { onPick: (q: string) => void }) {
  return (
    <div className="flex h-full flex-col items-center justify-center px-6 py-12 text-center">
      <span className="inline-flex h-11 w-11 items-center justify-center rounded-xl bg-ink text-base">
        <svg width="22" height="22" viewBox="0 0 16 16" fill="currentColor" aria-hidden>
          <path d="M8 0.5l1.7 4.1 4.1 1.7-4.1 1.7L8 12.1 6.3 8 2.2 6.3 6.3 4.6 8 0.5z" />
          <circle cx="2.4" cy="13.4" r="1.25" />
          <circle cx="13.6" cy="13.4" r="1.25" />
        </svg>
      </span>

      <h1 className="mt-5 text-[22px] font-semibold tracking-tight text-ink">
        Indian Startup Ecosystem RAG
      </h1>
      <p className="mt-2 max-w-md text-[14px] leading-relaxed text-muted">
        Ask anything about Indian startups. Answers are grounded in retrieved
        sources and cited inline.
      </p>

      <div className="mt-8 grid w-full max-w-lg gap-2 sm:grid-cols-2">
        {EXAMPLES.map((q) => (
          <button
            key={q}
            type="button"
            onClick={() => onPick(q)}
            className="rounded-card border border-line bg-panel px-4 py-3 text-left text-[13px] leading-snug text-muted transition-colors hover:border-line-strong hover:text-ink focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus/40"
          >
            {q}
          </button>
        ))}
      </div>
    </div>
  );
}
