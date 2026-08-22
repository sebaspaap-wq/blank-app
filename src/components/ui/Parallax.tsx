"use client";

import { useEffect, useRef, type ReactNode } from "react";

type Props = {
  children: ReactNode;
  /** Total travel as a fraction of the element height. Keep it small. */
  amount?: number;
  className?: string;
};

/**
 * Restrained parallax: one rAF loop, one transform, GPU only.
 */
export default function Parallax({ children, amount = 0.12, className }: Props) {
  const outer = useRef<HTMLDivElement>(null);
  const inner = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const host = outer.current;
    const target = inner.current;
    if (!host || !target) return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

    let frame = 0;
    let current = 0;
    let goal = 0;
    let visible = false;

    const measure = () => {
      const rect = host.getBoundingClientRect();
      const viewport = window.innerHeight;
      // -1 (entering from below) → 1 (leaving above)
      const progress = (rect.top + rect.height / 2 - viewport / 2) / (viewport / 2 + rect.height / 2);
      goal = Math.max(-1, Math.min(1, progress)) * amount * 100;
    };

    const tick = () => {
      current += (goal - current) * 0.08;
      target.style.transform = `translate3d(0, ${current.toFixed(3)}%, 0)`;
      frame = requestAnimationFrame(tick);
    };

    const io = new IntersectionObserver(
      ([entry]) => {
        visible = entry.isIntersecting;
        if (visible && !frame) {
          measure();
          frame = requestAnimationFrame(tick);
        } else if (!visible && frame) {
          cancelAnimationFrame(frame);
          frame = 0;
        }
      },
      { rootMargin: "20% 0px" }
    );

    io.observe(host);
    const onScroll = () => {
      if (visible) measure();
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", onScroll);

    return () => {
      io.disconnect();
      if (frame) cancelAnimationFrame(frame);
      window.removeEventListener("scroll", onScroll);
      window.removeEventListener("resize", onScroll);
    };
  }, [amount]);

  return (
    <div ref={outer} className={className}>
      <div ref={inner} className="h-full w-full will-change-transform">
        {children}
      </div>
    </div>
  );
}
