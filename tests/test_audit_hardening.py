import math
from types import SimpleNamespace

import pandas as pd

try:
    import price_action_ai_v1_7_5_audit_hardening as audit
except Exception:
    audit = None


def _df(times):
    n = len(times)
    return pd.DataFrame({
        'time': pd.to_datetime(times),
        'open': [1.0 + i * 0.001 for i in range(n)],
        'high': [1.001 + i * 0.001 for i in range(n)],
        'low': [0.999 + i * 0.001 for i in range(n)],
        'close': [1.0005 + i * 0.001 for i in range(n)],
    })


def test_module_exists():
    assert audit is not None, 'ADE-9 audit hardening module is not implemented yet'


def test_unexpected_multiday_gap_splits_segment_and_resets_active_window():
    assert audit is not None
    df = _df([
        '2026-08-03 00:00', '2026-08-03 00:30', '2026-08-03 01:00',
        '2026-08-20 10:00', '2026-08-20 10:30', '2026-08-20 11:00',
    ])
    result = audit.segment_on_unexpected_gaps(df, 'M30')
    assert len(result['segments']) == 2
    assert result['unexpected_gaps'][0]['new_segment_index'] == 3
    assert len(result['active_segment']) == 3
    assert result['active_segment'].iloc[0]['time'] == pd.Timestamp('2026-08-20 10:00')


def test_weekend_gap_is_scheduled_and_does_not_split():
    assert audit is not None
    df = _df([
        '2026-08-21 20:30', '2026-08-21 21:00',
        '2026-08-24 00:00', '2026-08-24 00:30',
    ])
    result = audit.segment_on_unexpected_gaps(df, 'M30')
    assert len(result['segments']) == 1
    assert result['unexpected_gaps'] == []
    assert result['scheduled_gaps']


def test_repeating_daily_session_closure_is_not_unexpected():
    assert audit is not None
    times = []
    for day in ('2026-08-24', '2026-08-25', '2026-08-26'):
        rng = pd.date_range(f'{day} 09:30', f'{day} 16:00', freq='30min')
        times.extend(str(x) for x in rng)
    df = _df(times)
    result = audit.segment_on_unexpected_gaps(df, 'M30')
    assert result['unexpected_gaps'] == []
    assert len(result['segments']) == 1


def test_reference_sufficiency_does_not_borrow_from_prior_segment():
    assert audit is not None
    assert audit.reference_data_status([1.0, 2.0], min_legs=3) == 'INSUFFICIENT_DATA'
    assert audit.reference_data_status([1.0, 2.0, 3.0], min_legs=3) == 'OK'


def test_fx_precision_and_pip_conversion():
    assert audit is not None
    info = SimpleNamespace(digits=5, point=0.00001, path='Forex\\Majors')
    spec = audit.symbol_display_spec('EURUSD_o', info)
    assert spec['is_fx'] is True
    assert spec['digits'] == 5
    assert math.isclose(spec['pip_size'], 0.0001)
    assert audit.format_price(1.08437, spec) == '1.08437'
    assert math.isclose(audit.raw_to_pips(0.00123, spec), 12.3, rel_tol=1e-9)


def test_count_audit_dedupes_removed_and_exposes_right_edge_provisional():
    assert audit is not None
    structural = [
        {'index': 1, 'kind': 'SH', 'price': 10.0},
        {'index': 2, 'kind': 'SL', 'price': 8.0},
        {'index': 3, 'kind': 'SH', 'price': 11.0},
        {'index': 4, 'kind': 'SL', 'price': 7.0},
        {'index': 5, 'kind': 'SH', 'price': 12.0},
    ]
    major = [structural[0], structural[3]]
    removed = [
        {'pivot': structural[1]}, {'pivot': structural[1]}, {'pivot': structural[2]}
    ]
    result = audit.audit_counts(structural, major, removed)
    assert result['removed_unique'] == 2
    assert result['right_edge_provisional'] == 1
    assert result['unaccounted'] == 0
    assert result['invariant_ok'] is True


def test_raw_structural_diagnostic_explicitly_reports_zero_filtering():
    assert audit is not None
    diag = audit.structural_filter_audit(raw_count=43, structural_count=43)
    assert diag['removed'] == 0
    assert diag['label'] == 'NO_STRUCTURAL_REMOVAL'
