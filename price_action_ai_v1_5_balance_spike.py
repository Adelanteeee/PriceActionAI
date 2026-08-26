from __future__ import annotations

import argparse
import math
import sys
from copy import deepcopy

import pandas as pd
import plotly.graph_objects as go


# ============================================================
# PriceActionAI Visual Research Prototype v1.5 BALANCE SPIKE
# Sprint 1 — Swing Engine
# Goal: Pivot candidates -> Structural Swing validation
# ============================================================

VERSION = "1.5-balance-spike"
CANDLE_COUNT = 100
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
REFERENCE_CLUSTER_TOLERANCE = 0.18
MAJOR_REJECT_RATIO = 0.50
MAJOR_ACCEPT_RATIO = 0.70
MID_QUALITY_THRESHOLD = 0.60

# Balance Compression experiment (Sprint 1 only; NOT the final Range Engine)
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
    if account is None:
        print("\n[ERROR] MT5 is open but no account was detected.")
        mt5.shutdown()
        sys.exit(1)

    print("\n============================================================")
    print(" PriceActionAI v1.5 SPIKE | Balance + Reference Leg + Major Swing")
    print("============================================================")
    print("MT5 connection : OK")
    print("Account        :", account.login)
    print("Server         :", account.server)
    print("Balance        :", account.balance)
    print("============================================================\n")


def find_gold_symbol(mt5):
    symbols = mt5.symbols_get()
    if symbols is None:
        return None

    names = [s.name for s in symbols]

    for exact in ("XAUUSD", "GOLD"):
        if exact in names:
            return exact

    xau = [name for name in names if "XAUUSD" in name.upper()]
    if xau:
        return xau[0]

    gold = [name for name in names if "GOLD" in name.upper()]
    if gold:
        return gold[0]

    return None


def resolve_mt5_timeframe(mt5, timeframe_name: str):
    timeframe_name = normalize_timeframe(timeframe_name)
    attr = {
        "M5": "TIMEFRAME_M5",
        "M15": "TIMEFRAME_M15",
        "M30": "TIMEFRAME_M30",
        "H1": "TIMEFRAME_H1",
    }[timeframe_name]
    return getattr(mt5, attr)


def get_candles(mt5, symbol, timeframe_name, count=CANDLE_COUNT):
    timeframe = resolve_mt5_timeframe(mt5, timeframe_name)

    if not mt5.symbol_select(symbol, True):
        print(f"[ERROR] Could not select symbol: {symbol}")
        return None

    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)

    if rates is None or len(rates) == 0:
        print("[ERROR] No candle data received.")
        print("MT5 error:", mt5.last_error())
        return None

    df = pd.DataFrame(rates)
    df["time"] = pd.to_datetime(df["time"], unit="s")
    return df.reset_index(drop=True)


def calculate_atr(df, period=ATR_PERIOD):
    prev_close = df["close"].shift(1)
    tr = pd.concat(
        [
            df["high"] - df["low"],
            (df["high"] - prev_close).abs(),
            (df["low"] - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return tr.rolling(period, min_periods=1).mean()


def detect_pivot_candidates(
    df,
    left=PIVOT_LEFT,
    right=PIVOT_RIGHT,
    atr_period=ATR_PERIOD,
    min_prominence_atr=MIN_PROMINENCE_ATR,
):
    """v1.2-compatible pivot candidate detector."""
    if len(df) < left + right + 1:
        return []

    atr = calculate_atr(df, atr_period)
    candidates = []

    for i in range(left, len(df) - right):
        window = df.iloc[i - left : i + right + 1]
        current_atr = float(atr.iloc[i])

        if not math.isfinite(current_atr) or current_atr <= 0:
            continue

        current_high = float(df.iloc[i]["high"])
        current_low = float(df.iloc[i]["low"])

        is_local_high = current_high >= float(window["high"].max())
        is_local_low = current_low <= float(window["low"].min())

        high_excursion = current_high - float(window["low"].min())
        low_excursion = float(window["high"].max()) - current_low
        min_excursion = min_prominence_atr * current_atr

        if is_local_high and high_excursion >= min_excursion:
            candidates.append(
                {
                    "index": i,
                    "time": df.iloc[i]["time"],
                    "kind": "SH",
                    "price": current_high,
                    "atr": current_atr,
                    "prominence_atr": high_excursion / current_atr,
                }
            )

        if is_local_low and low_excursion >= min_excursion:
            candidates.append(
                {
                    "index": i,
                    "time": df.iloc[i]["time"],
                    "kind": "SL",
                    "price": current_low,
                    "atr": current_atr,
                    "prominence_atr": low_excursion / current_atr,
                }
            )

    candidates.sort(key=lambda x: (x["index"], 0 if x["kind"] == "SL" else 1))
    return enforce_alternation(candidates)


def enforce_alternation(candidates):
    filtered = []

    for candidate in candidates:
        candidate = deepcopy(candidate)
        if not filtered:
            filtered.append(candidate)
            continue

        last = filtered[-1]

        if candidate["kind"] == last["kind"]:
            replace = (
                candidate["kind"] == "SH" and candidate["price"] > last["price"]
            ) or (
                candidate["kind"] == "SL" and candidate["price"] < last["price"]
            )
            if replace:
                filtered[-1] = candidate
            continue

        if candidate["index"] == last["index"]:
            if len(filtered) >= 2:
                previous = filtered[-2]
                old_move = abs(last["price"] - previous["price"])
                new_move = abs(candidate["price"] - previous["price"])
                if new_move > old_move:
                    filtered[-1] = candidate
            continue

        filtered.append(candidate)

    return filtered


def _retrace_ratio(a, b, c):
    impulse = abs(float(b["price"]) - float(a["price"]))
    if impulse <= 0:
        return float("inf")
    retrace = abs(float(c["price"]) - float(b["price"]))
    return retrace / impulse


def collapse_internal_swings(
    swings,
    max_internal_bars=MAX_INTERNAL_BARS,
    max_retrace_ratio=MAX_INTERNAL_RETRACE_RATIO,
):
    """
    Convert local pivots into structural swing candidates.

    A-B-C-D continuation pattern:
      Bullish: SL -> SH -> SL -> SH, with D > B
      Bearish: SH -> SL -> SH -> SL, with D < B

    B/C are removed as internal move pivots when:
      1) B->C lasts 1..max_internal_bars candles,
      2) B->C is not a near-total reversal,
      3) D resumes beyond B in the original direction.

    This explicitly models the user's "breathing / pressure drop / value
    discovery" concept. It is experimental and must be visually calibrated.
    """
    result = [deepcopy(s) for s in swings]
    removed = []

    changed = True
    while changed and len(result) >= 4:
        changed = False
        i = 0

        while i <= len(result) - 4:
            a, b, c, d = result[i : i + 4]

            bullish = (
                a["kind"] == "SL"
                and b["kind"] == "SH"
                and c["kind"] == "SL"
                and d["kind"] == "SH"
                and float(d["price"]) > float(b["price"])
            )
            bearish = (
                a["kind"] == "SH"
                and b["kind"] == "SL"
                and c["kind"] == "SH"
                and d["kind"] == "SL"
                and float(d["price"]) < float(b["price"])
            )

            counter_bars = int(c["index"]) - int(b["index"])
            retrace_ratio = _retrace_ratio(a, b, c)

            if (
                (bullish or bearish)
                and 0 < counter_bars <= max_internal_bars
                and retrace_ratio <= max_retrace_ratio
            ):
                b_removed = deepcopy(b)
                c_removed = deepcopy(c)
                reason = (
                    f"internal continuation | bars={counter_bars} | "
                    f"retrace={retrace_ratio:.1%}"
                )
                b_removed["filter_reason"] = reason
                c_removed["filter_reason"] = reason
                removed.extend([b_removed, c_removed])

                del result[i + 1 : i + 3]
                changed = True
                if i > 0:
                    i -= 1
                continue

            i += 1

    return result, removed


def _balance_metrics(segment):
    """Return reference-independent two-sided compression metrics."""
    if len(segment) < 2:
        return None
    prices = [float(s["price"]) for s in segment]
    legs = [abs(prices[i] - prices[i - 1]) for i in range(1, len(prices))]
    span = max(prices) - min(prices)
    gross = sum(legs)
    if span <= 0 or gross <= 0 or not legs:
        return None
    median_leg = float(pd.Series(legs).median())
    if median_leg <= 0:
        return None
    net = abs(prices[-1] - prices[0])
    return {
        "span": span,
        "gross": gross,
        "net": net,
        "median_leg": median_leg,
        "gross_to_span": gross / span,
        "net_efficiency": net / gross,
        "span_to_median_leg": span / median_leg,
    }


def detect_balance_packets(
    swings,
    min_pivots=BALANCE_MIN_PIVOTS,
    min_gross_to_span=BALANCE_MIN_GROSS_TO_SPAN,
    max_net_efficiency=BALANCE_MAX_NET_EFFICIENCY,
    max_span_to_median_leg=BALANCE_MAX_SPAN_TO_MEDIAN_LEG,
):
    """Detect non-overlapping balance-like pivot packets from right to left.

    Detection deliberately does NOT depend on Reference Leg. That prevents the
    circular failure seen on H1 where repeated small balance legs became the
    reference used to decide whether the same legs were important.
    """
    if len(swings) < min_pivots + 1:
        return []

    packets = []
    end = len(swings) - 1
    while end >= min_pivots:
        chosen = None
        latest_start = end - min_pivots + 1
        for start in range(1, latest_start + 1):
            segment = swings[start : end + 1]
            metrics = _balance_metrics(segment)
            if metrics is None:
                continue
            has_enough_sides = (
                sum(1 for s in segment if s["kind"] == "SH") >= 2
                and sum(1 for s in segment if s["kind"] == "SL") >= 2
            )
            qualifies = (
                has_enough_sides
                and metrics["gross_to_span"] >= min_gross_to_span
                and metrics["net_efficiency"] <= max_net_efficiency
                and metrics["span_to_median_leg"] <= max_span_to_median_leg
            )
            if qualifies:
                chosen = {
                    "start": start,
                    "end": end,
                    "start_index": int(swings[start]["index"]),
                    "end_index": int(swings[end]["index"]),
                    "start_time": swings[start]["time"],
                    "end_time": swings[end]["time"],
                    **metrics,
                }
                break

        if chosen is not None:
            packets.append(chosen)
            end = chosen["start"] - 1
        else:
            end -= 1

    return list(reversed(packets))


def compress_balance_packets(swings, packets):
    """Compress each packet to one directionally relevant effective swing.

    Both boundaries are preserved in packet metadata. Internal pivots are
    removed from the sequence passed to Reference Leg estimation.
    """
    result_source = [deepcopy(s) for s in swings]
    remove_positions = set()
    details = []

    for packet in packets:
        start = int(packet["start"])
        end = int(packet["end"])
        if start <= 0 or end >= len(result_source) or end < start:
            continue

        prior = result_source[start - 1]
        first = result_source[start]
        entry_bullish = float(first["price"]) > float(prior["price"])
        entry_direction = "BULLISH" if entry_bullish else "BEARISH"
        segment = result_source[start : end + 1]

        highs = [(start + i, s) for i, s in enumerate(segment) if s["kind"] == "SH"]
        lows = [(start + i, s) for i, s in enumerate(segment) if s["kind"] == "SL"]
        if not highs or not lows:
            continue

        high_pos, high_swing = max(highs, key=lambda x: float(x[1]["price"]))
        low_pos, low_swing = min(lows, key=lambda x: float(x[1]["price"]))
        effective_pos, effective = (
            (high_pos, high_swing) if entry_bullish else (low_pos, low_swing)
        )

        removed = []
        for pos in range(start, end + 1):
            if pos == effective_pos:
                continue
            remove_positions.add(pos)
            item = deepcopy(result_source[pos])
            item["filter_reason"] = (
                f"balance compression | entry={entry_direction} | "
                f"effective={effective['kind']}@{float(effective['price']):.3f}"
            )
            removed.append(item)

        details.append(
            {
                **packet,
                "entry_direction": entry_direction,
                "boundary_high": float(high_swing["price"]),
                "boundary_low": float(low_swing["price"]),
                "boundary_high_swing": deepcopy(high_swing),
                "boundary_low_swing": deepcopy(low_swing),
                "effective": deepcopy(effective),
                "removed": removed,
            }
        )

    compressed = [s for i, s in enumerate(result_source) if i not in remove_positions]
    return enforce_alternation(compressed), details


def _leg_thrusts(swings):
    return [
        abs(float(swings[i]["price"]) - float(swings[i - 1]["price"]))
        for i in range(1, len(swings))
    ]


def estimate_reference_leg(swings, tolerance=REFERENCE_CLUSTER_TOLERANCE):
    """Estimate one representative leg from the densest thrust cluster.

    This is intentionally experimental. It uses a relative neighborhood around
    every observed leg thrust, chooses the neighborhood with most members,
    then returns that cluster's median as ONE scalar reference value.
    """
    values = [v for v in _leg_thrusts(swings) if math.isfinite(v) and v > 0]
    if not values:
        return None, []
    if len(values) <= 2:
        ref = float(pd.Series(values).median())
        return ref, values

    best = None
    for center in values:
        lo = center * (1.0 - tolerance)
        hi = center * (1.0 + tolerance)
        members = [v for v in values if lo <= v <= hi]
        med = float(pd.Series(members).median())
        mad = (
            float(pd.Series([abs(v - med) for v in members]).median())
            if members
            else float("inf")
        )
        score = (len(members), -mad, med)
        if best is None or score > best[0]:
            best = (score, members, med)
    return best[2], sorted(best[1])


def move_quality(df, start_index, end_index, direction):
    """0..1 candle-behavior quality; used ONLY in the 50%-70% gray zone."""
    lo, hi = sorted((int(start_index), int(end_index)))
    segment = df.iloc[lo : hi + 1]
    if len(segment) == 0:
        return 0.0

    ranges = (segment["high"] - segment["low"]).clip(lower=1e-9)
    bodies = (segment["close"] - segment["open"]).abs()
    body_ratio = float((bodies / ranges).clip(0, 1).mean())

    signs = segment["close"] - segment["open"]
    if direction > 0:
        directional = float((signs > 0).mean())
    else:
        directional = float((signs < 0).mean())

    net = abs(float(segment.iloc[-1]["close"]) - float(segment.iloc[0]["open"]))
    gross = float(bodies.sum())
    efficiency = min(1.0, net / gross) if gross > 0 else 0.0

    overlaps = []
    for i in range(1, len(segment)):
        a = segment.iloc[i - 1]
        b = segment.iloc[i]
        overlap = max(
            0.0,
            min(float(a["high"]), float(b["high"]))
            - max(float(a["low"]), float(b["low"])),
        )
        denom = max(
            1e-9,
            min(float(a["high"] - a["low"]), float(b["high"] - b["low"])),
        )
        overlaps.append(min(1.0, overlap / denom))
    overlap_quality = 1.0 - (sum(overlaps) / len(overlaps) if overlaps else 0.0)

    return max(
        0.0,
        min(
            1.0,
            0.35 * directional
            + 0.30 * body_ratio
            + 0.20 * efficiency
            + 0.15 * overlap_quality,
        ),
    )


def classify_leg_against_reference(df, a, b, reference_leg):
    thrust = abs(float(b["price"]) - float(a["price"]))
    ratio = thrust / reference_leg if reference_leg and reference_leg > 0 else 0.0
    direction = 1 if float(b["price"]) > float(a["price"]) else -1
    quality = move_quality(df, a["index"], b["index"], direction)
    if ratio < MAJOR_REJECT_RATIO:
        status = "REJECT"
    elif ratio < MAJOR_ACCEPT_RATIO:
        status = "ACCEPT" if quality >= MID_QUALITY_THRESHOLD else "REJECT"
    else:
        status = "ACCEPT"
    return {"thrust": thrust, "ratio": ratio, "quality": quality, "status": status}


def select_major_swings(df, swings, reference_leg):
    """Right-to-left experimental major-swing compressor."""
    result = [deepcopy(s) for s in swings]
    removed = []
    changed = True
    while changed and len(result) >= 4:
        changed = False
        for i in range(len(result) - 4, -1, -1):
            a, b, c, d = result[i : i + 4]
            bullish = (
                a["kind"] == "SL"
                and b["kind"] == "SH"
                and c["kind"] == "SL"
                and d["kind"] == "SH"
                and float(d["price"]) > float(b["price"])
            )
            bearish = (
                a["kind"] == "SH"
                and b["kind"] == "SL"
                and c["kind"] == "SH"
                and d["kind"] == "SL"
                and float(d["price"]) < float(b["price"])
            )
            if not (bullish or bearish):
                continue

            counter = classify_leg_against_reference(df, b, c, reference_leg)
            if counter["status"] != "REJECT":
                continue

            reason = (
                f"reference-leg internal continuation | ref={reference_leg:.3f} | "
                f"counter={counter['thrust']:.3f} ({counter['ratio']:.1%}) | "
                f"quality={counter['quality']:.2f}"
            )
            for item in (b, c):
                r = deepcopy(item)
                r["major_filter_reason"] = reason
                r["filter_reason"] = reason
                removed.append(r)
            del result[i + 1 : i + 3]
            changed = True
            break

    return enforce_alternation(result), removed


def major_leg_report(df, swings, reference_leg):
    rows = []
    for i in range(1, len(swings)):
        a, b = swings[i - 1], swings[i]
        info = classify_leg_against_reference(df, a, b, reference_leg)
        rows.append((i, a, b, info))
    return rows


def add_swing_diagnostics(swings):
    result = [deepcopy(s) for s in swings]

    for n, swing in enumerate(result):
        swing["number"] = n + 1

        if n == 0:
            swing["bars_from_previous"] = None
            swing["thrust_from_previous"] = None
            swing["thrust_atr"] = None
            continue

        previous = result[n - 1]
        bars = swing["index"] - previous["index"]
        thrust = abs(swing["price"] - previous["price"])
        mean_atr = (swing["atr"] + previous["atr"]) / 2.0

        swing["bars_from_previous"] = bars
        swing["thrust_from_previous"] = thrust
        swing["thrust_atr"] = thrust / mean_atr if mean_atr > 0 else None

    return result


def print_diagnostics(df, raw_swings, structural_swings, removed, symbol, timeframe_name):
    print("------------------------------------------------------------")
    print("Symbol              :", symbol)
    print("Timeframe           :", timeframe_name)
    print("Candles             :", len(df))
    print("Raw pivot swings    :", len(raw_swings))
    print("Structural swings   :", len(structural_swings))
    print("Internal removed    :", len(removed))
    print("Pivot window        :", f"{PIVOT_LEFT} left / {PIVOT_RIGHT} right")
    print("Min prominence      :", f"{MIN_PROMINENCE_ATR:.2f} ATR")
    print("Internal max bars   :", MAX_INTERNAL_BARS)
    print("Internal max retrace:", f"{MAX_INTERNAL_RETRACE_RATIO:.0%}")
    print("------------------------------------------------------------")

    if removed:
        print("\nFiltered internal pivots:")
        for s in sorted(removed, key=lambda x: x["index"]):
            print(
                f"  {s['kind']} candle={s['index']:02d} price={s['price']:.3f} | "
                f"{s['filter_reason']}"
            )

    if not structural_swings:
        print("No structural swing candidates.")
        return

    print("\nStructural swings:")
    for s in structural_swings:
        if s["bars_from_previous"] is None:
            print(
                f"#{s['number']:02d} {s['kind']} | candle={s['index']:02d} | "
                f"price={s['price']:.3f} | prominence={s['prominence_atr']:.2f} ATR"
            )
        else:
            print(
                f"#{s['number']:02d} {s['kind']} | candle={s['index']:02d} | "
                f"price={s['price']:.3f} | bars={s['bars_from_previous']:02d} | "
                f"thrust={s['thrust_from_previous']:.3f} | "
                f"thrustATR={s['thrust_atr']:.2f}"
            )

    print("------------------------------------------------------------\n")


def show_chart(
    df,
    swings,
    symbol,
    timeframe_name,
    raw_count,
    removed_count,
    reference_source,
    reference_leg,
    auto_ref_before,
    auto_ref_after,
    cluster,
    balance_details,
):
    fig = go.Figure()

    fig.add_trace(
        go.Candlestick(
            x=df["time"],
            open=df["open"],
            high=df["high"],
            low=df["low"],
            close=df["close"],
            name=symbol,
        )
    )

    highs = [s for s in swings if s["kind"] == "SH"]
    lows = [s for s in swings if s["kind"] == "SL"]

    if highs:
        fig.add_trace(
            go.Scatter(
                x=[s["time"] for s in highs],
                y=[s["price"] for s in highs],
                mode="markers+text",
                marker=dict(symbol="triangle-down", size=13),
                text=[f"SH{s['number']}" for s in highs],
                textposition="top center",
                name="Structural Swing High",
                hovertemplate="%{text}<br>Price=%{y:.3f}<extra></extra>",
            )
        )

    if lows:
        fig.add_trace(
            go.Scatter(
                x=[s["time"] for s in lows],
                y=[s["price"] for s in lows],
                mode="markers+text",
                marker=dict(symbol="triangle-up", size=13),
                text=[f"SL{s['number']}" for s in lows],
                textposition="bottom center",
                name="Structural Swing Low",
                hovertemplate="%{text}<br>Price=%{y:.3f}<extra></extra>",
            )
        )

    if len(swings) >= 2:
        fig.add_trace(
            go.Scatter(
                x=[s["time"] for s in swings],
                y=[s["price"] for s in swings],
                mode="lines",
                name="Structural Swing Path",
                hoverinfo="skip",
            )
        )

    for n, packet in enumerate(balance_details or [], start=1):
        fig.add_shape(
            type="rect",
            x0=packet["start_time"],
            x1=packet["end_time"],
            y0=packet["boundary_low"],
            y1=packet["boundary_high"],
            line=dict(width=1, dash="dot"),
            fillcolor="rgba(180,180,180,0.08)",
            layer="below",
        )
        fig.add_annotation(
            x=packet["end_time"],
            y=packet["boundary_high"],
            text=f"BAL{n}",
            showarrow=False,
            xanchor="right",
            yanchor="bottom",
        )

    fig.update_layout(
        title=(
            f"PriceActionAI v{VERSION} | {symbol} | {timeframe_name} | "
            f"Last {len(df)} Candles | Structural Swing Calibration"
        ),
        xaxis_title="Time",
        yaxis_title="Price",
        xaxis_rangeslider_visible=False,
        template="plotly_dark",
        hovermode="x unified",
    )

    pre_ref_text = f"{auto_ref_before:.2f}" if auto_ref_before is not None else "N/A"
    post_ref_text = f"{auto_ref_after:.2f}" if auto_ref_after is not None else "N/A"
    cluster_text = ", ".join(f"{x:.2f}" for x in (cluster or [])) or "N/A"

    fig.add_annotation(
        xref="paper",
        yref="paper",
        x=0.01,
        y=0.99,
        xanchor="left",
        yanchor="top",
        showarrow=False,
        text=(
            f"RAW PIVOTS: {raw_count}<br>"
            f"STRUCTURAL: {len(swings)}<br>"
            f"INTERNAL REMOVED: {removed_count}<br>"
            f"TF: {timeframe_name}<br>"
            f"Balance packets: {len(balance_details or [])}<br>"
            f"Reference source: {reference_source}<br>"
            f"Pre-balance auto: {pre_ref_text}<br>"
            f"Auto estimate: {post_ref_text}<br>"
            f"Reference leg: {reference_leg:.2f}<br>"
            f"Cluster: {cluster_text}<br>"
            f"50%: {0.50 * reference_leg:.2f}<br>"
            f"70%: {0.70 * reference_leg:.2f}<br>"
            f"Internal max bars: {MAX_INTERNAL_BARS}"
        ),
        bgcolor="rgba(0,0,0,0.55)",
    )

    fig.show()


def build_parser():
    parser = argparse.ArgumentParser(
        description="PriceActionAI v1.5 Balance Compression Spike"
    )
    parser.add_argument(
        "--timeframe",
        "-t",
        default=None,
        help="M5, M15, M30, H1 (aliases: 5m, 15m, 30m, 1h)",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=CANDLE_COUNT,
        help=f"Number of candles (default: {CANDLE_COUNT})",
    )
    parser.add_argument(
        "--reference-leg",
        type=float,
        default=None,
        help="Optional manual reference-leg thrust. If omitted, v1.5 estimates one scalar value automatically after Balance Compression.",
    )
    return parser


def main():
    args = build_parser().parse_args()

    try:
        timeframe_name = choose_timeframe(args.timeframe)
    except ValueError as exc:
        print(f"[ERROR] {exc}")
        return 2

    if args.count < 20:
        print("[ERROR] --count must be at least 20 candles.")
        return 2

    mt5 = _load_mt5()
    connect_mt5(mt5)

    try:
        symbol = find_gold_symbol(mt5)
        if symbol is None:
            print("[ERROR] Gold/XAUUSD symbol was not found.")
            print("Open Gold in MT5 Market Watch and run again.")
            return 2

        print("Gold symbol detected:", symbol)
        print("Selected timeframe   :", timeframe_name)

        df = get_candles(mt5, symbol, timeframe_name, args.count)
        if df is None:
            return 2

        raw_swings = detect_pivot_candidates(df)
        structural_swings, removed = collapse_internal_swings(raw_swings)

        auto_ref_before, _ = estimate_reference_leg(structural_swings)

        balance_packets = detect_balance_packets(structural_swings)
        balance_swings, balance_details = compress_balance_packets(
            structural_swings, balance_packets
        )
        balance_removed = [
            item
            for packet in balance_details
            for item in packet.get("removed", [])
        ]

        auto_ref, cluster = estimate_reference_leg(balance_swings)
        reference_leg = (
            args.reference_leg
            if args.reference_leg and args.reference_leg > 0
            else auto_ref
        )
        if reference_leg is None:
            print(
                "[ERROR] Could not estimate a reference leg from balance-compressed swings."
            )
            return 2

        major_swings, major_removed = select_major_swings(
            df, balance_swings, reference_leg
        )
        major_swings = add_swing_diagnostics(major_swings)

        reference_source = "MANUAL" if args.reference_leg else "AUTO"
        print("\n============= v1.5 BALANCE + REFERENCE LEG SPIKE =============")
        print(f"Reference source       : {reference_source}")
        print(
            f"Pre-balance auto ref   : {auto_ref_before:.3f}"
            if auto_ref_before is not None
            else "Pre-balance auto ref   : N/A"
        )
        print(f"Reference leg          : {reference_leg:.3f}")
        if auto_ref is not None:
            print(f"Post-balance auto ref  : {auto_ref:.3f}")
            print("Dominant cluster       :", ", ".join(f"{x:.2f}" for x in cluster))
        print(f"50% boundary           : {0.50 * reference_leg:.3f}")
        print(f"70% boundary           : {0.70 * reference_leg:.3f}")
        print(f"Balance packets        : {len(balance_details)}")
        print(f"Balance pivots removed : {len(balance_removed)}")
        print(f"Major swings           : {len(major_swings)}")
        print(f"Major pivots removed   : {len(major_removed)}")
        print("===============================================================")

        if balance_details:
            print("\nBalance packets:")
            for i, packet in enumerate(balance_details, start=1):
                eff = packet["effective"]
                print(
                    f"  BAL{i} | pivots={packet['start']}..{packet['end']} | "
                    f"entry={packet['entry_direction']} | "
                    f"low={packet['boundary_low']:.3f} | high={packet['boundary_high']:.3f} | "
                    f"effective={eff['kind']}@{float(eff['price']):.3f} | "
                    f"gross/span={packet['gross_to_span']:.2f} | "
                    f"netEff={packet['net_efficiency']:.2f}"
                )

        report = major_leg_report(df, balance_swings, reference_leg)
        print("\nCandidate legs before major compression:")
        for _, a, b, info in report:
            print(
                f"  {a['kind']}@{a['index']:02d} -> {b['kind']}@{b['index']:02d} | "
                f"thrust={info['thrust']:.3f} | ref={info['ratio']:.1%} | "
                f"quality={info['quality']:.2f} | {info['status']}"
            )

        print_diagnostics(
            df,
            raw_swings,
            major_swings,
            removed + balance_removed + major_removed,
            symbol,
            timeframe_name,
        )
        show_chart(
            df,
            major_swings,
            symbol,
            timeframe_name,
            raw_count=len(raw_swings),
            removed_count=len(removed) + len(balance_removed) + len(major_removed),
            reference_source=reference_source,
            reference_leg=reference_leg,
            auto_ref_before=auto_ref_before,
            auto_ref_after=auto_ref,
            cluster=cluster,
            balance_details=balance_details,
        )

        print(f"PriceActionAI v{VERSION} finished successfully.")
        print(
            "SPIKE target: judge Balance Compression -> Reference Leg -> 50/70 filtering visually."
        )
        return 0

    finally:
        mt5.shutdown()


if __name__ == "__main__":
    raise SystemExit(main())
