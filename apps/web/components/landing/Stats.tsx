"use client";

import { useEffect, useRef, useState } from "react";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";

gsap.registerPlugin(ScrollTrigger);

const STATIC_STATS = [
  { value: 2, suffix: "", label: "data sources" },
  { value: 3, suffix: "", label: "retrieval modes" },
  { value: 384, suffix: "", label: "BGE-small dim" },
];

export function Stats() {
  const sectionRef = useRef<HTMLElement>(null);
  const valuesRef = useRef<(HTMLSpanElement | null)[]>([]);
  const [startupCount, setStartupCount] = useState(111);

  useEffect(() => {
    fetch("/api/startups?limit=1")
      .then((res) => res.json())
      .then((data) => {
        if (typeof data.total === "number") {
          setStartupCount(data.total);
        }
      })
      .catch(() => {
        // keep fallback
      });
  }, []);

  const stats = [
    { value: startupCount, suffix: "", label: "startups indexed" },
    ...STATIC_STATS,
  ];

  useEffect(() => {
    const triggers: ScrollTrigger[] = [];
    valuesRef.current.forEach((el, i) => {
      if (!el) return;
      const obj = { value: 0 };
      const tween = gsap.to(obj, {
        value: stats[i].value,
        duration: 1.5,
        ease: "power2.out",
        scrollTrigger: {
          trigger: sectionRef.current,
          start: "top 80%",
          once: true,
        },
        onUpdate: () => {
          el.textContent = Math.round(obj.value).toLocaleString();
        },
      });
      if (tween.scrollTrigger) triggers.push(tween.scrollTrigger);
    });

    return () => {
      triggers.forEach((t) => t.kill());
    };
  }, [stats]);

  return (
    <section ref={sectionRef} className="border-b border-line px-4 py-10 sm:px-6 lg:py-14">
      <div className="mx-auto grid max-w-7xl grid-cols-2 gap-px bg-line md:grid-cols-4">
        {stats.map((stat, i) => (
          <div
            key={stat.label}
            className="bg-base px-4 py-8 text-center sm:px-6 sm:py-10"
          >
            <div className="text-3xl font-semibold tracking-tight text-ink sm:text-4xl">
              <span ref={(el) => { valuesRef.current[i] = el; }}>0</span>
              <span className="text-[accent]">{stat.suffix}</span>
            </div>
            <p className="mt-1 text-sm text-muted">{stat.label}</p>
          </div>
        ))}
      </div>
    </section>
  );
}
