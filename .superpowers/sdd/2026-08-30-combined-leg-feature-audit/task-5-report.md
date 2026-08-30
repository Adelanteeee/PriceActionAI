# Task 5 Report: Supplementary Stratification and Cross-TF Consistency

## Scope

Implemented only the Task 5 report builders and their tests:

- `build_direction_stratified_report(rows, direction)` filters to the requested
  direction before calculating supplementary results over
  `MAIN_FEATURES + RAW_DIRECTION_SENSITIVE`.
- Its raw and duration-controlled tables contain 120 and 105 feature pairs,
  respectively, and every result carries `evidence_scope = SUPPLEMENTARY_ONLY`.
- `build_cross_tf_relationship_report(main_by_tf, partial_by_tf)` joins
  independently calculated timeframe results by `(feature_x, feature_y)`.
  It does not pool raw rows or use report-row positions.
- Cross-TF output supplies raw and controlled values per timeframe, raw sample
  counts, controlled eligibility, sign counts/ties/modal signs, and defined-only
  min/max/range values. Pairs involving `active_bar_count` have unavailable
  controlled values.

No `src/` modules, Gold inputs, or external data were accessed or changed.

## RED

Command:

```text
/workspace/scratch/a5877cf58447/combined-audit-venv/bin/python -m pytest -q tests/test_combined_audit_reports.py -k 'stratified or cross_tf'
```

Result before implementation:

```text
ImportError: cannot import name 'build_cross_tf_relationship_report'
```

## GREEN and verification

```text
pytest -q tests/test_combined_audit_reports.py -k 'stratified or cross_tf'
5 passed, 6 deselected

pytest -q tests/test_combined_audit_reports.py
12 passed

pytest -q tests/test_combined_audit_*.py
47 passed

pytest -q
161 passed
```

`git diff --check` completed without errors.

## Files

- `research/combined_audit_reports.py`
- `tests/test_combined_audit_reports.py`
- `.superpowers/sdd/2026-08-30-combined-leg-feature-audit/task-5-report.md`

## Self-review

- Same-direction filtering is applied before any feature column is calculated.
- Supplementary raw-sensitive fields appear only in the supplementary universe.
- Cross-TF results use pair-key indexes; a reversed-row-order regression test
  verifies that values stay associated with their pair.
- Ties list all modal signs in the locked order; all-undefined sign/range
  summaries stay `None`.
- The report has no qualitative labels, causal claims, raw pooling, or status
  coercion.

## Commit

SHA: `9ef1dea242463f19774e3bd0f24a9052637ca3d0` (superseded by the metadata-only
amend that records this report)

Subject: `feat: add stratified and cross-TF audit reports`

## Concerns

None. Python bytecode cache directories created by test execution remain
untracked and are intentionally excluded from the commit.
