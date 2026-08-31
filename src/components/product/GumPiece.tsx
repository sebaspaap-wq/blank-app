import type { CSSProperties } from "react";
import { cx } from "@/lib/format";

/**
 * A single coated gum square.
 *
 * The pieces are the product, so they are drawn as the product: matte coating,
 * a soft top light, a contact shadow. Placeholder geometry that a photographed
 * cut-out can replace one-for-one — same size, same position, same shadow.
 */

export type PieceTone = "bone" | "taupe" | "charcoal";

const tones: Record<PieceTone, { background: string; shadow: string }> = {
  bone: {
    background:
      "radial-gradient(125% 105% at 28% 20%, #ffffff 0%, #f3efe7 42%, #ddd7cb 78%, #cbc4b6 100%)",
    shadow:
      "0 18px 26px -14px rgba(25,25,25,0.55), 0 3px 6px -2px rgba(25,25,25,0.18), inset 0 1px 0 rgba(255,255,255,0.95), inset 0 0 0 1px rgba(25,25,25,0.055)",
  },
  taupe: {
    background:
      "radial-gradient(125% 105% at 28% 20%, #d5ccc0 0%, #b3a897 46%, #8f8474 82%, #7d7263 100%)",
    shadow:
      "0 18px 26px -14px rgba(25,25,25,0.6), 0 3px 6px -2px rgba(25,25,25,0.22), inset 0 1px 0 rgba(255,255,255,0.55)",
  },
  charcoal: {
    background:
      "radial-gradient(125% 105% at 28% 20%, #52504d 0%, #2a2a29 46%, #171716 100%)",
    shadow:
      "0 20px 30px -14px rgba(25,25,25,0.7), 0 3px 6px -2px rgba(25,25,25,0.3), inset 0 1px 0 rgba(255,255,255,0.18)",
  },
};

export type Piece = {
  /** Settled position, in % of the stage. */
  x: number;
  y: number;
  /** Size in % of the stage width. */
  size: number;
  /** Settled rotation. */
  rotate: number;
  /** Where it flies in from, in px. */
  fromX: number;
  fromY: number;
  fromRotate: number;
  delay: number;
  tone: PieceTone;
};

export function GumPiece({ piece, className }: { piece: Piece; className?: string }) {
  const tone = tones[piece.tone];

  return (
    <span
      aria-hidden="true"
      className={cx("piece", className)}
      style={
        {
          left: `${piece.x}%`,
          top: `${piece.y}%`,
          width: `${piece.size}%`,
          aspectRatio: "1.32 / 1",
          background: tone.background,
          boxShadow: tone.shadow,
          "--r": `${piece.rotate}deg`,
          "--from-x": `${piece.fromX}px`,
          "--from-y": `${piece.fromY}px`,
          "--from-r": `${piece.fromRotate}deg`,
          "--rise-delay": `${piece.delay}ms`,
        } as CSSProperties
      }
    />
  );
}
