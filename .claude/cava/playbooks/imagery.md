# Playbook — Imagery

## How the agent produces images

**Primary — Higgsfield.** `marketing/tools/higgsfield/` renders photography with Soul
(text-to-image) and animates stills into Reels with DoP (image-to-video).

```bash
cd marketing/tools/higgsfield
node render.mjs preflight                     # always first
node render.mjs brief.json ../../<campaign>/creative
```

Write a shot brief as JSON (see `brief.example.json`), one object per shot, using the prompt
formula below. Ratio keys: `feed-4x5`, `story-9x16`, `square-1x1`, `email-2x1`. Use
`batch_size: 4` on hero shots and pick the best frame — do not ship the first render.

Read `marketing/tools/higgsfield/README.md` before the first run of a cycle. Two things
that will otherwise waste your time: a `status: "nsfw"` result means Soul's filter rejected
the prompt (close the robe, drop skin references, retry — it is not a failure), and the SDK
reports **any** HTTP 403 as "Not enough credits", which may actually be a network block.

*Product consistency:* prompts alone will not hold the robe's details across a campaign.
Train a custom reference in Higgsfield on `.claude/cava/assets/` and set `custom_reference_id`
on every shot. Note this in `LOG.md` once done, with the id.

**Layout work — Canva MCP** if connected: `generate-design-structured` for anything with type
in it, `export-design` for the final PNG. Photography still comes from Higgsfield.

**If neither is available:** write the full prompts to `creative/prompts.md` — one numbered,
ready-to-paste prompt per asset, plus the crop sizes. Never ship a campaign with a missing
image and no prompt.

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
