/**
 * FAQ architecture.
 *
 * Answers marked `regulated: true` are placeholders that must be replaced with
 * approved product information before launch. They deliberately point to the
 * patient information leaflet rather than answering a medical question here.
 */

export type FaqItem = {
  id: string;
  question: string;
  answer: string[];
  category: "programme" | "medicine" | "delivery" | "account";
  regulated?: boolean;
};

export const faqCategories = [
  { id: "programme", label: "The programme" },
  { id: "medicine", label: "The medicine" },
  { id: "delivery", label: "Delivery & orders" },
  { id: "account", label: "After 90 days" },
] as const;

export const faqs: FaqItem[] = [
  {
    id: "what-is-quitter",
    question: "What is QUITTER?",
    answer: [
      "QUITTER is nicotine replacement therapy — 2 mg and 4 mg nicotine gum — sold as a 90-day programme rather than box by box.",
      "Placeholder: the approved description of the medicine and its indication will replace this text.",
    ],
    category: "programme",
    regulated: true,
  },
  {
    id: "how-nrt-works",
    question: "How does nicotine replacement work?",
    answer: [
      "Placeholder: approved wording from the patient information leaflet describing the role of nicotine replacement therapy in a quit attempt.",
      "Read the leaflet supplied with the medicine before use.",
    ],
    category: "medicine",
    regulated: true,
  },
  {
    id: "which-programme",
    question: "Which programme is right for me?",
    answer: [
      "Light, Regular and Intense differ in how much 2 mg and 4 mg gum they contain across the 90 days.",
      "Placeholder: the approved guidance on choosing a strength will replace this text. In the meantime, follow the patient information leaflet, or ask your pharmacist.",
    ],
    category: "programme",
    regulated: true,
  },
  {
    id: "2mg-vs-4mg",
    question: "What is the difference between 2 mg and 4 mg?",
    answer: [
      "They are the same gum at two nicotine strengths.",
      "Placeholder: approved wording on when each strength is appropriate will replace this text.",
    ],
    category: "medicine",
    regulated: true,
  },
  {
    id: "how-long",
    question: "How long is the programme?",
    answer: [
      "Ninety days from the day you start. One order covers the whole programme.",
    ],
    category: "programme",
  },
  {
    id: "delivery",
    question: "How does delivery work?",
    answer: [
      "Free delivery within the Netherlands and Belgium. Orders placed before 16:00 on a working day are dispatched the same day.",
      "Everything ships in a plain outer box with no product branding on the outside.",
    ],
    category: "delivery",
  },
  {
    id: "cancel",
    question: "Can I cancel?",
    answer: [
      "Yes. A programme is a one-off purchase, not a rolling subscription — there is nothing to cancel unless you have chosen a repeat delivery, which you can stop at any time from your order confirmation.",
      "For returns and the statutory right of withdrawal, including the limits that apply to medicines, see Returns & cancellation.",
    ],
    category: "account",
  },
  {
    id: "after-90-days",
    question: "What happens after 90 days?",
    answer: [
      "The programme ends. Nothing renews automatically.",
      "If you completed it, your QUITTER ZERO package is unlocked.",
    ],
    category: "account",
  },
  {
    id: "quitter-zero",
    question: "What is QUITTER ZERO?",
    answer: [
      "A 0 mg completion package, unlocked when you finish a 90-day programme. It is not sold separately.",
      "It is currently a concept product and its availability is subject to final regulatory assessment. No therapeutic effect is claimed for it.",
    ],
    category: "account",
  },
  {
    id: "patient-information",
    question: "Where can I find the official patient information?",
    answer: [
      "The patient information leaflet is supplied with the medicine and published on our patient information page.",
      "The official Dutch medicines information bank of the CBG-MEB is the authoritative source for registered medicine information.",
    ],
    category: "medicine",
  },
];
