"use client";

import { useEffect, useState } from "react";
import { Sidebar } from "./Sidebar";
import { Topbar } from "./Topbar";
import { CommandPalette } from "./CommandPalette";

const COLLAPSE_KEY = "isra-sidebar-collapsed";

export function AppShell({ children }: { children: React.ReactNode }) {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [collapsed, setCollapsed] = useState(false);

  useEffect(() => {
    try {
      setCollapsed(localStorage.getItem(COLLAPSE_KEY) === "1");
    } catch {
      
    }
  }, []);

  const toggleCollapsed = () =>
    setCollapsed((c) => {
      const next = !c;
      try {
        localStorage.setItem(COLLAPSE_KEY, next ? "1" : "0");
      } catch {
        
      }
      return next;
    });

  return (
    <div className="flex h-dvh overflow-hidden bg-base text-ink">
      {!collapsed && (
        <aside className="hidden w-[264px] shrink-0 border-r border-line lg:block">
          <Sidebar />
        </aside>
      )}

      {mobileOpen && (
        <div className="fixed inset-0 z-40 lg:hidden">
          <div
            className="absolute inset-0 bg-ink/25 backdrop-blur-[2px]"
            onClick={() => setMobileOpen(false)}
          />
          <aside className="absolute left-0 top-0 h-full w-[280px] border-r border-line bg-base shadow-[var(--shadow-panel)]">
            <Sidebar onNavigate={() => setMobileOpen(false)} />
          </aside>
        </div>
      )}

      <div className="flex min-w-0 flex-1 flex-col">
        <Topbar
          onMenu={() => setMobileOpen(true)}
          onToggleSidebar={toggleCollapsed}
        />
        <main className="min-h-0 flex-1 overflow-hidden">{children}</main>
        {/* The one line of framing that used to be a whole landing page. */}
        <footer className="shrink-0 border-t border-line px-4 py-2.5">
          <p className="font-mono text-[10px] leading-relaxed text-faint">
            Vector and keyword search run side by side, fuse, and rerank. Every
            answer cites the chunks it used. Reading is open; re-ingesting the
            corpus needs a key.
          </p>
        </footer>
      </div>

      <CommandPalette />
    </div>
  );
}
