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
- Production baseline: `src/price_action_ai_swing_v1.py`
- Market logic: **v1.7.5 Clean Baseline**
- Data-integrity/audit hardening: **ADE-9 included**
- v1.7.6 Depth × Time: **Experiment Failed — Not Adopted** (research archived)
- Next: **Sprint 2 — Leg Engine**

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

The locked suite includes a healthy fixed NZDUSD snapshot plus the historical NZDUSD broker-history gap case.

## Development flow

1. Read the Master Blueprint before starting a task.
2. Work only from the active Linear issue.
3. Implement code and tests in GitHub.
4. Validate against acceptance criteria.
5. Run regression checks against locked upstream modules.
6. Record strict review results.
7. Update the Master Blueprint if an approved rule changes.
8. Move the Linear issue to Done only after the Definition of Done is satisfied.
