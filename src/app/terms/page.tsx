import type { Metadata } from "next";
import { LegalPageView } from "@/components/layout/LegalPageView";
import { legalPages } from "@/content/legal";

const page = legalPages["terms"];

export const metadata: Metadata = {
  title: page.title,
  description: page.intro,
  alternates: { canonical: "/terms" },
};

export default function Page() {
  return <LegalPageView page={page} />;
}
