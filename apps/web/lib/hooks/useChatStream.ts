"use client";

import { useCallback, useRef, useState } from "react";
import { streamChat } from "@/lib/api";
import { newId } from "@/lib/id";
import { useConversations, type ChatMessage } from "@/lib/store/conversations";
import { useSettings } from "@/lib/store/settings";
import type {
  HistoryTurn,
  RetrievalMode,
  Source,
  StageName,
} from "@/lib/types";

export type StageStatus = "pending" | "running" | "done";

export interface PipelineState {
  mode: RetrievalMode;
  stages: { name: StageName; status: StageStatus }[];
}

export interface StreamingMessage {
  id: string;
  content: string;
  sources: Source[];
}

const HISTORY_LIMIT = 12;

function stageNamesFor(mode: RetrievalMode): StageName[] {
  if (mode === "vector") return ["vector", "generate"];
  if (mode === "hybrid") return ["vector", "keyword", "fusion", "generate"];
  return ["vector", "keyword", "fusion", "rerank", "generate"];
}

export function useChatStream() {
  const { active, activeId, newConversation, appendMessage } =
    useConversations();
  const { mode, topK } = useSettings();

  const [streaming, setStreaming] = useState<StreamingMessage | null>(null);
  const [pipeline, setPipeline] = useState<PipelineState | null>(null);

  const abortRef = useRef<AbortController | null>(null);
  const contentRef = useRef("");
  const sourcesRef = useRef<Source[]>([]);

  const isStreaming = streaming != null;

  const setStageStatus = useCallback((name: StageName, status: StageStatus) => {
    setPipeline((prev) =>
      prev
        ? {
            ...prev,
            stages: prev.stages.map((s) =>
              s.name === name ? { ...s, status } : s,
            ),
          }
        : prev,
    );
  }, []);

  const stop = useCallback(() => {
    abortRef.current?.abort();
  }, []);

  const send = useCallback(
    async (questionRaw: string) => {
      const question = questionRaw.trim();
      if (!question || abortRef.current) return;

      
      const priorMessages = active?.messages ?? [];
      const convId = activeId ?? newConversation();

      const history: HistoryTurn[] = priorMessages
        .filter((m) => m.content && m.status !== "error")
        .slice(-HISTORY_LIMIT)
        .map((m) => ({ role: m.role, content: m.content }));

      appendMessage(convId, {
        id: newId(),
        role: "user",
        content: question,
        status: "complete",
        createdAt: Date.now(),
      });

      const asstId = newId();
      contentRef.current = "";
      sourcesRef.current = [];
      setStreaming({ id: asstId, content: "", sources: [] });
      setPipeline({
        mode,
        stages: stageNamesFor(mode).map((name) => ({
          name,
          status: name === "generate" ? "pending" : "running",
        })),
      });

      const controller = new AbortController();
      abortRef.current = controller;
      let errorMessage: string | null = null;

      try {
        for await (const evt of streamChat(
          { question, history, top_k: topK, mode },
          controller.signal,
        )) {
          if (evt.type === "sources") {
            sourcesRef.current = evt.sources;
            setStreaming((s) => (s ? { ...s, sources: evt.sources } : s));
            
            setPipeline((prev) =>
              prev
                ? {
                    ...prev,
                    stages: prev.stages.map((st) => ({
                      ...st,
                      status: st.name === "generate" ? "running" : "done",
                    })),
                  }
                : prev,
            );
          } else if (evt.type === "token") {
            contentRef.current += evt.content;
            setStreaming((s) =>
              s ? { ...s, content: contentRef.current } : s,
            );
          } else if (evt.type === "done") {
            if (evt.answer) contentRef.current = evt.answer;
            setPipeline((prev) =>
              prev
                ? {
                    ...prev,
                    stages: prev.stages.map((st) => ({ ...st, status: "done" })),
                  }
                : prev,
            );
          } else if (evt.type === "stage") {
            setStageStatus(evt.name, evt.status === "done" ? "done" : "running");
          } else if (evt.type === "error") {
            errorMessage = evt.message || "The server reported an error.";
          }
        }
      } catch (err) {
        if (!controller.signal.aborted) {
          errorMessage =
            (err as Error)?.message || "Couldn’t reach the server.";
        }
      } finally {
        abortRef.current = null;
      }

      const finalMsg: ChatMessage = {
        id: asstId,
        role: "assistant",
        content: contentRef.current,
        sources: sourcesRef.current,
        status: errorMessage && !contentRef.current ? "error" : "complete",
        error: errorMessage ?? undefined,
        feedback: null,
        createdAt: Date.now(),
      };
      appendMessage(convId, finalMsg);

      setStreaming(null);
      setPipeline(null);
    },
    [active, activeId, appendMessage, mode, newConversation, topK, setStageStatus],
  );

  return { send, stop, streaming, pipeline, isStreaming };
}
