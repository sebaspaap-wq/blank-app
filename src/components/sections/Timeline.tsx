"use client";

import { useEffect, useRef, useState } from "react";
import { Container, Eyebrow, Section } from "@/components/ui/Section";
import { timeline, timelineOutro } from "@/content/timeline";
import { track } from "@/lib/analytics";
import { setJourneyProgress } from "@/lib/journey";
import { cx } from "@/lib/format";

/**
 * The 90-day timeline.
 *
 * A single scroll-linked progress line drives every milestone, so the whole
 * section costs one rAF-throttled scroll listener and only writes CSS custom
 * properties — no per-element observers, no layout thrash.
 */
export function Timeline() {
  const ref = useRef<HTMLDivElement | null>(null);
  const [progress, setProgress] = useState(0);
  const interacted = useRef(false);

  useEffect(() => {
    const node = ref.current;
    if (!node) return;

    let frame = 0;

    const measure = () => {
      frame = 0;
      const rect = node.getBoundingClientRect();
      const viewport = window.innerHeight;
      // 0 when the top of the track reaches 78% of the viewport,
      // 1 once the bottom has passed 55% of it.
      const start = viewport * 0.78;
      const end = viewport * 0.55;
      const travelled = start - rect.top;
      const distance = rect.height + start - end;
      const next = Math.min(1, Math.max(0, travelled / distance));
      setProgress(next);
      // The QUITTER ZERO vault listens to this: day 90 is what opens the lock.
      setJourneyProgress(next);

      if (!interacted.current && next > 0.05) {
        interacted.current = true;
        track("timeline_interaction", { label: "scroll_progress" });
      }
    };

    const onScroll = () => {
      if (frame) return;
      frame = window.requestAnimationFrame(measure);
    };

    measure();
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", onScroll, { passive: true });

    return () => {
      window.removeEventListener("scroll", onScroll);
      window.removeEventListener("resize", onScroll);
      if (frame) window.cancelAnimationFrame(frame);
    };
  }, []);

  const outroReached = progress >= 0.995;

  return (
    <Section id="timeline" tone="charcoal" size="loose">
      <Container>
        <div className="max-w-2xl">
          <Eyebrow tone="dark">The journey</Eyebrow>
          <h2 className="mt-5 text-headline">Ninety days, one line.</h2>
          <p className="mt-6 max-w-xl text-lede text-bone/60">
            Not a countdown. A plan you can see the end of from the first day.
          </p>
        </div>

        <div className="mt-20 grid gap-16 sm:mt-28 lg:grid-cols-[1fr_15rem] lg:gap-20">
          <div ref={ref} className="relative order-2 lg:order-1">
          {/* Track */}
          <div
            aria-hidden="true"
            className="absolute left-[7px] top-2 bottom-2 w-px bg-bone/15 sm:left-[9px]"
          />
          {/* Progress */}
          <div
            aria-hidden="true"
            className="absolute left-[7px] top-2 w-px origin-top bg-bone transition-transform duration-150 ease-out sm:left-[9px]"
            style={{
              height: "calc(100% - 1rem)",
              transform: `scaleY(${progress})`,
            }}
          />

          <ol className="space-y-20 sm:space-y-28">
            {timeline.map((milestone, index) => {
              const reached = progress >= milestone.progress - 0.02;
              return (
                <li key={milestone.day} className="relative pl-12 sm:pl-20">
                  <span
                    aria-hidden="true"
                    className={cx(
                      "absolute left-0 top-2 block size-[15px] rounded-full border transition-all duration-500 ease-[var(--ease-quit)] sm:size-[19px]",
                      reached
                        ? "border-bone bg-bone scale-100"
                        : "border-bone/25 bg-charcoal scale-90",
                    )}
                  />
                  <div
                    className={cx(
                      "transition-all duration-700 ease-[var(--ease-quit)]",
                      reached ? "opacity-100 translate-y-0" : "opacity-80 translate-y-3",
                    )}
                  >
                    <p className="text-mono uppercase text-taupe">
                      {milestone.day} — {milestone.label}
                    </p>
                    <h3 className="mt-4 max-w-2xl text-title">{milestone.title}</h3>
                    <p className="mt-4 max-w-xl text-lede text-bone/70">{milestone.body}</p>
                  </div>
                  <span className="sr-only">
                    {index + 1} of {timeline.length}
                  </span>
                </li>
              );
            })}
          </ol>

          <div className="relative mt-20 pl-12 sm:mt-28 sm:pl-20">
            <span
              aria-hidden="true"
              className={cx(
                "absolute left-0 top-2 block size-[15px] rounded-full border transition-all duration-500 ease-[var(--ease-quit)] sm:size-[19px]",
                outroReached ? "border-taupe bg-taupe" : "border-bone/25 bg-charcoal",
              )}
            />
            <div
              className={cx(
                "transition-all duration-700 ease-[var(--ease-quit)]",
                outroReached ? "opacity-100 translate-y-0" : "opacity-80 translate-y-3",
              )}
            >
              <p className="text-mono uppercase text-taupe">{timelineOutro.label}</p>
              <h3 className="mt-4 text-headline">{timelineOutro.title}</h3>
              <p className="mt-5 max-w-xl text-lede text-bone/70">{timelineOutro.body}</p>
            </div>
          </div>
          </div>

          {/* Day counter — the progress line, read as a number. */}
          <div className="order-1 hidden lg:order-2 lg:block" aria-hidden="true">
            <div className="sticky top-32 text-right">
              <p className="text-[7.5rem] font-semibold leading-[0.82] tracking-[-0.05em] tabular-nums">
                {String(Math.round(progress * 90)).padStart(2, "0")}
              </p>
              <p className="mt-5 text-mono uppercase text-taupe">of 90 days</p>
            </div>
          </div>
        </div>
      </Container>
    </Section>
  );
}
