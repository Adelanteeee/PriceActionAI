# Balance Compression Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add experimental Balance Packet detection/compression before Reference Leg estimation.

**Architecture:** Extend the existing v1.4 spike with two pure functions: `detect_balance_packets()` and `compress_balance_packets()`. Keep detection independent from Reference Leg, store packet boundaries as metadata, and feed the compressed swing sequence into the existing reference-leg estimator and 50/70 compressor.

**Tech Stack:** Python 3, pandas, Plotly, pytest, MetaTrader5 runtime adapter.

**Spec:** `docs/superpowers/specs/2026-08-26-balance-compression-design.md`

## Global Constraints
- Swing, Leg, and Trend Leg remain distinct concepts.
- The 4-candle minimum applies only to Trend Leg classification.
- Balance Compression is experimental and is not the final Range Engine.
- Both Balance boundaries must be preserved as metadata.
- Prior bullish leg -> keep highest SH; prior bearish leg -> keep lowest SL.
- Reference Leg is estimated only after Balance Compression.
- Wick outliers are diagnostics-only in this iteration.

---

### Task 1: Balance packet primitives
- [x] Write failing tests for balance detection, bullish compression, bearish compression, trend rejection, and reference cleanup.
- [x] Run tests and verify RED because functions are missing.
- [x] Implement minimal packet metrics and right-to-left packet discovery.
- [x] Implement compression using prior-leg direction and preserve both boundaries.
- [x] Run focused tests until GREEN.

### Task 2: Pipeline integration and diagnostics
- [x] Insert Balance detection/compression before automatic reference estimation.
- [x] Add console diagnostics for packet count, boundaries, entry direction, effective swing, and pre/post reference estimate.
- [x] Add chart diagnostics for Reference source/value/cluster/50%/70% and Balance packet count/boundaries.
- [x] Preserve manual `--reference-leg` override for controlled experiments.

### Task 3: Regression verification
- [x] Run v1.5 balance tests.
- [x] Run v1.3 regression tests.
- [x] Run Python syntax compilation.
- [x] Verify CLI help for M5/M15/M30/H1 and manual reference override.
- [x] Record status as experimental; do not mark Sprint 1 Done before real-data visual review.
