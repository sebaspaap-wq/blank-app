import type { Metadata } from "next";
import { PageHeader } from "@/components/layout/PageHeader";
import { HowItWorks } from "@/components/sections/HowItWorks";
import { Timeline } from "@/components/sections/Timeline";
import { Delivery } from "@/components/sections/Delivery";
import { ZeroSection } from "@/components/sections/ZeroSection";
import { TrustSection } from "@/components/sections/TrustSection";
import { ClosingCta } from "@/components/sections/ClosingCta";

export const metadata: Metadata = {
  title: "How it works",
  description:
    "Choose a programme, receive QUITTER, complete 90 days. How the QUITTER 90-day programme works, step by step.",
  alternates: { canonical: "/how-it-works" },
};

export default function HowItWorksPage() {
  return (
    <>
      <PageHeader
        eyebrow="How it works"
        title="Three steps, ninety days, one finish line."
        intro="No app to learn, no plan to build, no monthly re-ordering. The programme is the product."
      />
      <HowItWorks withCta={false} />
      <Timeline />
      <Delivery />
      <ZeroSection compact />
      <TrustSection />
      <ClosingCta />
    </>
  );
}
