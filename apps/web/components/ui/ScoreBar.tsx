import { cn } from "@/lib/cn";
import { channelStyle, type Channel } from "@/lib/channels";

/**
 * The score meter used everywhere a ranked result appears. It is deliberately
 * the same shape in the trace, the lab and the search list so a reader learns
 * to compare bar lengths across surfaces.
 */
export function ScoreBar({
  score,
  maxScore,
  channel,
  className,
}: {
  score: number;
  maxScore: number;
  channel: Channel;
  className?: string;
}) {
  const pct = maxScore > 0 ? Math.max(2, Math.round((score / maxScore) * 100)) : 0;
  return (
    <div
      className={cn(
        "h-1.5 w-full overflow-hidden rounded-full bg-panel-2",
        className,
      )}
    >
      <div
        className="h-full rounded-full transition-[width] duration-500 ease-out"
        style={{ width: `${pct}%`, ...channelStyle(channel) }}
      />
    </div>
  );
}
