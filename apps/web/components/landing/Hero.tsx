"use client";

import Link from "next/link";
import { Button } from "@/components/ui/Button";
import { ArrowRight, Sparkles } from "lucide-react";

function HeroIllustration() {
  return (
    <svg
      viewBox="0 0 400 240"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className="w-full max-w-lg opacity-90"
      aria-hidden
    >
      <g stroke="currentColor" strokeWidth="1.2" opacity="0.5">
        <path d="M40 200 L200 120 L360 200 L200 280 Z" />
        <path d="M40 200 L40 220 L200 300 L360 220 L360 200" />
        <path d="M200 120 L200 300" strokeDasharray="4 4" />
      </g>
      <g className="animate-[float_6s_ease-in-out_infinite]">
        <rect x="120" y="80" width="80" height="48" rx="8" fill="var(--panel)" stroke="currentColor" strokeWidth="1.2" />
        <text x="128" y="102" fontSize="7" fill="currentColor" opacity="0.7">BGE-small</text>
        <line x1="134" y1="112" x2="186" y2="112" stroke="currentColor" strokeWidth="1" opacity="0.3" />
      </g>
      <g className="animate-[float_5s_ease-in-out_infinite_1s]">
        <rect x="220" y="60" width="72" height="56" rx="8" fill="var(--panel)" stroke="currentColor" strokeWidth="1.2" />
        <circle cx="246" cy="88" r="10" stroke="currentColor" strokeWidth="1.2" />
        <circle cx="246" cy="88" r="4" fill="currentColor" opacity="0.6" />
        <text x="264" y="86" fontSize="6" fill="currentColor" opacity="0.5">pgvector</text>
        <text x="264" y="96" fontSize="6" fill="currentColor" opacity="0.5">tsvector</text>
      </g>
      <g className="animate-[float_7s_ease-in-out_infinite_0.5s]">
        <rect x="80" y="140" width="64" height="44" rx="8" fill="var(--panel)" stroke="currentColor" strokeWidth="1.2" />
        <rect x="94" y="156" width="36" height="6" rx="3" fill="currentColor" opacity="0.6" />
        <text x="94" y="176" fontSize="6" fill="currentColor" opacity="0.5">RRF K=60</text>
      </g>
      <style>{`
        @keyframes float {
          0%, 100% { transform: translateY(0); }
          50% { transform: translateY(-8px); }
        }
      `}</style>
    </svg>
  );
}

export function Hero() {
  return (
    <section className="relative overflow-hidden border-b border-line px-4 pt-32 pb-16 sm:px-6 lg:pt-40 lg:pb-24">
      <div className="mx-auto grid max-w-7xl gap-12 lg:grid-cols-2 lg:items-center">
        <div className="space-y-8">
          <div className="space-y-5">
            <div className="label inline-flex items-center gap-2 rounded-full border border-line bg-panel px-3 py-1.5">
              <Sparkles size={12} className="text-[accent]" />
              Hand-rolled RAG, no LangChain
            </div>
            <h1 className="text-4xl font-semibold leading-[1.1] tracking-tight sm:text-5xl lg:text-6xl">
              Research Indian startups{" "}
              <em className="font-serif not-italic text-[accent]">with sources.</em>
            </h1>
            <p className="max-w-lg text-lg text-muted">
              ISRA answers questions about the Indian startup ecosystem using
              curated data from Y Combinator and Wikipedia. Every answer is
              grounded in retrieved chunks and cites its sources inline.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <Button variant="primary" size="md" asChild className="h-11 gap-2 px-5 rounded-xl">
              <Link href="/login?redirect=/chat">
                Try the demo
                <ArrowRight size={16} />
              </Link>
            </Button>
            <Button variant="outline" size="md" asChild className="h-11 gap-2 px-5 rounded-xl">
              <Link href="/login?redirect=/lab">
                See retrieval lab
              </Link>
            </Button>
          </div>
        </div>

        <div className="flex items-center justify-center lg:justify-end">
          <HeroIllustration />
        </div>
      </div>
    </section>
  );
}
