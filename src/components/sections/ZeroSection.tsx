import { PackShot } from "@/components/product/PackShot";
import { Container, Eyebrow, Section } from "@/components/ui/Section";
import { Reveal } from "@/components/ui/Reveal";
import { ButtonLink } from "@/components/ui/Button";
import { InView } from "@/components/ui/InView";
import { zero } from "@/content/programs";

/**
 * QUITTER ZERO — the emotional finish line.
 *
 * Conceptual product: unlocked, never sold, and no therapeutic claim attached.
 * The conditions and disclaimer are rendered from content so regulatory can
 * adjust the wording in one place.
 */
export function ZeroSection({ compact = false }: { compact?: boolean }) {
  return (
    <Section tone="charcoal" size={compact ? "default" : "loose"}>
      <Container>
        <InView event="zero_section_viewed" />
        <div className="grid items-center gap-16 lg:grid-cols-2 lg:gap-24">
          <Reveal>
            <Eyebrow tone="dark">{zero.strength} · Completion package</Eyebrow>
            <h2 className="mt-6 text-display">{zero.headline}</h2>
            <p className="mt-8 max-w-md text-lede text-bone/60">{zero.description}</p>

            <ul className="mt-10 space-y-3 border-t border-bone/15 pt-8">
              {zero.conditions.map((condition) => (
                <li key={condition} className="flex gap-4 text-[0.9375rem] text-bone/55">
                  <span aria-hidden="true" className="mt-2 block size-1 shrink-0 rounded-full bg-taupe" />
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
          </Reveal>

          <Reveal delay={120} className="order-first lg:order-none">
            <div className="relative mx-auto aspect-square w-full max-w-[30rem]">
              <div
                aria-hidden="true"
                className="absolute inset-[10%] rounded-full"
                style={{
                  background:
                    "radial-gradient(circle at 50% 45%, rgba(166,155,141,0.30) 0%, rgba(166,155,141,0) 68%)",
                }}
              />
              <div className="absolute inset-x-[10%] top-[8%] w-[80%]">
                <PackShot
                  strength="0 mg"
                  descriptor="Quitter Zero"
                  footnote="Not for sale"
                  finish="charcoal"
                  angle={-14}
                />
              </div>
            </div>
          </Reveal>
        </div>
      </Container>
    </Section>
  );
}
