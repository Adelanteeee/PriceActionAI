from pathlib import Path
import importlib.util

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "price_action_ai_leg_v0.py"

spec = importlib.util.spec_from_file_location("leg_v0", SRC)
leg_v0 = importlib.util.module_from_spec(spec)
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
