"use client";

import { useEffect, useState } from "react";
import { ZeroVault } from "@/components/product/ZeroVault";
import { Container, Eyebrow, Section } from "@/components/ui/Section";
import { ButtonLink } from "@/components/ui/Button";
import { InView } from "@/components/ui/InView";
import { useJourney } from "@/lib/journey";
import { cx } from "@/lib/format";
import { zero } from "@/content/programs";

/**
 * QUITTER ZERO — the emotional finish line, and the one surprise on the site.
 *
 * The pack stays sealed until the visitor has been through the 90 days, so the
 * copy has two states. Both are content-driven, and the regulatory conditions
 * are shown the moment the product itself is.
 *
 * Conceptual product: unlocked, never sold, no therapeutic claim attached.
 */
export function ZeroSection({
  compact = false,
  unlockOn = "timeline",
}: {
  compact?: boolean;
  unlockOn?: "timeline" | "view";
}) {
  const { unlocked } = useJourney();
  const [revealed, setRevealed] = useState(false);

  useEffect(() => {
    if (!unlocked) return;
    // Hold the sealed copy until the doors are open — the words should land
    // with the pack, not before it.
    const timer = window.setTimeout(() => setRevealed(true), 1250);
    return () => window.clearTimeout(timer);
  }, [unlocked]);

  return (
    <Section tone="charcoal" size={compact ? "default" : "loose"}>
      <Container>
        <InView event="zero_section_viewed" />
        <div className="grid items-center gap-16 lg:grid-cols-2 lg:gap-24">
          <div className="relative">
            <div
              className={cx(
                "transition-all duration-700 ease-[var(--ease-quit)]",
                revealed ? "opacity-100" : "opacity-0",
                revealed ? "translate-y-0" : "translate-y-2",
                !revealed && "pointer-events-none absolute -z-10",
              )}
              aria-hidden={!revealed}
            >
              <Eyebrow tone="dark">{zero.strength} · Completion package</Eyebrow>
              <h2 className="mt-6 text-display">{zero.headline}</h2>
              <p className="mt-8 max-w-md text-lede text-bone/60">{zero.description}</p>

              <ul className="mt-10 space-y-3 border-t border-bone/15 pt-8">
                {zero.conditions.map((condition) => (
                  <li key={condition} className="flex gap-4 text-[0.9375rem] text-bone/55">
                    <span
                      aria-hidden="true"
                      className="mt-2 block size-1 shrink-0 rounded-full bg-taupe"
                    />
                    <span>{condition}</span>
                  </li>
                ))}
              </ul>

              {!compact ? (
                <ButtonLink href="/quitter-zero" variant="inverse" size="lg" className="mt-10" arrow>
                  About QUITTER ZERO
                </ButtonLink>
              ) : null}

              <p className="mt-10 max-w-md text-xs leading-relaxed text-bone/55">
                {zero.disclaimer}
              </p>
            </div>

            <div
              className={cx(
                "transition-all duration-700 ease-[var(--ease-quit)]",
                revealed ? "pointer-events-none absolute -z-10 opacity-0" : "opacity-100",
              )}
              aria-hidden={revealed}
            >
              <Eyebrow tone="dark">{zero.locked.eyebrow}</Eyebrow>
              <h2 className="mt-6 text-display">{zero.locked.headline}</h2>
              <p className="mt-8 max-w-md text-lede text-bone/60">
                {zero.locked.description}
              </p>
              <p className="mt-8 border-t border-bone/15 pt-8 text-mono uppercase text-taupe">
                {unlockOn === "timeline" ? zero.locked.hint : zero.locked.hintStandalone}
              </p>
              <p className="mt-10 max-w-md text-xs leading-relaxed text-bone/55">
                {zero.disclaimer}
              </p>
            </div>
          </div>

          <div className="order-first lg:order-none">
            <ZeroVault unlockOn={unlockOn} />
          </div>
        </div>
      </Container>
    </Section>
  );
}
