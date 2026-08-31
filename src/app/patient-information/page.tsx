import type { Metadata } from "next";
import { LegalPageView } from "@/components/layout/LegalPageView";
import { legalPages } from "@/content/legal";

const page = legalPages["patient-information"];

export const metadata: Metadata = {
  title: page.title,
  description: page.intro,
  alternates: { canonical: "/patient-information" },
};

export default function Page() {
  return <LegalPageView page={page} />;
}
