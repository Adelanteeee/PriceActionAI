from pathlib import Path
import importlib.util
import math
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "price_action_ai_leg_v0.py"

spec = importlib.util.spec_from_file_location("leg_v0", SRC)
leg_v0 = importlib.util.module_from_spec(spec)
sys.modules["leg_v0"] = leg_v0
spec.loader.exec_module(leg_v0)


def test_builds_bullish_confirmed_leg():
    result = leg_v0.build_confirmed_legs([
        {"index": 10, "kind": "SL", "price": 100.0},
        {"index": 15, "kind": "SH", "price": 130.0},
    ])

    assert result.errors == []
    assert len(result.legs) == 1
    leg = result.legs[0]
    assert leg.start["index"] == 10
    assert leg.end["index"] == 15
    assert leg.direction == "BULLISH"
    assert leg.active_bar_count == 5
    assert leg.net_thrust == 30.0


def test_builds_bearish_confirmed_leg():
    result = leg_v0.build_confirmed_legs([
        {"index": 20, "kind": "SH", "price": 130.0},
        {"index": 28, "kind": "SL", "price": 110.0},
    ])

    assert result.errors == []
    assert len(result.legs) == 1
    leg = result.legs[0]
    assert leg.direction == "BEARISH"
    assert leg.active_bar_count == 8
    assert leg.net_thrust == 20.0


def test_multiple_alternating_major_swings_build_multiple_legs():
    result = leg_v0.build_confirmed_legs([
        {"index": 3, "kind": "SL", "price": 100.0},
        {"index": 8, "kind": "SH", "price": 115.0},
        {"index": 13, "kind": "SL", "price": 107.0},
    ])

    assert result.errors == []
    assert [leg.direction for leg in result.legs] == ["BULLISH", "BEARISH"]
    assert [leg.active_bar_count for leg in result.legs] == [5, 5]
    assert [leg.net_thrust for leg in result.legs] == [15.0, 8.0]


def test_same_type_major_swings_surface_upstream_error_and_build_no_leg_for_pair():
    left = {"index": 10, "kind": "SL", "price": 100.0}
    right = {"index": 15, "kind": "SL", "price": 95.0}

    result = leg_v0.build_confirmed_legs([left, right])

    assert result.legs == []
    assert len(result.errors) == 1
    error = result.errors[0]
    assert error.code == "UPSTREAM_SWING_INVARIANT_ERROR"
    assert error.pair_index == 0
    assert error.left == left
    assert error.right == right


def test_single_major_swing_has_no_confirmed_leg_yet():
    result = leg_v0.build_confirmed_legs([
        {"index": 10, "kind": "SL", "price": 100.0},
    ])

    assert result.legs == []
    assert result.errors == []


def test_close_path_metrics_use_close_to_close_only_and_keep_net_thrust_separate():
    closes = [100.0, 106.0, 105.0, 114.0]
    result = leg_v0.build_confirmed_legs(
        [
            {"index": 0, "kind": "SL", "price": 99.0},
            {"index": 3, "kind": "SH", "price": 115.0},
        ],
        closes=closes,
    )

    leg = result.legs[0]
    assert leg.net_thrust == 16.0
    assert leg.gross_close_path == 16.0
    assert leg.net_close_displacement == 14.0
    assert math.isclose(leg.directional_efficiency, 14.0 / 16.0)
    assert 0.0 <= leg.directional_efficiency <= 1.0


def test_close_path_penalizes_back_and_forth_without_using_wicks():
    closes = [100.0, 108.0, 102.0, 111.0, 105.0, 115.0]
    result = leg_v0.build_confirmed_legs(
        [
            {"index": 0, "kind": "SL", "price": 98.0},
            {"index": 5, "kind": "SH", "price": 117.0},
        ],
        closes=closes,
    )

    leg = result.legs[0]
    assert leg.gross_close_path == 39.0
    assert leg.net_close_displacement == 15.0
    assert math.isclose(leg.directional_efficiency, 15.0 / 39.0)
    assert leg.directional_efficiency < 0.5


def test_flat_close_path_has_undefined_directional_efficiency():
    result = leg_v0.build_confirmed_legs(
        [
            {"index": 0, "kind": "SL", "price": 99.0},
            {"index": 3, "kind": "SH", "price": 101.0},
        ],
        closes=[100.0, 100.0, 100.0, 100.0],
    )

    leg = result.legs[0]
    assert leg.gross_close_path == 0.0
    assert leg.net_close_displacement == 0.0
    assert leg.directional_efficiency is None


def test_close_path_measurement_is_optional_for_backward_compatibility():
    result = leg_v0.build_confirmed_legs([
        {"index": 0, "kind": "SL", "price": 100.0},
        {"index": 2, "kind": "SH", "price": 110.0},
    ])

    leg = result.legs[0]
    assert leg.gross_close_path is None
    assert leg.net_close_displacement is None
    assert leg.directional_efficiency is None
