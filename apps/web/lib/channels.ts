import type { CSSProperties } from "react";
import type { RetrievalMode, TraceStage } from "@/lib/types";

/**
 * Colour is load-bearing here: each retrieval channel owns a hue, so a result's
 * bar tells you which search produced it without reading a label. Fusion is the
 * only blended case, because RRF genuinely is the two lists combined.
 */
export type Channel = "vector" | "keyword" | "fusion" | "rerank";

export const CHANNEL_LABELS: Record<Channel, string> = {
  vector: "Vector search",
  keyword: "Keyword search",
  fusion: "RRF fusion",
  rerank: "BGE rerank",
};

export const CHANNEL_HINTS: Record<Channel, string> = {
  vector: "Cosine similarity over pgvector embeddings",
  keyword: "Postgres full-text search over tsvector",
  fusion: "Reciprocal rank fusion of both lists",
  rerank: "Cross-encoder scoring of the fused list",
};

/**
 * Inline style that paints a bar or dot for the channel.
 *
 * Longhand `backgroundColor` on purpose: React serialises the `background`
 * shorthand differently on the server and the client, which trips a hydration
 * mismatch that React explicitly does not patch up — the element ends up with
 * no background at all.
 */
export function channelStyle(channel: Channel): CSSProperties {
  // Fusion and rerank are both "the resolved ranking", drawn in ink.
  const token = channel === "fusion" ? "rerank" : channel;
  return { backgroundColor: `var(--${token})` };
}

export function stageChannel(stage: TraceStage["name"]): Channel {
  return stage as Channel;
}

/** The channel whose scores a plain result list is showing. */
export function modeChannel(mode: RetrievalMode): Channel {
  if (mode === "vector") return "vector";
  if (mode === "hybrid") return "fusion";
  return "rerank";
}
