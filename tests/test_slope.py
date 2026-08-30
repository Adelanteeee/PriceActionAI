from __future__ import annotations

from pathlib import Path
import importlib.util
import math
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "price_action_ai_leg_v0.py"

spec = importlib.util.spec_from_file_location("leg_slope", SRC)
leg = importlib.util.module_from_spec(spec)
sys.modules["leg_slope"] = leg
spec.loader.exec_module(leg)


def _build(
    closes,
    *,
    direction="BULLISH",
    highs=None,
    lows=None,
    opens=None,
    start_index=0,
    end_index=None,
    scheduled_gap_after_indices=None,
):
    if end_index is None:
        end_index = len(closes) - 1
    if highs is None and closes is not None:
        highs = [float(c) + 1.0 for c in closes]
    if lows is None and closes is not None:
        lows = [float(c) - 1.0 for c in closes]
    if opens is None and closes is not None:
        opens = list(map(float, closes))

    if direction == "BULLISH":
        left = {"index": start_index, "kind": "SL", "price": float(lows[start_index]) if lows is not None else 0.0}
        right = {"index": end_index, "kind": "SH", "price": float(highs[end_index]) if highs is not None else 1.0}
    else:
        left = {"index": start_index, "kind": "SH", "price": float(highs[start_index]) if highs is not None else 1.0}
        right = {"index": end_index, "kind": "SL", "price": float(lows[end_index]) if lows is not None else 0.0}

    return leg.build_confirmed_legs(
        [left, right],
        opens=opens,
        highs=highs,
        lows=lows,
        closes=closes,
        scheduled_gap_after_indices=scheduled_gap_after_indices,
    ).legs[0]


def test_bullish_linear_close_sequence_has_expected_raw_directional_and_normalized_slope():
    x = _build([0, 10, 12, 14, 16])
    assert math.isclose(x.close_ols_slope, 2.0)
    assert math.isclose(x.directional_close_ols_slope, 2.0)
    assert math.isclose(x.normalized_directional_close_ols_slope, 1.0)


def test_bearish_linear_close_sequence_flips_directional_sign():
    x = _build([20, 16, 14, 12, 10], direction="BEARISH")
    assert math.isclose(x.close_ols_slope, -2.0)
    assert math.isclose(x.directional_close_ols_slope, 2.0)
    assert math.isclose(x.normalized_directional_close_ols_slope, 1.0)


def test_structurally_opposing_slope_is_negative_after_direction_mapping():
    x = _build([0, 16, 14, 12, 10], direction="BULLISH")
    assert math.isclose(x.close_ols_slope, -2.0)
    assert math.isclose(x.directional_close_ols_slope, -2.0)
    assert math.isclose(x.normalized_directional_close_ols_slope, -1.0)


def test_one_candle_leg_returns_all_none():
    x = _build([0, 10], end_index=1)
    assert x.active_bar_count == 1
    assert x.close_ols_slope is None
    assert x.directional_close_ols_slope is None
    assert x.normalized_directional_close_ols_slope is None


def test_missing_close_returns_all_none():
    highs = [1.0, 3.0, 4.0]
    lows = [0.0, 1.0, 2.0]
    opens = [0.5, 2.0, 3.0]
    swings = [
        {"index": 0, "kind": "SL", "price": 0.0},
        {"index": 2, "kind": "SH", "price": 4.0},
    ]
    x = leg.build_confirmed_legs(swings, opens=opens, highs=highs, lows=lows, closes=None).legs[0]
    assert x.close_ols_slope is None
    assert x.directional_close_ols_slope is None
    assert x.normalized_directional_close_ols_slope is None


def test_close_available_but_range_unavailable_keeps_raw_and_directional_only():
    closes = [0.0, 10.0, 12.0, 14.0]
    swings = [
        {"index": 0, "kind": "SL", "price": 0.0},
        {"index": 3, "kind": "SH", "price": 14.0},
    ]
    x = leg.build_confirmed_legs(swings, closes=closes).legs[0]
    assert math.isclose(x.close_ols_slope, 2.0)
    assert math.isclose(x.directional_close_ols_slope, 2.0)
    assert x.normalized_directional_close_ols_slope is None


def test_zero_total_range_yields_zero_raw_and_directional_but_normalized_none():
    closes = [5.0, 5.0, 5.0, 5.0]
    highs = lows = opens = list(closes)
    x = _build(closes, highs=highs, lows=lows, opens=opens)
    assert x.close_ols_slope == 0.0
    assert x.directional_close_ols_slope == 0.0
    assert x.normalized_directional_close_ols_slope is None


def test_zero_slope_with_positive_mean_range_normalizes_to_zero():
    closes = [0.0, 10.0, 10.0, 10.0]
    highs = [1.0, 11.0, 11.0, 11.0]
    lows = [-1.0, 9.0, 9.0, 9.0]
    x = _build(closes, highs=highs, lows=lows)
    assert x.close_ols_slope == 0.0
    assert x.directional_close_ols_slope == 0.0
    assert x.normalized_directional_close_ols_slope == 0.0


def test_normalized_slope_is_not_clipped():
    closes = [0.0, 10.0, 20.0, 30.0]
    highs = [0.5, 10.5, 20.5, 30.5]
    lows = [-0.5, 9.5, 19.5, 29.5]
    x = _build(closes, highs=highs, lows=lows)
    assert math.isclose(x.close_ols_slope, 10.0)
    assert x.normalized_directional_close_ols_slope > 1.0


def test_start_index_close_is_excluded():
    x = _build([999.0, 10.0, 12.0, 14.0])
    assert math.isclose(x.close_ols_slope, 2.0)


def test_end_index_close_is_included():
    x = _build([0.0, 10.0, 12.0, 20.0])
    # OLS on owned closes [10,12,20] with x=[1,2,3] -> beta=5
    assert math.isclose(x.close_ols_slope, 5.0)


def test_scheduled_gap_does_not_change_active_bar_indexing():
    plain = _build([0.0, 10.0, 15.0, 20.0])
    scheduled = _build([0.0, 10.0, 15.0, 20.0], scheduled_gap_after_indices={2})
    assert plain.close_ols_slope == scheduled.close_ols_slope
    assert plain.directional_close_ols_slope == scheduled.directional_close_ols_slope
    assert plain.normalized_directional_close_ols_slope == scheduled.normalized_directional_close_ols_slope


def test_same_ols_slope_can_have_different_noise_structure():
    clean = _build([0.0, 10.0, 12.0, 14.0, 16.0])
    noisy = _build([0.0, 8.0, 16.0, 10.0, 20.0])
    assert math.isclose(clean.close_ols_slope, noisy.close_ols_slope)


def test_locked_overlap_body_and_shadow_fields_remain_available():
    x = _build([0.0, 10.0, 12.0, 14.0])
    assert hasattr(x, "gross_body_magnitude")
    assert hasattr(x, "gross_shadow_magnitude")
    assert hasattr(x, "gross_overlap_magnitude")
    assert hasattr(x, "gross_overlap_capacity")
    assert hasattr(x, "overlap_ratio")
