import { Container, Section } from "@/components/ui/Section";
import { Reveal } from "@/components/ui/Reveal";
import { ButtonLink } from "@/components/ui/Button";
import { cta } from "@/content/site";
import { mandatoryNotice } from "@/content/medical";

export function ClosingCta() {
  return (
    <Section tone="deep" size="default">
      <Container>
        <Reveal className="flex flex-col items-start gap-10 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <h2 className="max-w-xl text-headline">Your next 90 days start here.</h2>
            <p className="mt-6 max-w-md text-lede text-charcoal/65">
              One programme. One delivery. One decision you only have to make once.
            </p>
          </div>
          <div className="flex flex-col gap-3 sm:flex-row">
            <ButtonLink href={cta.primary.href} size="lg" arrow>
              {cta.primary.label}
            </ButtonLink>
            <ButtonLink href={cta.tertiary.href} variant="outline" size="lg">
              {cta.tertiary.label}
            </ButtonLink>
          </div>
        </Reveal>
        <p className="mt-12 max-w-3xl text-xs leading-relaxed text-charcoal/65">
          {mandatoryNotice}
        </p>
      </Container>
    </Section>
  );
}
