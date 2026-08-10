"use client";

import { useCallback, useRef, useState } from "react";

import { parseSSE } from "@/lib/sse";
import type { LiveStage, RetrievalMode, TraceEvent } from "@/lib/types";

/**
 * Runs one query and collects the pipeline stages as they arrive.
 *
 * Stages are appended in the order the server finishes them, which is the order
 * the pipeline actually runs. Nothing here reorders or delays them: the reveal a
 * reader sees is the real timing, so the gap before the rerank column is the
 * cross-encoder's cost rather than an animation pretending to be one.
 */
export function useRetrievalStages() {
  const [stages, setStages] = useState<LiveStage[]>([]);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [ranQuery, setRanQuery] = useState("");
  const abortRef = useRef<AbortController | null>(null);

  const run = useCallback(
    async (query: string, topK: number, mode: RetrievalMode) => {
      const q = query.trim();
      if (!q) return;

      // A second run while one is in flight would interleave two pipelines into
      // one column set.
      abortRef.current?.abort();
      const controller = new AbortController();
      abortRef.current = controller;

      setStages([]);
      setError(null);
      setRanQuery(q);
      setRunning(true);

      try {
        const res = await fetch("/api/search/trace", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ query: q, top_k: topK, mode }),
          signal: controller.signal,
        });

        if (!res.ok || !res.body) {
          const text = await res.text().catch(() => "");
          let message = `Retrieval failed (${res.status})`;
          try {
            message = (JSON.parse(text) as { error?: string }).error ?? message;
          } catch {
            if (text) message = text;
          }
          throw new Error(message);
        }

        for await (const evt of parseSSE<TraceEvent>(res.body)) {
          if (evt.type === "stage") {
            const { type: _type, ...stage } = evt;
            setStages((prev) => [...prev, stage]);
          } else if (evt.type === "error") {
            setError(evt.message);
          }
        }
      } catch (e) {
        // An abort is this hook superseding itself, not a failure to report.
        if ((e as Error).name !== "AbortError") {
          setError((e as Error).message || "Retrieval failed.");
        }
      } finally {
        if (abortRef.current === controller) setRunning(false);
      }
    },
    [],
  );

  return { stages, running, error, ranQuery, run };
}
