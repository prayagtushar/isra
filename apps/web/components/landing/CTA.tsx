import Link from "next/link";
import { Button } from "@/components/ui/Button";
import { ArrowRight } from "lucide-react";

export function CTA() {
  return (
    <section className="bg-ink px-4 py-20 text-base sm:px-6 lg:py-28">
      <div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-8 lg:flex-row">
        <div className="space-y-4 text-center lg:text-left">
          <h2 className="text-3xl font-semibold tracking-tight sm:text-4xl">
            Ready to dig into the data?
          </h2>
          <p className="text-base/80">
            Explore 111 startups, compare retrieval modes, and ask questions that cite their sources.
          </p>
        </div>
        <Button
          variant="primary"
          size="md"
          asChild
          className="h-12 gap-2 bg-base px-6 text-ink hover:bg-base/90 rounded-xl"
        >
          <Link href="/login?redirect=/chat">
            Try the demo
            <ArrowRight size={16} />
          </Link>
        </Button>
      </div>
    </section>
  );
}
