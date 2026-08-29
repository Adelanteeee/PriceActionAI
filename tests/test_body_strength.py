from __future__ import annotations

from pathlib import Path
import importlib.util
import math
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "price_action_ai_leg_v0.py"

spec = importlib.util.spec_from_file_location("leg_body_strength", SRC)
leg = importlib.util.module_from_spec(spec)
sys.modules["leg_body_strength"] = leg
spec.loader.exec_module(leg)


def _build(
    direction: str,
    opens: list[float],
    highs: list[float],
    lows: list[float],
    closes: list[float],
):
    if direction == "BULLISH":
        swings = [
            {"index": 0, "kind": "SL", "price": lows[0]},
            {"index": len(closes) - 1, "kind": "SH", "price": highs[-1]},
        ]
    else:
        swings = [
            {"index": 0, "kind": "SH", "price": highs[0]},
            {"index": len(closes) - 1, "kind": "SL", "price": lows[-1]},
        ]
    return leg.build_confirmed_legs(
        swings,
        opens=opens,
        highs=highs,
        lows=lows,
        closes=closes,
    ).legs[0]


def test_body_strength_uses_sum_ratio_and_excludes_start_pivot_candle():
    x = _build(
        "BULLISH",
        opens=[0.0, 10.0, 20.0, 30.0],
        highs=[100.0, 14.0, 26.0, 34.0],
        lows=[0.0, 9.0, 19.0, 29.0],
        closes=[100.0, 13.0, 21.0, 33.0],
    )
    assert x.active_bar_count == 3
    assert x.gross_body_magnitude == 7.0
    assert x.gross_candle_range == 17.0
    assert math.isclose(x.body_strength_ratio, 7.0 / 17.0)


def test_body_strength_is_direction_neutral():
    opens = [100.0, 105.0, 101.0, 108.0]
    highs = [110.0, 108.0, 109.0, 111.0]
    lows = [95.0, 100.0, 99.0, 103.0]
    closes = [102.0, 101.0, 107.0, 104.0]
    bull = _build("BULLISH", opens, highs, lows, closes)
    bear = _build("BEARISH", opens, highs, lows, closes)
    assert bull.gross_body_magnitude == bear.gross_body_magnitude
    assert bull.gross_candle_range == bear.gross_candle_range
    assert bull.body_strength_ratio == bear.body_strength_ratio


def test_zero_gross_range_returns_none_ratio():
    x = _build(
        "BULLISH",
        opens=[10.0, 10.0],
        highs=[10.0, 10.0],
        lows=[10.0, 10.0],
        closes=[10.0, 10.0],
    )
    assert x.gross_body_magnitude == 0.0
    assert x.gross_candle_range == 0.0
    assert x.body_strength_ratio is None


def test_body_strength_invariants_for_valid_ohlc():
    x = _build(
        "BULLISH",
        opens=[10.0, 11.0, 12.0],
        highs=[12.0, 14.0, 15.0],
        lows=[9.0, 10.0, 11.0],
        closes=[11.0, 13.0, 12.0],
    )
    assert 0.0 <= x.gross_body_magnitude <= x.gross_candle_range
    assert 0.0 <= x.body_strength_ratio <= 1.0
