"use client";

import {
  useEffect,
  useRef,
  useState,
  type CSSProperties,
  type ElementType,
  type ReactNode,
} from "react";
import { cx } from "@/lib/format";

type RevealProps = {
  children: ReactNode;
  /** Stagger, in milliseconds. */
  delay?: number;
  className?: string;
  as?: ElementType;
  /** Fraction of the element that must be visible before revealing. */
  threshold?: number;
};

/**
 * Scroll reveal: transform and opacity only, one observer per element,
 * disconnected as soon as it fires. Reduced-motion users get the final state
 * immediately — the stylesheet neutralises the transition entirely.
 */
export function Reveal({
  children,
  delay = 0,
  className,
  as: Tag = "div",
  threshold = 0.15,
}: RevealProps) {
  const ref = useRef<HTMLElement | null>(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const node = ref.current;
    if (!node) return;

    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            setVisible(true);
            observer.disconnect();
          }
        }
      },
      { threshold, rootMargin: "0px 0px -8% 0px" },
    );

    observer.observe(node);
    return () => observer.disconnect();
  }, [threshold]);

  return (
    <Tag
      ref={ref}
      className={cx("reveal", className)}
      data-visible={visible ? "true" : "false"}
      style={{ "--reveal-delay": `${delay}ms` } as CSSProperties}
    >
      {children}
    </Tag>
  );
}
