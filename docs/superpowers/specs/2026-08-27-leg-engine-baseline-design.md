# Sprint 2 — Confirmed Leg Baseline Design

## Purpose
Build the smallest deterministic Leg Engine on top of locked Swing v1 without changing Swing behavior.

## Upstream contract
- Swing v1 is locked upstream.
- Primary Leg boundaries are consecutive **Major Swings** only.
- Structural/Internal Swings may be inspected later as inside-leg diagnostics, but they do not create primary Legs.
- Leg Engine must never repair, delete, merge, or reinterpret Swing output.
- Consecutive same-type Major Swings are an upstream invariant violation and produce `UPSTREAM_SWING_INVARIANT_ERROR`; no Leg is built across that pair.
- No Leg may cross an unexpected data-gap segment boundary.

## Confirmed Leg definition
- `Major SL -> next Major SH` = confirmed `BULLISH` Leg.
- `Major SH -> next Major SL` = confirmed `BEARISH` Leg.
- A confirmed Leg exists only after both endpoint Major Swings exist.
- Developing/Provisional/Live Legs are explicitly out of scope for this baseline.

## Baseline output
Each confirmed Leg exposes only measurement fields:
- `start`: upstream Major Swing at Leg origin.
- `end`: next opposite-type Major Swing.
- `direction`: `BULLISH` or `BEARISH`.
- `active_bar_count`: number of active market-bar intervals from start index to end index, defined as `end_index - start_index`.
- `net_thrust`: absolute endpoint price displacement, defined as `abs(end_price - start_price)`.

## Non-goals
This baseline does **not** classify Trend, Range, Money Entry, Correction, Leg Quality, Slope, Volume, Overlap, Wick, Directional Efficiency, or Internal Retracement. Those are later Sprint 2 steps after basic Leg construction is visually and quantitatively verified.

## Error behavior
The builder returns no fabricated Leg for invalid upstream pairs. The initial explicit invariant code is `UPSTREAM_SWING_INVARIANT_ERROR` for same-type consecutive Major Swings.

## Success criteria
1. Bullish and bearish confirmed Legs are built deterministically from alternating Major Swings.
2. `active_bar_count` and `net_thrust` are independently correct.
3. Same-type consecutive Major Swings are surfaced as an upstream error, not silently repaired.
4. Existing Swing v1 regression remains unchanged and green.
5. No Quality or Market-State logic is introduced.