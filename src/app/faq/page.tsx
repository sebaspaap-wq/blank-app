import type { Metadata } from "next";
import Link from "next/link";
import { PageHeader } from "@/components/layout/PageHeader";
import { FaqSection } from "@/components/sections/FaqSection";
import { ClosingCta } from "@/components/sections/ClosingCta";
import { Container, Section } from "@/components/ui/Section";
import { faqs } from "@/content/faq";

export const metadata: Metadata = {
  title: "FAQ",
  description:
    "Answers about the QUITTER 90-day programme, delivery, cancellation and where to find the official patient information.",
  alternates: { canonical: "/faq" },
};

/**
 * Only non-regulated answers are published as structured data: placeholder
 * medical wording must never be syndicated into search results.
 */
const faqSchema = {
  "@context": "https://schema.org",
  "@type": "FAQPage",
  mainEntity: faqs
    .filter((item) => !item.regulated)
    .map((item) => ({
      "@type": "Question",
      name: item.question,
      acceptedAnswer: { "@type": "Answer", text: item.answer.join(" ") },
    })),
};

export default function FaqPage() {
  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(faqSchema) }}
      />
      <PageHeader
        eyebrow="FAQ"
        title="Questions, answered plainly."
        intro="Anything medical follows the approved patient information — we do not improvise on that."
      />
      <FaqSection heading="All questions" />

      <Section tone="deep" size="tight">
        <Container>
          <div className="max-w-2xl">
            <h2 className="text-title">Still unanswered?</h2>
            <p className="mt-5 text-lede text-charcoal/65">
              Write to us and a person answers. For questions about how to use the medicine,
              read the patient information leaflet first, or ask your pharmacist.
            </p>
            <div className="mt-8 flex flex-wrap gap-6 text-[0.9375rem] font-medium">
              <Link href="/contact" className="underline-offset-4 hover:underline">
                Contact us →
              </Link>
              <Link href="/patient-information" className="underline-offset-4 hover:underline">
                Patient information →
              </Link>
            </div>
          </div>
        </Container>
      </Section>

      <ClosingCta />
    </>
  );
}
