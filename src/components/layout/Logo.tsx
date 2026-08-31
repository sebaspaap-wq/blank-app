import Link from "next/link";
import { cx } from "@/lib/format";

/** Wordmark. Type-set, not an image — it stays crisp and costs nothing. */
export function Logo({ className, label = "QUITTER" }: { className?: string; label?: string }) {
  return (
    <Link
      href="/"
      aria-label="QUITTER — home"
      className={cx(
        "text-[0.9375rem] font-semibold uppercase leading-none tracking-[0.34em] transition-opacity duration-300 hover:opacity-70",
        className,
      )}
    >
      {label}
    </Link>
  );
}
