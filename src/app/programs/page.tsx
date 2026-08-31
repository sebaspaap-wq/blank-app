import type { Metadata } from "next";
import { ProductPurchase } from "@/components/product/ProductPurchase";
import { HowItWorks } from "@/components/sections/HowItWorks";
import { Timeline } from "@/components/sections/Timeline";
import { Delivery } from "@/components/sections/Delivery";
import { MedicalInformation } from "@/components/sections/MedicalInformation";
import { ZeroSection } from "@/components/sections/ZeroSection";
import { FaqSection } from "@/components/sections/FaqSection";
import { ClosingCta } from "@/components/sections/ClosingCta";
import { programs } from "@/content/programs";
import { site } from "@/content/site";

export const metadata: Metadata = {
  title: "The 90-day programme",
  description:
    "Choose Light, Regular or Intense: a 90-day QUITTER programme of 2 mg and 4 mg nicotine gum, delivered free.",
  alternates: { canonical: "/programs" },
};

/**
 * Offer data only — price, currency, availability. No indications, claims or
 * medical descriptions are exposed in structured data.
 */
const offerSchema = {
  "@context": "https://schema.org",
  "@type": "ItemList",
  name: "QUITTER 90-day programmes",
  itemListElement: programs.map((program, index) => ({
    "@type": "ListItem",
    position: index + 1,
    item: {
      "@type": "Product",
      name: `QUITTER 90 — ${program.name}`,
      brand: { "@type": "Brand", name: site.name },
      offers: {
        "@type": "Offer",
        price: (program.priceCents / 100).toFixed(2),
        priceCurrency: "EUR",
        availability: "https://schema.org/InStock",
        url: `${site.url}/programs`,
      },
    },
  })),
};

export default function ProgramsPage() {
  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(offerSchema) }}
      />
      <ProductPurchase />
      <HowItWorks withCta={false} />
      <Timeline />
      <Delivery />
      <MedicalInformation />
      <ZeroSection compact />
      <FaqSection heading="Everything else." />
      <ClosingCta />
    </>
  );
}
