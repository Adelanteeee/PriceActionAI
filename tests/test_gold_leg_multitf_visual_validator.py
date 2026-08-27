from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "PriceActionAI_Gold_Leg_v0_MultiTF_Visual_Validator.py"


def _load_runner():
    spec = importlib.util.spec_from_file_location("gold_leg_multitf_runner", RUNNER)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_supported_timeframes_are_gold_validation_set():
    runner = _load_runner()
    assert runner.TIMEFRAMES == ("M5", "M15", "M30", "H1")


def test_active_bar_axis_is_contiguous_and_ignores_elapsed_clock_time():
    runner = _load_runner()
    timestamps = [
        "2026-08-21 22:30:00",
        "2026-08-21 23:00:00",
        "2026-08-24 00:00:00",
        "2026-08-24 00:30:00",
    ]
    assert runner.active_bar_axis(timestamps) == [0, 1, 2, 3]


def test_leg_display_coordinates_use_swing_indexes_not_timestamps():
    runner = _load_runner()
    start = {"index": 12, "time": "2026-08-21 23:00:00", "kind": "SL", "price": 4310.0}
    end = {"index": 18, "time": "2026-08-24 02:00:00", "kind": "SH", "price": 4342.5}
    assert runner.leg_display_coordinates(start, end) == ([12, 18], [4310.0, 4342.5])


def test_tick_labels_keep_real_timestamp_while_axis_stays_active_bar_based():
    runner = _load_runner()
    timestamps = [f"2026-08-24 {hour:02d}:00:00" for hour in range(10)]
    tickvals, ticktext = runner.sample_time_ticks(timestamps, max_ticks=4)
    assert all(isinstance(v, int) for v in tickvals)
    assert tickvals[0] == 0
    assert tickvals[-1] == 9
    assert ticktext[0].startswith("2026-08-24")
    assert ticktext[-1].startswith("2026-08-24")
