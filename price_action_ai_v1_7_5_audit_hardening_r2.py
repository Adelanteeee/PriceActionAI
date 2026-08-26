from __future__ import annotations

import argparse
import importlib
import math
import re
import sys
import webbrowser
from collections import Counter
from pathlib import Path
from typing import Any

import pandas as pd
import plotly.graph_objects as go

VERSION = "1.7.5-audit-hardening-r2"
CORE_MODULE = "price_action_ai_v1_7_5_offline_temporal_gate"
MIN_REFERENCE_LEGS = 3
WEEKEND_MAX_GAP_DAYS = 4
GAP_TOLERANCE_BARS = 3

_TIMEFRAME_MINUTES = {"M5": 5, "M15": 15, "M30": 30, "H1": 60}
_FX_CODES = {
    "USD", "EUR", "GBP", "JPY", "CHF", "AUD", "NZD", "CAD", "NOK", "SEK", "DKK",
    "SGD", "HKD", "CNH", "CNY", "MXN", "ZAR", "TRY", "PLN", "HUF", "CZK",
}


def timeframe_delta(timeframe: str) -> pd.Timedelta:
    tf = str(timeframe).upper()
    if tf not in _TIMEFRAME_MINUTES:
        raise ValueError(f"Unsupported timeframe for audit hardening: {timeframe}")
    return pd.Timedelta(minutes=_TIMEFRAME_MINUTES[tf])


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


def classify_time_gaps(df: pd.DataFrame, timeframe: str) -> dict[str, list[dict[str, Any]]]:
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
            continue

        if _crosses_weekend(prev, curr) and delta <= pd.Timedelta(days=WEEKEND_MAX_GAP_DAYS):
            gap["reason"] = "SCHEDULED_WEEKEND"
            scheduled.append(gap)
            continue

        if sig_counts[gap["signature"]] >= 2:
            gap["reason"] = "RECURRING_SESSION_CLOSURE"
            scheduled.append(gap)
            continue

        gap["reason"] = "UNEXPECTED_DATA_GAP"
        unexpected.append(gap)

    return {"scheduled": scheduled, "unexpected": unexpected}


def segment_on_unexpected_gaps(df: pd.DataFrame, timeframe: str) -> dict[str, Any]:
    if len(df) == 0:
        empty = df.copy().reset_index(drop=True)
        return {"segments": [empty], "active_segment": empty, "scheduled_gaps": [], "unexpected_gaps": []}

    ordered = df.copy()
    ordered["time"] = pd.to_datetime(ordered["time"])
    ordered = ordered.sort_values("time").reset_index(drop=True)
    ordered["source_index"] = range(len(ordered))

    gaps = classify_time_gaps(ordered, timeframe)
    boundaries = [g["new_segment_index"] for g in gaps["unexpected"]]
    starts = [0] + boundaries
    ends = boundaries + [len(ordered)]

    segments: list[pd.DataFrame] = []
    for start, end in zip(starts, ends):
        segments.append(ordered.iloc[start:end].copy().reset_index(drop=True))

    active = segments[-1].copy().reset_index(drop=True)
    return {
        "segments": segments,
        "active_segment": active,
        "scheduled_gaps": gaps["scheduled"],
        "unexpected_gaps": gaps["unexpected"],
    }


def reference_data_status(thrusts: list[float], min_legs: int = MIN_REFERENCE_LEGS) -> str:
    valid = [float(x) for x in thrusts if x is not None and math.isfinite(float(x)) and float(x) > 0]
    return "OK" if len(valid) >= int(min_legs) else "INSUFFICIENT_DATA"


def _clean_symbol_name(symbol: str) -> str:
    return "".join(ch for ch in str(symbol).upper() if ch.isalpha())


def _looks_like_fx(symbol: str, path: str = "") -> bool:
    if "FOREX" in str(path).upper() or "FX" in str(path).upper().split("\\"):
        return True
    clean = _clean_symbol_name(symbol)
    if len(clean) >= 6:
        base, quote = clean[:3], clean[3:6]
        return base in _FX_CODES and quote in _FX_CODES
    return False


def symbol_display_spec(symbol: str, symbol_info: Any | None) -> dict[str, Any]:
    digits = int(getattr(symbol_info, "digits", 5) if symbol_info is not None else 5)
    point = float(getattr(symbol_info, "point", 10 ** (-digits)) if symbol_info is not None else 10 ** (-digits))
    path = str(getattr(symbol_info, "path", "") if symbol_info is not None else "")
    is_fx = _looks_like_fx(symbol, path)
    pip_size = None
    if is_fx:
        pip_size = point * 10.0 if digits in (3, 5) else point
    return {"symbol": symbol, "digits": digits, "point": point, "is_fx": is_fx, "pip_size": pip_size}


def format_price(value: float, spec: dict[str, Any]) -> str:
    return f"{float(value):.{int(spec['digits'])}f}"


def format_delta(value: float, spec: dict[str, Any]) -> str:
    digits = int(spec["digits"])
    if spec.get("is_fx"):
        return f"{float(value):.{digits}f}"
    return f"{float(value):.{max(2, min(digits, 6))}f}"


def raw_to_pips(value: float, spec: dict[str, Any]) -> float | None:
    pip = spec.get("pip_size")
    if pip is None or pip <= 0:
        return None
    return float(value) / float(pip)


def atr_normalized(value: float, atr_value: float | None) -> float | None:
    if atr_value is None or not math.isfinite(float(atr_value)) or float(atr_value) <= 0:
        return None
    return float(value) / float(atr_value)


def _pivot_key(p: dict[str, Any]) -> tuple[int, str, float]:
    return (int(p["index"]), str(p["kind"]), round(float(p["price"]), 12))


def audit_counts(structural: list[dict], major: list[dict], major_removed: list[dict]) -> dict[str, Any]:
    structural_keys = [_pivot_key(p) for p in structural]
    structural_set = set(structural_keys)
    major_set = {_pivot_key(p) for p in major if _pivot_key(p) in structural_set}
    removed_set = set()
    for item in major_removed:
        if not isinstance(item, dict):
            continue
        pivot = item.get("pivot") if isinstance(item.get("pivot"), dict) else item
        if all(k in pivot for k in ("index", "kind", "price")):
            key = _pivot_key(pivot)
            if key in structural_set:
                removed_set.add(key)

    accounted = major_set | removed_set
    leftover = [k for k in structural_keys if k not in accounted]
    pos = {k: i for i, k in enumerate(structural_keys)}
    accounted_positions = [pos[k] for k in accounted if k in pos]
    last_accounted = max(accounted_positions) if accounted_positions else -1
    provisional = [k for k in leftover if pos[k] > last_accounted]
    unaccounted = [k for k in leftover if k not in provisional]
    total = len(major_set) + len(removed_set) + len(provisional) + len(unaccounted)

    return {
        "structural": len(structural_set),
        "major_unique": len(major_set),
        "removed_events": len(major_removed),
        "removed_unique": len(removed_set),
        "right_edge_provisional": len(provisional),
        "right_edge_provisional_keys": provisional,
        "unaccounted": len(unaccounted),
        "unaccounted_keys": unaccounted,
        "invariant_ok": total == len(structural_set) and len(unaccounted) == 0,
    }


def structural_filter_audit(raw_count: int, structural_count: int) -> dict[str, Any]:
    removed = max(0, int(raw_count) - int(structural_count))
    return {
        "raw": int(raw_count),
        "structural": int(structural_count),
        "removed": removed,
        "label": "NO_STRUCTURAL_REMOVAL" if removed == 0 else "STRUCTURAL_FILTER_APPLIED",
    }


def _detect_symbol_compat(core, mt5, requested: str | None = None) -> str:
    detector = getattr(core, "detect_symbol", None)
    if callable(detector):
        return detector(mt5, requested)

    finder = getattr(core, "find_symbol", None)
    if callable(finder):
        resolved = finder(mt5, requested or "XAUUSD")
        if resolved:
            mt5.symbol_select(resolved, True)
            return resolved

    symbols = mt5.symbols_get()
    if not symbols:
        raise RuntimeError("No MT5 symbols available.")

    names = [x.name for x in symbols]
    key = (requested or "XAUUSD").strip().upper().replace(" ", "")
    aliases = {
        "GOLD": ["XAUUSD", "GOLD"],
        "XAUUSD": ["XAUUSD", "GOLD"],
        "NASDAQ": ["NQ", "NAS100", "NASDAQ", "USTEC", "US100", "NASUSD"],
        "NAS100": ["NQ", "NAS100", "NASDAQ", "USTEC", "US100", "NASUSD"],
        "US100": ["NQ", "NAS100", "NASDAQ", "USTEC", "US100", "NASUSD"],
        "USTEC": ["NQ", "NAS100", "NASDAQ", "USTEC", "US100", "NASUSD"],
        "NQ": ["NQ", "NAS100", "NASDAQ", "USTEC", "US100", "NASUSD"],
        "DOW": ["YM", "US30", "DJ30", "DOW", "DJI"],
        "DJI": ["YM", "US30", "DJ30", "DOW", "DJI"],
        "US30": ["YM", "US30", "DJ30", "DOW", "DJI"],
        "YM": ["YM", "US30", "DJ30", "DOW", "DJI"],
    }
    candidates = aliases.get(key, [key])

    for candidate in candidates:
        for name in names:
            if name.upper() == candidate.upper():
                mt5.symbol_select(name, True)
                return name

    normalized_candidates = [c.upper().replace("_", "") for c in candidates]
    for name in names:
        normalized_name = name.upper().replace("_", "")
        if any(c in normalized_name for c in normalized_candidates):
            mt5.symbol_select(name, True)
            return name

    raise RuntimeError(
        f"Could not auto-detect symbol for '{requested or 'XAUUSD'}'. "
        "Use --symbol with the exact MT5 symbol name."
    )


def _fetch_candles_compat(core, mt5, symbol: str, timeframe: str, count: int) -> pd.DataFrame:
    fn = getattr(core, "fetch_candles", None)
    if callable(fn):
        df = fn(mt5, symbol, timeframe, count)
    else:
        fn = getattr(core, "get_candles", None)
        if not callable(fn):
            raise RuntimeError("Loaded v1.7.5 core has neither fetch_candles() nor get_candles().")
        df = fn(mt5, symbol, timeframe, count)

    if df is None or len(df) == 0:
        raise RuntimeError(f"No candle data returned for {symbol} {timeframe}.")

    out = df.copy()
    out["time"] = pd.to_datetime(out["time"])
    return out.sort_values("time").reset_index(drop=True)


def _structural_pipeline_compat(core, df: pd.DataFrame) -> tuple[list[dict], list[dict], list[dict]]:
    pipeline = getattr(core, "structural_swings", None)
    if callable(pipeline):
        raw, structural, internal = pipeline(df)
        return list(raw), list(structural), list(internal)

    detector = getattr(core, "detect_pivot_candidates", None)
    tagger = getattr(core, "tag_internal_candidates", None)
    if not callable(detector) or not callable(tagger):
        raise RuntimeError("Loaded v1.7.5 core is missing the structural swing pipeline.")

    raw = detector(df)
    structural, internal = tagger(raw)

    diagnostics = getattr(core, "add_swing_diagnostics", None)
    if callable(diagnostics):
        structural = diagnostics(structural)

    return list(raw), list(structural), list(internal)


def _leg_thrusts_compat(core, structural: list[dict]) -> list[float]:
    fn = getattr(core, "leg_thrusts", None)
    if callable(fn):
        return [float(x) for x in fn(structural)]

    fn = getattr(core, "_leg_thrusts", None)
    if callable(fn):
        return [float(x) for x in fn(structural)]

    return [
        abs(float(b["price"]) - float(a["price"]))
        for a, b in zip(structural[:-1], structural[1:])
        if abs(float(b["price"]) - float(a["price"])) > 0
    ]


def _reference_stats_compat(core, thrusts: list[float]) -> dict[str, float | str]:
    stats_fn = getattr(core, "reference_statistics", None)
    snap_fn = getattr(core, "select_nearest_actual_leg", None)

    if callable(stats_fn) and callable(snap_fn):
        stats = stats_fn(thrusts)
        ref, _ = snap_fn(thrusts, stats.get("rms"))
        ref = float(ref or 0.0)
        rms = float(stats.get("rms") or 0.0)
        return {
            "source": "RMS_NEAREST_ACTUAL_LEG",
            "reference": ref,
            "mean": float(stats.get("mean") or 0.0),
            "median": float(stats.get("median") or 0.0),
            "rms": rms,
            "snap_distance": abs(ref - rms),
        }

    estimator = getattr(core, "estimate_reference_leg", None)
    if callable(estimator):
        result = estimator(thrusts)
        if isinstance(result, dict):
            return {
                "source": str(result.get("source", "RMS_NEAREST_ACTUAL_LEG")),
                "reference": float(result.get("reference", 0.0)),
                "mean": float(result.get("mean", 0.0)),
                "median": float(result.get("median", 0.0)),
                "rms": float(result.get("rms", 0.0)),
                "snap_distance": float(result.get("snap_distance", 0.0)),
            }

    raise RuntimeError("Loaded v1.7.5 core does not expose a compatible Reference estimator.")


def _compute_atr_compat(core, df: pd.DataFrame) -> pd.Series:
    fn = getattr(core, "compute_atr", None)
    if not callable(fn):
        fn = getattr(core, "calculate_atr", None)
    if not callable(fn):
        raise RuntimeError("Loaded v1.7.5 core has no compatible ATR function.")
    return fn(df)


def _build_audit_chart(
    df: pd.DataFrame,
    symbol: str,
    timeframe: str,
    structural: list[dict],
    major: list[dict],
    summary: str,
):
    fig = go.Figure()
    x = list(range(len(df)))
    labels = df["time"].dt.strftime("%Y-%m-%d %H:%M")

    fig.add_trace(
        go.Candlestick(
            x=x,
            open=df["open"],
            high=df["high"],
            low=df["low"],
            close=df["close"],
            customdata=labels,
            name=symbol,
            hovertemplate=(
                "Time: %{customdata}<br>"
                "Open: %{open}<br>High: %{high}<br>"
                "Low: %{low}<br>Close: %{close}<extra></extra>"
            ),
        )
    )

    sh = [p for p in structural if p.get("kind") == "SH"]
    sl = [p for p in structural if p.get("kind") == "SL"]

    if sh:
        fig.add_trace(
            go.Scatter(
                x=[p["index"] for p in sh],
                y=[p["price"] for p in sh],
                mode="markers",
                marker=dict(symbol="triangle-down", size=7, opacity=0.4),
                name="Structural SH (all)",
            )
        )
    if sl:
        fig.add_trace(
            go.Scatter(
                x=[p["index"] for p in sl],
                y=[p["price"] for p in sl],
                mode="markers",
                marker=dict(symbol="triangle-up", size=7, opacity=0.4),
                name="Structural SL (all)",
            )
        )

    mh = [(i + 1, p) for i, p in enumerate(major) if p.get("kind") == "SH"]
    ml = [(i + 1, p) for i, p in enumerate(major) if p.get("kind") == "SL"]

    if mh:
        fig.add_trace(
            go.Scatter(
                x=[p["index"] for _, p in mh],
                y=[p["price"] for _, p in mh],
                mode="markers+text",
                marker=dict(symbol="triangle-down", size=13),
                text=[f"SH{n}" for n, _ in mh],
                textposition="top center",
                name="Major Swing High",
            )
        )
    if ml:
        fig.add_trace(
            go.Scatter(
                x=[p["index"] for _, p in ml],
                y=[p["price"] for _, p in ml],
                mode="markers+text",
                marker=dict(symbol="triangle-up", size=13),
                text=[f"SL{n}" for n, _ in ml],
                textposition="bottom center",
                name="Major Swing Low",
            )
        )

    if len(major) >= 2:
        fig.add_trace(
            go.Scatter(
                x=[p["index"] for p in major],
                y=[p["price"] for p in major],
                mode="lines",
                name="Major Swing Path",
                hoverinfo="skip",
            )
        )

    tick_count = min(10, len(df))
    if tick_count > 1:
        tickvals = sorted(
            set(
                int(round(i * (len(df) - 1) / (tick_count - 1)))
                for i in range(tick_count)
            )
        )
    else:
        tickvals = [0]

    ticktext = [
        df.iloc[i]["time"].strftime("%b %d\n%H:%M")
        for i in tickvals
    ] if len(df) else []

    fig.update_layout(
        title=f"PriceActionAI {VERSION} | {symbol} | {timeframe} | Active Segment {len(df)}",
        xaxis_title="Active Market Bars (scheduled closures compressed)",
        yaxis_title="Price",
        xaxis_rangeslider_visible=False,
        template="plotly_dark",
        hovermode="x unified",
    )
    fig.update_xaxes(tickmode="array", tickvals=tickvals, ticktext=ticktext)

    fig.add_annotation(
        x=0.01,
        y=0.99,
        xref="paper",
        yref="paper",
        text=summary,
        showarrow=False,
        align="left",
        xanchor="left",
        yanchor="top",
        bgcolor="rgba(0,0,0,0.62)",
        borderpad=6,
        font=dict(size=11),
    )
    return fig


def _load_core():
    try:
        return importlib.import_module(CORE_MODULE)
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            f"Missing {CORE_MODULE}.py. Keep the ADE-9 hardening file in the same folder as "
            "price_action_ai_v1_7_5_offline_temporal_gate.py."
        ) from exc


def _median_atr(core, df: pd.DataFrame) -> float | None:
    if len(df) == 0:
        return None
    atr = _compute_atr_compat(core, df)
    vals = [float(x) for x in atr if pd.notna(x) and float(x) > 0]
    return float(pd.Series(vals).median()) if vals else None


def _summary_text(*, symbol: str, timeframe: str, full_count: int, active_count: int, spec: dict[str, Any], status: str,
                  gap_result: dict[str, Any], raw: list[dict], structural: list[dict], internal_tags: list[dict],
                  major: list[dict], major_removed: list[dict], ref_stats: dict[str, float], median_atr: float | None) -> str:
    count_audit = audit_counts(structural, major, major_removed)
    sf = structural_filter_audit(len(raw), len(structural))
    ref = float(ref_stats.get("reference", 0.0))
    ref_pips = raw_to_pips(ref, spec)
    ref_atr = atr_normalized(ref, median_atr)

    lines = [
        f"STATUS: {status}", f"TF: {timeframe}", f"SNAPSHOT BARS: {full_count}",
        f"ACTIVE SEGMENT BARS: {active_count}", f"SEGMENTS: {len(gap_result['segments'])}",
        f"UNEXPECTED GAPS: {len(gap_result['unexpected_gaps'])}", f"SCHEDULED GAPS: {len(gap_result['scheduled_gaps'])}",
        f"RAW PIVOTS: {len(raw)}", f"STRUCTURAL: {len(structural)}",
        f"RAW->STRUCTURAL REMOVED: {sf['removed']} ({sf['label']})",
        f"MAJOR UNIQUE: {count_audit['major_unique']}",
        f"REMOVED UNIQUE: {count_audit['removed_unique']} (events={count_audit['removed_events']})",
        f"RIGHT_EDGE_PROVISIONAL: {count_audit['right_edge_provisional']}",
        f"COUNT INVARIANT: {'OK' if count_audit['invariant_ok'] else 'ERROR'}",
        f"INTERNAL CANDIDATES: {len(internal_tags)}", f"REFERENCE: {format_delta(ref, spec)}",
    ]
    if ref_pips is not None:
        lines.append(f"REFERENCE PIPS: {ref_pips:.1f}")
    if ref_atr is not None:
        lines.append(f"REFERENCE / MEDIAN ATR: {ref_atr:.2f}")
    lines.extend([
        f"MEAN: {format_delta(float(ref_stats.get('mean', 0.0)), spec)}",
        f"MEDIAN: {format_delta(float(ref_stats.get('median', 0.0)), spec)}",
        f"RMS TARGET: {format_delta(float(ref_stats.get('rms', 0.0)), spec)}",
        "REFERENCE_UNSTABLE: NOT_EVALUATED (ADE-11)", "BALANCE: PARKED",
    ])
    return "<br>".join(lines)


def _write_gap_report(path: Path, gap_result: dict[str, Any]) -> None:
    rows: list[dict[str, Any]] = []
    for category, items in (("SCHEDULED", gap_result["scheduled_gaps"]), ("UNEXPECTED", gap_result["unexpected_gaps"])):
        for g in items:
            rows.append({
                "category": category, "reason": g.get("reason"), "previous_index": g.get("previous_index"),
                "new_segment_index": g.get("new_segment_index"), "previous_time": g.get("previous_time"),
                "current_time": g.get("current_time"), "delta": g.get("delta"),
            })
    pd.DataFrame(rows).to_csv(path, index=False)


_REQUIRED_SNAPSHOT_COLUMNS = ("time", "open", "high", "low", "close")


def load_snapshot_file(path: str | Path) -> pd.DataFrame:
    """Load a fixed OHLC snapshot for reproducible audit.

    This path intentionally does not fetch or refresh any MT5 bars.
    """
    snapshot_path = Path(path).expanduser().resolve()
    if not snapshot_path.exists():
        raise FileNotFoundError(f"Snapshot file not found: {snapshot_path}")

    df = pd.read_csv(snapshot_path)
    missing = [c for c in _REQUIRED_SNAPSHOT_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(
            "Snapshot is missing required columns: " + ", ".join(missing)
        )

    out = df.copy()
    out["time"] = pd.to_datetime(out["time"], errors="coerce")
    if out["time"].isna().any():
        bad = int(out["time"].isna().sum())
        raise ValueError(f"Snapshot contains {bad} invalid time value(s).")

    for col in ("open", "high", "low", "close"):
        out[col] = pd.to_numeric(out[col], errors="coerce")
        if out[col].isna().any():
            bad = int(out[col].isna().sum())
            raise ValueError(f"Snapshot contains {bad} invalid {col} value(s).")

    out = out.sort_values("time").reset_index(drop=True)
    return out


def infer_symbol_from_snapshot(path: str | Path) -> str | None:
    """Best-effort symbol inference from PriceActionAI snapshot filenames."""
    stem = Path(path).stem
    patterns = (
        r"PriceActionAI_snapshot_(?:FULL_|ACTIVE_)?(.+?)_(M5|M15|M30|H1)(?:_\d+)?$",
        r"PriceActionAI_snapshot_(.+?)_(M5|M15|M30|H1)(?:_\d+)?$",
    )
    for pattern in patterns:
        m = re.match(pattern, stem, flags=re.IGNORECASE)
        if m:
            return m.group(1)
    return None


def snapshot_source_description(snapshot_file: str | None) -> str:
    return "FIXED_CSV_SNAPSHOT" if snapshot_file else "MT5_LIVE_FETCH"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="PriceActionAI v1.7.5 ADE-9 Audit Hardening (offline)")
    p.add_argument("--symbol", default=None)
    p.add_argument("--timeframe", default="M30")
    p.add_argument("--count", type=int, default=200)
    p.add_argument(
        "--snapshot-file",
        default=None,
        help="Load an existing fixed CSV snapshot instead of fetching MT5 bars.",
    )
    p.add_argument("--min-reference-legs", type=int, default=MIN_REFERENCE_LEGS)
    p.add_argument("--output-dir", default=None)
    p.add_argument("--no-open", action="store_true")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    core = _load_core()
    timeframe = core.normalize_timeframe(args.timeframe)
    count = max(20, int(args.count))
    output_dir = Path(args.output_dir).expanduser().resolve() if args.output_dir else Path.cwd()
    output_dir.mkdir(parents=True, exist_ok=True)

    mt5 = None
    try:
        if args.snapshot_file:
            full_df = load_snapshot_file(args.snapshot_file)
            symbol = args.symbol or infer_symbol_from_snapshot(args.snapshot_file) or "SNAPSHOT"
            spec = symbol_display_spec(symbol, None)
            source_mode = "FIXED_CSV_SNAPSHOT"
            source_path = Path(args.snapshot_file).expanduser().resolve()
            print("============================================================")
            print(" PriceActionAI v1.7.5 | ADE-9 Fixed Snapshot Audit")
            print("============================================================")
            print(f"Data source      : {source_mode}")
            print(f"Snapshot file   : {source_path}")
            print(f"Symbol          : {symbol}")
            print(f"Timeframe       : {timeframe}")
            print(f"Snapshot bars   : {len(full_df)}")
            print("MT5 data fetch  : DISABLED")
            print("============================================================")
        else:
            mt5 = core._load_mt5()
            core.connect_mt5(mt5)
            symbol = _detect_symbol_compat(core, mt5, args.symbol)
            symbol_info = mt5.symbol_info(symbol)
            spec = symbol_display_spec(symbol, symbol_info)
            full_df = _fetch_candles_compat(core, mt5, symbol, timeframe, count)
            source_mode = "MT5_LIVE_FETCH"
            source_path = None

        gap_result = segment_on_unexpected_gaps(full_df, timeframe)
        active_df = gap_result["active_segment"].copy().reset_index(drop=True)

        raw, structural, internal_tags = _structural_pipeline_compat(core, active_df)
        thrusts = _leg_thrusts_compat(core, structural)
        status = reference_data_status(thrusts, args.min_reference_legs)

        if status == "OK":
            ref_stats = _reference_stats_compat(core, thrusts)
            major, major_removed = core.select_major_swings(
                active_df, structural, ref_stats["reference"]
            )
        else:
            ref_stats = {
                "source": "INSUFFICIENT_DATA",
                "reference": 0.0,
                "mean": 0.0,
                "median": 0.0,
                "rms": 0.0,
                "snap_distance": 0.0,
            }
            major, major_removed = [], []

        median_atr = _median_atr(core, active_df)
        summary = _summary_text(
            symbol=symbol,
            timeframe=timeframe,
            full_count=len(full_df),
            active_count=len(active_df),
            spec=spec,
            status=status,
            gap_result=gap_result,
            raw=raw,
            structural=structural,
            internal_tags=internal_tags,
            major=major,
            major_removed=major_removed,
            ref_stats=ref_stats,
            median_atr=median_atr,
        )
        summary = f"DATA SOURCE: {source_mode}<br>" + summary

        fig = _build_audit_chart(
            active_df, symbol, timeframe, structural, major, summary
        )
        fig.update_layout(
            title=(
                f"PriceActionAI {VERSION} | {symbol} | {timeframe} | "
                f"Snapshot {len(full_df)} | Active Segment {len(active_df)} | {status}"
            )
        )
        if spec.get("is_fx"):
            fig.update_yaxes(tickformat=f".{spec['digits']}f")

        safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in symbol)
        full_snapshot = output_dir / f"PriceActionAI_snapshot_FULL_{safe}_{timeframe}_{len(full_df)}.csv"
        active_snapshot = output_dir / f"PriceActionAI_snapshot_ACTIVE_{safe}_{timeframe}_{len(active_df)}.csv"
        gap_report = output_dir / f"PriceActionAI_gap_audit_{safe}_{timeframe}.csv"
        html_path = output_dir / f"PriceActionAI_{VERSION}_{safe}_{timeframe}.html"
        full_df.to_csv(full_snapshot, index=False)
        active_df.to_csv(active_snapshot, index=False)
        _write_gap_report(gap_report, gap_result)
        fig.write_html(
            str(html_path),
            include_plotlyjs=True,
            full_html=True,
            auto_open=False,
        )

        count_audit = audit_counts(structural, major, major_removed)
        print("\n================ ADE-9 AUDIT HARDENING ================")
        print(f"Data source             : {source_mode}")
        if source_path is not None:
            print(f"Source snapshot         : {source_path}")
        print(f"Status                  : {status}")
        print(f"Symbol                  : {symbol}")
        print(f"Timeframe               : {timeframe}")
        print(f"Snapshot bars           : {len(full_df)}")
        print(f"Segments                : {len(gap_result['segments'])}")
        print(f"Active segment bars     : {len(active_df)}")
        print(f"Unexpected gaps         : {len(gap_result['unexpected_gaps'])}")
        print(f"Scheduled gaps          : {len(gap_result['scheduled_gaps'])}")
        for g in gap_result["unexpected_gaps"]:
            print(
                f"  GAP RESET: {g['previous_time']} -> "
                f"{g['current_time']} | {g['delta']}"
            )
        print(f"Raw pivots              : {len(raw)}")
        print(f"Structural              : {len(structural)}")
        print(f"Major unique            : {count_audit['major_unique']}")
        print(
            f"Removed unique/events   : "
            f"{count_audit['removed_unique']}/{count_audit['removed_events']}"
        )
        print(
            f"Right-edge provisional  : "
            f"{count_audit['right_edge_provisional']}"
        )
        print(
            f"Count invariant         : "
            f"{'OK' if count_audit['invariant_ok'] else 'ERROR'}"
        )
        print(
            f"Reference raw           : "
            f"{format_delta(ref_stats['reference'], spec)}"
        )
        pips = raw_to_pips(ref_stats["reference"], spec)
        if pips is not None:
            print(f"Reference pips          : {pips:.2f}")
        ref_atr = atr_normalized(ref_stats["reference"], median_atr)
        if ref_atr is not None:
            print(f"Reference / median ATR  : {ref_atr:.3f}")
        print(f"Full snapshot           : {full_snapshot}")
        print(f"Active snapshot         : {active_snapshot}")
        print(f"Gap audit               : {gap_report}")
        print(f"Offline HTML            : {html_path}")
        print("========================================================")

        if not args.no_open:
            try:
                webbrowser.open(html_path.resolve().as_uri(), new=2)
            except Exception as exc:
                print(f"[INFO] Could not auto-open local HTML: {exc}")
    finally:
        if mt5 is not None:
            mt5.shutdown()


if __name__ == "__main__":
    main()
