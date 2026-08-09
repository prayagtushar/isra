"use client";

import { useEffect, useMemo, useState } from "react";
import { LayoutGrid, Search as SearchIcon, TriangleAlert } from "lucide-react";
import { fetchStartups } from "@/lib/api";
import { Spinner } from "@/components/ui/Spinner";
import { StateView } from "@/components/ui/StateView";
import { StartupCard } from "./StartupCard";
import { StartupDrawer } from "./StartupDrawer";
import { cn } from "@/lib/cn";
import type { Startup } from "@/lib/types";

// The whole corpus, which is the endpoint's ceiling. It was 100, which silently
// hid every company past the hundredth and reported the page size as the total.
const CORPUS_LIMIT = 200;

// Sectors shown before the filter is asked to expand. The corpus carries about
// seventy, more than half of them on a single company, so listing all of them
// puts a wall of chips above the results and buries the ones worth clicking.
const VISIBLE_SECTORS = 12;

export function StartupsView() {
  const [all, setAll] = useState<Startup[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [q, setQ] = useState("");
  const [sector, setSector] = useState<string | null>(null);
  const [selected, setSelected] = useState<Startup | null>(null);
  const [allSectors, setAllSectors] = useState(false);

  const load = () => {
    setLoading(true);
    setError(null);
    fetchStartups({ limit: CORPUS_LIMIT })
      .then((res) => setAll(res.startups))
      .catch((e) => setError((e as Error).message || "Couldn’t load startups."))
      .finally(() => setLoading(false));
  };

  useEffect(load, []);

  // Ordered by how many companies each sector holds, so the chips that filter
  // to something substantial come first. Alphabetical order put "Adware", which
  // matches one company, ahead of "Financial Technology", which matches twenty.
  const sectors = useMemo(() => {
    const counts = new Map<string, number>();
    for (const startup of all) {
      for (const sec of startup.sectors) counts.set(sec, (counts.get(sec) ?? 0) + 1);
    }
    return [...counts.entries()]
      .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))
      .map(([name, count]) => ({ name, count }));
  }, [all]);

  // A selected sector stays visible even when collapsed, so the active filter is
  // never a chip the reader cannot see.
  const shownSectors = useMemo(() => {
    if (allSectors) return sectors;
    const head = sectors.slice(0, VISIBLE_SECTORS);
    if (sector && !head.some((s) => s.name === sector)) {
      const active = sectors.find((s) => s.name === sector);
      if (active) return [...head, active];
    }
    return head;
  }, [sectors, allSectors, sector]);

  const filtered = useMemo(() => {
    const query = q.trim().toLowerCase();
    return all.filter((s) => {
      if (sector && !s.sectors.includes(sector)) return false;
      if (
        query &&
        !s.name.toLowerCase().includes(query) &&
        !(s.one_liner ?? "").toLowerCase().includes(query) &&
        !(s.description ?? "").toLowerCase().includes(query)
      ) {
        return false;
      }
      return true;
    });
  }, [all, q, sector]);

  return (
    <div className="flex h-full flex-col">
      <div className="border-b border-line">
        <div className="mx-auto w-full max-w-6xl space-y-3 px-4 py-4">
          <div className="relative">
            <SearchIcon
              size={15}
              className="absolute left-3 top-1/2 -translate-y-1/2 text-faint"
            />
            <input
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="Search startups by name or description…"
              className="h-10 w-full rounded-[3px] border border-line bg-panel pl-9 pr-3 text-sm text-ink placeholder:text-faint focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus/40"
            />
          </div>
          {sectors.length > 0 && (
            <div className="flex flex-wrap items-center gap-1.5">
              <SectorChip active={sector === null} onClick={() => setSector(null)}>
                All <span className="opacity-60">{all.length}</span>
              </SectorChip>
              {shownSectors.map((sec) => (
                <SectorChip
                  key={sec.name}
                  active={sector === sec.name}
                  onClick={() => setSector(sector === sec.name ? null : sec.name)}
                >
                  {sec.name} <span className="opacity-60">{sec.count}</span>
                </SectorChip>
              ))}
              {sectors.length > VISIBLE_SECTORS && (
                <button
                  type="button"
                  onClick={() => setAllSectors((open) => !open)}
                  className="rounded-full px-2.5 py-1 font-mono text-[10px] uppercase tracking-[0.1em] text-faint underline decoration-dotted underline-offset-4 transition-colors hover:text-ink focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus/40"
                >
                  {allSectors ? "Fewer sectors" : `All ${sectors.length} sectors`}
                </button>
              )}
            </div>
          )}
        </div>
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto">
        <div className="mx-auto w-full max-w-6xl px-4 py-6">
          {loading ? (
            <div className="flex items-center justify-center gap-2 py-20 text-faint">
              <Spinner />
              <span className="font-mono text-[11px] uppercase tracking-[0.14em]">
                Loading
              </span>
            </div>
          ) : error ? (
            <StateView
              icon={TriangleAlert}
              title="Couldn’t load startups"
              hint={error}
              action={{ label: "Try again", onClick: load }}
            />
          ) : filtered.length === 0 ? (
            <StateView
              icon={LayoutGrid}
              title="No startups found"
              hint={
                all.length === 0
                  ? "The corpus is empty, or the /startups endpoint isn’t available yet."
                  : "Try a different search or sector filter."
              }
            />
          ) : (
            <>
              <p className="label mb-3">
                {filtered.length} {sector ? `${sector} · ` : ""}startup
                {filtered.length > 1 ? "s" : ""}
              </p>
              <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                {filtered.map((s) => (
                  <StartupCard
                    key={s.id}
                    startup={s}
                    onClick={() => setSelected(s)}
                  />
                ))}
              </div>
            </>
          )}
        </div>
      </div>

      <StartupDrawer startup={selected} onClose={() => setSelected(null)} />
    </div>
  );
}

function SectorChip({
  children,
  active,
  onClick,
}: {
  children: React.ReactNode;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "rounded-full border px-2.5 py-1 font-mono text-[10px] uppercase tracking-[0.1em] transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus/40",
        active
          ? "border-ink bg-ink text-base"
          : "border-line text-faint hover:text-ink",
      )}
    >
      {children}
    </button>
  );
}
