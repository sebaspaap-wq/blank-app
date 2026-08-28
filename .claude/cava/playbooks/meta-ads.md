# Playbook — Meta Ads

## Account structure the agent always produces

```
Campaign  (objective: Sales / Conversions, CBO on)
├── Ad set — Broad          age 18-40, no interests, all placements   ← 60% budget
├── Ad set — Retargeting    site 30d + IG engagers 90d + email list   ← 25% budget
└── Ad set — Lookalike      1% LAL of purchasers (only once ≥100 purch) ← 15% budget
```

`age_min: 18` on every ad set, no exceptions (`brand.md §8`).
Broad beats stacked interests at this budget level. Do not build interest ad sets unless
broad has been given 7 days and ≥50 results and still underperforms.

## Creative volume per cycle

Per weekly cycle, ship **9 ads**: 3 concepts × 3 formats (4:5 feed, 9:16 Reels/Stories, 1:1).
Concepts must be genuinely different angles, not three crops of one idea.

## The angle bank — rotate, never repeat two cycles running

1. **Weight** — the robe is heavier than expected. Physical, tactile, provable.
2. **The hotel** — you have worn this robe before, in a better country.
3. **Length** — thigh-length on purpose. Anti-hotel-robe, anti-frumpy.
4. **The hour** — 6pm, sea still on your skin, an hour before anyone needs you.
5. **The gift** — the thing she would never buy herself.
6. **The pack** — it goes in the suitcase. Segment C.
7. **Wash** — comes back the same shape. Longevity as luxury.
8. **Colour** — espresso vs ecru vs taupe, as a decision.
9. **Ritual** — the same ten minutes, every evening, in a better robe.

## Copy spec per ad

- **Primary text:** 125 characters before the fold. Front-load the hook. 3–4 short lines max.
- **Headline:** ≤ 27 characters. Not a repeat of the primary text.
- **Description:** ≤ 27 characters, or omit.
- **CTA:** `Shop now` for cold, `Shop now` for retargeting. Never `Learn more` on a product ad.
- No emoji. No exclamation marks. No unverified claims (`brand.md §6`).

## Hook rules

The first 3 words carry the ad. Test hooks that are:
- a physical fact ("Heavier than…")
- a contradiction ("Short. On purpose.")
- a place ("6pm. Puglia.")
Never a question. Never "POV:". Never "Stop scrolling".

## Reading results — the only rules that matter

Judge on **7-day windows, minimum 50 results.** Before that, do nothing.

| Signal | Read | Action |
|---|---|---|
| Hook rate (3s/impr) < 25% | Creative fails in the first second | Kill the ad. New concept, not a new crop. |
| Hold rate (thruplay/3s) < 15% | Middle sags | Same concept, tighter cut |
| CTR < 0.8% | Promise too weak | Rewrite hook + headline |
| CTR > 1.5%, CVR < 1% | Ad writes a cheque the PDP can't cash | Flag to human — it's a landing-page problem, not an ad problem |
| Frequency > 2.5 on cold | Audience fatigue | Refresh creative, do not raise budget |
| CPA within 20% of target | Working | Scale +20% max per 72h. Never double a budget. |

Kill an ad that has spent 3× target CPA with zero purchases. No exceptions, no "give it time".

## Output format

Write to `marketing/<YYYY-MM-DD>-meta/`:
- `ad-copy.md` — all 9 ads, formatted for direct paste into Ads Manager
- `bulk-import.csv` — Ads Manager bulk-sheet columns
- `creative/` — the rendered images/frames
- `targeting.md` — ad set specs including explicit `age_min: 18`
