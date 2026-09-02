# Parallel Visual Swing + Leg Inspector Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a parallel MT5-connected Plotly inspector that shows locked Swing/Leg geometry and all already-existing Leg measurements without adding any trading classification or rule.

**Architecture:** Keep the frozen Swing and advanced Leg engines unchanged. Add a prototype-only visual runner that reuses the locked engines, passes full OHLC/tick-volume inputs into `build_confirmed_legs`, produces one selectable Plotly trace per Leg, injects a small client-side inspector panel into the exported HTML, and exports the same measurements to CSV.

**Tech Stack:** Python, MetaTrader5 Python package, pandas, Plotly, pytest, GitHub branch isolation.

**Spec:** `docs/superpowers/specs/2026-09-02-parallel-visual-leg-inspector-design.md`

## Global Constraints

- Do not modify locked Swing Engine semantics.
- Do not modify advanced Leg Engine semantics.
- Do not continue Task 12 / Controlled Ablation.
- No Trend/Range/Correction/Balance/Setup/Entry label is created in this task.
- No Feature weight, score, threshold, Accept/Reject gate, prediction or optimization is created.
- Plotly remains a manual visual validator only.
- Activity source remains MT5 `tick_volume` only.

---

### Task 1: Define inspector payload contract with failing tests

**Files:**
- Create: `tests/test_parallel_visual_leg_inspector.py`
- Create later: `prototype/visual_leg_inspector.py`

**Interfaces:**
- Produces: `LEG_FEATURE_FIELDS`, `leg_engine_kwargs(df, scheduled_gap_indices)`, `leg_feature_record(leg_no, leg, df)`.

- [ ] **Step 1: Write failing tests** that import `prototype.visual_leg_inspector` and assert the exact existing metric field list, no classification fields, correct OHLC/tick-volume forwarding, and complete record extraction.
- [ ] **Step 2: Run `pytest tests/test_parallel_visual_leg_inspector.py -v`** and verify RED because the prototype module does not exist.
- [ ] **Step 3: Commit the RED test file.**

### Task 2: Implement pure inspector helpers

**Files:**
- Create: `prototype/__init__.py`
- Create: `prototype/visual_leg_inspector.py`
- Test: `tests/test_parallel_visual_leg_inspector.py`

**Interfaces:**
- `leg_engine_kwargs(df: pandas.DataFrame, scheduled_gap_indices: set[int]) -> dict`
- `leg_feature_record(leg_no: int, leg: object, df: pandas.DataFrame) -> dict`

- [ ] **Step 1: Implement only the helpers required by the failing tests.**
- [ ] **Step 2: Run `pytest tests/test_parallel_visual_leg_inspector.py -v`** and verify GREEN.
- [ ] **Step 3: Commit helper implementation.**

### Task 3: Add Plotly chart and click inspector

**Files:**
- Modify: `prototype/visual_leg_inspector.py`
- Modify: `tests/test_parallel_visual_leg_inspector.py`

**Interfaces:**
- Produces: `build_chart(...) -> plotly.graph_objects.Figure`
- Produces: `write_inspector_html(fig, records, output_path) -> pathlib.Path`

- [ ] **Step 1: Add failing tests** asserting each Leg trace contains stable Leg identity/customdata and generated HTML contains `Leg Inspector` plus a `plotly_click` listener.
- [ ] **Step 2: Run tests and verify RED.**
- [ ] **Step 3: Implement candlesticks, Swing spine, one Leg trace per confirmed Leg, compact hover, and client-side click panel.**
- [ ] **Step 4: Run tests and verify GREEN.**
- [ ] **Step 5: Commit visual interaction implementation.**

### Task 4: Wire MT5 and locked engines without semantic edits

**Files:**
- Modify: `prototype/visual_leg_inspector.py`
- Test: `tests/test_parallel_visual_leg_inspector.py`

**Interfaces:**
- Reuses current locked `src/price_action_ai_swing_v1.py` entry point.
- Reuses current `src/price_action_ai_leg_v0.py` without modification.

- [ ] **Step 1: Add failing tests** for engine-path resolution and supported MT5 timeframe mapping independent of a live terminal.
- [ ] **Step 2: Run tests and verify RED.**
- [ ] **Step 3: Implement MT5 connection, broker symbol discovery, candle acquisition, locked Swing pipeline invocation, scheduled-gap mapping, and full Leg build inputs.**
- [ ] **Step 4: Run tests and verify GREEN.**
- [ ] **Step 5: Commit integration runner.**

### Task 5: Export audit CSV and Windows launcher

**Files:**
- Modify: `prototype/visual_leg_inspector.py`
- Create: `prototype/RUN_VISUAL_LEG_INSPECTOR.bat`
- Modify: `tests/test_parallel_visual_leg_inspector.py`

**Interfaces:**
- CLI defaults: symbol `XAUUSD_o`, timeframe `M15`, bars `1000`.
- Outputs: one interactive HTML and one CSV under a user-selectable output directory.

- [ ] **Step 1: Add failing tests** for deterministic output filenames and CSV field order.
- [ ] **Step 2: Run tests and verify RED.**
- [ ] **Step 3: Implement CLI/output export and simple Windows launcher.**
- [ ] **Step 4: Run tests and verify GREEN.**
- [ ] **Step 5: Commit runnable prototype.**

### Task 6: Regression/scope verification and records

**Files:**
- No engine edits allowed.
- Update project records only after verification.

- [ ] **Step 1: Run prototype tests plus existing Swing/Leg regression tests available on the branch.**
- [ ] **Step 2: Compare branch against base `b2595784edc09d88f436fe447354f35a3cf4a850`; confirm no `src/` engine file changed.**
- [ ] **Step 3: Record the new parallel path and frozen-research decision in Linear.**
- [ ] **Step 4: Update the Google Drive Master Blueprint with the parallel-path decision, branch, baseline, and first prototype status.**
- [ ] **Step 5: Report exact files/commit and the command the user runs locally with MT5 open.**
