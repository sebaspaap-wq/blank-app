# Playbook — Imagery

## How the agent produces images

**Preferred:** the Canva MCP tools if connected in the session — `generate-design`,
`generate-design-structured` for layouts, `edit-design` to iterate, `export-design` for PNG/JPG.
Check `list-brand-kits` first and use the CAVÁ kit if one exists.

**Fallback when no image tool is connected:** write the full generation prompts to
`creative/prompts.md` — one numbered, ready-to-paste prompt per asset, plus the exact crop
sizes needed. Never ship a campaign with a missing-image placeholder and no prompt.

Reference frames live in `.claude/cava/assets/`. Match their lighting and surfaces —
they are the look, not a starting point to drift from.

## The prompt formula

> `[shot type]` of a woman in a `[colour]` heavyweight terry kimono-cut short bathrobe,
> shawl collar with tonal piping, patch pockets, tied self-belt, small tonal embroidered
> monogram at left chest, thigh-length — `[setting]` — `[light]` — undone low bun, bare feet,
> no jewellery, gaze off-camera — shot on 50mm, f/2, natural light, fine grain, unretouched skin
> texture — muted Mediterranean palette, travertine and linen, no colour cast

**Settings rotation:** limestone terrace with olive tree in a stone pot · plaster interior with
sheer curtain and sea beyond · poolside at a low-key beach club · stone steps down to water ·
open doorway, morning light across the floor.

**Light rotation:** last hour before sunset (warm, long shadows) · flat bright morning ·
overcast diffuse · candle and lantern at dusk.

## Sizes to render every cycle

| Use | Ratio | Pixels |
|---|---|---|
| Meta feed | 4:5 | 1080 × 1350 |
| Reels / Stories | 9:16 | 1080 × 1920 |
| Feed square | 1:1 | 1080 × 1080 |
| Email hero | 2:1 | 1200 × 600 |

Compose the 4:5 first, then reframe — do not upscale a crop.

## Text on image

Usually none. Meta creative performs better with the copy in the copy field.
When text is required (Stories, a sale frame):
- wordmark top-centre, small
- one line of headline, bottom-left, in the didone serif
- white on dark frames, near-black on light frames
- never over a face, never a coloured box behind the type

## Self-check before an image ships

- [ ] Robe reads first — lightest or darkest thing in frame
- [ ] Colourway is one of the three real ones
- [ ] Model reads clearly adult (`brand.md §8`)
- [ ] Robe closed and belt tied unless this is an 18+ paid placement
- [ ] No spa clichés, no studio white, no visible jewellery
- [ ] Palette holds — nothing outside the six brand colours
- [ ] Monogram present at the left chest, tonal, small
