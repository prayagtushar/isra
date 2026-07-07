import Link from "next/link";
import { Logo } from "@/components/layout/Logo";

const REPO_URL = "https://github.com/prayagtushar/isra";

const LINKS = {
  Product: [
    { label: "Chat", href: "/login?redirect=/chat" },
    { label: "Retrieval Lab", href: "/login?redirect=/lab" },
    { label: "Search Explorer", href: "/login?redirect=/search" },
    { label: "Startup Browser", href: "/login?redirect=/startups" },
  ],
  "Data Sources": [
    { label: "Y Combinator", href: "https://www.ycombinator.com" },
    { label: "Wikipedia Unicorns", href: "https://en.wikipedia.org/wiki/List_of_unicorn_startup_companies" },
  ],
  "Open Source": [
    { label: "GitHub", href: REPO_URL },
    { label: "Evaluation Results", href: "/login?redirect=/lab" },
  ],
  Resources: [
    { label: "AGENTS.md", href: `${REPO_URL}/blob/main/AGENTS.md` },
    { label: "README", href: `${REPO_URL}/blob/main/README.md` },
    { label: "License MIT", href: `${REPO_URL}/blob/main/LICENSE` },
  ],
};

export function Footer() {
  return (
    <footer className="border-t border-line bg-base px-4 py-14 sm:px-6">
      <div className="mx-auto max-w-7xl">
        <div className="grid gap-10 md:grid-cols-5">
          <div className="md:col-span-2">
            <Link href="/" className="flex items-center gap-2">
              <Logo />
              <span className="font-mono text-[13px] font-semibold tracking-[0.2em]">ISRA</span>
            </Link>
            <p className="mt-4 max-w-xs text-sm text-muted">
              Indian Startup Ecosystem RAG. Hand-rolled retrieval, cited answers, no LangChain.
            </p>
            <div className="mt-6 flex items-center gap-4 text-muted">
              <a href={REPO_URL} target="_blank" rel="noopener noreferrer" aria-label="GitHub" className="hover:text-ink">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor" aria-hidden>
                  <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0 0 24 12c0-6.63-5.37-12-12-12Z" />
                </svg>
              </a>
            </div>
          </div>

          {Object.entries(LINKS).map(([group, items]) => (
            <div key={group}>
              <p className="label mb-3">{group}</p>
              <ul className="space-y-2">
                {items.map((item) => (
                  <li key={item.label}>
                    <Link
                      href={item.href}
                      target={item.href.startsWith("http") ? "_blank" : undefined}
                      rel={item.href.startsWith("http") ? "noopener noreferrer" : undefined}
                      className="text-sm text-muted transition-colors hover:text-ink"
                    >
                      {item.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="mt-12 flex flex-col items-center justify-between gap-3 border-t border-line pt-6 text-sm text-muted sm:flex-row">
          <p>© {new Date().getFullYear()} ISRA. Open source under MIT.</p>
          <p>Built with Next.js 16, FastAPI, Postgres 16 + pgvector.</p>
        </div>
      </div>
    </footer>
  );
}
