# Parallel Visual Swing + Leg Inspector Design

## Status
APPROVED FROM USER ARCHITECTURE BRIEF — 2026-09-02

## Purpose
Create a parallel, deliberately simple prototype path for visually inspecting real XAUUSD Swing and Leg behavior before any Trend/Range/Correction/Setup/Entry rules are encoded.

## Isolation Contract
- Start from the current Task 11 implementation HEAD.
- Do not modify the locked Swing Engine semantics.
- Do not modify the advanced Leg Engine semantics.
- Do not continue Task 12 / Controlled Ablation.
- Do not merge this branch into the frozen research path as part of this work.
- All prototype code lives on `parallel-prototype-visual-leg-inspector`.

## Existing Baseline
Use `PriceActionAI_Gold_DirectionalContinuity_Visual_Validator.py` as the behavioral baseline because it already provides:
- direct MetaTrader 5 connection,
- XAUUSD broker-symbol discovery,
- active-bar-based chart geometry,
- locked Swing pipeline execution,
- confirmed Leg overlay,
- Plotly visual output.

The new inspector must consume existing locked Leg outputs rather than invent new Leg features.

## Visual Inspector v1
The first retained prototype shall:
1. fetch real broker candles from MetaTrader 5;
2. run the existing locked Swing pipeline unchanged;
3. build confirmed Legs from accepted Swing Low→Swing High / Swing High→Swing Low pairs;
4. pass existing OHLC, Close, scheduled-gap and MT5 tick-volume inputs into the existing Leg Engine so existing locked Leg metrics are populated;
5. render candlesticks, accepted Swing spine and confirmed Legs in Plotly;
6. expose a complete per-Leg inspection payload containing only already-existing measurement outputs;
7. allow manual inspection through hover and clickable/selectable Leg traces in the generated HTML;
8. export a CSV containing the same per-Leg measurements for auditability.

## Existing Measurements Exposed
The inspector may expose only fields already produced by the current Leg Engine, including:
- `active_bar_count`
- `net_thrust`
- `gross_close_path`
- `net_close_displacement`
- `signed_close_displacement`
- `direction_agreement`
- `directional_efficiency`
- `aligned_close_steps`
- `opposing_close_steps`
- `flat_close_steps`
- `directional_continuity_ratio`
- `close_confirmation_ratio`
- `temporal_profile_tag`
- `gap_path_contribution`
- `gap_path_share`
- `gross_body_magnitude`
- `gross_candle_range`
- `body_strength_ratio`
- `gross_upper_shadow`
- `gross_lower_shadow`
- `gross_forward_shadow`
- `gross_backward_shadow`
- `gross_shadow_magnitude`
- `shadow_position_imbalance`
- `gross_overlap_magnitude`
- `gross_overlap_capacity`
- `overlap_ratio`
- `close_ols_slope`
- `directional_close_ols_slope`
- `normalized_directional_close_ols_slope`
- `gross_tick_activity`
- `mean_tick_activity`

## Explicit Non-Goals
Visual Inspector v1 must not create or infer:
- Trend Leg labels,
- Range / Choppy labels,
- Correction / Pullback labels,
- Balance labels,
- Starter / Trigger Candle rules,
- Setup or Entry rules,
- Feature weights,
- Feature scores,
- Thresholds,
- Accept/Reject gates,
- predictions or optimization.

Plotly is a manual validator. The program must not interpret chart appearance on the user's behalf.

## Interaction Model
Each Leg is an independent Plotly trace with a stable Leg number. Hover shows compact measurements. A small client-side click handler updates an on-page `Leg Inspector` panel with the full payload for the selected Leg. This is presentation only; selection does not modify calculations or classifications.

## Data Integrity
- Active Bar Index remains the geometric/time basis.
- Real timestamps remain visible for human review.
- Scheduled closures remain compressed according to the locked upstream contract.
- Unexpected gaps remain upstream hard segment boundaries.
- Tick Activity uses `tick_volume` only, matching the locked Activity contract.

## Verification
Automated tests must prove:
- no new semantic classification fields are introduced;
- the complete existing metric payload can be produced from a confirmed Leg;
- the Leg Engine receives OHLC, Close, tick-volume and scheduled-gap inputs required to populate existing metrics;
- generated HTML contains the click-driven Leg Inspector panel;
- existing locked engine files are not edited by this feature branch.
