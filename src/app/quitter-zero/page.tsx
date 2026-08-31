import type { Metadata } from "next";
import { PageHeader } from "@/components/layout/PageHeader";
import { ZeroSection } from "@/components/sections/ZeroSection";
import { Container, Eyebrow, Section } from "@/components/ui/Section";
import { Reveal } from "@/components/ui/Reveal";
import { RegulatedCopy } from "@/components/ui/RegulatedCopy";
import { ClosingCta } from "@/components/sections/ClosingCta";
import { medicalCopy } from "@/content/medical";
import { zero } from "@/content/programs";

export const metadata: Metadata = {
  title: "QUITTER ZERO",
  description:
    "QUITTER ZERO is the 0 mg completion package unlocked when you finish a 90-day QUITTER programme. Not sold separately.",
  alternates: { canonical: "/quitter-zero" },
};

const unlockSteps = [
  { title: "Start a 90-day programme", body: "Light, Regular or Intense — any programme qualifies." },
  { title: "Complete the 90 days", body: "Your programme ends on day 90. Nothing renews in between." },
  { title: "Your package unlocks", body: "We send it to the address on your programme order. There is nothing to buy." },
];

export default function QuitterZeroPage() {
  return (
    <>
      <PageHeader
        eyebrow={`${zero.strength} · Completion package`}
        title="The finish line has a name."
        intro={zero.description}
      />
      <ZeroSection compact unlockOn="view" />

      <Section tone="bone">
        <Container>
          <div className="grid gap-14 lg:grid-cols-[0.75fr_1.25fr] lg:gap-20">
            <Reveal>
              <Eyebrow>How it unlocks</Eyebrow>
              <h2 className="mt-5 max-w-sm text-headline">Earned, not bought.</h2>
            </Reveal>
            <div className="grid gap-10 sm:grid-cols-3">
              {unlockSteps.map((step, index) => (
                <Reveal key={step.title} delay={index * 80}>
                  <div className="border-t border-charcoal/12 pt-6">
                    <p className="text-mono uppercase text-label">Step {index + 1}</p>
                    <h3 className="mt-5 text-[1.0625rem] font-semibold tracking-[-0.02em]">
                      {step.title}
                    </h3>
                    <p className="mt-3 text-[0.9375rem] leading-relaxed text-charcoal/65">
                      {step.body}
                    </p>
                  </div>
                </Reveal>
              ))}
            </div>
          </div>

          <Reveal className="mt-20">
            <RegulatedCopy block={medicalCopy.zero} headingLevel="h2" />
          </Reveal>
        </Container>
      </Section>

      <ClosingCta />
    </>
  );
}
