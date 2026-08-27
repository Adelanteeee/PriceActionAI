from pathlib import Path
import importlib.util
import math
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "price_action_ai_swing_v1.py"
DATA = ROOT / "tests" / "data"

spec = importlib.util.spec_from_file_location("swing_v1", SRC)
swing = importlib.util.module_from_spec(spec)
sys.modules["swing_v1"] = swing
spec.loader.exec_module(swing)


def _pipeline_df(full, timeframe="M30"):
    gap = swing.segment_on_unexpected_gaps(full, timeframe)
    df = gap["active_segment"].copy().reset_index(drop=True)

    raw = swing.detect_pivot_candidates(df)
    structural, internal = swing.tag_internal_candidates(raw)
    structural = swing.add_swing_diagnostics(structural)

    thrusts = swing._leg_thrusts(structural)
    stats = swing.reference_statistics(thrusts)
    reference, _ = swing.select_nearest_actual_leg(thrusts, stats["rms"])
    major, removed = swing.select_major_swings(df, structural, reference)
    audit = swing.audit_counts(structural, major, removed)
    signature = [
        (int(p["index"]), p["kind"], round(float(p["price"]), 8))
        for p in major
    ]
    return {
        "full": full,
        "gap": gap,
        "df": df,
        "raw": raw,
        "structural": structural,
        "internal": internal,
        "stats": stats,
        "reference": reference,
        "major": major,
        "removed": removed,
        "audit": audit,
        "signature": signature,
    }


def _pipeline(csv_name, timeframe="M30"):
    return _pipeline_df(swing.load_snapshot_file(DATA / csv_name), timeframe)


def test_locked_contract_constants():
    assert swing.VERSION == "1.7.5-clean-baseline"
    assert swing.MIN_CORRECTION_BARS == 5
    assert math.isclose(swing.MAJOR_REJECT_RATIO, 0.50)
    assert math.isclose(swing.MAJOR_ACCEPT_RATIO, 0.70)
    assert math.isclose(swing.MID_QUALITY_THRESHOLD, 0.60)


def test_reference_is_rms_target_snapped_to_observed_leg():
    values = [10.0, 12.0, 14.0, 30.0]
    stats = swing.reference_statistics(values)
    ref, selected = swing.select_nearest_actual_leg(values, stats["rms"])
    assert ref in values
    assert selected == [ref]
    assert math.isclose(stats["rms"], math.sqrt(sum(x*x for x in values)/len(values)))


def test_fixed_snapshot_loader_and_fx_diagnostics():
    full = swing.load_snapshot_file(DATA / "NZDUSD_o_M30_500_20260827_0000.csv")
    df = full.tail(200).reset_index(drop=True)
    assert len(df) == 200
    spec = swing.symbol_display_spec("NZDUSD_o", None)
    assert spec["is_fx"] is True
    assert math.isclose(swing.raw_to_pips(0.00151, spec), 15.1)


def test_broken_broker_history_is_hard_segment_boundary():
    r = _pipeline("NZDUSD_o_M30_200_broken_gap_20260826_1930.csv")
    assert len(r["gap"]["segments"]) == 2
    assert len(r["gap"]["unexpected_gaps"]) == 1
    assert len(r["df"]) == 40
    assert r["df"]["time"].min() > r["full"].iloc[0]["time"]
    first_active_source_index = int(r["df"].iloc[0]["source_index"])
    assert first_active_source_index == r["gap"]["unexpected_gaps"][0]["new_segment_index"]
    assert r["audit"]["invariant_ok"] is True


EXPECTED_200 = [
    (7, 'SL', 0.59393), (37, 'SH', 0.59881), (42, 'SL', 0.59686),
    (49, 'SH', 0.59851), (55, 'SL', 0.59673), (63, 'SH', 0.59828),
    (96, 'SL', 0.59511), (109, 'SH', 0.59679), (125, 'SL', 0.59464),
    (149, 'SH', 0.59826), (151, 'SL', 0.5966), (158, 'SH', 0.59779),
    (170, 'SL', 0.59445), (182, 'SH', 0.59628), (187, 'SL', 0.59329),
    (193, 'SH', 0.59449), (194, 'SL', 0.59409),
]

EXPECTED_500 = [
    (2, 'SL', 0.58577), (3, 'SH', 0.58855), (38, 'SL', 0.58215),
    (104, 'SH', 0.58986), (109, 'SL', 0.58844), (141, 'SH', 0.59263),
    (185, 'SL', 0.58722), (196, 'SH', 0.58926), (219, 'SL', 0.58605),
    (246, 'SH', 0.5938), (253, 'SL', 0.59238), (254, 'SH', 0.59383),
    (259, 'SL', 0.59249), (285, 'SH', 0.59644), (289, 'SL', 0.59404),
    (295, 'SH', 0.59605), (301, 'SL', 0.59369), (337, 'SH', 0.59881),
    (342, 'SL', 0.59686), (349, 'SH', 0.59851), (355, 'SL', 0.59673),
    (363, 'SH', 0.59828), (396, 'SL', 0.59511), (409, 'SH', 0.59679),
    (425, 'SL', 0.59464), (449, 'SH', 0.59826), (470, 'SL', 0.59445),
    (482, 'SH', 0.59628), (487, 'SL', 0.59329), (493, 'SH', 0.59449),
    (494, 'SL', 0.59409),
]


def test_healthy_200_snapshot_regression_signature():
    full = swing.load_snapshot_file(DATA / "NZDUSD_o_M30_500_20260827_0000.csv")
    r = _pipeline_df(full.tail(200).reset_index(drop=True))
    assert len(r["gap"]["segments"]) == 1
    assert len(r["gap"]["unexpected_gaps"]) == 0
    assert len(r["raw"]) == 43
    assert len(r["structural"]) == 43
    assert len(r["major"]) == 17
    assert len(r["removed"]) == 26
    assert math.isclose(r["reference"], 0.00151, rel_tol=0, abs_tol=1e-12)
    assert r["signature"] == EXPECTED_200
    assert r["audit"]["invariant_ok"] is True


def test_healthy_500_snapshot_regression_signature():
    r = _pipeline("NZDUSD_o_M30_500_20260827_0000.csv")
    assert len(r["gap"]["segments"]) == 1
    assert len(r["gap"]["unexpected_gaps"]) == 0
    assert len(r["raw"]) == 95
    assert len(r["structural"]) == 95
    assert len(r["major"]) == 31
    assert len(r["removed"]) == 64
    assert math.isclose(r["reference"], 0.00178, rel_tol=0, abs_tol=1e-12)
    assert r["signature"] == EXPECTED_500
    assert r["audit"]["invariant_ok"] is True


def test_raw_structural_semantics_are_explicit():
    diag = swing.structural_filter_audit(43, 43)
    assert diag == {
        "raw": 43,
        "structural": 43,
        "removed": 0,
        "label": "NO_STRUCTURAL_REMOVAL",
    }


def test_reference_insufficient_data_contract():
    assert swing.reference_data_status([1.0, 2.0], min_legs=3) == "INSUFFICIENT_DATA"
    assert swing.reference_data_status([1.0, 2.0, 3.0], min_legs=3) == "OK"


def test_clean_baseline_is_self_contained_core():
    core = swing._load_core()
    assert core is swing
    assert core.select_major_swings is swing.select_major_swings
