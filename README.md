# CAVÁ — Luxury, Lived In.

An ultra-premium storefront for CAVÁ, a Mediterranean bathrobe house. Built as a
fashion campaign that happens to have e-commerce functionality: full-bleed
photography, editorial typography, and motion that stays quiet.

## Stack

- **Next.js 15** (App Router) · **React 19** · **TypeScript**
- **Tailwind CSS v4** for layout utilities; a hand-written design system in
  `src/app/globals.css` for type, motion and colour
- **Framer Motion** for the overlays (menu, search, bag) and page transitions
- **next/image** with AVIF/WebP, blur placeholders and priority hints

## Running it

```bash
npm install
npm run dev      # http://localhost:3000
npm run build && npm run start
```

## Structure

```
src/
  app/
    page.tsx                  homepage — hero → collection → about → values → campaign → gallery
    collection/               collection index + /collection/[slug] product pages
    about/  journal/  contact/
    service/[slug]            shipping · returns · size-guide · care
    globals.css               design tokens, type scale, reveal + link primitives
  components/
    site/                     Navigation, MenuOverlay, SearchOverlay, CartDrawer,
                              CustomCursor, Footer, SiteProvider (bag + overlay state)
    home/                     Hero, Collection, ProductCard, About, Values,
                              EditorialSection, Gallery
    product/                  ProductView, Accordion
    ui/                       RevealProvider, RevealText, Parallax, ArrowLink
  lib/
    products.ts               the three colourways, copy, pricing, image crops
    images.ts                 campaign photography + generated blur placeholders
```

## Design system

| Token | Value | Use |
| --- | --- | --- |
| `--color-noir` | `#080807` | dark sections, footer, menu |
| `--color-ivory` | `#F5F2EB` | the default ground |
| `--color-sand` | `#C8B6A2` | Sand colourway |
| `--color-taupe` | `#A89683` | secondary accents |
| `--color-cacao` | `#3A2920` | Cacao colourway |

Playfair Display carries every headline; DM Sans (300/400) carries navigation and
body copy at wide tracking. Every transition uses
`cubic-bezier(0.22, 1, 0.36, 1)` — nothing bounces, nothing snaps.

## Motion

One `IntersectionObserver` in `RevealProvider` drives every scroll reveal on the
site, so server components only need a `data-reveal` attribute. Parallax runs on
a single rAF loop per section and only while the section is on screen. The custom
cursor is disabled on coarse pointers, and `prefers-reduced-motion` short-circuits
reveals, parallax, the cursor and every overlay animation.

## Behaviour

- Bag state persists to `localStorage`; adding a size opens the drawer rather than
  navigating away
- `ESC` and outside clicks close the menu, search and bag; scroll locks while open
- Product pages are statically generated per colourway with per-product metadata

## Photography

Campaign images live in `public/images` as WebP (~90–145 kB each), resized to
1600px and paired with 16px blur placeholders so nothing shifts on load. The hero
frame loads with priority; everything below the fold is lazy.
