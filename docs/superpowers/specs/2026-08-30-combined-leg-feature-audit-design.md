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
- tolerance policy
- verified rows
- failed rows

For ratio identities, a zero denominator that is defined by the Engine to produce `None` is **not** an identity failure.

### Locked deterministic tolerance policy
Tolerance is fixed by this design and must not be selected, inferred, widened, tuned, or changed at runtime.

- Integer/count identities: exact equality.
- `None`/definedness/status identities: exact semantic equality.
- Floating-point identities: `math.isclose(reconstructed, observed, rel_tol=1e-12, abs_tol=1e-12)`.

The provenance manifest must record:
```text
deterministic_float_rel_tol = 1e-12
deterministic_float_abs_tol = 1e-12
```

Any future change to these values requires a separate approved design change; the audit implementation may not adapt tolerance to the data.

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

### Missing-data and sample-size policy
For each pair report:
- `n_total`
- `n_valid_pairwise`
- `n_missing_x`
- `n_missing_y`
- `rho_raw`
- correlation status

Rules:
- pairwise complete observations only;
- no imputation;
- no silent zero-filling;
- undefined correlation is not converted to zero.

Status precedence for Main Raw Spearman:
1. if `n_valid_pairwise < 2`, report `UNDEFINED_INSUFFICIENT_OBSERVATIONS`;
2. otherwise, if either input is constant on the valid pairwise sample, report `UNDEFINED_CONSTANT_INPUT`;
3. otherwise compute `rho_raw`.

No qualitative interpretation is attached to the magnitude.

## Duration-Controlled Partial Spearman contract
Control variable:
```text
active_bar_count
```

Partial Spearman is calculated only when:
- the pair is main-pair eligible by role/direction/numeric rules;
- `X != active_bar_count`;
- `Y != active_bar_count`.

### Triple-complete sample
The controlled calculation uses the exact sample on which all three values are defined:

```text
X + Y + active_bar_count
```

Let:
```text
n_valid_triple = number of triple-complete observations
```

No row excluded from the Partial calculation may be used in the raw comparator for `delta_rho`.

### Exact method
On the exact triple-complete sample:
1. if `n_valid_triple < 3`, report `UNDEFINED_INSUFFICIENT_OBSERVATIONS`;
2. convert `X`, `Y`, and `active_bar_count` to ranks;
3. use **average ranks for ties**;
4. if any required ranked input is constant, report `UNDEFINED_CONSTANT_INPUT`;
5. regress ranked `X` on ranked `active_bar_count` with an intercept;
6. regress ranked `Y` on ranked `active_bar_count` with an intercept;
7. if either residual series is constant, report `UNDEFINED_CONSTANT_INPUT`;
8. compute the ordinary correlation of the two residual series as `rho_duration_controlled`.

### Raw comparator used for delta
The Main Raw Spearman matrix remains defined independently on the pairwise-complete `X + Y` sample.

For `delta_rho`, however, use a separate raw value calculated on the **same triple-complete sample** used by Partial Spearman:

```text
rho_raw_for_delta
= Spearman(X, Y)
  on the exact same triple-complete sample
```

Then:
```text
delta_rho
= rho_duration_controlled - rho_raw_for_delta
```

The main pairwise `rho_raw` and `rho_raw_for_delta` are distinct reported values and must not be silently substituted for one another.

Required Partial report outputs:
- `rho_raw_for_delta`
- `rho_duration_controlled`
- `delta_rho`
- `n_valid_triple`
- status

The controlled statistic is a statistical adjustment only. It must never be described as causal.

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

The same missing, insufficient-observation, and constant-input semantics used by the corresponding raw or controlled calculation apply inside each direction stratum.

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
- `n_positive_tf`
- `n_negative_tf`
- `n_zero_tf`
- `n_undefined_tf`
- `sign_agreement_count`
- `sign_agreement_tie`
- `sign_agreement_modal_signs`
- `rho_min`
- `rho_max`
- `rho_range`

### Cross-TF sign accounting
For the four per-TF raw `rho` values:

```text
n_positive_tf  = count(defined rho_TF > 0)
n_negative_tf  = count(defined rho_TF < 0)
n_zero_tf      = count(defined rho_TF == 0)
n_undefined_tf = count(undefined rho_TF)
```

Then:
```text
sign_agreement_count
= max(n_positive_tf, n_negative_tf, n_zero_tf)
```

Only defined values participate in positive/negative/zero counts. Undefined values are counted only in `n_undefined_tf` and never converted to zero.

If more than one of `n_positive_tf`, `n_negative_tf`, and `n_zero_tf` equals `sign_agreement_count`, report:
```text
sign_agreement_tie = true
```

and list every tied modal sign in:
```text
sign_agreement_modal_signs
```

No modal sign may be selected arbitrarily in a tie. If there is no defined rho value, `sign_agreement_count`, `sign_agreement_tie`, and `sign_agreement_modal_signs` remain undefined rather than fabricating a sign result.

### Cross-TF range
```text
rho_range = max(defined rho_TF values) - min(defined rho_TF values)
```

Undefined timeframe values remain undefined and are excluded from min/max/range calculations. They are never replaced with zero.

All sign fields are descriptive only. A tiny positive or negative rho still has a mathematical sign, but sign agreement by itself must never be interpreted as meaningful stability.

The same no-pooling rule applies to controlled values: each `controlled_rho_TF` is computed independently within that TF.

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
   - conditions
   - fixed tolerance policy
   - verified/failed counts

3. Per-timeframe `MAIN_SPEARMAN_PAIR_REPORT`
   - all eligible pairs
   - missingness/sample-size fields
   - raw rho/status

4. Per-timeframe `PARTIAL_SPEARMAN_PAIR_REPORT`
   - `rho_raw_for_delta` on triple-complete sample
   - controlled rho
   - delta rho
   - triple-complete sample size/status

5. Per-timeframe and direction `SUPPLEMENTARY_DIRECTION_STRATIFIED_REPORT`

6. `CROSS_TF_RELATIONSHIP_REPORT`
   - separate per-TF raw/controlled values
   - positive/negative/zero/undefined TF counts
   - descriptive sign agreement, tie state, and range fields

7. Provenance manifest
   - source commit
   - input audit package/snapshot hashes
   - symbol
   - broker/server
   - timeframes
   - audit version
   - `deterministic_float_rel_tol = 1e-12`
   - `deterministic_float_abs_tol = 1e-12`

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
4. deterministic integer/status identities use exact equality and floating identities use fixed `rel_tol=1e-12`, `abs_tol=1e-12`;
5. Raw Spearman is computed only within one timeframe at a time and uses pairwise-complete `X + Y` observations;
6. Main Raw Spearman reports insufficient when `n_valid_pairwise < 2`, then separately checks constant inputs;
7. Partial Spearman controls only `active_bar_count` using triple-complete observations, average tie ranks, ranked residual regression with intercept, and `n_valid_triple >= 3`;
8. `rho_raw_for_delta` is recalculated on the exact triple-complete Partial sample, and `delta_rho` never uses the main pairwise raw rho unless the samples happen to be identical;
9. missingness and sample sizes are explicit for every pair; no imputation or zero-filling occurs;
10. constant/insufficient cases remain undefined with explicit status;
11. raw direction-sensitive fields are excluded from the combined Bull+Bear main matrix and audited only in supplementary same-direction groups;
12. cross-timeframe output compares independently computed relationships, reports positive/negative/zero/undefined counts and ties explicitly, and never pools raw rows;
13. no outcome, prediction, score, threshold, qualitative strength label, optimization, or causal claim is introduced.
