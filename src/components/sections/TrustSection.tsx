import Link from "next/link";
import { Container, Eyebrow, Section } from "@/components/ui/Section";
import { Reveal } from "@/components/ui/Reveal";
import { trustHeadline, trustIntro, trustPoints } from "@/content/trust";
import { mandatoryNotice, ageNotice } from "@/content/medical";

export function TrustSection() {
  return (
    <Section id="trust" tone="bone">
      <Container>
        <Reveal className="max-w-2xl">
          <Eyebrow>Trust</Eyebrow>
          <h2 className="mt-5 text-headline">{trustHeadline}</h2>
          <p className="mt-6 text-lede text-charcoal/65">{trustIntro}</p>
        </Reveal>

        <div className="mt-16 grid gap-px overflow-hidden rounded-[20px] bg-charcoal/10 sm:grid-cols-2 lg:grid-cols-3">
          {trustPoints.map((point, index) => (
            <Reveal key={point.id} delay={(index % 3) * 70} className="bg-bone">
              <div className="flex h-full flex-col bg-bone p-8 sm:p-10">
                <p className="text-mono uppercase text-label">{point.label}</p>
                <h3 className="mt-6 text-[1.125rem] font-semibold tracking-[-0.02em]">
                  {point.title}
                </h3>
                <p className="mt-3 flex-1 text-[0.9375rem] leading-relaxed text-charcoal/65">
                  {point.body}
                </p>
                {point.href ? (
                  <Link
                    href={point.href}
                    className="group mt-7 inline-flex items-center gap-2 text-[0.9375rem] font-medium text-charcoal underline-offset-4 hover:underline"
                  >
                    {point.linkLabel ?? "Read more"}
                    <span
                      aria-hidden="true"
                      className="transition-transform duration-300 ease-[var(--ease-quit)] group-hover:translate-x-1"
                    >
                      →
                    </span>
                  </Link>
                ) : null}
              </div>
            </Reveal>
          ))}
        </div>

        <p className="mt-10 max-w-3xl text-xs leading-relaxed text-charcoal/65">
          {mandatoryNotice} {ageNotice}
        </p>
      </Container>
    </Section>
  );
}
