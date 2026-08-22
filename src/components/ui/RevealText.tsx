import { createElement, type ElementType } from "react";

type Props = {
  lines: string[];
  as?: ElementType;
  className?: string;
  /** ms between lines */
  stagger?: number;
  delay?: number;
};

/**
 * Masked, line-by-line text reveal. Rendered on the server; animated by
 * the shared RevealProvider observer.
 */
export default function RevealText({
  lines,
  as = "h2",
  className = "",
  stagger = 110,
  delay = 0,
}: Props) {
  return createElement(
    as,
    { className, "data-reveal": "fade" },
    lines.map((line, i) => (
      <span
        key={line + i}
        className="reveal-line"
        style={{ ["--line-delay" as string]: `${delay + i * stagger}ms` }}
      >
        <span>{line}</span>
      </span>
    ))
  );
}
