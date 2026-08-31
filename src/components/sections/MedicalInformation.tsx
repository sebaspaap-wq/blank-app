import Link from "next/link";
import { Container, Eyebrow, Section } from "@/components/ui/Section";
import { Reveal } from "@/components/ui/Reveal";
import { RegulatedCopy } from "@/components/ui/RegulatedCopy";
import { medicalCopy, mandatoryNotice, ageNotice } from "@/content/medical";

const blocks = [
  medicalCopy.whatItIs,
  medicalCopy.howItWorks,
  medicalCopy.strengths,
  medicalCopy.dosage,
  medicalCopy.warnings,
];

/**
 * Medicine information on the product page.
 *
 * Every block comes from the regulated content file and is replaced one-for-one
 * with approved product information before launch.
 */
export function MedicalInformation() {
  return (
    <Section id="medical-information" tone="deep">
      <Container>
        <div className="grid gap-12 lg:grid-cols-[0.75fr_1.25fr] lg:gap-20">
          <Reveal>
            <Eyebrow>Medicine information</Eyebrow>
            <h2 className="mt-5 max-w-sm text-headline">Read this before you order.</h2>
            <p className="mt-6 max-w-sm text-lede text-charcoal/65">
              QUITTER is a medicine. The full patient information leaflet is published on
              this site, not only inside the box.
            </p>
            <Link
              href="/patient-information"
              className="mt-8 inline-block text-[0.9375rem] font-medium underline-offset-4 hover:underline"
            >
              Patient information →
            </Link>
          </Reveal>

          <div className="grid gap-10 sm:grid-cols-2">
            {blocks.map((block, index) => (
              <Reveal key={block.id} delay={(index % 2) * 70}>
                <RegulatedCopy block={block} />
              </Reveal>
            ))}
          </div>
        </div>

        <p className="mt-14 max-w-3xl text-xs leading-relaxed text-charcoal/65">
          {mandatoryNotice} {ageNotice}
        </p>
      </Container>
    </Section>
  );
}
