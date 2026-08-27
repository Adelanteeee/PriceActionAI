from __future__ import annotations

import argparse
import importlib.util
import os
import sys
import webbrowser
from pathlib import Path
from typing import Iterable, Sequence

import pandas as pd
import plotly.graph_objects as go


TIMEFRAMES = ("M5", "M15", "M30", "H1")
DEFAULT_SYMBOL = "XAUUSD_o"
DEFAULT_BARS = 500
OUTPUT_DIR_NAME = "PriceActionAI_Gold_Leg_v0_Validation"


def active_bar_axis(timestamps: Iterable[object]) -> list[int]:
    """Return contiguous display coordinates, independent of elapsed clock time."""
    return list(range(len(list(timestamps))))


def leg_display_coordinates(start: dict, end: dict) -> tuple[list[int], list[float]]:
    """Map a confirmed Leg to the same contiguous Active-Bar axis used by candles."""
    return [int(start["index"]), int(end["index"])], [float(start["price"]), float(end["price"])]


def sample_time_ticks(timestamps: Sequence[object], max_ticks: int = 10) -> tuple[list[int], list[str]]:
    """Keep real timestamps as labels while the chart itself uses Active-Bar indexes."""
    n = len(timestamps)
    if n == 0:
        return [], []
    max_ticks = max(2, int(max_ticks))
    if n <= max_ticks:
        idx = list(range(n))
    else:
        step = (n - 1) / float(max_ticks - 1)
        idx = sorted({round(i * step) for i in range(max_ticks)})
        if idx[-1] != n - 1:
            idx.append(n - 1)
    text = [pd.Timestamp(timestamps[i]).strftime("%Y-%m-%d\n%H:%M") for i in idx]
    return idx, text


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _resolve_engine_file(filename: str) -> Path:
    here = Path(__file__).resolve().parent
    candidates = [
        here / "src" / filename,
        here / filename,
    ]
    for path in candidates:
        if path.exists():
            return path
    raise FileNotFoundError(
        f"Missing {filename}. Put this runner next to {filename}, or run it from the PriceActionAI repo."
    )


def load_locked_engines():
    swing_path = _resolve_engine_file("price_action_ai_swing_v1.py")
    leg_path = _resolve_engine_file("price_action_ai_leg_v0.py")
    swing = _load_module("price_action_ai_swing_v1_runner", swing_path)
    leg = _load_module("price_action_ai_leg_v0_runner", leg_path)
    return swing, leg


def _load_mt5():
    try:
        import MetaTrader5 as mt5
    except ImportError as exc:
        raise RuntimeError("MetaTrader5 package is missing. Run: pip install MetaTrader5 pandas plotly") from exc
    return mt5


def connect_mt5(mt5) -> None:
    if not mt5.initialize():
        raise RuntimeError(f"Could not initialize MetaTrader 5. MT5 error: {mt5.last_error()}")
    if mt5.account_info() is None:
        mt5.shutdown()
        raise RuntimeError("MT5 is open but no logged-in account was detected.")


def find_symbol(mt5, requested: str) -> str:
    symbols = mt5.symbols_get()
    if symbols is None:
        raise RuntimeError(f"Could not read MT5 symbols. MT5 error: {mt5.last_error()}")
    names = [s.name for s in symbols]
    req = requested.strip().upper()

    for name in names:
        if name.upper() == req:
            return name

    aliases = ("XAUUSD", "GOLD") if req in {"XAUUSD", "XAUUSD_O", "GOLD"} else (req,)
    for alias in aliases:
        hits = [n for n in names if n.upper().startswith(alias)]
        if hits:
            return sorted(hits, key=len)[0]
    for alias in aliases:
        hits = [n for n in names if alias in n.upper()]
        if hits:
            return sorted(hits, key=len)[0]

    raise RuntimeError(f"Could not find broker symbol for '{requested}'.")


def _mt5_timeframe(mt5, tf: str):
    mapping = {
        "M5": mt5.TIMEFRAME_M5,
        "M15": mt5.TIMEFRAME_M15,
        "M30": mt5.TIMEFRAME_M30,
        "H1": mt5.TIMEFRAME_H1,
    }
    return mapping[tf]


def get_candles(mt5, symbol: str, timeframe: str, count: int) -> pd.DataFrame:
    if not mt5.symbol_select(symbol, True):
        raise RuntimeError(f"Could not select MT5 symbol {symbol}. MT5 error: {mt5.last_error()}")
    rates = mt5.copy_rates_from_pos(symbol, _mt5_timeframe(mt5, timeframe), 0, int(count))
    if rates is None or len(rates) == 0:
        raise RuntimeError(f"No {timeframe} candles received for {symbol}. MT5 error: {mt5.last_error()}")
    df = pd.DataFrame(rates)
    df["time"] = pd.to_datetime(df["time"], unit="s")
    return df.reset_index(drop=True)


def run_locked_pipeline(swing, df: pd.DataFrame, timeframe: str) -> dict:
    gap = swing.segment_on_unexpected_gaps(df, timeframe)
    active = gap["active_segment"].copy().reset_index(drop=True)
    raw = swing.detect_pivot_candidates(active)
    structural, internal = swing.tag_internal_candidates(raw)
    structural = swing.add_swing_diagnostics(structural)
    thrusts = swing._leg_thrusts(structural)
    stats = swing.reference_statistics(thrusts)
    reference, _ = swing.select_nearest_actual_leg(thrusts, stats["rms"])
    if reference is None:
        raise RuntimeError(f"{timeframe}: Reference Leg could not be derived.")
    major, removed = swing.select_major_swings(active, structural, reference)
    return {
        "df": active,
        "gap": gap,
        "raw": raw,
        "structural": structural,
        "internal": internal,
        "stats": stats,
        "reference": float(reference),
        "major": major,
        "removed": removed,
    }


def _major_trace(df: pd.DataFrame, major: list[dict]) -> go.Scatter:
    return go.Scatter(
        x=[int(p["index"]) for p in major],
        y=[float(p["price"]) for p in major],
        mode="lines+markers+text",
        text=[p["kind"] for p in major],
        textposition=["top center" if p["kind"] == "SH" else "bottom center" for p in major],
        customdata=[[str(df.iloc[int(p["index"])]["time"]), p["kind"]] for p in major],
        hovertemplate=(
            "Major %{customdata[1]}<br>"
            "Active Bar=%{x}<br>"
            "Time=%{customdata[0]}<br>"
            "Price=%{y}<extra></extra>"
        ),
        name="Major Swing spine",
    )


def build_chart(symbol: str, timeframe: str, result: dict, build) -> go.Figure:
    df = result["df"]
    x = active_bar_axis(df["time"].tolist())
    customdata = [[str(t)] for t in df["time"]]

    fig = go.Figure()
    fig.add_trace(
        go.Candlestick(
            x=x,
            open=df["open"],
            high=df["high"],
            low=df["low"],
            close=df["close"],
            customdata=customdata,
            hovertext=[str(t) for t in df["time"]],
            name=f"{symbol} {timeframe}",
        )
    )
    fig.add_trace(_major_trace(df, result["major"]))

    for leg_no, leg in enumerate(build.legs, start=1):
        lx, ly = leg_display_coordinates(leg.start, leg.end)
        start_time = str(df.iloc[lx[0]]["time"])
        end_time = str(df.iloc[lx[1]]["time"])
        fig.add_trace(
            go.Scatter(
                x=lx,
                y=ly,
                mode="lines",
                line={"width": 4},
                showlegend=False,
                customdata=[
                    [leg_no, leg.direction, leg.active_bar_count, leg.net_thrust, start_time, end_time],
                    [leg_no, leg.direction, leg.active_bar_count, leg.net_thrust, start_time, end_time],
                ],
                hovertemplate=(
                    "Confirmed Leg %{customdata[0]}<br>"
                    "%{customdata[1]}<br>"
                    "Active Bars=%{customdata[2]}<br>"
                    "Net Thrust=%{customdata[3]:.5f}<br>"
                    "Start=%{customdata[4]}<br>"
                    "End=%{customdata[5]}<extra></extra>"
                ),
            )
        )

    tickvals, ticktext = sample_time_ticks(df["time"].tolist(), max_ticks=12)
    title = (
        f"PriceActionAI | Gold Confirmed Leg v0 | {symbol} {timeframe} | "
        f"Bars={len(df)} | Major={len(result['major'])} | Legs={len(build.legs)} | "
        f"Reference={result['reference']:.5f} | UnexpectedGaps={len(result['gap']['unexpected_gaps'])}"
    )
    fig.update_layout(
        title=title,
        xaxis_title="Active Market Bars (scheduled closures visually compressed)",
        yaxis_title="Price",
        xaxis_rangeslider_visible=False,
        hovermode="closest",
        height=900,
    )
    fig.update_xaxes(tickmode="array", tickvals=tickvals, ticktext=ticktext)
    return fig


def _leg_rows(df: pd.DataFrame, legs) -> list[dict]:
    rows = []
    for i, leg in enumerate(legs, start=1):
        si = int(leg.start["index"])
        ei = int(leg.end["index"])
        rows.append(
            {
                "leg_no": i,
                "direction": leg.direction,
                "start_index": si,
                "start_time": df.iloc[si]["time"],
                "start_kind": leg.start["kind"],
                "start_price": float(leg.start["price"]),
                "end_index": ei,
                "end_time": df.iloc[ei]["time"],
                "end_kind": leg.end["kind"],
                "end_price": float(leg.end["price"]),
                "active_bar_count": int(leg.active_bar_count),
                "net_thrust": float(leg.net_thrust),
            }
        )
    return rows


def validate_one_timeframe(swing, leg_engine, mt5, symbol: str, timeframe: str, count: int, output_dir: Path):
    full = get_candles(mt5, symbol, timeframe, count)
    result = run_locked_pipeline(swing, full, timeframe)
    build = leg_engine.build_confirmed_legs(result["major"])
    df = result["df"]

    invariant_ok = len(build.legs) == max(0, len(result["major"]) - 1)
    alternation_ok = all(a["kind"] != b["kind"] for a, b in zip(result["major"][:-1], result["major"][1:]))

    fig = build_chart(symbol, timeframe, result, build)
    html_path = output_dir / f"PriceActionAI_Gold_Leg_v0_{symbol}_{timeframe}.html"
    csv_path = output_dir / f"PriceActionAI_Gold_Leg_v0_{symbol}_{timeframe}.csv"
    fig.write_html(str(html_path), include_plotlyjs=True, full_html=True, auto_open=False)
    pd.DataFrame(_leg_rows(df, build.legs)).to_csv(csv_path, index=False)

    summary = {
        "timeframe": timeframe,
        "bars": len(df),
        "raw": len(result["raw"]),
        "structural": len(result["structural"]),
        "major": len(result["major"]),
        "legs": len(build.legs),
        "reference": result["reference"],
        "unexpected_gaps": len(result["gap"]["unexpected_gaps"]),
        "upstream_errors": len(build.errors),
        "leg_count_invariant_ok": invariant_ok,
        "alternation_ok": alternation_ok,
        "html": html_path,
        "csv": csv_path,
    }
    return summary


def print_summary(symbol: str, summaries: list[dict]) -> None:
    print("\n============================================================")
    print(f" PriceActionAI GOLD LEG v0 MULTI-TF VISUAL VALIDATOR | {symbol}")
    print(" Swing v1: READ-ONLY / UNCHANGED")
    print(" Leg v0  : Start, End, Direction, Active Bar Count, Net Thrust")
    print(" Display : Active-Bar axis; scheduled market closures compressed")
    print("============================================================")
    for s in summaries:
        print(
            f"{s['timeframe']:>3} | Bars={s['bars']:>4} | Raw={s['raw']:>3} | Structural={s['structural']:>3} | "
            f"Major={s['major']:>3} | Legs={s['legs']:>3} | Ref={s['reference']:.5f} | "
            f"UnexpectedGap={s['unexpected_gaps']} | Errors={s['upstream_errors']} | "
            f"LegInvariant={'OK' if s['leg_count_invariant_ok'] else 'FAIL'} | Alternation={'OK' if s['alternation_ok'] else 'FAIL'}"
        )
    print("============================================================\n")


def _open_outputs(summaries: list[dict]) -> None:
    for summary in summaries:
        try:
            path = Path(summary["html"]).resolve()
            if os.name == "nt" and hasattr(os, "startfile"):
                os.startfile(str(path))
            else:
                webbrowser.open_new_tab(path.as_uri())
        except Exception as exc:
            print(f"[WARN] Could not auto-open {summary['timeframe']} chart: {exc}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Gold-only multi-timeframe visual validator using locked Swing v1 + Confirmed Leg v0."
    )
    parser.add_argument("--symbol", default=DEFAULT_SYMBOL, help="Broker gold symbol. Default: XAUUSD_o")
    parser.add_argument("--bars", type=int, default=DEFAULT_BARS, help="Bars per timeframe. Default: 500")
    parser.add_argument(
        "--timeframes",
        nargs="+",
        default=list(TIMEFRAMES),
        choices=TIMEFRAMES,
        help="Timeframes to generate. Default: M5 M15 M30 H1",
    )
    parser.add_argument("--no-open", action="store_true", help="Generate files without opening browser tabs.")
    parser.add_argument("--output-dir", default=OUTPUT_DIR_NAME, help="Output folder.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    swing, leg_engine = load_locked_engines()
    mt5 = _load_mt5()

    try:
        connect_mt5(mt5)
        symbol = find_symbol(mt5, args.symbol)
        output_dir = Path(args.output_dir).resolve()
        output_dir.mkdir(parents=True, exist_ok=True)

        summaries = []
        for timeframe in args.timeframes:
            print(f"[RUN] {symbol} {timeframe} ...")
            summary = validate_one_timeframe(
                swing=swing,
                leg_engine=leg_engine,
                mt5=mt5,
                symbol=symbol,
                timeframe=timeframe,
                count=args.bars,
                output_dir=output_dir,
            )
            summaries.append(summary)

        print_summary(symbol, summaries)
        if not args.no_open:
            _open_outputs(summaries)

        hard_fail = any(
            s["upstream_errors"] > 0 or not s["leg_count_invariant_ok"] or not s["alternation_ok"]
            for s in summaries
        )
        return 1 if hard_fail else 0
    finally:
        mt5.shutdown()


if __name__ == "__main__":
    raise SystemExit(main())
