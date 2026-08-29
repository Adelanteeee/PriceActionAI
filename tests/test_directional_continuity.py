from __future__ import annotations

from pathlib import Path
import importlib.util
import math
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "price_action_ai_leg_v0.py"

spec = importlib.util.spec_from_file_location("leg_directional_continuity", SRC)
leg = importlib.util.module_from_spec(spec)
sys.modules["leg_directional_continuity"] = leg
spec.loader.exec_module(leg)


def _build(direction: str, closes: list[float], scheduled_gap_after_indices=None):
    if direction == "BULLISH":
        swings = [
            {"index": 0, "kind": "SL", "price": min(closes) - 1.0},
            {"index": len(closes) - 1, "kind": "SH", "price": max(closes) + 1.0},
        ]
    else:
        swings = [
            {"index": 0, "kind": "SH", "price": max(closes) + 1.0},
            {"index": len(closes) - 1, "kind": "SL", "price": min(closes) - 1.0},
        ]
    return leg.build_confirmed_legs(
        swings,
        closes=closes,
        scheduled_gap_after_indices=scheduled_gap_after_indices,
    ).legs[0]


def test_bullish_directional_continuity_counts_close_steps():
    x = _build("BULLISH", [100.0, 101.0, 102.0, 101.0, 103.0])
    assert x.active_bar_count == 4
    assert x.aligned_close_steps == 3
    assert x.opposing_close_steps == 1
    assert x.flat_close_steps == 0
    assert x.directional_continuity_ratio == 0.75
    assert x.aligned_close_steps + x.opposing_close_steps + x.flat_close_steps == x.active_bar_count


def test_bearish_directional_continuity_counts_flat_steps_in_denominator():
    x = _build("BEARISH", [100.0, 99.0, 99.0, 98.0, 99.0])
    assert x.active_bar_count == 4
    assert x.aligned_close_steps == 2
    assert x.opposing_close_steps == 1
    assert x.flat_close_steps == 1
    assert x.directional_continuity_ratio == 0.5
    assert x.aligned_close_steps + x.opposing_close_steps + x.flat_close_steps == x.active_bar_count


def test_continuity_is_step_share_not_run_length():
    a = _build("BULLISH", [100.0, 101.0, 102.0, 103.0, 102.0, 101.0, 102.0])
    b = _build("BULLISH", [100.0, 101.0, 100.0, 101.0, 100.0, 101.0, 102.0])
    assert a.aligned_close_steps == b.aligned_close_steps == 4
    assert a.directional_continuity_ratio == b.directional_continuity_ratio == 4.0 / 6.0


def test_scheduled_gap_transition_is_counted_normally():
    x = _build(
        "BULLISH",
        [100.0, 101.0, 110.0, 109.0],
        scheduled_gap_after_indices={2},
    )
    assert x.aligned_close_steps == 2
    assert x.opposing_close_steps == 1
    assert x.flat_close_steps == 0
    assert math.isclose(x.directional_continuity_ratio, 2.0 / 3.0)
    assert x.gap_path_contribution == 9.0


def test_close_data_absent_returns_none_for_all_continuity_fields():
    result = leg.build_confirmed_legs([
        {"index": 0, "kind": "SL", "price": 100.0},
        {"index": 3, "kind": "SH", "price": 110.0},
    ])
    x = result.legs[0]
    assert x.aligned_close_steps is None
    assert x.opposing_close_steps is None
    assert x.flat_close_steps is None
    assert x.directional_continuity_ratio is None


def test_zero_active_bar_count_has_none_ratio():
    metrics = leg._close_path_metrics(
        closes=[100.0],
        start_index=0,
        end_index=0,
        direction="BULLISH",
        scheduled_gap_after_indices=set(),
    )
    aligned, opposing, flat, ratio = metrics[7:11]
    assert aligned == 0
    assert opposing == 0
    assert flat == 0
    assert ratio is None
