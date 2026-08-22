"use client";

import { useEffect } from "react";

/**
 * A single IntersectionObserver drives every scroll reveal on the site.
 * Server components only need to render `data-reveal` — no client boundary,
 * no per-element observer, no layout thrash.
 */
export default function RevealProvider() {
  useEffect(() => {
    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    if (reduced) {
      document
        .querySelectorAll<HTMLElement>("[data-reveal], .reveal-line")
        .forEach((el) => el.classList.add("is-revealed"));
      return;
    }

    const pending = new Set<Element>();

    const reveal = (el: Element) => {
      el.classList.add("is-revealed");
      observer.unobserve(el);
      pending.delete(el);
    };

    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) reveal(entry.target);
        }
      },
      { rootMargin: "0px 0px -12% 0px", threshold: 0.08 }
    );

    /**
     * A fast flick — down the page, or sideways along the gallery — can carry
     * an element clean past the viewport between two frames, and the observer
     * never reports a state change at all. Sweep anything already behind us.
     */
    let frame = 0;
    const sweep = () => {
      frame = 0;
      if (!pending.size) return;
      for (const el of Array.from(pending)) {
        const box = el.getBoundingClientRect();
        if (box.top < 0 || box.right < 0) reveal(el);
      }
    };
    const onScroll = () => {
      if (!frame && pending.size) frame = requestAnimationFrame(sweep);
    };

    const scan = () => {
      document
        .querySelectorAll<HTMLElement>("[data-reveal]:not(.is-revealed)")
        .forEach((el) => {
          if (pending.has(el)) return;
          pending.add(el);
          observer.observe(el);
        });
    };

    scan();

    const mutation = new MutationObserver(scan);
    mutation.observe(document.body, { childList: true, subtree: true });

    // capture: true also catches scrolling inside the editorial gallery track
    document.addEventListener("scroll", onScroll, { capture: true, passive: true });

    return () => {
      observer.disconnect();
      mutation.disconnect();
      document.removeEventListener("scroll", onScroll, { capture: true });
      if (frame) cancelAnimationFrame(frame);
    };
  }, []);

  return null;
}
