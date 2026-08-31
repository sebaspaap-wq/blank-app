/**
 * Legal, medicine-information and service pages.
 *
 * These are working placeholders with the correct structure and routes so that
 * legal, regulatory and privacy counsel can drop final wording into place
 * without any layout work. Bracketed values are unresolved.
 */

export type LegalSection = {
  heading: string;
  paragraphs?: string[];
  bullets?: string[];
  /** Definition-style rows, e.g. company identifiers. */
  rows?: { label: string; value: string }[];
};

export type LegalPage = {
  slug: string;
  title: string;
  intro: string;
  updated: string;
  /** Marks pages whose wording is not final. */
  status: "placeholder" | "final";
  sections: LegalSection[];
};

export const legalPages: Record<string, LegalPage> = {
  privacy: {
    slug: "privacy",
    title: "Privacy statement",
    intro:
      "How QUITTER handles your personal data, what we collect, why, and how long we keep it.",
    updated: "Placeholder — set on publication",
    status: "placeholder",
    sections: [
      {
        heading: "What we collect",
        paragraphs: [
          "Placeholder: the categories of personal data processed — order data, delivery details, payment status, support correspondence.",
        ],
        bullets: [
          "Order and delivery details you enter at checkout",
          "Payment status received from the payment provider (never card details)",
          "Support messages you send us",
          "Analytics events, only where you have allowed them",
        ],
      },
      {
        heading: "Why we process it",
        paragraphs: [
          "Placeholder: the legal bases under the GDPR — performance of a contract for orders, legal obligation for pharmacovigilance and medicines record-keeping, consent for analytics and marketing, legitimate interest for fraud prevention.",
        ],
      },
      {
        heading: "Health data",
        paragraphs: [
          "Buying a medicine can say something about your health, so we keep the data set as small as an order allows and never use it for profiling or advertising.",
          "Placeholder: final wording on special categories of personal data.",
        ],
      },
      {
        heading: "Retention",
        paragraphs: [
          "Placeholder: retention periods per category, including the statutory retention that applies to medicines and to financial records.",
        ],
      },
      {
        heading: "Your rights",
        bullets: [
          "Access, rectification and erasure",
          "Restriction of and objection to processing",
          "Data portability",
          "Withdrawing consent at any time",
          "Lodging a complaint with the Autoriteit Persoonsgegevens",
        ],
      },
      {
        heading: "Contact",
        paragraphs: [
          "Privacy questions: privacy@quitter.nl. Placeholder: data protection officer details, if appointed.",
        ],
      },
    ],
  },
  terms: {
    slug: "terms",
    title: "Terms & conditions",
    intro: "The terms that apply when you order from QUITTER.",
    updated: "Placeholder — set on publication",
    status: "placeholder",
    sections: [
      {
        heading: "Who you are contracting with",
        paragraphs: [
          "Placeholder: legal entity, registered address, Chamber of Commerce and VAT numbers.",
        ],
      },
      {
        heading: "Orders and pricing",
        paragraphs: [
          "All prices include VAT. A programme is a one-off purchase for a fixed price; nothing renews automatically unless you explicitly choose a repeat delivery at checkout, which is stated on the order confirmation and can be stopped at any time.",
          "Placeholder: order acceptance, availability, pricing errors.",
        ],
      },
      {
        heading: "Sale of medicines",
        paragraphs: [
          "Placeholder: the conditions applying to the distance sale of non-prescription medicines in the Netherlands, including the age limit and quantity limits.",
        ],
      },
      {
        heading: "Delivery",
        paragraphs: ["Placeholder: delivery terms, timelines and risk of loss."],
      },
      {
        heading: "Liability and applicable law",
        paragraphs: [
          "Placeholder: liability, force majeure, Dutch law and competent court.",
        ],
      },
    ],
  },
  returns: {
    slug: "returns",
    title: "Returns & cancellation",
    intro:
      "Your right of withdrawal, and the limits that apply to medicines for safety reasons.",
    updated: "Placeholder — set on publication",
    status: "placeholder",
    sections: [
      {
        heading: "Right of withdrawal",
        paragraphs: [
          "Placeholder: the statutory 14-day right of withdrawal for distance purchases, how to exercise it and the model withdrawal form.",
        ],
      },
      {
        heading: "Medicines and sealed goods",
        paragraphs: [
          "Placeholder: the exception for sealed medicinal products that are unsuitable for return once opened for health protection or hygiene reasons, and how it applies to QUITTER.",
        ],
      },
      {
        heading: "Damaged or incorrect deliveries",
        paragraphs: [
          "If something arrives damaged, incomplete or incorrect, contact us and we will put it right.",
        ],
      },
      {
        heading: "Refunds",
        paragraphs: ["Placeholder: refund method and timelines."],
      },
    ],
  },
  contact: {
    slug: "contact",
    title: "Contact",
    intro: "Questions about an order, the programme, or the medicine itself.",
    updated: "Placeholder — set on publication",
    status: "placeholder",
    sections: [
      {
        heading: "Customer support",
        rows: [
          { label: "Email", value: "hello@quitter.nl" },
          { label: "Hours", value: "Mon–Fri, 09:00–17:30 CET" },
          { label: "Response", value: "Within one working day" },
        ],
      },
      {
        heading: "Medical and product questions",
        paragraphs: [
          "For questions about how to use the medicine, read the patient information leaflet first. For anything it does not answer, speak to your doctor or pharmacist.",
        ],
      },
      {
        heading: "Side effects",
        paragraphs: [
          "Suspected side effects can be reported to us at safety@quitter.nl or directly to Bijwerkingencentrum Lareb.",
        ],
      },
      {
        heading: "Complaints",
        paragraphs: [
          "Placeholder: complaints procedure, response times and escalation, including any dispute resolution body.",
        ],
      },
    ],
  },
  "patient-information": {
    slug: "patient-information",
    title: "Patient information",
    intro:
      "The official information for QUITTER 2 mg and 4 mg nicotine gum. Read it before use.",
    updated: "Placeholder — set on publication",
    status: "placeholder",
    sections: [
      {
        heading: "Patient information leaflet",
        paragraphs: [
          "Placeholder: the approved patient information leaflet (PIL) is published here in full, together with a downloadable PDF, once the marketing authorisation is in place.",
          "Until then, always read the leaflet supplied with the medicine.",
        ],
      },
      {
        heading: "Product details",
        rows: [
          { label: "Active substance", value: "Nicotine" },
          { label: "Strengths", value: "2 mg and 4 mg" },
          { label: "Pharmaceutical form", value: "Medicated chewing gum" },
          { label: "Registration numbers", value: "[RVG numbers]" },
          { label: "Marketing authorisation holder", value: "[MAH name]" },
          { label: "Manufacturer", value: "[Manufacturer name]" },
        ],
      },
      {
        heading: "Official source",
        paragraphs: [
          "Registered medicine information for the Netherlands is published by the CBG-MEB in the Geneesmiddeleninformatiebank.",
        ],
      },
      {
        heading: "If in doubt",
        paragraphs: [
          "This is a medicine. Not everything suits everyone. If you are pregnant, breastfeeding, under 18, or being treated for another condition, speak to your doctor or pharmacist before use.",
        ],
      },
    ],
  },
  pharmacovigilance: {
    slug: "pharmacovigilance",
    title: "Report a side effect",
    intro:
      "If you think you have experienced a side effect, reporting it helps keep the medicine safe for everyone.",
    updated: "Placeholder — set on publication",
    status: "placeholder",
    sections: [
      {
        heading: "Report to QUITTER",
        rows: [
          { label: "Email", value: "safety@quitter.nl" },
          { label: "Telephone", value: "[Pharmacovigilance telephone]" },
          { label: "Post", value: "[Pharmacovigilance postal address]" },
        ],
        paragraphs: [
          "Include the product and strength, the batch number on the pack, what happened and when it started.",
        ],
      },
      {
        heading: "Report to Lareb",
        paragraphs: [
          "You can also report directly to Bijwerkingencentrum Lareb, the Netherlands Pharmacovigilance Centre, at lareb.nl.",
        ],
      },
      {
        heading: "Urgent medical help",
        paragraphs: [
          "This page is not for emergencies. If you need urgent medical help, contact your doctor, the out-of-hours service, or the emergency number 112.",
        ],
      },
    ],
  },
  legal: {
    slug: "legal",
    title: "Legal & company details",
    intro: "Who we are, what is registered, and where to check it.",
    updated: "Placeholder — set on publication",
    status: "placeholder",
    sections: [
      {
        heading: "Company",
        rows: [
          { label: "Legal name", value: "Quitter B.V." },
          { label: "Registered address", value: "[Street, postcode, city], The Netherlands" },
          { label: "Chamber of Commerce (KvK)", value: "[KvK number]" },
          { label: "VAT (BTW)", value: "[VAT number]" },
          { label: "Email", value: "hello@quitter.nl" },
        ],
      },
      {
        heading: "Medicine",
        rows: [
          { label: "Marketing authorisation holder", value: "[MAH name and address]" },
          { label: "Registration numbers", value: "[RVG numbers — 2 mg / 4 mg]" },
          { label: "Manufacturer", value: "[Manufacturer name and address]" },
          { label: "Responsible pharmacist", value: "[Name]" },
        ],
      },
      {
        heading: "Supervision",
        paragraphs: [
          "Medicines in the Netherlands are assessed by the College ter Beoordeling van Geneesmiddelen (CBG-MEB) and supervised by the Inspectie Gezondheidszorg en Jeugd (IGJ).",
          "Placeholder: distance-selling registration and the EU common logo for legal online sale of medicines, once issued.",
        ],
      },
      {
        heading: "Advertising",
        paragraphs: [
          "Advertising for non-prescription medicines in the Netherlands is subject to the Geneesmiddelenwet and the Code voor de Publieksreclame voor Geneesmiddelen (CPG). All claims on this site are limited to the approved product information.",
        ],
      },
    ],
  },
};

export const legalSlugs = Object.keys(legalPages);
