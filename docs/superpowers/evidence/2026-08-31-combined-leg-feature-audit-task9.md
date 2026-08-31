# Combined Leg Feature Audit — Task 9 Gold Evidence

## Final status

Task 9 / Production Gold Combined Audit is complete and independently reviewed.
No Ablation, Causal Replay, Outcome, Score, Threshold, Prediction, Optimization,
PCA, Mutual Information, Clustering, Feature Weight, Accept/Reject rule, or
causal interpretation was performed.

## Provenance

- Input: `GOLD_ACTIVITY_AUDIT_PACKAGE_FINAL_LOCKED.zip`
- Input SHA-256: `1e9f13fd88fc1e8e0e66d801be8c15d726639eaea25e53fef7c3bb88bfd05192`
- Audit code commit: `1c40cd3d3507c473fd07ea25c010d386be8a0043`
- Evidence package: `GOLD_COMBINED_LEG_FEATURE_AUDIT_PACKAGE.zip`
- Evidence package SHA-256: `968f4826858a0bbb8254218711f4ad3e3487370ca8d0f288133ee36f7a4fa40d`
- Evidence package size: 70,373 bytes
- Logical artifacts: 20 CSV/JSON files

## Gate results

| Gate | Result |
|---|---|
| Canonical input SHA | PASS |
| ZIP integrity and manifest provenance | PASS |
| Required schema | PASS |
| Numeric finiteness | PASS |
| Snapshot SHA verification | PASS |
| Deterministic non-vacuous coverage | PASS |
| Deterministic zero failures | PASS |
| Main Raw per-TF reports | PASS |
| Partial same-sample discipline | PASS |
| Bull/Bear supplementary reports | PASS |
| Cross-TF sign/range reconstruction | PASS |
| Raw cross-TF pooling | FORBIDDEN / NOT USED |
| Two clean-run logical byte comparison | PASS — all 20 identical |
| Independent evidence ZIP repeat build | PASS — byte-identical |
| Engine / Leg Engine / Swing changes | NONE |
| Independent review | SPEC PASS / QUALITY APPROVED |

## Report row counts

| Report | Rows |
|---|---:|
| Feature Role Matrix | 47 |
| Deterministic Identity Report | 44 |
| Main Raw Spearman M5 / M15 / M30 / H1 | 78 / 78 / 78 / 78 |
| Partial Spearman M5 / M15 / M30 / H1 | 66 / 66 / 66 / 66 |
| Supplementary Bullish/Bearish per TF | 120 / 120 |
| Cross-TF Relationship Report | 78 |
| Combined Audit Manifest | 1 JSON |

## Deterministic coverage

Each cell is `total / verified / failed`.

| Identity | M5 | M15 | M30 | H1 |
|---|---:|---:|---:|---:|
| CLOSE_DISPLACEMENT_ABS | 142/142/0 | 170/170/0 | 184/184/0 | 181/181/0 |
| CONTINUITY_COUNT_SUM | 142/142/0 | 170/170/0 | 184/184/0 | 181/181/0 |
| CONTINUITY_RATIO | 142/142/0 | 170/170/0 | 184/184/0 | 181/181/0 |
| BODY_STRENGTH_RATIO | 142/142/0 | 170/170/0 | 184/184/0 | 181/181/0 |
| GAP_PATH_SHARE | 142/142/0 | 170/170/0 | 184/184/0 | 181/181/0 |
| SHADOW_MAGNITUDE_SUM | 142/142/0 | 170/170/0 | 184/184/0 | 181/181/0 |
| SHADOW_POSITION_IMBALANCE | 142/142/0 | 170/170/0 | 184/184/0 | 181/181/0 |
| OVERLAP_RATIO | 142/142/0 | 170/170/0 | 184/184/0 | 181/181/0 |
| SLOPE_DIRECTION | 142/142/0 | 170/170/0 | 184/184/0 | 181/181/0 |
| SLOPE_NORMALIZATION | 142/142/0 | 170/170/0 | 184/184/0 | 181/181/0 |
| TICK_ACTIVITY_IDENTITY | 142/142/0 | 170/170/0 | 184/184/0 | 181/181/0 |

For every identity and timeframe:

`verified_rows + failed_rows = total_rows` and `failed_rows = 0`.

## Test evidence

- Full repository: `226 passed in 1.29s`
- Task reviewer: no Critical, Important, or Minor findings
- Final controller verification: PASS

## Stop gate

Task 9 is complete. The process stops here. Any Ablation, Causal Replay,
Score, Threshold, or later phase requires new explicit authorization.
