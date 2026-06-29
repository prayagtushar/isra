"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Check, Pencil, Trash2, X } from "lucide-react";
import { useConversations } from "@/lib/store/conversations";
import { relativeTime } from "@/lib/format";
import { cn } from "@/lib/cn";

export function ConversationList({ onNavigate }: { onNavigate?: () => void }) {
  const {
    conversations,
    activeId,
    hydrated,
    selectConversation,
    deleteConversation,
    renameConversation,
  } = useConversations();
  const router = useRouter();
  const [editingId, setEditingId] = useState<string | null>(null);
  const [draft, setDraft] = useState("");

  
  
  if (!hydrated) return null;

  if (conversations.length === 0) {
    return (
      <p className="px-3 py-2 text-[12px] leading-relaxed text-faint">
        Your conversations will appear here.
      </p>
    );
  }

  const open = (id: string) => {
    selectConversation(id);
    router.push("/chat");
    onNavigate?.();
  };

  const commit = () => {
    if (editingId) renameConversation(editingId, draft);
    setEditingId(null);
  };

  return (
    <ul className="flex flex-col gap-0.5 pb-2">
      {conversations.map((c) => {
        const active = c.id === activeId;
        const title = c.title || "New chat";

        if (editingId === c.id) {
          return (
            <li key={c.id} className="flex items-center gap-1 px-0.5">
              <input
                autoFocus
                value={draft}
                onChange={(e) => setDraft(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") commit();
                  if (e.key === "Escape") setEditingId(null);
                }}
                className="h-8 min-w-0 flex-1 rounded-md border border-line bg-panel px-2 text-[13px] text-ink focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus/40"
              />
              <SmallIcon label="Save" onClick={commit}>
                <Check size={13} />
              </SmallIcon>
              <SmallIcon label="Cancel" onClick={() => setEditingId(null)}>
                <X size={13} />
              </SmallIcon>
            </li>
          );
        }

        return (
          <li key={c.id} className="group relative">
            <button
              type="button"
              onClick={() => open(c.id)}
              className={cn(
                "flex w-full items-center gap-2 rounded-md py-2 pl-3 pr-16 text-left text-[13px] transition-colors",
                active
                  ? "bg-panel-2 text-ink"
                  : "text-muted hover:bg-panel-2 hover:text-ink",
              )}
            >
              <span className="min-w-0 flex-1 truncate">{title}</span>
            </button>
            <span className="pointer-events-none absolute right-2 top-1/2 -translate-y-1/2 font-mono text-[10px] text-faint group-hover:opacity-0">
              {relativeTime(c.updatedAt)}
            </span>
            <div className="absolute right-1 top-1/2 hidden -translate-y-1/2 items-center gap-0.5 group-hover:flex">
              <SmallIcon
                label="Rename conversation"
                onClick={() => {
                  setEditingId(c.id);
                  setDraft(c.title);
                }}
              >
                <Pencil size={12} />
              </SmallIcon>
              <SmallIcon
                label="Delete conversation"
                onClick={() => {
                  if (confirm("Delete this conversation?")) deleteConversation(c.id);
                }}
              >
                <Trash2 size={12} />
              </SmallIcon>
            </div>
          </li>
        );
      })}
    </ul>
  );
}

function SmallIcon({
  children,
  label,
  onClick,
}: {
  children: React.ReactNode;
  label: string;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      aria-label={label}
      title={label}
      onClick={onClick}
      className="inline-flex h-6 w-6 items-center justify-center rounded-md text-faint transition-colors hover:bg-line-strong hover:text-ink focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus/40"
    >
      {children}
    </button>
  );
}
