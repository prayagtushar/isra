"use client";

import { TriangleAlert } from "lucide-react";
import { Answer } from "./Answer";
import { SourcesPanel } from "./SourcesPanel";
import { FeedbackBar } from "./FeedbackBar";
import { PipelineTree } from "./PipelineTree";
import { cn } from "@/lib/cn";
import type { ChatMessage } from "@/lib/store/conversations";
import type {
  PipelineState,
  StreamingMessage,
} from "@/lib/hooks/useChatStream";

function UserBubble({ content }: { content: string }) {
  return (
    <div className="flex justify-end">
      <div className="max-w-[85%] whitespace-pre-wrap rounded-2xl rounded-br-md border border-line bg-panel px-4 py-2.5 text-[15px] leading-relaxed text-ink">
        {content}
      </div>
    </div>
  );
}

function ErrorNote({ message, subtle }: { message?: string; subtle?: boolean }) {
  return (
    <div
      className={cn(
        "flex items-start gap-2 rounded-lg border border-line px-3 py-2 text-[13px] text-muted",
        subtle ? "mt-3" : "bg-panel-2",
      )}
    >
      <TriangleAlert size={14} className="mt-0.5 shrink-0 text-faint" />
      <span>
        {message || "Something went wrong while answering. Please try again."}
      </span>
    </div>
  );
}

export function Message({
  message,
  query,
  onFeedback,
}: {
  message: ChatMessage;
  query: string;
  onFeedback: (f: "up" | "down") => void;
}) {
  if (message.role === "user") return <UserBubble content={message.content} />;

  const hasError = message.status === "error";

  return (
    <div className="animate-rise-in">
      {hasError && !message.content ? (
        <ErrorNote message={message.error} />
      ) : (
        <>
          <Answer content={message.content} sources={message.sources ?? []} />
          {hasError && message.error && (
            <ErrorNote message={message.error} subtle />
          )}
          <SourcesPanel sources={message.sources ?? []} />
          {message.content && !hasError && (
            <FeedbackBar
              query={query}
              answer={message.content}
              feedback={message.feedback ?? null}
              onFeedback={onFeedback}
            />
          )}
        </>
      )}
    </div>
  );
}

export function StreamingView({
  streaming,
  pipeline,
}: {
  streaming: StreamingMessage;
  pipeline: PipelineState | null;
}) {
  return (
    <div className="animate-rise-in">
      {pipeline && <PipelineTree pipeline={pipeline} />}
      {streaming.content && (
        <div className="mt-4">
          <Answer content={streaming.content} sources={streaming.sources} />
        </div>
      )}
      {streaming.sources.length > 0 && (
        <SourcesPanel sources={streaming.sources} defaultOpen />
      )}
    </div>
  );
}
