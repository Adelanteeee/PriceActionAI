# Parallel Trend Leg Visual Validator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Add a manual Trend-Leg evidence validator with direction-aware close-location measurements while leaving locked Swing/Leg semantics unchanged.

**Architecture:** Implement DCL as a separate prototype module layered on top of `prototype.visual_leg_inspector`; do not edit locked `src` Swing/Leg files. Extend records and chart rendering in the new module, then provide a four-timeframe Windows launcher.

**Tech Stack:** Python, pandas, Plotly, MetaTrader5, pytest.

**Spec:** `docs/superpowers/specs/2026-09-03-parallel-trend-leg-visual-validator-design.md`

## Global Constraints
- `active_bar_count >= 4` is the only hard v1 eligibility rule.
- No automatic Trend/Not-Trend classification.
- No score, weight, ML, optimization, or added Trend thresholds.
- DCL terminal-third geometry is exactly `>= 2/3`.
- M5/M15/M30/H1 all run from one launcher.
- Locked Swing/Leg files are read-only.

---

### Task 1: DCL measurement core
**Files:** Create `prototype/trend_leg_visual_validator.py`; create `tests/test_trend_leg_visual_validator.py`.

**Interfaces:**
- `directional_close_location(direction, high, low, close) -> float | None`
- `candle_close_evidence(direction, high, low, close) -> dict`
- `leg_close_evidence(record, df) -> dict`
- `trend_review_state(active_bar_count) -> str`

Steps: write failing tests for Bullish/Bearish DCL, terminal-third boundary, zero-range, aggregation and timeframe eligibility; confirm RED; implement minimal pure functions; confirm GREEN.

### Task 2: Visual and export integration
**Files:** Modify new validator module and test file.

**Interfaces:** `trend_leg_record` extends existing Leg payload; chart adds terminal-third markers; HTML adds persistent evidence panel; timeframe validation writes HTML/CSV/JSON.

Steps: add failing integration tests; confirm RED; implement minimal chart/export integration using existing locked pipeline; confirm GREEN.

### Task 3: Four-timeframe launcher and regression verification
**Files:** Create `prototype/RUN_TREND_LEG_VISUAL_VALIDATOR.bat`; test launcher content.

Steps: test M5/M15/M30/H1 command; confirm RED; add launcher; run Trend tests; run py_compile; verify locked Swing/Leg source paths are unchanged by the implementation commit.
