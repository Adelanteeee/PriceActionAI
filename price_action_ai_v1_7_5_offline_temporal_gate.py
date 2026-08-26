from __future__ import annotations

import argparse
import math
import os
import sys
import webbrowser
from pathlib import Path
from copy import deepcopy

import pandas as pd
import plotly.graph_objects as go


# ============================================================
# PriceActionAI Visual Research Prototype v1.7.3 EXTREME CARRY-FORWARD
# Sprint 1 — Swing Engine
# Goal: Preserve structural pivots -> tag internal candidates -> RMS-nearest actual Reference -> Major Swing
# ============================================================

VERSION = "1.7.5-offline-temporal-gate"
CANDLE_COUNT = 200
SUPPORTED_TIMEFRAMES = ("M5", "M15", "M30", "H1")

# Pivot candidate baseline (carried forward from v1.2)
PIVOT_LEFT = 2
PIVOT_RIGHT = 2
ATR_PERIOD = 14
MIN_PROMINENCE_ATR = 0.60

# Structural Swing Validation — EXPERIMENTAL v1.3
# A counter-move lasting 1-4 candles can be breathing / pressure drop,
# not a structural correction, IF price resumes and breaks the previous
# directional extreme. Near-total reversals are protected from merging.
MAX_INTERNAL_BARS = 4
MAX_INTERNAL_RETRACE_RATIO = 0.80

# Reference Leg / Major Swing experiment
# A counter-move needs at least this many ACTIVE bars before it can be
# evaluated as an independent correction. Shorter moves remain internal.
MIN_CORRECTION_BARS = 5
REFERENCE_CLUSTER_TOLERANCE = 0.18
MAJOR_REJECT_RATIO = 0.50
MAJOR_ACCEPT_RATIO = 0.70
MID_QUALITY_THRESHOLD = 0.60

# Balance Tagging experiment (Sprint 1 only; NOT the final Range Engine)
BALANCE_MIN_PIVOTS = 5
BALANCE_MIN_GROSS_TO_SPAN = 2.20
BALANCE_MAX_NET_EFFICIENCY = 0.45
BALANCE_MAX_SPAN_TO_MEDIAN_LEG = 2.80



def normalize_timeframe(value: str) -> str:
    if value is None:
        return "M5"

    cleaned = str(value).strip().upper().replace(" ", "")
    aliases = {
        "5": "M5",
        "5M": "M5",
        "M5": "M5",
        "15": "M15",
        "15M": "M15",
        "M15": "M15",
        "30": "M30",
        "30M": "M30",
        "M30": "M30",
        "60": "H1",
        "60M": "H1",
        "1H": "H1",
        "H1": "H1",
    }

    if cleaned not in aliases:
        raise ValueError(
            f"Unsupported timeframe '{value}'. Use one of: M5, M15, M30, H1."
        )

    return aliases[cleaned]


def choose_timeframe(cli_value: str | None) -> str:
    if cli_value:
        return normalize_timeframe(cli_value)

    print("\nSelect timeframe:")
    print("  1) M5")
    print("  2) M15")
    print("  3) M30")
    print("  4) H1")
    raw = input("Timeframe [default M5]: ").strip()

    numeric = {"1": "M5", "2": "M15", "3": "M30", "4": "H1"}
    if raw in numeric:
        return numeric[raw]
    if not raw:
        return "M5"
    return normalize_timeframe(raw)


def _load_mt5():
    try:
        import MetaTrader5 as mt5
    except ImportError:
        print("\n[ERROR] Python package MetaTrader5 is not installed.")
        print("Run: pip install MetaTrader5 pandas plotly")
        sys.exit(1)
    return mt5


def connect_mt5(mt5):
    if not mt5.initialize():
        print("\n[ERROR] Could not connect to MetaTrader 5.")
        print("MT5 error:", mt5.last_error())
        print("Make sure MT5 is OPEN and logged in.")
        sys.exit(1)

    account = mt5.account_info()
    terminal = mt5.terminal_info()

    print("============================================================")
    print(" PriceActionAI v1.7.5 | Correction Temporal Gate")
    print("============================================================")
    print("MT5 connection : OK")
    if account is not None:
        print(f"Account        : {getattr(account, 'login', 'N/A')}")
        print(f"Server         : {getattr(account, 'server', 'N/A')}")
        print(f"Balance        : {getattr(account, 'balance', 'N/A')}")
    if terminal is not None:
        print(f"Data path      : {getattr(terminal, 'data_path', 'N/A')}")
    print("============================================================")


def _candidate_symbol_names(requested: str | None) -> list[str]:
    if requested:
        key = requested.strip().upper().replace(" ", "")
    else:
        key = "GOLD"

    aliases: dict[str, list[str]] = {
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
    return aliases.get(key, [requested] if requested else ["XAUUSD", "GOLD"])


def detect_symbol(mt5, requested: str | None = None) -> str:
    symbols = mt5.symbols_get()
    if not symbols:
        raise RuntimeError("No MT5 symbols available.")

    names = [s.name for s in symbols]
    upper_map = {name.upper(): name for name in names}
    candidates = _candidate_symbol_names(requested)

    for candidate in candidates:
        if not candidate:
            continue
        exact = upper_map.get(candidate.upper())
        if exact:
            mt5.symbol_select(exact, True)
            return exact

    normalized_candidates = [c.upper().replace("_", "") for c in candidates if c]
    for name in names:
        normalized_name = name.upper().replace("_", "")
        if any(c in normalized_name for c in normalized_candidates):
            mt5.symbol_select(name, True)
            return name

    requested_text = requested or "Gold"
    raise RuntimeError(
        f"Could not auto-detect symbol for '{requested_text}'. "
        "Use --symbol with the exact MT5 symbol name."
    )


def timeframe_constant(mt5, timeframe: str):
    mapping = {
        "M5": mt5.TIMEFRAME_M5,
        "M15": mt5.TIMEFRAME_M15,
        "M30": mt5.TIMEFRAME_M30,
        "H1": mt5.TIMEFRAME_H1,
    }
    return mapping[timeframe]


def fetch_candles(mt5, symbol: str, timeframe: str, count: int) -> pd.DataFrame:
    tf_const = timeframe_constant(mt5, timeframe)
    rates = mt5.copy_rates_from_pos(symbol, tf_const, 0, count)
    if rates is None or len(rates) == 0:
        raise RuntimeError(f"No candle data returned for {symbol} {timeframe}.")

    df = pd.DataFrame(rates)
    df["time"] = pd.to_datetime(df["time"], unit="s")
    df = df.sort_values("time").reset_index(drop=True)
    return df


def true_range(df: pd.DataFrame) -> pd.Series:
    prev_close = df["close"].shift(1)
    tr = pd.concat(
        [
            df["high"] - df["low"],
            (df["high"] - prev_close).abs(),
            (df["low"] - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return tr


def compute_atr(df: pd.DataFrame, period: int = ATR_PERIOD) -> pd.Series:
    tr = true_range(df)
    return tr.rolling(period, min_periods=1).mean()


def raw_pivots(
    df: pd.DataFrame,
    left: int = PIVOT_LEFT,
    right: int = PIVOT_RIGHT,
    min_prominence_atr: float = MIN_PROMINENCE_ATR,
) -> list[dict]:
    atr = compute_atr(df)
    out: list[dict] = []

    for i in range(left, len(df) - right):
        row = df.iloc[i]
        window = df.iloc[i - left : i + right + 1]
        local_high = float(window["high"].max())
        local_low = float(window["low"].min())
        a = float(atr.iloc[i]) if not pd.isna(atr.iloc[i]) else 0.0
        if a <= 0:
            continue

        is_high = float(row["high"]) >= local_high
        is_low = float(row["low"]) <= local_low

        if is_high:
            surrounding_low = min(
                float(df.iloc[i - left : i]["low"].min()),
                float(df.iloc[i + 1 : i + right + 1]["low"].min()),
            )
            prominence = (float(row["high"]) - surrounding_low) / a
            if prominence >= min_prominence_atr:
                out.append(
                    {
                        "index": i,
                        "time": row["time"],
                        "kind": "SH",
                        "price": float(row["high"]),
                        "atr": a,
                        "prominence_atr": prominence,
                    }
                )

        if is_low:
            surrounding_high = max(
                float(df.iloc[i - left : i]["high"].max()),
                float(df.iloc[i + 1 : i + right + 1]["high"].max()),
            )
            prominence = (surrounding_high - float(row["low"])) / a
            if prominence >= min_prominence_atr:
                out.append(
                    {
                        "index": i,
                        "time": row["time"],
                        "kind": "SL",
                        "price": float(row["low"]),
                        "atr": a,
                        "prominence_atr": prominence,
                    }
                )

    out.sort(key=lambda x: (x["index"], 0 if x["kind"] == "SL" else 1))
    return out


def enforce_alternation(pivots: list[dict]) -> list[dict]:
    if not pivots:
        return []

    result: list[dict] = []
    for p in pivots:
        if not result:
            result.append(deepcopy(p))
            continue

        last = result[-1]
        if p["kind"] != last["kind"]:
            result.append(deepcopy(p))
            continue

        if p["kind"] == "SH":
            if p["price"] > last["price"]:
                result[-1] = deepcopy(p)
        else:
            if p["price"] < last["price"]:
                result[-1] = deepcopy(p)

    return result


def _internal_pattern_metrics(a: dict, b: dict, c: dict, d: dict) -> dict | None:
    if not (a["kind"] == c["kind"] and b["kind"] == d["kind"]):
        return None
    if a["kind"] == b["kind"]:
        return None

    if a["kind"] == "SL":
        parent_thrust = b["price"] - a["price"]
        counter = b["price"] - c["price"]
        resumes = d["price"] > b["price"]
    else:
        parent_thrust = a["price"] - b["price"]
        counter = c["price"] - b["price"]
        resumes = d["price"] < b["price"]

    if parent_thrust <= 0 or counter < 0:
        return None

    bars = c["index"] - b["index"]
    retrace = counter / parent_thrust if parent_thrust else math.inf
    return {
        "parent_thrust": float(parent_thrust),
        "counter": float(counter),
        "bars": int(bars),
        "retrace": float(retrace),
        "resumes": bool(resumes),
    }


def tag_internal_candidates(swings: list[dict]) -> tuple[list[dict], list[dict]]:
    """Non-destructive v1.7.2 replacement for old pre-Reference collapse.

    The structural swing sequence is preserved. Patterns matching the legacy
    short/internal heuristic are tagged only for diagnostics and later review.
    """
    preserved = [deepcopy(x) for x in swings]
    tags: list[dict] = []

    for i in range(len(preserved) - 3):
        a, b, c, d = preserved[i : i + 4]
        m = _internal_pattern_metrics(a, b, c, d)
        if m is None:
            continue
        if (
            m["resumes"]
            and m["bars"] <= MAX_INTERNAL_BARS
            and m["retrace"] <= MAX_INTERNAL_RETRACE_RATIO
        ):
            tags.append(
                {
                    "start_pos": i,
                    "b_index": b["index"],
                    "c_index": c["index"],
                    "bars": m["bars"],
                    "retrace": m["retrace"],
                    "reason": "INTERNAL_CANDIDATE",
                }
            )

    return preserved, tags


def structural_swings(df: pd.DataFrame) -> tuple[list[dict], list[dict], list[dict]]:
    raw = raw_pivots(df)
    alternating = enforce_alternation(raw)
    preserved, internal_tags = tag_internal_candidates(alternating)
    return raw, preserved, internal_tags


def leg_thrusts(swings: list[dict]) -> list[float]:
    vals: list[float] = []
    for a, b in zip(swings[:-1], swings[1:]):
        thrust = abs(float(b["price"]) - float(a["price"]))
        if thrust > 0:
            vals.append(thrust)
    return vals


def estimate_reference_leg(thrusts: list[float]) -> dict:
    if not thrusts:
        return {
            "source": "NONE",
            "reference": 0.0,
            "mean": 0.0,
            "median": 0.0,
            "rms": 0.0,
            "snap_distance": 0.0,
        }

    vals = [float(x) for x in thrusts if x > 0]
    if not vals:
        return {
            "source": "NONE",
            "reference": 0.0,
            "mean": 0.0,
            "median": 0.0,
            "rms": 0.0,
            "snap_distance": 0.0,
        }

    mean = sum(vals) / len(vals)
    sorted_vals = sorted(vals)
    n = len(sorted_vals)
    if n % 2:
        median = sorted_vals[n // 2]
    else:
        median = (sorted_vals[n // 2 - 1] + sorted_vals[n // 2]) / 2.0
    rms = math.sqrt(sum(x * x for x in vals) / len(vals))

    # Snap the dynamic RMS target to an ACTUAL observed structural leg.
    # Tie-break: smaller actual leg to avoid accidental over-filtering.
    reference = min(vals, key=lambda x: (abs(x - rms), x))
    snap_distance = abs(reference - rms)
    return {
        "source": "RMS_NEAREST_ACTUAL_LEG",
        "reference": float(reference),
        "mean": float(mean),
        "median": float(median),
        "rms": float(rms),
        "snap_distance": float(snap_distance),
    }


def _move_quality(df: pd.DataFrame, a: dict, b: dict) -> float:
    i0, i1 = sorted((int(a["index"]), int(b["index"])))
    if i1 <= i0:
        return 0.0
    seg = df.iloc[i0 : i1 + 1]
    if len(seg) < 2:
        return 0.0

    net = abs(float(b["price"]) - float(a["price"]))
    path = float(seg["close"].diff().abs().sum())
    efficiency = net / path if path > 0 else 0.0

    bodies = (seg["close"] - seg["open"]).abs()
    ranges = (seg["high"] - seg["low"]).replace(0, math.nan)
    body_ratio = float((bodies / ranges).fillna(0).mean())

    if b["price"] >= a["price"]:
        directional = float((seg["close"].diff().fillna(0) > 0).mean())
    else:
        directional = float((seg["close"].diff().fillna(0) < 0).mean())

    score = 0.45 * efficiency + 0.30 * body_ratio + 0.25 * directional
    return max(0.0, min(1.0, score))


def _carry_forward_origin(a: dict, c: dict) -> dict:
    """Preserve the furthest same-type origin extreme when B/C are compressed."""
    if a["kind"] != c["kind"]:
        return deepcopy(a)
    if a["kind"] == "SH":
        return deepcopy(c if c["price"] > a["price"] else a)
    return deepcopy(c if c["price"] < a["price"] else a)


def select_major_swings(
    df: pd.DataFrame,
    structural: list[dict],
    reference_leg: float,
) -> tuple[list[dict], list[dict]]:
    if len(structural) < 2 or reference_leg <= 0:
        return [deepcopy(x) for x in structural], []

    work = [deepcopy(x) for x in structural]
    removed: list[dict] = []
    changed = True

    while changed and len(work) >= 4:
        changed = False
        i = 0
        new: list[dict] = []

        while i < len(work):
            if i + 3 >= len(work):
                new.extend(deepcopy(x) for x in work[i:])
                break

            a, b, c, d = work[i : i + 4]
            m = _internal_pattern_metrics(a, b, c, d)
            if m is None or not m["resumes"]:
                new.append(deepcopy(a))
                i += 1
                continue

            counter = m["counter"]
            ratio = counter / reference_leg if reference_leg else math.inf
            quality = _move_quality(df, b, c)
            counter_bars = int(m["bars"])

            # v1.7.5 Correction Temporal Gate:
            # 1 bar is never an independent correction.
            # 2-4 bars default to internal / pressure drop.
            # >=5 bars become eligible for the existing Reference/Quality rule.
            if counter_bars < MIN_CORRECTION_BARS:
                reject_counter = True
            elif ratio < MAJOR_REJECT_RATIO:
                reject_counter = True
            elif ratio >= MAJOR_ACCEPT_RATIO:
                reject_counter = False
            else:
                reject_counter = quality < MID_QUALITY_THRESHOLD

            if reject_counter:
                origin = _carry_forward_origin(a, c)
                new.append(origin)
                new.append(deepcopy(d))
                removed.extend(
                    [
                        {
                            "pivot": deepcopy(b),
                            "reason": "major compression",
                            "counter": counter,
                            "ratio": ratio,
                            "quality": quality,
                            "counter_bars": counter_bars,
                        },
                        {
                            "pivot": deepcopy(c),
                            "reason": "major compression",
                            "counter": counter,
                            "ratio": ratio,
                            "quality": quality,
                            "counter_bars": counter_bars,
                        },
                    ]
                )
                i += 4
                changed = True
            else:
                new.append(deepcopy(a))
                i += 1

        work = enforce_alternation(new)

    return work, removed


def _tick_positions(n: int, target_ticks: int = 10) -> list[int]:
    if n <= 1:
        return [0]
    step = max(1, round((n - 1) / target_ticks))
    ticks = list(range(0, n, step))
    if ticks[-1] != n - 1:
        ticks.append(n - 1)
    return ticks


def _format_tick_label(ts: pd.Timestamp, timeframe: str) -> str:
    if timeframe == "H1":
        return ts.strftime("%b %d %H:%M")
    return ts.strftime("%b %d %H:%M")


def build_chart(
    df: pd.DataFrame,
    symbol: str,
    timeframe: str,
    raw: list[dict],
    structural: list[dict],
    internal_tags: list[dict],
    major: list[dict],
    major_removed: list[dict],
    ref_stats: dict,
    count: int,
) -> go.Figure:
    x = list(range(len(df)))
    fig = go.Figure()

    custom = [[t.strftime("%Y-%m-%d %H:%M")] for t in df["time"]]
    fig.add_trace(
        go.Candlestick(
            x=x,
            open=df["open"],
            high=df["high"],
            low=df["low"],
            close=df["close"],
            customdata=custom,
            hovertemplate=(
                "Time: %{customdata[0]}<br>"
                "Open: %{open}<br>High: %{high}<br>Low: %{low}<br>Close: %{close}<extra></extra>"
            ),
            name=symbol,
        )
    )

    sh = [p for p in structural if p["kind"] == "SH"]
    sl = [p for p in structural if p["kind"] == "SL"]
    if sh:
        fig.add_trace(
            go.Scatter(
                x=[p["index"] for p in sh],
                y=[p["price"] for p in sh],
                mode="markers",
                marker=dict(symbol="triangle-down", size=7),
                opacity=0.35,
                name="Structural SH (all)",
                hovertext=[f"Structural SH | {p['time']} | {p['price']:.4f}" for p in sh],
                hoverinfo="text",
            )
        )
    if sl:
        fig.add_trace(
            go.Scatter(
                x=[p["index"] for p in sl],
                y=[p["price"] for p in sl],
                mode="markers",
                marker=dict(symbol="triangle-up", size=7),
                opacity=0.35,
                name="Structural SL (all)",
                hovertext=[f"Structural SL | {p['time']} | {p['price']:.4f}" for p in sl],
                hoverinfo="text",
            )
        )

    if major:
        fig.add_trace(
            go.Scatter(
                x=[p["index"] for p in major],
                y=[p["price"] for p in major],
                mode="lines",
                line=dict(width=2.3),
                name="Major Swing Path",
                hoverinfo="skip",
            )
        )
        m_sh = [(i + 1, p) for i, p in enumerate(major) if p["kind"] == "SH"]
        m_sl = [(i + 1, p) for i, p in enumerate(major) if p["kind"] == "SL"]
        if m_sh:
            fig.add_trace(
                go.Scatter(
                    x=[p["index"] for _, p in m_sh],
                    y=[p["price"] for _, p in m_sh],
                    mode="markers+text",
                    marker=dict(symbol="triangle-down", size=12),
                    text=[f"SH{i}" for i, _ in m_sh],
                    textposition="top center",
                    name="Major Swing High",
                    hovertext=[f"Major SH{i} | {p['time']} | {p['price']:.4f}" for i, p in m_sh],
                    hoverinfo="text",
                )
            )
        if m_sl:
            fig.add_trace(
                go.Scatter(
                    x=[p["index"] for _, p in m_sl],
                    y=[p["price"] for _, p in m_sl],
                    mode="markers+text",
                    marker=dict(symbol="triangle-up", size=12),
                    text=[f"SL{i}" for i, _ in m_sl],
                    textposition="bottom center",
                    name="Major Swing Low",
                    hovertext=[f"Major SL{i} | {p['time']} | {p['price']:.4f}" for i, p in m_sl],
                    hoverinfo="text",
                )
            )

    thrusts = leg_thrusts(structural)
    thrust_text = ", ".join(f"{x:.1f}" for x in thrusts[:12])
    if len(thrusts) > 12:
        thrust_text += ", ..."

    summary = (
        f"RAW PIVOTS: {len(raw)}<br>"
        f"STRUCTURAL: {len(structural)}<br>"
        f"MAJOR: {len(major)}<br>"
        f"INTERNAL CANDIDATES: {len(internal_tags)}<br>"
        f"MAJOR REMOVED: {len(major_removed)}<br>"
        f"TF: {timeframe}<br>"
        f"Weekend compression: ON<br>"
        f"Reference source: {ref_stats['source']}<br>"
        f"Reference leg (actual): {ref_stats['reference']:.2f}<br>"
        f"Mean: {ref_stats['mean']:.2f}<br>"
        f"Median: {ref_stats['median']:.2f}<br>"
        f"RMS target: {ref_stats['rms']:.2f}<br>"
        f"Snap distance: {ref_stats['snap_distance']:.2f}<br>"
        f"50%: {ref_stats['reference'] * MAJOR_REJECT_RATIO:.2f}<br>"
        f"70%: {ref_stats['reference'] * MAJOR_ACCEPT_RATIO:.2f}<br>"
        f"Structural leg thrusts: {thrust_text}"
    )

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
        bgcolor="rgba(0,0,0,0.55)",
        borderpad=6,
        font=dict(size=12),
    )

    ticks = _tick_positions(len(df), 10)
    fig.update_xaxes(
        tickmode="array",
        tickvals=ticks,
        ticktext=[_format_tick_label(df.iloc[i]["time"], timeframe) for i in ticks],
        rangeslider_visible=False,
        title="Active Market Bars (scheduled closures compressed)",
    )
    fig.update_yaxes(title="Price")
    fig.update_layout(
        title=(
            f"PriceActionAI v{VERSION} | {symbol} | {timeframe} | Last {count} Candles | "
            "RMS Target -> Actual Reference + Major Swing"
        ),
        template="plotly_dark",
        height=900,
        hovermode="closest",
        margin=dict(l=70, r=180, t=100, b=80),
        legend=dict(x=1.02, y=1),
    )
    return fig


def save_snapshot(df: pd.DataFrame, symbol: str, timeframe: str, count: int, output_dir: Path) -> Path:
    safe_symbol = "".join(c if c.isalnum() or c in "-_" else "_" for c in symbol)
    path = output_dir / f"PriceActionAI_snapshot_{safe_symbol}_{timeframe}_{count}.csv"
    df.to_csv(path, index=False)
    return path


def save_offline_html(fig: go.Figure, symbol: str, timeframe: str, count: int, output_dir: Path) -> Path:
    safe_symbol = "".join(c if c.isalnum() or c in "-_" else "_" for c in symbol)
    path = output_dir / f"PriceActionAI_{VERSION}_{safe_symbol}_{timeframe}_{count}.html"
    fig.write_html(
        str(path),
        include_plotlyjs=True,
        full_html=True,
        auto_open=False,
    )
    return path


def open_local_file(path: Path):
    try:
        webbrowser.open(path.resolve().as_uri(), new=2)
    except Exception as exc:
        print(f"[INFO] Could not auto-open browser: {exc}")


def print_diagnostics(
    symbol: str,
    timeframe: str,
    count: int,
    raw: list[dict],
    structural: list[dict],
    internal_tags: list[dict],
    major: list[dict],
    major_removed: list[dict],
    ref_stats: dict,
    snapshot: Path,
    html: Path,
):
    thrusts = leg_thrusts(structural)
    print("\n================ v1.7.5 CORRECTION TEMPORAL GATE ================")
    print(f"Symbol               : {symbol}")
    print(f"Timeframe            : {timeframe}")
    print(f"Candles              : {count}")
    print(f"Raw pivots           : {len(raw)}")
    print(f"Structural swings    : {len(structural)}")
    print(f"Internal candidates  : {len(internal_tags)}")
    print(f"Major swings         : {len(major)}")
    print(f"Major pivots removed : {len(major_removed)}")
    print(f"Reference source     : {ref_stats['source']}")
    print(f"Reference leg actual : {ref_stats['reference']:.4f}")
    print(f"Arithmetic mean      : {ref_stats['mean']:.4f}")
    print(f"Median               : {ref_stats['median']:.4f}")
    print(f"RMS target           : {ref_stats['rms']:.4f}")
    print(f"Snap distance        : {ref_stats['snap_distance']:.4f}")
    print(f"50% boundary         : {ref_stats['reference'] * MAJOR_REJECT_RATIO:.4f}")
    print(f"70% boundary         : {ref_stats['reference'] * MAJOR_ACCEPT_RATIO:.4f}")
    print("Structural leg thrusts:")
    print("  " + ", ".join(f"{x:.4f}" for x in thrusts))
    print(f"Snapshot saved       : {snapshot}")
    print(f"Offline HTML saved   : {html}")
    print("==================================================================")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="PriceActionAI v1.7.5 — Offline Correction Temporal Gate generalization test"
    )
    parser.add_argument("--symbol", default=None, help="Symbol or alias, e.g. XAUUSD, NASDAQ, NQ, YM, EURUSD")
    parser.add_argument("--timeframe", default=None, help="M5, M15, M30, H1")
    parser.add_argument("--count", type=int, default=CANDLE_COUNT, help="Number of market candles (default 200)")
    parser.add_argument("--reference-leg", type=float, default=None, help="Optional manual actual Reference Leg override")
    parser.add_argument("--output-dir", default=None, help="Directory for offline HTML and CSV snapshot")
    parser.add_argument("--no-open", action="store_true", help="Save output but do not auto-open the local HTML")
    return parser.parse_args()


def main():
    args = parse_args()
    timeframe = choose_timeframe(args.timeframe)
    count = max(20, int(args.count))
    output_dir = Path(args.output_dir).expanduser().resolve() if args.output_dir else Path.cwd()
    output_dir.mkdir(parents=True, exist_ok=True)

    mt5 = _load_mt5()
    try:
        connect_mt5(mt5)
        symbol = detect_symbol(mt5, args.symbol)
        print(f"Requested symbol    : {args.symbol or 'AUTO/GOLD'}")
        print(f"Resolved MT5 symbol : {symbol}")
        print(f"Selected timeframe  : {timeframe}")
        print(f"Requested candles   : {count}")

        df = fetch_candles(mt5, symbol, timeframe, count)
        raw, structural, internal_tags = structural_swings(df)
        thrusts = leg_thrusts(structural)
        ref_stats = estimate_reference_leg(thrusts)
        if args.reference_leg is not None:
            ref_stats = dict(ref_stats)
            ref_stats["source"] = "MANUAL_ACTUAL_LEG"
            ref_stats["reference"] = float(args.reference_leg)
            ref_stats["snap_distance"] = abs(ref_stats["reference"] - ref_stats["rms"])

        major, major_removed = select_major_swings(df, structural, ref_stats["reference"])
        fig = build_chart(
            df,
            symbol,
            timeframe,
            raw,
            structural,
            internal_tags,
            major,
            major_removed,
            ref_stats,
            count,
        )
        snapshot = save_snapshot(df, symbol, timeframe, count, output_dir)
        html = save_offline_html(fig, symbol, timeframe, count, output_dir)
        print_diagnostics(
            symbol,
            timeframe,
            count,
            raw,
            structural,
            internal_tags,
            major,
            major_removed,
            ref_stats,
            snapshot,
            html,
        )
        if not args.no_open:
            open_local_file(html)
    finally:
        mt5.shutdown()


if __name__ == "__main__":
    main()
