

export function formatFunding(usd?: number | null): string | null {
  if (usd == null || Number.isNaN(usd)) return null;
  if (usd >= 1e9) return `$${trim(usd / 1e9)}B`;
  if (usd >= 1e6) return `$${trim(usd / 1e6)}M`;
  if (usd >= 1e3) return `$${trim(usd / 1e3)}K`;
  return `$${Math.round(usd)}`;
}

function trim(n: number): string {
  
  return n.toFixed(1).replace(/\.0$/, "");
}

export function formatScore(score: number): string {
  return score.toFixed(3);
}

export function relativeTime(ts: number, now: number = Date.now()): string {
  const s = Math.max(0, Math.round((now - ts) / 1000));
  if (s < 45) return "just now";
  const m = Math.round(s / 60);
  if (m < 60) return `${m}m`;
  const h = Math.round(m / 60);
  if (h < 24) return `${h}h`;
  const d = Math.round(h / 24);
  if (d < 7) return `${d}d`;
  return new Date(ts).toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
  });
}

export function hostname(url: string): string {
  try {
    return new URL(url).hostname.replace(/^www\./, "");
  } catch {
    return url;
  }
}

export function truncate(text: string, max: number): string {
  const t = text.trim();
  return t.length > max ? `${t.slice(0, max - 1).trimEnd()}…` : t;
}
