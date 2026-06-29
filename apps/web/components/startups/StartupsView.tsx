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

export function StartupsView() {
  const [all, setAll] = useState<Startup[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [q, setQ] = useState("");
  const [sector, setSector] = useState<string | null>(null);
  const [selected, setSelected] = useState<Startup | null>(null);

  const load = () => {
    setLoading(true);
    setError(null);
    fetchStartups({ limit: 100 })
      .then((res) => setAll(res.startups))
      .catch((e) => setError((e as Error).message || "Couldn’t load startups."))
      .finally(() => setLoading(false));
  };

  useEffect(load, []);

  const sectors = useMemo(
    () => Array.from(new Set(all.flatMap((s) => s.sectors))).sort(),
    [all],
  );

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
              className="h-10 w-full rounded-lg border border-line bg-panel pl-9 pr-3 text-sm text-ink placeholder:text-faint focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus/40"
            />
          </div>
          {sectors.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              <SectorChip active={sector === null} onClick={() => setSector(null)}>
                All
              </SectorChip>
              {sectors.map((sec) => (
                <SectorChip
                  key={sec}
                  active={sector === sec}
                  onClick={() => setSector(sector === sec ? null : sec)}
                >
                  {sec}
                </SectorChip>
              ))}
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
