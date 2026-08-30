# Combined Leg Feature Audit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an audit-only research pipeline that consumes the Final-Locked Leg evidence package and produces deterministic within-TF Spearman, duration-controlled Partial Spearman, deterministic-identity, direction-stratified, and cross-TF consistency reports without changing Swing or Leg Engine behavior.

**Architecture:** Add a small research-only subsystem under `research/` with four responsibilities kept separate: frozen contract/roles, statistical primitives, report construction, and package I/O/CLI. The audit consumes existing locked CSV/manifest evidence from `GOLD_ACTIVITY_AUDIT_PACKAGE_FINAL_LOCKED.zip`; it never imports or recomputes Swing/Leg Engine outputs. Tests use synthetic rows/packages first, then the final task runs the completed audit against the locked Gold package and verifies non-regression and provenance.

**Tech Stack:** Python 3.12, pytest, Python standard library only (`argparse`, `csv`, `dataclasses`, `hashlib`, `itertools`, `json`, `math`, `pathlib`, `statistics`, `subprocess`, `zipfile`). No SciPy/Pandas dependency is required for the statistical core.

**Spec:** `docs/superpowers/specs/2026-08-30-combined-leg-feature-audit-design.md`

## Global Constraints
- Exactly 13 main `ANALYSIS_FEATURE` columns; no fourteenth main feature.
- Primary analysis unit is one timeframe: M5, M15, M30, H1.
- Raw rows across timeframes must never be pooled.
- Deterministic identities are audited separately and take precedence over statistical results.
- Main Raw Spearman uses pairwise-complete `X + Y` observations only.
- Raw Spearman: `n_valid_pairwise < 2 -> UNDEFINED_INSUFFICIENT_OBSERVATIONS`; after that, constant inputs -> `UNDEFINED_CONSTANT_INPUT`.
- Partial Spearman controls only `active_bar_count`.
- Partial Spearman uses exact triple-complete `X + Y + active_bar_count` observations, average tie ranks, ranked OLS residuals with intercept, and requires `n_valid_triple >= 3`.
- `rho_raw_for_delta` is recomputed on the exact triple-complete sample; `delta_rho = rho_duration_controlled - rho_raw_for_delta`.
- No imputation, no silent zero filling, and no undefined correlation coerced to zero.
- Raw direction-sensitive fields are excluded from the combined Bull+Bear main matrix and appear only in same-TF, same-direction supplementary reports.
- Cross-TF output compares independently computed per-TF relationships; sign agreement is descriptive only and ties are explicit.
- Deterministic integer/count identities use exact equality.
- Deterministic `None`/definedness/status identities use exact semantic equality.
- Deterministic floating identities use `math.isclose(..., rel_tol=1e-12, abs_tol=1e-12)`; these values are fixed and recorded in the output manifest.
- No Outcome, Profit/Loss, MFE/MAE, Prediction, Good/Bad, Threshold, Score, Feature Weight, Accept/Reject, Optimization, PCA, Mutual Information, Clustering, qualitative strength label, or causal interpretation.
- Do not modify `src/price_action_ai_swing_v1_locked.py`, `src/price_action_ai_leg_v0.py`, any locked Swing/Leg formula, or historical snapshots.
- Audit implementation must consume locked evidence; it must not import the Swing or Leg Engine to regenerate features.

## Planned File Structure

- Create `research/combined_audit_contract.py` — frozen feature roles, direction semantics, deterministic registry metadata, constants, and output schemas.
- Create `research/combined_audit_stats.py` — average ranks, Pearson, pairwise Spearman, ranked OLS residuals, Partial Spearman, and explicit statuses.
- Create `research/combined_audit_reports.py` — deterministic audit, main per-TF pair reports, supplementary direction-stratified reports, and cross-TF aggregation.
- Create `research/combined_audit_io.py` — locked ZIP/manifest/CSV reader, provenance validation, deterministic CSV/JSON writer, output bundle creation.
- Create `research/run_combined_leg_feature_audit.py` — thin CLI orchestrator only.
- Create `tests/test_combined_audit_contract.py` — exact frozen role/eligibility contract tests.
- Create `tests/test_combined_audit_stats.py` — statistical primitive and edge-case tests.
- Create `tests/test_combined_audit_deterministic.py` — identity/tolerance/zero-denominator tests.
- Create `tests/test_combined_audit_reports.py` — pair counts, no-pooling, direction-stratification, sign accounting, and sample-policy tests.
- Create `tests/test_combined_audit_io.py` — synthetic locked-package/provenance/output determinism tests.
- Create `tests/test_combined_audit_integration.py` — end-to-end synthetic package test without touching production Engine code.

---

### Task 1: Freeze the machine-readable Feature Role Matrix and deterministic registry

**Files:**
- Create: `research/combined_audit_contract.py`
- Create: `tests/test_combined_audit_contract.py`

**Interfaces:**
- Produces: `FeatureSpec` dataclass.
- Produces: `MAIN_FEATURES: tuple[str, ...]` in the exact locked 13-feature order.
- Produces: `RAW_DIRECTION_SENSITIVE: tuple[str, ...]`.
- Produces: `FEATURE_SPECS: dict[str, FeatureSpec]`.
- Produces: `DETERMINISTIC_FLOAT_REL_TOL = 1e-12` and `DETERMINISTIC_FLOAT_ABS_TOL = 1e-12`.
- Produces: `feature_role_rows() -> list[dict[str, object]]` for `FEATURE_ROLE_MATRIX.csv`.
- No dependency on `src/` modules.

- [ ] **Step 1: Write failing contract tests**

```python
from research.combined_audit_contract import (
    DETERMINISTIC_FLOAT_ABS_TOL,
    DETERMINISTIC_FLOAT_REL_TOL,
    FEATURE_SPECS,
    MAIN_FEATURES,
    RAW_DIRECTION_SENSITIVE,
)


def test_main_feature_set_is_exactly_locked_13():
    assert MAIN_FEATURES == (
        "active_bar_count",
        "net_thrust",
        "gross_close_path",
        "net_close_displacement",
        "directional_efficiency",
        "directional_continuity_ratio",
        "close_confirmation_ratio",
        "gap_path_share",
        "body_strength_ratio",
        "shadow_position_imbalance",
        "overlap_ratio",
        "normalized_directional_close_ols_slope",
        "mean_tick_activity",
    )
    assert len(MAIN_FEATURES) == 13


def test_raw_direction_sensitive_fields_are_not_main_features():
    assert RAW_DIRECTION_SENSITIVE == (
        "close_ols_slope",
        "gross_upper_shadow",
        "gross_lower_shadow",
    )
    assert set(RAW_DIRECTION_SENSITIVE).isdisjoint(MAIN_FEATURES)


def test_direction_and_roles_match_locked_contract():
    assert FEATURE_SPECS["net_thrust"].direction_semantics == "DIRECTION_NEUTRAL"
    assert FEATURE_SPECS["net_close_displacement"].direction_semantics == "DIRECTION_NEUTRAL"
    assert FEATURE_SPECS["shadow_position_imbalance"].direction_semantics == "DIRECTION_RELATIVE"
    assert FEATURE_SPECS["close_ols_slope"].analysis_role == "RAW_DIRECTION_SENSITIVE"
    assert FEATURE_SPECS["gross_tick_activity"].analysis_role == "IDENTITY_COMPONENT"
    assert FEATURE_SPECS["mean_candle_range"].analysis_role == "SUPPORTING_COMPONENT"


def test_locked_float_tolerance_is_exact():
    assert DETERMINISTIC_FLOAT_REL_TOL == 1e-12
    assert DETERMINISTIC_FLOAT_ABS_TOL == 1e-12
```

- [ ] **Step 2: Run tests to verify RED**

Run:
```bash
pytest -q tests/test_combined_audit_contract.py
```
Expected: FAIL because `research/combined_audit_contract.py` does not exist.

- [ ] **Step 3: Implement the frozen contract module**

Use this exact shape; populate every locked field from the approved spec, not by inspecting current data distributions:

```python
from dataclasses import dataclass

DETERMINISTIC_FLOAT_REL_TOL = 1e-12
DETERMINISTIC_FLOAT_ABS_TOL = 1e-12
TIMEFRAMES = ("M5", "M15", "M30", "H1")
DIRECTIONS = ("BULLISH", "BEARISH")

MAIN_FEATURES = (
    "active_bar_count",
    "net_thrust",
    "gross_close_path",
    "net_close_displacement",
    "directional_efficiency",
    "directional_continuity_ratio",
    "close_confirmation_ratio",
    "gap_path_share",
    "body_strength_ratio",
    "shadow_position_imbalance",
    "overlap_ratio",
    "normalized_directional_close_ols_slope",
    "mean_tick_activity",
)

RAW_DIRECTION_SENSITIVE = (
    "close_ols_slope",
    "gross_upper_shadow",
    "gross_lower_shadow",
)

@dataclass(frozen=True)
class FeatureSpec:
    feature: str
    formula: str
    sign_semantics: str
    direction_semantics: str
    analysis_role: str
    pairwise_eligible: bool
    controlled_eligible: bool
    stratified_audit_eligible: bool
```

`FEATURE_SPECS` must include main features, supporting/identity components, raw-direction fields, and non-feature fields needed for traceability. `active_bar_count.controlled_eligible` must be `False`. `mean_candle_range` must be present as a derived supporting component and must not appear in `MAIN_FEATURES`.

- [ ] **Step 4: Add deterministic registry metadata constants**

Represent each locked relation with a stable ID and exact formula text so output rows are traceable:

```python
DETERMINISTIC_RELATIONS = (
    "CLOSE_DISPLACEMENT_ABS",
    "CONTINUITY_COUNT_SUM",
    "CONTINUITY_RATIO",
    "BODY_STRENGTH_RATIO",
    "GAP_PATH_SHARE",
    "SHADOW_MAGNITUDE_SUM",
    "SHADOW_POSITION_IMBALANCE",
    "OVERLAP_RATIO",
    "SLOPE_DIRECTION",
    "SLOPE_NORMALIZATION",
    "TICK_ACTIVITY_IDENTITY",
)
```

The Shadow formula string must be exactly directionally consistent with the locked source:

```text
(gross_backward_shadow - gross_forward_shadow) / gross_shadow_magnitude
```

- [ ] **Step 5: Run contract tests to GREEN**

Run:
```bash
pytest -q tests/test_combined_audit_contract.py
```
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add research/combined_audit_contract.py tests/test_combined_audit_contract.py
git commit -m "test: lock Combined Audit feature contract"
```

---

### Task 2: Implement deterministic statistical primitives with exact sample semantics

**Files:**
- Create: `research/combined_audit_stats.py`
- Create: `tests/test_combined_audit_stats.py`

**Interfaces:**
- Consumes: `Sequence[float | int | None]`.
- Produces: `average_ranks(values: Sequence[float]) -> list[float]`.
- Produces: `pearson(values_x, values_y) -> float` for non-constant equal-length numeric sequences.
- Produces: `spearman_pairwise(x, y) -> RawSpearmanResult`.
- Produces: `partial_spearman_duration(x, y, active_bar_count) -> PartialSpearmanResult`.
- Status strings are exactly `DEFINED`, `UNDEFINED_INSUFFICIENT_OBSERVATIONS`, `UNDEFINED_CONSTANT_INPUT`.

- [ ] **Step 1: Write RED tests for average ties and Raw Spearman gates**

```python
from research.combined_audit_stats import average_ranks, spearman_pairwise


def test_average_ranks_use_average_for_ties():
    assert average_ranks([10.0, 20.0, 20.0, 40.0]) == [1.0, 2.5, 2.5, 4.0]


def test_raw_spearman_uses_pairwise_complete_only():
    r = spearman_pairwise(
        [1.0, 2.0, None, 4.0],
        [1.0, None, 3.0, 4.0],
    )
    assert r.n_total == 4
    assert r.n_valid_pairwise == 2
    assert r.n_missing_x == 1
    assert r.n_missing_y == 1
    assert r.status == "DEFINED"
    assert r.rho_raw == 1.0


def test_raw_spearman_insufficient_precedes_constant_check():
    r = spearman_pairwise([1.0, None], [1.0, None])
    assert r.n_valid_pairwise == 1
    assert r.status == "UNDEFINED_INSUFFICIENT_OBSERVATIONS"
    assert r.rho_raw is None


def test_raw_spearman_constant_is_undefined_not_zero():
    r = spearman_pairwise([5.0, 5.0, 5.0], [1.0, 2.0, 3.0])
    assert r.status == "UNDEFINED_CONSTANT_INPUT"
    assert r.rho_raw is None
```

- [ ] **Step 2: Run Raw Spearman tests to verify RED**

Run:
```bash
pytest -q tests/test_combined_audit_stats.py -k "average or raw"
```
Expected: FAIL because statistical functions do not exist.

- [ ] **Step 3: Implement average ranks and Pearson without external libraries**

```python
def average_ranks(values):
    order = sorted(range(len(values)), key=values.__getitem__)
    ranks = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i + 1
        while j < len(order) and values[order[j]] == values[order[i]]:
            j += 1
        average_rank = ((i + 1) + j) / 2.0
        for k in range(i, j):
            ranks[order[k]] = average_rank
        i = j
    return ranks


def pearson(x, y):
    mean_x = sum(x) / len(x)
    mean_y = sum(y) / len(y)
    dx = [v - mean_x for v in x]
    dy = [v - mean_y for v in y]
    numerator = sum(a * b for a, b in zip(dx, dy))
    denominator = math.sqrt(sum(a * a for a in dx) * sum(b * b for b in dy))
    return numerator / denominator
```

Constant detection must occur before calling `pearson`; `pearson` is not allowed to silently return zero for zero variance.

- [ ] **Step 4: Implement `RawSpearmanResult` and pairwise-complete calculation**

```python
@dataclass(frozen=True)
class RawSpearmanResult:
    n_total: int
    n_valid_pairwise: int
    n_missing_x: int
    n_missing_y: int
    rho_raw: float | None
    status: str
```

Pairwise sample is exactly:

```python
pairs = [(a, b) for a, b in zip(x, y) if a is not None and b is not None]
```

Check `len(pairs) < 2` before checking constants.

- [ ] **Step 5: Write RED tests for triple-complete Partial Spearman and `rho_raw_for_delta` separation**

```python
from research.combined_audit_stats import partial_spearman_duration


def test_partial_uses_triple_complete_sample_and_separate_raw_for_delta():
    x = [1.0, 2.0, 3.0, 4.0, 5.0]
    y = [1.0, 5.0, 2.0, 4.0, 3.0]
    duration = [1.0, 2.0, None, 1.0, 3.0]

    main_raw = spearman_pairwise(x, y)
    partial = partial_spearman_duration(x, y, duration)

    assert main_raw.n_valid_pairwise == 5
    assert partial.n_valid_triple == 4
    assert partial.rho_raw_for_delta == spearman_pairwise(
        [1.0, 2.0, 4.0, 5.0],
        [1.0, 5.0, 4.0, 3.0],
    ).rho_raw
    assert partial.rho_raw_for_delta != main_raw.rho_raw


def test_partial_requires_three_triple_complete_observations():
    r = partial_spearman_duration(
        [1.0, 2.0, None],
        [2.0, 1.0, None],
        [1.0, 2.0, None],
    )
    assert r.n_valid_triple == 2
    assert r.status == "UNDEFINED_INSUFFICIENT_OBSERVATIONS"


def test_partial_constant_control_is_undefined():
    r = partial_spearman_duration(
        [1.0, 2.0, 4.0],
        [4.0, 1.0, 3.0],
        [5.0, 5.0, 5.0],
    )
    assert r.status == "UNDEFINED_CONSTANT_INPUT"
```

- [ ] **Step 6: Run Partial tests to verify RED**

Run:
```bash
pytest -q tests/test_combined_audit_stats.py -k partial
```
Expected: FAIL because Partial Spearman is not implemented.

- [ ] **Step 7: Implement ranked OLS residuals with intercept and Partial Spearman**

```python
def residuals_on_control(values, control):
    mean_v = sum(values) / len(values)
    mean_c = sum(control) / len(control)
    dc = [c - mean_c for c in control]
    denom = sum(c * c for c in dc)
    slope = sum((v - mean_v) * c for v, c in zip(values, dc)) / denom
    intercept = mean_v - slope * mean_c
    return [v - (intercept + slope * c) for v, c in zip(values, control)]
```

`partial_spearman_duration` must:
1. build the exact triple-complete sample;
2. gate `n_valid_triple < 3`;
3. rank X, Y, and duration with average ties;
4. gate constant ranked X/Y/control;
5. compute ranked residuals with intercept;
6. gate constant residual X/Y;
7. calculate `rho_raw_for_delta` from X/Y on the same triple sample;
8. calculate residual Pearson as `rho_duration_controlled`;
9. calculate `delta_rho = rho_duration_controlled - rho_raw_for_delta`.

- [ ] **Step 8: Run all statistical tests to GREEN**

Run:
```bash
pytest -q tests/test_combined_audit_stats.py
```
Expected: PASS.

- [ ] **Step 9: Commit**

```bash
git add research/combined_audit_stats.py tests/test_combined_audit_stats.py
git commit -m "feat: add deterministic Spearman audit primitives"
```

---

### Task 3: Implement the Deterministic Identity Auditor

**Files:**
- Create: `tests/test_combined_audit_deterministic.py`
- Modify: `research/combined_audit_reports.py` (create in this task)

**Interfaces:**
- Consumes: one TF's parsed locked Leg rows as `list[dict[str, object]]`.
- Produces: `build_deterministic_identity_report(rows) -> list[dict[str, object]]`.
- One output row per locked identity, with relation ID, formula, conditions, tolerance policy, verified rows, failed rows.

- [ ] **Step 1: Write failing tests for locked Shadow sign and zero-denominator semantics**

```python
from research.combined_audit_reports import build_deterministic_identity_report


def _by_id(report):
    return {row["relation_id"]: row for row in report}


def test_shadow_identity_uses_backward_minus_forward():
    rows = [{
        "gross_forward_shadow": 2.0,
        "gross_backward_shadow": 6.0,
        "gross_shadow_magnitude": 8.0,
        "shadow_position_imbalance": 0.5,
    }]
    result = _by_id(build_deterministic_identity_report(rows))
    assert result["SHADOW_POSITION_IMBALANCE"]["failed_rows"] == 0


def test_zero_shadow_denominator_requires_none_and_is_not_failure():
    rows = [{
        "gross_forward_shadow": 0.0,
        "gross_backward_shadow": 0.0,
        "gross_shadow_magnitude": 0.0,
        "shadow_position_imbalance": None,
    }]
    result = _by_id(build_deterministic_identity_report(rows))
    assert result["SHADOW_POSITION_IMBALANCE"]["verified_rows"] == 1
    assert result["SHADOW_POSITION_IMBALANCE"]["failed_rows"] == 0
```

- [ ] **Step 2: Add tests for count exactness, slope chain, ratio `None`, and Activity identity**

```python
def test_count_identity_uses_exact_equality():
    rows = [{
        "aligned_close_steps": 3,
        "opposing_close_steps": 1,
        "flat_close_steps": 1,
        "active_bar_count": 5,
    }]
    result = _by_id(build_deterministic_identity_report(rows))
    assert result["CONTINUITY_COUNT_SUM"]["failed_rows"] == 0


def test_slope_normalization_matches_source_defined_chain():
    rows = [{
        "active_bar_count": 4,
        "gross_candle_range": 20.0,
        "close_ols_slope": -2.0,
        "direction": "BEARISH",
        "directional_close_ols_slope": 2.0,
        "normalized_directional_close_ols_slope": 0.4,
    }]
    result = _by_id(build_deterministic_identity_report(rows))
    assert result["SLOPE_DIRECTION"]["failed_rows"] == 0
    assert result["SLOPE_NORMALIZATION"]["failed_rows"] == 0


def test_tick_activity_identity_uses_locked_float_tolerance():
    rows = [{
        "gross_tick_activity": 3001,
        "mean_tick_activity": 1000.3333333333334,
        "active_bar_count": 3,
    }]
    result = _by_id(build_deterministic_identity_report(rows))
    assert result["TICK_ACTIVITY_IDENTITY"]["failed_rows"] == 0
```

- [ ] **Step 3: Run tests to verify RED**

Run:
```bash
pytest -q tests/test_combined_audit_deterministic.py
```
Expected: FAIL because report builder does not exist.

- [ ] **Step 4: Implement exact semantic comparison helpers**

```python
def _float_equal(expected, observed):
    return math.isclose(
        float(expected),
        float(observed),
        rel_tol=DETERMINISTIC_FLOAT_REL_TOL,
        abs_tol=DETERMINISTIC_FLOAT_ABS_TOL,
    )


def _optional_float_equal(expected, observed):
    if expected is None or observed is None:
        return expected is None and observed is None
    return _float_equal(expected, observed)
```

Integer/count comparison uses `expected == observed` with no tolerance. `None` semantics use identity/definedness equality, not numeric replacement.

- [ ] **Step 5: Implement all 11 locked identities**

The reconstruction logic must use these exact formulas/conditions:

```text
CLOSE_DISPLACEMENT_ABS:
net_close_displacement = abs(signed_close_displacement)

CONTINUITY_COUNT_SUM:
aligned_close_steps + opposing_close_steps + flat_close_steps = active_bar_count

CONTINUITY_RATIO:
active_bar_count > 0 -> aligned_close_steps / active_bar_count

BODY_STRENGTH_RATIO:
gross_candle_range > 0 -> gross_body_magnitude / gross_candle_range
else None

GAP_PATH_SHARE:
gross_close_path > 0 -> gap_path_contribution / gross_close_path
else None

SHADOW_MAGNITUDE_SUM:
gross_forward_shadow + gross_backward_shadow = gross_shadow_magnitude

SHADOW_POSITION_IMBALANCE:
gross_shadow_magnitude > 0 ->
(gross_backward_shadow - gross_forward_shadow) / gross_shadow_magnitude
else None

OVERLAP_RATIO:
gross_overlap_capacity > 0 -> gross_overlap_magnitude / gross_overlap_capacity
else None

SLOPE_DIRECTION:
direction_sign = +1 BULLISH, -1 BEARISH
directional_close_ols_slope = direction_sign * close_ols_slope

SLOPE_NORMALIZATION:
active_bar_count > 0 -> mean_candle_range = gross_candle_range / active_bar_count
mean_candle_range > 0 -> directional_close_ols_slope / mean_candle_range
else None

TICK_ACTIVITY_IDENTITY:
gross_tick_activity = mean_tick_activity * active_bar_count
```

Rows lacking an identity's required source fields because the source value is legitimately missing must be evaluated by the identity's locked `None` semantics; do not fill missing values with zero.

- [ ] **Step 6: Run deterministic tests to GREEN**

Run:
```bash
pytest -q tests/test_combined_audit_deterministic.py
```
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add research/combined_audit_reports.py tests/test_combined_audit_deterministic.py
git commit -m "feat: add deterministic Leg identity audit"
```

---

### Task 4: Build per-timeframe Main Raw and Partial Spearman reports

**Files:**
- Modify: `research/combined_audit_reports.py`
- Create: `tests/test_combined_audit_reports.py`

**Interfaces:**
- Consumes: one TF's list of parsed Leg rows.
- Produces: `build_main_spearman_report(rows) -> list[dict[str, object]]`.
- Produces: `build_partial_spearman_report(rows) -> list[dict[str, object]]`.
- Pair order is deterministic: combinations of `MAIN_FEATURES` in frozen feature order.

- [ ] **Step 1: Write failing tests for pair universe and exclusion rules**

```python
from research.combined_audit_contract import MAIN_FEATURES
from research.combined_audit_reports import (
    build_main_spearman_report,
    build_partial_spearman_report,
)


def test_main_report_contains_exactly_13_choose_2_pairs(sample_leg_rows):
    report = build_main_spearman_report(sample_leg_rows)
    assert len(report) == 78
    seen = {(r["feature_x"], r["feature_y"]) for r in report}
    assert ("active_bar_count", "net_thrust") in seen
    assert all("gross_tick_activity" not in pair for pair in seen)
    assert all("close_ols_slope" not in pair for pair in seen)


def test_partial_report_excludes_pairs_with_control_variable(sample_leg_rows):
    report = build_partial_spearman_report(sample_leg_rows)
    assert len(report) == 66
    assert all(r["feature_x"] != "active_bar_count" for r in report)
    assert all(r["feature_y"] != "active_bar_count" for r in report)
```

- [ ] **Step 2: Write tests for pairwise missing counts and triple-complete delta semantics**

```python
def test_main_report_preserves_pairwise_missing_counts(sample_leg_rows):
    rows = [dict(r) for r in sample_leg_rows]
    rows[0]["overlap_ratio"] = None
    result = next(
        r for r in build_main_spearman_report(rows)
        if r["feature_x"] == "body_strength_ratio" and r["feature_y"] == "overlap_ratio"
    )
    assert result["n_total"] == len(rows)
    assert result["n_missing_y"] == 1
    assert result["n_valid_pairwise"] == len(rows) - 1


def test_partial_report_uses_rho_raw_for_delta_not_main_raw(sample_leg_rows):
    rows = [dict(r) for r in sample_leg_rows]
    rows[0]["active_bar_count"] = None
    main = next(
        r for r in build_main_spearman_report(rows)
        if r["feature_x"] == "net_thrust" and r["feature_y"] == "mean_tick_activity"
    )
    partial = next(
        r for r in build_partial_spearman_report(rows)
        if r["feature_x"] == "net_thrust" and r["feature_y"] == "mean_tick_activity"
    )
    assert partial["n_valid_triple"] == main["n_valid_pairwise"] - 1
    assert "rho_raw_for_delta" in partial
```

- [ ] **Step 3: Run report tests to verify RED**

Run:
```bash
pytest -q tests/test_combined_audit_reports.py -k "main or partial"
```
Expected: FAIL because report functions are not implemented.

- [ ] **Step 4: Implement deterministic pair iteration and column extraction**

```python
from itertools import combinations


def _column(rows, name):
    return [row.get(name) for row in rows]


def build_main_spearman_report(rows):
    output = []
    for feature_x, feature_y in combinations(MAIN_FEATURES, 2):
        result = spearman_pairwise(_column(rows, feature_x), _column(rows, feature_y))
        output.append({
            "feature_x": feature_x,
            "feature_y": feature_y,
            "n_total": result.n_total,
            "n_valid_pairwise": result.n_valid_pairwise,
            "n_missing_x": result.n_missing_x,
            "n_missing_y": result.n_missing_y,
            "rho_raw": result.rho_raw,
            "status": result.status,
        })
    return output
```

- [ ] **Step 5: Implement the 66-row Partial report**

Use `MAIN_FEATURES[1:]` as the controlled pair universe only because `active_bar_count` is the first locked feature and cannot be X or Y in Partial Spearman. Do not infer this exclusion from data.

Each row must contain:

```python
{
    "feature_x": feature_x,
    "feature_y": feature_y,
    "rho_raw_for_delta": result.rho_raw_for_delta,
    "rho_duration_controlled": result.rho_duration_controlled,
    "delta_rho": result.delta_rho,
    "n_valid_triple": result.n_valid_triple,
    "status": result.status,
}
```

- [ ] **Step 6: Run Main/Partial tests to GREEN**

Run:
```bash
pytest -q tests/test_combined_audit_reports.py -k "main or partial"
```
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add research/combined_audit_reports.py tests/test_combined_audit_reports.py
git commit -m "feat: add per-TF Combined Audit pair reports"
```

---

### Task 5: Add supplementary Bull/Bear stratification and Cross-TF consistency

**Files:**
- Modify: `research/combined_audit_reports.py`
- Modify: `tests/test_combined_audit_reports.py`

**Interfaces:**
- Produces: `build_direction_stratified_report(rows, direction) -> dict[str, list[dict[str, object]]]` with `raw` and `partial` tables.
- Produces: `build_cross_tf_relationship_report(main_by_tf, partial_by_tf) -> list[dict[str, object]]`.
- Supplementary universe = `MAIN_FEATURES + RAW_DIRECTION_SENSITIVE`, same TF and same direction only.

- [ ] **Step 1: Write failing stratification tests**

```python
def test_direction_stratified_report_never_mixes_bull_and_bear(sample_leg_rows):
    bullish = build_direction_stratified_report(sample_leg_rows, "BULLISH")
    bearish = build_direction_stratified_report(sample_leg_rows, "BEARISH")
    assert bullish["source_row_count"] == sum(r["direction"] == "BULLISH" for r in sample_leg_rows)
    assert bearish["source_row_count"] == sum(r["direction"] == "BEARISH" for r in sample_leg_rows)


def test_raw_direction_fields_exist_only_in_supplementary_pairs(sample_leg_rows):
    supplementary = build_direction_stratified_report(sample_leg_rows, "BULLISH")
    pairs = {(r["feature_x"], r["feature_y"]) for r in supplementary["raw"]}
    assert any("close_ols_slope" in pair for pair in pairs)
    assert any("gross_upper_shadow" in pair for pair in pairs)
    assert any("gross_lower_shadow" in pair for pair in pairs)
```

The supplementary raw universe has 16 eligible numeric fields, therefore exactly `16 choose 2 = 120` rows per TF/direction. The supplementary Partial universe excludes `active_bar_count`, therefore exactly `15 choose 2 = 105` rows per TF/direction. These rows are all tagged `evidence_scope = SUPPLEMENTARY_ONLY`.

- [ ] **Step 2: Write failing Cross-TF sign-accounting tests**

```python
def test_cross_tf_sign_accounting_reports_tie_without_picking_sign():
    main_by_tf = {
        "M5": [{"feature_x": "a", "feature_y": "b", "rho_raw": 0.2, "status": "DEFINED", "n_valid_pairwise": 10}],
        "M15": [{"feature_x": "a", "feature_y": "b", "rho_raw": -0.3, "status": "DEFINED", "n_valid_pairwise": 11}],
        "M30": [{"feature_x": "a", "feature_y": "b", "rho_raw": 0.0, "status": "DEFINED", "n_valid_pairwise": 12}],
        "H1": [{"feature_x": "a", "feature_y": "b", "rho_raw": None, "status": "UNDEFINED_CONSTANT_INPUT", "n_valid_pairwise": 13}],
    }
    row = build_cross_tf_relationship_report(main_by_tf, {tf: [] for tf in main_by_tf})[0]
    assert row["n_positive_tf"] == 1
    assert row["n_negative_tf"] == 1
    assert row["n_zero_tf"] == 1
    assert row["n_undefined_tf"] == 1
    assert row["sign_agreement_count"] == 1
    assert row["sign_agreement_tie"] is True
    assert row["sign_agreement_modal_signs"] == ["NEGATIVE", "POSITIVE", "ZERO"]


def test_cross_tf_range_ignores_undefined_not_zero():
    # Uses the same fixture: defined raw rhos are -0.3, 0.0, 0.2.
    row = build_cross_tf_relationship_report(main_by_tf, {tf: [] for tf in main_by_tf})[0]
    assert row["rho_min"] == -0.3
    assert row["rho_max"] == 0.2
    assert math.isclose(row["rho_range"], 0.5)
```

- [ ] **Step 3: Run supplementary/cross-TF tests to verify RED**

Run:
```bash
pytest -q tests/test_combined_audit_reports.py -k "stratified or cross_tf"
```
Expected: FAIL because these report builders are not implemented.

- [ ] **Step 4: Implement same-direction filtering before any pair calculation**

```python
eligible = MAIN_FEATURES + RAW_DIRECTION_SENSITIVE
subset = [row for row in rows if row.get("direction") == direction]
```

Raw and Partial statistics then operate only on `subset`. Never calculate over all rows and filter results afterward.

- [ ] **Step 5: Implement Cross-TF merge by pair key, not by row position**

```python
pair_key = (row["feature_x"], row["feature_y"])
```

For every one of the 78 main pairs, attach M5/M15/M30/H1 independently computed raw values. For the 66 controlled-eligible pairs, attach independently computed Partial values; for the 12 pairs involving `active_bar_count`, controlled values remain `None` and `controlled_eligible = False`.

Sign accounting uses raw `rho_TF` only:

```python
positive = sum(v is not None and v > 0 for v in raw_values)
negative = sum(v is not None and v < 0 for v in raw_values)
zero = sum(v is not None and v == 0 for v in raw_values)
undefined = sum(v is None for v in raw_values)
```

If all four values are undefined, leave `sign_agreement_count`, `sign_agreement_tie`, `sign_agreement_modal_signs`, `rho_min`, `rho_max`, and `rho_range` as `None`.

- [ ] **Step 6: Run report tests to GREEN**

Run:
```bash
pytest -q tests/test_combined_audit_reports.py
```
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add research/combined_audit_reports.py tests/test_combined_audit_reports.py
git commit -m "feat: add stratified and cross-TF audit reports"
```

---

### Task 6: Read the Final-Locked Activity package and write deterministic audit artifacts

**Files:**
- Create: `research/combined_audit_io.py`
- Create: `tests/test_combined_audit_io.py`

**Interfaces:**
- Consumes: path to `GOLD_ACTIVITY_AUDIT_PACKAGE_FINAL_LOCKED.zip`.
- Produces: `AuditInputBundle(manifest, rows_by_tf, input_zip_sha256, snapshot_sha256_by_tf)`.
- Produces: `load_locked_activity_package(path: Path) -> AuditInputBundle`.
- Produces: deterministic `write_csv`, `write_json`, and `write_output_bundle` helpers.

- [ ] **Step 1: Write failing package-loader tests with a synthetic ZIP**

Create the synthetic ZIP in pytest's `tmp_path`; do not add binary fixtures to the repo.

```python
def test_loader_requires_final_lock_status(tmp_path):
    package = make_synthetic_activity_zip(tmp_path, status="LOCK CANDIDATE")
    with pytest.raises(ValueError, match="FINAL LOCK / PASS"):
        load_locked_activity_package(package)


def test_loader_uses_manifest_csv_names_and_preserves_tf_separation(tmp_path):
    package = make_synthetic_activity_zip(tmp_path, status="FINAL LOCK / PASS")
    bundle = load_locked_activity_package(package)
    assert tuple(bundle.rows_by_tf) == ("M5", "M15", "M30", "H1")
    assert bundle.rows_by_tf["M5"] is not bundle.rows_by_tf["M15"]
```

- [ ] **Step 2: Add provenance tests for snapshot hashes and locked source metadata**

The synthetic manifest follows the real package shape:

```json
{
  "status": "FINAL LOCK / PASS",
  "current_commit": "b43ed7a6d1d8538d8860934abbb24b0c9561a317",
  "broker_company": "LiteFinance Global LLC",
  "broker_server": "LiteFinance-MT5-Live",
  "timeframes": {
    "M5": {"symbol": "XAUUSD_o", "timeframe": "M5", "csv": "M5.csv", "snapshot_file": "M5_snapshot.csv", "snapshot_sha256": "..."}
  }
}
```

Test that a mismatched snapshot hash raises an explicit `ValueError` rather than continuing.

- [ ] **Step 3: Run I/O tests to verify RED**

Run:
```bash
pytest -q tests/test_combined_audit_io.py
```
Expected: FAIL because I/O helpers do not exist.

- [ ] **Step 4: Implement CSV parsing with explicit numeric/None conversion**

Parse `""` as `None`. Parse known integer fields (`leg_no`, indexes, count fields, `gross_tick_activity`) as `int`. Parse locked numeric measurement fields as `float`. Parse `direction` and categorical/metadata as strings. Do not parse diagnostic `True/False` columns as features.

The loader must source per-TF leg CSV names from `manifest["timeframes"][tf]["csv"]`; it must not discover/merge arbitrary CSV files by glob.

- [ ] **Step 5: Implement package and snapshot SHA verification**

```python
def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()
```

For each TF, read the exact `snapshot_file` named by the manifest and require its SHA-256 to equal `snapshot_sha256`. Record the entire input ZIP SHA-256 separately for provenance. This validates input integrity; it does not recompute Swing or Leg metrics.

- [ ] **Step 6: Implement deterministic writers**

CSV field order is supplied explicitly per report. JSON uses:

```python
json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
```

Do not insert current timestamps into output artifacts; identical inputs/code should produce byte-stable logical report content.

- [ ] **Step 7: Run I/O tests to GREEN**

Run:
```bash
pytest -q tests/test_combined_audit_io.py
```
Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add research/combined_audit_io.py tests/test_combined_audit_io.py
git commit -m "feat: add locked audit-package I/O"
```

---

### Task 7: Add the CLI orchestrator and end-to-end synthetic integration test

**Files:**
- Create: `research/run_combined_leg_feature_audit.py`
- Create: `tests/test_combined_audit_integration.py`
- Modify: `research/combined_audit_io.py`

**Interfaces:**
- CLI:

```bash
python research/run_combined_leg_feature_audit.py \
  --input-zip /path/to/GOLD_ACTIVITY_AUDIT_PACKAGE_FINAL_LOCKED.zip \
  --output-dir /path/to/combined_audit_output
```

- Produces audit-only files; does not write into or mutate the input ZIP.

- [ ] **Step 1: Write a failing end-to-end test**

```python
def test_end_to_end_synthetic_package_writes_all_required_artifacts(tmp_path):
    input_zip = make_four_tf_synthetic_locked_package(tmp_path)
    output_dir = tmp_path / "out"
    rc = main(["--input-zip", str(input_zip), "--output-dir", str(output_dir)])
    assert rc == 0

    expected = {
        "FEATURE_ROLE_MATRIX.csv",
        "DETERMINISTIC_IDENTITY_REPORT.csv",
        "MAIN_SPEARMAN_M5.csv",
        "MAIN_SPEARMAN_M15.csv",
        "MAIN_SPEARMAN_M30.csv",
        "MAIN_SPEARMAN_H1.csv",
        "PARTIAL_SPEARMAN_M5.csv",
        "PARTIAL_SPEARMAN_M15.csv",
        "PARTIAL_SPEARMAN_M30.csv",
        "PARTIAL_SPEARMAN_H1.csv",
        "CROSS_TF_RELATIONSHIP_REPORT.csv",
        "COMBINED_AUDIT_MANIFEST.json",
    }
    assert expected.issubset({p.name for p in output_dir.iterdir()})
```

Also require eight supplementary files:

```text
SUPPLEMENTARY_M5_BULLISH.csv
SUPPLEMENTARY_M5_BEARISH.csv
SUPPLEMENTARY_M15_BULLISH.csv
SUPPLEMENTARY_M15_BEARISH.csv
SUPPLEMENTARY_M30_BULLISH.csv
SUPPLEMENTARY_M30_BEARISH.csv
SUPPLEMENTARY_H1_BULLISH.csv
SUPPLEMENTARY_H1_BEARISH.csv
```

Each supplementary CSV contains both raw and controlled fields in one row schema, with `evidence_scope=SUPPLEMENTARY_ONLY`; `rho_duration_controlled` is `None` for pairs containing `active_bar_count`.

- [ ] **Step 2: Add manifest assertions**

```python
manifest = json.loads((output_dir / "COMBINED_AUDIT_MANIFEST.json").read_text())
assert manifest["analysis_feature_count"] == 13
assert manifest["timeframes"] == ["M5", "M15", "M30", "H1"]
assert manifest["raw_cross_tf_pooling"] is False
assert manifest["control_variable"] == "active_bar_count"
assert manifest["deterministic_float_rel_tol"] == 1e-12
assert manifest["deterministic_float_abs_tol"] == 1e-12
assert manifest["input_locked_leg_source_commit"] == "b43ed7a6d1d8538d8860934abbb24b0c9561a317"
```

The manifest must also record input ZIP SHA-256, broker/server, symbol per TF, snapshot hashes, audit code commit, and exact report filenames.

- [ ] **Step 3: Run integration test to verify RED**

Run:
```bash
pytest -q tests/test_combined_audit_integration.py
```
Expected: FAIL because CLI orchestration/output writing is incomplete.

- [ ] **Step 4: Implement orchestration without Engine imports**

The CLI flow is exactly:

```python
bundle = load_locked_activity_package(input_zip)
feature_roles = feature_role_rows()
for tf in TIMEFRAMES:
    rows = bundle.rows_by_tf[tf]
    deterministic[tf] = build_deterministic_identity_report(rows)
    main[tf] = build_main_spearman_report(rows)
    partial[tf] = build_partial_spearman_report(rows)
    for direction in DIRECTIONS:
        supplementary[(tf, direction)] = build_direction_stratified_report(rows, direction)
cross_tf = build_cross_tf_relationship_report(main, partial)
write_output_bundle(...)
```

`research/run_combined_leg_feature_audit.py` must not import `price_action_ai_leg_v0`, Swing code, MT5, Plotly, or any outcome/strategy module.

- [ ] **Step 5: Define deterministic output aggregation**

`DETERMINISTIC_IDENTITY_REPORT.csv` contains a `timeframe` column plus the per-identity fields so all four TFs are represented without pooling row-level observations. This is report concatenation of already independent identity results, not statistical pooling.

`CROSS_TF_RELATIONSHIP_REPORT.csv` contains exactly 78 main pair rows.

- [ ] **Step 6: Run all new Combined Audit tests**

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
Expected: all PASS.

- [ ] **Step 7: Commit**

```bash
git add \
  research/run_combined_leg_feature_audit.py \
  research/combined_audit_io.py \
  tests/test_combined_audit_integration.py
git commit -m "feat: add Combined Audit research runner"
```

---

### Task 8: Prove production non-regression before any Gold audit run

**Files:**
- No production file modifications.
- Verification only.

**Interfaces:**
- Consumes: implementation branch after Tasks 1-7.
- Produces: fresh test output and Git diff evidence showing audit-only changes.

- [ ] **Step 1: Run locked Leg metric regressions**

Run:
```bash
pytest -q \
  tests/test_leg_v0_baseline.py \
  tests/test_directional_continuity.py \
  tests/test_body_strength.py \
  tests/test_shadow_position.py \
  tests/test_overlap.py \
  tests/test_slope.py \
  tests/test_activity.py
```
Expected: all selected locked Leg tests PASS with zero failures.

- [ ] **Step 2: Run the full Combined Audit test suite again**

Run:
```bash
pytest -q tests/test_combined_audit_*.py
```
Expected: all PASS with zero failures.

- [ ] **Step 3: Verify no production source changed**

Run:
```bash
git diff --name-only b43ed7a6d1d8538d8860934abbb24b0c9561a317...HEAD
```
Expected changed paths are limited to:

```text
docs/superpowers/specs/2026-08-30-combined-leg-feature-audit-design.md
docs/superpowers/plans/2026-08-30-combined-leg-feature-audit.md
research/combined_audit_contract.py
research/combined_audit_stats.py
research/combined_audit_reports.py
research/combined_audit_io.py
research/run_combined_leg_feature_audit.py
tests/test_combined_audit_contract.py
tests/test_combined_audit_stats.py
tests/test_combined_audit_deterministic.py
tests/test_combined_audit_reports.py
tests/test_combined_audit_io.py
tests/test_combined_audit_integration.py
```

Any `src/` change is a blocker. Stop and open a separate Change Request rather than continuing.

- [ ] **Step 4: Record implementation commit**

Run:
```bash
git rev-parse HEAD
```
Use that exact SHA as `audit_code_commit` when the Gold audit is executed in Task 9.

---

### Task 9: Execute the Combined Audit on the Final-Locked Gold package and harden the evidence bundle

**Files:**
- Input only: `GOLD_ACTIVITY_AUDIT_PACKAGE_FINAL_LOCKED.zip`
- Generate locally under a clean output directory; do not commit generated Gold audit CSV/ZIP artifacts unless separately requested.

**Interfaces:**
- Consumes the exact Final-Locked Activity package with M5/M15/M30/H1 locked Leg CSVs and snapshots.
- Produces `GOLD_COMBINED_LEG_FEATURE_AUDIT_PACKAGE.zip` plus the logical report files required by the spec.

- [ ] **Step 1: Verify the input package SHA before running**

Run:
```bash
python - <<'PY'
from hashlib import sha256
from pathlib import Path
p = Path("GOLD_ACTIVITY_AUDIT_PACKAGE_FINAL_LOCKED.zip")
print(sha256(p.read_bytes()).hexdigest())
PY
```
Expected for the currently Final-Locked package:

```text
1e9f13fd88fc1e8e0e66d801be8c15d726639eaea25e53fef7c3bb88bfd05192
```

If the hash differs, stop and identify which approved locked package is being used before running the audit.

- [ ] **Step 2: Run the audit once into a clean directory**

```bash
python research/run_combined_leg_feature_audit.py \
  --input-zip GOLD_ACTIVITY_AUDIT_PACKAGE_FINAL_LOCKED.zip \
  --output-dir GOLD_COMBINED_LEG_FEATURE_AUDIT
```

Expected logical outputs:
- 1 Feature Role Matrix;
- 1 combined Deterministic Identity Report with four TF labels;
- 4 Main Raw Spearman reports, each 78 pair rows;
- 4 Partial Spearman reports, each 66 pair rows;
- 8 supplementary direction-stratified reports;
- 1 Cross-TF report with 78 pair rows;
- 1 provenance Manifest.

- [ ] **Step 3: Verify real-data row counts without interpreting correlation magnitudes**

Use a verification script that only checks schemas/counts/status domains:

```python
assert main_rows_per_tf == {"M5": 78, "M15": 78, "M30": 78, "H1": 78}
assert partial_rows_per_tf == {"M5": 66, "M15": 66, "M30": 66, "H1": 66}
assert cross_tf_rows == 78
assert manifest["analysis_feature_count"] == 13
assert manifest["raw_cross_tf_pooling"] is False
```

Do not add `STRONG`, `WEAK`, `STABLE`, `UNSTABLE`, `REDUNDANT`, or `ORTHOGONAL` labels during review.

- [ ] **Step 4: Verify every deterministic identity row has zero failures**

Acceptance criterion:

```text
failed_rows = 0
```

for every identity in every TF. Any deterministic failure blocks the Combined Audit and must be investigated before statistical results are interpreted.

- [ ] **Step 5: Verify Partial sample discipline on every controlled row**

For each Partial report row, independently check:

```text
rho_raw_for_delta uses exactly n_valid_triple rows
rho_duration_controlled uses exactly the same n_valid_triple rows
delta_rho = rho_duration_controlled - rho_raw_for_delta
```

Undefined rows must preserve the explicit status and must not contain fabricated zero correlations.

- [ ] **Step 6: Verify Cross-TF sign accounting and range semantics**

For each of 78 pairs independently reconstruct:

```text
n_positive_tf
n_negative_tf
n_zero_tf
n_undefined_tf
sign_agreement_count
sign_agreement_tie
sign_agreement_modal_signs
rho_min
rho_max
rho_range
```

Only defined raw per-TF rho values enter min/max/range and positive/negative/zero counts.

- [ ] **Step 7: Re-run the audit into a second clean directory and compare deterministic content**

```bash
python research/run_combined_leg_feature_audit.py \
  --input-zip GOLD_ACTIVITY_AUDIT_PACKAGE_FINAL_LOCKED.zip \
  --output-dir GOLD_COMBINED_LEG_FEATURE_AUDIT_RERUN
```

Compare all generated CSV/JSON report bytes. They must match exactly between runs because no runtime timestamp or adaptive tolerance is allowed.

- [ ] **Step 8: Create the final evidence ZIP**

Archive only the generated Combined Audit artifacts, not modified copies of Engine/Swing source:

```bash
python - <<'PY'
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile
src = Path("GOLD_COMBINED_LEG_FEATURE_AUDIT")
out = Path("GOLD_COMBINED_LEG_FEATURE_AUDIT_PACKAGE.zip")
with ZipFile(out, "w", compression=ZIP_DEFLATED) as z:
    for p in sorted(src.iterdir(), key=lambda x: x.name):
        z.write(p, arcname=p.name)
print(out)
PY
```

- [ ] **Step 9: Verify ZIP integrity and calculate final SHA-256**

```bash
python - <<'PY'
from hashlib import sha256
from pathlib import Path
from zipfile import ZipFile
p = Path("GOLD_COMBINED_LEG_FEATURE_AUDIT_PACKAGE.zip")
with ZipFile(p) as z:
    assert z.testzip() is None
print(sha256(p.read_bytes()).hexdigest())
PY
```

Only after Tasks 8 and 9 have fresh passing evidence may the Combined Audit itself be presented for research review. Passing implementation tests alone does not authorize a statistical conclusion or Causal Replay transition.

---

## Final Verification Checklist

Before declaring implementation complete, verify all of the following with fresh evidence:

- [ ] Design Spec SHA/branch is the approved Final-Locked version.
- [ ] `MAIN_FEATURES` is exactly 13 and machine-tested.
- [ ] No supporting/identity/raw-direction field enters the main 78-pair matrix.
- [ ] Main Raw Spearman uses pairwise-complete samples and exact status precedence.
- [ ] Partial Spearman uses triple-complete samples, average tie ranks, intercept residualization, `n_valid_triple >= 3`, and separate `rho_raw_for_delta`.
- [ ] Deterministic identities use exact integer/status semantics and fixed `1e-12` float tolerances.
- [ ] Shadow identity is `backward - forward` and zero-total returns `None`.
- [ ] Slope direction and normalization reproduce the exact locked Source-defined chain.
- [ ] Supplementary direction-sensitive analysis is same-TF and same-direction only.
- [ ] Cross-TF output never pools raw observations and reports sign ties/undefined values explicitly.
- [ ] No qualitative correlation labels are emitted.
- [ ] No Outcome, Score, Threshold, Prediction, Optimization, or Causal claim is emitted.
- [ ] Locked Leg tests pass freshly.
- [ ] Combined Audit tests pass freshly.
- [ ] `git diff` shows no `src/` modifications.
- [ ] Gold run is repeatable byte-for-byte for generated CSV/JSON logical artifacts.
- [ ] Final evidence ZIP integrity passes and SHA-256 is recorded.
