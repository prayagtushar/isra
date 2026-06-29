"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import {
  Plus,
  Search,
  SlidersHorizontal,
  SunMoon,
  type LucideIcon,
} from "lucide-react";
import { NAV } from "./nav";
import { Kbd } from "@/components/ui/Kbd";
import { useConversations } from "@/lib/store/conversations";
import { useSettings } from "@/lib/store/settings";
import { useTheme } from "@/lib/theme";
import { RETRIEVAL_MODES } from "@/lib/types";
import { cn } from "@/lib/cn";

interface Action {
  id: string;
  label: string;
  icon: LucideIcon;
  run: () => void;
}

export function CommandPalette() {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [index, setIndex] = useState(0);
  const router = useRouter();
  const { newConversation } = useConversations();
  const { setMode } = useSettings();
  const { toggle: toggleTheme } = useTheme();
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setOpen((o) => !o);
      } else if (e.key === "Escape") {
        setOpen(false);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  useEffect(() => {
    if (open) {
      setQuery("");
      setIndex(0);
      const t = setTimeout(() => inputRef.current?.focus(), 0);
      return () => clearTimeout(t);
    }
  }, [open]);

  const actions = useMemo<Action[]>(() => {
    const close = () => setOpen(false);
    return [
      {
        id: "new",
        label: "New chat",
        icon: Plus,
        run: () => {
          newConversation();
          router.push("/chat");
          close();
        },
      },
      ...NAV.map((n) => ({
        id: `nav-${n.href}`,
        label: `Go to ${n.label}`,
        icon: n.icon,
        run: () => {
          router.push(n.href);
          close();
        },
      })),
      ...RETRIEVAL_MODES.map((m) => ({
        id: `mode-${m}`,
        label: `Set mode: ${m}`,
        icon: SlidersHorizontal,
        run: () => {
          setMode(m);
          close();
        },
      })),
      {
        id: "theme",
        label: "Toggle theme",
        icon: SunMoon,
        run: () => {
          toggleTheme();
          close();
        },
      },
    ];
  }, [router, newConversation, setMode, toggleTheme]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return q ? actions.filter((a) => a.label.toLowerCase().includes(q)) : actions;
  }, [actions, query]);

  useEffect(() => setIndex(0), [query]);

  if (!open) return null;

  const onKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setIndex((i) => Math.min(filtered.length - 1, i + 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setIndex((i) => Math.max(0, i - 1));
    } else if (e.key === "Enter") {
      e.preventDefault();
      filtered[index]?.run();
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center p-4 pt-[12vh]"
      role="dialog"
      aria-modal="true"
      aria-label="Command palette"
    >
      <div
        className="absolute inset-0 bg-ink/25 backdrop-blur-[2px]"
        onClick={() => setOpen(false)}
      />
      <div className="relative w-full max-w-lg overflow-hidden rounded-xl border border-line bg-panel shadow-[var(--shadow-panel)] animate-rise-in">
        <div className="flex items-center gap-2 border-b border-line px-3">
          <Search size={15} className="text-faint" />
          <input
            ref={inputRef}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={onKeyDown}
            placeholder="Type a command…"
            className="h-11 w-full bg-transparent text-sm text-ink placeholder:text-faint focus:outline-none"
          />
          <Kbd>ESC</Kbd>
        </div>
        <ul className="max-h-72 overflow-y-auto p-1.5">
          {filtered.length === 0 && (
            <li className="px-3 py-6 text-center text-[13px] text-faint">
              No matching commands.
            </li>
          )}
          {filtered.map((a, i) => {
            const Icon = a.icon;
            return (
              <li key={a.id}>
                <button
                  type="button"
                  onMouseEnter={() => setIndex(i)}
                  onClick={a.run}
                  className={cn(
                    "flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-left text-[13px] transition-colors",
                    i === index ? "bg-panel-2 text-ink" : "text-muted",
                  )}
                >
                  <Icon size={15} className="text-faint" />
                  {a.label}
                </button>
              </li>
            );
          })}
        </ul>
      </div>
    </div>
  );
}
