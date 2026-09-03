from pathlib import Path
import importlib.util
import math

import pandas as pd

MODULE_PATH = Path(__file__).resolve().parents[1] / "prototype" / "trend_leg_visual_validator.py"


def load_module():
    spec = importlib.util.spec_from_file_location("trend_leg_visual_validator", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_directional_close_location_bullish_and_bearish():
    m = load_module()
    assert m.directional_close_location("BULLISH", 110, 100, 108) == 0.8
    assert m.directional_close_location("BEARISH", 110, 100, 102) == 0.8


def test_terminal_third_boundary_is_inclusive():
    m = load_module()
    dcl = 2.0 / 3.0
    assert m.is_terminal_third(dcl) is True
    assert m.is_terminal_third(dcl - 1e-12) is False


def test_zero_range_candle_has_undefined_dcl():
    m = load_module()
    assert m.directional_close_location("BULLISH", 100, 100, 100) is None


def test_leg_close_evidence_excludes_undefined_dcl_from_denominator():
    m = load_module()
    df = pd.DataFrame({"high": [0, 110, 100, 120], "low": [0, 100, 100, 110], "close": [0, 108, 100, 112]})
    record = {"direction": "BULLISH", "start_index": 0, "end_index": 3}
    out = m.leg_close_evidence(record, df)
    assert out["defined_dcl_candle_count"] == 2
    assert out["terminal_third_close_count"] == 1
    assert out["terminal_third_close_ratio"] == 0.5
    assert math.isclose(out["mean_directional_close_location"], 0.5)


def test_timeframe_eligibility_minimum_four_bars_only():
    m = load_module()
    assert m.trend_review_state(3) == "TF_UNDERSAMPLED"
    assert m.trend_review_state(4) == "TF_ELIGIBLE_FOR_TREND_REVIEW"
    assert m.trend_review_state(18) == "TF_ELIGIBLE_FOR_TREND_REVIEW"


def test_trend_record_contains_dcl_fields_without_binary_trend_label():
    m = load_module()
    df = pd.DataFrame({"high": [0, 110, 112, 114, 116], "low": [0, 100, 102, 104, 106], "close": [0, 108, 110, 112, 114]})
    base = {
        "leg_no": 1, "direction": "BULLISH", "start_index": 0, "end_index": 4,
        "active_bar_count": 4, "net_thrust": 16.0,
        "normalized_directional_close_ols_slope": 0.5, "body_strength_ratio": 0.7,
        "directional_continuity_ratio": 0.75, "directional_efficiency": 0.8, "overlap_ratio": 0.2,
    }
    out = m.trend_leg_record(base, df)
    assert out["trend_review_state"] == "TF_ELIGIBLE_FOR_TREND_REVIEW"
    assert "mean_directional_close_location" in out
    assert "terminal_third_close_ratio" in out
    forbidden = {"trend", "is_trend", "trend_score", "not_trend"}
    assert not (forbidden & set(out))


def test_terminal_third_marker_trace_uses_owned_terminal_candles_only():
    m = load_module()
    df = pd.DataFrame({
        "time": pd.date_range("2026-09-01", periods=5, freq="15min"),
        "high": [100, 110, 112, 114, 116], "low": [100, 100, 102, 104, 106], "close": [100, 108, 106, 112, 107],
    })
    record = {"leg_no": 1, "direction": "BULLISH", "start_index": 0, "end_index": 4}
    trace = m.terminal_third_marker_trace(record, df)
    assert trace.meta["pai_kind"] == "terminal_third_close"
    assert list(trace.x) == [1, 3]


def test_launcher_contains_all_four_timeframes():
    launcher = Path(__file__).resolve().parents[1] / "prototype" / "RUN_TREND_LEG_VISUAL_VALIDATOR.bat"
    text = launcher.read_text(encoding="utf-8")
    assert "--timeframes M5 M15 M30 H1" in text
