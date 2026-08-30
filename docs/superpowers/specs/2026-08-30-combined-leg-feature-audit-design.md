# Sprint 2 — Combined Leg Feature Audit Design

## Purpose
Freeze the current confirmed-Leg feature set and evaluate **within-timeframe dependency, deterministic redundancy, duration sensitivity, and cross-timeframe relationship consistency** before any outcome, prediction, scoring, thresholding, or causal replay work.

This phase is descriptive and structural only. It must not alter Swing v1, the Leg Engine, any locked metric formula, or any historical output.

## Locked scope

### Primary analysis unit
Each timeframe is analyzed independently:
- `M5`
- `M15`
- `M30`
- `H1`

Raw observations from different timeframes must never be pooled for a primary dependency calculation.

### Secondary cross-timeframe role
Cross-timeframe analysis is descriptive only. For each feature pair, compute the relationship separately in M5, M15, M30, and H1, then compare those four results.

Cross-timeframe analysis must not:
- concatenate raw rows across timeframes;
- become the basis of a primary conclusion;
- hide an undefined timeframe result by replacing it with zero.

### Explicitly out of scope
- Future outcome
- Profit / Loss
- MFE / MAE
- Prediction
- Good / Bad labels
- Thresholds
- Scores
- Feature weights
- Accept / Reject rules
- Optimization
- PCA
- Mutual Information
- Clustering
- Raw cross-timeframe pooling
- Causal interpretation

## Statistical approach
The approved approach is:

1. **Deterministic Audit**
2. **Pairwise Spearman**
3. **Duration-Controlled Partial Spearman**
4. **Cross-TF Relationship Consistency**

No arbitrary correlation cutoff or qualitative strength label is permitted in this phase.

Forbidden labels include:
- `STRONG`
- `WEAK`
- `STABLE`
- `UNSTABLE`
- `REDUNDANT`
- `ORTHOGONAL`

Only raw values, missingness, sample sizes, and deterministic identity results are reported.

## Frozen main feature set
Exactly these 13 columns are the main `ANALYSIS_FEATURE` set:

1. `active_bar_count`
2. `net_thrust`
3. `gross_close_path`
4. `net_close_displacement`
5. `directional_efficiency`
6. `directional_continuity_ratio`
7. `close_confirmation_ratio`
8. `gap_path_share`
9. `body_strength_ratio`
10. `shadow_position_imbalance`
11. `overlap_ratio`
12. `normalized_directional_close_ols_slope`
13. `mean_tick_activity`

No fourteenth main feature may be introduced during this audit without a separate approved design change.

## Feature role architecture
Every relevant Leg column must have an explicit role.

### `ANALYSIS_FEATURE`
Eligible for the main within-timeframe Bull+Bear Spearman matrix when all pair-eligibility rules are satisfied.

### `SUPPORTING_COMPONENT`
Used to explain, reconstruct, or inspect a locked metric but not treated as an independent main statistical feature.

### `IDENTITY_COMPONENT`
Participates in a deterministic formula and is excluded from the main statistical evidence set to avoid double-counting definition-derived information.

### `RAW_DIRECTION_SENSITIVE`
Excluded from the combined Bull+Bear main matrix. Eligible only in supplementary same-timeframe, same-direction audits.

### `CATEGORICAL / METADATA / DIAGNOSTIC`
Excluded from correlation matrices. Used only for stratification, provenance, traceability, or audit status.

## Direction semantics
Classification is formula-based, not name-based.

### Direction-neutral main features
- `active_bar_count`
- `net_thrust = abs(end_price - start_price)`
- `gross_close_path`
- `net_close_displacement = abs(close_end - close_start)`
- `gap_path_share`
- `body_strength_ratio`
- `overlap_ratio`
- `mean_tick_activity`

### Direction-normalized / direction-relative main features
- `directional_efficiency`
- `directional_continuity_ratio`
- `close_confirmation_ratio`
- `shadow_position_imbalance`
- `normalized_directional_close_ols_slope`

These may participate in the combined Bull+Bear main matrix because structural direction is already represented in their definitions.

### Raw direction-sensitive fields
- `close_ols_slope`
- `gross_upper_shadow`
- `gross_lower_shadow`

These are excluded from the combined-direction main matrix.

They may be audited only as:
- M5 Bullish-only
- M5 Bearish-only
- M15 Bullish-only
- M15 Bearish-only
- M30 Bullish-only
- M30 Bearish-only
- H1 Bullish-only
- H1 Bearish-only

The stratified results are supplementary evidence only and must not be counted as a second independent confirmation of a relationship already present in the main matrix.

### Direction-relative supporting fields
- `gross_forward_shadow`
- `gross_backward_shadow`
- `directional_close_ols_slope`

These remain supporting/identity components, not main features.

## Supporting and identity components
The following are excluded from the main Raw Spearman, main Partial Spearman, and primary Cross-TF evidence tables:

- `signed_close_displacement`
- `aligned_close_steps`
- `opposing_close_steps`
- `flat_close_steps`
- `gap_path_contribution`
- `gross_body_magnitude`
- `gross_candle_range`
- `gross_forward_shadow`
- `gross_backward_shadow`
- `gross_shadow_magnitude`
- `gross_overlap_magnitude`
- `gross_overlap_capacity`
- `directional_close_ols_slope`
- `gross_tick_activity`
- derived `mean_candle_range`

If any is inspected statistically, the result must be explicitly labeled `SUPPLEMENTARY_COMPONENT_AUDIT`. Such inspection does not promote the field to `ANALYSIS_FEATURE`.

## Non-feature fields
The following must never be treated as ordinary numeric features:
- IDs
- start/end objects
- start/end indexes
- timestamps
- `symbol`
- `timeframe`
- broker/server metadata
- snapshot hashes
- status fields
- diagnostic flags
- categorical labels
- manifest fields
- `direction_agreement`
- `temporal_profile_tag`

`direction` is used only for stratification.

## Deterministic registry
Deterministic relationships are audited in a separate registry and take precedence over any statistical result.

A Partial Spearman value can never make components of a deterministic identity independent evidence.

Each registry row must report:
- `relation_type = DETERMINISTIC`
- formula
- participating features
- conditions
- tolerance
- verified rows
- failed rows

For ratio identities, a zero denominator that is defined by the Engine to produce `None` is **not** an identity failure.

### Close displacement identity
Condition: `direction_sign ∈ {-1,+1}`.

```text
net_close_displacement = abs(signed_close_displacement)
```

### Directional continuity identities
```text
aligned_close_steps + opposing_close_steps + flat_close_steps
= active_bar_count
```

When `active_bar_count > 0`:
```text
directional_continuity_ratio
= aligned_close_steps / active_bar_count
```

### Body Strength identity
When `gross_candle_range > 0`:
```text
body_strength_ratio
= gross_body_magnitude / gross_candle_range
```

When `gross_candle_range == 0`:
```text
body_strength_ratio = None
```

### Gap Path identity
When `gross_close_path > 0`:
```text
gap_path_share
= gap_path_contribution / gross_close_path
```

When `gross_close_path == 0`:
```text
gap_path_share = None
```

### Shadow identities
```text
gross_shadow_magnitude
= gross_forward_shadow + gross_backward_shadow
```

When `gross_shadow_magnitude > 0`:
```text
shadow_position_imbalance
= (gross_backward_shadow - gross_forward_shadow)
  / gross_shadow_magnitude
```

When `gross_shadow_magnitude == 0`:
```text
shadow_position_imbalance = None
```

Locked sign semantics:
- positive -> Backward-shadow dominance
- zero -> equal Forward / Backward
- negative -> Forward-shadow dominance

### Overlap identity
When `gross_overlap_capacity > 0`:
```text
overlap_ratio
= gross_overlap_magnitude / gross_overlap_capacity
```

When `gross_overlap_capacity == 0`:
```text
overlap_ratio = None
```

### Slope direction identity
```text
direction_sign = +1 for Bullish
                 -1 for Bearish
```

```text
directional_close_ols_slope
= direction_sign * close_ols_slope
```

### Slope normalization identity
When `active_bar_count > 0`:
```text
mean_candle_range
= gross_candle_range / active_bar_count
```

Otherwise:
```text
mean_candle_range = None
```

When `mean_candle_range is not None` and `mean_candle_range > 0`:
```text
normalized_directional_close_ols_slope
= directional_close_ols_slope / mean_candle_range
```

Otherwise:
```text
normalized_directional_close_ols_slope = None
```

`mean_candle_range` is a derived supporting component, not a fourteenth main feature.

### Tick Activity identity
```text
gross_tick_activity
= mean_tick_activity * active_bar_count
```

This identity establishes that Gross Activity, Mean Activity, and Duration are not statistically independent features.

## Main Raw Spearman contract
A pair is eligible only when:

```text
both roles = ANALYSIS_FEATURE
AND both inputs are numeric
AND both belong to the same timeframe
AND direction semantics permit Bull+Bear combination
AND pairwise-complete observations are used
AND both valid inputs are non-constant
```

### Missing-data policy
For each pair report:
- `n_total`
- `n_valid_pairwise`
- `n_missing_x`
- `n_missing_y`
- `rho_raw`

Rules:
- pairwise complete observations only;
- no imputation;
- no silent zero-filling;
- undefined correlation is not converted to zero.

If an eligible input is constant on the valid pairwise sample, report:
```text
UNDEFINED_CONSTANT_INPUT
```

If valid observations are insufficient for the correlation calculation, report:
```text
UNDEFINED_INSUFFICIENT_OBSERVATIONS
```

No qualitative interpretation is attached to the magnitude.

## Duration-Controlled Partial Spearman contract
Control variable:
```text
active_bar_count
```

Partial Spearman is calculated only when:
- the pair is main-pair eligible;
- `X != active_bar_count`;
- `Y != active_bar_count`.

### Exact method
For the pairwise-complete sample of `X`, `Y`, and `active_bar_count`:
1. convert each variable to ranks;
2. use **average ranks for ties**;
3. regress ranked `X` on ranked `active_bar_count` with an intercept;
4. regress ranked `Y` on ranked `active_bar_count` with an intercept;
5. compute the ordinary correlation of the two residual series.

Required outputs:
- `rho_raw`
- `rho_duration_controlled`
- `delta_rho = rho_duration_controlled - rho_raw`
- `n_valid`

The controlled statistic is a statistical adjustment only. It must never be described as causal.

If either residual series is constant:
```text
UNDEFINED_CONSTANT_INPUT
```

If valid observations are insufficient:
```text
UNDEFINED_INSUFFICIENT_OBSERVATIONS
```

## Supplementary direction-stratified audit
A stratified pair is eligible only when:

```text
same timeframe
AND same leg direction
AND each input is either ANALYSIS_FEATURE
    or RAW_DIRECTION_SENSITIVE
AND numeric
AND pairwise complete
AND both valid inputs are non-constant
```

Supporting and identity components remain excluded unless a separate result is explicitly emitted under `SUPPLEMENTARY_COMPONENT_AUDIT`.

No stratified result upgrades, duplicates, or overrides main-matrix evidence.

## Cross-timeframe consistency report
For every eligible main feature pair, report the separately calculated within-TF values:

- `rho_M5`
- `rho_M15`
- `rho_M30`
- `rho_H1`
- `controlled_rho_M5`
- `controlled_rho_M15`
- `controlled_rho_M30`
- `controlled_rho_H1`
- `n_valid_M5`
- `n_valid_M15`
- `n_valid_M30`
- `n_valid_H1`
- `sign_agreement_count`
- `rho_min`
- `rho_max`
- `rho_range`

Definition:
```text
rho_range = max(defined rho_TF values) - min(defined rho_TF values)
```

Undefined timeframe values remain undefined and are excluded from min/max/range calculations. They are never replaced with zero.

`sign_agreement_count` is descriptive only. A tiny positive or negative rho still has a mathematical sign, but sign agreement by itself must never be interpreted as meaningful stability.

## Deterministic precedence rule
For any pair or feature set that participates in a deterministic identity:

```text
Deterministic Identity > Statistical Result
```

Statistical outputs may be displayed for observation, but they cannot be used to reject the identity or to claim independent information among identity-linked components.

## Required outputs of the future audit implementation
The implementation plan may refine file names, but the audit must preserve these logical artifacts:

1. `FEATURE_ROLE_MATRIX`
   - feature
   - formula or source definition
   - sign semantics
   - direction semantics
   - analysis role
   - pairwise eligible
   - controlled eligible
   - stratified audit eligible

2. `DETERMINISTIC_IDENTITY_REPORT`
   - one row/result per locked identity
   - conditions and tolerance
   - verified/failed counts

3. Per-timeframe `MAIN_SPEARMAN_PAIR_REPORT`
   - all eligible pairs
   - missingness/sample-size fields
   - raw rho/status

4. Per-timeframe `PARTIAL_SPEARMAN_PAIR_REPORT`
   - controlled rho
   - delta rho
   - sample size/status

5. Per-timeframe and direction `SUPPLEMENTARY_DIRECTION_STRATIFIED_REPORT`

6. `CROSS_TF_RELATIONSHIP_REPORT`
   - separate per-TF raw/controlled values
   - descriptive sign agreement and range fields

7. Provenance manifest
   - source commit
   - input audit package/snapshot hashes
   - symbol
   - broker/server
   - timeframes
   - audit version

## Non-regression requirements
This audit is a consumer of frozen outputs. It must not change:
- Swing v1 source or output;
- Leg Engine source or output;
- any locked metric formula;
- feature values;
- historical snapshots.

The implementation should read locked Leg outputs/evidence and compute audit-only artifacts separately.

Any requirement to modify Engine semantics discovered during implementation is a blocker and requires a separate design/change request.

## Success criteria
The design is satisfied when the future implementation can demonstrate all of the following without changing Engine behavior:

1. exactly 13 main analysis features are used;
2. feature roles and direction semantics are explicit and machine-verifiable;
3. deterministic identities are checked separately and take precedence over statistical results;
4. Raw Spearman is computed only within one timeframe at a time;
5. Partial Spearman controls only `active_bar_count` using ranked residual regression with intercept and average tie ranks;
6. missingness and pairwise sample sizes are explicit for every pair;
7. constant/insufficient cases remain undefined with explicit status, never zero-filled;
8. raw direction-sensitive fields are excluded from the combined Bull+Bear main matrix and audited only in supplementary same-direction groups;
9. cross-timeframe output compares independently computed relationships and never pools raw rows;
10. no outcome, prediction, score, threshold, qualitative strength label, optimization, or causal claim is introduced.
