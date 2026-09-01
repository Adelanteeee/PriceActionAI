# Task 11 Evidence Review & Hypothesis Registration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a research-only, fail-closed Task 11 pipeline that validates the canonical locked Task 10 Production ZIP and deterministically emits exactly 78 neutral pair-level Hypothesis records, one closed provenance manifest, and the required deterministic two-member production archive without calculating, interpreting, ranking, scoring, selecting, removing, predicting, or testing anything.

**Architecture:** Task 11 has four focused units: a frozen machine-readable contract, a strict Task 10 package loader plus deterministic writer, a pure Hypothesis registry builder, and a provenance-gated production runner/CLI. The public loader accepts only the canonical Task 10 package SHA; synthetic tests use a private byte seam. The builder copies JSON values from each canonical Main Relationship Dossier, while the runner computes only serialization hashes and locked counts needed for provenance.

**Tech Stack:** Python 3.12, pytest, and Python standard library only (`argparse`, `ast`, `copy`, `csv`, `dataclasses`, `hashlib`, `io`, `itertools`, `json`, `math`, `pathlib`, `re`, `subprocess`, `zipfile`, `collections`, `collections.abc`, `types`, `typing`). No new package dependency and no import from `src/`.

**Spec:** `docs/superpowers/specs/2026-09-01-task11-evidence-review-hypothesis-registration-design.md`

**Locked Spec Commit:** `7a3553770ea51e4ae72662fa44907f507779d22d`

**Locked Spec Blob:** `99e93ef6ca7cf1038561e7d6c4217e226ba99dfb`

**Spec Lock Record:** `docs/superpowers/specs/2026-09-01-task11-evidence-review-hypothesis-registration-design.LOCKED.md`

**Spec Lock Record Commit / Plan Base HEAD:** `a51dc7f76a5c3ea4c8e2929be7859c02c879a2d9`

## Global Constraints

- `HYPOTHESIS_UNIT = "PAIRWISE_ONLY"`.
- `HYPOTHESIS_CARDINALITY = "EXACTLY_ONE_PER_CANONICAL_PAIR"`.
- The input sequence is exactly 78 canonical Task 10 Main Relationship Dossiers and the output sequence is exactly 78 Hypothesis records in the same index order.
- Each output record contains exactly one source `pair_key`, exactly two distinct canonical Main Features, and no cross-pair or multi-feature content.
- `hypothesis_id = "TASK11_HYPOTHESIS__" + pair_key`; no normalization, reordering, hashing, abbreviation, numbering, timestamp, UUID, or manual ID is permitted.
- `TEST_QUESTION_POLICY = "SINGLE_FIXED_TEMPLATE"` and `TEST_QUESTION_TEMPLATE_ID = "TASK11_PAIRWISE_NEUTRAL_V1"`.
- The test question is rendered by literal replacement of only `{feature_x}` and `{feature_y}` in the locked template; no natural-language generation or pair-specific rewrite is permitted.
- `evidence_summary` is an exact ordered string-array copy of Task 10 `observations`.
- `raw_evidence_by_tf` is an exact recursive JSON-type-sensitive copy of Task 10 `raw_by_tf`.
- `duration_control_applicability` is an exact copy of Task 10 `partial_applicability`.
- `controlled_evidence_by_tf` is an exact recursive JSON-type-sensitive copy of Task 10 `partial_by_tf`.
- `cross_tf_evidence` is an exact recursive JSON-type-sensitive copy of Task 10 `cross_tf`.
- `direct_deterministic_dependency`, `deterministic_relation_ids`, and `deterministic_context` are exact Task 10 copies; the four deterministic-context pairs create no extra records.
- `delta_rho_by_tf` is prohibited. The only authorized `delta_rho` location is `controlled_evidence_by_tf[timeframe].delta_rho`.
- Task 11 computes no new association statistic or other statistic. SHA-256 digests and exact locked counts are provenance/validation operations, not research statistics.
- No rank, score, weight, priority, strength/stability/redundancy label, Keep/Drop recommendation, outcome, prediction, threshold, Ablation result, causal interpretation, Feature Importance, Feature Selection, Feature Removal, Optimization, raw cross-TF pooling, directional removal test, horizon, or Causal Replay implementation is permitted.
- The only logical output filenames are `TASK11_HYPOTHESIS_REGISTRY.json` and `TASK11_MANIFEST.json`.
- The required production archive is `TASK11_EVIDENCE_REVIEW_HYPOTHESIS_REGISTRATION_PACKAGE.zip` and contains exactly those two logical files.
- Locked counts are `78 / 78 / 66 / 12 / 4 / 2` for main pairs, Hypotheses, Duration-control eligible pairs, control-feature non-applicable pairs, deterministic-context pairs, and logical files.
- JSON is UTF-8, sorted-key, compact (`separators=(",", ":")`), `allow_nan=False`, and ends with exactly one newline.
- ZIP members are sorted by filename, use timestamp `(1980, 1, 1, 0, 0, 0)`, deflate level 9, Unix regular-file mode `0o100644`, and no extra metadata.
- Public production execution validates a clean tracked worktree, clean index, committed implementation files, locked Spec ancestry/blob, and locked Spec Lock Record ancestry/blob before reading the input ZIP or creating output.
- Public APIs and CLI expose no SHA, loader, preloaded bundle, template, identifier, count, ordering, implementation-commit, scope, score, threshold, outcome, or experimental override.
- Synthetic tests call only private seams; production calls only the canonical-SHA public loader.
- Do not modify `src/`, `evidence/`, `research/combined_audit_*.py`, `research/task10_interpretation_*.py`, `research/run_task10_dependency_interpretation.py`, Task 9/10 evidence packages, the locked Task 11 Spec, the Spec Lock Record, or this Plan during implementation.
- Controlled Ablation Design/execution, Causal Replay, outcomes, horizons, conclusions, and feature decisions require future separately locked and authorized work.

## Canonical Input Binding

```text
Task 10 implementation commit:
0a780ca95c4e6853bb2530436c6045c54f508e80

Task 10 canonical logical package filename:
TASK10_PRODUCTION_RUN1.zip

Task 10 canonical package SHA-256:
464465ef3dd435ed3a574bf8ded917095dcb76bb614416625b8c96db78c48903
```

Exact uncompressed member SHA-256 mapping:

```text
TASK10_MAIN_RELATIONSHIP_DOSSIERS.json  954bd97aeb41b33669c99695b88a1715aa01a19bd697282f8e1b437be57de4d3
TASK10_SUPPLEMENTARY_EVIDENCE.csv       d4bd7ba2162429b0224fb1de39d4c4d71b5558b3a470d2224390faba7d1fbcf0
TASK10_FEATURE_DOSSIERS.json            8eeefc8393485e77e688e9ad298aba56bcbf20eac9d995f3c6b803dec6e97354
TASK10_FUTURE_ABLATION_HYPOTHESES.json  37517e5f3dc66819f61f5a7bb8ace1921282415f10551d2defa5c3eb0985b570
TASK10_MANIFEST.json                    f6736c59bc120b8ed8bb5bcaf9ea0d3fb65931cfc2a82e142295c33333500a20
```

The public loader hashes the complete package before ZIP parsing, validates ZIP safety and the exact member set, hashes every uncompressed member before JSON/CSV parsing, and only then interprets member content.

## Execution Baseline and Environment

At the beginning of a future authorized implementation session, verify that the checked-out implementation branch begins at the committed Plan and capture the baseline without an unknown SHA literal:

```bash
TASK11_EXECUTION_BASELINE="$(git log -1 --format=%H -- docs/superpowers/plans/2026-09-01-task11-evidence-review-hypothesis-registration.md)"
test "$(git rev-parse HEAD)" = "$TASK11_EXECUTION_BASELINE"
test "$(git rev-parse "$TASK11_EXECUTION_BASELINE^")" = "a51dc7f76a5c3ea4c8e2929be7859c02c879a2d9"
git status --porcelain=v1 --untracked-files=no
git diff --cached --quiet
```

Expected: both `test` commands and `git diff --cached --quiet` exit 0; tracked-status output is empty. Install the repository's test dependencies if the execution environment does not already provide them:

```bash
python -m pip install --upgrade pytest pandas plotly
```

This environment installation does not change repository files.

## Planned File Structure

Create exactly these implementation/test files; modify no existing source, test, evidence, Spec, Lock Record, or Plan file:

| Path | Responsibility |
|---|---|
| `research/task11_hypothesis_contract.py` | Frozen Task 11 constants, canonical hashes, exact input/output schemas, counts, deterministic-context mapping, manifest fields, and scope-state constants. Metadata only; no I/O or statistics. |
| `research/task11_hypothesis_io.py` | Canonical Task 10 ZIP SHA/member/safety/UTF-8/JSON/CSV validation, immutable loaded-bundle boundary, deterministic JSON serialization, exact logical-file writing, and deterministic ZIP writing. |
| `research/task11_hypothesis_registry.py` | Pure index-preserving transformation from validated Task 10 Main Dossiers to exact closed Task 11 Hypothesis records, plus exact registry validation. |
| `research/run_task11_hypothesis_registration.py` | Manifest construction, private deterministic orchestration seam, clean committed provenance guard, public production function, parser, and CLI. |
| `tests/test_task11_hypothesis_contract.py` | Exact constant, hash, schema, count, output-name, template, and prohibited-field contract tests. |
| `tests/test_task11_hypothesis_io.py` | Synthetic Task 10 package fixture plus package/member/ZIP/JSON/CSV/schema/provenance/fail-closed loader and deterministic writer tests. |
| `tests/test_task11_hypothesis_registry.py` | Exact copy, identity, fixed question, order, locators, Duration-control, deterministic-context, closed-schema, and prohibition tests. |
| `tests/test_task11_hypothesis_integration.py` | Private two-run byte repeatability, exact manifest/output/ZIP tests, public CLI boundary, provenance-guard behavior, and no-output-on-failure tests. |

## Interfaces Between Units

`research.task11_hypothesis_contract` exports immutable constants consumed by every other Task 11 module. `TIMEFRAMES`, `TASK10_CANONICAL_PAIR_KEYS`, every field-schema constant, and `TASK11_FALSE_SCOPE_FIELDS` are ordered tuples of strings. `TASK10_MEMBER_SHA256_BY_FILENAME` maps each of the five member names to one lowercase 64-hex digest. `DETERMINISTIC_RELATION_IDS_BY_PAIR_KEY` maps each of the four deterministic pair keys to one ordered tuple of relation IDs.

`research.task11_hypothesis_io` owns these exact interfaces:

- `Task10ProductionBundle` is a frozen/slotted dataclass with `main_dossiers` as an immutable ordered tuple of mappings, `manifest` as an immutable mapping, `production_zip_sha256: str`, and `member_sha256_by_filename: Mapping[str, str]`.
- Public `load_task10_production_package(path: Path) -> Task10ProductionBundle`.
- Private `_load_task10_production_bytes(package_bytes: bytes, *, expected_package_sha256: str, expected_member_sha256_by_filename: Mapping[str, str]) -> Task10ProductionBundle`.
- Private `_json_bytes(value: object) -> bytes`.
- `write_task11_outputs(output_dir: Path, *, implementation_commit: str, registry: Sequence[Mapping[str, object]], manifest: Mapping[str, object], output_zip: Path) -> None`.

`research.task11_hypothesis_registry` exposes only:

- `render_test_question(feature_x: str, feature_y: str) -> str`.
- `build_hypothesis_registry(main_dossiers: Sequence[Mapping[str, object]]) -> list[dict[str, object]]`.
- `validate_hypothesis_registry(registry: Sequence[Mapping[str, object]], main_dossiers: Sequence[Mapping[str, object]]) -> None`.

`research.run_task11_hypothesis_registration` owns:

- `assert_clean_committed_task11_worktree() -> str`.
- `_build_manifest(bundle: Task10ProductionBundle, *, implementation_commit: str, hypothesis_registry_sha256: str, main_pair_count: int, hypothesis_count: int, duration_control_eligible_count: int, control_feature_non_applicable_count: int, deterministic_context_pair_count: int) -> dict[str, object]`.
- `_run_task11_from_bundle(bundle: Task10ProductionBundle, output_dir: Path, *, implementation_commit: str, output_zip: Path) -> dict[str, object]`.
- Public `run_task11(input_task10_production: Path, output_dir: Path, *, output_zip: Path) -> dict[str, object]`.
- `build_parser() -> argparse.ArgumentParser` and `main(argv: list[str] | None = None) -> int`.

The private loader/orchestration seams are importable for pytest only and are never reachable through `run_task11()` or CLI parameters.

---

### Task 1: Freeze the Task 11 machine-readable contract

**Files:**
- Create: `research/task11_hypothesis_contract.py`
- Create: `tests/test_task11_hypothesis_contract.py`

**Interfaces:**
- Consumes read-only `MAIN_FEATURES` and `TIMEFRAMES` from `research.combined_audit_contract` solely to validate the locked canonical Task 10 pair set/order; no record value is built from Feature metadata.
- Produces every constant, exact field tuple, locked count, hash, filename, deterministic-context map, and false-scope tuple listed in the global interface section.

- [ ] **Step 1: Write the failing exact-contract tests**

Create `tests/test_task11_hypothesis_contract.py` with assertions for the exact Spec/Lock/Input bindings, 78 ordered pair keys, fixed template, exact schemas, output names, counts, and prohibited top-level fields:

```python
from research.task11_hypothesis_contract import (
    CONTROL_FEATURE_NON_APPLICABLE_COUNT,
    DETERMINISTIC_CONTEXT_PAIR_COUNT,
    DETERMINISTIC_RELATION_IDS_BY_PAIR_KEY,
    DURATION_CONTROL_ELIGIBLE_COUNT,
    HYPOTHESIS_COUNT,
    HYPOTHESIS_ID_PREFIX,
    LOGICAL_FILE_COUNT,
    MAIN_PAIR_COUNT,
    OUTPUT_ZIP_FILENAME,
    TASK10_IMPLEMENTATION_COMMIT,
    TASK10_MAIN_DOSSIERS_MEMBER_SHA256,
    TASK10_MANIFEST_MEMBER_SHA256,
    TASK10_MEMBER_SHA256_BY_FILENAME,
    TASK10_PRODUCTION_PACKAGE_SHA256,
    TASK11_FALSE_SCOPE_FIELDS,
    TASK11_HYPOTHESIS_RECORD_FIELDS,
    TASK11_LOGICAL_FILENAMES,
    TASK11_MANIFEST_FIELDS,
    TASK11_SOURCE_LOCATOR_FIELDS,
    TASK11_SPEC_BLOB_SHA,
    TASK11_SPEC_COMMIT,
    TASK11_SPEC_LOCK_COMMIT,
    TEST_QUESTION_TEMPLATE,
    TEST_QUESTION_TEMPLATE_ID,
    TASK10_CANONICAL_PAIR_KEYS,
)


def test_locked_provenance_and_counts_are_exact():
    assert TASK11_SPEC_COMMIT == "7a3553770ea51e4ae72662fa44907f507779d22d"
    assert TASK11_SPEC_BLOB_SHA == "99e93ef6ca7cf1038561e7d6c4217e226ba99dfb"
    assert TASK11_SPEC_LOCK_COMMIT == "a51dc7f76a5c3ea4c8e2929be7859c02c879a2d9"
    assert TASK10_IMPLEMENTATION_COMMIT == "0a780ca95c4e6853bb2530436c6045c54f508e80"
    assert TASK10_PRODUCTION_PACKAGE_SHA256 == "464465ef3dd435ed3a574bf8ded917095dcb76bb614416625b8c96db78c48903"
    assert TASK10_MAIN_DOSSIERS_MEMBER_SHA256 == "954bd97aeb41b33669c99695b88a1715aa01a19bd697282f8e1b437be57de4d3"
    assert TASK10_MANIFEST_MEMBER_SHA256 == "f6736c59bc120b8ed8bb5bcaf9ea0d3fb65931cfc2a82e142295c33333500a20"
    assert (MAIN_PAIR_COUNT, HYPOTHESIS_COUNT) == (78, 78)
    assert (DURATION_CONTROL_ELIGIBLE_COUNT, CONTROL_FEATURE_NON_APPLICABLE_COUNT) == (66, 12)
    assert (DETERMINISTIC_CONTEXT_PAIR_COUNT, LOGICAL_FILE_COUNT) == (4, 2)
    assert len(TASK10_CANONICAL_PAIR_KEYS) == len(set(TASK10_CANONICAL_PAIR_KEYS)) == 78


def test_question_and_output_contract_are_exact():
    assert HYPOTHESIS_ID_PREFIX == "TASK11_HYPOTHESIS__"
    assert TEST_QUESTION_TEMPLATE_ID == "TASK11_PAIRWISE_NEUTRAL_V1"
    assert TEST_QUESTION_TEMPLATE == (
        "Under a future separately locked controlled ablation protocol, "
        "does the information relationship between {feature_x} and {feature_y} "
        "remain measurable when their incremental information contributions "
        "are evaluated separately?"
    )
    assert TASK11_LOGICAL_FILENAMES == (
        "TASK11_HYPOTHESIS_REGISTRY.json",
        "TASK11_MANIFEST.json",
    )
    assert OUTPUT_ZIP_FILENAME == "TASK11_EVIDENCE_REVIEW_HYPOTHESIS_REGISTRATION_PACKAGE.zip"


def test_closed_record_and_locator_schemas_are_exact():
    assert TASK11_HYPOTHESIS_RECORD_FIELDS == (
        "hypothesis_id", "pair_key", "feature_x", "feature_y",
        "raw_evidence_by_tf", "duration_control_applicability",
        "controlled_evidence_by_tf", "cross_tf_evidence",
        "direct_deterministic_dependency", "deterministic_relation_ids",
        "deterministic_context", "evidence_summary",
        "test_question_template_id", "test_question", "source_locators",
    )
    assert TASK11_SOURCE_LOCATOR_FIELDS == (
        "task10_main_dossier",
        "upstream_raw_source_artifact_by_tf",
        "upstream_raw_source_row_locator_by_tf",
        "upstream_partial_source_artifact_by_tf",
        "upstream_partial_source_row_locator_by_tf",
        "upstream_cross_tf_source_artifact",
        "upstream_cross_tf_source_row_locator",
    )
    assert "delta_rho_by_tf" not in TASK11_HYPOTHESIS_RECORD_FIELDS
    assert len(TASK11_MANIFEST_FIELDS) == len(set(TASK11_MANIFEST_FIELDS))
    assert len(TASK11_FALSE_SCOPE_FIELDS) == 17
```

In the same test file, add literal-equality tests for every tuple and immutable mapping defined in Step 3: all five package-member hashes; the 24-field Main Dossier schema; raw, eligible-partial, control-partial, 26-field cross-TF, and deterministic-context nested schemas; the complete 43-field Task 11 Manifest schema; all 17 false-scope fields in order; both sorted logical filenames; all four deterministic pair/relation mappings; the exact 24-field Task 10 Manifest schema; and every Task 10 Manifest locked value. These tests compare the complete literal containers, not only their lengths or selected elements.

- [ ] **Step 2: Run the contract test to prove RED**

```bash
pytest -q tests/test_task11_hypothesis_contract.py
```

Expected: FAIL during collection with `ModuleNotFoundError: No module named 'research.task11_hypothesis_contract'`.

- [ ] **Step 3: Implement the exact constants and schemas**

Create `research/task11_hypothesis_contract.py`. Derive only the canonical pair-key order from the locked upstream feature order; hard-code every Spec/Lock/package binding and every closed schema:

```python
from itertools import combinations
from types import MappingProxyType

from research.combined_audit_contract import MAIN_FEATURES, TIMEFRAMES

TASK11_SPEC_PATH = "docs/superpowers/specs/2026-09-01-task11-evidence-review-hypothesis-registration-design.md"
TASK11_SPEC_COMMIT = "7a3553770ea51e4ae72662fa44907f507779d22d"
TASK11_SPEC_BLOB_SHA = "99e93ef6ca7cf1038561e7d6c4217e226ba99dfb"
TASK11_SPEC_LOCK_RECORD_PATH = "docs/superpowers/specs/2026-09-01-task11-evidence-review-hypothesis-registration-design.LOCKED.md"
TASK11_SPEC_LOCK_COMMIT = "a51dc7f76a5c3ea4c8e2929be7859c02c879a2d9"
TASK11_SPEC_LOCK_RECORD_BLOB_SHA = "de87a930b424b0cf9e58e14c8b27dca336954f33"

TASK10_IMPLEMENTATION_COMMIT = "0a780ca95c4e6853bb2530436c6045c54f508e80"
TASK10_PRODUCTION_PACKAGE_FILENAME = "TASK10_PRODUCTION_RUN1.zip"
TASK10_PRODUCTION_PACKAGE_SHA256 = "464465ef3dd435ed3a574bf8ded917095dcb76bb614416625b8c96db78c48903"
TASK10_MAIN_DOSSIERS_MEMBER_SHA256 = "954bd97aeb41b33669c99695b88a1715aa01a19bd697282f8e1b437be57de4d3"
TASK10_MANIFEST_MEMBER_SHA256 = "f6736c59bc120b8ed8bb5bcaf9ea0d3fb65931cfc2a82e142295c33333500a20"

TASK10_CANONICAL_PAIR_KEYS = tuple(
    f"{feature_x}__{feature_y}"
    for feature_x, feature_y in combinations(MAIN_FEATURES, 2)
)

HYPOTHESIS_ID_PREFIX = "TASK11_HYPOTHESIS__"
TEST_QUESTION_TEMPLATE_ID = "TASK11_PAIRWISE_NEUTRAL_V1"
TEST_QUESTION_TEMPLATE = (
    "Under a future separately locked controlled ablation protocol, "
    "does the information relationship between {feature_x} and {feature_y} "
    "remain measurable when their incremental information contributions "
    "are evaluated separately?"
)
```

Define these exact immutable input-hash and source-schema contracts in the same file. Dictionary key order is not a JSON semantic; validators compare closed key sets, while the tuple order below provides one deterministic construction order:

```python
TASK10_MEMBER_SHA256_BY_FILENAME = MappingProxyType({
    "TASK10_MAIN_RELATIONSHIP_DOSSIERS.json": "954bd97aeb41b33669c99695b88a1715aa01a19bd697282f8e1b437be57de4d3",
    "TASK10_SUPPLEMENTARY_EVIDENCE.csv": "d4bd7ba2162429b0224fb1de39d4c4d71b5558b3a470d2224390faba7d1fbcf0",
    "TASK10_FEATURE_DOSSIERS.json": "8eeefc8393485e77e688e9ad298aba56bcbf20eac9d995f3c6b803dec6e97354",
    "TASK10_FUTURE_ABLATION_HYPOTHESES.json": "37517e5f3dc66819f61f5a7bb8ace1921282415f10551d2defa5c3eb0985b570",
    "TASK10_MANIFEST.json": "f6736c59bc120b8ed8bb5bcaf9ea0d3fb65931cfc2a82e142295c33333500a20",
})

TASK10_MAIN_DOSSIER_FIELDS = (
    "cross_tf", "cross_tf_source_artifact", "cross_tf_source_row_locator",
    "deterministic_context", "direct_deterministic_dependency",
    "direct_deterministic_relation_ids", "feature_x",
    "feature_x_analysis_role", "feature_x_direction_semantics",
    "feature_x_formula", "feature_y", "feature_y_analysis_role",
    "feature_y_direction_semantics", "feature_y_formula", "observations",
    "pair_key", "partial_applicability", "partial_by_tf",
    "partial_source_artifact_by_tf", "partial_source_row_locator_by_tf",
    "raw_by_tf", "raw_source_artifact_by_tf",
    "raw_source_row_locator_by_tf", "source_pair_key",
)

TASK10_RAW_TF_FIELDS = (
    "feature_x", "feature_y", "n_missing_x", "n_missing_y", "n_total",
    "n_valid_pairwise", "rho_raw", "status",
)
TASK10_ELIGIBLE_PARTIAL_TF_FIELDS = (
    "feature_x", "feature_y", "rho_raw_for_delta",
    "rho_duration_controlled", "delta_rho", "n_valid_triple", "status",
)
TASK10_CONTROL_PARTIAL_TF_FIELDS = (
    "rho_raw_for_delta", "rho_duration_controlled", "delta_rho",
    "n_valid_triple", "status",
)
TASK10_CROSS_TF_FIELDS = (
    "controlled_eligible", "controlled_rho_H1", "controlled_rho_M15",
    "controlled_rho_M30", "controlled_rho_M5", "feature_x", "feature_y",
    "n_defined_tf", "n_negative_tf", "n_positive_tf", "n_undefined_tf",
    "n_valid_H1", "n_valid_M15", "n_valid_M30", "n_valid_M5",
    "n_zero_tf", "rho_H1", "rho_M15", "rho_M30", "rho_M5",
    "rho_max", "rho_min", "rho_range", "sign_agreement_count",
    "sign_agreement_modal_signs", "sign_agreement_tie",
)
TASK10_DETERMINISTIC_CONTEXT_FIELDS = (
    "co_participating_relation_ids", "co_participation_semantics",
)
```

Define these exact Task 11 closed field tuples:

```python
TASK11_HYPOTHESIS_RECORD_FIELDS = (
    "hypothesis_id", "pair_key", "feature_x", "feature_y",
    "raw_evidence_by_tf", "duration_control_applicability",
    "controlled_evidence_by_tf", "cross_tf_evidence",
    "direct_deterministic_dependency", "deterministic_relation_ids",
    "deterministic_context", "evidence_summary",
    "test_question_template_id", "test_question", "source_locators",
)

TASK11_SOURCE_LOCATOR_FIELDS = (
    "task10_main_dossier",
    "upstream_raw_source_artifact_by_tf",
    "upstream_raw_source_row_locator_by_tf",
    "upstream_partial_source_artifact_by_tf",
    "upstream_partial_source_row_locator_by_tf",
    "upstream_cross_tf_source_artifact",
    "upstream_cross_tf_source_row_locator",
)

TASK11_MANIFEST_FIELDS = (
    "task", "task11_spec_commit", "task11_implementation_commit",
    "hypothesis_registry_filename", "hypothesis_registry_sha256",
    "production_archive_filename", "logical_output_filenames",
    "task10_implementation_commit", "task10_production_package_filename",
    "task10_production_package_sha256",
    "task10_main_dossiers_member_sha256", "task10_manifest_member_sha256",
    "hypothesis_unit", "hypothesis_cardinality", "hypothesis_id_policy",
    "hypothesis_id_prefix", "test_question_policy",
    "test_question_template_id", "evidence_summary_policy",
    "cross_tf_evidence_policy", "main_pair_count", "hypothesis_count",
    "duration_control_eligible_count",
    "control_feature_non_applicable_count",
    "deterministic_context_pair_count", "logical_file_count",
    "new_statistics_computed", "raw_cross_tf_pooling", "ranking_performed",
    "score_computed", "threshold_applied", "outcome_used",
    "prediction_performed", "optimization_performed", "ablation_executed",
    "causal_replay_executed", "causal_claims_made",
    "ablation_protocol_designed", "directional_tests_defined",
    "feature_importance_assessed", "feature_selection_performed",
    "feature_removal_recommended", "keep_drop_recommendation_made",
)
TASK11_FALSE_SCOPE_FIELDS = (
    "new_statistics_computed", "raw_cross_tf_pooling", "ranking_performed",
    "score_computed", "threshold_applied", "outcome_used",
    "prediction_performed", "optimization_performed", "ablation_executed",
    "causal_replay_executed", "causal_claims_made",
    "ablation_protocol_designed", "directional_tests_defined",
    "feature_importance_assessed", "feature_selection_performed",
    "feature_removal_recommended", "keep_drop_recommendation_made",
)

TASK11_LOGICAL_FILENAMES = (
    "TASK11_HYPOTHESIS_REGISTRY.json",
    "TASK11_MANIFEST.json",
)
OUTPUT_ZIP_FILENAME = (
    "TASK11_EVIDENCE_REVIEW_HYPOTHESIS_REGISTRATION_PACKAGE.zip"
)

DETERMINISTIC_RELATION_IDS_BY_PAIR_KEY = MappingProxyType({
    "active_bar_count__directional_continuity_ratio": ("CONTINUITY_RATIO",),
    "active_bar_count__normalized_directional_close_ols_slope": (
        "SLOPE_NORMALIZATION",
    ),
    "active_bar_count__mean_tick_activity": ("TICK_ACTIVITY_IDENTITY",),
    "gross_close_path__gap_path_share": ("GAP_PATH_SHARE",),
})
```

Also define the exact count constants `MAIN_PAIR_COUNT = 78`, `HYPOTHESIS_COUNT = 78`, `DURATION_CONTROL_ELIGIBLE_COUNT = 66`, `CONTROL_FEATURE_NON_APPLICABLE_COUNT = 12`, `DETERMINISTIC_CONTEXT_PAIR_COUNT = 4`, and `LOGICAL_FILE_COUNT = 2`; `CONTROL_FEATURE = "active_bar_count"`, `CONTROL_NOT_APPLICABLE = "NOT_APPLICABLE_CONTROL_FEATURE"`, `ELIGIBLE = "ELIGIBLE"`; and `LOCKED_STATISTICAL_STATUSES = frozenset({"DEFINED", "UNDEFINED_INSUFFICIENT_OBSERVATIONS", "UNDEFINED_CONSTANT_INPUT"})`.

Define `TASK10_MANIFEST_FIELDS` as the exact 24-key tuple below and `TASK10_MANIFEST_EXPECTED_VALUES` as an immutable mapping with exactly these key/value pairs:

```python
TASK10_MANIFEST_FIELDS = (
    "ablation_executed", "causal_replay_executed",
    "control_feature_non_applicable_pair_count", "cutoff_applied",
    "feature_dossier_count", "feature_removal_recommended",
    "future_ablation_hypothesis_count", "main_relationship_dossier_count",
    "new_association_statistics_computed", "outcome_used",
    "partial_delta_eligible_pair_count", "ranking_performed",
    "raw_cross_tf_pooling", "score_computed",
    "supplementary_evidence_row_count", "task",
    "task10_implementation_commit", "task10_spec_commit",
    "task9_activity_input_sha256", "task9_audit_code_commit",
    "task9_evidence_package_filename", "task9_evidence_package_sha256",
    "task9_registration_commit", "threshold_applied",
)
TASK10_MANIFEST_EXPECTED_VALUES = MappingProxyType({
    "ablation_executed": False,
    "causal_replay_executed": False,
    "control_feature_non_applicable_pair_count": 12,
    "cutoff_applied": False,
    "feature_dossier_count": 13,
    "feature_removal_recommended": False,
    "future_ablation_hypothesis_count": 0,
    "main_relationship_dossier_count": 78,
    "new_association_statistics_computed": False,
    "outcome_used": False,
    "partial_delta_eligible_pair_count": 66,
    "ranking_performed": False,
    "raw_cross_tf_pooling": False,
    "score_computed": False,
    "supplementary_evidence_row_count": 960,
    "task": "Task 10 Dependency / Redundancy Interpretation",
    "task10_implementation_commit": "0a780ca95c4e6853bb2530436c6045c54f508e80",
    "task10_spec_commit": "dfc91e3c75a12a3dfa008c17453b622f03ed41ad",
    "task9_activity_input_sha256": "1e9f13fd88fc1e8e0e66d801be8c15d726639eaea25e53fef7c3bb88bfd05192",
    "task9_audit_code_commit": "1c40cd3d3507c473fd07ea25c010d386be8a0043",
    "task9_evidence_package_filename": "GOLD_COMBINED_LEG_FEATURE_AUDIT_PACKAGE.zip",
    "task9_evidence_package_sha256": "968f4826858a0bbb8254218711f4ad3e3487370ca8d0f288133ee36f7a4fa40d",
    "task9_registration_commit": "78e54fb50ce82a0cba7f91f40a6451e82996008d",
    "threshold_applied": False,
})
```

Wrap constant dictionaries in `MappingProxyType` so tests cannot mutate the process-wide contract.

- [ ] **Step 4: Run the contract test to prove GREEN**

```bash
pytest -q tests/test_task11_hypothesis_contract.py
```

Expected: PASS; all tests in this file pass and pytest exits 0.

- [ ] **Step 5: Commit the independently reviewable contract**

```bash
git add research/task11_hypothesis_contract.py tests/test_task11_hypothesis_contract.py
git commit -m "test: freeze Task 11 hypothesis contract"
```

Expected: one commit containing exactly the two Task 1 paths.

---
### Task 2: Load and validate the canonical Task 10 Production package

**Files:**
- Create: `research/task11_hypothesis_io.py`
- Create: `tests/test_task11_hypothesis_io.py`

**Interfaces:**
- Consumes only frozen Task 11 contract constants and standard-library bytes/ZIP/JSON/CSV APIs.
- Produces `Task10ProductionBundle`, public `load_task10_production_package()`, and private `_load_task10_production_bytes()`.
- Guarantees that downstream code receives exactly 78 validated Main Dossiers in canonical source order and a validated exact Task 10 Manifest.

- [ ] **Step 1: Write a complete synthetic Task 10 package fixture in the I/O test file**

In `tests/test_task11_hypothesis_io.py`, define test-only helper `make_synthetic_task10_production_zip(*, mutate: Callable[[dict[str, bytes]], None] | None = None, duplicate_member: str | None = None, extra_member: str | None = None) -> bytes` and helper `member_sha256_by_filename(package_bytes: bytes) -> dict[str, str]`. Define the loader wrapper exactly:

```python
def load_synthetic_task10(package_bytes: bytes) -> Task10ProductionBundle:
    return _load_task10_production_bytes(
        package_bytes,
        expected_package_sha256=hashlib.sha256(package_bytes).hexdigest(),
        expected_member_sha256_by_filename=member_sha256_by_filename(package_bytes),
    )
```

The fixture creates all five required members. Its Main Dossier JSON contains the exact 78 `TASK10_CANONICAL_PAIR_KEYS` in order. Every record uses the exact Task 10 source schema, all four `TIMEFRAMES`, unique values that make copy/order assertions observable, 66 `ELIGIBLE` partial mappings, 12 `NOT_APPLICABLE_CONTROL_FEATURE` mappings containing `active_bar_count`, and the four exact deterministic-context mappings. Its Task 10 Manifest contains the exact locked Task 10 fields/values. The supplementary member is a valid UTF-8 CSV, the Feature Dossiers member is valid JSON, and `TASK10_FUTURE_ABLATION_HYPOTHESES.json` is exactly an empty JSON array.

The helper is test-only. Production modules must not import from `tests/`.

- [ ] **Step 2: Write RED tests for package SHA, ZIP safety, and member SHA ordering**

Add these tests before creating the I/O module:

```python
def test_public_loader_rejects_noncanonical_sha_before_zip_parse(tmp_path: Path):
    path = tmp_path / "not-a-zip.bin"
    path.write_bytes(b"not a zip")
    with pytest.raises(ValueError, match="Task 10 Production SHA-256 mismatch"):
        load_task10_production_package(path)


def test_public_loader_has_no_hash_or_bundle_override():
    parameters = inspect.signature(load_task10_production_package).parameters
    assert tuple(parameters) == ("path",)


def test_private_loader_rejects_duplicate_and_unsafe_members():
    duplicate = make_synthetic_task10_production_zip(
        duplicate_member="TASK10_MANIFEST.json"
    )
    with pytest.raises(ValueError, match="duplicate ZIP members"):
        load_synthetic_task10(duplicate)

    unsafe = make_synthetic_task10_production_zip(extra_member="../escape.json")
    with pytest.raises(ValueError, match="unsafe ZIP member"):
        load_synthetic_task10(unsafe)


def test_member_sha_mismatch_stops_before_json_decode(monkeypatch):
    package = make_synthetic_task10_production_zip()
    expected_members = member_sha256_by_filename(package)
    expected_members["TASK10_MANIFEST.json"] = "0" * 64

    import research.task11_hypothesis_io as module
    monkeypatch.setattr(
        module,
        "_decode_json",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("JSON decode ran before member SHA validation")
        ),
    )
    with pytest.raises(ValueError, match="member SHA-256 mismatch"):
        _load_task10_production_bytes(
            package,
            expected_package_sha256=hashlib.sha256(package).hexdigest(),
            expected_member_sha256_by_filename=expected_members,
        )
```

Add one parametrized ZIP-name test covering an absolute member, a directory member, a backslash member, an empty path component, `.` and `..`. Add separate tests for one missing expected member and one unexpected safe member. Every test expects a `ValueError` that identifies the ZIP/member contract.

- [ ] **Step 3: Run the I/O test to prove RED**

```bash
pytest -q tests/test_task11_hypothesis_io.py
```

Expected: FAIL during collection because `research.task11_hypothesis_io` does not exist.

- [ ] **Step 4: Implement package-level fail-closed validation**

Create `research/task11_hypothesis_io.py` with the frozen boundary:

```python
@dataclass(frozen=True, slots=True)
class Task10ProductionBundle:
    main_dossiers: Sequence[Mapping[str, object]]
    manifest: Mapping[str, object]
    production_zip_sha256: str
    member_sha256_by_filename: Mapping[str, str]
```

Implement `_member_counts()` using `ZipInfo.filename`. Reject a name when it is empty, contains `\\`, begins with `/`, ends with `/`, or has any `/`-separated component in `{"", ".", ".."}`. Count all `ZipInfo` objects before reading; reject duplicate names. Require the exact five-name set from `TASK10_MEMBER_SHA256_BY_FILENAME`.

Implement the private loader in this exact gate order:

```python
def _load_task10_production_bytes(
    package_bytes: bytes,
    *,
    expected_package_sha256: str,
    expected_member_sha256_by_filename: Mapping[str, str],
) -> Task10ProductionBundle:
    actual_package_sha256 = hashlib.sha256(package_bytes).hexdigest()
    if actual_package_sha256 != expected_package_sha256:
        raise ValueError(
            "Task 10 Production SHA-256 mismatch: "
            f"expected {expected_package_sha256}, got {actual_package_sha256}"
        )
    members = _read_exact_members(package_bytes)
    actual_member_hashes = {
        name: hashlib.sha256(data).hexdigest() for name, data in members.items()
    }
    if actual_member_hashes != dict(expected_member_sha256_by_filename):
        raise ValueError("Task 10 Production member SHA-256 mismatch")
    return _decode_and_validate_task10_members(
        members,
        production_zip_sha256=actual_package_sha256,
        member_sha256_by_filename=actual_member_hashes,
    )
```

The public function has no override:

```python
def load_task10_production_package(path: Path) -> Task10ProductionBundle:
    return _load_task10_production_bytes(
        Path(path).read_bytes(),
        expected_package_sha256=TASK10_PRODUCTION_PACKAGE_SHA256,
        expected_member_sha256_by_filename=TASK10_MEMBER_SHA256_BY_FILENAME,
    )
```

The private seam is permitted only for synthetic tests. Do not export it in `__all__`.

- [ ] **Step 5: Write RED tests for strict decoding and exact Task 10 content contracts**

Add mutations that recompute the private expected package/member hashes, so these tests reach parsing and structural validation rather than failing at the earlier hash gate:

```python
@pytest.mark.parametrize(
    "member,replacement,error",
    [
        ("TASK10_MAIN_RELATIONSHIP_DOSSIERS.json", b"{bad json", "valid UTF-8 JSON"),
        ("TASK10_FEATURE_DOSSIERS.json", b'[{"x":NaN}]', "non-finite JSON"),
        ("TASK10_MANIFEST.json", b'{"task":1,"task":2}', "duplicate JSON key"),
        ("TASK10_SUPPLEMENTARY_EVIDENCE.csv", b"\xff", "must be UTF-8"),
    ],
)
def test_private_loader_rejects_malformed_member_content(
    member, replacement, error
):
    def mutate(members):
        members[member] = replacement
    package = make_synthetic_task10_production_zip(mutate=mutate)
    with pytest.raises(ValueError, match=error):
        load_synthetic_task10(package)
```

Add exact structural drift tests for:

1. Main Dossier root is not an array.
2. Count is 77 or 79.
3. Duplicate `pair_key`.
4. Pair array order differs from `TASK10_CANONICAL_PAIR_KEYS`.
5. A record has one missing or one extra top-level Task 10 field.
6. `pair_key != feature_x + "__" + feature_y`, identical features, or non-string features.
7. A raw/partial map lacks one of `M5/M15/M30/H1` or has an extra timeframe.
8. Raw, eligible-partial, control-partial, cross-TF, or deterministic-context nested key-set drift.
9. `n_defined_tf + n_undefined_tf != 4`.
10. Applicability count differs from 66/12, a control pair is eligible, or a non-control pair is non-applicable.
11. Control partial numeric fields are not JSON `null` or status is not `NOT_APPLICABLE_CONTROL_FEATURE`.
12. Raw/eligible controlled statistical status is outside `LOCKED_STATISTICAL_STATUSES`.
13. Deterministic mapping differs from the exact four locked pairs or a fifth pair is marked direct.
14. Artifact/row-locator maps are incomplete or conflict with locked control/eligible structure.
15. Task 10 Manifest has a missing/extra field, wrong Task 10 implementation commit, wrong Task 9 provenance, count drift, or any scope flag not exactly JSON `false`.
16. `TASK10_FUTURE_ABLATION_HYPOTHESES.json` is not the empty array.
17. Supplementary CSV is malformed under `csv.reader(stream, strict=True)`.

Each failure assertion matches the artifact name plus `pair_key` and timeframe/nested field when those values exist.

- [ ] **Step 6: Implement strict JSON/CSV and Main Dossier validation**

Implement `_reject_duplicate_json_keys`, `_reject_nonfinite_constant`, `_validate_json_finite`, `_decode_json`, `_validate_csv`, and `_decode_and_validate_task10_members(members: Mapping[str, bytes], *, production_zip_sha256: str, member_sha256_by_filename: Mapping[str, str]) -> Task10ProductionBundle`. `_decode_json` must use:

```python
json.loads(
    data.decode("utf-8"),
    object_pairs_hook=_reject_duplicate_json_keys,
    parse_constant=_reject_nonfinite_constant,
)
```

Recursively reject every non-finite `float`, including finite-looking JSON exponents that decode to infinity. `_validate_csv` decodes UTF-8, uses `csv.reader(stream, strict=True)`, consumes all rows, rejects parser errors, and authors no Task 11 data.

Implement `_validate_task10_manifest()` against the exact closed Task 10 Manifest key set and exact locked values from Task 1.

Implement `_validate_main_dossiers()` with all 17 structural checks from Step 5. The validator compares the observed ordered `pair_key` tuple to `TASK10_CANONICAL_PAIR_KEYS`; it never sorts source records. It validates exact JSON types with `type(value) is expected_type` where Python's `bool`/`int` subtype relationship could otherwise weaken the contract.

After all validations, return immutable top-level boundaries using `MappingProxyType` and tuples. The builder in Task 3 performs explicit recursive JSON copies; it never mutates this bundle.

- [ ] **Step 7: Run the I/O test to prove GREEN**

```bash
pytest -q tests/test_task11_hypothesis_io.py
```

Expected: PASS; all SHA-ordering, ZIP-safety, decoding, schema, provenance, count, deterministic-context, locator, and fail-closed tests pass; pytest exits 0.

- [ ] **Step 8: Commit the independently reviewable loader**

```bash
git add research/task11_hypothesis_io.py tests/test_task11_hypothesis_io.py
git commit -m "feat: add strict Task 10 production loader"
```

Expected: one commit containing exactly the two Task 2 paths.

---

### Task 3: Build and validate exactly 78 canonical Hypothesis records

**Files:**
- Create: `research/task11_hypothesis_registry.py`
- Create: `tests/test_task11_hypothesis_registry.py`

**Interfaces:**
- Consumes only `Sequence[Mapping[str, object]]` from `Task10ProductionBundle.main_dossiers` and frozen contract constants.
- Produces a JSON-native `list[dict[str, object]]` in exact source index order.
- Provides a separate validator used before serialization/writing.

- [ ] **Step 1: Write RED tests for cardinality, ordering, identity, and the fixed question**

Use `load_synthetic_task10(make_synthetic_task10_production_zip())` from the Task 2 test support and write:

```python
def test_registry_is_exactly_one_record_per_source_pair_in_source_order():
    bundle = load_synthetic_task10(make_synthetic_task10_production_zip())
    registry = build_hypothesis_registry(bundle.main_dossiers)

    assert len(registry) == 78
    assert [record["pair_key"] for record in registry] == [
        dossier["pair_key"] for dossier in bundle.main_dossiers
    ]
    assert len({record["hypothesis_id"] for record in registry}) == 78
    for source, record in zip(bundle.main_dossiers, registry, strict=True):
        assert record["feature_x"] == source["feature_x"]
        assert record["feature_y"] == source["feature_y"]
        assert record["hypothesis_id"] == "TASK11_HYPOTHESIS__" + source["pair_key"]


def test_every_question_is_the_single_locked_literal_template():
    bundle = load_synthetic_task10(make_synthetic_task10_production_zip())
    registry = build_hypothesis_registry(bundle.main_dossiers)

    for source, record in zip(bundle.main_dossiers, registry, strict=True):
        expected = (
            "Under a future separately locked controlled ablation protocol, "
            f"does the information relationship between {source['feature_x']} "
            f"and {source['feature_y']} remain measurable when their incremental "
            "information contributions are evaluated separately?"
        )
        assert record["test_question_template_id"] == "TASK11_PAIRWISE_NEUTRAL_V1"
        assert record["test_question"] == expected
```

Add an explicit test that reversing the source sequence before calling the builder raises `ValueError` with `canonical pair order`; the builder does not silently sort or normalize it.

- [ ] **Step 2: Run the registry test to prove RED**

```bash
pytest -q tests/test_task11_hypothesis_registry.py
```

Expected: FAIL during collection because `research.task11_hypothesis_registry` does not exist.

- [ ] **Step 3: Implement exact JSON-copy and identity/question construction**

Create `research/task11_hypothesis_registry.py` with a recursive JSON copier that preserves JSON scalar types and array order while converting immutable loader mappings/tuples back to JSON-native dict/list containers:

```python
def _copy_json(value: object) -> object:
    if isinstance(value, Mapping):
        return {key: _copy_json(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_copy_json(item) for item in value]
    if value is None or type(value) in {str, bool, int, float}:
        return value
    raise TypeError(f"unsupported JSON value type: {type(value).__name__}")


def render_test_question(feature_x: str, feature_y: str) -> str:
    return TEST_QUESTION_TEMPLATE.replace(
        "{feature_x}", feature_x
    ).replace("{feature_y}", feature_y)
```

Build every output record with exactly this field mapping and no additional key:

```python
record = {
    "hypothesis_id": HYPOTHESIS_ID_PREFIX + source["pair_key"],
    "pair_key": source["pair_key"],
    "feature_x": source["feature_x"],
    "feature_y": source["feature_y"],
    "raw_evidence_by_tf": _copy_json(source["raw_by_tf"]),
    "duration_control_applicability": source["partial_applicability"],
    "controlled_evidence_by_tf": _copy_json(source["partial_by_tf"]),
    "cross_tf_evidence": _copy_json(source["cross_tf"]),
    "direct_deterministic_dependency": source["direct_deterministic_dependency"],
    "deterministic_relation_ids": _copy_json(
        source["direct_deterministic_relation_ids"]
    ),
    "deterministic_context": _copy_json(source["deterministic_context"]),
    "evidence_summary": _copy_json(source["observations"]),
    "test_question_template_id": TEST_QUESTION_TEMPLATE_ID,
    "test_question": render_test_question(
        source["feature_x"], source["feature_y"]
    ),
    "source_locators": {
        "task10_main_dossier": (
            "TASK10_MAIN_RELATIONSHIP_DOSSIERS.json#" + source["pair_key"]
        ),
        "upstream_raw_source_artifact_by_tf": _copy_json(
            source["raw_source_artifact_by_tf"]
        ),
        "upstream_raw_source_row_locator_by_tf": _copy_json(
            source["raw_source_row_locator_by_tf"]
        ),
        "upstream_partial_source_artifact_by_tf": _copy_json(
            source["partial_source_artifact_by_tf"]
        ),
        "upstream_partial_source_row_locator_by_tf": _copy_json(
            source["partial_source_row_locator_by_tf"]
        ),
        "upstream_cross_tf_source_artifact": source["cross_tf_source_artifact"],
        "upstream_cross_tf_source_row_locator": source[
            "cross_tf_source_row_locator"
        ],
    },
}
```

`build_hypothesis_registry()` first validates source count/order against `TASK10_CANONICAL_PAIR_KEYS`, appends one record per source, calls `validate_hypothesis_registry(registry, main_dossiers)`, and returns only after validation succeeds.

- [ ] **Step 4: Write RED tests for every exact copy and closed-schema boundary**

Add tests that assert recursive JSON-type-sensitive equality for each mapped field, not only numeric equality:

```python
def assert_json_exact(actual, expected):
    assert type(actual) is type(expected)
    if isinstance(expected, dict):
        assert set(actual) == set(expected)
        for key in expected:
            assert_json_exact(actual[key], expected[key])
    elif isinstance(expected, list):
        assert len(actual) == len(expected)
        for left, right in zip(actual, expected, strict=True):
            assert_json_exact(left, right)
    else:
        assert actual == expected
```

Before comparison, convert the immutable synthetic source using the same test-only JSON-native conversion used by the fixture. For each record assert:

```python
assert_json_exact(record["raw_evidence_by_tf"], source_json["raw_by_tf"])
assert record["duration_control_applicability"] == source_json["partial_applicability"]
assert_json_exact(record["controlled_evidence_by_tf"], source_json["partial_by_tf"])
assert_json_exact(record["cross_tf_evidence"], source_json["cross_tf"])
assert record["direct_deterministic_dependency"] is source_json["direct_deterministic_dependency"]
assert_json_exact(record["deterministic_relation_ids"], source_json["direct_deterministic_relation_ids"])
assert_json_exact(record["deterministic_context"], source_json["deterministic_context"])
assert_json_exact(record["evidence_summary"], source_json["observations"])
assert set(record) == set(TASK11_HYPOTHESIS_RECORD_FIELDS)
assert set(record["source_locators"]) == set(TASK11_SOURCE_LOCATOR_FIELDS)
```

Add focused assertions for:

- Exactly 66 records copy complete eligible controlled evidence for all four TFs.
- Exactly 12 records copy `NOT_APPLICABLE_CONTROL_FEATURE`, retain JSON `null` controlled numeric fields, and retain null partial-artifact maps/status row-locator maps.
- `delta_rho_by_tf` is absent at the record top level and source-locator level; `delta_rho` remains present only in each copied `controlled_evidence_by_tf[tf]` object.
- Exactly four records copy the exact relation IDs in `DETERMINISTIC_RELATION_IDS_BY_PAIR_KEY`; all other records copy false/empty deterministic state and no extra Hypothesis is created.
- `evidence_summary` count, order, and every string are exact; modifying one observation or swapping two observations causes validation failure.
- The seven intentionally omitted Task 10 metadata fields and the Task 10 alias field names are absent from every record.
- The prohibited record field names from Spec Section 12 are absent.
- Mutating any copied nested output value does not mutate the loaded source bundle.

- [ ] **Step 5: Implement exact output validation**

Implement `validate_hypothesis_registry()` with these fail-closed checks:

1. Source and registry counts are both exactly 78.
2. Both ordered pair-key sequences equal `TASK10_CANONICAL_PAIR_KEYS` index-for-index.
3. Every record's key set exactly equals `TASK11_HYPOTHESIS_RECORD_FIELDS`.
4. Every locator key set exactly equals `TASK11_SOURCE_LOCATOR_FIELDS`; parsed JSON object-member order is not treated as semantic.
5. Pair/feature/ID/question values equal the locked formulas exactly.
6. Every copied field passes recursive JSON-type-sensitive equality against its Task 10 source.
7. Every source locator equals the exact Section 10 mapping.
8. Counts are exactly 66/12/4 and no deterministic pair adds a record.
9. No excluded Task 10 alias/metadata field, prohibited field, or independent `delta_rho_by_tf` exists.
10. `test_question_template_id` and `test_question` have no drift.

Error messages include the failing `pair_key`, index, and nested field path. Validation authors no interpretation text.

- [ ] **Step 6: Run the registry test to prove GREEN**

```bash
pytest -q tests/test_task11_hypothesis_registry.py
```

Expected: PASS; all 78-record, order, copy, template, identity, locator, deterministic-context, control-applicability, immutability, and prohibition tests pass; pytest exits 0.

- [ ] **Step 7: Commit the independently reviewable registry builder**

```bash
git add research/task11_hypothesis_registry.py tests/test_task11_hypothesis_registry.py
git commit -m "feat: register canonical Task 11 hypotheses"
```

Expected: one commit containing exactly the two Task 3 paths.

---

### Task 4: Build the closed manifest and deterministic logical outputs/archive

**Files:**
- Modify: `research/task11_hypothesis_io.py`
- Create: `research/run_task11_hypothesis_registration.py`
- Create: `tests/test_task11_hypothesis_integration.py`

**Interfaces:**
- Consumes a validated `Task10ProductionBundle`, exact registry builder, runtime committed implementation SHA, output directory, and required ZIP path.
- Produces `_build_manifest()`, `_run_task11_from_bundle()`, deterministic `TASK11_HYPOTHESIS_REGISTRY.json`, deterministic `TASK11_MANIFEST.json`, and deterministic production ZIP.
- Does not yet expose the public loader/guard/CLI path; Task 5 adds that boundary.

- [ ] **Step 1: Write the RED private two-run integration test**

Create `tests/test_task11_hypothesis_integration.py` and import the Task 2 fixture. Run the private seam twice with the same synthetic bundle and fixed test commit:

```python
def artifact_bytes(directory: Path) -> dict[str, bytes]:
    return {path.name: path.read_bytes() for path in directory.iterdir()}


def test_private_pipeline_is_byte_deterministic_and_scope_locked(tmp_path: Path):
    package = make_synthetic_task10_production_zip()
    bundle = load_synthetic_task10(package)
    first_dir = tmp_path / "first"
    second_dir = tmp_path / "second"
    first_zip = tmp_path / "first.zip"
    second_zip = tmp_path / "second.zip"

    first_manifest = _run_task11_from_bundle(
        bundle,
        first_dir,
        implementation_commit="a" * 40,
        output_zip=first_zip,
    )
    second_manifest = _run_task11_from_bundle(
        bundle,
        second_dir,
        implementation_commit="a" * 40,
        output_zip=second_zip,
    )

    assert set(artifact_bytes(first_dir)) == set(TASK11_LOGICAL_FILENAMES)
    assert artifact_bytes(first_dir) == artifact_bytes(second_dir)
    assert first_zip.read_bytes() == second_zip.read_bytes()
    assert first_manifest == second_manifest
```

Parse the registry and manifest and assert registry count 78, manifest key set exactly `TASK11_MANIFEST_FIELDS`, `hypothesis_registry_sha256` equals the SHA-256 of the exact written registry bytes, and all 17 `TASK11_FALSE_SCOPE_FIELDS` are exactly `False` by identity.

- [ ] **Step 2: Run the integration test to prove RED**

```bash
pytest -q tests/test_task11_hypothesis_integration.py
```

Expected: FAIL during collection because `research.run_task11_hypothesis_registration` does not exist.

- [ ] **Step 3: Implement deterministic JSON and ZIP primitives**

Append to `research/task11_hypothesis_io.py`:

```python
def _json_bytes(value: object) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            allow_nan=False,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")


def _write_deterministic_zip(path: Path, members: Mapping[str, bytes]) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(
        destination,
        "w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9,
    ) as archive:
        for name in sorted(members):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(
                info,
                members[name],
                compress_type=zipfile.ZIP_DEFLATED,
                compresslevel=9,
            )
```

`write_task11_outputs()` must perform every validation in memory before `mkdir()` or the first write:

1. `implementation_commit` matches lowercase SHA-1 regex `[0-9a-f]{40}`.
2. Registry validates against the supplied source dossiers before this writer is called.
3. Manifest key set exactly equals `TASK11_MANIFEST_FIELDS`.
4. `task11_implementation_commit` equals the supplied implementation commit with exact string type.
5. Manifest `hypothesis_registry_sha256` equals `sha256(_json_bytes(registry))`.
6. All locked manifest constants/counts/policies/false flags are exact with type-sensitive comparison.
7. Member mapping is exactly the two `TASK11_LOGICAL_FILENAMES`.

Only after those checks, write the two logical files and the required ZIP. `output_zip` has no `None` branch.

- [ ] **Step 4: Implement exact closed manifest construction and private orchestration**

Create `research/run_task11_hypothesis_registration.py` with `_build_manifest()`. Reject an implementation commit that is not lowercase 40-hex and reject any observed count tuple other than `(78, 78, 66, 12, 4, 2)`.

Construct exactly this closed manifest and no extra field:

```python
manifest: dict[str, object] = {
    "task": "Task 11 — Evidence Review & Hypothesis Registration",
    "task11_spec_commit": TASK11_SPEC_COMMIT,
    "task11_implementation_commit": implementation_commit,
    "hypothesis_registry_filename": "TASK11_HYPOTHESIS_REGISTRY.json",
    "hypothesis_registry_sha256": hypothesis_registry_sha256,
    "production_archive_filename": OUTPUT_ZIP_FILENAME,
    "logical_output_filenames": list(TASK11_LOGICAL_FILENAMES),
    "task10_implementation_commit": TASK10_IMPLEMENTATION_COMMIT,
    "task10_production_package_filename": TASK10_PRODUCTION_PACKAGE_FILENAME,
    "task10_production_package_sha256": TASK10_PRODUCTION_PACKAGE_SHA256,
    "task10_main_dossiers_member_sha256": TASK10_MAIN_DOSSIERS_MEMBER_SHA256,
    "task10_manifest_member_sha256": TASK10_MANIFEST_MEMBER_SHA256,
    "hypothesis_unit": "PAIRWISE_ONLY",
    "hypothesis_cardinality": "EXACTLY_ONE_PER_CANONICAL_PAIR",
    "hypothesis_id_policy": "DETERMINISTIC_FROM_PAIR_KEY",
    "hypothesis_id_prefix": HYPOTHESIS_ID_PREFIX,
    "test_question_policy": "SINGLE_FIXED_TEMPLATE",
    "test_question_template_id": TEST_QUESTION_TEMPLATE_ID,
    "evidence_summary_policy": "COPY_LOCKED_TASK10_OBSERVATIONS",
    "cross_tf_evidence_policy": "COPY_LOCKED_TASK10_CROSS_TF",
    "main_pair_count": main_pair_count,
    "hypothesis_count": hypothesis_count,
    "duration_control_eligible_count": duration_control_eligible_count,
    "control_feature_non_applicable_count": (
        control_feature_non_applicable_count
    ),
    "deterministic_context_pair_count": deterministic_context_pair_count,
    "logical_file_count": LOGICAL_FILE_COUNT,
    **{field: False for field in TASK11_FALSE_SCOPE_FIELDS},
}
if set(manifest) != set(TASK11_MANIFEST_FIELDS):
    raise RuntimeError("Task 11 manifest closed schema drifted")
```

Implement the private pipeline in this exact order:

```python
def _run_task11_from_bundle(
    bundle: Task10ProductionBundle,
    output_dir: Path,
    *,
    implementation_commit: str,
    output_zip: Path,
) -> dict[str, object]:
    registry = build_hypothesis_registry(bundle.main_dossiers)
    validate_hypothesis_registry(registry, bundle.main_dossiers)
    registry_bytes = _json_bytes(registry)
    eligible_count = sum(
        record["duration_control_applicability"] == "ELIGIBLE"
        for record in registry
    )
    control_count = sum(
        record["duration_control_applicability"]
        == "NOT_APPLICABLE_CONTROL_FEATURE"
        for record in registry
    )
    deterministic_count = sum(
        record["direct_deterministic_dependency"] is True
        for record in registry
    )
    manifest = _build_manifest(
        bundle,
        implementation_commit=implementation_commit,
        hypothesis_registry_sha256=hashlib.sha256(registry_bytes).hexdigest(),
        main_pair_count=len(bundle.main_dossiers),
        hypothesis_count=len(registry),
        duration_control_eligible_count=eligible_count,
        control_feature_non_applicable_count=control_count,
        deterministic_context_pair_count=deterministic_count,
    )
    write_task11_outputs(
        output_dir,
        implementation_commit=implementation_commit,
        registry=registry,
        manifest=manifest,
        output_zip=output_zip,
    )
    return manifest
```

The `sum()` calls classify already-copied locked states; they do not compute a research statistic. `_build_manifest()` also verifies `bundle.production_zip_sha256` and both relevant member hashes against the canonical constants before returning.

- [ ] **Step 5: Write RED tests for manifest drift, fail-closed output, and ZIP metadata**

Add tests that mutate each manifest field class before `write_task11_outputs()` and assert no output directory or ZIP is created:

```python
@pytest.mark.parametrize(
    "field,bad_value",
    [
        ("hypothesis_count", 77),
        ("logical_file_count", 3),
        ("task11_spec_commit", "0" * 40),
        ("task10_production_package_sha256", "0" * 64),
        ("ranking_performed", True),
        ("score_computed", True),
        ("threshold_applied", True),
        ("ablation_executed", True),
        ("causal_replay_executed", True),
        ("feature_selection_performed", True),
    ],
)
def test_writer_rejects_manifest_drift_before_creating_output(
    tmp_path, field, bad_value
):
    bundle = load_synthetic_task10(make_synthetic_task10_production_zip())
    registry = build_hypothesis_registry(bundle.main_dossiers)
    registry_bytes = _json_bytes(registry)
    manifest = _build_manifest(
        bundle,
        implementation_commit="a" * 40,
        hypothesis_registry_sha256=hashlib.sha256(registry_bytes).hexdigest(),
        main_pair_count=78,
        hypothesis_count=78,
        duration_control_eligible_count=66,
        control_feature_non_applicable_count=12,
        deterministic_context_pair_count=4,
    )
    manifest[field] = bad_value
    output_dir = tmp_path / "rejected"
    output_zip = tmp_path / "rejected.zip"
    with pytest.raises(ValueError, match="manifest"):
        write_task11_outputs(
            output_dir,
            implementation_commit="a" * 40,
            registry=registry,
            manifest=manifest,
            output_zip=output_zip,
        )
    assert not output_dir.exists()
    assert not output_zip.exists()
```

Add one missing-key and one extra-key manifest test. Add a registry-hash mismatch test. Add ZIP assertions:

```python
with zipfile.ZipFile(first_zip) as archive:
    assert archive.namelist() == sorted(TASK11_LOGICAL_FILENAMES)
    for info in archive.infolist():
        assert info.date_time == (1980, 1, 1, 0, 0, 0)
        assert info.create_system == 3
        assert info.external_attr >> 16 == 0o100644
        assert info.extra == b""
```

Assert both logical JSON files end in exactly one newline, contain no `NaN`/`Infinity`, and reserialize byte-identically with the locked serializer.

- [ ] **Step 6: Run the integration test to prove GREEN**

```bash
pytest -q tests/test_task11_hypothesis_integration.py
```

Expected: PASS; exact manifest/schema/hash/count/scope, pre-write failure, two logical files, deterministic JSON, deterministic ZIP metadata, and byte-repeatability tests pass; pytest exits 0.

- [ ] **Step 7: Run all Task 11 tests accumulated so far**

```bash
pytest -q tests/test_task11_hypothesis_contract.py tests/test_task11_hypothesis_io.py tests/test_task11_hypothesis_registry.py tests/test_task11_hypothesis_integration.py
```

Expected: PASS; all Task 1–4 tests pass and pytest exits 0.

- [ ] **Step 8: Commit the independently reviewable deterministic private pipeline**

```bash
git add research/task11_hypothesis_io.py research/run_task11_hypothesis_registration.py tests/test_task11_hypothesis_integration.py
git commit -m "feat: add deterministic Task 11 output pipeline"
```

Expected: one commit containing exactly the three Task 4 paths.

---

### Task 5: Add the production provenance gate, public function, and CLI

**Files:**
- Modify: `research/run_task11_hypothesis_registration.py`
- Modify: `tests/test_task11_hypothesis_integration.py`

**Interfaces:**
- Produces `assert_clean_committed_task11_worktree() -> str`, public `run_task11()`, `build_parser()`, and `main()`.
- Public flow is strictly `guard → canonical loader → private deterministic pipeline`.
- Captured guard SHA is the sole value allowed in `task11_implementation_commit`.

- [ ] **Step 1: Write RED tests for the public signature and CLI surface**

```python
def test_public_function_and_cli_expose_only_locked_runtime_paths():
    parameters = inspect.signature(run_task11).parameters
    assert tuple(parameters) == (
        "input_task10_production",
        "output_dir",
        "output_zip",
    )
    assert parameters["output_zip"].kind is inspect.Parameter.KEYWORD_ONLY
    assert parameters["output_zip"].default is inspect.Parameter.empty

    option_strings = {
        option
        for action in build_parser()._actions
        for option in action.option_strings
    }
    assert option_strings == {
        "-h",
        "--help",
        "--input-task10-production",
        "--output-dir",
        "--output-zip",
    }
    assert all(
        build_parser().get_default(name) is None
        for name in ("input_task10_production", "output_dir", "output_zip")
    )
```

Inspect each parser action and assert the three non-help options are `required=True` and `type is Path`. Assert no option/parameter contains any of: `sha`, `loader`, `bundle`, `template`, `identifier`, `count`, `ordering`, `commit`, `rank`, `score`, `threshold`, `outcome`, `ablation`, `causal`, `feature_selection`.

- [ ] **Step 2: Write RED tests proving the guard runs before input read/output creation**

```python
def test_public_flow_stops_at_guard_before_loader_or_output(tmp_path, monkeypatch):
    import research.run_task11_hypothesis_registration as runner

    def blocked_guard():
        raise RuntimeError("guard blocked")

    def loader_must_not_run(_path):
        raise AssertionError("loader ran after failed provenance guard")

    monkeypatch.setattr(runner, "assert_clean_committed_task11_worktree", blocked_guard)
    monkeypatch.setattr(runner, "load_task10_production_package", loader_must_not_run)

    output_dir = tmp_path / "blocked"
    output_zip = tmp_path / "blocked.zip"
    with pytest.raises(RuntimeError, match="guard blocked"):
        run_task11(
            tmp_path / "unused.zip",
            output_dir,
            output_zip=output_zip,
        )
    assert not output_dir.exists()
    assert not output_zip.exists()
```

Add a second test that monkeypatches the guard to return `"b" * 40`, supplies a validated synthetic bundle through the loader, runs `run_task11()`, and asserts both the returned and written Manifest contain exactly `"b" * 40` as `task11_implementation_commit`.

- [ ] **Step 3: Write RED tests for clean committed repository provenance**

Create `_init_guard_repo()` in the integration test. It must:

1. Initialize a temporary Git repository and configure a test identity.
2. Copy the locked Spec bytes into `TASK11_SPEC_PATH`, commit them, and capture the synthetic Spec commit/blob.
3. Copy the locked Lock Record bytes into `TASK11_SPEC_LOCK_RECORD_PATH`, commit them, and capture the synthetic Lock commit/blob.
4. Create and commit the four required Task 11 implementation paths.
5. Monkeypatch runner constants to those synthetic commit/blob values and `_REPOSITORY_ROOT` to the temporary repository.

Test these exact cases:

- Clean tracked tree and clean index return exact HEAD.
- Unstaged tracked change rejects with `tracked worktree is not clean`.
- Staged change rejects with the same error.
- Missing any one required Task 11 implementation path at HEAD rejects and names the path.
- Locked Spec commit is not an ancestor of HEAD rejects with `locked Task 11 Spec commit is not an ancestor`.
- Lock Record commit is not an ancestor rejects with `Task 11 Spec Lock commit is not an ancestor`.
- Committed Spec bytes with a different blob reject with `locked Task 11 Spec blob mismatch`.
- Committed Lock Record bytes with a different blob reject with `Task 11 Spec Lock Record blob mismatch`.
- Invalid or absent HEAD rejects with `invalid HEAD SHA`.

- [ ] **Step 4: Run the integration test to prove RED**

```bash
pytest -q tests/test_task11_hypothesis_integration.py
```

Expected: FAIL because the guard/public/CLI interfaces are not yet defined.

- [ ] **Step 5: Implement the exact provenance guard**

In `research/run_task11_hypothesis_registration.py`, add:

```python
_REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
_REQUIRED_HEAD_PATHS = (
    "research/task11_hypothesis_contract.py",
    "research/task11_hypothesis_io.py",
    "research/task11_hypothesis_registry.py",
    "research/run_task11_hypothesis_registration.py",
    TASK11_SPEC_PATH,
    TASK11_SPEC_LOCK_RECORD_PATH,
)
_SHA1_RE = re.compile(r"[0-9a-f]{40}\Z")


def _git(*args: str, capture_output: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=_REPOSITORY_ROOT,
        check=False,
        capture_output=capture_output,
        text=True,
    )
```

`assert_clean_committed_task11_worktree()` runs the following in order:

1. `git diff --quiet` and `git diff --cached --quiet`; any nonzero status fails.
2. `git status --porcelain=v1 --untracked-files=no`; command failure or nonempty output fails. Untracked output artifacts are intentionally ignored.
3. `git rev-parse HEAD`; require lowercase 40-hex.
4. `git merge-base --is-ancestor TASK11_SPEC_COMMIT HEAD`; require exit 0.
5. `git merge-base --is-ancestor TASK11_SPEC_LOCK_COMMIT HEAD`; require exit 0.
6. `git cat-file -e "HEAD:${path}"` for every `path` in `_REQUIRED_HEAD_PATHS`.
7. `git rev-parse HEAD:TASK11_SPEC_PATH`; require `TASK11_SPEC_BLOB_SHA`.
8. `git rev-parse HEAD:TASK11_SPEC_LOCK_RECORD_PATH`; require `TASK11_SPEC_LOCK_RECORD_BLOB_SHA`.
9. Return the exact HEAD captured in Step 3.

The guard performs no checkout, reset, index mutation, commit, or file write.

- [ ] **Step 6: Implement the public function and required CLI**

```python
def run_task11(
    input_task10_production: Path,
    output_dir: Path,
    *,
    output_zip: Path,
) -> dict[str, object]:
    implementation_commit = assert_clean_committed_task11_worktree()
    bundle = load_task10_production_package(input_task10_production)
    return _run_task11_from_bundle(
        bundle,
        output_dir,
        implementation_commit=implementation_commit,
        output_zip=output_zip,
    )
```

Define parser options exactly:

```python
parser.add_argument("--input-task10-production", required=True, type=Path)
parser.add_argument("--output-dir", required=True, type=Path)
parser.add_argument("--output-zip", required=True, type=Path)
```

`main()` passes only those three paths to `run_task11()` and returns 0. The module ends with `raise SystemExit(main())` under the standard `__main__` guard.

- [ ] **Step 7: Run GREEN public-boundary tests**

```bash
pytest -q tests/test_task11_hypothesis_integration.py
```

Expected: PASS; signature, CLI, guard ordering, exact implementation SHA propagation, clean/dirty/index/missing-path/ancestry/blob cases, and no-output-on-guard-failure tests pass; pytest exits 0.

- [ ] **Step 8: Run all Task 11 tests**

```bash
pytest -q tests/test_task11_hypothesis_contract.py tests/test_task11_hypothesis_io.py tests/test_task11_hypothesis_registry.py tests/test_task11_hypothesis_integration.py
```

Expected: PASS; all Task 11 tests pass and pytest exits 0.

- [ ] **Step 9: Commit the independently reviewable public production boundary**

```bash
git add research/run_task11_hypothesis_registration.py tests/test_task11_hypothesis_integration.py
git commit -m "feat: add provenance-safe Task 11 CLI"
```

Expected: one commit containing exactly the two Task 5 paths.

---

### Task 6: Full verification, regression protection, and scope audit

**Files:**
- Test/inspection only; create or modify no file.

**Interfaces:**
- Consumes the committed Task 1–5 implementation state.
- Produces a review report with test results, compile result, changed-path allowlist, protected-path confirmation, and tracked/index cleanliness.

- [ ] **Step 1: Compile every new production module**

```bash
python -m py_compile \
  research/task11_hypothesis_contract.py \
  research/task11_hypothesis_io.py \
  research/task11_hypothesis_registry.py \
  research/run_task11_hypothesis_registration.py
```

Expected: exit 0 and no output.

- [ ] **Step 2: Run the complete Task 11 test suite**

```bash
pytest -q \
  tests/test_task11_hypothesis_contract.py \
  tests/test_task11_hypothesis_io.py \
  tests/test_task11_hypothesis_registry.py \
  tests/test_task11_hypothesis_integration.py
```

Expected: PASS; zero failures/errors/skips caused by Task 11 and pytest exits 0.

- [ ] **Step 3: Run the complete locked Task 10 regression suite**

```bash
pytest -q \
  tests/test_task10_interpretation_contract.py \
  tests/test_task10_interpretation_io.py \
  tests/test_task10_interpretation_reports.py \
  tests/test_task10_interpretation_integration.py
```

Expected: PASS; zero failures/errors and pytest exits 0.

- [ ] **Step 4: Run the complete Combined Audit regression suite**

```bash
pytest -q \
  tests/test_combined_audit_contract.py \
  tests/test_combined_audit_stats.py \
  tests/test_combined_audit_deterministic.py \
  tests/test_combined_audit_reports.py \
  tests/test_combined_audit_io.py \
  tests/test_combined_audit_integration.py
```

Expected: PASS; zero failures/errors and pytest exits 0.

- [ ] **Step 5: Run the full repository regression**

```bash
pytest -q
```

Expected: PASS; zero failures/errors and pytest exits 0.

- [ ] **Step 6: Prove the implementation changed exactly the eight allowed paths**

```bash
TASK11_EXECUTION_BASELINE="$(git log -1 --format=%H -- docs/superpowers/plans/2026-09-01-task11-evidence-review-hypothesis-registration.md)"
git diff --name-only "$TASK11_EXECUTION_BASELINE" HEAD
```

Expected output, with no extra path:

```text
research/run_task11_hypothesis_registration.py
research/task11_hypothesis_contract.py
research/task11_hypothesis_io.py
research/task11_hypothesis_registry.py
tests/test_task11_hypothesis_contract.py
tests/test_task11_hypothesis_integration.py
tests/test_task11_hypothesis_io.py
tests/test_task11_hypothesis_registry.py
```

Enforce it mechanically:

```bash
TASK11_EXECUTION_BASELINE="$(git log -1 --format=%H -- docs/superpowers/plans/2026-09-01-task11-evidence-review-hypothesis-registration.md)"
git diff --name-only "$TASK11_EXECUTION_BASELINE" HEAD | sort > /tmp/task11-actual-paths.txt
printf '%s\n' \
  research/run_task11_hypothesis_registration.py \
  research/task11_hypothesis_contract.py \
  research/task11_hypothesis_io.py \
  research/task11_hypothesis_registry.py \
  tests/test_task11_hypothesis_contract.py \
  tests/test_task11_hypothesis_integration.py \
  tests/test_task11_hypothesis_io.py \
  tests/test_task11_hypothesis_registry.py \
  | sort > /tmp/task11-allowed-paths.txt
cmp /tmp/task11-allowed-paths.txt /tmp/task11-actual-paths.txt
```

Expected: `cmp` exits 0 with no output. `/tmp` files are verification scratch data outside the repository.

- [ ] **Step 7: Prove every locked/protected path is unchanged**

```bash
TASK11_EXECUTION_BASELINE="$(git log -1 --format=%H -- docs/superpowers/plans/2026-09-01-task11-evidence-review-hypothesis-registration.md)"
git diff --quiet "$TASK11_EXECUTION_BASELINE" HEAD -- \
  src \
  evidence \
  'research/combined_audit_*.py' \
  research/task10_interpretation_contract.py \
  research/task10_interpretation_io.py \
  research/task10_interpretation_reports.py \
  research/run_task10_dependency_interpretation.py \
  docs/superpowers/specs/2026-09-01-task11-evidence-review-hypothesis-registration-design.md \
  docs/superpowers/specs/2026-09-01-task11-evidence-review-hypothesis-registration-design.LOCKED.md \
  docs/superpowers/plans/2026-09-01-task11-evidence-review-hypothesis-registration.md
```

Expected: exit 0 and no output. Then reverify immutable bindings:

```bash
test "$(git rev-parse HEAD:docs/superpowers/specs/2026-09-01-task11-evidence-review-hypothesis-registration-design.md)" = "99e93ef6ca7cf1038561e7d6c4217e226ba99dfb"
test "$(git rev-parse HEAD:docs/superpowers/specs/2026-09-01-task11-evidence-review-hypothesis-registration-design.LOCKED.md)" = "de87a930b424b0cf9e58e14c8b27dca336954f33"
```

Expected: both commands exit 0.

- [ ] **Step 8: Static no-statistics/no-unauthorized-scope inspection**

Run an AST scan over the four new production modules. Fail if they import `statistics`, `numpy`, `pandas`, `scipy`, `research.combined_audit_stats`, or `src`; fail if any call target is named `spearman_pairwise`, `partial_spearman_duration`, `corr`, `rank`, `score`, `predict`, `optimize`, `ablate`, or `causal_replay`.

```bash
python - <<'PY'
import ast
from pathlib import Path

paths = [
    Path("research/task11_hypothesis_contract.py"),
    Path("research/task11_hypothesis_io.py"),
    Path("research/task11_hypothesis_registry.py"),
    Path("research/run_task11_hypothesis_registration.py"),
]
forbidden_import_roots = {
    "statistics", "numpy", "pandas", "scipy", "src"
}
forbidden_modules = {"research.combined_audit_stats"}
forbidden_calls = {
    "spearman_pairwise", "partial_spearman_duration", "corr", "rank",
    "score", "predict", "optimize", "ablate", "causal_replay",
}
for path in paths:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in forbidden_import_roots
                assert alias.name not in forbidden_modules
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            assert module.split(".")[0] not in forbidden_import_roots
            assert module not in forbidden_modules
        elif isinstance(node, ast.Call):
            target = node.func
            name = target.id if isinstance(target, ast.Name) else (
                target.attr if isinstance(target, ast.Attribute) else ""
            )
            assert name not in forbidden_calls
print("Task 11 static scope scan: PASS")
PY
```

Expected exact output: `Task 11 static scope scan: PASS`.

- [ ] **Step 9: Verify committed clean state and stop before production**

```bash
git diff --quiet
git diff --cached --quiet
test -z "$(git status --porcelain=v1 --untracked-files=no)"
git rev-parse HEAD
```

Expected: the first three checks exit 0; the final command prints the committed Task 11 implementation HEAD. Do not create an empty verification commit.

Report Task 11 tests, Task 10 regression, Combined Audit regression, full pytest, exact changed paths, protected-path hashes, static scope scan, implementation HEAD, and clean tracked/index state. Then stop for a separate production authorization.

---

## HUMAN APPROVAL GATE — REQUIRED BEFORE TASK 11 PRODUCTION EXECUTION

Tasks 1–6 implement and verify the locked registration layer only after separate implementation authorization. Even after those tasks pass, do not run the canonical production package until a human explicitly authorizes Task 11 Production.

Controlled Ablation Design/execution, Causal Replay, Score, Threshold, Ranking, Outcome, Prediction, Optimization, Feature Removal, and Feature Selection remain unauthorized regardless of Task 11 Production authorization.

---

### Task 7: Production registration and verification — only after separate explicit authorization

**Files:**
- Production execution/verification only; create no tracked repository file and make no commit.
- Generated outputs must be outside tracked repository paths.

**Interfaces:**
- Consumes the operator-supplied local path in `TASK11_TASK10_ZIP`; the public loader accepts it only when its bytes match the canonical SHA.
- Produces two independent output directories and two required ZIPs for byte comparison, then designates either identical ZIP as the final production archive.

- [ ] **Step 1: Bind the runtime input path and verify the public provenance guard**

```bash
: "${TASK11_TASK10_ZIP:?TASK11_TASK10_ZIP must name the existing canonical Task 10 Production ZIP}"
test -f "$TASK11_TASK10_ZIP"
export TASK11_TASK10_ZIP
TASK11_IMPLEMENTATION_HEAD="$(python - <<'PY'
from research.run_task11_hypothesis_registration import (
    assert_clean_committed_task11_worktree,
)
print(assert_clean_committed_task11_worktree())
PY
)"
test "$TASK11_IMPLEMENTATION_HEAD" = "$(git rev-parse HEAD)"
export TASK11_IMPLEMENTATION_HEAD
```

Expected: all commands exit 0; `TASK11_IMPLEMENTATION_HEAD` is the current clean committed lowercase 40-hex HEAD. Any failure stops production before reading the ZIP or creating output.

- [ ] **Step 2: Independently verify the canonical Task 10 package SHA-256**

```bash
TASK11_TASK10_SHA_BEFORE="$(sha256sum "$TASK11_TASK10_ZIP" | awk '{print $1}')"
test "$TASK11_TASK10_SHA_BEFORE" = "464465ef3dd435ed3a574bf8ded917095dcb76bb614416625b8c96db78c48903"
export TASK11_TASK10_SHA_BEFORE
```

Expected: exit 0. Mismatch is a blocker before ZIP parsing.

- [ ] **Step 3: Run the public CLI twice into new untracked temporary paths**

```bash
TASK11_RUN_ROOT="$(mktemp -d)"
export TASK11_RUN_ROOT
python -m research.run_task11_hypothesis_registration \
  --input-task10-production "$TASK11_TASK10_ZIP" \
  --output-dir "$TASK11_RUN_ROOT/run1" \
  --output-zip "$TASK11_RUN_ROOT/TASK11_PRODUCTION_RUN1.zip"
python -m research.run_task11_hypothesis_registration \
  --input-task10-production "$TASK11_TASK10_ZIP" \
  --output-dir "$TASK11_RUN_ROOT/run2" \
  --output-zip "$TASK11_RUN_ROOT/TASK11_PRODUCTION_RUN2.zip"
```

Expected: both commands exit 0 and create exactly two logical files per run plus one ZIP per run. Do not use the private synthetic seam.

- [ ] **Step 4: Byte-compare both logical files and both ZIPs**

```bash
cmp \
  "$TASK11_RUN_ROOT/run1/TASK11_HYPOTHESIS_REGISTRY.json" \
  "$TASK11_RUN_ROOT/run2/TASK11_HYPOTHESIS_REGISTRY.json"
cmp \
  "$TASK11_RUN_ROOT/run1/TASK11_MANIFEST.json" \
  "$TASK11_RUN_ROOT/run2/TASK11_MANIFEST.json"
cmp \
  "$TASK11_RUN_ROOT/TASK11_PRODUCTION_RUN1.zip" \
  "$TASK11_RUN_ROOT/TASK11_PRODUCTION_RUN2.zip"
```

Expected: all three `cmp` commands exit 0 with no output.

- [ ] **Step 5: Independently validate records, exact copies, locators, manifest, and ZIP metadata**

```bash
python - <<'PY'
import hashlib
import json
import os
from pathlib import Path
import zipfile

from research.task11_hypothesis_contract import (
    DETERMINISTIC_RELATION_IDS_BY_PAIR_KEY,
    TASK11_FALSE_SCOPE_FIELDS,
    TASK11_HYPOTHESIS_RECORD_FIELDS,
    TASK11_LOGICAL_FILENAMES,
    TASK11_MANIFEST_FIELDS,
    TASK11_SOURCE_LOCATOR_FIELDS,
    TEST_QUESTION_TEMPLATE,
    TEST_QUESTION_TEMPLATE_ID,
)

root = Path(os.environ["TASK11_RUN_ROOT"])
source_zip = Path(os.environ["TASK11_TASK10_ZIP"])
implementation_head = os.environ["TASK11_IMPLEMENTATION_HEAD"]
with zipfile.ZipFile(source_zip) as archive:
    source = json.loads(
        archive.read("TASK10_MAIN_RELATIONSHIP_DOSSIERS.json")
    )
registry_path = root / "run1" / "TASK11_HYPOTHESIS_REGISTRY.json"
manifest_path = root / "run1" / "TASK11_MANIFEST.json"
registry_bytes = registry_path.read_bytes()
registry = json.loads(registry_bytes)
manifest = json.loads(manifest_path.read_bytes())

assert len(source) == len(registry) == 78
assert [item["pair_key"] for item in registry] == [
    item["pair_key"] for item in source
]

excluded = {
    "source_pair_key",
    "feature_x_analysis_role",
    "feature_y_analysis_role",
    "feature_x_formula",
    "feature_y_formula",
    "feature_x_direction_semantics",
    "feature_y_direction_semantics",
    "raw_by_tf",
    "partial_by_tf",
    "cross_tf",
    "observations",
    "delta_rho_by_tf",
}
for source_record, record in zip(source, registry, strict=True):
    pair_key = source_record["pair_key"]
    feature_x = source_record["feature_x"]
    feature_y = source_record["feature_y"]
    assert set(record) == set(TASK11_HYPOTHESIS_RECORD_FIELDS)
    assert record["pair_key"] == pair_key
    assert record["feature_x"] == feature_x
    assert record["feature_y"] == feature_y
    assert record["hypothesis_id"] == "TASK11_HYPOTHESIS__" + pair_key
    assert record["raw_evidence_by_tf"] == source_record["raw_by_tf"]
    assert record["duration_control_applicability"] == source_record["partial_applicability"]
    assert record["controlled_evidence_by_tf"] == source_record["partial_by_tf"]
    assert record["cross_tf_evidence"] == source_record["cross_tf"]
    assert record["direct_deterministic_dependency"] is source_record["direct_deterministic_dependency"]
    assert record["deterministic_relation_ids"] == source_record["direct_deterministic_relation_ids"]
    assert record["deterministic_context"] == source_record["deterministic_context"]
    assert record["evidence_summary"] == source_record["observations"]
    assert record["test_question_template_id"] == TEST_QUESTION_TEMPLATE_ID
    assert record["test_question"] == TEST_QUESTION_TEMPLATE.replace(
        "{feature_x}", feature_x
    ).replace("{feature_y}", feature_y)
    assert set(record["source_locators"]) == set(TASK11_SOURCE_LOCATOR_FIELDS)
    assert record["source_locators"] == {
        "task10_main_dossier": (
            "TASK10_MAIN_RELATIONSHIP_DOSSIERS.json#" + pair_key
        ),
        "upstream_raw_source_artifact_by_tf": source_record["raw_source_artifact_by_tf"],
        "upstream_raw_source_row_locator_by_tf": source_record["raw_source_row_locator_by_tf"],
        "upstream_partial_source_artifact_by_tf": source_record["partial_source_artifact_by_tf"],
        "upstream_partial_source_row_locator_by_tf": source_record["partial_source_row_locator_by_tf"],
        "upstream_cross_tf_source_artifact": source_record["cross_tf_source_artifact"],
        "upstream_cross_tf_source_row_locator": source_record["cross_tf_source_row_locator"],
    }
    assert not (set(record) & excluded)

assert sum(
    item["duration_control_applicability"] == "ELIGIBLE"
    for item in registry
) == 66
assert sum(
    item["duration_control_applicability"]
    == "NOT_APPLICABLE_CONTROL_FEATURE"
    for item in registry
) == 12
assert sum(
    item["direct_deterministic_dependency"] is True for item in registry
) == 4
assert {
    item["pair_key"]: tuple(item["deterministic_relation_ids"])
    for item in registry
    if item["direct_deterministic_dependency"]
} == dict(DETERMINISTIC_RELATION_IDS_BY_PAIR_KEY)

assert set(manifest) == set(TASK11_MANIFEST_FIELDS)
assert manifest["task"] == "Task 11 — Evidence Review & Hypothesis Registration"
assert manifest["task11_spec_commit"] == "7a3553770ea51e4ae72662fa44907f507779d22d"
assert manifest["task11_implementation_commit"] == implementation_head
assert manifest["hypothesis_registry_filename"] == "TASK11_HYPOTHESIS_REGISTRY.json"
assert manifest["production_archive_filename"] == "TASK11_EVIDENCE_REVIEW_HYPOTHESIS_REGISTRATION_PACKAGE.zip"
assert manifest["task10_implementation_commit"] == "0a780ca95c4e6853bb2530436c6045c54f508e80"
assert manifest["task10_production_package_filename"] == "TASK10_PRODUCTION_RUN1.zip"
assert manifest["task10_production_package_sha256"] == "464465ef3dd435ed3a574bf8ded917095dcb76bb614416625b8c96db78c48903"
assert manifest["task10_main_dossiers_member_sha256"] == "954bd97aeb41b33669c99695b88a1715aa01a19bd697282f8e1b437be57de4d3"
assert manifest["task10_manifest_member_sha256"] == "f6736c59bc120b8ed8bb5bcaf9ea0d3fb65931cfc2a82e142295c33333500a20"
assert manifest["hypothesis_registry_sha256"] == hashlib.sha256(registry_bytes).hexdigest()
assert manifest["logical_output_filenames"] == list(TASK11_LOGICAL_FILENAMES)
assert manifest["hypothesis_unit"] == "PAIRWISE_ONLY"
assert manifest["hypothesis_cardinality"] == "EXACTLY_ONE_PER_CANONICAL_PAIR"
assert manifest["hypothesis_id_policy"] == "DETERMINISTIC_FROM_PAIR_KEY"
assert manifest["hypothesis_id_prefix"] == "TASK11_HYPOTHESIS__"
assert manifest["test_question_policy"] == "SINGLE_FIXED_TEMPLATE"
assert manifest["test_question_template_id"] == "TASK11_PAIRWISE_NEUTRAL_V1"
assert manifest["evidence_summary_policy"] == "COPY_LOCKED_TASK10_OBSERVATIONS"
assert manifest["cross_tf_evidence_policy"] == "COPY_LOCKED_TASK10_CROSS_TF"
assert manifest["main_pair_count"] == 78
assert manifest["hypothesis_count"] == 78
assert manifest["duration_control_eligible_count"] == 66
assert manifest["control_feature_non_applicable_count"] == 12
assert manifest["deterministic_context_pair_count"] == 4
assert manifest["logical_file_count"] == 2
assert all(manifest[field] is False for field in TASK11_FALSE_SCOPE_FIELDS)

for run_number in (1, 2):
    path = root / f"TASK11_PRODUCTION_RUN{run_number}.zip"
    with zipfile.ZipFile(path) as archive:
        assert archive.namelist() == sorted(TASK11_LOGICAL_FILENAMES)
        assert {
            name: archive.read(name) for name in archive.namelist()
        } == {
            name: (root / f"run{run_number}" / name).read_bytes()
            for name in TASK11_LOGICAL_FILENAMES
        }
        for info in archive.infolist():
            assert info.date_time == (1980, 1, 1, 0, 0, 0)
            assert info.create_system == 3
            assert info.external_attr >> 16 == 0o100644
            assert info.extra == b""

print("Task 11 production contract validation: PASS")
PY
```

Expected exact output: `Task 11 production contract validation: PASS`.

- [ ] **Step 6: Re-run Task 11, Task 10, Combined Audit, and full repository tests**

```bash
pytest -q \
  tests/test_task11_hypothesis_contract.py \
  tests/test_task11_hypothesis_io.py \
  tests/test_task11_hypothesis_registry.py \
  tests/test_task11_hypothesis_integration.py
pytest -q \
  tests/test_task10_interpretation_contract.py \
  tests/test_task10_interpretation_io.py \
  tests/test_task10_interpretation_reports.py \
  tests/test_task10_interpretation_integration.py
pytest -q \
  tests/test_combined_audit_contract.py \
  tests/test_combined_audit_stats.py \
  tests/test_combined_audit_deterministic.py \
  tests/test_combined_audit_reports.py \
  tests/test_combined_audit_io.py \
  tests/test_combined_audit_integration.py
pytest -q
```

Expected: every command exits 0 with zero failures/errors.

- [ ] **Step 7: Verify source immutability, scope, final ZIP SHA, and clean tracked/index state**

```bash
TASK11_TASK10_SHA_AFTER="$(sha256sum "$TASK11_TASK10_ZIP" | awk '{print $1}')"
test "$TASK11_TASK10_SHA_AFTER" = "$TASK11_TASK10_SHA_BEFORE"
test "$TASK11_TASK10_SHA_AFTER" = "464465ef3dd435ed3a574bf8ded917095dcb76bb614416625b8c96db78c48903"
TASK11_RUN1_REGISTRY_SHA256="$(sha256sum "$TASK11_RUN_ROOT/run1/TASK11_HYPOTHESIS_REGISTRY.json" | awk '{print $1}')"
TASK11_RUN2_REGISTRY_SHA256="$(sha256sum "$TASK11_RUN_ROOT/run2/TASK11_HYPOTHESIS_REGISTRY.json" | awk '{print $1}')"
TASK11_RUN1_MANIFEST_SHA256="$(sha256sum "$TASK11_RUN_ROOT/run1/TASK11_MANIFEST.json" | awk '{print $1}')"
TASK11_RUN2_MANIFEST_SHA256="$(sha256sum "$TASK11_RUN_ROOT/run2/TASK11_MANIFEST.json" | awk '{print $1}')"
TASK11_RUN1_ZIP_SHA256="$(sha256sum "$TASK11_RUN_ROOT/TASK11_PRODUCTION_RUN1.zip" | awk '{print $1}')"
TASK11_RUN2_ZIP_SHA256="$(sha256sum "$TASK11_RUN_ROOT/TASK11_PRODUCTION_RUN2.zip" | awk '{print $1}')"
test "$TASK11_RUN1_REGISTRY_SHA256" = "$TASK11_RUN2_REGISTRY_SHA256"
test "$TASK11_RUN1_MANIFEST_SHA256" = "$TASK11_RUN2_MANIFEST_SHA256"
test "$TASK11_RUN1_ZIP_SHA256" = "$TASK11_RUN2_ZIP_SHA256"
TASK11_FINAL_ZIP_SHA256="$TASK11_RUN1_ZIP_SHA256"
TASK11_FINAL_ZIP_SIZE="$(stat -c '%s' "$TASK11_RUN_ROOT/TASK11_PRODUCTION_RUN1.zip")"
export TASK11_RUN1_REGISTRY_SHA256 TASK11_RUN2_REGISTRY_SHA256
export TASK11_RUN1_MANIFEST_SHA256 TASK11_RUN2_MANIFEST_SHA256
export TASK11_RUN1_ZIP_SHA256 TASK11_RUN2_ZIP_SHA256
export TASK11_FINAL_ZIP_SHA256 TASK11_FINAL_ZIP_SIZE
git diff --quiet
git diff --cached --quiet
test -z "$(git status --porcelain=v1 --untracked-files=no)"
printf 'TASK11_RUN1_REGISTRY_SHA256=%s\n' "$TASK11_RUN1_REGISTRY_SHA256"
printf 'TASK11_RUN2_REGISTRY_SHA256=%s\n' "$TASK11_RUN2_REGISTRY_SHA256"
printf 'TASK11_RUN1_MANIFEST_SHA256=%s\n' "$TASK11_RUN1_MANIFEST_SHA256"
printf 'TASK11_RUN2_MANIFEST_SHA256=%s\n' "$TASK11_RUN2_MANIFEST_SHA256"
printf 'TASK11_RUN1_ZIP_SHA256=%s\n' "$TASK11_RUN1_ZIP_SHA256"
printf 'TASK11_RUN2_ZIP_SHA256=%s\n' "$TASK11_RUN2_ZIP_SHA256"
printf 'TASK11_FINAL_ZIP_SHA256=%s\n' "$TASK11_FINAL_ZIP_SHA256"
printf 'TASK11_FINAL_ZIP_SIZE=%s\n' "$TASK11_FINAL_ZIP_SIZE"
printf 'TASK11_RUN_ROOT=%s\n' "$TASK11_RUN_ROOT"
```

Expected: all checks exit 0; the paired registry, manifest, and ZIP hashes match; and the nine printed values identify both runs, the final byte-identical production ZIP, and the retained output root. Re-run Task 6 Steps 6–8 to reconfirm the exact implementation allowlist, protected paths, and static scope scan.

- [ ] **Step 8: Report production and stop**

Report implementation HEAD; Spec commit/blob; Lock Record commit/blob; Task 10 input path/SHA; Run 1 and Run 2 output paths; both logical-file SHA-256 values; both ZIP SHA-256 values; byte-identity results; `78/78/66/12/4/2` counts; exact manifest provenance/scope flags; Task 11/Task 10/Combined Audit/full pytest results; changed-path allowlist; protected-path confirmations; tracked/index cleanliness; final ZIP path/SHA/size.

Create no production commit. Stop. Do not proceed to Controlled Ablation Design/execution, Causal Replay, Score, Threshold, Ranking, Outcome, Prediction, Optimization, Feature Removal, or Feature Selection.

---

## Locked Spec Coverage Map

| Locked Spec requirement | Plan implementation / validation |
|---|---|
| Purpose and no-answer boundary (Sections 1, 4, 19) | Global Constraints; Tasks 3, 6 Step 8, Task 7 Step 8 |
| Source-of-truth and no inference (Section 2) | Canonical Input Binding; Task 2 hash-first loader; Task 3 exact source copies |
| Task 10 package/implementation/member provenance (Section 3) | Task 1 constants; Task 2 Steps 2–7; Task 7 Steps 1–2 and 7 |
| Pairwise-only universe and exactly 78 records (Section 5) | Task 1 pair contract; Task 2 source validation; Task 3 Steps 1–6; Task 7 Step 5 |
| Deterministic reversible ID (Section 6) | Task 1 prefix; Task 3 Steps 1, 3, 5; Task 7 Step 5 |
| Single fixed neutral question (Section 7) | Task 1 template; Task 3 Steps 1, 3–5; Task 7 Step 5 |
| Closed record schema and JSON types (Section 8) | Task 1 schema; Task 3 Steps 4–5; Task 7 Step 5 |
| Exact raw/controlled/cross-TF/evidence-summary copies (Section 9) | Task 2 nested source schemas; Task 3 Steps 3–5; Task 7 Step 5 |
| 66 eligible / 12 control-feature non-applicable and no duplicate `delta_rho_by_tf` (Section 9.3) | Tasks 1–3; Task 4 count gate; Task 7 Step 5 |
| Four deterministic-context pairs are context only (Section 9.5) | Task 1 mapping; Task 2 validation; Task 3 copy/count tests; Task 7 Step 5 |
| Closed source locators (Section 10) | Task 1 locator schema; Task 2 locator validation; Task 3 exact mapping tests; Task 7 Step 5 |
| Intentionally omitted Task 10 fields (Section 11) | Task 3 Steps 4–5; Task 7 Step 5 |
| Prohibited fields/semantics (Section 12) | Global Constraints; Task 1 false-scope/prohibited schema tests; Task 3 prohibition tests; Task 6 AST scan; Task 7 Step 8 |
| Two logical outputs and required archive (Section 13) | Task 1 filenames; Task 4 writer/repeatability; Task 7 Steps 3–5 |
| Closed manifest and exact provenance/count/scope values (Section 13.2) | Task 1 manifest contract; Task 4 Steps 4–5; Task 5 guard SHA; Task 7 Step 5 |
| Source-order preservation and deterministic serialization/ZIP (Section 14) | Task 2 canonical order; Task 3 order preservation; Task 4 deterministic tests; Task 7 Steps 4–5 |
| Package/Main Dossier/Hypothesis/output validation (Section 15) | Tasks 1–5 test cycles; Task 7 Steps 2, 4–5 |
| Fail-closed before output and contextual errors (Section 16) | Task 2 invalid-input tests; Task 3 validator; Task 4 no-output tests; Task 5 guard-first tests |
| Clean committed production provenance and no public overrides (Section 17) | Task 5 Steps 1–7; Task 7 Step 1 |
| Research-only non-regression/scope isolation (Section 18) | Planned File Structure; Task 6 Steps 3–8; Task 7 Steps 6–7 |
| Design-phase lock and immutable approved bytes (Section 20 plus Lock Record) | Global Constraints; Task 5 ancestry/blob guard; Task 6 Step 7 |

## Plan Authoring Self-Review

- [x] Every substantive locked Spec section maps to at least one implementation task and one validation or production gate.
- [x] Every new function signature, field name, filename, count, hash, source locator, return type, and call direction is consistent across tasks.
- [x] Every behavioral implementation task begins with a failing test, states the expected failure, adds the minimal implementation, runs an exact passing command, and ends with an independently reviewable commit.
- [x] Production is separated behind an explicit later human authorization gate.
- [x] The Plan introduces no research statistic, evidence interpretation, directional test, outcome, horizon, rank, score, threshold, feature decision, Ablation execution, or Causal Replay.
- [x] Planned implementation paths are exactly four new `research/task11_*`/runner files and four new Task 11 test files.
- [x] `src/`, `evidence/`, Combined Audit, Task 10, locked Spec, Lock Record, and Plan paths are protected by exact diff/hash gates.
- [x] Public loader/runner/CLI cannot override canonical SHA, loader, bundle, template, ID, ordering, counts, implementation SHA, or scope.
- [x] The required archive is never treated as optional.
- [x] No unresolved design marker, unbound interface, deferred branch, or unspecified validation remains.

## Plan Review Gate

This Plan requires human review before any implementation task is authorized. After Plan approval, execution must start from the committed Plan HEAD, use the execution-baseline command above, and follow Tasks 1–6 in order. Task 7 remains separately authorization-gated even after implementation verification passes.
