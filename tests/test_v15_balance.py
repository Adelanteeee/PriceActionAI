import importlib.util
from pathlib import Path

MODULE_PATH = Path(__file__).parents[1] / 'price_action_ai_v1_5_balance_spike.py'
spec = importlib.util.spec_from_file_location('pai_v15', MODULE_PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def swing(i, kind, price):
    return {
        'index': i,
        'time': i,
        'kind': kind,
        'price': float(price),
        'atr': 10.0,
        'prominence_atr': 1.0,
    }


def test_detects_choppy_balance_packet():
    swings = [
        swing(0, 'SL', 4500), swing(10, 'SH', 4630), swing(14, 'SL', 4595),
        swing(18, 'SH', 4675), swing(22, 'SL', 4625), swing(26, 'SH', 4695),
        swing(30, 'SL', 4618), swing(34, 'SH', 4660), swing(38, 'SL', 4605),
        swing(42, 'SH', 4670),
    ]
    packets = mod.detect_balance_packets(swings)
    assert packets
    packet = packets[-1]
    assert packet['start'] >= 1
    assert packet['end'] == len(swings) - 1
    assert packet['gross_to_span'] >= mod.BALANCE_MIN_GROSS_TO_SPAN


def test_bullish_entry_keeps_highest_high_as_effective_swing():
    swings = [
        swing(0, 'SL', 4500), swing(10, 'SH', 4630), swing(14, 'SL', 4595),
        swing(18, 'SH', 4675), swing(22, 'SL', 4625), swing(26, 'SH', 4695),
        swing(30, 'SL', 4618), swing(34, 'SH', 4660), swing(38, 'SL', 4605),
        swing(42, 'SH', 4670),
    ]
    packets = mod.detect_balance_packets(swings)
    _, details = mod.compress_balance_packets(swings, packets)
    d = details[-1]
    assert d['entry_direction'] == 'BULLISH'
    assert d['effective']['kind'] == 'SH'
    assert d['effective']['price'] == 4695.0
    assert d['boundary_low'] == 4595.0


def test_bearish_entry_keeps_lowest_low_as_effective_swing():
    swings = [
        swing(0, 'SH', 4700), swing(10, 'SL', 4580), swing(14, 'SH', 4620),
        swing(18, 'SL', 4540), swing(22, 'SH', 4605), swing(26, 'SL', 4520),
        swing(30, 'SH', 4590), swing(34, 'SL', 4535), swing(38, 'SH', 4610),
        swing(42, 'SL', 4550),
    ]
    packets = mod.detect_balance_packets(swings)
    _, details = mod.compress_balance_packets(swings, packets)
    d = details[-1]
    assert d['entry_direction'] == 'BEARISH'
    assert d['effective']['kind'] == 'SL'
    assert d['effective']['price'] == 4520.0
    assert d['boundary_high'] == 4620.0


def test_clean_trend_is_not_compressed_as_balance():
    swings = [
        swing(0, 'SL', 4500), swing(10, 'SH', 4560), swing(20, 'SL', 4545),
        swing(30, 'SH', 4620), swing(40, 'SL', 4600), swing(50, 'SH', 4680),
        swing(60, 'SL', 4660), swing(70, 'SH', 4740),
    ]
    assert mod.detect_balance_packets(swings) == []


def test_reference_estimator_changes_after_balance_compression():
    swings = [
        swing(0, 'SL', 4500), swing(10, 'SH', 4580), swing(20, 'SL', 4510),
        swing(30, 'SH', 4595), swing(34, 'SL', 4555), swing(38, 'SH', 4597),
        swing(42, 'SL', 4558), swing(46, 'SH', 4601), swing(50, 'SL', 4560),
        swing(54, 'SH', 4600),
    ]
    raw_ref, _ = mod.estimate_reference_leg(swings)
    packets = mod.detect_balance_packets(swings)
    compressed, _ = mod.compress_balance_packets(swings, packets)
    clean_ref, _ = mod.estimate_reference_leg(compressed)
    assert raw_ref < 50
    assert clean_ref > raw_ref
