/**
 * Programme + product catalogue.
 *
 * This file is the single source of truth for what is sold, at what price and
 * with which (approved) description. Regulatory and commercial owners can edit
 * every field here — name, duration, box mix, price, description, eligibility —
 * without touching a component.
 *
 * IMPORTANT: `audience`, `description` and `eligibility` are commercial
 * placeholders. Final categorisation, indications and dosing must come from the
 * approved product information (SmPC / patient leaflet). Fields carrying
 * `copyStatus: "awaiting-approval"` are rendered through <RegulatedCopy /> so
 * they can be swapped for approved wording in one place.
 */

export type Strength = 2 | 4;

export type BoxLine = {
  strengthMg: Strength;
  boxes: number;
  /** Pieces per box — set from the approved pack size before launch. */
  piecesPerBox: number;
};

export type Program = {
  id: "light" | "regular" | "intense";
  name: string;
  slug: string;
  /** One-line positioning. Non-medical, commercial language only. */
  audience: string;
  /** Longer commercial description; replaceable with approved copy. */
  description: string;
  durationDays: number;
  contents: BoxLine[];
  priceCents: number;
  /** Marked most popular in the selector. Exactly one programme should be true. */
  popular?: boolean;
  includes: string[];
  /** Configurable eligibility guidance — to be confirmed by the medical team. */
  eligibility: string[];
  copyStatus: "awaiting-approval" | "approved";
};

/** Price of a single box bought on its own. Used for programme value maths. */
export const SINGLE_BOX_PRICE_CENTS = 1495;

/** Placeholder pack size, replaced by the approved pack size. */
const PIECES_PER_BOX = 30;

export const programs: Program[] = [
  {
    id: "light",
    name: "Light",
    slug: "light",
    audience: "For lighter smokers",
    description:
      "A 90-day plan built around a lighter daily habit. Mostly 2 mg gum, with 4 mg for the harder moments.",
    durationDays: 90,
    contents: [
      { strengthMg: 2, boxes: 2, piecesPerBox: PIECES_PER_BOX },
      { strengthMg: 4, boxes: 1, piecesPerBox: PIECES_PER_BOX },
    ],
    priceCents: 3995,
    includes: [
      "3 boxes of QUITTER gum",
      "Your 90-day plan card",
      "Free delivery, every shipment",
      "QUITTER ZERO on completion",
    ],
    eligibility: [
      "Adults 18 and over",
      "Guidance on which strength suits you is in the patient information leaflet",
    ],
    copyStatus: "awaiting-approval",
  },
  {
    id: "regular",
    name: "Regular",
    slug: "regular",
    audience: "For regular smokers",
    description:
      "The standard 90-day plan. A balanced mix of 4 mg and 2 mg gum across the full programme.",
    durationDays: 90,
    contents: [
      { strengthMg: 4, boxes: 3, piecesPerBox: PIECES_PER_BOX },
      { strengthMg: 2, boxes: 2, piecesPerBox: PIECES_PER_BOX },
    ],
    priceCents: 5995,
    popular: true,
    includes: [
      "5 boxes of QUITTER gum",
      "Your 90-day plan card",
      "Free delivery, every shipment",
      "QUITTER ZERO on completion",
    ],
    eligibility: [
      "Adults 18 and over",
      "Guidance on which strength suits you is in the patient information leaflet",
    ],
    copyStatus: "awaiting-approval",
  },
  {
    id: "intense",
    name: "Intense",
    slug: "intense",
    audience: "For heavier smokers",
    description:
      "A 90-day plan with more 4 mg gum for a heavier daily habit, stepping down over the programme.",
    durationDays: 90,
    contents: [
      { strengthMg: 4, boxes: 5, piecesPerBox: PIECES_PER_BOX },
      { strengthMg: 2, boxes: 2, piecesPerBox: PIECES_PER_BOX },
    ],
    priceCents: 7995,
    includes: [
      "7 boxes of QUITTER gum",
      "Your 90-day plan card",
      "Free delivery, every shipment",
      "QUITTER ZERO on completion",
    ],
    eligibility: [
      "Adults 18 and over",
      "Guidance on which strength suits you is in the patient information leaflet",
    ],
    copyStatus: "awaiting-approval",
  },
];

export type SingleProduct = {
  id: string;
  name: string;
  strengthMg: Strength;
  piecesPerBox: number;
  priceCents: number;
  description: string;
};

/** Individual boxes stay available, but the programme is the main offer. */
export const singleProducts: SingleProduct[] = [
  {
    id: "box-2mg",
    name: "QUITTER 2 mg",
    strengthMg: 2,
    piecesPerBox: PIECES_PER_BOX,
    priceCents: SINGLE_BOX_PRICE_CENTS,
    description: "One box of 2 mg nicotine gum.",
  },
  {
    id: "box-4mg",
    name: "QUITTER 4 mg",
    strengthMg: 4,
    piecesPerBox: PIECES_PER_BOX,
    priceCents: SINGLE_BOX_PRICE_CENTS,
    description: "One box of 4 mg nicotine gum.",
  },
];

export const totalBoxes = (program: Program): number =>
  program.contents.reduce((sum, line) => sum + line.boxes, 0);

/** What the same boxes would cost bought individually. */
export const individualValueCents = (program: Program): number =>
  totalBoxes(program) * SINGLE_BOX_PRICE_CENTS;

export const savingCents = (program: Program): number =>
  Math.max(0, individualValueCents(program) - program.priceCents);

export const getProgram = (slug: string): Program | undefined =>
  programs.find((program) => program.slug === slug);

export const defaultProgram: Program =
  programs.find((program) => program.popular) ?? programs[0];

/**
 * QUITTER ZERO — 0 mg completion product.
 *
 * Conceptual. Not for sale, not shipped, and no therapeutic claim is made or
 * implied. Availability is subject to final regulatory assessment.
 */
export const zero = {
  name: "QUITTER ZERO",
  strength: "0 mg",
  headline: "The finish line.",
  description:
    "Complete your 90-day QUITTER programme and unlock your QUITTER ZERO package.",
  conditions: [
    "Not sold separately and not available for individual purchase.",
    "Unlocked on completion of a 90-day programme.",
    "Concept product — availability is subject to final regulatory assessment.",
  ],
  disclaimer:
    "QUITTER ZERO contains no nicotine. It is a completion item and no therapeutic effect is claimed for it.",
} as const;

export const delivery = {
  headline: "Delivered, discreetly.",
  points: [
    { label: "Shipping", value: "Free on every programme, within the Netherlands and Belgium." },
    { label: "Dispatch", value: "Ordered before 16:00 on a working day, shipped the same day." },
    { label: "Packaging", value: "Plain outer box. Nothing on the outside says what is inside." },
    { label: "Carbon", value: "Shipped with the carrier's standard network — no separate courier runs." },
  ],
} as const;
