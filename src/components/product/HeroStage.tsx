"use client";

import { useEffect, useRef, type CSSProperties } from "react";
import { PackShot } from "./PackShot";
import { GumPiece, type Piece } from "./GumPiece";

/**
 * The opening moment.
 *
 * On load the packs fly into position and the gum scatters into place around
 * them — one orchestrated arrival of about 1.5s, then everything settles and
 * only breathes. Pointer movement shifts three depth planes against each other,
 * so the scatter reads as a lit still life rather than a flat collage.
 *
 * Deterministic by design: fixed coordinates, no randomness, so the server and
 * the client render the same stage.
 */

const farPieces: Piece[] = [
  { x: 6, y: 12, size: 5.6, rotate: -14, fromX: -170, fromY: -60, fromRotate: -40, delay: 420, tone: "bone" },
  { x: 26, y: 2, size: 4.8, rotate: 22, fromX: -40, fromY: -150, fromRotate: 50, delay: 520, tone: "taupe" },
  { x: 70, y: 6, size: 5.2, rotate: -8, fromX: 120, fromY: -140, fromRotate: -35, delay: 480, tone: "bone" },
  { x: 89, y: 20, size: 6, rotate: 16, fromX: 190, fromY: -70, fromRotate: 45, delay: 560, tone: "bone" },
  { x: 10, y: 58, size: 5, rotate: 30, fromX: -180, fromY: 40, fromRotate: -55, delay: 620, tone: "bone" },
  { x: 86, y: 64, size: 5.4, rotate: -22, fromX: 190, fromY: 60, fromRotate: 40, delay: 600, tone: "taupe" },
  { x: 44, y: 1, size: 4.4, rotate: 40, fromX: 20, fromY: -170, fromRotate: 70, delay: 660, tone: "bone" },
  { x: 55, y: 70, size: 4.6, rotate: -30, fromX: 60, fromY: 150, fromRotate: -60, delay: 700, tone: "bone" },
];

const midPieces: Piece[] = [
  { x: 0, y: 34, size: 8.4, rotate: -18, fromX: -200, fromY: 20, fromRotate: -60, delay: 300, tone: "bone" },
  { x: 92, y: 42, size: 7.8, rotate: 24, fromX: 210, fromY: 30, fromRotate: 55, delay: 340, tone: "bone" },
  { x: 60, y: 82, size: 8.6, rotate: -12, fromX: 90, fromY: 170, fromRotate: -45, delay: 700, tone: "taupe" },
  { x: 26, y: 88, size: 7.4, rotate: 34, fromX: -70, fromY: 180, fromRotate: 60, delay: 660, tone: "bone" },
  { x: 3, y: 80, size: 7, rotate: 8, fromX: -160, fromY: 120, fromRotate: -30, delay: 740, tone: "charcoal" },
  { x: 78, y: 16, size: 6.6, rotate: -26, fromX: 160, fromY: -110, fromRotate: 50, delay: 620, tone: "bone" },
  { x: 16, y: 24, size: 6.2, rotate: 18, fromX: -150, fromY: -90, fromRotate: -50, delay: 580, tone: "bone" },
];

const nearPieces: Piece[] = [
  { x: 14, y: 70, size: 12, rotate: -26, fromX: -190, fromY: 150, fromRotate: -70, delay: 380, tone: "bone" },
  { x: 70, y: 90, size: 11, rotate: 18, fromX: 150, fromY: 200, fromRotate: 62, delay: 800, tone: "bone" },
  { x: 94, y: 72, size: 9.6, rotate: -34, fromX: 220, fromY: 120, fromRotate: 70, delay: 860, tone: "charcoal" },
  { x: 36, y: 62, size: 9.2, rotate: 12, fromX: -60, fromY: 190, fromRotate: -50, delay: 900, tone: "bone" },
  { x: 48, y: 94, size: 8.8, rotate: -16, fromX: 30, fromY: 210, fromRotate: 55, delay: 940, tone: "taupe" },
];

export function HeroStage() {
  const stageRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const stage = stageRef.current;
    if (!stage) return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    if (!window.matchMedia("(hover: hover) and (pointer: fine)").matches) return;

    let frame = 0;
    let x = 0;
    let y = 0;

    const apply = () => {
      frame = 0;
      stage.style.setProperty("--px", `${x.toFixed(2)}px`);
      stage.style.setProperty("--py", `${y.toFixed(2)}px`);
    };

    const onMove = (event: PointerEvent) => {
      const rect = stage.getBoundingClientRect();
      // −1 … 1 from the centre of the stage, capped so the scene never lurches.
      x = Math.max(-1, Math.min(1, (event.clientX - (rect.left + rect.width / 2)) / rect.width)) * 12;
      y = Math.max(-1, Math.min(1, (event.clientY - (rect.top + rect.height / 2)) / rect.height)) * 12;
      if (!frame) frame = window.requestAnimationFrame(apply);
    };

    const onLeave = () => {
      x = 0;
      y = 0;
      if (!frame) frame = window.requestAnimationFrame(apply);
    };

    window.addEventListener("pointermove", onMove, { passive: true });
    window.addEventListener("pointerleave", onLeave);
    return () => {
      window.removeEventListener("pointermove", onMove);
      window.removeEventListener("pointerleave", onLeave);
      if (frame) window.cancelAnimationFrame(frame);
    };
  }, []);

  return (
    <div
      ref={stageRef}
      className="relative mx-auto aspect-square w-full max-w-[26rem] sm:max-w-[34rem]"
    >
      {/* Studio light, opening up behind the scene */}
      <div
        aria-hidden="true"
        className="arrive absolute inset-[6%] rounded-full"
        style={{
          background:
            "radial-gradient(circle at 50% 42%, #ffffff 0%, rgba(247,246,242,0.6) 45%, rgba(247,246,242,0) 72%)",
          "--rise-delay": "0ms",
          "--from-y": "0px",
        } as CSSProperties}
      />

      <div
        className="plane hidden opacity-80 blur-[2px] sm:block"
        style={{ "--depth": "0.35" } as CSSProperties}
      >
        {farPieces.map((piece) => (
          <GumPiece key={`far-${piece.x}-${piece.y}`} piece={piece} />
        ))}
      </div>

      <div className="plane blur-[0.4px]" style={{ "--depth": "0.7" } as CSSProperties}>
        {midPieces.map((piece) => (
          <GumPiece key={`mid-${piece.x}-${piece.y}`} piece={piece} />
        ))}
      </div>

      {/* The packs sit between the mid and near planes */}
      <div className="plane" style={{ "--depth": "1" } as CSSProperties}>
        <div
          className="arrive float-slow absolute left-[4%] top-[8%] w-[56%]"
          style={{ "--rise-delay": "160ms", "--from-x": "-90px", "--from-y": "70px", "--from-r": "-10deg" } as CSSProperties}
        >
          <PackShot strength="4 mg" angle={-19} />
        </div>
        <div
          className="arrive absolute right-[2%] top-[30%] w-[48%]"
          style={{ "--rise-delay": "320ms", "--from-x": "110px", "--from-y": "60px", "--from-r": "9deg" } as CSSProperties}
        >
          <PackShot strength="2 mg" angle={-12} />
        </div>
      </div>

      <div className="plane" style={{ "--depth": "1.6" } as CSSProperties}>
        {nearPieces.map((piece) => (
          <GumPiece key={`near-${piece.x}-${piece.y}`} piece={piece} />
        ))}
      </div>

      {/* One specular pass across the finished scene */}
      <div aria-hidden="true" className="pointer-events-none absolute inset-0 overflow-hidden">
        <span className="sweep" />
      </div>
    </div>
  );
}
