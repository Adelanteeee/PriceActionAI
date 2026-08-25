from datetime import datetime, timedelta

from price_action_ai_v1_3 import collapse_internal_swings, normalize_timeframe


def swing(i, kind, price):
    return {
        "index": i,
        "time": datetime(2026, 8, 25) + timedelta(minutes=5 * i),
        "kind": kind,
        "price": float(price),
        "atr": 5.0,
        "prominence_atr": 1.0,
    }


def kp(items):
    return [(x["kind"], x["price"]) for x in items]


def test_timeframe_aliases_are_supported():
    assert normalize_timeframe("M5") == "M5"
    assert normalize_timeframe("15m") == "M15"
    assert normalize_timeframe("30m") == "M30"
    assert normalize_timeframe("1h") == "H1"


def test_bullish_short_countermove_is_internal():
    swings = [swing(0, "SL", 100), swing(6, "SH", 120), swing(9, "SL", 108), swing(15, "SH", 130)]
    result, removed = collapse_internal_swings(swings)
    assert kp(result) == [("SL", 100.0), ("SH", 130.0)]
    assert len(removed) == 2


def test_bearish_short_countermove_is_internal():
    swings = [swing(0, "SH", 130), swing(5, "SL", 110), swing(8, "SH", 122), swing(14, "SL", 100)]
    result, removed = collapse_internal_swings(swings)
    assert kp(result) == [("SH", 130.0), ("SL", 100.0)]
    assert len(removed) == 2


def test_longer_correction_remains_structural():
    swings = [swing(0, "SL", 100), swing(6, "SH", 120), swing(12, "SL", 110), swing(18, "SH", 130)]
    result, removed = collapse_internal_swings(swings)
    assert kp(result) == kp(swings)
    assert removed == []


def test_near_total_reversal_is_not_hidden():
    swings = [swing(0, "SL", 100), swing(6, "SH", 120), swing(9, "SL", 101), swing(15, "SH", 130)]
    result, removed = collapse_internal_swings(swings)
    assert kp(result) == kp(swings)
    assert removed == []
