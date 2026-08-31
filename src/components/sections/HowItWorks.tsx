import { Container, Eyebrow, Section } from "@/components/ui/Section";
import { Reveal } from "@/components/ui/Reveal";
import { ButtonLink } from "@/components/ui/Button";
import { howItWorksSteps } from "@/content/timeline";
import { cta } from "@/content/site";

export function HowItWorks({ withCta = true }: { withCta?: boolean }) {
  return (
    <Section id="how-it-works" tone="bone">
      <Container>
        <Reveal className="max-w-2xl">
          <Eyebrow>How it works</Eyebrow>
          <h2 className="mt-5 text-headline">Three steps. Then it is behind you.</h2>
        </Reveal>

        <div className="mt-16 grid gap-12 sm:mt-20 md:grid-cols-3 md:gap-8">
          {howItWorksSteps.map((step, index) => (
            <Reveal key={step.number} delay={index * 90}>
              <div className="border-t border-charcoal/12 pt-7">
                <p className="text-[3.25rem] font-semibold leading-none tracking-[-0.05em] text-label">
                  {step.number}
                </p>
                <h3 className="mt-8 text-title">{step.title}</h3>
                <p className="mt-4 max-w-sm text-lede text-charcoal/65">{step.body}</p>
              </div>
            </Reveal>
          ))}
        </div>

        {withCta ? (
          <Reveal delay={120} className="mt-16">
            <ButtonLink href={cta.primary.href} size="lg" arrow>
              {cta.primary.label}
            </ButtonLink>
          </Reveal>
        ) : null}
      </Container>
    </Section>
  );
}
