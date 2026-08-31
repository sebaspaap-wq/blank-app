/**
 * Trust section.
 *
 * Only factual, substantiable statements. Anything requiring a registration
 * number, certificate or authority reference is a bracketed placeholder until
 * the real value exists — never presented as verified while it is a placeholder.
 */

export type TrustPoint = {
  id: string;
  label: string;
  title: string;
  body: string;
  href?: string;
  linkLabel?: string;
};

export const trustHeadline = "Made for a real quit.";

export const trustIntro =
  "A medicine should be easy to check. Everything you would want to look up about QUITTER is one click away — not buried in a footer.";

export const trustPoints: TrustPoint[] = [
  {
    id: "registered-medicine",
    label: "Registered medicine",
    title: "Assessed, registered, traceable.",
    body: "QUITTER nicotine gum is a non-prescription medicine. Its registration details are published in the Dutch medicines information bank of the CBG-MEB.",
    href: "/legal",
    linkLabel: "Registration details",
  },
  {
    id: "patient-information",
    label: "Patient information",
    title: "The leaflet, before you buy.",
    body: "The full patient information leaflet is on the site, not only in the box. Read it before you order, not after.",
    href: "/patient-information",
    linkLabel: "Read the leaflet",
  },
  {
    id: "manufacturer",
    label: "Manufacturer",
    title: "One manufacturer, named.",
    body: "The manufacturer and marketing authorisation holder are published in full on our legal page.",
    href: "/legal",
    linkLabel: "Company details",
  },
  {
    id: "pharmacovigilance",
    label: "Side effects",
    title: "A direct line for side effects.",
    body: "Report a suspected side effect to us directly, or to Bijwerkingencentrum Lareb. Both routes are listed.",
    href: "/pharmacovigilance",
    linkLabel: "Report a side effect",
  },
  {
    id: "privacy",
    label: "Privacy",
    title: "Health data stays minimal.",
    body: "We ask for what an order needs and nothing more. No non-essential tracking runs before you allow it.",
    href: "/privacy",
    linkLabel: "Privacy statement",
  },
  {
    id: "support",
    label: "Support",
    title: "A person, not a form.",
    body: "Questions about an order or the programme are answered by our team in Amsterdam on working days.",
    href: "/contact",
    linkLabel: "Contact us",
  },
];

/** Short, factual strip under the hero. */
export const heroTrustPoints = [
  "Non-prescription medicine",
  "Free discreet delivery",
  "One price, no auto-renewal",
] as const;
