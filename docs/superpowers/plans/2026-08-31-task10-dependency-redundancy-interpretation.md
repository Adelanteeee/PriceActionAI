# Task 10 Dependency / Redundancy Interpretation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a research-only interpretation pipeline that consumes the Final-Locked Task 9 Combined Audit Evidence Package and emits exactly 78 non-decision-making Main Relationship Dossiers, 960 Supplementary Evidence rows, exactly 13 Feature Dossiers, an explicitly untested future-Ablation hypothesis artifact, and a deterministic provenance manifest without recomputing Task 9 statistics or touching locked Engine code.

**Architecture:** Task 10 is a read-only interpretation layer over Task 9 outputs. Production entry points enforce the canonical Task 9 Evidence SHA and a clean committed worktree before any output is produced. Synthetic tests use private test-only seams that are not reachable from the public loader or CLI. Main/Partial/Cross-TF/Supplementary rows are joined by canonical pair keys and preserved with explicit source-artifact/row locators.

**Tech Stack:** Python 3.12, pytest, Python standard library only (`argparse`, `csv`, `hashlib`, `io`, `itertools`, `json`, `math`, `pathlib`, `re`, `subprocess`, `zipfile`, `dataclasses`, `collections.abc`). Reuse locked Task 9 constants and schemas from `research.combined_audit_contract` and `research.combined_audit_io`; never import `src/` Engine modules.

**Spec:** `docs/superpowers/specs/2026-08-31-task10-dependency-redundancy-interpretation-design.md`

**Locked Spec Commit:** `dfc91e3c75a12a3dfa008c17453b622f03ed41ad`

## Global Constraints

- Canonical Task 9 Evidence Package: `GOLD_COMBINED_LEG_FEATURE_AUDIT_PACKAGE.zip`.
- Canonical Task 9 Evidence SHA-256: `968f4826858a0bbb8254218711f4ad3e3487370ca8d0f288133ee36f7a4fa40d`.
- Canonical upstream Activity SHA-256: `1e9f13fd88fc1e8e0e66d801be8c15d726639eaea25e53fef7c3bb88bfd05192`.
- Task 9 audit-code commit: `1c40cd3d3507c473fd07ea25c010d386be8a0043`.
- Task 9 registration commit: `78e54fb50ce82a0cba7f91f40a6451e82996008d`.
- Main feature universe is exactly the locked 13 `MAIN_FEATURES`.
- Main Relationship Dossiers: exactly 78.
- Partial/`delta_rho` eligible main pairs: exactly 66.
- Main pairs containing `active_bar_count`: exactly 12; controlled status must be `NOT_APPLICABLE_CONTROL_FEATURE`.
- `NOT_APPLICABLE_CONTROL_FEATURE` is a structural state, not zero, missingness, undefined correlation, failure, insufficient observations, or constant input.
- Main pairwise `rho_raw` remains distinct from triple-complete `rho_raw_for_delta`.
- Task 10 never recomputes Raw Spearman, Partial Spearman, or `delta_rho`.
- `rho_range` is based only on defined raw TF values and every dossier includes `n_defined_tf`.
- Every dossier must satisfy `n_defined_tf + n_undefined_tf == 4`.
- Undefined TF values are never converted to zero.
- Supplementary evidence remains separate: 120 rows × 2 directions × 4 TF = 960 rows.
- Any pair containing `close_ols_slope`, `gross_upper_shadow`, or `gross_lower_shadow` remains outside the 78 Main Dossiers.
- Deterministic identity evidence precedes statistical evidence; Task 10 invents no new deterministic identity.
- No Ranking, Cutoff, qualitative strength/stability/redundancy label, feature importance, Feature Weight, Keep/Drop recommendation, Score, Threshold, Outcome, Prediction, Optimization, PCA, Mutual Information, Clustering, Ablation execution, Causal Replay, or causal interpretation.
- No raw cross-TF pooling.
- No modification to Task 9 evidence, `research/combined_audit_*.py`, `src/price_action_ai_swing_v1_locked.py`, `src/price_action_ai_leg_v0.py`, locked Swing/Leg formulas, or historical evidence.
- Tasks 1–6 and Task 7 remain **NOT AUTHORIZED** until separate explicit human authorization.

## Review Corrections Incorporated

1. **Synthetic SHA seam:** public `load_task9_evidence_package()` always enforces the canonical SHA. Synthetic tests use private `_load_task9_evidence_bytes(..., expected_sha256=...)` and private `_run_task10_from_bundle(...)`; neither seam is exposed by CLI or production `run_task10()`.
2. **Main Dossier completeness:** every main dossier must include `feature_x_analysis_role`, `feature_y_analysis_role`, `direct_deterministic_dependency`, source-artifact maps, cross-TF source artifact, and stable source-pair/row locators. Feature Role source keys are exactly `formula`, `analysis_role`, and `direction_semantics`.
3. **Scope allowlist:** the Spec Lock Record file `docs/superpowers/specs/2026-08-31-task10-dependency-redundancy-interpretation-design.LOCKED.md` is explicitly allowed.
4. **Production provenance:** production execution is blocked unless tracked worktree and staging area are clean and the current HEAD contains all Task 10 implementation files. The validated HEAD SHA is passed into output construction and is the only Task 10 implementation SHA written to the manifest.

## Planned Files

- Create `research/task10_interpretation_contract.py`.
- Create `research/task10_interpretation_io.py`.
- Create `research/task10_interpretation_reports.py`.
- Create `research/run_task10_dependency_interpretation.py`.
- Create `tests/test_task10_interpretation_contract.py`.
- Create `tests/test_task10_interpretation_io.py`.
- Create `tests/test_task10_interpretation_reports.py`.
- Create `tests/test_task10_interpretation_integration.py`.

## Physical Outputs

1. `TASK10_MAIN_RELATIONSHIP_DOSSIERS.json` — 78 records.
2. `TASK10_SUPPLEMENTARY_EVIDENCE.csv` — 960 rows.
3. `TASK10_FEATURE_DOSSIERS.json` — 13 records.
4. `TASK10_FUTURE_ABLATION_HYPOTHESES.json` — initial automated output is `[]`.
5. `TASK10_MANIFEST.json`.

Optional deterministic archive:

```text
TASK10_DEPENDENCY_REDUNDANCY_INTERPRETATION_PACKAGE.zip
```

---

### Task 1: Freeze contract, canonical pair sets, and output schemas

**Files:**
- Create: `research/task10_interpretation_contract.py`
- Create: `tests/test_task10_interpretation_contract.py`

**Interfaces:**
- Consume `MAIN_FEATURES`, `RAW_DIRECTION_SENSITIVE`, `TIMEFRAMES`, `DIRECTIONS`.
- Produce `MAIN_PAIR_KEYS`, `PARTIAL_PAIR_KEYS`, `CONTROL_PAIR_KEYS`, `SUPPLEMENTARY_PAIR_KEYS`.
- Produce `CONTROL_NOT_APPLICABLE = "NOT_APPLICABLE_CONTROL_FEATURE"`.
- Produce stable pair-key helpers and output filenames.

- [ ] **Step 1: Write RED count tests**

```python
from research.task10_interpretation_contract import (
    CONTROL_PAIR_KEYS,
    MAIN_PAIR_KEYS,
    PARTIAL_PAIR_KEYS,
    SUPPLEMENTARY_PAIR_KEYS,
)


def test_pair_counts_are_locked():
    assert len(MAIN_PAIR_KEYS) == 78
    assert len(PARTIAL_PAIR_KEYS) == 66
    assert len(CONTROL_PAIR_KEYS) == 12
    assert len(SUPPLEMENTARY_PAIR_KEYS) == 120
    assert set(PARTIAL_PAIR_KEYS).isdisjoint(CONTROL_PAIR_KEYS)
    assert set(PARTIAL_PAIR_KEYS) | set(CONTROL_PAIR_KEYS) == set(MAIN_PAIR_KEYS)
```

- [ ] **Step 2: Run RED**

```bash
pytest -q tests/test_task10_interpretation_contract.py
```

Expected: FAIL because module does not exist.

- [ ] **Step 3: Implement exact constants**

```python
from itertools import combinations
from research.combined_audit_contract import MAIN_FEATURES, RAW_DIRECTION_SENSITIVE

TASK9_EVIDENCE_PACKAGE_FILENAME = "GOLD_COMBINED_LEG_FEATURE_AUDIT_PACKAGE.zip"
TASK9_EVIDENCE_SHA256 = "968f4826858a0bbb8254218711f4ad3e3487370ca8d0f288133ee36f7a4fa40d"
TASK9_ACTIVITY_INPUT_SHA256 = "1e9f13fd88fc1e8e0e66d801be8c15d726639eaea25e53fef7c3bb88bfd05192"
TASK9_AUDIT_CODE_COMMIT = "1c40cd3d3507c473fd07ea25c010d386be8a0043"
TASK9_REGISTRATION_COMMIT = "78e54fb50ce82a0cba7f91f40a6451e82996008d"
TASK10_SPEC_COMMIT = "dfc91e3c75a12a3dfa008c17453b622f03ed41ad"

CONTROL_FEATURE = "active_bar_count"
CONTROL_NOT_APPLICABLE = "NOT_APPLICABLE_CONTROL_FEATURE"
MAIN_PAIR_KEYS = tuple(combinations(MAIN_FEATURES, 2))
PARTIAL_PAIR_KEYS = tuple(p for p in MAIN_PAIR_KEYS if CONTROL_FEATURE not in p)
CONTROL_PAIR_KEYS = tuple(p for p in MAIN_PAIR_KEYS if CONTROL_FEATURE in p)
SUPPLEMENTARY_FEATURES = MAIN_FEATURES + RAW_DIRECTION_SENSITIVE
SUPPLEMENTARY_PAIR_KEYS = tuple(combinations(SUPPLEMENTARY_FEATURES, 2))
```

- [ ] **Step 4: Implement stable pair key**

```python
_FEATURE_ORDER = {
    name: i for i, name in enumerate(MAIN_FEATURES + RAW_DIRECTION_SENSITIVE)
}


def canonical_pair(x: str, y: str) -> tuple[str, str]:
    if x == y:
        raise ValueError("pair requires two distinct features")
    try:
        a, b = sorted((x, y), key=_FEATURE_ORDER.__getitem__)
    except KeyError as exc:
        raise ValueError(f"unknown Task 10 feature: {exc.args[0]}") from exc
    return a, b


def pair_key(x: str, y: str) -> str:
    a, b = canonical_pair(x, y)
    return f"{a}__{b}"
```

- [ ] **Step 5: Run GREEN and commit**

```bash
pytest -q tests/test_task10_interpretation_contract.py
git add research/task10_interpretation_contract.py tests/test_task10_interpretation_contract.py
git commit -m "test: lock Task 10 interpretation contract"
```

---

### Task 2: Strict Task 9 Evidence loader with private synthetic seam

**Files:**
- Create: `research/task10_interpretation_io.py`
- Create: `tests/test_task10_interpretation_io.py`

**Interfaces:**
- Public production loader: `load_task9_evidence_package(path: Path) -> Task9EvidenceBundle`.
- Private test seam: `_load_task9_evidence_bytes(package_bytes: bytes, *, expected_sha256: str) -> Task9EvidenceBundle`.
- Public loader must not expose `expected_sha256`.
- CLI must not expose any SHA override.

- [ ] **Step 1: Write RED public-loader SHA test**

```python
from pathlib import Path
import pytest
from research.task10_interpretation_io import load_task9_evidence_package


def test_public_loader_rejects_noncanonical_sha_before_zip_parse(tmp_path: Path):
    p = tmp_path / "bad.zip"
    p.write_bytes(b"not-a-zip")
    with pytest.raises(ValueError, match="Task 9 Evidence SHA-256 mismatch"):
        load_task9_evidence_package(p)
```

- [ ] **Step 2: Implement private bytes loader and strict public wrapper**

```python
def load_task9_evidence_package(path: Path) -> Task9EvidenceBundle:
    package_bytes = Path(path).read_bytes()
    return _load_task9_evidence_bytes(
        package_bytes,
        expected_sha256=TASK9_EVIDENCE_SHA256,
    )


def _load_task9_evidence_bytes(
    package_bytes: bytes,
    *,
    expected_sha256: str,
) -> Task9EvidenceBundle:
    actual_sha = hashlib.sha256(package_bytes).hexdigest()
    if actual_sha != expected_sha256:
        raise ValueError(
            f"Task 9 Evidence SHA-256 mismatch: expected {expected_sha256}, got {actual_sha}"
        )
    # ZIP parsing begins only after SHA success.
    ...
```

The implementation following the shown guard must perform exact member, duplicate-member, path-safety, UTF-8/CSV/JSON, numeric-finiteness, row-count, pair-set, and Task 9 manifest provenance validation. No production caller may supply an alternate expected SHA.

- [ ] **Step 3: Lock exact Task 9 source schemas/counts**

Require:

```text
Feature Role Matrix       = 47 rows
Deterministic Identity    = 44 rows
Main Raw                  = 78 rows per TF
Partial                   = 66 rows per TF
Supplementary             = 120 rows per direction per TF
Cross-TF                  = 78 rows
```

Require exact pair sets for Main/Partial/Supplementary/Cross-TF. Reject any raw-direction-sensitive feature in Main/Cross-TF.

- [ ] **Step 4: Lock Feature Role source column names**

Import `FEATURE_ROLE_COLUMNS` from the locked Task 9 contract and require the exact source keys:

```python
required_role_columns = {
    "feature",
    "formula",
    "analysis_role",
    "direction_semantics",
}
assert required_role_columns <= set(FEATURE_ROLE_COLUMNS)
```

All Task 10 lookups use exactly `formula`, `analysis_role`, and `direction_semantics`; no humanized aliases such as `formula or source definition` are permitted.

- [ ] **Step 5: Add tests proving the seam is private-only**

```python
import inspect
from research.task10_interpretation_io import load_task9_evidence_package


def test_public_loader_has_no_sha_override():
    assert "expected_sha256" not in inspect.signature(load_task9_evidence_package).parameters
```

Synthetic ZIP tests call only:

```python
bundle = _load_task9_evidence_bytes(
    synthetic_bytes,
    expected_sha256=hashlib.sha256(synthetic_bytes).hexdigest(),
)
```

- [ ] **Step 6: Run GREEN and commit**

```bash
pytest -q tests/test_task10_interpretation_io.py
git add research/task10_interpretation_io.py tests/test_task10_interpretation_io.py
git commit -m "feat: add strict Task 10 evidence loader"
```

---

### Task 3: Build 78 Main Relationship Dossiers with complete source traceability

**Files:**
- Create: `research/task10_interpretation_reports.py`
- Create: `tests/test_task10_interpretation_reports.py`

**Interfaces:**
- `build_main_relationship_dossiers(bundle) -> list[dict[str, object]]`.
- No Task 10 call to `spearman_pairwise()` or `partial_spearman_duration()`.

- [ ] **Step 1: Write RED required-field test**

Every dossier must include at least:

```python
REQUIRED_MAIN_DOSSIER_FIELDS = {
    "pair_key",
    "source_pair_key",
    "feature_x",
    "feature_y",
    "feature_x_analysis_role",
    "feature_y_analysis_role",
    "direct_deterministic_dependency",
    "direct_deterministic_relation_ids",
    "raw_source_artifact_by_tf",
    "raw_source_row_locator_by_tf",
    "partial_source_artifact_by_tf",
    "partial_source_row_locator_by_tf",
    "cross_tf_source_artifact",
    "cross_tf_source_row_locator",
    "partial_applicability",
    "raw_by_tf",
    "partial_by_tf",
    "cross_tf",
    "deterministic_context",
    "observations",
}
```

Test all 78 records and exact 66/12 applicability counts.

- [ ] **Step 2: Define source-pair and row-locator contract**

For each canonical pair:

```python
source_pair_key = pair_key(feature_x, feature_y)
raw_source_artifact_by_tf = {
    tf: f"MAIN_SPEARMAN_{tf}.csv" for tf in TIMEFRAMES
}
raw_source_row_locator_by_tf = {
    tf: f"MAIN_SPEARMAN_{tf}.csv#{source_pair_key}" for tf in TIMEFRAMES
}
cross_tf_source_artifact = "CROSS_TF_RELATIONSHIP_REPORT.csv"
cross_tf_source_row_locator = (
    f"CROSS_TF_RELATIONSHIP_REPORT.csv#{source_pair_key}"
)
```

For eligible pairs:

```python
partial_source_artifact_by_tf = {
    tf: f"PARTIAL_SPEARMAN_{tf}.csv" for tf in TIMEFRAMES
}
partial_source_row_locator_by_tf = {
    tf: f"PARTIAL_SPEARMAN_{tf}.csv#{source_pair_key}" for tf in TIMEFRAMES
}
```

For the 12 control-feature pairs:

```python
partial_source_artifact_by_tf = {tf: None for tf in TIMEFRAMES}
partial_source_row_locator_by_tf = {
    tf: CONTROL_NOT_APPLICABLE for tf in TIMEFRAMES
}
```

- [ ] **Step 3: Copy exact Feature Role metadata**

Build a unique `feature_role_by_name` index from Task 9 rows and copy:

```python
feature_x_analysis_role = feature_role_by_name[feature_x]["analysis_role"]
feature_y_analysis_role = feature_role_by_name[feature_y]["analysis_role"]
feature_x_formula = feature_role_by_name[feature_x]["formula"]
feature_y_formula = feature_role_by_name[feature_y]["formula"]
feature_x_direction_semantics = feature_role_by_name[feature_x]["direction_semantics"]
feature_y_direction_semantics = feature_role_by_name[feature_y]["direction_semantics"]
```

Main features must resolve to `ANALYSIS_FEATURE`; otherwise fail closed.

- [ ] **Step 4: Define `direct_deterministic_dependency` without inventing a new identity**

Parse the locked Task 9 deterministic `participating_features` field. For a main pair:

```python
shared_relation_ids = sorted(
    relation_id
    for relation_id, participants in task9_relation_participants.items()
    if {feature_x, feature_y} <= participants
)
direct_deterministic_dependency = bool(shared_relation_ids)
```

Semantics are frozen: `True` means both main features co-participate in at least one locked Task 9 deterministic identity row. It does **not** mean either feature is a two-variable function solely of the other. Emit the exact supporting IDs in `direct_deterministic_relation_ids`.

- [ ] **Step 5: Preserve raw/partial values and control non-applicability**

For 66 eligible pairs copy Task 9 Partial rows exactly by pair+TF. For the 12 control pairs emit per TF:

```python
{
    "rho_raw_for_delta": None,
    "rho_duration_controlled": None,
    "delta_rho": None,
    "n_valid_triple": None,
    "status": "NOT_APPLICABLE_CONTROL_FEATURE",
}
```

Presence of a Task 9 Partial row for a control-feature pair is a blocker.

- [ ] **Step 6: Enforce defined-TF/range semantics**

```python
raw_values = [cross_row[f"rho_{tf}"] for tf in TIMEFRAMES]
defined = [v for v in raw_values if v is not None]
n_defined_tf = len(defined)
assert n_defined_tf + cross_row["n_undefined_tf"] == 4
```

If defined is empty, `rho_min/rho_max/rho_range` must all be `None`. Otherwise reconstruct min/max/range from defined values only and require exact equality with Task 9. Exactly one defined TF may legitimately have `rho_range == 0`, but `n_defined_tf` must remain `1`.

- [ ] **Step 7: Add static no-recompute test**

```python
from pathlib import Path


def test_task10_reports_do_not_recompute_task9_statistics():
    text = Path("research/task10_interpretation_reports.py").read_text("utf-8")
    assert "spearman_pairwise(" not in text
    assert "partial_spearman_duration(" not in text
```

- [ ] **Step 8: Run GREEN and commit**

```bash
pytest -q tests/test_task10_interpretation_reports.py
git add research/task10_interpretation_reports.py tests/test_task10_interpretation_reports.py
git commit -m "feat: build traceable Task 10 main dossiers"
```

---

### Task 4: Supplementary layer, 13 Feature Dossiers, and zero invented hypotheses

**Files:**
- Modify: `research/task10_interpretation_reports.py`
- Modify: `tests/test_task10_interpretation_reports.py`

**Interfaces:**
- `build_supplementary_evidence(bundle) -> list[dict[str, object]]`.
- `build_feature_dossiers(bundle, main_dossiers) -> list[dict[str, object]]`.
- `build_future_ablation_hypotheses() -> list[dict[str, object]]`.

- [ ] **Step 1: Test exact 960-row supplementary boundary**

```python
rows = build_supplementary_evidence(bundle)
assert len(rows) == 960
```

Copy Task 9 values/statuses exactly and add only TF, direction, source artifact, source pair key/locator, `contains_raw_direction_sensitive`, and `is_main_pair`.

- [ ] **Step 2: Test raw-direction-sensitive separation**

Any row containing one of the three raw-direction-sensitive features must have:

```text
is_main_pair = false
evidence_scope = SUPPLEMENTARY_ONLY
```

- [ ] **Step 3: Build exactly 13 Feature Dossiers**

Each feature dossier uses the exact Task 9 keys:

```python
{
    "feature": feature,
    "formula": feature_role_by_name[feature]["formula"],
    "analysis_role": feature_role_by_name[feature]["analysis_role"],
    "direction_semantics": feature_role_by_name[feature]["direction_semantics"],
    "main_relationship_pair_keys": [... exactly 12 ...],
    "future_ablation_hypothesis_ids": [],
}
```

No rank, score, weight, priority, aggregate correlation, or recommendation field.

- [ ] **Step 4: Keep automated hypothesis file empty**

```python
def build_future_ablation_hypotheses() -> list[dict[str, object]]:
    return []
```

- [ ] **Step 5: Run GREEN and commit**

```bash
pytest -q tests/test_task10_interpretation_reports.py
git add research/task10_interpretation_reports.py tests/test_task10_interpretation_reports.py
git commit -m "feat: add Task 10 supplementary and feature dossiers"
```

---

### Task 5: Deterministic outputs, private synthetic orchestration seam, and production provenance gate

**Files:**
- Modify: `research/task10_interpretation_io.py`
- Create: `research/run_task10_dependency_interpretation.py`
- Create: `tests/test_task10_interpretation_integration.py`

**Interfaces:**
- Private test/orchestration seam: `_run_task10_from_bundle(bundle, output_dir, *, implementation_commit, output_zip=None)`.
- Public production entry: `run_task10(input_evidence, output_dir, *, output_zip=None)`.
- Production provenance guard: `assert_clean_committed_task10_worktree() -> str`.

- [ ] **Step 1: Implement provenance guard before any production output**

The guard must run these checks from repository root:

```python
subprocess.run(["git", "diff", "--quiet"], check=True)
subprocess.run(["git", "diff", "--cached", "--quiet"], check=True)
status = subprocess.run(
    ["git", "status", "--porcelain=v1", "--untracked-files=no"],
    check=True,
    capture_output=True,
    text=True,
).stdout
if status:
    raise RuntimeError("tracked worktree is not clean")
```

Then obtain and validate `HEAD`:

```python
head = subprocess.run(
    ["git", "rev-parse", "HEAD"],
    check=True,
    capture_output=True,
    text=True,
).stdout.strip()
if not re.fullmatch(r"[0-9a-f]{40}", head):
    raise RuntimeError("invalid HEAD SHA")
```

Require HEAD to contain all Task 10 production implementation paths:

```python
required_head_paths = (
    "research/task10_interpretation_contract.py",
    "research/task10_interpretation_io.py",
    "research/task10_interpretation_reports.py",
    "research/run_task10_dependency_interpretation.py",
)
for path in required_head_paths:
    subprocess.run(["git", "cat-file", "-e", f"HEAD:{path}"], check=True)
return head
```

Untracked output directories are deliberately ignored; staged or unstaged tracked changes are blockers.

- [ ] **Step 2: Separate public production flow from private synthetic flow**

```python
def _run_task10_from_bundle(
    bundle: Task9EvidenceBundle,
    output_dir: Path,
    *,
    implementation_commit: str,
    output_zip: Path | None = None,
) -> dict[str, object]:
    ...


def run_task10(
    input_evidence: Path,
    output_dir: Path,
    *,
    output_zip: Path | None = None,
) -> dict[str, object]:
    implementation_commit = assert_clean_committed_task10_worktree()
    bundle = load_task9_evidence_package(input_evidence)
    return _run_task10_from_bundle(
        bundle,
        output_dir,
        implementation_commit=implementation_commit,
        output_zip=output_zip,
    )
```

The public function has no loader override, SHA override, bundle override, or implementation-commit override.

- [ ] **Step 3: Fix Synthetic Integration Test seam explicitly**

Synthetic end-to-end tests must **not** call public `run_task10()`.

```python
synthetic_bytes = make_synthetic_task9_evidence_zip(...)
bundle = _load_task9_evidence_bytes(
    synthetic_bytes,
    expected_sha256=hashlib.sha256(synthetic_bytes).hexdigest(),
)
_run_task10_from_bundle(
    bundle,
    output_dir,
    implementation_commit="a" * 40,
    output_zip=output_zip,
)
```

Add a test that `inspect.signature(run_task10)` contains neither `expected_sha256` nor `implementation_commit` nor `loader`.

- [ ] **Step 4: Manifest must use the pre-output validated commit**

`write_task10_outputs()` receives `implementation_commit` as an argument. It must not independently call `git rev-parse` while writing the manifest.

Manifest includes:

```python
{
    "task10_spec_commit": TASK10_SPEC_COMMIT,
    "task10_implementation_commit": implementation_commit,
    "task9_evidence_package_sha256": bundle.evidence_zip_sha256,
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
    "ablation_executed": False,
    "causal_replay_executed": False,
}
```

- [ ] **Step 5: Deterministic writer/repeatability tests**

Write JSON with sorted keys, `allow_nan=False`; CSV with frozen fields and `\n`; ZIP with sorted members, timestamp `(1980,1,1,0,0,0)`, deflate level 9, stable Unix mode. Run the private synthetic seam twice with the same fixed test commit and require all five logical files and both ZIPs byte-identical.

- [ ] **Step 6: CLI has only production-safe arguments**

```python
parser.add_argument("--input-evidence", required=True, type=Path)
parser.add_argument("--output-dir", required=True, type=Path)
parser.add_argument("--output-zip", type=Path)
```

No SHA, loader, bundle, commit, threshold, rank, score, control, method, outcome, or ablation override.

- [ ] **Step 7: Run GREEN and commit**

```bash
pytest -q tests/test_task10_interpretation_integration.py
git add research/task10_interpretation_io.py research/run_task10_dependency_interpretation.py tests/test_task10_interpretation_integration.py
git commit -m "feat: add provenance-safe Task 10 pipeline"
```

---

### Task 6: Non-regression, scope isolation, and implementation verification

**Files:** test/verification only.

- [ ] **Step 1: Run all Task 10 tests**

```bash
pytest -q tests/test_task10_interpretation_contract.py tests/test_task10_interpretation_io.py tests/test_task10_interpretation_reports.py tests/test_task10_interpretation_integration.py
```

- [ ] **Step 2: Run Combined Audit regression**

```bash
pytest -q tests/test_combined_audit_contract.py tests/test_combined_audit_stats.py tests/test_combined_audit_deterministic.py tests/test_combined_audit_reports.py tests/test_combined_audit_io.py tests/test_combined_audit_integration.py
```

- [ ] **Step 3: Run full repository tests**

```bash
pytest -q
```

- [ ] **Step 4: Scope allowlist check against Task 9 registration base**

```bash
git diff --name-only 78e54fb50ce82a0cba7f91f40a6451e82996008d...HEAD
```

Allowed paths are exactly:

```text
docs/superpowers/specs/2026-08-31-task10-dependency-redundancy-interpretation-design.md
docs/superpowers/specs/2026-08-31-task10-dependency-redundancy-interpretation-design.LOCKED.md
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

Any `src/`, `research/combined_audit_*.py`, Task 9 evidence, or unlisted path is a blocker.

- [ ] **Step 5: Static no-recompute/no-unauthorized-scope scan**

Inspect Task 10 implementation for calls to Task 9 statistical primitives and for unauthorized phase implementation. Scope-manifest strings such as `ablation_executed=False` are allowed; actual execution code is not.

- [ ] **Step 6: Verify production provenance guard behavior**

Tests must prove:
- unstaged tracked change → guard fails;
- staged change → guard fails;
- missing Task 10 file from HEAD → guard fails;
- clean tracked tree + all Task 10 files in HEAD → guard returns exact HEAD SHA.

Do not create an empty verification commit.

---

## HUMAN APPROVAL GATE — REQUIRED BEFORE PRODUCTION TASK 10 EXECUTION

After Tasks 1–6 are implemented, reviewed, and verified, stop and report:
- implementation branch and HEAD SHA;
- changed paths versus Task 9 registration base;
- Task 10 test result;
- Combined Audit regression result;
- full repository test result;
- confirmation Task 9 Evidence and `src/` are unchanged;
- confirmation public/CLI production path has no synthetic SHA seam;
- confirmation production provenance guard is green on committed HEAD.

Then wait for explicit human authorization.

**Do not run production Task 10 before this approval.**

**Ablation and Causal Replay remain NOT AUTHORIZED.**

---

### Task 7: Production Task 10 interpretation — ONLY AFTER SEPARATE EXPLICIT AUTHORIZATION

- [ ] **Step 1: Pre-execution provenance gate**

Before reading the canonical ZIP or creating any output, run the public production path's `assert_clean_committed_task10_worktree()` and record its returned HEAD SHA. Any dirty tracked worktree, dirty staging area, or Task 10 implementation path absent from HEAD is a blocker.

- [ ] **Step 2: Independently verify canonical Task 9 Evidence SHA**

Expected exactly:

```text
968f4826858a0bbb8254218711f4ad3e3487370ca8d0f288133ee36f7a4fa40d
```

Mismatch → stop before ZIP parsing.

- [ ] **Step 3: Run public production CLI twice into clean output directories**

Both executions must use only:

```text
--input-evidence
--output-dir
--output-zip
```

No test seam or override is permitted.

- [ ] **Step 4: Byte-compare both runs**

Require all five logical files byte-identical and both deterministic ZIPs byte-identical.

- [ ] **Step 5: Validate locked counts and dossier contracts**

```text
Main Relationship Dossiers          = 78
Partial/delta eligible              = 66
Control-feature non-applicable      = 12
Feature Dossiers                    = 13
Supplementary rows                  = 960
Future Ablation Hypotheses          = 0
Logical files                       = 5
```

Every main dossier must contain all mandatory role/provenance fields and satisfy `n_defined_tf + n_undefined_tf = 4`.

- [ ] **Step 6: Validate manifest provenance**

`task10_implementation_commit` must exactly equal the clean committed HEAD returned before output generation. It must not refer to an earlier commit while executing uncommitted code.

- [ ] **Step 7: Re-run full repository tests, report, and stop**

Report input SHA, implementation SHA, Spec SHA, all gates/counts, repeatability, output ZIP SHA, tests, generated files, and confirmation Task 9/Swing/Leg remain unchanged.

Then stop.

**Ablation → NOT AUTHORIZED**

**Causal Replay → NOT AUTHORIZED**

**Score / Threshold / Feature Selection → NOT AUTHORIZED**

## Plan Self-Review

- [ ] Synthetic Integration does not use the public canonical-SHA loader.
- [ ] Private SHA seam is inaccessible from public `run_task10()` and CLI.
- [ ] Main Dossiers contain all required analysis-role and provenance fields.
- [ ] Feature Role keys are exactly `formula`, `analysis_role`, `direction_semantics`.
- [ ] `direct_deterministic_dependency` has locked co-participation semantics and relation IDs.
- [ ] Lock Record is in scope allowlist.
- [ ] Production requires clean tracked worktree, clean index, and Task 10 files committed at HEAD.
- [ ] Manifest implementation SHA is captured before output from the clean committed state.
- [ ] Counts remain 78 / 66 / 12 / 13 / 960 / 0 / 5.
- [ ] No statistical recomputation, ranking, cutoff, qualitative label, Ablation, or Causal Replay is introduced.
