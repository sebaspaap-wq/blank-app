# CAVÁ Marketing Log

The `cava-marketing` agent reads this at the start of every run and appends to it at the end.
It is the agent's only memory between runs. Newest entry at the top.

Each entry records: date · what shipped · angle used · segment · reasoning · what to watch ·
what was deliberately not done.

---

## 2026-08-28 — Agent set up

Brand bible, three channel playbooks and visual references established from founder-supplied
assets (wordmark + four product frames: espresso sunset, ecru interior, taupe terrace,
espresso poolside).

**Decisions locked in at setup:**
- Paid targeting floor set at 18 (`brand.md §8`). Stated audience was 14–40; 14–17 is an
  organic-only audience, since platform policy bars interest/behaviour targeting of minors
  and the poolside/swimwear creative may not serve to them.
- Three colourways only — espresso, ecru, taupe. No fourth invented.
- All product specs (GSM, composition, price, shipping, certifications) marked unverified.
  Nothing may be claimed as fact until the founder confirms.

**No campaign has run yet.** No performance data exists. First cycle is open.

**Next run should:** pick segment A ("The Reset") and the Weight angle for the first Meta set —
it is the most defensible position and the espresso frames already support it.

---

## 2026-08-28 — Higgsfield connected

Image generation wired up at `marketing/tools/higgsfield/`. Soul for stills, DoP for
image-to-video Reels. Verified against `@higgsfield/client@0.2.1`.

**Known at setup:**
- Soul has no native 4:5 or 2:1 — renders go out at 3:4 and 16:9 and get cropped to
  delivery size. Crop targets are recorded in each run's `manifest.json`.
- The SDK reports every HTTP 403 as "Not enough credits". Run `preflight` to tell an
  egress block from an actual balance problem before topping up.
- **Not yet done:** a custom reference for product consistency. Until one is trained on
  `.claude/cava/assets/`, the robe's shawl collar, piping and monogram will drift between
  renders. Train it, then record the `custom_reference_id` here.
- Credit cost per render is unverified — `docs.higgsfield.ai` was unreachable at setup.
  Check pricing before a large batch.

**Not runnable from the Claude Code web sandbox:** `platform.higgsfield.ai` is blocked by
the egress proxy there (403 on CONNECT). Run renders locally, or allowlist the host in the
environment's network policy.
