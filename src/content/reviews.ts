/**
 * Social proof architecture.
 *
 * NO REVIEWS ARE PUBLISHED HERE. `reviews` is intentionally empty: the site
 * ships with the components in place, and the section only renders once real,
 * verified customer reviews are loaded into this array (or fed in from a
 * review platform). Aggregate figures are null until they can be substantiated.
 *
 * Never populate this file with invented content.
 */

export type Review = {
  id: string;
  rating: 1 | 2 | 3 | 4 | 5;
  title?: string;
  body: string;
  author: string;
  /** Only verified purchasers should ever be labelled as such. */
  verified: boolean;
  programme?: string;
  date: string;
};

export type ReviewSummary = {
  /** Average rating, or null when there is nothing verified to report. */
  average: number | null;
  count: number | null;
  source?: string;
};

export const reviews: Review[] = [];

export const reviewSummary: ReviewSummary = {
  average: null,
  count: null,
};

/** Shown in place of reviews until verified ones exist. */
export const reviewPlaceholder = {
  title: "Reviews open when the first programmes are complete.",
  body: "We only publish reviews from verified customers who bought and used a QUITTER programme. Until then, this space stays empty.",
} as const;

/** Customer story slots, filled with real stories only. */
export const customerStories: {
  id: string;
  quote: string;
  author: string;
  detail: string;
}[] = [];
