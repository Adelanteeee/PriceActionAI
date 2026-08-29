from __future__ import annotations

from pathlib import Path
import importlib.util
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SWING_SRC = ROOT / "src" / "price_action_ai_swing_v1.py"


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


swing = load("ade12_authoritative_swing", SWING_SRC)


def _ohlc(times):
    n = len(times)
    return pd.DataFrame({
        "time": pd.to_datetime(times),
        "open": [100.0] * n,
        "high": [101.0] * n,
        "low": [99.0] * n,
        "close": [100.0] * n,
    })


def test_locked_swing_entry_point_accepts_symbol_and_classifies_xau_m5_daily_closure():
    df = _ohlc([
        "2026-08-27 23:50",
        "2026-08-27 23:55",
        "2026-08-28 01:00",
        "2026-08-28 01:05",
    ])
    result = swing.segment_on_unexpected_gaps(df, "M5", symbol="XAUUSD_o")
    assert len(result["unexpected_gaps"]) == 0
    assert len(result["scheduled_gaps"]) == 1
    assert result["scheduled_gaps"][0]["reason"] == "SCHEDULED_XAU_DAILY_CLOSURE"
    assert len(result["active_segment"]) == 4


def test_locked_swing_entry_point_keeps_real_intraday_gap_as_hard_boundary():
    df = _ohlc([
        "2026-08-27 10:00",
        "2026-08-27 10:05",
        "2026-08-27 12:00",
        "2026-08-27 12:05",
    ])
    result = swing.segment_on_unexpected_gaps(df, "M5", symbol="XAUUSD_o")
    assert len(result["unexpected_gaps"]) == 1
    assert len(result["segments"]) == 2
    assert len(result["active_segment"]) == 2
