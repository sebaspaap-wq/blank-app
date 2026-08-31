"use client";

import { useEffect, useState } from "react";
import { usePathname } from "next/navigation";
import { TrackedLink } from "@/components/ui/TrackedLink";
import { cta } from "@/content/site";
import { cx } from "@/lib/format";

/**
 * Sticky mobile CTA.
 *
 * Appears once the hero has been passed, and never in checkout — where it would
 * compete with the order itself.
 */
export function MobileCta() {
  const [visible, setVisible] = useState(false);
  const pathname = usePathname();
  const hidden = pathname.startsWith("/checkout");

  useEffect(() => {
    if (hidden) return;

    const onScroll = () => {
      const passedHero = window.scrollY > window.innerHeight * 0.75;
      const atFooter =
        window.innerHeight + window.scrollY >= document.body.scrollHeight - 220;
      setVisible(passedHero && !atFooter);
    };

    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", onScroll, { passive: true });
    return () => {
      window.removeEventListener("scroll", onScroll);
      window.removeEventListener("resize", onScroll);
    };
  }, [hidden]);

  if (hidden) return null;

  return (
    <div
      className={cx(
        "fixed inset-x-0 bottom-0 z-40 px-4 pb-[max(1rem,env(safe-area-inset-bottom))] transition-all duration-500 ease-[var(--ease-quit)] lg:hidden",
        visible && !hidden ? "translate-y-0 opacity-100" : "pointer-events-none translate-y-6 opacity-0",
      )}
    >
      <TrackedLink
        href={cta.primaryShort.href}
        event="hero_cta_click"
        payload={{ label: cta.primaryShort.label, location: "mobile_sticky" }}
        size="lg"
        className="w-full shadow-[0_18px_40px_-16px_rgba(25,25,25,0.55)]"
        arrow
      >
        {cta.primaryShort.label}
      </TrackedLink>
    </div>
  );
}
