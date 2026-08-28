# Playbook — Email

## Flows (build once, then maintain)

| Flow | Trigger | Emails | Job |
|---|---|---|---|
| Welcome | signup | 3 over 5 days | Positioning → product → first order |
| Browse abandon | PDP view, no cart | 1 at 4h | Low-pressure reminder |
| Cart abandon | cart, no purchase | 3 at 1h / 24h / 48h | Only #3 may carry an incentive |
| Post-purchase | order | 2 at ship + 14d | Care instructions → review request |
| Winback | 120d silent | 2 | New colourway or seasonal peg |

## Campaigns

Two per week, maximum. One sells, one does not.
The non-selling send is the reason the list stays alive: art direction, a place, the making of
the fabric, how to wash terry. If both weekly sends push product, the agent has failed.

## Structure of a CAVÁ email

1. Wordmark, small, centred, generous clear space
2. One image, full width — never a collage, never a grid of three
3. Headline, ≤ 8 words, sentence case
4. Body, 2–3 short lines. Not a paragraph.
5. One button. One. `Shop the robe` / `See the colours`
6. Footer: address, one-click unsubscribe, preference link

## Subject lines

- 30–45 characters. Preview text is a second line of copy, never "View in browser".
- No emoji. No `RE:` or `FWD:` fakery. No false urgency, no fake scarcity.
- The subject must be true. If it says new colour, there is a new colour.

Good: `Heavier than the hotel one` · `The espresso is back` · `How to wash terry`
Bad: `You're going to LOVE this ✨` · `Last chance!!!` · `Don't miss out`

## Discipline

- Segment every send. Never blast the whole list.
- Suppress: purchased in last 14d, unengaged 180d, anyone who clicked unsubscribe.
- Discounting: maximum one promotional discount per quarter outside of a named sale window.
  A discount is a decision with brand consequences — the agent drafts it and flags it,
  it does not launch it.
- Consent-based lists only. Physical address and working unsubscribe in every send (`brand.md §7`).

## Output format

Write to `marketing/<YYYY-MM-DD>-email/`:
- `<send-name>.md` — subject, preview, full copy, image brief, single CTA
- `<send-name>.html` — responsive, table-based, dark-mode safe, inline CSS
- `segments.md` — who receives it and who is suppressed
