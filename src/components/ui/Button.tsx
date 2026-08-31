import Link from "next/link";
import type { ComponentPropsWithoutRef, ReactNode } from "react";
import { cx } from "@/lib/format";

type Variant = "solid" | "outline" | "inverse" | "outlineInverse" | "quiet";
type Size = "md" | "lg";

const base =
  "group inline-flex items-center justify-center gap-2.5 rounded-full font-medium tracking-[-0.01em] " +
  "transition-[transform,background-color,color,border-color,box-shadow] duration-300 ease-[var(--ease-quit)] " +
  "active:scale-[0.985] disabled:pointer-events-none disabled:opacity-45";

const variants: Record<Variant, string> = {
  solid:
    "bg-charcoal text-bone shadow-[0_1px_2px_rgba(25,25,25,0.16)] hover:bg-charcoal-soft hover:shadow-[0_14px_30px_-16px_rgba(25,25,25,0.7)]",
  outline:
    "border border-charcoal/20 text-charcoal hover:border-charcoal/60 hover:bg-charcoal/[0.03]",
  inverse:
    "bg-bone text-charcoal hover:bg-white shadow-[0_1px_2px_rgba(0,0,0,0.2)] hover:shadow-[0_14px_30px_-16px_rgba(0,0,0,0.8)]",
  outlineInverse:
    "border border-bone/25 text-bone hover:border-bone/70 hover:bg-bone/[0.06]",
  quiet: "text-charcoal/70 hover:text-charcoal",
};

const sizes: Record<Size, string> = {
  md: "h-11 px-6 text-[0.9375rem]",
  lg: "h-14 px-8 text-base sm:h-[3.75rem] sm:px-10 sm:text-[1.0625rem]",
};

type CommonProps = {
  variant?: Variant;
  size?: Size;
  className?: string;
  children: ReactNode;
  /** Trailing arrow that nudges on hover. */
  arrow?: boolean;
};

export function buttonClasses({
  variant = "solid",
  size = "md",
  className,
}: Pick<CommonProps, "variant" | "size" | "className">) {
  return cx(base, variants[variant], sizes[size], className);
}

function Arrow() {
  return (
    <span
      aria-hidden="true"
      className="transition-transform duration-300 ease-[var(--ease-quit)] group-hover:translate-x-1"
    >
      →
    </span>
  );
}

export function ButtonLink({
  href,
  variant,
  size,
  className,
  children,
  arrow,
  ...rest
}: CommonProps & { href: string } & Omit<ComponentPropsWithoutRef<typeof Link>, "href" | "className" | "children">) {
  return (
    <Link href={href} className={buttonClasses({ variant, size, className })} {...rest}>
      {children}
      {arrow ? <Arrow /> : null}
    </Link>
  );
}

export function Button({
  variant,
  size,
  className,
  children,
  arrow,
  type = "button",
  ...rest
}: CommonProps & ComponentPropsWithoutRef<"button">) {
  return (
    <button type={type} className={buttonClasses({ variant, size, className })} {...rest}>
      {children}
      {arrow ? <Arrow /> : null}
    </button>
  );
}
