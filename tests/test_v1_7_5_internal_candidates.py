import importlib.util
import math
from pathlib import Path

import pandas as pd

MODULE_PATH = Path(__file__).resolve().parents[1] / 'price_action_ai_v1_7_5_offline_temporal_gate.py'
spec = importlib.util.spec_from_file_location('pai_v171', MODULE_PATH)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def swing(index, kind, price):
    return {
        'index': index,
        'time': pd.Timestamp('2026-08-26 00:00') + pd.Timedelta(minutes=15*index),
        'kind': kind,
        'price': float(price),
        'atr': 5.0,
        'prominence_atr': 1.0,
    }


def flat_df(n=20):
    rows = []
    for i in range(n):
        o = 100.0 + i * 0.1
        c = o + (0.4 if i % 2 == 0 else -0.2)
        hi = max(o, c) + 0.5
        lo = min(o, c) - 0.5
        rows.append({'open': o, 'high': hi, 'low': lo, 'close': c})
    return pd.DataFrame(rows)


def test_internal_pattern_is_tagged_not_deleted():
    swings = [
        swing(0, 'SL', 100),
        swing(3, 'SH', 140),
        swing(6, 'SL', 110),
        swing(9, 'SH', 150),
    ]
    result, candidates = m.collapse_internal_swings(swings)
    assert len(result) == 4, f'expected non-destructive preservation, got {len(result)} swings'
    assert result[1].get('internal_candidate') is True
    assert result[2].get('internal_candidate') is True
    assert len(candidates) == 2


def test_three_bar_countermove_is_temporally_internal_even_if_large():
    swings = [
        swing(0, 'SL', 100),
        swing(3, 'SH', 140),
        swing(6, 'SL', 110),
        swing(9, 'SH', 150),
    ]
    structural, _ = m.collapse_internal_swings(swings)
    major, removed = m.select_major_swings(flat_df(), structural, reference_leg=30.0)
    assert [(x['kind'], x['price']) for x in major] == [('SL', 100.0), ('SH', 150.0)]
    assert len(removed) == 2


def test_bearish_merge_keeps_furthest_low():
    swings = [
        swing(0, 'SH', 200),
        swing(3, 'SL', 150),
        swing(6, 'SH', 160),
        swing(9, 'SL', 130),
    ]
    major, removed = m.select_major_swings(flat_df(), swings, reference_leg=50.0)
    assert len(major) == 2
    assert major[-1]['kind'] == 'SL'
    assert math.isclose(major[-1]['price'], 130.0)


def test_bullish_merge_keeps_furthest_high():
    swings = [
        swing(0, 'SL', 100),
        swing(3, 'SH', 150),
        swing(6, 'SL', 140),
        swing(9, 'SH', 175),
    ]
    major, removed = m.select_major_swings(flat_df(), swings, reference_leg=50.0)
    assert len(major) == 2
    assert major[-1]['kind'] == 'SH'
    assert math.isclose(major[-1]['price'], 175.0)


if __name__ == '__main__':
    tests = [name for name in globals() if name.startswith('test_')]
    failures = []
    for name in tests:
        try:
            globals()[name]()
            print(f'PASS {name}')
        except Exception as exc:
            failures.append((name, exc))
            print(f'FAIL {name}: {exc}')
    if failures:
        raise SystemExit(1)
    print(f'PASS {len(tests)}/{len(tests)}')
