# Higgsfield renderer

Renders CAVÁ campaign imagery with **Higgsfield Soul** (text-to-image) and animates
stills into Reels with **DoP** (image-to-video).

## Setup

```bash
cd marketing/tools/higgsfield
npm install
export HF_CREDENTIALS="KEY_ID:KEY_SECRET"   # from Higgsfield Cloud
node render.mjs preflight
```

`preflight` checks credentials and reachability separately, so you get a real diagnosis
instead of a guess. Run it first, always.

## Rendering

```bash
node render.mjs brief.example.json ../../2026-08-28-meta/creative
```

The brief is JSON — one object per shot. See `brief.example.json` for a working set of
four CAVÁ prompts. Output: the image files, plus `manifest.json` recording every
`request_id`, status and filename.

## Shot fields

| Field | Notes |
|---|---|
| `id` | Becomes the filename stem |
| `ratio` | `feed-4x5` · `story-9x16` · `square-1x1` · `email-2x1` |
| `prompt` | Follow the formula in `.claude/cava/playbooks/imagery.md` |
| `batch_size` | `1` or `4`. Use 4 for hero shots — you want options |
| `quality` | `720p` or `1080p` (default) |
| `seed` | Set to reproduce a frame you liked |
| `reference_url` | Public URL of a reference image, for product consistency |
| `custom_reference_id` | A trained custom reference in Higgsfield — better than `reference_url` |
| `type: "video"` | Uses DoP instead; also needs `image_url` and optional `motions` |

## Resolutions

Soul emits a fixed set of sizes and has **no native 4:5 or 2:1**. The script renders the
nearest larger ratio and records the delivery crop in the manifest:

| Ratio key | Rendered | Crop to | Use |
|---|---|---|---|
| `feed-4x5` | 1536×2048 (3:4) | 1080×1350 | Meta feed |
| `story-9x16` | 1152×2048 | 1080×1920 | Reels / Stories |
| `square-1x1` | 1536×1536 | 1080×1080 | Feed square |
| `email-2x1` | 2048×1152 (16:9) | 1200×600 | Email hero |

Cropping is a separate step — the raw renders are kept so you can reframe.

## Product consistency

Prompts alone will not hold the robe's details across a campaign. Two options, in order:

1. **Custom reference** — train one in Higgsfield on the frames in `.claude/cava/assets/`,
   then set `custom_reference_id` on every shot. Best consistency.
2. **`reference_url`** — needs a **publicly reachable URL**. The local files in
   `.claude/cava/assets/` will not work; host them first.

## Two traps

**"Not enough credits" may be a lie.** The SDK maps *every* HTTP 403 to that message,
including a 403 from a proxy that never reached Higgsfield. Run `preflight` before you
top up an account.

**`status: "nsfw"`** means Soul's filter rejected the prompt, not that the render failed.
Close the robe, remove skin and swimwear references, retry. The manifest records it.

## Verified vs. assumed

Verified against `@higgsfield/client@0.2.1`: base URL `https://platform.higgsfield.ai`,
credential env vars, endpoints `/v1/text2image/soul` and `/v1/image2video/dop`, the input
schemas, the resolution list, and the `queued|in_progress|completed|failed|nsfw` states.

Not verified: per-render credit cost, rate limits, and whether Soul's filter tolerates the
robe-open frames. `docs.higgsfield.ai` was unreachable from the environment this was written
in — check pricing there before running a large batch.
