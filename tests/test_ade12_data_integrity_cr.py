from pathlib import Path
import importlib.util
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "price_action_ai_data_integrity_cr.py"
spec = importlib.util.spec_from_file_location("ade12_data_cr", SRC)
data_cr = importlib.util.module_from_spec(spec)
sys.modules["ade12_data_cr"] = data_cr
spec.loader.exec_module(data_cr)


def df_times(values):
    return pd.DataFrame({"time": pd.to_datetime(values)})


def test_xau_m5_daily_closure_is_scheduled_not_unexpected():
    df = df_times(["2026-08-27 23:50", "2026-08-27 23:55", "2026-08-28 01:00", "2026-08-28 01:05"])
    result = data_cr.classify_time_gaps(df, "M5", symbol="XAUUSD_o")
    assert len(result["unexpected"]) == 0
    assert [g["reason"] for g in result["scheduled"]] == ["SCHEDULED_XAU_DAILY_CLOSURE"]


def test_xau_h1_memorial_day_2026_closure_is_scheduled_not_unexpected():
    df = df_times(["2026-05-25 21:00", "2026-05-26 01:00"])
    result = data_cr.classify_time_gaps(df, "H1", symbol="XAUUSD_o")
    assert len(result["unexpected"]) == 0
    assert [g["reason"] for g in result["scheduled"]] == ["SCHEDULED_XAU_MEMORIAL_DAY_2026"]


def test_same_h1_holiday_signature_on_neighbor_date_stays_unexpected():
    df = df_times(["2026-05-26 21:00", "2026-05-27 01:00"])
    result = data_cr.classify_time_gaps(df, "H1", symbol="XAUUSD_o")
    assert len(result["unexpected"]) == 1
    assert result["unexpected"][0]["reason"] == "UNEXPECTED_DATA_GAP"


def test_same_h1_holiday_signature_is_not_special_for_non_gold():
    df = df_times(["2026-05-25 21:00", "2026-05-26 01:00"])
    result = data_cr.classify_time_gaps(df, "H1", symbol="EURUSD")
    assert len(result["unexpected"]) == 1
    assert result["unexpected"][0]["reason"] == "UNEXPECTED_DATA_GAP"


def test_same_65_minute_gap_is_not_special_for_non_gold():
    df = df_times(["2026-08-27 23:55", "2026-08-28 01:00"])
    result = data_cr.classify_time_gaps(df, "M5", symbol="EURUSD")
    assert len(result["unexpected"]) == 1
    assert result["unexpected"][0]["reason"] == "UNEXPECTED_DATA_GAP"


def test_wrong_xau_clock_signature_stays_unexpected():
    df = df_times(["2026-08-27 22:55", "2026-08-28 00:00"])
    result = data_cr.classify_time_gaps(df, "M5", symbol="XAUUSD_o")
    assert len(result["unexpected"]) == 1


def test_weekend_stays_scheduled():
    df = df_times(["2026-08-21 23:55", "2026-08-24 01:05"])
    result = data_cr.classify_time_gaps(df, "M5", symbol="XAUUSD_o")
    assert len(result["unexpected"]) == 0
    assert result["scheduled"][0]["reason"] == "SCHEDULED_WEEKEND"


def test_unexpected_gap_still_segments_and_resets_active_segment():
    df = df_times(["2026-08-27 10:00", "2026-08-27 10:05", "2026-08-27 12:00", "2026-08-27 12:05"])
    result = data_cr.segment_on_unexpected_gaps(df, "M5", symbol="XAUUSD_o")
    assert len(result["segments"]) == 2
    assert len(result["active_segment"]) == 2
    assert len(result["unexpected_gaps"]) == 1
