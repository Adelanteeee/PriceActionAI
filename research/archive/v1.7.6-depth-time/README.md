# v1.7.6 Depth × Time — Research Archive

Status: **Experiment Failed — Not Adopted**

This archive preserves the tested v1.7.6 implementation and evidence. It is **not** the production Swing Engine.

The hypothesis that correction independence may depend on both temporal development and parent-leg retracement depth is **not permanently disproven**. The tested rule was rejected because it over-segmented the Major Swing path on a healthy fixed NZDUSD_o M30 snapshot.

## Fixed-snapshot A/B result

- v1.7.5 Clean Baseline: **29 Major**
- v1.7.6 Depth × Time: **43 Major**
- Net effect: **+14 Major pivots**
- Reference Leg: unchanged
- Raw Pivots: unchanged
- Structural path: unchanged

## Attribution of the +14 pivots

- 50–70% parent-retracement bucket: **8** total (6 direct, 2 cascade-associated)
- >=70% bucket: **6** total (5 direct, 1 cascade-associated)

The experiment therefore showed over-sensitivity in the tested rule, not proof that Depth × Time can never be useful.

## Reopening rule

Swing Engine may only be reopened by an explicit Change Request after repeated, specific downstream evidence from Leg Engine or later backtests demonstrates a Swing-layer defect. Any change must pass the locked Sprint 1 regression suite.

## Archived source

`PriceActionAI_v1_7_6_Depth_Time_r1.py.gz.b64` is the gzip-compressed, base64-encoded experimental source kept for research reproducibility.

Decode on Linux/macOS:

```bash
base64 -d PriceActionAI_v1_7_6_Depth_Time_r1.py.gz.b64 | gunzip > PriceActionAI_v1_7_6_Depth_Time_r1.py
```
