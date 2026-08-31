"use client";

import { useEffect, useRef } from "react";
import { track, type AnalyticsEvent, type AnalyticsPayload } from "@/lib/analytics";

/**
 * Fires a single analytics event the first time a section is genuinely seen.
 * Rendered as a zero-height marker so it never affects layout — place it where
 * "seen" should mean seen, usually just inside the section content.
 */
export function InView({
  event,
  payload,
}: {
  event: AnalyticsEvent;
  payload?: AnalyticsPayload;
}) {
  const ref = useRef<HTMLSpanElement | null>(null);

  useEffect(() => {
    const node = ref.current;
    if (!node) return;

    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            track(event, payload);
            observer.disconnect();
          }
        }
      },
      // Zero-area targets report a ratio of 0, so the trigger point is set with
      // a root margin instead: the marker must be a quarter into the viewport.
      { threshold: 0, rootMargin: "0px 0px -25% 0px" },
    );

    observer.observe(node);
    return () => observer.disconnect();
    // payload is a small literal object; identity changes should not re-fire.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [event]);

  return <span ref={ref} aria-hidden="true" className="block h-0 w-0" />;
}
