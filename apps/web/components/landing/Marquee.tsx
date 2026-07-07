const SOURCES = [
  "Y Combinator",
  "Wikipedia Unicorn List",
  "Polygon Technology",
  "OYO Rooms",
  "Dream11",
  "Ola Electric",
  "PharmEasy",
  "Paytm",
  "Zerodha",
  "Razorpay",
];

export function Marquee() {
  const items = [...SOURCES, ...SOURCES, ...SOURCES];

  return (
    <section id="data-sources" className="overflow-hidden border-b border-line bg-panel py-5">
      <div className="marquee-track flex whitespace-nowrap">
        {items.map((source, i) => (
          <span
            key={`${source}-${i}`}
            className="mx-6 inline-flex items-center gap-2 text-sm font-medium text-muted transition-colors hover:text-ink"
          >
            <span className="h-1.5 w-1.5 rounded-full bg-[accent]" />
            {source}
          </span>
        ))}
      </div>
      <style>{`
        @keyframes marquee {
          from { transform: translateX(0); }
          to { transform: translateX(-33.333%); }
        }
        .marquee-track {
          animation: marquee 24s linear infinite;
          width: max-content;
        }
        .marquee-track:hover {
          animation-play-state: paused;
        }
      `}</style>
    </section>
  );
}
