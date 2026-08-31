import type { CSSProperties } from "react";
import { HeroStage } from "@/components/product/HeroStage";
import { Container, Eyebrow } from "@/components/ui/Section";
import { ButtonLink } from "@/components/ui/Button";
import { TrackedLink } from "@/components/ui/TrackedLink";
import { cta, site } from "@/content/site";
import { heroTrustPoints } from "@/content/trust";
import { mandatoryNotice } from "@/content/medical";

/**
 * Above the fold: what QUITTER is, what the 90 days are, and the one action
 * to take. Nothing else.
 */
export function Hero() {
  return (
    <section className="relative overflow-hidden bg-bone pt-28 sm:pt-32 lg:pt-36">
      {/* Studio light */}
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-0 -z-10"
        style={{
          background:
            "radial-gradient(120% 80% at 72% 18%, #ffffff 0%, rgba(255,255,255,0) 58%), radial-gradient(90% 60% at 8% 100%, rgba(166,155,141,0.14) 0%, rgba(166,155,141,0) 60%)",
        }}
      />

      <Container className="relative">
        <div className="grid items-center gap-14 lg:grid-cols-[1.05fr_0.95fr] lg:gap-8">
          <div className="max-w-2xl">
            <Eyebrow className="rise" as="p">
              Nicotine replacement · 2 mg &amp; 4 mg
            </Eyebrow>

            <h1 className="mt-6 text-display">
              <span className="rise block" style={{ "--rise-delay": "60ms" } as CSSProperties}>
                90 days.
              </span>
              <span className="block text-label">
                <span
                  className="rise inline-block"
                  style={{ "--rise-delay": "210ms" } as CSSProperties}
                >
                  One
                </span>{" "}
                <span
                  className="rise inline-block"
                  style={{ "--rise-delay": "340ms" } as CSSProperties}
                >
                  decision.
                </span>
              </span>
            </h1>

            <p
              className="rise mt-7 max-w-xl text-lede text-charcoal/70"
              style={{ "--rise-delay": "180ms" } as CSSProperties}
            >
              A 90-day nicotine replacement programme built around the way people actually
              quit: one plan, one delivery, one finish line.
            </p>

            <div
              className="rise mt-10 flex flex-col gap-3 sm:flex-row sm:items-center"
              style={{ "--rise-delay": "260ms" } as CSSProperties}
            >
              <TrackedLink
                href={cta.primary.href}
                event="hero_cta_click"
                payload={{ label: cta.primary.label, location: "hero" }}
                size="lg"
                arrow
              >
                {cta.primary.label}
              </TrackedLink>
              <ButtonLink href={cta.tertiary.href} variant="outline" size="lg">
                {cta.tertiary.label}
              </ButtonLink>
            </div>

            <dl
              className="rise mt-12 grid gap-x-8 gap-y-3 border-t border-charcoal/10 pt-7 sm:grid-cols-3"
              style={{ "--rise-delay": "340ms" } as CSSProperties}
            >
              {[
                { term: "In the box", detail: "2 mg + 4 mg nicotine gum" },
                { term: "Delivery", detail: "Free, discreet, to your door" },
                { term: "At day 90", detail: "Unlock QUITTER ZERO" },
              ].map((item) => (
                <div key={item.term}>
                  <dt className="text-mono uppercase text-label">{item.term}</dt>
                  <dd className="mt-2 text-[0.9375rem] leading-snug text-charcoal/80">
                    {item.detail}
                  </dd>
                </div>
              ))}
            </dl>
          </div>

          {/* Product stage */}
          <div className="relative">
            <HeroStage />
          </div>
        </div>

        <div className="mt-14 flex flex-wrap items-center gap-x-8 gap-y-3 border-t border-charcoal/10 py-6 sm:mt-20">
          {heroTrustPoints.map((point) => (
            <span key={point} className="text-mono uppercase text-charcoal/65">
              {point}
            </span>
          ))}
        </div>

        <p className="max-w-3xl pb-16 text-xs leading-relaxed text-charcoal/65 sm:pb-20">
          {mandatoryNotice} {site.name} nicotine gum is a non-prescription medicine.
        </p>
      </Container>
    </section>
  );
}
