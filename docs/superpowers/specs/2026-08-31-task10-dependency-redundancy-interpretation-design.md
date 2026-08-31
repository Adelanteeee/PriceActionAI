# Sprint 2 — Task 10 Dependency / Redundancy Interpretation Design

## Status

**DESIGN APPROVED FOR FORMAL SPEC WRITING**

This document defines Task 10 only. It does not authorize Task 10 execution.
Execution requires a separate explicit human approval after this Spec is reviewed and locked.

## Purpose

Task 10 adds a descriptive interpretation layer on top of the Final-Locked Task 9 Gold Combined Audit evidence.

Task 10 must answer only structural questions such as:
- which main-feature associations persist or change after controlling for `active_bar_count`;
- whether the mathematical sign of a relationship is consistent or mixed across M5/M15/M30/H1;
- how much the within-TF raw relationship varies across defined timeframes;
- whether Bullish/Bearish supplementary evidence differs from the combined main relationship;
- which observations should be carried forward as hypotheses for a future Ablation phase.

Task 10 is non-decision-making. It must not select, delete, rank, score, weight, accept, reject, optimize, or promote any feature.

## Immutable upstream evidence

Task 9 and its evidence package are immutable inputs.

Canonical Task 9 Evidence Package:

```text
GOLD_COMBINED_LEG_FEATURE_AUDIT_PACKAGE.zip
SHA-256:
968f4826858a0bbb8254218711f4ad3e3487370ca8d0f288133ee36f7a4fa40d
```

Task 10 must not rewrite, regenerate, normalize, repackage, or replace Task 9 artifacts.
It may only read them and produce separate Task 10 artifacts.

Task 9 provenance remains authoritative:
- canonical Activity input SHA-256: `1e9f13fd88fc1e8e0e66d801be8c15d726639eaea25e53fef7c3bb88bfd05192`;
- audit-code commit: `1c40cd3d3507c473fd07ea25c010d386be8a0043`;
- Task 9 registration commit: `78e54fb50ce82a0cba7f91f40a6451e82996008d`.

## Frozen main feature set

Task 10 uses exactly the 13 Task 9 main analysis features:

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

No new main feature may be introduced in Task 10.

## Hard scope boundary

### In scope

- deterministic-relationship context from Task 9;
- the 78 main within-TF feature pairs;
- raw Spearman values from M5/M15/M30/H1;
- duration-controlled Partial Spearman for eligible pairs only;
- `rho_raw_for_delta` and `delta_rho` for eligible pairs only;
- Task 9 cross-TF sign accounting;
- Task 9 cross-TF defined-value range information;
- Bullish/Bearish supplementary evidence as a separate evidence layer;
- descriptive synthesis of the evidence;
- non-ranked hypotheses for a future Ablation phase.

### Explicitly out of scope

- any modification to Task 9;
- any modification to Swing, Leg Engine, or locked metric semantics;
- Future Outcome;
- Profit/Loss;
- MFE/MAE;
- Prediction;
- Good/Bad labels;
- Score;
- Threshold;
- Feature Weight;
- Accept/Reject rule;
- Optimization;
- PCA;
- Mutual Information;
- Clustering;
- raw cross-timeframe pooling;
- causal interpretation;
- Ablation execution;
- Causal Replay;
- feature removal;
- feature promotion;
- feature ranking.

## Prohibited decision language

Task 10 must not create a qualitative classification or magnitude label.

Forbidden examples include, but are not limited to:
- `STRONG`
- `WEAK`
- `STABLE`
- `UNSTABLE`
- `REDUNDANT`
- `ORTHOGONAL`
- `NEAR_DUPLICATE`
- `KEEP`
- `DROP`
- `BEST`
- `WORST`
- `IMPORTANT`
- `UNIMPORTANT`

No arbitrary or data-derived cutoff may convert a continuous statistic into a categorical decision.

Task 10 may describe the observed numbers and exact changes only.

## Primary analysis unit: 78 Main Relationship Dossiers

With 13 main features, Task 10 has exactly:

```text
13 choose 2 = 78
```

Therefore:

```text
Main Relationship Dossiers
→ exactly 78 pairs
```

Each unordered main pair appears exactly once.
No supplementary-only pair may increase this count.

Each Main Relationship Dossier is the primary evidence record for one main pair.

### Required dossier fields

Each dossier must contain at least:

#### Identity
- `feature_x`
- `feature_y`
- canonical pair key with deterministic ordering;
- Task 9 role of each feature;
- whether an exact deterministic identity directly links the pair;
- relevant deterministic context, if any.

#### Raw within-TF evidence
For each of M5/M15/M30/H1:
- `rho_raw_TF`
- `raw_status_TF`
- `n_valid_pairwise_TF`
- missingness fields available from Task 9.

The values must be read from Task 9 Main Raw reports and must not be recomputed with different semantics.

#### Duration-controlled evidence
For eligible pairs only:
- `rho_raw_for_delta_TF`
- `rho_duration_controlled_TF`
- `delta_rho_TF`
- `n_valid_triple_TF`
- `partial_status_TF`.

The values must be read from Task 9 Partial reports and retain the exact Task 9 same-sample discipline.

#### Cross-TF descriptive evidence
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
- `n_defined_tf`.

No field in this group is a stability score or decision criterion.

#### Supplementary references
Where available, the dossier may reference Bullish/Bearish supplementary rows for the same main pair.
Supplementary observations remain explicitly secondary and must not be counted as an additional independent confirmation.

#### Descriptive synthesis
A dossier may state only observations directly supported by the numbers, for example:
- the raw sign is positive in three defined TFs and negative in one;
- the controlled value is defined in all four TFs;
- `delta_rho` is negative in M5 and positive in M15;
- the Bullish and Bearish stratified values have opposite mathematical signs;
- a relationship remains defined after duration control.

It must not convert those observations into a categorical strength, importance, redundancy, or removal recommendation.

## Partial / delta eligibility contract

The control feature is:

```text
active_bar_count
```

Exactly 12 of the 78 main pairs contain `active_bar_count`.
Those 12 pairs are not eligible for a Partial Spearman that controls for the same feature.

Therefore:

```text
Partial / delta_rho eligible
→ exactly 66 pairs
```

For each of the 12 pairs where either side is `active_bar_count`, the dossier must explicitly record:

```text
partial_rho → NOT_APPLICABLE_CONTROL_FEATURE
delta_rho   → NOT_APPLICABLE_CONTROL_FEATURE
```

This is not an undefined statistical result and must not be represented as:
- zero;
- missing data;
- failed calculation;
- insufficient observations;
- constant input.

It is a structural non-applicability state caused by the control-feature contract.

No substitute control variable is permitted in Task 10.

## Raw versus controlled interpretation contract

For the 66 eligible pairs, Task 10 may compare:

```text
rho_raw_for_delta
rho_duration_controlled
delta_rho = rho_duration_controlled - rho_raw_for_delta
```

Only values from the same Task 9 triple-complete sample may be compared through `delta_rho`.

The Main Raw `rho_raw` calculated on the pairwise-complete sample must remain distinguishable from `rho_raw_for_delta`.
Task 10 must not silently substitute one for the other.

Permitted descriptive statement:

```text
On the Task 9 triple-complete sample, rho changed from A to B after the duration adjustment; delta_rho = C.
```

Forbidden statement:

```text
Duration caused the relationship to weaken/strengthen.
```

The adjustment is statistical, not causal.

## Cross-TF range contract

For every main pair:

```text
rho_range
→ computed only from defined Task 9 raw rho values
```

Task 10 must also report:

```text
n_defined_tf
```

where:

```text
n_defined_tf = 4 - n_undefined_tf
```

or equivalently the count of defined raw `rho_TF` values.

Rules:
- undefined TF values are never replaced with zero;
- undefined TF values do not participate in `rho_min`, `rho_max`, or `rho_range`;
- if no TF is defined, `rho_min`, `rho_max`, and `rho_range` remain undefined;
- if exactly one TF is defined, `rho_min = rho_max` and `rho_range = 0` is mathematically valid, but the dossier must retain `n_defined_tf = 1` so the value cannot be mistaken for four-TF agreement;
- `rho_range` must never be interpreted by a cutoff or converted into a stability label.

Task 10 should use the Task 9 cross-TF report as the authoritative source and may reconstruct `n_defined_tf` only from Task 9 definedness/sign-count fields as an audit check.

## Cross-TF sign contract

Task 10 inherits Task 9 sign semantics exactly.

For the four raw within-TF `rho` values:
- positive, negative, and exact zero are counted only when defined;
- undefined values are counted only in `n_undefined_tf`;
- ties in modal sign remain ties;
- no tied modal sign is selected arbitrarily.

Task 10 may state the exact sign counts.
It must not convert sign agreement into a qualitative stability or importance judgment.

## Supplementary evidence boundary

Task 9 supplementary reports contain 120 raw pair rows per direction per timeframe from the allowed supplementary universe.

Task 10 preserves this boundary:

```text
78 Main Pairs
→ Primary Main Relationship Dossiers
```

```text
120 Bull/Bear Stratified Pairs per direction per TF
→ Supplementary Evidence only
```

Pairs containing a `RAW_DIRECTION_SENSITIVE` feature remain supplementary and must never enter the 78 Main Relationship Dossiers.

The raw direction-sensitive fields remain:
- `close_ols_slope`
- `gross_upper_shadow`
- `gross_lower_shadow`.

A supplementary pair containing any of those fields may be described only inside the Supplementary Evidence layer.
It must not:
- create a new Main Relationship Dossier;
- be promoted into the 13-feature main universe;
- be counted as independent primary confirmation;
- trigger feature selection or deletion.

For a supplementary row whose pair contains `active_bar_count`, controlled fields remain subject to the Task 9 control-feature non-eligibility semantics.

## Deterministic precedence

Task 10 inherits the locked rule:

```text
Deterministic Identity > Statistical Result
```

If Task 9 identifies a deterministic relationship, Task 10 must present that fact before any statistical association involving the same identity-linked quantities.

No Spearman, Partial Spearman, cross-TF sign pattern, or supplementary result may override a deterministic identity or be used to claim independent information between definition-linked components.

Task 10 must not invent new deterministic identities.

## Feature Dossiers

In addition to the 78 pair dossiers, Task 10 may produce exactly one Feature Dossier for each of the 13 main features.

Therefore:

```text
Feature Dossiers
→ exactly 13
```

A Feature Dossier is an index and evidence synthesis, not a ranking record.

It may contain:
- the feature definition and role;
- deterministic context;
- links to its 12 Main Relationship Dossiers;
- exact raw/controlled/cross-TF observations already contained in those dossiers;
- references to relevant Bull/Bear supplementary evidence;
- non-ranked hypotheses for future Ablation.

It must not contain:
- importance rank;
- aggregate score;
- weighted average correlation;
- keep/drop recommendation;
- feature priority.

## Ablation hypotheses contract

Task 10 may record hypotheses for a future Ablation phase, but Task 10 must not execute or simulate Ablation.

Each hypothesis must be phrased as a question or testable proposition, not a conclusion.

Permitted form:

```text
Future Ablation hypothesis:
Test whether removing Feature X changes the incremental information available when Feature Y is retained.
```

Forbidden form:

```text
Feature X is redundant and should be removed.
```

Hypotheses:
- must cite the exact Task 10 dossier observations that motivated them;
- must not be ranked or prioritized;
- must not contain a threshold;
- must not claim expected trading performance;
- must remain explicitly untested.

Ablation remains **NOT AUTHORIZED** until separately approved.

## No new statistical model

Task 10 is an interpretation layer, not a new statistical-estimation phase.

Unless a separate design change is approved, Task 10 must not calculate a new association statistic beyond deterministic reconstruction checks needed to verify transcription of Task 9 evidence.

In particular, Task 10 must not introduce:
- Pearson correlation as a new evidence stream;
- Kendall correlation;
- regression coefficients as feature evidence;
- p-value screening;
- confidence-interval ranking;
- composite dependency indices;
- graph centrality scores;
- distance metrics;
- learned embeddings.

The evidence base remains the Final-Locked Task 9 outputs.

## Required logical outputs

An implementation plan may refine physical file formats, but Task 10 execution must preserve these logical artifacts:

### 1. `TASK10_MAIN_RELATIONSHIP_DOSSIERS`
- exactly 78 main pair records;
- complete raw within-TF Task 9 evidence;
- exactly 66 Partial/delta-eligible pair records;
- exactly 12 control-feature non-applicable pair records;
- cross-TF sign/range fields including `n_defined_tf`;
- deterministic context;
- optional references to same-pair supplementary evidence;
- descriptive observations only.

### 2. `TASK10_SUPPLEMENTARY_EVIDENCE`
- remains separate from the 78 primary dossiers;
- preserves TF and direction stratification;
- preserves Task 9 statuses and sample counts;
- keeps every pair containing a raw direction-sensitive feature outside primary evidence.

### 3. `TASK10_FEATURE_DOSSIERS`
- exactly 13 feature records;
- evidence-index role only;
- no ranking, scoring, weighting, or recommendation.

### 4. `TASK10_FUTURE_ABLATION_HYPOTHESES`
- zero or more non-ranked, explicitly untested hypotheses;
- each hypothesis traceable to exact dossier evidence;
- no Ablation result.

### 5. `TASK10_MANIFEST`
Must record at least:
- Task 9 Evidence Package filename;
- Task 9 Evidence Package SHA-256;
- Task 10 code/implementation commit when execution is later authorized;
- Task 10 Spec commit;
- counts of Main Relationship Dossiers, Partial-eligible pairs, control-feature non-applicable pairs, Feature Dossiers, and supplementary evidence rows consumed;
- explicit flags showing no ranking, cutoff, score, outcome, Ablation, Causal Replay, or raw cross-TF pooling was performed.

## Validation gates for future execution

Task 10 execution, if later authorized, must fail closed when any of these conditions is violated:

1. Task 9 Evidence Package SHA-256 does not equal the canonical locked SHA.
2. Main pair count is not exactly 78.
3. Partial/delta eligible pair count is not exactly 66.
4. Control-feature non-applicable pair count is not exactly 12.
5. Any `active_bar_count` pair receives a computed Partial or `delta_rho` value instead of `NOT_APPLICABLE_CONTROL_FEATURE`.
6. Any undefined TF is converted to zero for cross-TF calculations.
7. `n_defined_tf + n_undefined_tf != 4` for any main pair.
8. Any pair containing a raw direction-sensitive feature enters the 78 main dossiers.
9. Any qualitative ranking, strength label, cutoff, keep/drop decision, feature weight, Score, Outcome, Ablation result, or causal claim is emitted.
10. Any Swing, Leg Engine, locked metric implementation, or Task 9 artifact is modified.

## Traceability and reproducibility

Every Task 10 statement must be traceable to:
- the main-pair key or supplementary-pair key;
- timeframe;
- direction where applicable;
- Task 9 source artifact;
- Task 9 source row/status;
- exact numeric values used in the statement.

No prose conclusion may rely on a hidden aggregation or undocumented transformation.

Task 10 outputs must be reproducible from the canonical Task 9 Evidence Package alone plus the locked Task 10 implementation version.

## Definition of Done for Task 10 Design

This Design is ready to be locked when all of the following are true:

- Task 9 remains immutable.
- Main Relationship Dossiers are fixed at 78.
- Partial/delta eligibility is fixed at 66.
- The 12 `active_bar_count` pairs use `NOT_APPLICABLE_CONTROL_FEATURE` for Partial and delta.
- `rho_range` uses defined TFs only and is always accompanied by `n_defined_tf`.
- undefined TF values are never zero-filled.
- Bull/Bear supplementary evidence remains separate from primary evidence.
- raw direction-sensitive pairs cannot enter the 78 Main Relationship Dossiers.
- no ranking, cutoff, qualitative label, feature removal recommendation, Score, Outcome, Ablation, Causal Replay, or causal interpretation is permitted.
- future Ablation hypotheses are unranked, traceable, explicitly untested, and do not authorize Ablation.
- Task 10 execution remains blocked pending a separate explicit human authorization after Spec lock.

## Authorization gate

Current authorization state:

```text
Task 10 Design                 → APPROVED
Formal Spec Writing            → AUTHORIZED
Task 10 Execution              → NOT AUTHORIZED
Ablation                       → NOT AUTHORIZED
Causal Replay                  → NOT AUTHORIZED
Score / Threshold              → NOT AUTHORIZED
Feature Removal / Selection    → NOT AUTHORIZED
```

After this Spec is reviewed and explicitly locked, the next permitted action is preparation of a formal Task 10 implementation plan only if separately authorized under the project workflow. No Task 10 execution may begin from this document alone.
