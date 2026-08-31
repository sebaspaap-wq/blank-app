/**
 * Regulated copy.
 *
 * Every string here is a PLACEHOLDER awaiting approved wording from the
 * marketing authorisation dossier (SmPC / patient information leaflet) as
 * assessed by the CBG-MEB. Each block has a stable `id` so the regulatory team
 * can map approved text onto it one-for-one, and a `status` so unreviewed copy
 * is easy to find (and to flag visually in non-production builds).
 *
 * Rules that must survive any edit:
 *  - no efficacy claims beyond the approved indication
 *  - no invented statistics, studies, doctors or endorsements
 *  - no comparison with other brands
 *  - no claim that a product guarantees cessation
 */

export type CopyStatus = "awaiting-approval" | "approved";

export type RegulatedBlock = {
  id: string;
  title: string;
  /** Paragraphs of approved (or placeholder) text. */
  body: string[];
  status: CopyStatus;
  /** Where the approved wording will come from. Internal note, never rendered. */
  source?: string;
};

export const medicalCopy: Record<string, RegulatedBlock> = {
  whatItIs: {
    id: "what-it-is",
    title: "What QUITTER is",
    body: [
      "QUITTER is nicotine replacement therapy in the form of chewing gum, available in 2 mg and 4 mg strengths.",
      "Placeholder: the approved indication, target group and treatment description will be inserted here verbatim from the approved product information.",
    ],
    status: "awaiting-approval",
    source: "SmPC section 4.1 / patient leaflet section 1",
  },
  howItWorks: {
    id: "how-it-works",
    title: "How nicotine replacement works",
    body: [
      "Placeholder: approved wording describing the role of nicotine replacement therapy in a quit attempt.",
      "Placeholder: approved wording on how the gum is used and over what period.",
    ],
    status: "awaiting-approval",
    source: "Patient leaflet sections 1 and 3",
  },
  strengths: {
    id: "strengths",
    title: "2 mg and 4 mg",
    body: [
      "Placeholder: approved wording on the difference between the 2 mg and 4 mg strengths and how to choose between them.",
      "Until this text is approved, refer to the patient information leaflet supplied with the medicine.",
    ],
    status: "awaiting-approval",
    source: "Patient leaflet section 3 (dosage)",
  },
  dosage: {
    id: "dosage",
    title: "How to use it",
    body: [
      "Placeholder: approved dosing instructions, maximum daily amounts and duration of treatment.",
      "Always read the patient information leaflet before use.",
    ],
    status: "awaiting-approval",
    source: "Patient leaflet section 3",
  },
  warnings: {
    id: "warnings",
    title: "Warnings and precautions",
    body: [
      "Placeholder: approved contraindications, warnings, interactions and use in specific groups.",
      "Placeholder: approved wording on side effects and what to do if they occur.",
    ],
    status: "awaiting-approval",
    source: "Patient leaflet sections 2 and 4",
  },
  zero: {
    id: "zero",
    title: "About QUITTER ZERO",
    body: [
      "QUITTER ZERO contains no nicotine. It is a completion item unlocked at the end of a 90-day programme and is not sold separately.",
      "It is a concept product. Availability, composition and any wording used about it are subject to final regulatory assessment. No therapeutic effect is claimed for it.",
    ],
    status: "awaiting-approval",
    source: "To be confirmed with regulatory affairs",
  },
};

/**
 * The mandatory notice for advertising a non-prescription medicine to the
 * public. Final wording is set by Dutch/EU rules — replace with the exact
 * required sentence before launch.
 */
export const mandatoryNotice =
  "This is a medicine. Read the patient information leaflet before use. Not suitable for everyone. Consult your doctor or pharmacist if symptoms persist.";

export const ageNotice = "Sold to adults 18 and over.";
