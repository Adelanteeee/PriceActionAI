from pathlib import Path
import base64
import gzip
import importlib.util
import math
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "tests" / "data"
SWING_SRC = ROOT / "src" / "price_action_ai_swing_v1.py"
LEG_SRC = ROOT / "src" / "price_action_ai_leg_v0.py"


def _load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


swing = _load_module("swing_v1_leg_real", SWING_SRC)
leg_v0 = _load_module("leg_v0_real", LEG_SRC)


def _decoded_fixture(stem):
    encoded = (DATA / f"{stem}.csv.gz.b64").read_text(encoding="utf-8").strip()
    raw = gzip.decompress(base64.b64decode(encoded))
    outdir = Path(tempfile.gettempdir()) / "priceactionai_leg_v0_fixtures"
    outdir.mkdir(parents=True, exist_ok=True)
    path = outdir / f"{stem}.csv"
    path.write_bytes(raw)
    return path


def _major_swings_from_healthy_500():
    full = swing.load_snapshot_file(_decoded_fixture("NZDUSD_o_M30_500_20260827_0000"))
    gap = swing.segment_on_unexpected_gaps(full, "M30")
    df = gap["active_segment"].copy().reset_index(drop=True)
    raw = swing.detect_pivot_candidates(df)
    structural, _ = swing.tag_internal_candidates(raw)
    structural = swing.add_swing_diagnostics(structural)
    thrusts = swing._leg_thrusts(structural)
    stats = swing.reference_statistics(thrusts)
    reference, _ = swing.select_nearest_actual_leg(thrusts, stats["rms"])
    major, _ = swing.select_major_swings(df, structural, reference)
    return df, reference, major


def test_real_nzdusd_m30_500_builds_30_confirmed_legs_without_upstream_errors():
    df, reference, major = _major_swings_from_healthy_500()
    result = leg_v0.build_confirmed_legs(major)

    assert len(df) == 500
    assert math.isclose(reference, 0.00178, rel_tol=0, abs_tol=1e-12)
    assert len(major) == 31
    assert len(result.legs) == 30
    assert result.errors == []


def test_real_snapshot_first_and_last_leg_measurements_match_major_endpoints():
    _, _, major = _major_swings_from_healthy_500()
    result = leg_v0.build_confirmed_legs(major)

    first = result.legs[0]
    assert first.direction == "BULLISH"
    assert first.start["index"] == 2
    assert first.end["index"] == 3
    assert first.active_bar_count == 1
    assert math.isclose(first.net_thrust, 0.00278, rel_tol=0, abs_tol=1e-12)

    last = result.legs[-1]
    assert last.direction == "BEARISH"
    assert last.start["index"] == 493
    assert last.end["index"] == 494
    assert last.active_bar_count == 1
    assert math.isclose(last.net_thrust, 0.00040, rel_tol=0, abs_tol=1e-12)
