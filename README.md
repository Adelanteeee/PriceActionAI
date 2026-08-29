# PriceActionAI

Rule-based multi-timeframe Price Action trading system with locked definitions, regression safety, and strict review gates.

## Project operating model

- **Google Drive / Docs** = Product & Strategy Single Source of Truth
- **Linear** = Sprint / Task execution layer
- **GitHub** = Code, tests, regression fixtures, branches, commits and pull requests

## Governing rule

No downstream module may silently change a locked upstream definition. Any change to a Done/Locked module requires an explicit Change Request plus regression testing.

## Current project state

- **Sprint 1 — Swing Engine: Locked**
- **Sprint 2 — Leg Engine: Active**
- **ADE-12 Leg Metrics baseline: Locked on `sprint2-leg-baseline`**
- Swing market logic: **v1.7.5 Clean Baseline**
- Swing Data Integrity: **ADE-9 + bounded ADE-12 XAU M5 session-gap CR**
- v1.7.6 Depth × Time: **Experiment Failed — Not Adopted** (research archived)

## Locked Leg Metrics baseline

The current Sprint 2 baseline keeps the following dimensions separate:

- **Net Thrust** = structural extreme-to-extreme size
- **Gross Close Path** = close-to-close path length
- **Signed Close Displacement** = structural-direction-aware close displacement
- **Direction Agreement** = signed displacement > 0
- **Directional Efficiency** = clipped signed displacement / gross close path
- **Close Confirmation Ratio** = clipped signed displacement / net thrust
- **Temporal Profile Tag** = diagnostic only
- **Gap Path Contribution / Share** = scheduled-gap diagnostics only

No Body/Wick/Overlap/Volume, no Quality Score, and no Accept/Reject gate are part of this locked baseline.

## Swing v1 lock contract

Leg Engine may consume Swing Engine output but may not silently modify:
- Structural Swing sequence
- Reference Leg definition
- Major Swing classification
- Temporal Gate
- Extreme Carry-Forward
- Data Integrity boundaries

Any change requires an explicit Change Request plus Sprint 1 regression.

## Canonical references

- Master Blueprint: https://docs.google.com/document/d/1mLzBoUT4JE992IMsyCjHIiGhAXsg_FdSXoSJFwJ6bzI
- Linear Project: https://linear.app/adelantee/project/priceactionai-7d4d921509d8
- Working Agreement: https://linear.app/adelantee/document/priceactionai-working-agreement-873f91c036cb

## Regression

Run:

```bash
pytest -q
```

The locked suite includes Swing lock regression, Leg baseline regression, ADE-12 hardening regression, authoritative Data Integrity path regression, and historical NZDUSD gap fixtures.

## Development flow

1. Read the Master Blueprint before starting a task.
2. Work only from the active Linear issue.
3. Implement code and tests in GitHub.
4. Validate against acceptance criteria.
5. Run regression checks against locked upstream modules.
6. Record strict review results.
7. Update the Master Blueprint if an approved rule changes.
8. Move the Linear issue to Done only after the Definition of Done is satisfied.
