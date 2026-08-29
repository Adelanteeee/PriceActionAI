from __future__ import annotations

import argparse
import importlib.util
import os
import statistics
import sys
import webbrowser
from pathlib import Path
from typing import Any, Iterable

import pandas as pd
import plotly.graph_objects as go

TIMEFRAMES = ("M5", "M15", "M30", "H1")
DEFAULT_SYMBOL = "XAUUSD_o"
DEFAULT_BARS = 500
DEFAULT_OUTPUT = "PriceActionAI_Leg_Quality_Audit_Output"


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def load_engines():
    here = Path(__file__).resolve().parent
    swing_path = here / "price_action_ai_swing_v1.py"
    leg_path = here / "price_action_ai_leg_v0.py"
    if not swing_path.exists() or not leg_path.exists():
        raise FileNotFoundError(
            "Keep this auditor beside price_action_ai_swing_v1.py and price_action_ai_leg_v0.py"
        )
    swing = _load_module("pai_swing_quality_auditor", swing_path)
    leg = _load_module("pai_leg_quality_auditor", leg_path)
    return swing, leg


def _load_mt5():
    try:
        import MetaTrader5 as mt5
    except ImportError as exc:
        raise RuntimeError(
            "MetaTrader5 is not installed. Run: pip install MetaTrader5 pandas plotly"
        ) from exc
    return mt5


def connect_mt5(mt5):
    if not mt5.initialize():
        raise RuntimeError(f"Could not initialize MT5: {mt5.last_error()}")
    account = mt5.account_info()
    if account is None:
        mt5.shutdown()
        raise RuntimeError("MT5 is open but no logged-in account was detected.")
    print("\n============================================================")
    print(" PriceActionAI | GOLD LEG QUALITY AUDITOR | RAW METRICS ONLY")
    print("============================================================")
    print("Account :", account.login)
    print("Server  :", account.server)
    print("============================================================\n")


def resolve_symbol(mt5, requested: str) -> str:
    symbols = mt5.symbols_get()
    if symbols is None:
        raise RuntimeError(f"Could not read MT5 symbols: {mt5.last_error()}")
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
    raise RuntimeError(f"Could not resolve broker symbol: {requested}")


def _mt5_timeframe(mt5, tf: str):
    return {
        "M5": mt5.TIMEFRAME_M5,
        "M15": mt5.TIMEFRAME_M15,
        "M30": mt5.TIMEFRAME_M30,
        "H1": mt5.TIMEFRAME_H1,
    }[tf]


def fetch_once(mt5, symbol: str, timeframe: str, bars: int) -> pd.DataFrame:
    if not mt5.symbol_select(symbol, True):
        raise RuntimeError(f"Could not select {symbol}: {mt5.last_error()}")
    rates = mt5.copy_rates_from_pos(symbol, _mt5_timeframe(mt5, timeframe), 0, int(bars))
    if rates is None or len(rates) == 0:
        raise RuntimeError(f"No {timeframe} data: {mt5.last_error()}")
    df = pd.DataFrame(rates)
    df["time"] = pd.to_datetime(df["time"], unit="s")
    return df.reset_index(drop=True)


def run_locked_swing(swing, full_df: pd.DataFrame, timeframe: str) -> dict[str, Any]:
    gap = swing.segment_on_unexpected_gaps(full_df.copy(), timeframe)
    df = gap["active_segment"].copy().reset_index(drop=True)

    raw = swing.detect_pivot_candidates(df)
    structural, internal = swing.tag_internal_candidates(raw)
    structural = swing.add_swing_diagnostics(structural)

    thrusts = swing._leg_thrusts(structural)
    status = swing.reference_data_status(thrusts)
    if status != "OK":
        return {
            "status": status,
            "full_df": full_df,
            "df": df,
            "gap": gap,
            "raw": raw,
            "structural": structural,
            "internal": internal,
            "reference": None,
            "major": [],
            "removed": [],
        }

    stats = swing.reference_statistics(thrusts)
    reference, _ = swing.select_nearest_actual_leg(thrusts, stats["rms"])
    if reference is None:
        raise RuntimeError(f"{timeframe}: Reference could not be derived")

    major, removed = swing.select_major_swings(df, structural, reference)
    major = swing.add_swing_diagnostics(major)

    return {
        "status": "OK",
        "full_df": full_df,
        "df": df,
        "gap": gap,
        "raw": raw,
        "structural": structural,
        "internal": internal,
        "reference": float(reference),
        "major": major,
        "removed": removed,
    }


def build_audit_rows(timeframe: str, df: pd.DataFrame, legs: Iterable[Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for n, leg in enumerate(legs, start=1):
        si = int(leg.start["index"])
        ei = int(leg.end["index"])
        rows.append(
            {
                "timeframe": timeframe,
                "leg_id": f"{timeframe}-L{n:03d}",
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
                "gross_close_path": None if leg.gross_close_path is None else float(leg.gross_close_path),
                "net_close_displacement": None if leg.net_close_displacement is None else float(leg.net_close_displacement),
                "directional_efficiency": None if leg.directional_efficiency is None else float(leg.directional_efficiency),
            }
        )
    return rows


def describe_efficiency(rows: Iterable[dict[str, Any]]) -> dict[str, float | int | None]:
    values = [
        float(row["directional_efficiency"])
        for row in rows
        if row.get("directional_efficiency") is not None
    ]
    if not values:
        return {"count": 0, "min": None, "median": None, "mean": None, "max": None}
    return {
        "count": len(values),
        "min": min(values),
        "median": statistics.median(values),
        "mean": statistics.fmean(values),
        "max": max(values),
    }


def _time_ticks(df: pd.DataFrame, max_ticks: int = 10):
    n = len(df)
    if n == 0:
        return [], []
    if n <= max_ticks:
        idx = list(range(n))
    else:
        step = (n - 1) / float(max_ticks - 1)
        idx = sorted({round(i * step) for i in range(max_ticks)})
    text = [df.iloc[i]["time"].strftime("%b %d\n%H:%M") for i in idx]
    return idx, text


def build_audit_chart(symbol: str, timeframe: str, result: dict, rows: list[dict[str, Any]]):
    df = result["df"]
    fig = go.Figure()
    x = list(range(len(df)))

    fig.add_trace(
        go.Candlestick(
            x=x,
            open=df["open"],
            high=df["high"],
            low=df["low"],
            close=df["close"],
            name=f"{symbol} {timeframe}",
        )
    )

    major = result["major"]
    if major:
        fig.add_trace(
            go.Scatter(
                x=[int(p["index"]) for p in major],
                y=[float(p["price"]) for p in major],
                mode="lines+markers",
                line={"width": 1.5, "dash": "dot"},
                marker={"size": 6},
                name="Locked Major Swing Path",
                hovertemplate="Major %{x}<br>Price=%{y}<extra></extra>",
            )
        )

    bull_legend = False
    bear_legend = False
    for row in rows:
        bullish = row["direction"] == "BULLISH"
        showlegend = (bullish and not bull_legend) or ((not bullish) and not bear_legend)
        bull_legend = bull_legend or bullish
        bear_legend = bear_legend or (not bullish)
        mid_x = (row["start_index"] + row["end_index"]) / 2.0
        mid_y = (row["start_price"] + row["end_price"]) / 2.0
        eff = row["directional_efficiency"]
        eff_text = "NA" if eff is None else f"{eff:.3f}"

        fig.add_trace(
            go.Scatter(
                x=[row["start_index"], row["end_index"]],
                y=[row["start_price"], row["end_price"]],
                mode="lines",
                line={"width": 4, "color": "#00CC96" if bullish else "#EF553B"},
                opacity=0.72,
                showlegend=showlegend,
                name="Bullish Leg" if bullish else "Bearish Leg",
                customdata=[
                    [
                        row["leg_id"], row["active_bar_count"], row["net_thrust"],
                        row["gross_close_path"], row["net_close_displacement"], eff_text,
                        str(row["start_time"]), str(row["end_time"]),
                    ],
                    [
                        row["leg_id"], row["active_bar_count"], row["net_thrust"],
                        row["gross_close_path"], row["net_close_displacement"], eff_text,
                        str(row["start_time"]), str(row["end_time"]),
                    ],
                ],
                hovertemplate=(
                    "%{customdata[0]}<br>"
                    "Active Bars=%{customdata[1]}<br>"
                    "Net Thrust=%{customdata[2]:.5f}<br>"
                    "Gross Close Path=%{customdata[3]:.5f}<br>"
                    "Net Close Displacement=%{customdata[4]:.5f}<br>"
                    "Directional Efficiency=%{customdata[5]}<br>"
                    "Start=%{customdata[6]}<br>"
                    "End=%{customdata[7]}<extra></extra>"
                ),
            )
        )
        fig.add_annotation(
            x=mid_x,
            y=mid_y,
            text=row["leg_id"],
            showarrow=False,
            font={"size": 9},
            bgcolor="rgba(0,0,0,0.45)",
        )

    desc = describe_efficiency(rows)
    if desc["count"]:
        panel = (
            f"RAW LEG AUDIT — no quality thresholds<br>"
            f"Legs: {len(rows)}<br>"
            f"Efficiency min: {desc['min']:.3f}<br>"
            f"Efficiency median: {desc['median']:.3f}<br>"
            f"Efficiency mean: {desc['mean']:.3f}<br>"
            f"Efficiency max: {desc['max']:.3f}"
        )
    else:
        panel = f"RAW LEG AUDIT — no quality thresholds<br>Legs: {len(rows)}<br>Efficiency: NA"

    fig.add_annotation(
        xref="paper", yref="paper", x=0.01, y=0.99,
        xanchor="left", yanchor="top", showarrow=False,
        text=panel, bgcolor="rgba(0,0,0,0.60)", align="left",
    )

    tickvals, ticktext = _time_ticks(df)
    fig.update_layout(
        title=(
            f"PriceActionAI Leg Quality Auditor | {symbol} {timeframe} | "
            f"Snapshot {len(result['full_df'])} | Active {len(df)} | "
            f"Major {len(major)} | Legs {len(rows)} | Ref {result['reference']:.5f}"
        ),
        template="plotly_dark",
        xaxis_title="Active Market Bars (scheduled closures compressed)",
        yaxis_title="Price",
        xaxis_rangeslider_visible=False,
        hovermode="closest",
        height=900,
    )
    fig.update_xaxes(tickmode="array", tickvals=tickvals, ticktext=ticktext)
    return fig


def audit_one_timeframe(swing, leg_engine, mt5, symbol: str, timeframe: str, bars: int, output_dir: Path):
    full_df = fetch_once(mt5, symbol, timeframe, bars)
    result = run_locked_swing(swing, full_df, timeframe)
    if result["status"] != "OK":
        return {
            "timeframe": timeframe,
            "status": result["status"],
            "snapshot": len(full_df),
            "active": len(result["df"]),
            "major": 0,
            "legs": 0,
            "unexpected_gaps": len(result["gap"]["unexpected_gaps"]),
        }, []

    build = leg_engine.build_confirmed_legs(
        result["major"],
        closes=result["df"]["close"].tolist(),
    )
    if build.errors:
        raise RuntimeError(f"{timeframe}: upstream invariant error(s): {build.errors}")
    if len(build.legs) != max(0, len(result["major"]) - 1):
        raise RuntimeError(
            f"{timeframe}: Leg invariant failed: Major={len(result['major'])}, Legs={len(build.legs)}"
        )

    rows = build_audit_rows(timeframe, result["df"], build.legs)
    desc = describe_efficiency(rows)

    snapshot_path = output_dir / f"SNAPSHOT_{symbol}_{timeframe}_{len(full_df)}.csv"
    csv_path = output_dir / f"LEG_AUDIT_{symbol}_{timeframe}.csv"
    html_path = output_dir / f"LEG_AUDIT_{symbol}_{timeframe}.html"
    full_df.to_csv(snapshot_path, index=False)
    pd.DataFrame(rows).to_csv(csv_path, index=False)
    build_audit_chart(symbol, timeframe, result, rows).write_html(
        str(html_path), include_plotlyjs=True, full_html=True, auto_open=False
    )

    summary = {
        "timeframe": timeframe,
        "status": "OK",
        "snapshot": len(full_df),
        "active": len(result["df"]),
        "segments": len(result["gap"]["segments"]),
        "unexpected_gaps": len(result["gap"]["unexpected_gaps"]),
        "scheduled_gaps": len(result["gap"]["scheduled_gaps"]),
        "major": len(result["major"]),
        "legs": len(rows),
        "reference": result["reference"],
        "efficiency_count": desc["count"],
        "efficiency_min": desc["min"],
        "efficiency_median": desc["median"],
        "efficiency_mean": desc["mean"],
        "efficiency_max": desc["max"],
        "snapshot_file": str(snapshot_path),
        "csv": str(csv_path),
        "html": str(html_path),
    }
    return summary, rows


def print_summary(symbol: str, summaries: list[dict[str, Any]]):
    print("\n============================================================================")
    print(f" PriceActionAI | {symbol} | LEG QUALITY AUDIT — RAW/DESCRIPTIVE ONLY")
    print("============================================================================")
    for s in summaries:
        if s["status"] != "OK":
            print(f"{s['timeframe']:>3} | Status={s['status']} | Active={s['active']}")
            continue
        print(
            f"{s['timeframe']:>3} | Active={s['active']:>3} | Major={s['major']:>3} | Legs={s['legs']:>3} | "
            f"Ref={s['reference']:.5f} | UnexpectedGap={s['unexpected_gaps']}"
        )
        print(
            f"    Efficiency min/median/mean/max = "
            f"{s['efficiency_min']:.3f} / {s['efficiency_median']:.3f} / "
            f"{s['efficiency_mean']:.3f} / {s['efficiency_max']:.3f}"
        )
    print("============================================================================")
    print("No thresholds, scores, or quality labels were applied.\n")


def _open_htmls(summaries):
    for s in summaries:
        html = s.get("html")
        if not html:
            continue
        try:
            path = Path(html).resolve()
            if os.name == "nt" and hasattr(os, "startfile"):
                os.startfile(str(path))
            else:
                webbrowser.open_new_tab(path.as_uri())
        except Exception as exc:
            print(f"[WARN] Could not open {s['timeframe']} HTML: {exc}")


def build_parser():
    p = argparse.ArgumentParser(
        description="Gold Leg Quality Auditor: raw Leg measurements only; no quality classification."
    )
    p.add_argument("--symbol", default=DEFAULT_SYMBOL)
    p.add_argument("--bars", type=int, default=DEFAULT_BARS)
    p.add_argument("--timeframes", nargs="+", choices=TIMEFRAMES, default=list(TIMEFRAMES))
    p.add_argument("--output-dir", default=DEFAULT_OUTPUT)
    p.add_argument("--no-open", action="store_true")
    return p


def main():
    args = build_parser().parse_args()
    if args.bars < 20:
        print("[ERROR] --bars must be >= 20")
        return 2

    swing, leg_engine = load_engines()
    mt5 = _load_mt5()
    try:
        connect_mt5(mt5)
        symbol = resolve_symbol(mt5, args.symbol)
        print("Requested symbol :", args.symbol)
        print("Resolved symbol  :", symbol)

        output_dir = Path(args.output_dir).resolve()
        output_dir.mkdir(parents=True, exist_ok=True)

        summaries = []
        all_rows = []
        for tf in args.timeframes:
            print(f"\n[RUN] {symbol} {tf} | one MT5 fetch...")
            summary, rows = audit_one_timeframe(
                swing, leg_engine, mt5, symbol, tf, args.bars, output_dir
            )
            summaries.append(summary)
            all_rows.extend(rows)

        pd.DataFrame(all_rows).to_csv(output_dir / "LEG_AUDIT_ALL_TIMEFRAMES.csv", index=False)
        pd.DataFrame(summaries).to_csv(output_dir / "LEG_AUDIT_SUMMARY_ALL_TIMEFRAMES.csv", index=False)
        print_summary(symbol, summaries)
        if not args.no_open:
            _open_htmls(summaries)
        return 0
    finally:
        mt5.shutdown()


if __name__ == "__main__":
    raise SystemExit(main())
