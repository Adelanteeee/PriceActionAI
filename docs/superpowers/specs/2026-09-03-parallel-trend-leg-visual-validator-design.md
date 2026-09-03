# Parallel Trend Leg Visual Validator — Design

Date: 2026-09-03
Branch: `parallel-prototype-visual-leg-inspector`
Status: Approved by user for implementation.

## Purpose
Build the first Trend Leg visual-validation layer on top of the locked Swing and Leg engines without modifying their semantics. The prototype tests whether the user's visual Trend-Leg concept can be represented by existing Leg measurements plus one new close-location measurement.

## Hard constraints
- Locked Swing and existing Leg formulas remain unchanged.
- Task 12 / ablation stays paused.
- No weights, score, ML, optimization, or invented Trend threshold in v1.
- No Range/Choppy definition yet.
- Shadow and Activity remain visible diagnostics but are not Trend gates in v1.
- Multi-TF visual review must support M5, M15, M30, H1.

## Timeframe eligibility
The only hard v1 rule is `active_bar_count >= 4`.
- `<4`: `TF_UNDERSAMPLED`; review on a lower timeframe. This is not a Not-Trend label.
- `>=4`: `TF_ELIGIBLE_FOR_TREND_REVIEW`.
- 4–12 is a useful working region, not a hard upper bound.
- Long Legs may be reviewed on a higher timeframe rather than rejected.

## Existing evidence set
- `net_thrust`
- `normalized_directional_close_ols_slope`
- `body_strength_ratio`
- `directional_continuity_ratio`
- `directional_efficiency`
- `overlap_ratio`
- `active_bar_count`

All are descriptive evidence only in v1.

## New feature: Directional Close Location (DCL)
For each owned candle of a confirmed Leg:

Bullish:
`DCL_i = (Close_i - Low_i) / (High_i - Low_i)`

Bearish:
`DCL_i = (High_i - Close_i) / (High_i - Low_i)`

Expected range: `[0,1]` for valid OHLC candles.
If `High_i == Low_i`, DCL is undefined (`None`).

Terminal-third flag:
`terminal_third_i = DCL_i >= 2/3`

This defines the geometric terminal third only. It is not a Trend gate.

Leg aggregates:
- `mean_directional_close_location`
- `terminal_third_close_count`
- `defined_dcl_candle_count`
- `terminal_third_close_ratio = terminal_third_close_count / defined_dcl_candle_count`

Undefined zero-range candles are excluded from both aggregate denominators.

No special first/launch candle exemption exists in v1.

## Semantic states
The validator emits only:
- `TF_UNDERSAMPLED`
- `TF_ELIGIBLE_FOR_TREND_REVIEW`

It must not output automatic `TREND` / `NOT_TREND` in v1.

## Visual behavior
For each of M5/M15/M30/H1:
1. Fetch MT5 data.
2. Run locked Swing.
3. Build locked Legs.
4. Compute DCL externally without changing Leg v0.
5. Draw candles, Major Swing, and clickable Leg lines.
6. Mark owned candles whose DCL is in the terminal third.
7. Click panel shows existing Trend evidence plus DCL aggregates.
8. Export CSV and JSON summary/evidence.

## Acceptance criteria
1. Locked Swing/Leg source files unchanged.
2. Bullish/Bearish DCL unit tests pass.
3. Zero-range handling tested.
4. `DCL >= 2/3` boundary tested exactly.
5. Aggregation excludes undefined candles.
6. `<4` only produces undersampled state.
7. No score/weight/Trend threshold exists.
8. M5/M15/M30/H1 launcher supported.
9. Terminal-third candles are visibly marked.
10. CSV/JSON contains DCL aggregate fields.
