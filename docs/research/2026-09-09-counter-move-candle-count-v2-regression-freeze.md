# Counter-Move Candle Count v2 — Regression Freeze

Date: 2026-09-09

## Frozen regressions

- M30 `164 SL -> 166 SH`: reject; only 2 bars.
- H1 `81 SL -> 90 SH`: reject; counter-move after 81 lasts about 2 bars before downside continuation resumes.
- H1 `143 SL -> 144 SH`: reject; only 1 bar.

## Root cause

The old Candle Count feature measured how long the pivot extreme survived before being broken. That is not the agreed four-bar contract.

## V2 contract

For `SL`, the counter-move is upward and downside resumption is the first bar where:

```text
close < previous close
AND
(low < previous low OR high < previous high)
```

For `SH`, use the symmetric upside condition.

The continuation bar itself is not counted.

`counter_move_bar_count >= 4` is a hard gate for every selected pivot, including prominence-strong pivots.

## TDD verification

RED: all three regression tests fail on frozen v1.

GREEN: all three regression tests pass on v2.

Exact feature checks on the uploaded `output.zip`:

- M30 164 SL -> count 2 -> FAIL
- M30 166 SH -> count 1 -> FAIL
- H1 81 SL -> count 2 -> FAIL
- H1 90 SH -> count 4 -> PASS; the invalid pair is broken because 81 fails
- H1 143 SL -> count 1 -> FAIL
- H1 144 SH -> count 2 -> FAIL

## Artifact

`PriceActionAI_Gold_CounterMove_CandleCount_v2.zip`

SHA-256:

```text
04f479b89c2ada8490491c0ced320222222905015ec4cb3ee36aa0b2280d27f9
```

## Status

Research retest candidate only. Frozen v1 references remain unchanged. Visual retest on XAUUSD M5/M15/M30/H1/H4/D1 is required before promoting this logic into Combined v2.
