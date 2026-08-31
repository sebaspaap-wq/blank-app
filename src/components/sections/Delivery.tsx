import { Container, Eyebrow, Section } from "@/components/ui/Section";
import { Reveal } from "@/components/ui/Reveal";
import { delivery } from "@/content/programs";

export function Delivery() {
  return (
    <Section tone="bone" size="tight">
      <Container>
        <div className="grid gap-12 lg:grid-cols-[0.75fr_1.25fr] lg:gap-20">
          <Reveal>
            <Eyebrow>Delivery</Eyebrow>
            <h2 className="mt-5 text-headline">{delivery.headline}</h2>
          </Reveal>
          <dl className="grid gap-px overflow-hidden rounded-[20px] bg-charcoal/10 sm:grid-cols-2">
            {delivery.points.map((point, index) => (
              <Reveal
                key={point.label}
                delay={(index % 2) * 70}
                className="h-full bg-bone p-8"
              >
                <dt className="text-mono uppercase text-label">{point.label}</dt>
                <dd className="mt-4 text-[0.9375rem] leading-relaxed text-charcoal/65">
                  {point.value}
                </dd>
              </Reveal>
            ))}
          </dl>
        </div>
      </Container>
    </Section>
  );
}
