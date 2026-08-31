# Task 10 Dependency / Redundancy Interpretation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a research-only interpretation pipeline that reads the Final-Locked Task 9 Combined Audit Evidence Package and produces exactly 78 non-decision-making Main Relationship Dossiers, a separate supplementary evidence layer, exactly 13 Feature Dossiers, an explicitly untested future-Ablation hypothesis artifact, and a provenance manifest without recomputing Task 9 statistics or changing any locked Engine code.

**Architecture:** Add a small Task-10-only subsystem under `research/`. The subsystem first validates the immutable Task 9 Evidence ZIP by exact SHA-256 and exact artifact schemas/counts, then joins already-computed Task 9 Main/Partial/Cross-TF/Supplementary rows by canonical pair keys. It emits deterministic JSON/CSV artifacts only; no new association statistic, threshold, ranking, causal model, feature-selection decision, or raw cross-TF pooling is permitted.

**Tech Stack:** Python 3.12, pytest, Python standard library only (`argparse`, `csv`, `hashlib`, `io`, `itertools`, `json`, `math`, `pathlib`, `re`, `subprocess`, `zipfile`, `dataclasses`, `collections.abc`). Reuse locked Task 9 constants/schemas from `research.combined_audit_contract` and `research.combined_audit_io`; do not import `src/` Engine modules.

**Spec:** `docs/superpowers/specs/2026-08-31-task10-dependency-redundancy-interpretation-design.md`

**Locked Spec Commit:** `dfc91e3c75a12a3dfa008c17453b622f03ed41ad`

## Global Constraints

- Task 9 Evidence Package is immutable: `GOLD_COMBINED_LEG_FEATURE_AUDIT_PACKAGE.zip`.
- Canonical Task 9 Evidence Package SHA-256 is exactly `968f4826858a0bbb8254218711f4ad3e3487370ca8d0f288133ee36f7a4fa40d`.
- Canonical upstream Activity input SHA-256 remains exactly `1e9f13fd88fc1e8e0e66d801be8c15d726639eaea25e53fef7c3bb88bfd05192`.
- Task 9 audit-code commit is exactly `1c40cd3d3507c473fd07ea25c010d386be8a0043` and is remotely resolvable through the provenance ref.
- Task 9 registration commit is exactly `78e54fb50ce82a0cba7f91f40a6451e82996008d`.
- Main feature universe is exactly the locked 13 `MAIN_FEATURES`; no fourteenth main feature.
- Main Relationship Dossiers are exactly `13 choose 2 = 78` unordered canonical pairs.
- Exactly 66 main pairs are Partial/`delta_rho` eligible.
- Exactly 12 main pairs contain `active_bar_count` and must use the exact structural state `NOT_APPLICABLE_CONTROL_FEATURE` for Partial and `delta_rho`.
- `NOT_APPLICABLE_CONTROL_FEATURE` is not zero, missing data, statistical undefinedness, failure, insufficient observations, or constant input.
- Task 10 must preserve the distinction between Main pairwise `rho_raw` and triple-complete `rho_raw_for_delta`.
- Task 10 must not recompute Raw Spearman, Partial Spearman, or `delta_rho`; it reads the Final-Locked Task 9 values.
- `rho_range` is authoritative from Task 9 and is defined only from defined raw TF values.
- Every Main Dossier must include `n_defined_tf` and satisfy `n_defined_tf + n_undefined_tf == 4`.
- Undefined TF values are never converted to zero and never participate in `rho_min`, `rho_max`, or `rho_range`.
- The 120 Bull/Bear stratified rows per direction per TF remain Supplementary Evidence only.
- Any pair containing `close_ols_slope`, `gross_upper_shadow`, or `gross_lower_shadow` must remain outside the 78 Main Relationship Dossiers.
- Deterministic Identity evidence precedes statistical evidence; Task 10 invents no new deterministic identity.
- No Ranking, Cutoff, qualitative strength/stability/redundancy label, feature importance, Feature Weight, Keep/Drop recommendation, Score, Threshold, Outcome, Prediction, Optimization, PCA, Mutual Information, Clustering, Ablation execution, Causal Replay, or causal interpretation.
- Future Ablation hypotheses are optional, unranked, explicitly untested, and may not authorize Ablation.
- No raw cross-TF pooling.
- Do not modify `src/price_action_ai_swing_v1_locked.py`, `src/price_action_ai_leg_v0.py`, any locked Swing/Leg formula, any Task 9 report, or `evidence/GOLD_COMBINED_LEG_FEATURE_AUDIT_PACKAGE.zip`.
- Task 10 implementation must read Task 9 evidence; it must not regenerate Leg rows or import Swing/Leg Engine code.
- **Task 10 implementation and Production execution remain NOT AUTHORIZED until a separate explicit human approval after this Plan is reviewed and locked.**

## Planned File Structure

- Create `research/task10_interpretation_contract.py` — canonical pair ordering, frozen counts, physical output schemas/names, provenance constants, non-applicability state, and text-safety rules.
- Create `research/task10_interpretation_io.py` — exact SHA-first Task 9 Evidence ZIP loader, member/schema/count/pair-set/provenance validation, typed CSV parsing, deterministic writers, manifest construction, and deterministic output ZIP creation.
- Create `research/task10_interpretation_reports.py` — Main Relationship Dossier construction, exact `n_defined_tf` validation, neutral observations, Supplementary Evidence projection, Feature Dossiers, and empty-by-default future-Ablation hypotheses.
- Create `research/run_task10_dependency_interpretation.py` — thin CLI orchestration only.
- Create `tests/test_task10_interpretation_contract.py` — exact 78/66/12 contracts and output schemas.
- Create `tests/test_task10_interpretation_io.py` — synthetic Task 9 Evidence ZIP, SHA/member/schema/provenance/count/pair-set gates.
- Create `tests/test_task10_interpretation_reports.py` — dossier joins, non-applicable control behavior, defined-TF/range rules, supplementary separation, observations, 13 Feature Dossiers.
- Create `tests/test_task10_interpretation_integration.py` — synthetic end-to-end deterministic output and forbidden-scope checks.

## Physical Task 10 Outputs

Execution, when separately authorized, writes exactly these logical files:

1. `TASK10_MAIN_RELATIONSHIP_DOSSIERS.json` — JSON list of exactly 78 primary main-pair dossiers.
2. `TASK10_SUPPLEMENTARY_EVIDENCE.csv` — exactly 960 rows = 4 TF × 2 directions × 120 Task 9 supplementary rows, with TF/direction/source traceability.
3. `TASK10_FEATURE_DOSSIERS.json` — JSON list of exactly 13 feature dossiers.
4. `TASK10_FUTURE_ABLATION_HYPOTHESES.json` — JSON list; initial automated implementation emits `[]` because the locked Spec permits zero or more hypotheses and no unapproved hypothesis-selection rule may be invented.
5. `TASK10_MANIFEST.json` — provenance, counts, implementation commit, locked Spec commit, and explicit scope flags.

A deterministic archive may package only those five logical files as:

```text
TASK10_DEPENDENCY_REDUNDANCY_INTERPRETATION_PACKAGE.zip
```

The archive is a Task 10 output only. It must not replace or mutate the Task 9 Evidence ZIP.

---

### Task 1: Freeze Task 10 contract, canonical pair sets, and physical schemas

**Files:**
- Create: `research/task10_interpretation_contract.py`
- Create: `tests/test_task10_interpretation_contract.py`

**Interfaces:**
- Consumes locked constants from `research.combined_audit_contract`: `MAIN_FEATURES`, `RAW_DIRECTION_SENSITIVE`, `TIMEFRAMES`, `DIRECTIONS`.
- Produces `TASK9_EVIDENCE_PACKAGE_FILENAME: str`.
- Produces `TASK9_EVIDENCE_SHA256: str`.
- Produces `TASK9_ACTIVITY_INPUT_SHA256: str`.
- Produces `TASK9_AUDIT_CODE_COMMIT: str`.
- Produces `TASK9_REGISTRATION_COMMIT: str`.
- Produces `TASK10_SPEC_COMMIT: str`.
- Produces `CONTROL_FEATURE = "active_bar_count"`.
- Produces `CONTROL_NOT_APPLICABLE = "NOT_APPLICABLE_CONTROL_FEATURE"`.
- Produces `MAIN_PAIR_KEYS`, `PARTIAL_PAIR_KEYS`, `CONTROL_PAIR_KEYS`, and `SUPPLEMENTARY_PAIR_KEYS` as canonical ordered tuples.
- Produces output filenames and exact output field schemas.
- Produces `pair_key(feature_x: str, feature_y: str) -> str` and `canonical_pair(feature_x: str, feature_y: str) -> tuple[str, str]`.
- Produces `validate_observation_text(text: str) -> None` for prohibited qualitative decision labels only.

- [ ] **Step 1: Write failing count/order tests**

```python
from research.task10_interpretation_contract import (
    CONTROL_FEATURE,
    CONTROL_NOT_APPLICABLE,
    CONTROL_PAIR_KEYS,
    MAIN_PAIR_KEYS,
    PARTIAL_PAIR_KEYS,
    SUPPLEMENTARY_PAIR_KEYS,
    TASK9_EVIDENCE_SHA256,
)


def test_task10_pair_contract_is_exact():
    assert CONTROL_FEATURE == "active_bar_count"
    assert CONTROL_NOT_APPLICABLE == "NOT_APPLICABLE_CONTROL_FEATURE"
    assert len(MAIN_PAIR_KEYS) == 78
    assert len(PARTIAL_PAIR_KEYS) == 66
    assert len(CONTROL_PAIR_KEYS) == 12
    assert len(SUPPLEMENTARY_PAIR_KEYS) == 120
    assert set(PARTIAL_PAIR_KEYS).isdisjoint(CONTROL_PAIR_KEYS)
    assert set(PARTIAL_PAIR_KEYS) | set(CONTROL_PAIR_KEYS) == set(MAIN_PAIR_KEYS)


def test_control_pairs_all_contain_active_bar_count():
    assert all("active_bar_count" in pair for pair in CONTROL_PAIR_KEYS)


def test_locked_task9_evidence_sha_is_exact():
    assert TASK9_EVIDENCE_SHA256 == (
        "968f4826858a0bbb8254218711f4ad3e3487370ca8d0f288133ee36f7a4fa40d"
    )
```

- [ ] **Step 2: Run the contract test to verify RED**

Run:
```bash
pytest -q tests/test_task10_interpretation_contract.py
```
Expected: FAIL because `research/task10_interpretation_contract.py` does not exist.

- [ ] **Step 3: Implement exact constants and canonical pair order**

```python
from itertools import combinations

from research.combined_audit_contract import (
    DIRECTIONS,
    MAIN_FEATURES,
    RAW_DIRECTION_SENSITIVE,
    TIMEFRAMES,
)

TASK9_EVIDENCE_PACKAGE_FILENAME = "GOLD_COMBINED_LEG_FEATURE_AUDIT_PACKAGE.zip"
TASK9_EVIDENCE_SHA256 = "968f4826858a0bbb8254218711f4ad3e3487370ca8d0f288133ee36f7a4fa40d"
TASK9_ACTIVITY_INPUT_SHA256 = "1e9f13fd88fc1e8e0e66d801be8c15d726639eaea25e53fef7c3bb88bfd05192"
TASK9_AUDIT_CODE_COMMIT = "1c40cd3d3507c473fd07ea25c010d386be8a0043"
TASK9_REGISTRATION_COMMIT = "78e54fb50ce82a0cba7f91f40a6451e82996008d"
TASK10_SPEC_COMMIT = "dfc91e3c75a12a3dfa008c17453b622f03ed41ad"

CONTROL_FEATURE = "active_bar_count"
CONTROL_NOT_APPLICABLE = "NOT_APPLICABLE_CONTROL_FEATURE"

MAIN_PAIR_KEYS = tuple(combinations(MAIN_FEATURES, 2))
PARTIAL_PAIR_KEYS = tuple(
    pair for pair in MAIN_PAIR_KEYS if CONTROL_FEATURE not in pair
)
CONTROL_PAIR_KEYS = tuple(
    pair for pair in MAIN_PAIR_KEYS if CONTROL_FEATURE in pair
)
SUPPLEMENTARY_FEATURES = MAIN_FEATURES + RAW_DIRECTION_SENSITIVE
SUPPLEMENTARY_PAIR_KEYS = tuple(combinations(SUPPLEMENTARY_FEATURES, 2))

assert len(MAIN_PAIR_KEYS) == 78
assert len(PARTIAL_PAIR_KEYS) == 66
assert len(CONTROL_PAIR_KEYS) == 12
assert len(SUPPLEMENTARY_PAIR_KEYS) == 120
```

- [ ] **Step 4: Add stable pair-key helpers**

```python
_FEATURE_ORDER = {
    feature: index
    for index, feature in enumerate(MAIN_FEATURES + RAW_DIRECTION_SENSITIVE)
}


def canonical_pair(feature_x: str, feature_y: str) -> tuple[str, str]:
    if feature_x == feature_y:
        raise ValueError("pair requires two distinct features")
    try:
        ordered = sorted((feature_x, feature_y), key=_FEATURE_ORDER.__getitem__)
    except KeyError as exc:
        raise ValueError(f"unknown Task 10 feature: {exc.args[0]}") from exc
    return ordered[0], ordered[1]


def pair_key(feature_x: str, feature_y: str) -> str:
    x, y = canonical_pair(feature_x, feature_y)
    return f"{x}__{y}"
```

- [ ] **Step 5: Freeze physical output names and Supplementary CSV fields**

```python
MAIN_DOSSIERS_FILENAME = "TASK10_MAIN_RELATIONSHIP_DOSSIERS.json"
SUPPLEMENTARY_FILENAME = "TASK10_SUPPLEMENTARY_EVIDENCE.csv"
FEATURE_DOSSIERS_FILENAME = "TASK10_FEATURE_DOSSIERS.json"
HYPOTHESES_FILENAME = "TASK10_FUTURE_ABLATION_HYPOTHESES.json"
MANIFEST_FILENAME = "TASK10_MANIFEST.json"
OUTPUT_ZIP_FILENAME = "TASK10_DEPENDENCY_REDUNDANCY_INTERPRETATION_PACKAGE.zip"

TASK10_LOGICAL_FILENAMES = (
    MAIN_DOSSIERS_FILENAME,
    SUPPLEMENTARY_FILENAME,
    FEATURE_DOSSIERS_FILENAME,
    HYPOTHESES_FILENAME,
    MANIFEST_FILENAME,
)

SUPPLEMENTARY_OUTPUT_FIELDS = (
    "timeframe",
    "direction",
    "source_artifact",
    "pair_key",
    "feature_x",
    "feature_y",
    "contains_raw_direction_sensitive",
    "is_main_pair",
    "n_total",
    "n_valid_pairwise",
    "n_missing_x",
    "n_missing_y",
    "rho_raw",
    "raw_status",
    "rho_raw_for_delta",
    "rho_duration_controlled",
    "delta_rho",
    "n_valid_triple",
    "controlled_status",
    "evidence_scope",
)
```

- [ ] **Step 6: Add observation-text safety tests and implementation**

```python
import pytest

from research.task10_interpretation_contract import validate_observation_text


@pytest.mark.parametrize(
    "text",
    [
        "Feature X is STRONG",
        "feature x is weak",
        "this is redundant",
        "KEEP feature x",
        "drop feature y",
        "near_duplicate candidate",
    ],
)
def test_observation_text_rejects_decision_language(text):
    with pytest.raises(ValueError):
        validate_observation_text(text)


def test_observation_text_allows_exact_numeric_description():
    validate_observation_text(
        "M15 raw rho=-0.21; controlled rho=-0.08; delta_rho=0.13"
    )
```

Implement with word-boundary, case-insensitive matching over this exact frozen set:

```python
import re

_PROHIBITED_QUALITATIVE_TERMS = (
    "STRONG",
    "WEAK",
    "STABLE",
    "UNSTABLE",
    "REDUNDANT",
    "ORTHOGONAL",
    "NEAR_DUPLICATE",
    "KEEP",
    "DROP",
    "BEST",
    "WORST",
    "IMPORTANT",
    "UNIMPORTANT",
)
_PROHIBITED_RE = re.compile(
    r"\b(?:" + "|".join(map(re.escape, _PROHIBITED_QUALITATIVE_TERMS)) + r")\b",
    re.IGNORECASE,
)


def validate_observation_text(text: str) -> None:
    match = _PROHIBITED_RE.search(text)
    if match:
        raise ValueError(
            f"Task 10 observation contains prohibited qualitative term: {match.group(0)!r}"
        )
```

- [ ] **Step 7: Run Task 1 tests to GREEN**

Run:
```bash
pytest -q tests/test_task10_interpretation_contract.py
```
Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add research/task10_interpretation_contract.py tests/test_task10_interpretation_contract.py
git commit -m "test: lock Task 10 interpretation contract"
```

---

### Task 2: Load and fail-closed validate the immutable Task 9 Evidence ZIP

**Files:**
- Create: `research/task10_interpretation_io.py`
- Create: `tests/test_task10_interpretation_io.py`

**Interfaces:**
- Consumes Task 9 report schemas from `research.combined_audit_io`: `FEATURE_ROLE_COLUMNS`, `DETERMINISTIC_FIELDS`, `MAIN_FIELDS`, `PARTIAL_FIELDS`, `SUPPLEMENTARY_FIELDS`, `CROSS_TF_FIELDS`, and `combined_audit_report_filenames()`.
- Produces frozen dataclass `Task9EvidenceBundle`.
- Produces `sha256_bytes(data: bytes) -> str`.
- Produces `load_task9_evidence_package(path: Path) -> Task9EvidenceBundle`.
- The SHA check happens before `zipfile.ZipFile` is opened.
- No dependency on `src/`.

- [ ] **Step 1: Write RED test proving SHA is checked before ZIP parsing**

```python
from pathlib import Path

import pytest

from research.task10_interpretation_io import load_task9_evidence_package


def test_wrong_sha_stops_before_zip_processing(tmp_path: Path):
    package = tmp_path / "wrong.zip"
    package.write_bytes(b"not-even-a-zip")

    with pytest.raises(ValueError, match="Task 9 Evidence SHA-256 mismatch"):
        load_task9_evidence_package(package)
```

- [ ] **Step 2: Run the single test to verify RED**

Run:
```bash
pytest -q tests/test_task10_interpretation_io.py::test_wrong_sha_stops_before_zip_processing
```
Expected: FAIL because the module does not exist.

- [ ] **Step 3: Implement SHA-first package shell and immutable bundle type**

```python
from __future__ import annotations

import csv
import hashlib
import io
import json
import zipfile
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType

from research.combined_audit_contract import DIRECTIONS, MAIN_FEATURES, TIMEFRAMES
from research.combined_audit_io import (
    COMBINED_MANIFEST_FILENAME,
    CROSS_TF_FIELDS,
    CROSS_TF_FILENAME,
    DETERMINISTIC_FIELDS,
    DETERMINISTIC_FILENAME,
    FEATURE_ROLE_COLUMNS,
    FEATURE_ROLE_FILENAME,
    MAIN_FIELDS,
    PARTIAL_FIELDS,
    SUPPLEMENTARY_FIELDS,
    combined_audit_report_filenames,
)
from research.task10_interpretation_contract import (
    MAIN_PAIR_KEYS,
    PARTIAL_PAIR_KEYS,
    SUPPLEMENTARY_PAIR_KEYS,
    TASK9_ACTIVITY_INPUT_SHA256,
    TASK9_AUDIT_CODE_COMMIT,
    TASK9_EVIDENCE_SHA256,
)


@dataclass(frozen=True, slots=True)
class Task9EvidenceBundle:
    evidence_zip_sha256: str
    task9_manifest: Mapping[str, object]
    feature_role_rows: tuple[Mapping[str, object], ...]
    deterministic_rows: tuple[Mapping[str, object], ...]
    main_by_tf: Mapping[str, tuple[Mapping[str, object], ...]]
    partial_by_tf: Mapping[str, tuple[Mapping[str, object], ...]]
    supplementary_by_tf_direction: Mapping[
        tuple[str, str], tuple[Mapping[str, object], ...]
    ]
    cross_tf_rows: tuple[Mapping[str, object], ...]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()
```

The first lines of `load_task9_evidence_package()` must be:

```python
def load_task9_evidence_package(path: Path) -> Task9EvidenceBundle:
    package_bytes = Path(path).read_bytes()
    actual_sha = sha256_bytes(package_bytes)
    if actual_sha != TASK9_EVIDENCE_SHA256:
        raise ValueError(
            "Task 9 Evidence SHA-256 mismatch: "
            f"expected {TASK9_EVIDENCE_SHA256}, got {actual_sha}"
        )

    try:
        archive_context = zipfile.ZipFile(io.BytesIO(package_bytes))
    except zipfile.BadZipFile as exc:
        raise ValueError(f"Task 9 Evidence is not a valid ZIP: {exc}") from exc
```

- [ ] **Step 4: Add exact member-set, duplicate-member, and path-safety gates**

Use the exact Task 9 logical member set:

```python
expected_members = set(combined_audit_report_filenames())
```

Reject:
- missing member;
- unexpected member;
- duplicate filename;
- absolute path;
- `..`, `.`, blank path segment, backslash, or directory member.

Add tests that synthesize a structurally valid ZIP and mutate one property at a time. Because production SHA is fixed, expose a test-only helper with explicit expected SHA injection only at the private function boundary:

```python
def _load_task9_evidence_bytes(
    package_bytes: bytes,
    *,
    expected_sha256: str,
) -> Task9EvidenceBundle:
    ...
```

Production `load_task9_evidence_package()` must always call it with `TASK9_EVIDENCE_SHA256`; the CLI must expose no SHA override.

- [ ] **Step 5: Implement strict CSV header parsing while preserving Task 9 values**

Use exact headers from Task 9. Numeric output cells parse as finite `float`/`int`; blank numeric cells become `None`; statuses and `sign_agreement_modal_signs` remain text. Do not reinterpret blank as zero.

The parser must reject `NaN`, `Inf`, `-Inf`, malformed numeric text, duplicate columns, missing required columns, and duplicate pair rows.

Add these helpers:

```python
def _read_csv_member(
    archive: zipfile.ZipFile,
    member: str,
    expected_fields: tuple[str, ...],
) -> list[dict[str, object]]:
    ...


def _index_unique_pairs(
    rows: list[dict[str, object]],
    *,
    source: str,
) -> dict[tuple[str, str], dict[str, object]]:
    ...
```

- [ ] **Step 6: Add exact row-count and pair-set gates**

Tests must require:

```python
assert len(feature_role_rows) == 47
assert len(deterministic_rows) == 44
assert all(len(main_by_tf[tf]) == 78 for tf in TIMEFRAMES)
assert all(len(partial_by_tf[tf]) == 66 for tf in TIMEFRAMES)
assert all(
    len(supplementary_by_tf_direction[(tf, direction)]) == 120
    for tf in TIMEFRAMES
    for direction in DIRECTIONS
)
assert len(cross_tf_rows) == 78
```

And exact pair universes:

```python
assert set(main_pair_index) == set(MAIN_PAIR_KEYS)
assert set(partial_pair_index) == set(PARTIAL_PAIR_KEYS)
assert set(supplementary_pair_index) == set(SUPPLEMENTARY_PAIR_KEYS)
assert set(cross_tf_pair_index) == set(MAIN_PAIR_KEYS)
```

Reject any Main/Cross-TF row containing a raw direction-sensitive feature.

- [ ] **Step 7: Validate the Task 9 Combined Audit manifest provenance**

Require at least:

```python
if manifest["analysis_feature_count"] != 13:
    raise ValueError("Task 9 manifest analysis_feature_count must be 13")
if manifest["control_variable"] != "active_bar_count":
    raise ValueError("Task 9 manifest control_variable mismatch")
if manifest["input_zip_sha256"] != TASK9_ACTIVITY_INPUT_SHA256:
    raise ValueError("Task 9 manifest upstream Activity SHA mismatch")
if manifest["audit_code_commit"] != TASK9_AUDIT_CODE_COMMIT:
    raise ValueError("Task 9 manifest audit-code commit mismatch")
if manifest["raw_cross_tf_pooling"] is not False:
    raise ValueError("Task 9 manifest reports raw cross-TF pooling")
if set(manifest["report_filenames"]) != set(combined_audit_report_filenames()):
    raise ValueError("Task 9 manifest report_filenames mismatch")
```

- [ ] **Step 8: Run Task 2 tests to GREEN**

Run:
```bash
pytest -q tests/test_task10_interpretation_io.py
```
Expected: PASS.

- [ ] **Step 9: Commit**

```bash
git add research/task10_interpretation_io.py tests/test_task10_interpretation_io.py
git commit -m "feat: validate locked Task 9 interpretation input"
```

---

### Task 3: Build exactly 78 Main Relationship Dossiers without new statistics

**Files:**
- Create: `research/task10_interpretation_reports.py`
- Create: `tests/test_task10_interpretation_reports.py`

**Interfaces:**
- Consumes `Task9EvidenceBundle`.
- Produces `build_main_relationship_dossiers(bundle) -> list[dict[str, object]]`.
- Produces `build_neutral_observations(dossier) -> list[str]`.
- Every dossier is joined by canonical pair key, never row position.
- No call to `spearman_pairwise()` or `partial_spearman_duration()` is permitted in Task 10.

- [ ] **Step 1: Write RED test for 78/66/12 dossier contract**

Using a synthetic valid `Task9EvidenceBundle`, assert:

```python
from research.task10_interpretation_contract import CONTROL_NOT_APPLICABLE
from research.task10_interpretation_reports import build_main_relationship_dossiers


def test_main_dossiers_are_exactly_78_with_66_eligible_and_12_control_pairs(bundle):
    dossiers = build_main_relationship_dossiers(bundle)

    assert len(dossiers) == 78
    assert sum(d["partial_applicability"] == "ELIGIBLE" for d in dossiers) == 66
    assert sum(
        d["partial_applicability"] == CONTROL_NOT_APPLICABLE
        for d in dossiers
    ) == 12
```

- [ ] **Step 2: Verify RED**

Run:
```bash
pytest -q tests/test_task10_interpretation_reports.py::test_main_dossiers_are_exactly_78_with_66_eligible_and_12_control_pairs
```
Expected: FAIL because the report module does not exist.

- [ ] **Step 3: Implement pair-index joins in frozen main order**

Start with:

```python
from research.combined_audit_contract import DETERMINISTIC_REGISTRY, MAIN_FEATURES, TIMEFRAMES
from research.task10_interpretation_contract import (
    CONTROL_FEATURE,
    CONTROL_NOT_APPLICABLE,
    MAIN_PAIR_KEYS,
    pair_key,
    validate_observation_text,
)


def _pair_index(rows):
    return {
        (row["feature_x"], row["feature_y"]): row
        for row in rows
    }
```

The outer loop must be exactly:

```python
for feature_x, feature_y in MAIN_PAIR_KEYS:
    ...
```

Never sort by observed correlation magnitude or sample size.

- [ ] **Step 4: Preserve raw and controlled evidence with explicit control non-applicability**

For each dossier, construct:

```python
{
    "pair_key": pair_key(feature_x, feature_y),
    "feature_x": feature_x,
    "feature_y": feature_y,
    "partial_applicability": (
        CONTROL_NOT_APPLICABLE
        if CONTROL_FEATURE in (feature_x, feature_y)
        else "ELIGIBLE"
    ),
    "raw_by_tf": {...},
    "partial_by_tf": {...},
    "cross_tf": {...},
    "deterministic_context": {...},
    "supplementary_same_pair_by_tf_direction": {...},
    "observations": [],
}
```

For a control-feature pair, every TF must have:

```python
{
    "rho_raw_for_delta": None,
    "rho_duration_controlled": None,
    "delta_rho": None,
    "n_valid_triple": None,
    "status": CONTROL_NOT_APPLICABLE,
}
```

No Task 9 Partial row may exist for those 12 pairs; treat existence as a blocker.

For the 66 eligible pairs, copy the Task 9 Partial row exactly by pair key and TF.

- [ ] **Step 5: Enforce exact `n_defined_tf` and authoritative Task 9 `rho_range` semantics**

For each Task 9 Cross-TF row:

```python
raw_values = [cross_row[f"rho_{tf}"] for tf in TIMEFRAMES]
reconstructed_defined = [value for value in raw_values if value is not None]
n_defined_tf = len(reconstructed_defined)

if n_defined_tf + cross_row["n_undefined_tf"] != 4:
    raise ValueError("cross-TF defined/undefined count mismatch")

if n_defined_tf == 0:
    if any(cross_row[name] is not None for name in ("rho_min", "rho_max", "rho_range")):
        raise ValueError("undefined cross-TF relationship has fabricated range")
else:
    expected_min = min(reconstructed_defined)
    expected_max = max(reconstructed_defined)
    expected_range = expected_max - expected_min
    if cross_row["rho_min"] != expected_min:
        raise ValueError("Task 9 rho_min reconstruction mismatch")
    if cross_row["rho_max"] != expected_max:
        raise ValueError("Task 9 rho_max reconstruction mismatch")
    if cross_row["rho_range"] != expected_range:
        raise ValueError("Task 9 rho_range reconstruction mismatch")
```

Then add, without changing Task 9 fields:

```python
cross_tf = dict(cross_row)
cross_tf["n_defined_tf"] = n_defined_tf
```

Tests must include:
- 4 defined TFs;
- 3 defined + 1 undefined;
- exactly 1 defined TF where `rho_range == 0` and `n_defined_tf == 1`;
- 0 defined TFs where min/max/range are all `None`;
- failure if an undefined TF is represented as zero.

- [ ] **Step 6: Attach deterministic context without inventing a new identity**

Parse the Task 9 deterministic report and `DETERMINISTIC_REGISTRY` only as context. Store:

```python
{
    "task9_relation_ids_referencing_feature_x": [...],
    "task9_relation_ids_referencing_feature_y": [...],
    "shared_task9_relation_ids": [...],
    "precedence_rule": "DETERMINISTIC_IDENTITY_PRECEDES_STATISTICAL_RESULT",
}
```

Do not emit `direct_deterministic_dependency=True` unless the locked Task 9 registry itself explicitly defines that exact two-main-feature identity. The initial implementation should not infer a new two-feature deterministic relation from multi-component identities.

- [ ] **Step 7: Add neutral descriptive observations using exact values only**

Every dossier must contain a deterministic-order list of observations. Use exact-value statements such as:

```python
observations = [
    (
        "RAW_SIGN_COUNTS "
        f"positive={cross['n_positive_tf']} "
        f"negative={cross['n_negative_tf']} "
        f"zero={cross['n_zero_tf']} "
        f"undefined={cross['n_undefined_tf']}"
    ),
    (
        "RAW_DEFINED_TF "
        f"n_defined_tf={cross['n_defined_tf']} "
        f"rho_min={cross['rho_min']} "
        f"rho_max={cross['rho_max']} "
        f"rho_range={cross['rho_range']}"
    ),
]
```

For each TF append either:

```text
M5 RAW rho=<value> status=<status> n_valid_pairwise=<n>
```

and, for eligible pairs:

```text
M5 CONTROLLED rho_raw_for_delta=<a> rho_duration_controlled=<b> delta_rho=<c> status=<status> n_valid_triple=<n>
```

or, for control-feature pairs:

```text
M5 CONTROLLED NOT_APPLICABLE_CONTROL_FEATURE
```

Run every generated observation through `validate_observation_text()`.

Do not use words such as stronger, weaker, stable, redundant, independent, important, useful, better, worse, keep, drop, or near-duplicate.

- [ ] **Step 8: Verify no Task 10 code invokes Task 9 statistical primitives**

Add a static test:

```python
from pathlib import Path


def test_task10_reports_do_not_recompute_task9_statistics():
    text = Path("research/task10_interpretation_reports.py").read_text(encoding="utf-8")
    assert "spearman_pairwise(" not in text
    assert "partial_spearman_duration(" not in text
```

- [ ] **Step 9: Run Task 3 tests to GREEN**

Run:
```bash
pytest -q tests/test_task10_interpretation_reports.py
```
Expected: PASS.

- [ ] **Step 10: Commit**

```bash
git add research/task10_interpretation_reports.py tests/test_task10_interpretation_reports.py
git commit -m "feat: build Task 10 main relationship dossiers"
```

---

### Task 4: Build the separate 960-row Supplementary layer and exactly 13 Feature Dossiers

**Files:**
- Modify: `research/task10_interpretation_reports.py`
- Modify: `tests/test_task10_interpretation_reports.py`

**Interfaces:**
- Produces `build_supplementary_evidence(bundle) -> list[dict[str, object]]`.
- Produces `build_feature_dossiers(bundle, main_dossiers) -> list[dict[str, object]]`.
- Produces `build_future_ablation_hypotheses() -> list[dict[str, object]]` returning `[]` in the initial locked implementation.

- [ ] **Step 1: Write failing Supplementary boundary tests**

```python
from research.combined_audit_contract import RAW_DIRECTION_SENSITIVE
from research.task10_interpretation_reports import build_supplementary_evidence


def test_supplementary_layer_is_exactly_960_rows(bundle):
    rows = build_supplementary_evidence(bundle)
    assert len(rows) == 4 * 2 * 120


def test_raw_direction_sensitive_pairs_are_never_primary(rows):
    for row in rows:
        contains_raw = bool(
            {row["feature_x"], row["feature_y"]} & set(RAW_DIRECTION_SENSITIVE)
        )
        assert row["contains_raw_direction_sensitive"] is contains_raw
        if contains_raw:
            assert row["is_main_pair"] is False
            assert row["evidence_scope"] == "SUPPLEMENTARY_ONLY"
```

- [ ] **Step 2: Implement Supplementary projection without recomputation**

Iterate deterministic order:

```python
for tf in TIMEFRAMES:
    for direction in DIRECTIONS:
        for source_row in bundle.supplementary_by_tf_direction[(tf, direction)]:
            ...
```

Copy all Task 9 raw/controlled values and statuses exactly. Add only:
- `timeframe`;
- `direction`;
- `source_artifact = f"SUPPLEMENTARY_{tf}_{direction}.csv"`;
- canonical `pair_key`;
- `contains_raw_direction_sensitive`;
- `is_main_pair`.

Do not promote raw-direction-sensitive rows to primary evidence.

- [ ] **Step 3: Write failing Feature Dossier tests**

```python
from research.combined_audit_contract import MAIN_FEATURES
from research.task10_interpretation_reports import build_feature_dossiers


def test_feature_dossiers_are_exactly_13_and_each_links_12_pairs(bundle, main_dossiers):
    dossiers = build_feature_dossiers(bundle, main_dossiers)
    assert [d["feature"] for d in dossiers] == list(MAIN_FEATURES)
    assert len(dossiers) == 13
    assert all(len(d["main_relationship_pair_keys"]) == 12 for d in dossiers)
    assert all("rank" not in d for d in dossiers)
    assert all("score" not in d for d in dossiers)
    assert all("weight" not in d for d in dossiers)
    assert all("recommendation" not in d for d in dossiers)
```

- [ ] **Step 4: Implement Feature Dossiers as evidence indexes only**

Use the exact frozen `MAIN_FEATURES` order. Each Feature Dossier must contain:

```python
{
    "feature": feature,
    "task9_definition": feature_role_by_name[feature]["formula or source definition"],
    "task9_analysis_role": feature_role_by_name[feature]["analysis role"],
    "task9_direction_semantics": feature_role_by_name[feature]["direction semantics"],
    "deterministic_context": {...},
    "main_relationship_pair_keys": [exactly 12 keys in MAIN_PAIR_KEYS order],
    "supplementary_pair_keys": [keys involving this feature],
    "future_ablation_hypothesis_ids": [],
}
```

When actual Task 9 Feature Role Matrix header strings differ in punctuation/casing, use the exact header constants/values from the loaded row rather than guessing. The implementation must resolve required columns once and fail if they are absent.

No aggregate correlation, rank, score, weighted statistic, or keep/drop field is allowed.

- [ ] **Step 5: Freeze future-Ablation hypotheses as empty-by-default**

```python
def build_future_ablation_hypotheses() -> list[dict[str, object]]:
    """Task 10 permits zero or more hypotheses; no selection rule is authorized."""
    return []
```

Add test:

```python
def test_automated_task10_does_not_invent_ablation_hypotheses():
    assert build_future_ablation_hypotheses() == []
```

This preserves the Spec's ability to add traceable, unranked hypotheses later under explicit Task 10 review without inventing a cutoff or selection criterion in code.

- [ ] **Step 6: Run Task 4 tests to GREEN**

Run:
```bash
pytest -q tests/test_task10_interpretation_reports.py
```
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add research/task10_interpretation_reports.py tests/test_task10_interpretation_reports.py
git commit -m "feat: add Task 10 supplementary and feature dossiers"
```

---

### Task 5: Write deterministic Task 10 outputs, provenance manifest, and thin CLI

**Files:**
- Modify: `research/task10_interpretation_io.py`
- Create: `research/run_task10_dependency_interpretation.py`
- Create: `tests/test_task10_interpretation_integration.py`

**Interfaces:**
- Produces `write_task10_outputs(output_dir: Path, *, bundle, main_dossiers, supplementary, feature_dossiers, hypotheses) -> None`.
- Produces `write_task10_output_bundle(output_dir: Path, zip_path: Path) -> None`.
- Produces `task10_implementation_commit() -> str`.
- CLI arguments: `--input-evidence`, `--output-dir`, optional `--output-zip`.
- CLI has no threshold, score, rank, outcome, alternative SHA, alternate control, or statistical-method argument.

- [ ] **Step 1: Write RED integration test for exact five logical files**

```python
from research.task10_interpretation_contract import TASK10_LOGICAL_FILENAMES


def test_end_to_end_writes_exactly_five_logical_artifacts(tmp_path, valid_task9_zip):
    output_dir = tmp_path / "out"
    run_task10(valid_task9_zip, output_dir)

    assert sorted(path.name for path in output_dir.iterdir()) == sorted(
        TASK10_LOGICAL_FILENAMES
    )
```

- [ ] **Step 2: Implement deterministic JSON and CSV writers**

Use exactly:

```python
def write_json(path: Path, payload: object) -> None:
    data = json.dumps(
        payload,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
        allow_nan=False,
    ).encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
```

For CSV:
- UTF-8;
- exact frozen `SUPPLEMENTARY_OUTPUT_FIELDS` order;
- `lineterminator="\n"`;
- `extrasaction="raise"` so unplanned fields are not silently emitted.

- [ ] **Step 3: Implement the Task 10 manifest with explicit no-scope flags**

Manifest fields must include at least:

```python
{
    "task": "Task 10 Dependency / Redundancy Interpretation",
    "task10_spec_commit": TASK10_SPEC_COMMIT,
    "task10_implementation_commit": task10_implementation_commit(),
    "task9_evidence_package_filename": TASK9_EVIDENCE_PACKAGE_FILENAME,
    "task9_evidence_package_sha256": bundle.evidence_zip_sha256,
    "task9_activity_input_sha256": TASK9_ACTIVITY_INPUT_SHA256,
    "task9_audit_code_commit": TASK9_AUDIT_CODE_COMMIT,
    "task9_registration_commit": TASK9_REGISTRATION_COMMIT,
    "main_relationship_dossier_count": 78,
    "partial_delta_eligible_pair_count": 66,
    "control_feature_non_applicable_pair_count": 12,
    "feature_dossier_count": 13,
    "supplementary_evidence_row_count": 960,
    "future_ablation_hypothesis_count": 0,
    "raw_cross_tf_pooling": False,
    "new_association_statistics_computed": False,
    "ranking_performed": False,
    "cutoff_applied": False,
    "score_computed": False,
    "outcome_used": False,
    "ablation_executed": False,
    "causal_replay_executed": False,
    "feature_removal_recommended": False,
}
```

Reject manifest construction if actual output counts differ from these locked values.

- [ ] **Step 4: Implement the implementation-commit provenance helper**

```python
def task10_implementation_commit() -> str:
    repository = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        ["git", "-C", str(repository), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    )
    commit = result.stdout.strip()
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise RuntimeError(f"invalid git commit SHA: {commit!r}")
    return commit
```

- [ ] **Step 5: Implement deterministic ZIP writer**

Package only `TASK10_LOGICAL_FILENAMES`, sorted by member name, with stable ZIP timestamps `(1980, 1, 1, 0, 0, 0)`, deflate level 9, and stable Unix file mode `0o100644`.

Reject missing or extra logical output files before creating the ZIP.

- [ ] **Step 6: Implement thin orchestration function before CLI parsing**

```python
def run_task10(input_evidence: Path, output_dir: Path) -> dict[str, object]:
    bundle = load_task9_evidence_package(input_evidence)
    main_dossiers = build_main_relationship_dossiers(bundle)
    supplementary = build_supplementary_evidence(bundle)
    feature_dossiers = build_feature_dossiers(bundle, main_dossiers)
    hypotheses = build_future_ablation_hypotheses()

    write_task10_outputs(
        output_dir,
        bundle=bundle,
        main_dossiers=main_dossiers,
        supplementary=supplementary,
        feature_dossiers=feature_dossiers,
        hypotheses=hypotheses,
    )
    return {
        "main_relationship_dossiers": len(main_dossiers),
        "supplementary_rows": len(supplementary),
        "feature_dossiers": len(feature_dossiers),
        "hypotheses": len(hypotheses),
    }
```

- [ ] **Step 7: Implement CLI with only three arguments**

```python
parser.add_argument("--input-evidence", required=True, type=Path)
parser.add_argument("--output-dir", required=True, type=Path)
parser.add_argument("--output-zip", type=Path)
```

No `--threshold`, `--rank`, `--score`, `--control`, `--method`, `--outcome`, `--ablation`, or SHA override flag.

- [ ] **Step 8: Add byte-for-byte repeatability integration test**

Run the same synthetic package into `run_a/` and `run_b/`. For every filename in `TASK10_LOGICAL_FILENAMES`:

```python
assert (run_a / filename).read_bytes() == (run_b / filename).read_bytes()
```

Build two output ZIPs and require byte identity as well.

Because the manifest contains `task10_implementation_commit`, both runs must occur at the same commit and produce identical bytes.

- [ ] **Step 9: Add exact output-content assertions**

Integration test must parse outputs and assert:

```python
assert len(main_dossiers) == 78
assert sum(d["partial_applicability"] == "ELIGIBLE" for d in main_dossiers) == 66
assert sum(
    d["partial_applicability"] == "NOT_APPLICABLE_CONTROL_FEATURE"
    for d in main_dossiers
) == 12
assert len(feature_dossiers) == 13
assert hypotheses == []
assert len(supplementary_rows) == 960
assert all(d["cross_tf"]["n_defined_tf"] + d["cross_tf"]["n_undefined_tf"] == 4 for d in main_dossiers)
```

- [ ] **Step 10: Run Task 5 tests to GREEN**

Run:
```bash
pytest -q tests/test_task10_interpretation_integration.py
```
Expected: PASS.

- [ ] **Step 11: Commit**

```bash
git add \
  research/task10_interpretation_io.py \
  research/run_task10_dependency_interpretation.py \
  tests/test_task10_interpretation_integration.py
git commit -m "feat: add deterministic Task 10 interpretation pipeline"
```

---

### Task 6: Non-regression, scope isolation, and final implementation verification

**Files:**
- Test only; do not modify production `src/` files.

**Interfaces:**
- Consumes the completed Task 10 implementation.
- Produces verification evidence only.

- [ ] **Step 1: Run all Task 10 tests**

Run:
```bash
pytest -q \
  tests/test_task10_interpretation_contract.py \
  tests/test_task10_interpretation_io.py \
  tests/test_task10_interpretation_reports.py \
  tests/test_task10_interpretation_integration.py
```
Expected: all PASS.

- [ ] **Step 2: Run the locked Combined Audit regression tests**

Run:
```bash
pytest -q \
  tests/test_combined_audit_contract.py \
  tests/test_combined_audit_stats.py \
  tests/test_combined_audit_deterministic.py \
  tests/test_combined_audit_reports.py \
  tests/test_combined_audit_io.py \
  tests/test_combined_audit_integration.py
```
Expected: all PASS; no Task 9 behavior changes.

- [ ] **Step 3: Run full repository tests**

Run:
```bash
pytest -q
```
Expected: PASS with zero failures.

- [ ] **Step 4: Prove Task 9 Evidence and Engine files were not modified**

Run from the implementation branch against the locked Task 9 registration base:

```bash
git diff --name-only 78e54fb50ce82a0cba7f91f40a6451e82996008d...HEAD
```

Allowed paths are limited to:

```text
docs/superpowers/specs/2026-08-31-task10-dependency-redundancy-interpretation-design.md
docs/superpowers/plans/2026-08-31-task10-dependency-redundancy-interpretation.md
research/task10_interpretation_contract.py
research/task10_interpretation_io.py
research/task10_interpretation_reports.py
research/run_task10_dependency_interpretation.py
tests/test_task10_interpretation_contract.py
tests/test_task10_interpretation_io.py
tests/test_task10_interpretation_reports.py
tests/test_task10_interpretation_integration.py
```

Any changed path under `src/`, any changed `research/combined_audit_*.py`, or any change to `evidence/GOLD_COMBINED_LEG_FEATURE_AUDIT_PACKAGE.zip` is a blocker.

- [ ] **Step 5: Static forbidden-scope scan over Task 10 implementation**

Run:

```bash
git grep -n -E \
  'spearman_pairwise\(|partial_spearman_duration\(|PCA|Mutual Information|Clustering|MFE|MAE|Profit|Loss|Prediction|Feature Weight|Accept/Reject' \
  -- research/task10_interpretation_*.py research/run_task10_dependency_interpretation.py
```

Expected:
- no statistical primitive invocation;
- provenance/scope-manifest strings may mention prohibited phase names only as explicit `False` flags;
- no implementation of those phases.

Inspect any hit manually; do not suppress a genuine violation.

- [ ] **Step 6: Verify CLI has no decision/statistical override flags**

Run:
```bash
python -m research.run_task10_dependency_interpretation --help
```
Expected arguments only:
- `--input-evidence`;
- `--output-dir`;
- optional `--output-zip`.

- [ ] **Step 7: Commit only if verification required a test-only correction**

If no changes were needed, do not create an empty commit.
If a test-only correction was required:

```bash
git add tests/test_task10_interpretation_*.py
git commit -m "test: harden Task 10 interpretation verification"
```

---

## HUMAN APPROVAL GATE — REQUIRED BEFORE PRODUCTION TASK 10 EXECUTION

After Tasks 1–6 are implemented, reviewed, and verified, stop.

Report:
- implementation branch;
- implementation HEAD SHA;
- changed paths versus `78e54fb50ce82a0cba7f91f40a6451e82996008d`;
- Task 10 test count/result;
- Combined Audit regression result;
- full-repository test result;
- explicit confirmation that Task 9 Evidence and `src/` were unchanged.

Then wait for explicit human authorization.

**Do not open or interpret the canonical production Task 9 Evidence ZIP through the Task 10 pipeline before this approval.**

**Do not execute Ablation or Causal Replay under any circumstance from this Plan.**

---

### Task 7: Production Task 10 interpretation — ONLY AFTER SEPARATE EXPLICIT AUTHORIZATION

**Files:**
- Read only: `evidence/GOLD_COMBINED_LEG_FEATURE_AUDIT_PACKAGE.zip`
- Write only to new clean Task 10 output directories and optional new Task 10 output archive.
- Do not modify source, Task 9 evidence, Task 9 reports, Swing, or Leg Engine.

**Interfaces:**
- Consumes the exact canonical Task 9 Evidence ZIP.
- Produces the five locked Task 10 logical artifacts and optional deterministic Task 10 ZIP.

- [ ] **Step 1: Verify production input SHA independently before execution**

Run:
```bash
python -c "from pathlib import Path; import hashlib; p=Path('evidence/GOLD_COMBINED_LEG_FEATURE_AUDIT_PACKAGE.zip'); print(hashlib.sha256(p.read_bytes()).hexdigest())"
```
Expected exactly:
```text
968f4826858a0bbb8254218711f4ad3e3487370ca8d0f288133ee36f7a4fa40d
```
Any mismatch is a blocker; do not open the ZIP through the pipeline.

- [ ] **Step 2: Run production interpretation twice into clean directories**

```bash
rm -rf .task10-run-a .task10-run-b
python -m research.run_task10_dependency_interpretation \
  --input-evidence evidence/GOLD_COMBINED_LEG_FEATURE_AUDIT_PACKAGE.zip \
  --output-dir .task10-run-a \
  --output-zip .task10-run-a/TASK10_DEPENDENCY_REDUNDANCY_INTERPRETATION_PACKAGE.zip

python -m research.run_task10_dependency_interpretation \
  --input-evidence evidence/GOLD_COMBINED_LEG_FEATURE_AUDIT_PACKAGE.zip \
  --output-dir .task10-run-b \
  --output-zip .task10-run-b/TASK10_DEPENDENCY_REDUNDANCY_INTERPRETATION_PACKAGE.zip
```

On Windows PowerShell, use `Remove-Item -Recurse -Force` instead of `rm -rf`; do not alter the command semantics.

- [ ] **Step 3: Compare all five logical outputs byte-for-byte**

Use a Python comparison that fails on the first mismatch:

```python
from pathlib import Path

names = (
    "TASK10_MAIN_RELATIONSHIP_DOSSIERS.json",
    "TASK10_SUPPLEMENTARY_EVIDENCE.csv",
    "TASK10_FEATURE_DOSSIERS.json",
    "TASK10_FUTURE_ABLATION_HYPOTHESES.json",
    "TASK10_MANIFEST.json",
)

for name in names:
    a = Path(".task10-run-a", name).read_bytes()
    b = Path(".task10-run-b", name).read_bytes()
    if a != b:
        raise SystemExit(f"BYTE MISMATCH: {name}")
print("ALL 5 LOGICAL FILES BYTE-IDENTICAL")
```

- [ ] **Step 4: Compare both deterministic Task 10 ZIPs byte-for-byte and hash them**

```python
from pathlib import Path
import hashlib

name = "TASK10_DEPENDENCY_REDUNDANCY_INTERPRETATION_PACKAGE.zip"
a = Path(".task10-run-a", name).read_bytes()
b = Path(".task10-run-b", name).read_bytes()
assert a == b
print(hashlib.sha256(a).hexdigest())
```

Record the resulting SHA-256 as the Task 10 output-package SHA. Do not predeclare its value in the Plan.

- [ ] **Step 5: Validate production logical counts**

Parse outputs and require:

```text
Main Relationship Dossiers          = 78
Partial/delta eligible pairs        = 66
Control-feature non-applicable      = 12
Feature Dossiers                    = 13
Supplementary Evidence rows         = 960
Future Ablation Hypotheses          = 0
Logical output files                = 5
```

For every Main Dossier require:

```text
n_defined_tf + n_undefined_tf = 4
```

For every one of the 12 `active_bar_count` pairs require every controlled TF status to equal:

```text
NOT_APPLICABLE_CONTROL_FEATURE
```

- [ ] **Step 6: Verify raw-direction-sensitive separation in production output**

Require no Main Relationship Dossier pair to contain:

```text
close_ols_slope
gross_upper_shadow
gross_lower_shadow
```

Require those fields, when present, to appear only in `TASK10_SUPPLEMENTARY_EVIDENCE.csv`.

- [ ] **Step 7: Verify no decision language or unauthorized phase output was emitted**

Inspect the 78 dossier `observations` and hypotheses artifact. Require:
- hypotheses file is exactly an empty JSON list;
- no ranking fields;
- no cutoff fields;
- no score/weight/recommendation fields;
- no qualitative strength/stability/redundancy labels;
- manifest flags show `ablation_executed=false`, `causal_replay_executed=false`, `raw_cross_tf_pooling=false`, and `new_association_statistics_computed=false`.

- [ ] **Step 8: Re-run full repository tests after production output generation**

Run:
```bash
pytest -q
```
Expected: PASS with zero failures.

- [ ] **Step 9: Report and stop**

Report only:
- Task 9 Evidence input SHA-256;
- Task 10 implementation commit SHA;
- locked Spec commit SHA;
- all Task 10 validation gate results;
- `78 / 66 / 12 / 13 / 960 / 0 / 5` locked counts;
- two-run logical byte comparison result;
- two-run ZIP byte comparison result;
- Task 10 output ZIP SHA-256;
- test evidence;
- generated filenames;
- confirmation that Task 9, Swing, Leg Engine, and locked metrics were unchanged.

Then stop.

**Ablation remains NOT AUTHORIZED.**

**Causal Replay remains NOT AUTHORIZED.**

**Score / Threshold / Feature Selection remain NOT AUTHORIZED.**

---

## Plan Self-Review Checklist

Before declaring this Plan ready for human review, verify:

- [ ] Every locked Spec requirement maps to a Task above.
- [ ] The Plan contains no `TBD`, `TODO`, `implement later`, or hidden placeholder.
- [ ] Main pair count is exactly 78 everywhere.
- [ ] Partial/delta eligible count is exactly 66 everywhere.
- [ ] Control-feature non-applicable count is exactly 12 everywhere.
- [ ] Supplementary physical count is exactly 960 rows = 120 × 2 × 4.
- [ ] Feature Dossier count is exactly 13 everywhere.
- [ ] `n_defined_tf` is explicit and Undefined is never zero-filled.
- [ ] Task 9 Main `rho_raw` remains distinct from `rho_raw_for_delta`.
- [ ] No Task 10 statistical recomputation is planned.
- [ ] No raw-direction-sensitive pair can enter Main Dossiers.
- [ ] No ranking/cutoff/qualitative label/removal recommendation is planned.
- [ ] Automated hypotheses remain empty rather than inventing an unapproved selection rule.
- [ ] Task 9 Evidence SHA is checked before ZIP parsing.
- [ ] No `src/`, Task 9 audit code, or Task 9 Evidence mutation is planned.
- [ ] Human approval gate exists before production execution.
- [ ] Ablation and Causal Replay remain explicitly unauthorized.
