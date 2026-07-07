"use client";

import Link from "next/link";
import { useState } from "react";
import { Menu, X } from "lucide-react";
import { Logo } from "@/components/layout/Logo";
import { ThemeToggle } from "@/components/layout/ThemeToggle";
import { Button } from "@/components/ui/Button";

const LINKS = [
  { href: "#features", label: "Product" },
  { href: "#architecture", label: "Architecture" },
  { href: "#data-sources", label: "Data Sources" },
  { href: "https://github.com/prayagtushar/isra", label: "GitHub", external: true },
];

export function Navbar() {
  const [open, setOpen] = useState(false);

  return (
    <header className="fixed top-0 z-50 w-full border-b border-line bg-base/80 backdrop-blur-md">
      <nav className="mx-auto flex h-14 max-w-7xl items-center justify-between px-4 sm:px-6">
        <Link href="/" className="flex items-center gap-2">
          <Logo />
          <span className="font-mono text-[13px] font-semibold tracking-[0.2em]">ISRA</span>
        </Link>

        <div className="hidden items-center gap-6 md:flex">
          {LINKS.map((link) => (
            <Link
              key={link.label}
              href={link.href}
              target={link.external ? "_blank" : undefined}
              rel={link.external ? "noopener noreferrer" : undefined}
              className="text-sm text-muted transition-colors hover:text-ink"
            >
              {link.label}
            </Link>
          ))}
        </div>

        <div className="hidden items-center gap-3 md:flex">
          <ThemeToggle />
          <Button variant="primary" size="sm" asChild className="rounded-lg">
            <Link href="/login?redirect=/chat">Try the demo</Link>
          </Button>
        </div>

        <button
          type="button"
          className="inline-flex h-9 w-9 items-center justify-center rounded-lg text-muted hover:bg-panel-2 hover:text-ink md:hidden"
          onClick={() => setOpen((o) => !o)}
          aria-label="Toggle menu"
        >
          {open ? <X size={18} /> : <Menu size={18} />}
        </button>
      </nav>

      {open && (
        <div className="border-b border-line bg-base px-4 pb-4 md:hidden">
          <div className="flex flex-col gap-2 pt-2">
            {LINKS.map((link) => (
              <Link
                key={link.label}
                href={link.href}
                target={link.external ? "_blank" : undefined}
                rel={link.external ? "noopener noreferrer" : undefined}
                className="rounded-lg px-3 py-2 text-sm text-muted hover:bg-panel-2 hover:text-ink"
                onClick={() => setOpen(false)}
              >
                {link.label}
              </Link>
            ))}
            <div className="flex items-center justify-between px-3 pt-2">
              <ThemeToggle />
              <Button variant="primary" size="sm" asChild className="rounded-lg">
                <Link href="/login?redirect=/chat">Try the demo</Link>
              </Button>
            </div>
          </div>
        </div>
      )}
    </header>
  );
}
