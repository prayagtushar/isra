import { formatFunding } from "@/lib/format";
import type { Startup } from "@/lib/types";

export function StartupCard({
  startup,
  onClick,
}: {
  startup: Startup;
  onClick: () => void;
}) {
  const funding = formatFunding(startup.fundings);
  return (
    <button
      type="button"
      onClick={onClick}
      className="flex h-full flex-col rounded-card border border-line bg-panel p-4 text-left transition-colors hover:border-line-strong focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus/40"
    >
      <div className="flex items-start justify-between gap-2">
        <span className="text-[15px] font-semibold text-ink">
          {startup.name}
        </span>
        {funding && (
          <span className="shrink-0 font-mono text-[10px] tabular-nums text-faint">
            {funding}
          </span>
        )}
      </div>
      {startup.one_liner && (
        <p className="mt-1 line-clamp-2 text-[13px] leading-snug text-muted">
          {startup.one_liner}
        </p>
      )}
      {startup.sectors.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-1">
          {startup.sectors.slice(0, 3).map((sec) => (
            <span
              key={sec}
              className="rounded-full border border-line px-2 py-0.5 font-mono text-[9.5px] uppercase tracking-[0.1em] text-faint"
            >
              {sec}
            </span>
          ))}
        </div>
      )}
    </button>
  );
}
