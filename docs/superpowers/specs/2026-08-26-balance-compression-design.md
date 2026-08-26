# Balance Compression Design

## Goal
Add an experimental Balance Compression layer to Sprint 1 so repeated pivots inside a compact, two-sided area do not pollute Reference Leg estimation.

## Scope
This is not the final Range Engine. It only detects a balance-like packet from already-validated structural swings, stores both packet boundaries for diagnostics/future use, and keeps one effective swing based on the direction of the leg entering the packet.

## Pipeline
Raw Pivot -> Internal Noise Filter -> Balance Packet Detection -> Balance Compression -> Reference Leg -> 50/70 Major Swing Filter

## Balance Packet signal
A candidate packet must:
- contain at least 5 alternating pivots,
- show repeated back-and-forth travel relative to its total price span,
- have low net directional progress versus gross travel,
- remain compact relative to its typical internal leg size.

The detector is reference-leg independent to avoid circular logic.

## Compression rule
- If the leg entering the packet is bullish, keep the highest valid SH in the packet as the effective swing.
- If the leg entering the packet is bearish, keep the lowest valid SL in the packet as the effective swing.
- Preserve both packet boundaries (`boundary_high`, `boundary_low`) as metadata.
- Internal pivots are excluded from Reference Leg estimation.

## Wick outlier
Do not delete long wicks in this iteration. Keep them available for diagnostics until a separate numeric acceptance rule is approved.

## Non-goals
- No final Range classification.
- No breakout trading rule.
- No entry/stop logic.
- No higher-timeframe context integration in this iteration.

## Success criteria
- Synthetic balance is detected and compressed.
- Clean trend structure is not compressed.
- Effective swing follows prior-leg direction.
- Reference Leg estimation can change after balance compression.
- Existing timeframe and structural-swing behavior remains intact.
