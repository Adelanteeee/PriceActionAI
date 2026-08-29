from __future__ import annotations

from pathlib import Path
import importlib.util
import math
import sys

ROOT = Path(__file__).resolve().parents[1]


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


leg = load("ade12_leg", ROOT / "src" / "price_action_ai_leg_v0.py")


def test_signed_metrics_penalize_bullish_leg_when_closes_move_down():
    result = leg.build_confirmed_legs(
        [
            {"index": 0, "kind": "SL", "price": 99.0},
            {"index": 3, "kind": "SH", "price": 115.0},
        ],
        closes=[110.0, 106.0, 103.0, 100.0],
    )
    x = result.legs[0]
    assert x.net_close_displacement == 10.0
    assert x.signed_close_displacement == -10.0
    assert x.direction_agreement is False
    assert x.directional_efficiency == 0.0
    assert x.close_confirmation_ratio == 0.0


def test_signed_metrics_reward_bearish_leg_when_closes_move_down():
    result = leg.build_confirmed_legs(
        [
            {"index": 0, "kind": "SH", "price": 120.0},
            {"index": 3, "kind": "SL", "price": 100.0},
        ],
        closes=[116.0, 112.0, 108.0, 104.0],
    )
    x = result.legs[0]
    assert x.signed_close_displacement == 12.0
    assert x.direction_agreement is True
    assert x.gross_close_path == 12.0
    assert x.directional_efficiency == 1.0
    assert math.isclose(x.close_confirmation_ratio, 12.0 / 20.0)


def test_temporal_profile_tags_are_diagnostic_only():
    swings = [
        {"index": 0, "kind": "SL", "price": 100.0},
        {"index": 3, "kind": "SH", "price": 110.0},
        {"index": 7, "kind": "SL", "price": 101.0},
        {"index": 22, "kind": "SH", "price": 120.0},
        {"index": 38, "kind": "SL", "price": 105.0},
    ]
    closes = [100.0 + i * 0.1 for i in range(39)]
    result = leg.build_confirmed_legs(swings, closes=closes)
    assert [x.active_bar_count for x in result.legs] == [3, 4, 15, 16]
    assert [x.temporal_profile_tag for x in result.legs] == [
        "UNDER_SAMPLED",
        "NORMAL_TEMPORAL_PROFILE",
        "NORMAL_TEMPORAL_PROFILE",
        "HIGHER_TF_CANDIDATE",
    ]
    assert len(result.legs) == 4


def test_gap_path_contribution_is_reported_separately_from_gross_path():
    result = leg.build_confirmed_legs(
        [
            {"index": 0, "kind": "SL", "price": 99.0},
            {"index": 3, "kind": "SH", "price": 115.0},
        ],
        closes=[100.0, 102.0, 110.0, 112.0],
        scheduled_gap_after_indices={2},
    )
    x = result.legs[0]
    assert x.gross_close_path == 12.0
    assert x.gap_path_contribution == 8.0
    assert math.isclose(x.gap_path_share, 8.0 / 12.0)


def test_previous_close_path_behavior_is_preserved_when_direction_agrees():
    result = leg.build_confirmed_legs(
        [
            {"index": 0, "kind": "SL", "price": 99.0},
            {"index": 3, "kind": "SH", "price": 115.0},
        ],
        closes=[100.0, 106.0, 105.0, 114.0],
    )
    x = result.legs[0]
    assert x.net_thrust == 16.0
    assert x.gross_close_path == 16.0
    assert x.net_close_displacement == 14.0
    assert x.signed_close_displacement == 14.0
    assert math.isclose(x.directional_efficiency, 14.0 / 16.0)


def test_same_type_major_still_surfaces_upstream_error():
    result = leg.build_confirmed_legs([
        {"index": 10, "kind": "SL", "price": 100.0},
        {"index": 15, "kind": "SL", "price": 95.0},
    ])
    assert result.legs == []
    assert len(result.errors) == 1
    assert result.errors[0].code == "UPSTREAM_SWING_INVARIANT_ERROR"
