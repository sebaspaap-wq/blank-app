/**
 * Global site configuration.
 *
 * Everything a non-developer is likely to change (brand strings, navigation,
 * company details, CTA labels) lives in `src/content`. Components read from
 * these objects and never hard-code copy.
 */

export const site = {
  name: "QUITTER",
  legalName: "Quitter B.V.",
  tagline: "90 days. One decision.",
  description:
    "QUITTER is a 90-day nicotine replacement programme with 2 mg and 4 mg nicotine gum, delivered to your door.",
  url: "https://www.quitter.nl",
  locale: "en_NL",
  lang: "en",
  country: "NL",
  email: "hello@quitter.nl",
  supportHours: "Mon–Fri, 09:00–17:30 CET",
} as const;

/** Repeated calls to action. Keep them short, confident and identical sitewide. */
export const cta = {
  primary: { label: "Start my 90 days", href: "/programs#choose" },
  primaryShort: { label: "Start your 90 days", href: "/programs#choose" },
  secondary: { label: "Build my plan", href: "/programs#choose" },
  tertiary: { label: "See how it works", href: "/how-it-works" },
} as const;

export type NavItem = { label: string; href: string; description?: string };

export const primaryNav: NavItem[] = [
  { label: "Programs", href: "/programs", description: "Light, Regular, Intense" },
  { label: "How it works", href: "/how-it-works", description: "Three steps, 90 days" },
  { label: "QUITTER ZERO", href: "/quitter-zero", description: "The finish line" },
  { label: "FAQ", href: "/faq", description: "Answers, plainly" },
];

export const footerNav: { title: string; items: NavItem[] }[] = [
  {
    title: "Programme",
    items: [
      { label: "Choose your journey", href: "/programs" },
      { label: "How it works", href: "/how-it-works" },
      { label: "The 90-day timeline", href: "/how-it-works#timeline" },
      { label: "QUITTER ZERO", href: "/quitter-zero" },
    ],
  },
  {
    title: "Medicine information",
    items: [
      { label: "Patient information", href: "/patient-information" },
      { label: "Report a side effect", href: "/pharmacovigilance" },
      { label: "FAQ", href: "/faq" },
      { label: "Contact", href: "/contact" },
    ],
  },
  {
    title: "Legal",
    items: [
      { label: "Privacy", href: "/privacy" },
      { label: "Terms", href: "/terms" },
      { label: "Returns & cancellation", href: "/returns" },
      { label: "Legal & company details", href: "/legal" },
    ],
  },
];

/**
 * Company and regulatory identifiers.
 *
 * PLACEHOLDER VALUES — replace with the registered details before launch.
 * Nothing here should be presented to a visitor as verified until it is.
 */
export const company = {
  legalName: "Quitter B.V.",
  addressLines: ["[Street and number]", "[Postcode] [City]", "The Netherlands"],
  kvk: "[KvK number]",
  vat: "[VAT / BTW number]",
  marketingAuthorisationHolder: "[Marketing authorisation holder]",
  marketingAuthorisationNumbers: "[RVG numbers — 2 mg / 4 mg]",
  manufacturer: "[Manufacturer name and address]",
  responsiblePharmacist: "[Responsible pharmacist]",
  pharmacovigilanceEmail: "safety@quitter.nl",
  pharmacovigilancePhone: "[Telephone number]",
  regulatorName: "College ter Beoordeling van Geneesmiddelen (CBG-MEB)",
  regulatorUrl: "https://www.geneesmiddeleninformatiebank.nl",
  sideEffectReportingName: "Bijwerkingencentrum Lareb",
  sideEffectReportingUrl: "https://www.lareb.nl",
} as const;
