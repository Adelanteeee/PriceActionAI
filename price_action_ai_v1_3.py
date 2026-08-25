from __future__ import annotations

import argparse
import math
import sys
from copy import deepcopy

import pandas as pd
import plotly.graph_objects as go

VERSION = "1.3"
CANDLE_COUNT = 100
PIVOT_LEFT = 2
PIVOT_RIGHT = 2
ATR_PERIOD = 14
MIN_PROMINENCE_ATR = 0.60
MAX_INTERNAL_BARS = 4
MAX_INTERNAL_RETRACE_RATIO = 0.80


def normalize_timeframe(value: str) -> str:
    if value is None:
        return "M5"
    cleaned = str(value).strip().upper().replace(" ", "")
    aliases = {
        "5": "M5", "5M": "M5", "M5": "M5",
        "15": "M15", "15M": "M15", "M15": "M15",
        "30": "M30", "30M": "M30", "M30": "M30",
        "60": "H1", "60M": "H1", "1H": "H1", "H1": "H1",
    }
    if cleaned not in aliases:
        raise ValueError(f"Unsupported timeframe '{value}'. Use M5, M15, M30, or H1.")
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
        print("\n[ERROR] MetaTrader5 package is not installed.")
        print("Run: pip install MetaTrader5 pandas plotly")
        sys.exit(1)
    return mt5


def connect_mt5(mt5):
    if not mt5.initialize():
        print("\n[ERROR] Could not connect to MetaTrader 5.")
        print("MT5 error:", mt5.last_error())
        sys.exit(1)
    account = mt5.account_info()
    if account is None:
        mt5.shutdown()
        print("\n[ERROR] MT5 is open but no account was detected.")
        sys.exit(1)
    print("\n============================================================")
    print(" PriceActionAI v1.3 | Structural Swing Research Build")
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
    return gold[0] if gold else None


def resolve_mt5_timeframe(mt5, timeframe_name: str):
    name = normalize_timeframe(timeframe_name)
    attr = {"M5": "TIMEFRAME_M5", "M15": "TIMEFRAME_M15", "M30": "TIMEFRAME_M30", "H1": "TIMEFRAME_H1"}[name]
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
    tr = pd.concat([
        df["high"] - df["low"],
        (df["high"] - prev_close).abs(),
        (df["low"] - prev_close).abs(),
    ], axis=1).max(axis=1)
    return tr.rolling(period, min_periods=1).mean()


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


def detect_pivot_candidates(df, left=PIVOT_LEFT, right=PIVOT_RIGHT, atr_period=ATR_PERIOD, min_prominence_atr=MIN_PROMINENCE_ATR):
    if len(df) < left + right + 1:
        return []
    atr = calculate_atr(df, atr_period)
    candidates = []
    for i in range(left, len(df) - right):
        window = df.iloc[i - left:i + right + 1]
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
            candidates.append({"index": i, "time": df.iloc[i]["time"], "kind": "SH", "price": current_high, "atr": current_atr, "prominence_atr": high_excursion / current_atr})
        if is_local_low and low_excursion >= min_excursion:
            candidates.append({"index": i, "time": df.iloc[i]["time"], "kind": "SL", "price": current_low, "atr": current_atr, "prominence_atr": low_excursion / current_atr})
    candidates.sort(key=lambda x: (x["index"], 0 if x["kind"] == "SL" else 1))
    return enforce_alternation(candidates)


def _retrace_ratio(a, b, c):
    impulse = abs(float(b["price"]) - float(a["price"]))
    if impulse <= 0:
        return float("inf")
    retrace = abs(float(c["price"]) - float(b["price"]))
    return retrace / impulse


def collapse_internal_swings(swings, max_internal_bars=MAX_INTERNAL_BARS, max_retrace_ratio=MAX_INTERNAL_RETRACE_RATIO):
    result = [deepcopy(s) for s in swings]
    removed = []
    changed = True
    while changed and len(result) >= 4:
        changed = False
        i = 0
        while i <= len(result) - 4:
            a, b, c, d = result[i:i + 4]
            bullish = a["kind"] == "SL" and b["kind"] == "SH" and c["kind"] == "SL" and d["kind"] == "SH" and float(d["price"]) > float(b["price"])
            bearish = a["kind"] == "SH" and b["kind"] == "SL" and c["kind"] == "SH" and d["kind"] == "SL" and float(d["price"]) < float(b["price"])
            counter_bars = int(c["index"]) - int(b["index"])
            retrace_ratio = _retrace_ratio(a, b, c)
            if (bullish or bearish) and 0 < counter_bars <= max_internal_bars and retrace_ratio <= max_retrace_ratio:
                reason = f"internal continuation | bars={counter_bars} | retrace={retrace_ratio:.1%}"
                for item in (b, c):
                    r = deepcopy(item)
                    r["filter_reason"] = reason
                    removed.append(r)
                del result[i + 1:i + 3]
                changed = True
                if i > 0:
                    i -= 1
                continue
            i += 1
    return result, removed


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
            print(f"  {s['kind']} candle={s['index']:02d} price={s['price']:.3f} | {s['filter_reason']}")
    if not structural_swings:
        print("No structural swing candidates.")
        return
    print("\nStructural swings:")
    for s in structural_swings:
        if s["bars_from_previous"] is None:
            print(f"#{s['number']:02d} {s['kind']} | candle={s['index']:02d} | price={s['price']:.3f} | prominence={s['prominence_atr']:.2f} ATR")
        else:
            print(f"#{s['number']:02d} {s['kind']} | candle={s['index']:02d} | price={s['price']:.3f} | bars={s['bars_from_previous']:02d} | thrust={s['thrust_from_previous']:.3f} | thrustATR={s['thrust_atr']:.2f}")
    print("------------------------------------------------------------\n")


def show_chart(df, swings, symbol, timeframe_name, raw_count, removed_count):
    fig = go.Figure()
    fig.add_trace(go.Candlestick(x=df["time"], open=df["open"], high=df["high"], low=df["low"], close=df["close"], name=symbol))
    highs = [s for s in swings if s["kind"] == "SH"]
    lows = [s for s in swings if s["kind"] == "SL"]
    if highs:
        fig.add_trace(go.Scatter(x=[s["time"] for s in highs], y=[s["price"] for s in highs], mode="markers+text", marker=dict(symbol="triangle-down", size=13), text=[f"SH{s['number']}" for s in highs], textposition="top center", name="Structural Swing High"))
    if lows:
        fig.add_trace(go.Scatter(x=[s["time"] for s in lows], y=[s["price"] for s in lows], mode="markers+text", marker=dict(symbol="triangle-up", size=13), text=[f"SL{s['number']}" for s in lows], textposition="bottom center", name="Structural Swing Low"))
    if len(swings) >= 2:
        fig.add_trace(go.Scatter(x=[s["time"] for s in swings], y=[s["price"] for s in swings], mode="lines", name="Structural Swing Path", hoverinfo="skip"))
    fig.update_layout(title=f"PriceActionAI v{VERSION} | {symbol} | {timeframe_name} | Last {len(df)} Candles | Structural Swing Calibration", xaxis_title="Time", yaxis_title="Price", xaxis_rangeslider_visible=False, template="plotly_dark", hovermode="x unified")
    fig.add_annotation(xref="paper", yref="paper", x=0.01, y=0.99, xanchor="left", yanchor="top", showarrow=False, text=f"RAW PIVOTS: {raw_count}<br>STRUCTURAL: {len(swings)}<br>INTERNAL REMOVED: {removed_count}<br>TF: {timeframe_name}<br>Internal max bars: {MAX_INTERNAL_BARS}", bgcolor="rgba(0,0,0,0.55)")
    fig.show()


def build_parser():
    parser = argparse.ArgumentParser(description="PriceActionAI v1.3 Swing Research")
    parser.add_argument("--timeframe", "-t", default=None, help="M5, M15, M30, H1 (aliases: 5m, 15m, 30m, 1h)")
    parser.add_argument("--count", type=int, default=CANDLE_COUNT, help=f"Number of candles (default: {CANDLE_COUNT})")
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
            return 2
        print("Gold symbol detected:", symbol)
        print("Selected timeframe   :", timeframe_name)
        df = get_candles(mt5, symbol, timeframe_name, args.count)
        if df is None:
            return 2
        raw_swings = detect_pivot_candidates(df)
        structural_swings, removed = collapse_internal_swings(raw_swings)
        structural_swings = add_swing_diagnostics(structural_swings)
        print_diagnostics(df, raw_swings, structural_swings, removed, symbol, timeframe_name)
        show_chart(df, structural_swings, symbol, timeframe_name, len(raw_swings), len(removed))
        print(f"PriceActionAI v{VERSION} finished successfully.")
        print("Research target: verify structural swings on M5/M15/M30/H1.")
        return 0
    finally:
        mt5.shutdown()


if __name__ == "__main__":
    raise SystemExit(main())
