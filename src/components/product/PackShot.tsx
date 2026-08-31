import type { CSSProperties } from "react";
import Image from "next/image";
import { cx } from "@/lib/format";

/**
 * Product visual.
 *
 * Real product photography does not exist yet, so this renders a faithful,
 * lit 3D placeholder of the pack: matte warm white, charcoal typography,
 * taupe accent. The moment photography or a render exists, pass `image` and
 * the component swaps in the asset at the same size, framing and shadow —
 * no page redesign, no layout shift.
 */

export type PackFinish = "bone" | "charcoal" | "clay";

export type PackShotProps = {
  strength: string;
  /** Product line printed under the wordmark. */
  descriptor?: string;
  /** Small print on the pack face, e.g. pack size. */
  footnote?: string;
  finish?: PackFinish;
  /** Real asset. When present it replaces the placeholder entirely. */
  image?: { src: string; alt: string; width: number; height: number };
  className?: string;
  style?: CSSProperties;
  /** Rotation of the staged pack, in degrees. */
  angle?: number;
  priority?: boolean;
};

const finishes: Record<
  PackFinish,
  {
    face: string;
    edge: string;
    top: string;
    text: string;
    muted: string;
    rule: string;
    /** Extra rim light, so a dark pack keeps its silhouette on a dark ground. */
    rim?: string;
  }
> = {
  bone: {
    face: "linear-gradient(148deg,#fdfcfa 0%,#f6f4ef 46%,#eae7e0 100%)",
    edge: "linear-gradient(180deg,#ded9d1 0%,#cbc5bb 100%)",
    top: "linear-gradient(180deg,#fffefc 0%,#f0ede6 100%)",
    text: "#191919",
    muted: "#a69b8d",
    rule: "rgba(166,155,141,0.45)",
  },
  charcoal: {
    face: "linear-gradient(148deg,#2c2c2c 0%,#1d1d1d 48%,#131313 100%)",
    edge: "linear-gradient(180deg,#151515 0%,#0c0c0c 100%)",
    top: "linear-gradient(180deg,#3a3a3a 0%,#1f1f1f 100%)",
    text: "#f7f6f2",
    muted: "#a69b8d",
    rule: "rgba(166,155,141,0.5)",
    rim: "inset 0 0 0 1px rgba(247,246,242,0.10), inset 0 1px 0 rgba(247,246,242,0.16)",
  },
  clay: {
    face: "linear-gradient(148deg,#b3a897 0%,#a69b8d 48%,#8d8375 100%)",
    edge: "linear-gradient(180deg,#8b8173 0%,#736a5e 100%)",
    top: "linear-gradient(180deg,#c2b8a8 0%,#a39887 100%)",
    text: "#1d1b18",
    muted: "#4a453d",
    rule: "rgba(29,27,24,0.35)",
  },
};

export function PackShot({
  strength,
  descriptor = "Nicotine gum",
  footnote = "30 pieces",
  finish = "bone",
  image,
  className,
  style,
  angle = -17,
  priority = false,
}: PackShotProps) {
  if (image) {
    return (
      <div className={cx("relative isolate", className)} style={style}>
        <Image
          src={image.src}
          alt={image.alt}
          width={image.width}
          height={image.height}
          priority={priority}
          sizes="(max-width: 768px) 70vw, 34vw"
          className="h-auto w-full object-contain drop-shadow-[0_40px_60px_rgba(25,25,25,0.22)]"
        />
      </div>
    );
  }

  const tone = finishes[finish];

  return (
    <div
      className={cx("relative isolate select-none [perspective:1600px]", className)}
      style={style}
      role="img"
      aria-label={`QUITTER ${strength} ${descriptor} pack`}
    >
      {/* Contact shadow */}
      <div
        aria-hidden="true"
        className="absolute inset-x-[12%] bottom-[2%] h-[9%] rounded-[50%] blur-2xl"
        style={{ background: "rgba(25,25,25,0.28)" }}
      />

      <div className="relative mx-auto aspect-[3/4] w-[78%] [container-type:inline-size]">
        <div
          className="absolute inset-0 [transform-style:preserve-3d]"
          style={{ transform: `rotateX(4deg) rotateY(${angle}deg)` }}
        >
          {/* Right edge */}
          <div
            aria-hidden="true"
            className="absolute inset-y-0 right-0 w-[13%] origin-right rounded-r-[3px]"
            style={{ background: tone.edge, transform: "rotateY(90deg)" }}
          />
          {/* Top edge */}
          <div
            aria-hidden="true"
            className="absolute inset-x-0 top-0 h-[9%] origin-top"
            style={{ background: tone.top, transform: "rotateX(90deg)" }}
          />

          {/* Front face */}
          <div
            className="absolute inset-0 flex flex-col justify-between overflow-hidden rounded-[4px] p-[9%]"
            style={{
              background: tone.face,
              boxShadow: tone.rim
                ? `var(--shadow-pack), ${tone.rim}`
                : "var(--shadow-pack)",
            }}
          >
            <div className="flex items-start justify-between">
              <span
                className="text-[clamp(0.7rem,1.9cqw,1.05rem)] font-semibold uppercase leading-none tracking-[0.34em]"
                style={{ color: tone.text }}
              >
                Quitter
              </span>
              <span
                className="mt-[0.15em] text-[clamp(0.42rem,1.1cqw,0.6rem)] uppercase leading-none tracking-[0.24em]"
                style={{ color: tone.muted }}
              >
                NL
              </span>
            </div>

            <div>
              <div
                aria-hidden="true"
                className="mb-[8%] h-px w-[38%]"
                style={{ background: tone.rule }}
              />
              <p
                className="text-[clamp(1.6rem,7.2cqw,3.4rem)] font-semibold leading-[0.86] tracking-[-0.045em]"
                style={{ color: tone.text }}
              >
                {strength}
              </p>
              <p
                className="mt-[4%] text-[clamp(0.52rem,1.7cqw,0.9rem)] uppercase leading-none tracking-[0.2em]"
                style={{ color: tone.muted }}
              >
                {descriptor}
              </p>
            </div>

            <p
              className="text-[clamp(0.45rem,1.25cqw,0.7rem)] uppercase leading-none tracking-[0.2em]"
              style={{ color: tone.muted }}
            >
              {footnote}
            </p>

            {/* Studio light across the face */}
            <div
              aria-hidden="true"
              className="pointer-events-none absolute inset-0"
              style={{
                background:
                  "linear-gradient(112deg,rgba(255,255,255,0.55) 0%,rgba(255,255,255,0.08) 26%,rgba(255,255,255,0) 52%,rgba(25,25,25,0.07) 100%)",
              }}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
