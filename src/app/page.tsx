import type { Metadata } from "next";
import { Hero } from "@/components/sections/Hero";
import { Manifesto } from "@/components/sections/Manifesto";
import { ProgramSelector } from "@/components/sections/ProgramSelector";
import { HowItWorks } from "@/components/sections/HowItWorks";
import { Timeline } from "@/components/sections/Timeline";
import { ZeroSection } from "@/components/sections/ZeroSection";
import { SocialProof } from "@/components/sections/SocialProof";
import { TrustSection } from "@/components/sections/TrustSection";
import { FaqSection } from "@/components/sections/FaqSection";
import { ClosingCta } from "@/components/sections/ClosingCta";

export const metadata: Metadata = {
  alternates: { canonical: "/" },
};

export default function HomePage() {
  return (
    <>
      <Hero />
      <Manifesto />
      <HowItWorks withCta={false} />
      <ProgramSelector />
      <Timeline />
      <ZeroSection />
      <SocialProof />
      <TrustSection />
      <FaqSection limit={5} />
      <ClosingCta />
    </>
  );
}
