# Task 11 — Evidence Review & Hypothesis Registration Design Spec

## Document status

```text
Status: FORMAL DESIGN SPEC — PENDING HUMAN REVIEW
Authorization: DESIGN / SPEC WRITING ONLY
Implementation Plan: NOT AUTHORIZED
Implementation: NOT AUTHORIZED
Production Execution: NOT AUTHORIZED
```

This document formalizes the human-approved Task 11 architecture. It does not
authorize an implementation plan, production code, hypothesis execution,
Ablation, Causal Replay, scoring, thresholding, ranking, prediction,
optimization, or feature selection.

## 1. Purpose

Task 11 is a deterministic Evidence Review and Hypothesis Registration layer
over the locked Task 10 Production package. It registers exactly one neutral,
pair-level future test question for each canonical Task 10 Main Relationship
Dossier while preserving the locked Task 10 evidence and its traceability.

Task 11 does not answer any hypothesis. It does not reinterpret evidence and
does not decide whether any feature is useful, redundant, important,
removable, or retainable.

## 2. Source-of-truth hierarchy

The sources of truth, in descending order, are:

1. This human-approved Task 11 architecture as recorded in this Spec after
   human review and lock.
2. The canonical Task 10 Production ZIP identified below.
3. The exact Main Relationship Dossier selected by canonical `pair_key`.
4. The upstream artifact and row locators already recorded by Task 10.

Task 11 must not infer missing information from repository code, filenames,
feature names, neighboring records, supplementary evidence, or statistical
conventions. Any missing, inconsistent, or untraceable required value is a
fail-closed error.

## 3. Canonical input and provenance

### 3.1 Task 10 implementation provenance

```text
Task 10 implementation HEAD:
0a780ca95c4e6853bb2530436c6045c54f508e80
```

### 3.2 Canonical Task 10 Production package

```text
Filename:
TASK10_PRODUCTION_RUN1.zip

SHA-256:
464465ef3dd435ed3a574bf8ded917095dcb76bb614416625b8c96db78c48903
```

The filename is descriptive; the SHA-256 is the authoritative package
identity. A differently named file is acceptable only if its bytes produce the
exact canonical SHA-256 above.

### 3.3 Exact package members

The ZIP must contain exactly these five logical members, with no duplicate,
missing, unexpected, directory, absolute, or path-traversal member:

```text
TASK10_MAIN_RELATIONSHIP_DOSSIERS.json
TASK10_SUPPLEMENTARY_EVIDENCE.csv
TASK10_FEATURE_DOSSIERS.json
TASK10_FUTURE_ABLATION_HYPOTHESES.json
TASK10_MANIFEST.json
```

The canonical uncompressed member SHA-256 values are:

| Member | SHA-256 |
|---|---|
| `TASK10_MAIN_RELATIONSHIP_DOSSIERS.json` | `954bd97aeb41b33669c99695b88a1715aa01a19bd697282f8e1b437be57de4d3` |
| `TASK10_SUPPLEMENTARY_EVIDENCE.csv` | `d4bd7ba2162429b0224fb1de39d4c4d71b5558b3a470d2224390faba7d1fbcf0` |
| `TASK10_FEATURE_DOSSIERS.json` | `8eeefc8393485e77e688e9ad298aba56bcbf20eac9d995f3c6b803dec6e97354` |
| `TASK10_FUTURE_ABLATION_HYPOTHESES.json` | `37517e5f3dc66819f61f5a7bb8ace1921282415f10551d2defa5c3eb0985b570` |
| `TASK10_MANIFEST.json` | `f6736c59bc120b8ed8bb5bcaf9ea0d3fb65931cfc2a82e142295c33333500a20` |

Package SHA verification must occur before ZIP parsing. Member SHA verification
must occur before JSON or CSV interpretation.

### 3.4 Input use boundaries

`TASK10_MAIN_RELATIONSHIP_DOSSIERS.json` is the sole record-level source for
Task 11 Hypotheses. The remaining four members are validated as part of the
canonical package and provenance contract, but Task 11 must not use them to
invent additional Hypotheses or fields.

In particular:

- Supplementary rows do not enter the 78-pair Hypothesis universe.
- The empty Task 10 future-hypothesis artifact does not authorize invention of
  a different Hypothesis universe.
- Feature metadata may be resolved from the locked Feature Dossiers when a
  future consumer needs it, but it is not duplicated into each Task 11 record.

## 4. Scope

### 4.1 In scope

- Validate the canonical Task 10 Production package and provenance.
- Read the 78 locked Task 10 Main Relationship Dossiers.
- Register exactly one canonical Hypothesis record per canonical `pair_key`.
- Copy the approved Task 10 evidence fields by exact structural equality.
- Create a deterministic `hypothesis_id` from the canonical `pair_key`.
- Render one fixed neutral test-question template using the canonical feature
  names.
- Preserve complete source locators.
- Emit deterministic Task 11 logical outputs and the required deterministic
  production ZIP.

### 4.2 Out of scope

- Answering or evaluating a Hypothesis.
- Executing or designing an Ablation protocol.
- Directional removal tests or removal order.
- Causal Replay or any causal claim.
- Outcome or prediction-target definition.
- Horizon definition.
- Ranking, scoring, weighting, priority, cutoff, or threshold.
- Feature importance, selection, removal, Keep, or Drop decisions.
- Prediction or optimization.
- New statistical calculations of any kind.
- Raw pooling across timeframes.
- Qualitative strength, stability, redundancy, or usefulness labels.
- Multi-feature, grouped, cluster-level, interaction-level, or cross-pair
  Hypotheses.

## 5. Hypothesis universe and cardinality

```text
HYPOTHESIS_UNIT = PAIRWISE_ONLY
HYPOTHESIS_CARDINALITY = EXACTLY_ONE_PER_CANONICAL_PAIR
```

Each Hypothesis must reference exactly one canonical `pair_key` from the locked
set of 78 Task 10 Main Relationship Dossiers and must contain exactly two
distinct Main Features: `feature_x` and `feature_y`.

The required mapping is:

```text
78 canonical Task 10 pair_keys
→ 78 Task 11 Hypothesis records
```

No canonical pair may have zero records or more than one record. The four
deterministic-context pairs remain part of the same 78-record universe and do
not generate additional records.

## 6. Hypothesis identity

```text
HYPOTHESIS_ID_POLICY = DETERMINISTIC_FROM_PAIR_KEY
HYPOTHESIS_ID_PREFIX = TASK11_HYPOTHESIS__
```

For every record:

```text
hypothesis_id == "TASK11_HYPOTHESIS__" + pair_key
```

The Task 10 `pair_key` must be copied exactly. It must not be reordered,
normalized, renamed, hashed, abbreviated, sequence-numbered, timestamped,
replaced with a UUID, or manually assigned.

The mapping between `pair_key` and `hypothesis_id` must be deterministic,
unique, one-to-one, and reversible by removing the exact prefix once.

## 7. Canonical test question

```text
TEST_QUESTION_POLICY = SINGLE_FIXED_TEMPLATE
TEST_QUESTION_TEMPLATE_ID = TASK11_PAIRWISE_NEUTRAL_V1
```

The canonical template is the following single logical string:

```text
Under a future separately locked controlled ablation protocol, does the information relationship between {feature_x} and {feature_y} remain measurable when their incremental information contributions are evaluated separately?
```

For every record, `test_question` is produced only by replacing the literal
`{feature_x}` and `{feature_y}` placeholders with the corresponding canonical
Task 10 feature-name strings. No other character, spacing, punctuation,
capitalization, or wording may vary between records.

Pair-specific rewriting, paraphrasing, qualitative wording, directional
wording, strength wording, removal wording, and human-authored custom questions
are prohibited.

The question deliberately does not determine intervention direction, feature
removal order, outcome, prediction target, horizon, threshold, score, Ablation
protocol, conditioning strategy, or causal interpretation. Those decisions
belong to a future separately authorized and locked stage.

## 8. Closed Hypothesis record schema

Every Hypothesis record must be a JSON object containing exactly these keys and
no others:

```text
TASK11_HYPOTHESIS_RECORD_FIELDS = (
    hypothesis_id
    pair_key
    feature_x
    feature_y

    raw_evidence_by_tf
    duration_control_applicability
    controlled_evidence_by_tf
    cross_tf_evidence

    direct_deterministic_dependency
    deterministic_relation_ids
    deterministic_context

    evidence_summary

    test_question_template_id
    test_question

    source_locators
)
```

Arbitrary optional fields are prohibited. A missing required key or an extra
key is a fail-closed schema error.

The JSON types are fixed as follows:

| Field | Required JSON type and constraint |
|---|---|
| `hypothesis_id` | string; exact value from Section 6 |
| `pair_key` | string; exact Task 10 copy |
| `feature_x` | string; exact Task 10 copy |
| `feature_y` | string; exact Task 10 copy and distinct from `feature_x` |
| `raw_evidence_by_tf` | object; exact Task 10 `raw_by_tf` copy |
| `duration_control_applicability` | string; exactly `ELIGIBLE` or `NOT_APPLICABLE_CONTROL_FEATURE`, as copied from Task 10 |
| `controlled_evidence_by_tf` | object; exact Task 10 `partial_by_tf` copy |
| `cross_tf_evidence` | object; exact Task 10 `cross_tf` copy |
| `direct_deterministic_dependency` | boolean; exact Task 10 copy |
| `deterministic_relation_ids` | array of strings; exact Task 10 ordered-array copy |
| `deterministic_context` | object; exact Task 10 copy |
| `evidence_summary` | array of strings; exact Task 10 ordered-array copy |
| `test_question_template_id` | string; exact constant from Section 7 |
| `test_question` | string; exact fixed-template rendering from Section 7 |
| `source_locators` | object; exact closed schema from Section 10 |

The copied evidence and context objects retain their complete locked Task 10
nested schemas and value types. Task 11 neither narrows nor extends them.

## 9. Exact field mapping

For a Task 10 Main Relationship Dossier `source`, the Task 11 record `record`
must satisfy every equality below.

Every copy/equality requirement in this Spec is recursive and JSON-type
sensitive: object key sets and values must match, arrays must preserve order,
strings must preserve exact Unicode content, and numbers must not be coerced
between integer and floating-point representations. Object member order and
surrounding serialization whitespace are not part of parsed-value equality.

### 9.1 Identity fields

```text
record.pair_key == source.pair_key
record.feature_x == source.feature_x
record.feature_y == source.feature_y
record.hypothesis_id == "TASK11_HYPOTHESIS__" + source.pair_key
```

`feature_x` and `feature_y` must preserve the canonical Task 10 pair ordering.
They must be distinct strings and must reconstruct the exact source `pair_key`
under the locked Task 10 canonical pair-key contract.

### 9.2 Raw evidence

```text
record.raw_evidence_by_tf == source.raw_by_tf
```

This is exact nested-object equality. Task 11 must not drop fields, rename
fields, normalize values, change `None`/JSON `null`, or recompute Raw Spearman.

### 9.3 Duration-controlled evidence

```text
record.duration_control_applicability == source.partial_applicability
record.controlled_evidence_by_tf == source.partial_by_tf
```

For the 66 eligible pairs:

```text
duration_control_applicability = ELIGIBLE
```

The complete locked `partial_by_tf` evidence is copied for `M5`, `M15`, `M30`,
and `H1`.

For the 12 pairs containing `active_bar_count`:

```text
duration_control_applicability = NOT_APPLICABLE_CONTROL_FEATURE
```

The complete locked Task 10 non-applicable structure is copied exactly. Its
controlled numeric fields remain JSON `null` and its status remains
`NOT_APPLICABLE_CONTROL_FEATURE`. These nulls represent structural
non-applicability and are not zero, missing evidence, undefined correlation, or
invented controlled values.

Task 11 must not contain an independent `delta_rho_by_tf` field. The sole
authorized `delta_rho` value is the one already present at:

```text
controlled_evidence_by_tf[timeframe].delta_rho
```

Creating a second projection or duplicate is prohibited.

### 9.4 Cross-timeframe evidence

```text
CROSS_TF_EVIDENCE_POLICY = COPY_LOCKED_TASK10_CROSS_TF
record.cross_tf_evidence == source.cross_tf
```

Task 11 must not recompute cross-timeframe statistics, pool raw observations,
reinterpret sign consistency, or create stability or strength labels.

### 9.5 Deterministic context

```text
record.direct_deterministic_dependency
== source.direct_deterministic_dependency

record.deterministic_relation_ids
== source.direct_deterministic_relation_ids

record.deterministic_context
== source.deterministic_context
```

Deterministic co-participation is context only. It does not mean that one
feature is a two-variable function solely of the other, and it must not create
a redundancy claim, removal Hypothesis, Keep/Drop recommendation, or importance
claim.

The canonical deterministic-context mapping contains exactly these four pairs:

| `pair_key` | Relation IDs |
|---|---|
| `active_bar_count__directional_continuity_ratio` | `CONTINUITY_RATIO` |
| `active_bar_count__normalized_directional_close_ols_slope` | `SLOPE_NORMALIZATION` |
| `active_bar_count__mean_tick_activity` | `TICK_ACTIVITY_IDENTITY` |
| `gross_close_path__gap_path_share` | `GAP_PATH_SHARE` |

All other records must retain the corresponding locked false/empty Task 10
deterministic state.

### 9.6 Evidence summary

```text
EVIDENCE_SUMMARY_POLICY = COPY_LOCKED_TASK10_OBSERVATIONS
record.evidence_summary == source.observations
```

Equality means exact ordered string-array equality:

- same observation count;
- same array ordering;
- same string content;
- no string normalization or modification;
- no paraphrase;
- no insertion or deletion;
- no aggregation;
- no new statistic;
- no new interpretation.

This requirement concerns the parsed ordered string array. It does not require
the whitespace or formatting of the surrounding JSON serialization to equal
Task 10.

Task 11 must not author any new evidence-summary prose. For the 12 control
pairs, the locked `CONTROLLED NOT_APPLICABLE_CONTROL_FEATURE` observations are
preserved exactly. Deterministic context remains in its separate structural
fields and does not modify the summary.

### 9.7 Test-question fields

```text
record.test_question_template_id == "TASK11_PAIRWISE_NEUTRAL_V1"
record.test_question == render_fixed_template(source.feature_x, source.feature_y)
```

Rendering means literal placeholder substitution only. It is not a natural
language generation step.

## 10. Closed source-locator schema

`source_locators` must be a JSON object containing exactly these keys and no
others:

```text
SOURCE_LOCATOR_FIELDS = (
    task10_main_dossier
    upstream_raw_source_artifact_by_tf
    upstream_raw_source_row_locator_by_tf
    upstream_partial_source_artifact_by_tf
    upstream_partial_source_row_locator_by_tf
    upstream_cross_tf_source_artifact
    upstream_cross_tf_source_row_locator
)
```

The exact mappings are:

```text
source_locators.task10_main_dossier
== "TASK10_MAIN_RELATIONSHIP_DOSSIERS.json#" + source.pair_key

source_locators.upstream_raw_source_artifact_by_tf
== source.raw_source_artifact_by_tf

source_locators.upstream_raw_source_row_locator_by_tf
== source.raw_source_row_locator_by_tf

source_locators.upstream_partial_source_artifact_by_tf
== source.partial_source_artifact_by_tf

source_locators.upstream_partial_source_row_locator_by_tf
== source.partial_source_row_locator_by_tf

source_locators.upstream_cross_tf_source_artifact
== source.cross_tf_source_artifact

source_locators.upstream_cross_tf_source_row_locator
== source.cross_tf_source_row_locator
```

`task10_main_dossier` is created only by the exact formula above. Every upstream
locator is copied from Task 10 and must not be synthesized from a filename
pattern or other assumption.

For the 12 control pairs, the locked `None`/JSON `null` partial-artifact map and
`NOT_APPLICABLE_CONTROL_FEATURE` partial-row-locator map are preserved exactly.

## 11. Task 10 fields intentionally not copied

The following Task 10 fields must not appear as top-level Task 11 Hypothesis
record fields:

```text
source_pair_key
feature_x_analysis_role
feature_y_analysis_role
feature_x_formula
feature_y_formula
feature_x_direction_semantics
feature_y_direction_semantics
```

`source_pair_key` duplicates `pair_key`. Feature formula, role, and direction
semantics belong to locked Feature metadata and may be resolved from the Task 10
Feature Dossiers when a future consumer needs them. They must not be duplicated
across 78 Hypothesis records.

The Task 10 source field names `raw_by_tf`, `partial_by_tf`, `cross_tf`,
`observations`, and the upstream locator fields do not remain as additional
top-level aliases. Their values are carried only through the exact Task 11
fields and locator object defined in Sections 8–10.

## 12. Prohibited fields and semantics

The following fields, aliases, or semantic equivalents are prohibited anywhere
in a Task 11 Hypothesis record:

```text
rank
score
weight
priority
strength_label
stability_label
redundancy_label
keep_recommendation
drop_recommendation
outcome
prediction
threshold
ablation_result
causal_interpretation
delta_rho_by_tf
```

Also prohibited are Feature importance, Feature selection, Feature removal,
Ranking, Scoring, Thresholding, Prediction, Optimization, Ablation execution,
Causal Replay, causal claims, qualitative evidence labels, and new statistical
calculations.

Scope-state fields in the manifest that explicitly record these operations as
`false` are required provenance and are not prohibited semantics.

## 13. Output contract

Task 11 has exactly two logical output files:

```text
TASK11_HYPOTHESIS_REGISTRY.json
TASK11_MANIFEST.json
```

The required deterministic production archive must contain exactly those two
members:

```text
TASK11_EVIDENCE_REVIEW_HYPOTHESIS_REGISTRATION_PACKAGE.zip
```

### 13.1 Hypothesis Registry

`TASK11_HYPOTHESIS_REGISTRY.json` is a JSON array of exactly 78 records using
the closed schema in Section 8.

### 13.2 Manifest

`TASK11_MANIFEST.json` must be a closed JSON object containing exactly:

```text
TASK11_MANIFEST_FIELDS = (
    task
    task11_spec_commit
    task11_implementation_commit

    hypothesis_registry_filename
    hypothesis_registry_sha256
    production_archive_filename
    logical_output_filenames

    task10_implementation_commit
    task10_production_package_filename
    task10_production_package_sha256
    task10_main_dossiers_member_sha256
    task10_manifest_member_sha256

    hypothesis_unit
    hypothesis_cardinality
    hypothesis_id_policy
    hypothesis_id_prefix
    test_question_policy
    test_question_template_id
    evidence_summary_policy
    cross_tf_evidence_policy

    main_pair_count
    hypothesis_count
    duration_control_eligible_count
    control_feature_non_applicable_count
    deterministic_context_pair_count
    logical_file_count

    new_statistics_computed
    raw_cross_tf_pooling
    ranking_performed
    score_computed
    threshold_applied
    outcome_used
    prediction_performed
    optimization_performed
    ablation_executed
    causal_replay_executed
    causal_claims_made
    ablation_protocol_designed
    directional_tests_defined
    feature_importance_assessed
    feature_selection_performed
    feature_removal_recommended
    keep_drop_recommendation_made
)
```

Required manifest values include:

```text
task = "Task 11 — Evidence Review & Hypothesis Registration"

hypothesis_registry_filename = "TASK11_HYPOTHESIS_REGISTRY.json"
production_archive_filename =
"TASK11_EVIDENCE_REVIEW_HYPOTHESIS_REGISTRATION_PACKAGE.zip"
logical_output_filenames =
["TASK11_HYPOTHESIS_REGISTRY.json", "TASK11_MANIFEST.json"]

task10_implementation_commit =
"0a780ca95c4e6853bb2530436c6045c54f508e80"

task10_production_package_sha256 =
"464465ef3dd435ed3a574bf8ded917095dcb76bb614416625b8c96db78c48903"

task10_production_package_filename = "TASK10_PRODUCTION_RUN1.zip"

task10_main_dossiers_member_sha256 =
"954bd97aeb41b33669c99695b88a1715aa01a19bd697282f8e1b437be57de4d3"

task10_manifest_member_sha256 =
"f6736c59bc120b8ed8bb5bcaf9ea0d3fb65931cfc2a82e142295c33333500a20"

hypothesis_unit = "PAIRWISE_ONLY"
hypothesis_cardinality = "EXACTLY_ONE_PER_CANONICAL_PAIR"
hypothesis_id_policy = "DETERMINISTIC_FROM_PAIR_KEY"
hypothesis_id_prefix = "TASK11_HYPOTHESIS__"
test_question_policy = "SINGLE_FIXED_TEMPLATE"
test_question_template_id = "TASK11_PAIRWISE_NEUTRAL_V1"
evidence_summary_policy = "COPY_LOCKED_TASK10_OBSERVATIONS"
cross_tf_evidence_policy = "COPY_LOCKED_TASK10_CROSS_TF"

main_pair_count = 78
hypothesis_count = 78
duration_control_eligible_count = 66
control_feature_non_applicable_count = 12
deterministic_context_pair_count = 4
logical_file_count = 2
```

`hypothesis_registry_sha256` must be the lowercase 64-hex SHA-256 of the exact
serialized `TASK11_HYPOTHESIS_REGISTRY.json` bytes included in the production
archive. `logical_output_filenames` is the lexicographically sorted logical
member list. `task10_production_package_filename` records the canonical logical
source filename from Section 3.2 even if the local physical file carrying the
canonical bytes has a different basename.

`task11_spec_commit` must equal the exact future human-approved and locked Spec
commit recorded by the Task 11 Spec Lock Record. `task11_implementation_commit`
must equal the clean committed implementation HEAD captured by the production
provenance gate before output generation. Neither value may be supplied by a
public override.

Every scope-state field from `new_statistics_computed` through
`keep_drop_recommendation_made` must be exactly JSON `false`.

## 14. Deterministic ordering and serialization

### 14.1 Record ordering

The Hypothesis Registry array must preserve the exact array order of the 78
canonical Task 10 Main Relationship Dossiers. Re-sorting by lexicographic
`pair_key`, `hypothesis_id`, feature name, evidence value, or any other criterion
is prohibited.

This source order is canonical because the entire input package and Main
Dossiers member are SHA-locked. Output record `i` must correspond to input Main
Dossier `i` for every index from 0 through 77.

### 14.2 Nested evidence ordering

Arrays copied from Task 10 must preserve their exact source order. JSON object
equality is defined by keys and values rather than member order; no logic may
depend on source JSON object-key order.

### 14.3 Serialization

Logical JSON outputs must be UTF-8, use deterministic key ordering, reject
duplicate keys and non-finite numbers, set `allow_nan=False`, and end with one
newline. Repeated execution with identical input bytes and the same locked
implementation commit must produce byte-identical logical files.

The required production ZIP must contain the two logical members in sorted
member-name order, use a fixed ZIP timestamp of `1980-01-01 00:00:00`, stable
compression settings, stable Unix regular-file mode, and no extra metadata.
Repeated production executions must produce byte-identical ZIPs.

## 15. Validation requirements

Before any output is written, Task 11 must validate all of the following:

### 15.1 Package and provenance gates

- Package SHA equals the canonical Task 10 Production SHA before ZIP parsing.
- ZIP member set, duplicate-member state, and path safety match Section 3.
- Every member SHA matches Section 3.3.
- `TASK10_MANIFEST.json` records the expected Task 10 implementation commit;
  Task 9 provenance; counts of 78 Main Dossiers, 66 partial/delta-eligible
  pairs, 12 control-feature non-applicable pairs, 13 Feature Dossiers, 960
  supplementary rows, and zero future Ablation Hypotheses; and the locked
  false scope flags. The Task 10 Manifest does not claim the containing Task 10
  ZIP SHA or member SHAs; Task 11 validates those independently under Sections
  3.2–3.3.
- Task 10 future Ablation Hypotheses member is the exact locked empty array.

### 15.2 Main Dossier gates

- The source is a JSON array of exactly 78 objects.
- Every source object has the exact locked Task 10 Main Dossier schema.
- All 78 `pair_key` values are unique and equal the canonical Task 10 pair set.
- Each `pair_key` agrees with ordered `feature_x` and `feature_y`.
- Every nested evidence mapping covers exactly `M5`, `M15`, `M30`, and `H1`.
- Every dossier satisfies `n_defined_tf + n_undefined_tf == 4`.
- Exactly 66 records are `ELIGIBLE` for Duration control.
- Exactly 12 records are `NOT_APPLICABLE_CONTROL_FEATURE` and contain
  `active_bar_count`.
- No control-feature pair is represented as eligible.
- The exact four deterministic-context mappings in Section 9.5 are present;
  every other pair retains the locked non-context state.
- Source artifact maps and row-locator maps are complete and consistent with
  the locked source values.

### 15.3 Hypothesis gates

- Registry count is exactly 78.
- Registry record order matches source dossier order index-for-index.
- Record key set equals the closed Task 11 schema exactly.
- Every canonical source pair maps to exactly one output record.
- Every `hypothesis_id`, `pair_key`, and feature field satisfies Sections 5–6.
- Every evidence field satisfies exact parsed-value equality with Task 10.
- Every `evidence_summary` satisfies exact ordered string-array equality.
- Every test question uses the fixed template and exact canonical feature names.
- Every locator object has the exact closed key set and values in Section 10.
- `delta_rho_by_tf` and every other prohibited field are absent.
- No prohibited term or semantic output is generated outside required
  manifest false-state keys.

### 15.4 Output and repeatability gates

- Logical output set is exactly the two filenames in Section 13.
- Manifest schema and values are exact.
- Two independent runs using the same canonical input and committed
  implementation state produce byte-identical logical files.
- Production ZIPs from the two runs are byte-identical and contain exactly the
  logical output set.

## 16. Fail-closed behavior

Any validation failure must terminate Task 11 before creating or replacing any
logical output. Task 11 must not produce a partial registry, partial manifest,
best-effort record, warning-only downgrade, substituted default, inferred
locator, normalized identifier, zero-filled value, or skipped pair.

Specific fail-closed conditions include:

- input package or member SHA mismatch;
- malformed ZIP, JSON, CSV, UTF-8, duplicate key, unsafe path, or non-finite
  numeric value;
- missing, unexpected, duplicate, or reordered source pair;
- missing or extra Task 11 field;
- evidence inequality at any nesting level;
- an unknown applicability or statistical status;
- controlled numeric evidence present where control is non-applicable;
- a missing controlled value where locked eligible evidence contains one;
- altered observation string or ordering;
- deterministic-context mismatch;
- locator mismatch;
- test-template drift;
- a count other than 78/78/66/12/4/2;
- any unauthorized semantic field or operation;
- dirty tracked implementation state at production execution.

Validation errors must identify the artifact, `pair_key` when applicable,
timeframe or nested field when applicable, and the violated contract without
adding an interpretive judgment about the evidence.

## 17. Production provenance boundary

A future Task 11 production entry point must fail before reading the canonical
ZIP or writing output unless:

- the tracked worktree and staging area are clean;
- every required Task 11 implementation file exists at `HEAD`;
- `HEAD` is a valid committed SHA;
- the implementation contains the human-approved locked Task 11 Spec commit;
- the public production path exposes no input-SHA, loader, source-bundle,
  template, identifier, ordering, count, or implementation-commit override.

The validated implementation HEAD must be captured before output construction
and must be the only Task 11 implementation SHA written to the manifest.
Synthetic tests, if later authorized, must use a private seam inaccessible from
the public production function and CLI.

## 18. Non-regression and scope isolation

Any future Task 11 implementation must be research-only and must not modify:

- `src/` Swing or Leg Engine code;
- Task 9 or Task 10 evidence packages;
- `research/combined_audit_*.py`;
- Task 10 implementation or contracts;
- locked formulas, metrics, feature definitions, or historical evidence;
- this Spec after it is human-approved and locked.

The future implementation scope must be separately enumerated in a formal Plan
and verified against a path allowlist. No implementation work is authorized by
this Spec-writing task.

## 19. Future-stage boundary

Task 11 ends after deterministic registration and verified production delivery
of the 78 neutral pair-level Hypothesis records, if and only if those later
steps receive separate authorization.

Task 11 must not decompose a pair-level question into directional tests. A
future separately specified, reviewed, locked, and authorized Controlled
Ablation Design task may define intervention direction, feature-removal order,
conditioning strategy, outcomes, prediction targets, horizons, test statistics,
multiple-testing policy, thresholds, or decision rules. None of those future
choices is implied or constrained by a Task 11 Hypothesis beyond its canonical
pair identity and preserved evidence.

Causal Replay requires its own later design and explicit authorization and is
not part of Task 11 or the Controlled Ablation Design by default.

## 20. Definition of Done for the Task 11 design phase

The Task 11 design phase is complete only when:

1. This Spec contains no unresolved design marker or placeholder other than
   the two locked `{feature_x}` and `{feature_y}` template tokens, contradictory
   requirement, optional arbitrary field, or undefined scope decision.
2. Human review explicitly approves the Spec.
3. The approved Spec bytes are committed and recorded by a separate Spec Lock
   Record with the exact commit SHA.
4. No implementation Plan or production code has been created under the
   current Design-only authorization.

Current authorization ends after committing this single Spec file for human
review. The next permissible action is human review. A formal implementation
Plan requires separate explicit authorization after the Spec is approved and
locked.
