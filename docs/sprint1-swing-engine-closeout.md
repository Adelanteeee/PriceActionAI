# Sprint 1 — Swing Engine Closeout

## Locked production baseline

`src/price_action_ai_swing_v1.py`

Production market logic is **v1.7.5 Clean Baseline + ADE-9 data-integrity/audit hardening**.

Locked behavior:
- non-destructive Internal Candidates
- RMS target snapped to nearest actual Structural Leg
- Major thresholds: <50% reject, 50–70% quality-dependent, >=70% accept
- Extreme Carry-Forward
- Temporal Gate: 1–4 active-bar counter-moves remain internal by default; >=5 bars use normal Reference/Quality evaluation
- Balance remains parked for Sprint 3

## Data-integrity boundary

An unexpected broker/history gap is a hard segment boundary. Swing, Reference and Major state cannot cross that boundary. A new segment must construct Reference independently; otherwise the contract is `INSUFFICIENT_DATA`.

## Reproducible regression

The repository contains:
- healthy NZDUSD_o M30 500-bar fixture
- exact healthy tail-200 regression derived from that fixture
- historical broken-broker-data NZDUSD_o M30 fixture containing the old unexpected gap
- CI compile + pytest regression gate

Previously accepted cross-asset visual evidence included XAUUSD, NQ, YM, EURUSD, GBPUSD, USDCAD and NVDA. Those historical visuals informed acceptance, while the currently committed machine-reproducible fixtures focus on the healthy/broken NZDUSD cases that drove final hardening.

## v1.7.6 Depth × Time decision

**Experiment Failed — Not Adopted.**

This rejects the tested implementation, not the hypothesis forever. Fixed-snapshot A/B produced 29 Major pivots in v1.7.5 versus 43 in v1.7.6 with Reference/Raw/Structural unchanged, demonstrating over-segmentation in the tested rule. The source and attribution evidence are preserved under `research/archive/v1.7.6-depth-time/`.

## Strict closeout review

- Senior Trader: **8/10** — accepted Major structure is coherent on reviewed samples; market-state context remains intentionally downstream.
- Senior Developer: **8.5/10** — deterministic core, reproducible CI regression, explicit data-gap boundary; regression fixture diversity can grow later without changing the lock.
- CTO: **8/10** — clean upstream contract and self-contained production path; later modular extraction is possible but not required for Sprint 2.
- Product/Visual: **8/10** — interpretable Major path and auditable diagnostics; visual ergonomics can improve independently.

Overall closeout assessment: **8/10 — sufficient to lock and proceed.**

## Upstream lock contract for Sprint 2

Leg Engine consumes Swing Engine output. It must not silently modify Structural pivots, Reference definition, Major classification, Temporal Gate, Extreme Carry-Forward or Data Integrity behavior.

Any requested Swing change requires:
1. explicit Change Request,
2. repeated downstream evidence of a Swing-layer defect,
3. full Sprint 1 regression pass,
4. user approval before re-locking.
