import type { ElementType, ReactNode } from "react";
import { cx } from "@/lib/format";

export function Container({
  children,
  className,
  width = "default",
}: {
  children: ReactNode;
  className?: string;
  width?: "default" | "wide" | "narrow";
}) {
  const widths = {
    narrow: "max-w-3xl",
    default: "max-w-[84rem]",
    wide: "max-w-[96rem]",
  } as const;

  return (
    <div className={cx("mx-auto w-full px-5 sm:px-8 lg:px-12", widths[width], className)}>
      {children}
    </div>
  );
}

export function Eyebrow({
  children,
  className,
  as: Tag = "p",
  tone = "light",
}: {
  children: ReactNode;
  className?: string;
  as?: ElementType;
  /** Background the label sits on — it decides which accent keeps AA contrast. */
  tone?: "light" | "dark";
}) {
  return (
    <Tag
      className={cx(
        "text-mono uppercase",
        tone === "dark" ? "text-taupe" : "text-label",
        className,
      )}
    >
      {children}
    </Tag>
  );
}

export function Section({
  children,
  className,
  id,
  tone = "bone",
  size = "default",
}: {
  children: ReactNode;
  className?: string;
  id?: string;
  tone?: "bone" | "deep" | "charcoal" | "transparent";
  size?: "default" | "tight" | "loose";
}) {
  const tones = {
    bone: "bg-bone text-charcoal",
    deep: "bg-bone-deep text-charcoal",
    charcoal: "bg-charcoal text-bone",
    transparent: "",
  } as const;

  const sizes = {
    tight: "py-16 sm:py-20",
    default: "py-20 sm:py-28 lg:py-36",
    loose: "py-24 sm:py-36 lg:py-48",
  } as const;

  return (
    <section id={id} className={cx(tones[tone], sizes[size], "scroll-mt-24", className)}>
      {children}
    </section>
  );
}
