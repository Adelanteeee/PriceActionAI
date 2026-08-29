from __future__ import annotations

from collections import Counter
from typing import Any

import pandas as pd

WEEKEND_MAX_GAP_DAYS = 4
GAP_TOLERANCE_BARS = 3
_TIMEFRAME_MINUTES = {"M5": 5, "M15": 15, "M30": 30, "H1": 60}


def normalize_timeframe(value: str) -> str:
    cleaned = str(value).strip().upper().replace(" ", "")
    aliases = {
        "5": "M5", "5M": "M5", "M5": "M5",
        "15": "M15", "15M": "M15", "M15": "M15",
        "30": "M30", "30M": "M30", "M30": "M30",
        "60": "H1", "60M": "H1", "1H": "H1", "H1": "H1",
    }
    if cleaned not in aliases:
        raise ValueError(f"Unsupported timeframe: {value}")
    return aliases[cleaned]


def timeframe_delta(timeframe: str) -> pd.Timedelta:
    return pd.Timedelta(minutes=_TIMEFRAME_MINUTES[normalize_timeframe(timeframe)])


def _crosses_weekend(start: pd.Timestamp, end: pd.Timestamp) -> bool:
    if end <= start:
        return False
    day = start.normalize()
    last = end.normalize()
    while day <= last:
        if day.weekday() >= 5:
            return True
        day += pd.Timedelta(days=1)
    return False


def _gap_signature(prev: pd.Timestamp, curr: pd.Timestamp, expected: pd.Timedelta) -> tuple[str, str, int]:
    bars = max(1, int(round((curr - prev) / expected)))
    return (prev.strftime("%H:%M"), curr.strftime("%H:%M"), bars)


def _is_xau_symbol(symbol: str | None) -> bool:
    if symbol is None:
        return False
    value = str(symbol).strip().upper()
    return value.startswith("XAUUSD") or value.startswith("GOLD")


def _is_scheduled_xau_daily_closure(
    prev: pd.Timestamp,
    curr: pd.Timestamp,
    timeframe: str,
    symbol: str | None,
) -> bool:
    """Narrow CR for the observed LiteFinance XAU M5 23:55 -> 01:00 closure."""
    if normalize_timeframe(timeframe) != "M5" or not _is_xau_symbol(symbol):
        return False
    if prev.strftime("%H:%M") != "23:55" or curr.strftime("%H:%M") != "01:00":
        return False
    if curr.normalize() != prev.normalize() + pd.Timedelta(days=1):
        return False
    return (curr - prev) == pd.Timedelta(minutes=65)


def classify_time_gaps(
    df: pd.DataFrame,
    timeframe: str,
    *,
    symbol: str | None = None,
) -> dict[str, list[dict[str, Any]]]:
    if "time" not in df.columns:
        raise ValueError("DataFrame must contain a 'time' column")
    if len(df) < 2:
        return {"scheduled": [], "unexpected": []}

    expected = timeframe_delta(timeframe)
    times = pd.to_datetime(df["time"]).reset_index(drop=True)
    candidates: list[dict[str, Any]] = []

    for i in range(1, len(times)):
        prev = times.iloc[i - 1]
        curr = times.iloc[i]
        delta = curr - prev
        if delta > expected * 1.5:
            candidates.append({
                "previous_index": i - 1,
                "new_segment_index": i,
                "previous_time": prev,
                "current_time": curr,
                "delta": delta,
                "signature": _gap_signature(prev, curr, expected),
            })

    sig_counts = Counter(c["signature"] for c in candidates)
    scheduled: list[dict[str, Any]] = []
    unexpected: list[dict[str, Any]] = []

    for gap in candidates:
        delta = gap["delta"]
        prev = gap["previous_time"]
        curr = gap["current_time"]

        if delta <= expected * GAP_TOLERANCE_BARS:
            gap["reason"] = "TOLERATED_BAR_GAP"
            scheduled.append(gap)
        elif _crosses_weekend(prev, curr) and delta <= pd.Timedelta(days=WEEKEND_MAX_GAP_DAYS):
            gap["reason"] = "SCHEDULED_WEEKEND"
            scheduled.append(gap)
        elif _is_scheduled_xau_daily_closure(prev, curr, timeframe, symbol):
            gap["reason"] = "SCHEDULED_XAU_DAILY_CLOSURE"
            scheduled.append(gap)
        elif sig_counts[gap["signature"]] >= 2:
            gap["reason"] = "RECURRING_SESSION_CLOSURE"
            scheduled.append(gap)
        else:
            gap["reason"] = "UNEXPECTED_DATA_GAP"
            unexpected.append(gap)

    return {"scheduled": scheduled, "unexpected": unexpected}


def segment_on_unexpected_gaps(
    df: pd.DataFrame,
    timeframe: str,
    *,
    symbol: str | None = None,
) -> dict[str, Any]:
    if len(df) == 0:
        empty = df.copy().reset_index(drop=True)
        return {
            "segments": [empty],
            "active_segment": empty,
            "scheduled_gaps": [],
            "unexpected_gaps": [],
        }

    ordered = df.copy()
    ordered["time"] = pd.to_datetime(ordered["time"])
    ordered = ordered.sort_values("time").reset_index(drop=True)
    ordered["source_index"] = range(len(ordered))

    gaps = classify_time_gaps(ordered, timeframe, symbol=symbol)
    boundaries = [g["new_segment_index"] for g in gaps["unexpected"]]
    starts = [0] + boundaries
    ends = boundaries + [len(ordered)]
    segments = [ordered.iloc[s:e].copy().reset_index(drop=True) for s, e in zip(starts, ends)]

    return {
        "segments": segments,
        "active_segment": segments[-1].copy().reset_index(drop=True),
        "scheduled_gaps": gaps["scheduled"],
        "unexpected_gaps": gaps["unexpected"],
    }
