# QUITTER — 90 days. One decision.

The D2C website for QUITTER, a Dutch nicotine-replacement brand concept sold as a
90-day programme rather than box by box.

Built with **Next.js 16 (App Router) · TypeScript · Tailwind CSS 4**, statically
rendered, no client-side data fetching, no third-party scripts.

```bash
npm install
npm run dev        # http://localhost:3000
npm run build      # production build
npm run lint       # eslint
npm run typecheck  # tsc --noEmit
```

---

## What is here

| Route | Purpose |
| --- | --- |
| `/` | Homepage: hero, why QUITTER, how it works, programme selector, 90-day timeline, QUITTER ZERO, social proof, trust, FAQ |
| `/programs` | Product/programme page and the buying module (`#choose`) |
| `/how-it-works` | Three steps, the timeline, delivery, trust |
| `/quitter-zero` | The 0 mg completion package |
| `/faq` | Full FAQ |
| `/checkout` → `/checkout/confirmation` | One-page checkout and order confirmation |
| `/privacy` `/terms` `/returns` `/contact` `/patient-information` `/pharmacovigilance` `/legal` | Legal and medicine information |
| `/sitemap.xml` `/robots.txt` | Generated from the content config |

```
src/
├── app/          routes, metadata, sitemap, robots
├── components/
│   ├── layout/   header, footer, mobile CTA, cookie consent, legal page view
│   ├── sections/ hero, manifesto, how it works, programme selector, timeline, zero, social proof, trust, FAQ, closing CTA
│   ├── product/  pack shot, programme card, buying module
│   ├── checkout/ checkout and confirmation
│   └── ui/       button, section/container/eyebrow, reveal, tracked link, in-view, regulated copy
├── content/      ← everything editable without touching a component
└── lib/          analytics, consent, cart, formatting
```

---

## Content configuration (`src/content`)

No copy is hard-coded in a component. Business and regulatory owners edit these
files:

| File | Owns |
| --- | --- |
| `site.ts` | Brand strings, CTA labels, navigation, footer, company and regulatory identifiers |
| `programs.ts` | Programmes (name, duration, box mix, price, description, eligibility), single boxes, QUITTER ZERO, delivery |
| `medical.ts` | Regulated copy blocks + the mandatory medicine notice |
| `faq.ts` | FAQ items, flagged `regulated` where the answer must come from approved text |
| `trust.ts` | Trust section |
| `timeline.ts` | The 90-day milestones and the three steps |
| `reviews.ts` | Verified customer reviews (**empty by design**) |
| `legal.ts` | Every legal / medicine-information page |

### Prices

`programs.ts` is the single source of truth. `SINGLE_BOX_PRICE_CENTS` (€14,95)
drives the "bought box by box" comparison, which is derived — never typed twice:

```ts
individualValueCents(program) = totalBoxes(program) × SINGLE_BOX_PRICE_CENTS
savingCents(program)          = individualValue − programme price
```

Current placeholders: Light €39,95 (3 boxes) · Regular €59,95 (5 boxes) ·
Intense €79,95 (7 boxes).

---

## Regulatory rules baked into the build

QUITTER is intended to be a non-prescription medicine, so the site is built so
that approved copy can replace placeholders without a redesign.

- **No invented claims.** No efficacy statistics, no clinical claims, no
  comparisons with other brands, no invented doctors, no promise that the
  product makes anyone quit.
- **No invented testimonials.** `reviews.ts` ships empty and the social-proof
  section renders a "reserved" state until verified reviews exist. Only real
  verified purchasers may ever be labelled as such.
- **Regulated copy is isolated.** Every medical statement lives in
  `medical.ts` (or an FAQ item flagged `regulated: true`) as a block with an
  `id`, a `status` and an internal `source` note pointing at the SmPC / patient
  leaflet section it must come from. `<RegulatedCopy />` renders these blocks and
  outlines any block still `awaiting-approval` in non-production builds only.
- **The mandatory notice** (`mandatoryNotice` in `medical.ts`) appears on every
  commercial surface: hero, programme selector, product page, trust, checkout,
  footer and every legal page. Replace it with the exact required wording.
- **Programme names are commercial, not medical.** Light / Regular / Intense
  describe how much gum is in the box. Dosing guidance points to the approved
  patient information; the site never invents a dose.
- **QUITTER ZERO** is presented as a conceptual completion item, never sold
  separately, with no therapeutic claim and an explicit "subject to final
  regulatory assessment" condition.

### Launch checklist

1. Replace every block in `medical.ts` with approved wording and set
   `status: "approved"`.
2. Replace regulated FAQ answers in `faq.ts`.
3. Fill the bracketed values in `site.ts` (`company`) and `legal.ts`: KvK, VAT,
   RVG numbers, MAH, manufacturer, responsible pharmacist, pharmacovigilance
   contact.
4. Publish the patient information leaflet on `/patient-information`.
5. Have counsel finalise `/privacy`, `/terms`, `/returns` (each is marked
   `status: "placeholder"`).
6. Connect a payment provider — see below.

---

## Product photography

`components/product/PackShot.tsx` renders a lit 3D placeholder of the pack
(matte warm white, charcoal type, taupe accent). When real photography or a
render exists, pass it in — same size, framing and shadow, no layout change:

```tsx
<PackShot
  strength="4 mg"
  image={{ src: "/product/quitter-4mg.webp", alt: "QUITTER 4 mg pack", width: 1200, height: 1600 }}
/>
```

Position packs from the parent (`<div className="absolute …"><PackShot …/></div>`),
not through `className` on the component.

---

## Checkout

One page: programme → delivery → payment → total. No dark patterns, no
countdowns, no pre-ticked upsells. The repeat-delivery option is opt-in and
states the exact recurring charge, its date and how to stop it, before it can be
ticked. An 18+ / leaflet confirmation is required.

**No payment provider is connected.** `submitOrder` in
`components/checkout/CheckoutClient.tsx` is the single integration point: replace
the local order reference with a call that creates the payment and redirects to
the provider. The UI states plainly that no money is taken until this is done.

---

## Analytics & consent

`lib/analytics.ts` defines one typed event vocabulary for the funnel:

`hero_cta_click` · `program_selector_opened` · `program_selected` ·
`add_to_cart` · `checkout_started` · `checkout_step_completed` ·
`purchase_completed` · `subscription_started` · `faq_opened` ·
`timeline_interaction` · `zero_section_viewed` · `patient_information_opened` ·
`consent_decision`

- Payloads carry identifiers and values only — never names, addresses, emails or
  anything that could describe a visitor's health.
- Events are **queued** until the visitor allows analytics, then flushed to
  `window.dataLayer`; refusing clears the queue. Connect your tag manager to
  `dataLayer`, or swap the `send` function.
- `lib/consent.ts` stores the decision (versioned, so changing categories
  re-asks) and broadcasts changes. Refusing is exactly as easy as accepting.

---

## Design system

Tokens live in `app/globals.css` (`@theme`).

| Token | Value | Use |
| --- | --- | --- |
| `--color-bone` | `#F7F6F2` | Page ground |
| `--color-bone-deep` | `#EFECE5` | Alternate sections |
| `--color-charcoal` | `#191919` | Type, inverted sections |
| `--color-grey` | `#D8D6D0` | Rules, dividers |
| `--color-taupe` | `#A69B8D` | Accent on dark grounds |
| `--color-clay` | `#756B60` | Accent on light grounds |
| `--color-label` | `#6A6056` | Clay darkened for 11px labels (WCAG AA) |

Type scale: `text-display`, `text-headline`, `text-title`, `text-lede`,
`text-mono` (the small uppercase label). Inter via `next/font`, three weights.

Motion: one easing curve (`--ease-quit`), transform/opacity only, entrance
choreography above the fold and `Reveal` (a single IntersectionObserver per
element) below it. Everything collapses to the final state under
`prefers-reduced-motion`, and reveals are visible without JavaScript.

---

## Quality gates

- `npm run build` — 19 static routes, no dynamic rendering.
- `npm run lint` and `npm run typecheck` — clean.
- axe-core (WCAG 2.0/2.1 A + AA) — no violations on `/`, `/programs`,
  `/how-it-works`, `/quitter-zero`, `/faq`, `/checkout`, `/legal`,
  `/patient-information`.
- Mobile-first: sticky bottom CTA that hides in checkout and near the footer,
  44px touch targets, no horizontal scroll at 390px.

---

## Note on the repository

This repository started as a blank Streamlit template; `streamlit_app.py`,
`pyproject.toml` and `uv.lock` are leftovers from it and are not used by the
website.
