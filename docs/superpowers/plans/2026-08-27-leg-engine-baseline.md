# Confirmed Leg Baseline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the minimum confirmed Leg Engine from locked Major Swing pairs with five baseline measurements and explicit upstream invariant errors.

**Architecture:** Add a dedicated Leg module that consumes already-produced Major Swings and never mutates Swing logic. Keep confirmed-Leg construction separate from future quality/classification work. Regression must always run both Swing v1 and Leg baseline tests.

**Tech Stack:** Python 3.12, pytest, existing PriceActionAI Swing v1 module.

**Spec:** `docs/superpowers/specs/2026-08-27-leg-engine-baseline-design.md`

## Global Constraints
- Swing v1 is locked upstream and must not be modified.
- Major Swings define confirmed Leg boundaries.
- Structural/Internal Swings do not create primary Legs.
- `active_bar_count = end_index - start_index`.
- `net_thrust = abs(end_price - start_price)`.
- Same-type consecutive Major Swings produce `UPSTREAM_SWING_INVARIANT_ERROR` and no fabricated Leg.
- No Trend/Range/Quality logic in this baseline.

---

### Task 1: Confirmed Leg data contract and builder

**Files:**
- Create: `src/price_action_ai_leg_v0.py`
- Test: `tests/test_leg_v0_baseline.py`

**Interfaces:**
- Consumes: `list[dict]` Major Swings containing `index`, `kind`, `price` and optional `time` / `segment_id`.
- Produces: `build_confirmed_legs(major_swings) -> LegBuildResult`.
- Produces: `ConfirmedLeg(start, end, direction, active_bar_count, net_thrust)`.
- Produces: `LegBuildError(code, pair_index, left, right)`.

- [ ] **Step 1: Write failing tests**

```python
def test_builds_bullish_leg():
    result = build_confirmed_legs([
        {"index": 10, "kind": "SL", "price": 100.0},
        {"index": 15, "kind": "SH", "price": 130.0},
    ])
    assert len(result.legs) == 1
    leg = result.legs[0]
    assert leg.direction == "BULLISH"
    assert leg.active_bar_count == 5
    assert leg.net_thrust == 30.0


def test_builds_bearish_leg():
    result = build_confirmed_legs([
        {"index": 20, "kind": "SH", "price": 130.0},
        {"index": 28, "kind": "SL", "price": 110.0},
    ])
    leg = result.legs[0]
    assert leg.direction == "BEARISH"
    assert leg.active_bar_count == 8
    assert leg.net_thrust == 20.0


def test_same_type_major_swings_surface_upstream_error():
    result = build_confirmed_legs([
        {"index": 10, "kind": "SL", "price": 100.0},
        {"index": 15, "kind": "SL", "price": 95.0},
    ])
    assert result.legs == []
    assert result.errors[0].code == "UPSTREAM_SWING_INVARIANT_ERROR"
```

- [ ] **Step 2: Run test to verify RED**

Run: `pytest -q tests/test_leg_v0_baseline.py`
Expected: FAIL because `src/price_action_ai_leg_v0.py` does not exist.

- [ ] **Step 3: Implement minimum builder**

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class ConfirmedLeg:
    start: dict
    end: dict
    direction: str
    active_bar_count: int
    net_thrust: float

@dataclass(frozen=True)
class LegBuildError:
    code: str
    pair_index: int
    left: dict
    right: dict

@dataclass(frozen=True)
class LegBuildResult:
    legs: list[ConfirmedLeg]
    errors: list[LegBuildError]


def build_confirmed_legs(major_swings):
    legs = []
    errors = []
    for pair_index, (left, right) in enumerate(zip(major_swings[:-1], major_swings[1:])):
        if left["kind"] == right["kind"]:
            errors.append(LegBuildError("UPSTREAM_SWING_INVARIANT_ERROR", pair_index, left, right))
            continue
        direction = "BULLISH" if left["kind"] == "SL" and right["kind"] == "SH" else "BEARISH"
        legs.append(ConfirmedLeg(
            start=left,
            end=right,
            direction=direction,
            active_bar_count=int(right["index"]) - int(left["index"]),
            net_thrust=abs(float(right["price"]) - float(left["price"])),
        ))
    return LegBuildResult(legs=legs, errors=errors)
```

- [ ] **Step 4: Run Leg tests to GREEN**

Run: `pytest -q tests/test_leg_v0_baseline.py`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/price_action_ai_leg_v0.py tests/test_leg_v0_baseline.py
git commit -m "feat: add confirmed Leg baseline builder"
```

### Task 2: Protect upstream Swing lock in CI

**Files:**
- Create: `.github/workflows/leg-v0-regression.yml`

**Interfaces:**
- Consumes: existing `tests/test_swing_v1_lock.py` and new `tests/test_leg_v0_baseline.py`.
- Produces: CI gate requiring compile + Swing v1 regression + Leg baseline regression.

- [ ] **Step 1: Add CI workflow**

```yaml
name: Leg v0 Regression

on:
  push:
    branches:
      - sprint2-leg-baseline
  pull_request:
    branches:
      - main

jobs:
  regression:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: python -m pip install --upgrade pip pytest pandas plotly
      - run: python -m py_compile src/price_action_ai_swing_v1.py src/price_action_ai_leg_v0.py
      - run: pytest -q tests/test_swing_v1_lock.py tests/test_leg_v0_baseline.py
```

- [ ] **Step 2: Verify CI**

Expected: Swing v1 regression remains green and all Leg baseline tests pass.

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/leg-v0-regression.yml
git commit -m "ci: gate Leg v0 against locked Swing v1"
```
