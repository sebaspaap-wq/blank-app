"use client";

import { useEffect, useRef, useState } from "react";

type Mode = "default" | "link" | "view";

export default function CustomCursor() {
  const ring = useRef<HTMLDivElement>(null);
  const dot = useRef<HTMLDivElement>(null);
  const [mode, setMode] = useState<Mode>("default");
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const fine = window.matchMedia("(pointer: fine)").matches;
    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (!fine || reduced) return;

    let frame = 0;
    const pointer = { x: window.innerWidth / 2, y: window.innerHeight / 2 };
    const ringPos = { ...pointer };

    const onMove = (event: PointerEvent) => {
      pointer.x = event.clientX;
      pointer.y = event.clientY;
      if (dot.current) {
        dot.current.style.transform = `translate3d(${pointer.x}px, ${pointer.y}px, 0) translate(-50%, -50%)`;
      }
      setVisible(true);
    };

    const onOver = (event: MouseEvent) => {
      const target = (event.target as HTMLElement | null)?.closest?.(
        "[data-cursor], a, button, input, textarea, select"
      ) as HTMLElement | null;

      if (!target) return setMode("default");

      const explicit = target.dataset?.cursor as Mode | undefined;
      if (explicit === "view") return setMode("view");
      if (explicit === "default") return setMode("default");
      setMode("link");
    };

    const tick = () => {
      ringPos.x += (pointer.x - ringPos.x) * 0.16;
      ringPos.y += (pointer.y - ringPos.y) * 0.16;
      if (ring.current) {
        ring.current.style.transform = `translate3d(${ringPos.x}px, ${ringPos.y}px, 0) translate(-50%, -50%)`;
      }
      frame = requestAnimationFrame(tick);
    };

    frame = requestAnimationFrame(tick);
    window.addEventListener("pointermove", onMove, { passive: true });
    window.addEventListener("mouseover", onOver, { passive: true });
    document.addEventListener("mouseleave", () => setVisible(false));

    return () => {
      cancelAnimationFrame(frame);
      window.removeEventListener("pointermove", onMove);
      window.removeEventListener("mouseover", onOver);
    };
  }, []);

  const size = mode === "view" ? 78 : mode === "link" ? 38 : 26;

  return (
    <div className="cursor-root" aria-hidden>
      <div
        ref={ring}
        className="absolute flex items-center justify-center rounded-full border border-white"
        style={{
          width: size,
          height: size,
          opacity: visible ? (mode === "default" ? 0.55 : 1) : 0,
          backgroundColor: mode === "view" ? "rgba(255,255,255,0.06)" : "transparent",
          transition:
            "width 0.55s var(--ease), height 0.55s var(--ease), opacity 0.5s var(--ease), background-color 0.55s var(--ease)",
        }}
      >
        <span
          className="eyebrow text-white"
          style={{
            fontSize: "0.5rem",
            letterSpacing: "0.28em",
            textIndent: "0.28em",
            opacity: mode === "view" ? 1 : 0,
            transform: `scale(${mode === "view" ? 1 : 0.85})`,
            transition: "opacity 0.45s var(--ease), transform 0.55s var(--ease)",
          }}
        >
          VIEW
        </span>
      </div>

      <div
        ref={dot}
        className="absolute rounded-full bg-white"
        style={{
          width: 4,
          height: 4,
          opacity: visible && mode === "default" ? 0.9 : 0,
          transition: "opacity 0.4s var(--ease)",
        }}
      />
    </div>
  );
}
