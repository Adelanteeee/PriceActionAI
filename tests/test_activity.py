from __future__ import annotations

from pathlib import Path
import importlib.util
import math
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "price_action_ai_leg_v0.py"

spec = importlib.util.spec_from_file_location("leg_activity", SRC)
leg = importlib.util.module_from_spec(spec)
sys.modules["leg_activity"] = leg
spec.loader.exec_module(leg)


def _build(
    tick_volume,
    *,
    direction="BULLISH",
    start_index=0,
    end_index=None,
    scheduled_gap_after_indices=None,
):
    if end_index is None:
        end_index = len(tick_volume) - 1

    if direction == "BULLISH":
        swings = [
            {"index": start_index, "kind": "SL", "price": 10.0},
            {"index": end_index, "kind": "SH", "price": 20.0},
        ]
    else:
        swings = [
            {"index": start_index, "kind": "SH", "price": 20.0},
            {"index": end_index, "kind": "SL", "price": 10.0},
        ]

    return leg.build_confirmed_legs(
        swings,
        tick_volume=tick_volume,
        scheduled_gap_after_indices=scheduled_gap_after_indices,
    ).legs[0]


def test_gross_and_mean_tick_activity_use_owned_active_bars():
    x = _build([999, 100, 200, 300])
    assert x.gross_tick_activity == 600
    assert isinstance(x.gross_tick_activity, int)
    assert x.mean_tick_activity == 200.0
    assert isinstance(x.mean_tick_activity, float)


def test_one_candle_leg_uses_only_end_bar_activity():
    x = _build([999, 123], end_index=1)
    assert x.active_bar_count == 1
    assert x.gross_tick_activity == 123
    assert x.mean_tick_activity == 123.0


def test_one_candle_zero_activity_is_valid_zero_not_none():
    x = _build([999, 0], end_index=1)
    assert x.gross_tick_activity == 0
    assert x.mean_tick_activity == 0.0


def test_missing_entire_tick_volume_series_returns_none_none():
    swings = [
        {"index": 0, "kind": "SL", "price": 10.0},
        {"index": 2, "kind": "SH", "price": 20.0},
    ]
    x = leg.build_confirmed_legs(swings, tick_volume=None).legs[0]
    assert x.gross_tick_activity is None
    assert x.mean_tick_activity is None


def test_start_pivot_value_is_excluded_even_if_invalid():
    x = _build([800.5, 100, 200, 300])
    assert x.gross_tick_activity == 600
    assert x.mean_tick_activity == 200.0


def test_end_index_value_is_included():
    x = _build([0, 100, 200, 900])
    assert x.gross_tick_activity == 1200
    assert x.mean_tick_activity == 400.0


def test_direction_does_not_change_activity():
    bullish = _build([0, 100, 200, 300], direction="BULLISH")
    bearish = _build([0, 100, 200, 300], direction="BEARISH")
    assert bullish.gross_tick_activity == bearish.gross_tick_activity
    assert bullish.mean_tick_activity == bearish.mean_tick_activity


def test_scheduled_gap_has_no_special_activity_adjustment():
    plain = _build([0, 100, 200, 300])
    scheduled = _build([0, 100, 200, 300], scheduled_gap_after_indices={2})
    assert plain.gross_tick_activity == scheduled.gross_tick_activity
    assert plain.mean_tick_activity == scheduled.mean_tick_activity


def test_exact_integral_float_is_accepted_as_integer_tick_count():
    x = _build([0, 100.0, 200.0, 300.0])
    assert x.gross_tick_activity == 600
    assert isinstance(x.gross_tick_activity, int)
    assert x.mean_tick_activity == 200.0


@pytest.mark.parametrize("bad_value", [100.5, -1, float("nan"), float("inf"), float("-inf"), True, "100", None])
def test_invalid_or_partial_missing_owned_tick_value_is_data_integrity_error(bad_value):
    values = [0, 100, bad_value, 300]
    with pytest.raises(ValueError, match="tick_volume"):
        _build(values)


def test_tick_volume_series_must_cover_end_index():
    swings = [
        {"index": 0, "kind": "SL", "price": 10.0},
        {"index": 3, "kind": "SH", "price": 20.0},
    ]
    with pytest.raises(IndexError, match="tick_volume"):
        leg.build_confirmed_legs(swings, tick_volume=[0, 100, 200])


def test_zero_bar_confirmed_leg_is_invariant_error():
    swings = [
        {"index": 1, "kind": "SL", "price": 10.0},
        {"index": 1, "kind": "SH", "price": 20.0},
    ]
    with pytest.raises(AssertionError, match="active_bar_count"):
        leg.build_confirmed_legs(swings, tick_volume=[0, 100, 200])


def test_gross_mean_duration_identity_holds():
    x = _build([0, 101, 202, 304])
    assert x.gross_tick_activity == 607
    assert math.isclose(x.mean_tick_activity * x.active_bar_count, x.gross_tick_activity)


def test_locked_leg_metric_fields_remain_available():
    x = _build([0, 100, 200, 300])
    for field in (
        "gross_close_path",
        "directional_efficiency",
        "directional_continuity_ratio",
        "gross_body_magnitude",
        "gross_shadow_magnitude",
        "gross_overlap_magnitude",
        "close_ols_slope",
        "normalized_directional_close_ols_slope",
    ):
        assert hasattr(x, field)
