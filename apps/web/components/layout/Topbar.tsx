"use client";

import { usePathname } from "next/navigation";
import { Menu, PanelLeft } from "lucide-react";
import { activeNav } from "./nav";
import { ThemeToggle } from "./ThemeToggle";
import { Kbd } from "@/components/ui/Kbd";
import { useSettings } from "@/lib/store/settings";

export function Topbar({
  onMenu,
  onToggleSidebar,
}: {
  onMenu: () => void;
  onToggleSidebar: () => void;
}) {
  const pathname = usePathname();
  const active = activeNav(pathname);
  const { mode } = useSettings();

  return (
    <header className="flex h-14 shrink-0 items-center justify-between gap-3 border-b border-line px-3 sm:px-4">
      <div className="flex min-w-0 items-center gap-1.5">
        <button
          type="button"
          onClick={onMenu}
          aria-label="Open navigation"
          className="inline-flex h-8 w-8 items-center justify-center rounded-lg text-muted transition-colors hover:bg-panel-2 hover:text-ink lg:hidden"
        >
          <Menu size={16} />
        </button>
        <button
          type="button"
          onClick={onToggleSidebar}
          aria-label="Toggle sidebar"
          className="hidden h-8 w-8 items-center justify-center rounded-lg text-muted transition-colors hover:bg-panel-2 hover:text-ink lg:inline-flex"
        >
          <PanelLeft size={16} />
        </button>
        <span className="label ml-1 truncate">{active?.label ?? "ISRA"}</span>
      </div>

      <div className="flex items-center gap-2">
        <span className="hidden items-center gap-1.5 sm:flex">
          <span className="h-1.5 w-1.5 rounded-full bg-ink/40" />
          <span className="font-mono text-[10px] uppercase tracking-[0.12em] text-faint">
            {mode}
          </span>
        </span>
        <span className="hidden items-center gap-1 md:flex">
          <Kbd>⌘</Kbd>
          <Kbd>K</Kbd>
        </span>
        <ThemeToggle />
      </div>
    </header>
  );
}
