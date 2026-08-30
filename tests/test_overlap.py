from __future__ import annotations

from pathlib import Path
import importlib.util
import math
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "price_action_ai_leg_v0.py"

spec = importlib.util.spec_from_file_location("leg_overlap", SRC)
leg = importlib.util.module_from_spec(spec)
sys.modules["leg_overlap"] = leg
spec.loader.exec_module(leg)


def _ohlc_from_ranges(ranges: list[tuple[float, float]]):
    lows = [float(lo) for lo, _ in ranges]
    highs = [float(hi) for _, hi in ranges]
    opens = [(lo + hi) / 2.0 for lo, hi in ranges]
    closes = list(opens)
    return opens, highs, lows, closes


def _build_one(
    ranges: list[tuple[float, float]],
    *,
    direction: str = "BULLISH",
    start_index: int = 0,
    end_index: int | None = None,
    scheduled_gap_after_indices: set[int] | None = None,
):
    opens, highs, lows, closes = _ohlc_from_ranges(ranges)
    if end_index is None:
        end_index = len(ranges) - 1
    if direction == "BULLISH":
        swings = [
            {"index": start_index, "kind": "SL", "price": lows[start_index]},
            {"index": end_index, "kind": "SH", "price": highs[end_index]},
        ]
    else:
        swings = [
            {"index": start_index, "kind": "SH", "price": highs[start_index]},
            {"index": end_index, "kind": "SL", "price": lows[end_index]},
        ]
    return leg.build_confirmed_legs(
        swings,
        opens=opens,
        highs=highs,
        lows=lows,
        closes=closes,
        scheduled_gap_after_indices=scheduled_gap_after_indices,
    ).legs[0]


def test_disjoint_ranges_have_zero_overlap():
    x = _build_one([(0, 1), (10, 12), (13, 15)])
    assert x.gross_overlap_magnitude == 0.0
    assert x.gross_overlap_capacity == 2.0
    assert x.overlap_ratio == 0.0


def test_identical_ranges_have_ratio_one():
    x = _build_one([(0, 1), (10, 15), (10, 15)])
    assert x.gross_overlap_magnitude == 5.0
    assert x.gross_overlap_capacity == 5.0
    assert x.overlap_ratio == 1.0


def test_full_containment_has_ratio_one():
    x = _build_one([(0, 1), (10, 20), (13, 17)])
    assert x.gross_overlap_magnitude == 4.0
    assert x.gross_overlap_capacity == 4.0
    assert x.overlap_ratio == 1.0


def test_partial_overlap_uses_smaller_range_capacity():
    x = _build_one([(0, 1), (10, 20), (15, 25)])
    assert x.gross_overlap_magnitude == 5.0
    assert x.gross_overlap_capacity == 10.0
    assert x.overlap_ratio == 0.5


def test_point_contact_has_zero_overlap():
    x = _build_one([(0, 1), (10, 15), (15, 20)])
    assert x.gross_overlap_magnitude == 0.0
    assert x.gross_overlap_capacity == 5.0
    assert x.overlap_ratio == 0.0


def test_pair_order_symmetry():
    a = _build_one([(0, 1), (10, 20), (15, 25)])
    b = _build_one([(0, 1), (15, 25), (10, 20)])
    assert a.gross_overlap_magnitude == b.gross_overlap_magnitude
    assert a.gross_overlap_capacity == b.gross_overlap_capacity
    assert a.overlap_ratio == b.overlap_ratio


def test_one_candle_leg_is_zero_zero_none():
    x = _build_one([(0, 2), (10, 15)], start_index=0, end_index=1)
    assert x.active_bar_count == 1
    assert x.gross_overlap_magnitude == 0.0
    assert x.gross_overlap_capacity == 0.0
    assert x.overlap_ratio is None


def test_zero_range_pair_contributes_zero_capacity_and_overlap():
    x = _build_one([(0, 1), (10, 10), (9, 11)])
    assert x.gross_overlap_magnitude == 0.0
    assert x.gross_overlap_capacity == 0.0
    assert x.overlap_ratio is None


def test_mixed_zero_and_nonzero_capacity_pairs_ignore_zero_pair():
    x = _build_one([(0, 1), (10, 10), (9, 11), (10, 12)])
    assert x.gross_overlap_magnitude == 1.0
    assert x.gross_overlap_capacity == 2.0
    assert x.overlap_ratio == 0.5


def test_overlap_is_ratio_of_sums_not_mean_of_pair_ratios():
    x = _build_one([(100, 101), (0, 10), (0, 10), (10, 12)])
    assert x.gross_overlap_magnitude == 10.0
    assert x.gross_overlap_capacity == 12.0
    assert math.isclose(x.overlap_ratio, 10.0 / 12.0)
    assert not math.isclose(x.overlap_ratio, 0.5)


def test_start_index_candle_is_excluded_from_overlap_pairs():
    x = _build_one([(10, 20), (10, 20), (30, 40)])
    assert x.gross_overlap_magnitude == 0.0
    assert x.gross_overlap_capacity == 10.0
    assert x.overlap_ratio == 0.0


def test_end_index_candle_is_included_in_overlap_pairs():
    x = _build_one([(0, 1), (10, 20), (15, 25)], end_index=2)
    assert x.gross_overlap_magnitude == 5.0
    assert x.gross_overlap_capacity == 10.0
    assert x.overlap_ratio == 0.5


def test_adjacent_legs_do_not_share_cross_pivot_pair():
    ranges = [(0, 1), (0, 2), (10, 12), (10, 12), (20, 22)]
    opens, highs, lows, closes = _ohlc_from_ranges(ranges)
    swings = [
        {"index": 0, "kind": "SL", "price": lows[0]},
        {"index": 2, "kind": "SH", "price": highs[2]},
        {"index": 4, "kind": "SL", "price": lows[4]},
    ]
    result = leg.build_confirmed_legs(
        swings, opens=opens, highs=highs, lows=lows, closes=closes
    )
    assert len(result.legs) == 2
    assert result.legs[0].gross_overlap_magnitude == 0.0  # pair (1,2)
    assert result.legs[1].gross_overlap_magnitude == 0.0  # pair (3,4)


def test_scheduled_gap_has_no_special_overlap_logic():
    plain = _build_one([(0, 1), (10, 20), (15, 25)])
    scheduled = _build_one(
        [(0, 1), (10, 20), (15, 25)], scheduled_gap_after_indices={2}
    )
    assert plain.gross_overlap_magnitude == scheduled.gross_overlap_magnitude
    assert plain.gross_overlap_capacity == scheduled.gross_overlap_capacity
    assert plain.overlap_ratio == scheduled.overlap_ratio


def test_overlap_bounds_and_formula_invariants():
    x = _build_one([(0, 1), (0, 10), (5, 15), (14, 18), (30, 35)])
    assert 0.0 <= x.gross_overlap_magnitude <= x.gross_overlap_capacity
    assert x.gross_overlap_capacity > 0.0
    assert 0.0 <= x.overlap_ratio <= 1.0
    assert math.isclose(
        x.overlap_ratio,
        x.gross_overlap_magnitude / x.gross_overlap_capacity,
    )


def test_locked_body_and_shadow_metrics_remain_unchanged_for_known_case():
    opens = [0.5, 11.0, 12.0]
    highs = [1.0, 14.0, 16.0]
    lows = [0.0, 10.0, 11.0]
    closes = [0.5, 13.0, 15.0]
    swings = [
        {"index": 0, "kind": "SL", "price": lows[0]},
        {"index": 2, "kind": "SH", "price": highs[2]},
    ]
    x = leg.build_confirmed_legs(
        swings, opens=opens, highs=highs, lows=lows, closes=closes
    ).legs[0]
    assert x.gross_body_magnitude == 5.0
    assert x.gross_candle_range == 9.0
    assert math.isclose(x.body_strength_ratio, 5.0 / 9.0)
    assert x.gross_upper_shadow == 2.0
    assert x.gross_lower_shadow == 2.0
    assert x.gross_forward_shadow == 2.0
    assert x.gross_backward_shadow == 2.0
    assert x.gross_shadow_magnitude == 4.0
    assert x.shadow_position_imbalance == 0.0
