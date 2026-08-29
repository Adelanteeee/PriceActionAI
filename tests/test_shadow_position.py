from __future__ import annotations

from pathlib import Path
import importlib.util
import math
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "price_action_ai_leg_v0.py"

spec = importlib.util.spec_from_file_location("leg_shadow_position", SRC)
leg = importlib.util.module_from_spec(spec)
sys.modules["leg_shadow_position"] = leg
spec.loader.exec_module(leg)

TOL = 1e-12


def _build(direction, opens, highs, lows, closes, *, scheduled_gap_after_indices=None):
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
        scheduled_gap_after_indices=scheduled_gap_after_indices,
    ).legs[0]


def test_bullish_maps_upper_to_forward_and_lower_to_backward():
    x = _build("BULLISH", [10, 10], [10, 14], [10, 8], [10, 12])
    assert math.isclose(x.gross_upper_shadow, 2.0, abs_tol=TOL)
    assert math.isclose(x.gross_lower_shadow, 2.0, abs_tol=TOL)
    assert math.isclose(x.gross_forward_shadow, 2.0, abs_tol=TOL)
    assert math.isclose(x.gross_backward_shadow, 2.0, abs_tol=TOL)


def test_bearish_maps_lower_to_forward_and_upper_to_backward():
    x = _build("BEARISH", [10, 10], [10, 14], [10, 8], [10, 12])
    assert math.isclose(x.gross_forward_shadow, 2.0, abs_tol=TOL)
    assert math.isclose(x.gross_backward_shadow, 2.0, abs_tol=TOL)


def test_forward_only_shadow_is_minus_one():
    x = _build("BULLISH", [10, 10], [10, 15], [10, 10], [10, 12])
    assert math.isclose(x.gross_shadow_magnitude, 3.0, abs_tol=TOL)
    assert math.isclose(x.shadow_position_imbalance, -1.0, abs_tol=TOL)


def test_backward_only_shadow_is_plus_one():
    x = _build("BULLISH", [10, 10], [10, 12], [10, 7], [10, 12])
    assert math.isclose(x.gross_shadow_magnitude, 3.0, abs_tol=TOL)
    assert math.isclose(x.shadow_position_imbalance, 1.0, abs_tol=TOL)


def test_equal_shadow_sides_is_zero():
    x = _build("BULLISH", [10, 10], [10, 14], [10, 8], [10, 12])
    assert math.isclose(x.shadow_position_imbalance, 0.0, abs_tol=TOL)


def test_no_shadow_returns_none_imbalance():
    x = _build("BULLISH", [10, 10], [10, 12], [10, 10], [10, 12])
    assert math.isclose(x.gross_shadow_magnitude, 0.0, abs_tol=TOL)
    assert x.shadow_position_imbalance is None


def test_doji_candle_counts_both_shadows_and_zero_body():
    x = _build("BULLISH", [10, 11], [10, 14], [10, 8], [10, 11])
    assert math.isclose(x.gross_body_magnitude, 0.0, abs_tol=TOL)
    assert math.isclose(x.gross_upper_shadow, 3.0, abs_tol=TOL)
    assert math.isclose(x.gross_lower_shadow, 3.0, abs_tol=TOL)
    assert math.isclose(x.gross_shadow_magnitude, 6.0, abs_tol=TOL)


def test_zero_range_candle_has_zero_shadow_and_none_imbalance():
    x = _build("BULLISH", [10, 10], [10, 10], [10, 10], [10, 10])
    assert math.isclose(x.gross_upper_shadow, 0.0, abs_tol=TOL)
    assert math.isclose(x.gross_lower_shadow, 0.0, abs_tol=TOL)
    assert math.isclose(x.gross_shadow_magnitude, 0.0, abs_tol=TOL)
    assert x.shadow_position_imbalance is None


def test_start_index_is_excluded_and_end_index_is_included():
    x = _build(
        "BULLISH",
        [50, 10, 20],
        [100, 14, 25],
        [0, 9, 18],
        [50, 13, 22],
    )
    assert x.active_bar_count == 2
    assert math.isclose(x.gross_upper_shadow, 4.0, abs_tol=TOL)
    assert math.isclose(x.gross_lower_shadow, 3.0, abs_tol=TOL)


def test_adjacent_legs_do_not_double_own_shared_pivot_candle():
    swings = [
        {"index": 0, "kind": "SL", "price": 9.0},
        {"index": 2, "kind": "SH", "price": 15.0},
        {"index": 4, "kind": "SL", "price": 7.0},
    ]
    opens = [10, 10, 12, 13, 11]
    highs = [11, 13, 15, 14, 12]
    lows = [9, 9, 11, 10, 7]
    closes = [10, 12, 14, 11, 8]
    result = leg.build_confirmed_legs(swings, opens=opens, highs=highs, lows=lows, closes=closes)
    a, b = result.legs
    expected = sum(
        (highs[i] - max(opens[i], closes[i])) + (min(opens[i], closes[i]) - lows[i])
        for i in range(1, 5)
    )
    assert a.active_bar_count + b.active_bar_count == 4
    assert math.isclose(a.gross_shadow_magnitude + b.gross_shadow_magnitude, expected, abs_tol=TOL)


def test_range_decomposition_matches_locked_body_strength():
    x = _build("BULLISH", [10, 10, 12], [10, 15, 16], [10, 8, 11], [10, 13, 14])
    assert math.isclose(x.gross_body_magnitude + x.gross_shadow_magnitude, x.gross_candle_range, rel_tol=0.0, abs_tol=TOL)
    assert math.isclose(x.gross_upper_shadow + x.gross_lower_shadow, x.gross_shadow_magnitude, rel_tol=0.0, abs_tol=TOL)
    assert math.isclose(x.gross_forward_shadow + x.gross_backward_shadow, x.gross_shadow_magnitude, rel_tol=0.0, abs_tol=TOL)


def test_gap_transition_is_not_counted_as_shadow():
    opens = [10, 20]
    highs = [10, 22]
    lows = [10, 19]
    closes = [10, 21]
    plain = _build("BULLISH", opens, highs, lows, closes)
    gap = _build("BULLISH", opens, highs, lows, closes, scheduled_gap_after_indices={1})
    assert math.isclose(plain.gross_shadow_magnitude, gap.gross_shadow_magnitude, abs_tol=TOL)
    assert math.isclose(plain.gross_upper_shadow, gap.gross_upper_shadow, abs_tol=TOL)
    assert math.isclose(plain.gross_lower_shadow, gap.gross_lower_shadow, abs_tol=TOL)


def test_shadow_position_bounds_when_defined():
    x = _build("BEARISH", [10, 12, 11], [10, 15, 14], [10, 8, 9], [10, 9, 12])
    assert x.shadow_position_imbalance is not None
    assert -1.0 <= x.shadow_position_imbalance <= 1.0
