from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
import webbrowser
from pathlib import Path
from typing import Any, Iterable, Sequence

import pandas as pd
import plotly.graph_objects as go

TIMEFRAMES = ("M5", "M15", "M30", "H1")
DEFAULT_SYMBOL = "XAUUSD_o"
DEFAULT_BARS = 3000
OUTPUT_DIR_NAME = "PriceActionAI_Gold_Continuity_Visual_Output"


def active_bar_axis(timestamps: Iterable[object]) -> list[int]:
    return list(range(len(list(timestamps))))


def sample_time_ticks(timestamps: Sequence[object], max_ticks: int = 12) -> tuple[list[int], list[str]]:
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


def leg_metric_label(leg_no: int, leg: Any) -> str:
    continuity = getattr(leg, "directional_continuity_ratio", None)
    efficiency = getattr(leg, "directional_efficiency", None)
    c_text = "NA" if continuity is None else f"{float(continuity):.3f}"
    e_text = "NA" if efficiency is None else f"{float(efficiency):.3f}"
    return f"L{leg_no} | C={c_text} | E={e_text}"


def scheduled_gap_active_indices(active_df: pd.DataFrame, gap_result: dict) -> set[int]:
    if "source_index" not in active_df.columns:
        return set()
    source_to_active = {
        int(source_index): active_index
        for active_index, source_index in enumerate(active_df["source_index"].tolist())
    }
    mapped: set[int] = set()
    for gap in gap_result.get("scheduled_gaps", []):
        source_index = int(gap["new_segment_index"])
        if source_index in source_to_active:
            mapped.add(int(source_to_active[source_index]))
    return mapped


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def find_repo_root(explicit: str | None = None) -> Path:
    candidates: list[Path] = []
    if explicit:
        candidates.append(Path(explicit).expanduser().resolve())
    here = Path(__file__).resolve().parent
    candidates.extend([here, here.parent, here / "_PriceActionAI_repo", here / "PriceActionAI"])
    for root in candidates:
        if (root / "src" / "price_action_ai_swing_v1.py").exists() and (root / "src" / "price_action_ai_leg_v0.py").exists():
            return root
    raise FileNotFoundError(
        "PriceActionAI repo was not found. Put this bundle inside/next to the repo, "
        "or run with --repo-root <path>. RUN_GOLD_VISUAL_TEST.bat can clone the branch automatically."
    )


def load_locked_engines(repo_root: Path):
    swing = _load_module("price_action_ai_swing_v1_visual_test", repo_root / "src" / "price_action_ai_swing_v1.py")
    leg = _load_module("price_action_ai_leg_v0_visual_test", repo_root / "src" / "price_action_ai_leg_v0.py")
    return swing, leg


def _load_mt5():
    try:
        import MetaTrader5 as mt5
    except ImportError as exc:
        raise RuntimeError("MetaTrader5 package is missing. Run SETUP_ONCE.bat first.") from exc
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
    return {
        "M5": mt5.TIMEFRAME_M5,
        "M15": mt5.TIMEFRAME_M15,
        "M30": mt5.TIMEFRAME_M30,
        "H1": mt5.TIMEFRAME_H1,
    }[tf]


def get_candles(mt5, symbol: str, timeframe: str, count: int) -> pd.DataFrame:
    if not mt5.symbol_select(symbol, True):
        raise RuntimeError(f"Could not select MT5 symbol {symbol}. MT5 error: {mt5.last_error()}")
    rates = mt5.copy_rates_from_pos(symbol, _mt5_timeframe(mt5, timeframe), 0, int(count))
    if rates is None or len(rates) == 0:
        raise RuntimeError(f"No {timeframe} candles received for {symbol}. MT5 error: {mt5.last_error()}")
    df = pd.DataFrame(rates)
    df["time"] = pd.to_datetime(df["time"], unit="s")
    return df.reset_index(drop=True)


def run_locked_pipeline(swing, df: pd.DataFrame, timeframe: str, symbol: str) -> dict:
    gap = swing.segment_on_unexpected_gaps(df, timeframe, symbol=symbol)
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
    fig = go.Figure()
    fig.add_trace(
        go.Candlestick(
            x=x,
            open=df["open"],
            high=df["high"],
            low=df["low"],
            close=df["close"],
            customdata=[[str(t)] for t in df["time"]],
            hovertemplate=(
                "Time=%{customdata[0]}<br>"
                "O=%{open}<br>H=%{high}<br>L=%{low}<br>C=%{close}<extra></extra>"
            ),
            name=f"{symbol} {timeframe}",
        )
    )
    fig.add_trace(_major_trace(df, result["major"]))

    for leg_no, leg in enumerate(build.legs, start=1):
        si = int(leg.start["index"])
        ei = int(leg.end["index"])
        lx = [si, ei]
        ly = [float(leg.start["price"]), float(leg.end["price"])]
        start_time = str(df.iloc[si]["time"])
        end_time = str(df.iloc[ei]["time"])
        detail = [
            leg_no,
            leg.direction,
            leg.active_bar_count,
            leg.net_thrust,
            leg.gross_close_path,
            leg.directional_efficiency,
            leg.aligned_close_steps,
            leg.opposing_close_steps,
            leg.flat_close_steps,
            leg.directional_continuity_ratio,
            leg.gap_path_contribution,
            leg.gap_path_share,
            start_time,
            end_time,
        ]
        fig.add_trace(
            go.Scatter(
                x=lx,
                y=ly,
                mode="lines",
                line={"width": 4},
                showlegend=False,
                customdata=[detail, detail],
                hovertemplate=(
                    "Leg %{customdata[0]} | %{customdata[1]}<br>"
                    "Active Bars=%{customdata[2]}<br>"
                    "Net Thrust=%{customdata[3]:.5f}<br>"
                    "Gross Close Path=%{customdata[4]:.5f}<br>"
                    "Directional Efficiency=%{customdata[5]:.4f}<br>"
                    "Aligned=%{customdata[6]} | Opposing=%{customdata[7]} | Flat=%{customdata[8]}<br>"
                    "Directional Continuity=%{customdata[9]:.4f}<br>"
                    "Gap Path=%{customdata[10]:.5f} | Gap Share=%{customdata[11]:.4f}<br>"
                    "Start=%{customdata[12]}<br>End=%{customdata[13]}<extra></extra>"
                ),
            )
        )
        mid_x = (si + ei) / 2.0
        mid_y = (float(leg.start["price"]) + float(leg.end["price"])) / 2.0
        fig.add_annotation(
            x=mid_x,
            y=mid_y,
            text=leg_metric_label(leg_no, leg),
            showarrow=False,
            bgcolor="rgba(255,255,255,0.78)",
            bordercolor="rgba(0,0,0,0.35)",
            borderwidth=1,
            font={"size": 10},
        )

    tickvals, ticktext = sample_time_ticks(df["time"].tolist(), max_ticks=12)
    fig.update_layout(
        title=(
            f"PriceActionAI | GOLD Directional Continuity Visual Audit | {symbol} {timeframe} | "
            f"Active Bars={len(df)} | Major={len(result['major'])} | Legs={len(build.legs)} | "
            f"Reference={result['reference']:.5f} | UnexpectedGaps={len(result['gap']['unexpected_gaps'])}"
        ),
        xaxis_title="Active Market Bars (scheduled closures compressed)",
        yaxis_title="Price",
        xaxis_rangeslider_visible=False,
        hovermode="closest",
        height=950,
    )
    fig.update_xaxes(tickmode="array", tickvals=tickvals, ticktext=ticktext)
    return fig


def _leg_rows(df: pd.DataFrame, legs) -> list[dict]:
    rows = []
    for i, leg in enumerate(legs, start=1):
        si = int(leg.start["index"])
        ei = int(leg.end["index"])
        invariant_ok = (
            leg.aligned_close_steps is None
            or leg.aligned_close_steps + leg.opposing_close_steps + leg.flat_close_steps == leg.active_bar_count
        )
        rows.append({
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
            "gross_close_path": leg.gross_close_path,
            "directional_efficiency": leg.directional_efficiency,
            "aligned_close_steps": leg.aligned_close_steps,
            "opposing_close_steps": leg.opposing_close_steps,
            "flat_close_steps": leg.flat_close_steps,
            "directional_continuity_ratio": leg.directional_continuity_ratio,
            "continuity_invariant_ok": invariant_ok,
            "gap_path_contribution": leg.gap_path_contribution,
            "gap_path_share": leg.gap_path_share,
        })
    return rows


def validate_one_timeframe(swing, leg_engine, mt5, symbol: str, timeframe: str, count: int, output_dir: Path):
    full = get_candles(mt5, symbol, timeframe, count)
    result = run_locked_pipeline(swing, full, timeframe, symbol)
    df = result["df"]
    gap_indices = scheduled_gap_active_indices(df, result["gap"])
    build = leg_engine.build_confirmed_legs(
        result["major"],
        closes=df["close"].tolist(),
        scheduled_gap_after_indices=gap_indices,
    )

    leg_count_ok = len(build.legs) == max(0, len(result["major"]) - 1)
    alternation_ok = all(a["kind"] != b["kind"] for a, b in zip(result["major"][:-1], result["major"][1:]))
    continuity_ok = all(
        leg.aligned_close_steps is not None
        and leg.aligned_close_steps + leg.opposing_close_steps + leg.flat_close_steps == leg.active_bar_count
        for leg in build.legs
    )

    html_path = output_dir / f"GOLD_CONTINUITY_{symbol}_{timeframe}.html"
    csv_path = output_dir / f"GOLD_CONTINUITY_{symbol}_{timeframe}.csv"
    json_path = output_dir / f"GOLD_CONTINUITY_{symbol}_{timeframe}_SUMMARY.json"

    build_chart(symbol, timeframe, result, build).write_html(
        str(html_path), include_plotlyjs=True, full_html=True, auto_open=False
    )
    pd.DataFrame(_leg_rows(df, build.legs)).to_csv(csv_path, index=False)

    summary = {
        "symbol": symbol,
        "timeframe": timeframe,
        "requested_bars": int(count),
        "active_bars": len(df),
        "raw_swings": len(result["raw"]),
        "structural_swings": len(result["structural"]),
        "major_swings": len(result["major"]),
        "legs": len(build.legs),
        "reference": result["reference"],
        "scheduled_gaps": len(result["gap"]["scheduled_gaps"]),
        "unexpected_gaps": len(result["gap"]["unexpected_gaps"]),
        "upstream_errors": len(build.errors),
        "leg_count_invariant_ok": leg_count_ok,
        "alternation_ok": alternation_ok,
        "directional_continuity_invariant_ok": continuity_ok,
        "html": str(html_path),
        "csv": str(csv_path),
    }
    json_path.write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    return summary


def print_summary(symbol: str, summaries: list[dict]) -> None:
    print("\n==========================================================================")
    print(f" PriceActionAI | GOLD DIRECTIONAL CONTINUITY VISUAL AUDIT | {symbol}")
    print(" Swing v1: READ-ONLY | Continuity: RAW DESCRIPTIVE METRIC ONLY")
    print("==========================================================================")
    for s in summaries:
        print(
            f"{s['timeframe']:>3} | Active={s['active_bars']:>5} | Major={s['major_swings']:>3} | "
            f"Legs={s['legs']:>3} | UnexpectedGap={s['unexpected_gaps']} | "
            f"LegInv={'OK' if s['leg_count_invariant_ok'] else 'FAIL'} | "
            f"ContinuityInv={'OK' if s['directional_continuity_invariant_ok'] else 'FAIL'}"
        )
    print("==========================================================================\n")


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
    parser = argparse.ArgumentParser(description="Visual Gold audit for Directional Continuity using locked Swing v1.")
    parser.add_argument("--repo-root", default=None, help="Path to PriceActionAI repo. Auto-detected if omitted.")
    parser.add_argument("--symbol", default=DEFAULT_SYMBOL, help="Broker gold symbol. Default: XAUUSD_o")
    parser.add_argument("--bars", type=int, default=DEFAULT_BARS, help="Bars per timeframe. Default: 3000")
    parser.add_argument("--timeframes", nargs="+", default=list(TIMEFRAMES), choices=TIMEFRAMES)
    parser.add_argument("--no-open", action="store_true", help="Do not open generated HTML charts automatically.")
    parser.add_argument("--output-dir", default=OUTPUT_DIR_NAME, help="Output folder.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    repo_root = find_repo_root(args.repo_root)
    swing, leg_engine = load_locked_engines(repo_root)
    mt5 = _load_mt5()
    try:
        connect_mt5(mt5)
        symbol = find_symbol(mt5, args.symbol)
        output_dir = Path(args.output_dir).resolve()
        output_dir.mkdir(parents=True, exist_ok=True)
        summaries = []
        for timeframe in args.timeframes:
            print(f"[RUN] {symbol} {timeframe} ...")
            summaries.append(validate_one_timeframe(
                swing, leg_engine, mt5, symbol, timeframe, args.bars, output_dir
            ))
        print_summary(symbol, summaries)
        if not args.no_open:
            _open_outputs(summaries)
        hard_fail = any(
            s["upstream_errors"] > 0
            or not s["leg_count_invariant_ok"]
            or not s["alternation_ok"]
            or not s["directional_continuity_invariant_ok"]
            for s in summaries
        )
        return 1 if hard_fail else 0
    finally:
        mt5.shutdown()


if __name__ == "__main__":
    raise SystemExit(main())
