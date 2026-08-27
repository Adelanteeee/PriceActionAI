from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go

ROOT = Path(__file__).resolve().parents[1]
SWING_SRC = ROOT / "src" / "price_action_ai_swing_v1.py"
LEG_SRC = ROOT / "src" / "price_action_ai_leg_v0.py"
DEFAULT_COUNT = 500
TIMEFRAME = "M30"
SYMBOL = "XAUUSD"


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _load_gold_csv(path: Path, count: int) -> pd.DataFrame:
    df = pd.read_csv(path)
    df.columns = [str(c).strip().lower() for c in df.columns]

    time_col = next((c for c in ("time", "datetime", "date", "timestamp") if c in df.columns), None)
    if time_col is None:
        raise ValueError(f"No time column found. Columns={list(df.columns)}")

    required = ["open", "high", "low", "close"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing OHLC columns: {missing}")

    df = df.rename(columns={time_col: "time"})
    df["time"] = pd.to_datetime(df["time"], utc=True, errors="coerce").dt.tz_convert(None)
    for col in required:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["time", *required]).sort_values("time").drop_duplicates("time", keep="last")
    if len(df) < count:
        raise ValueError(f"Need at least {count} valid bars, got {len(df)}")

    return df.tail(count).reset_index(drop=True)


def _run_pipeline(swing, df: pd.DataFrame):
    gap = swing.segment_on_unexpected_gaps(df, TIMEFRAME)
    active = gap["active_segment"].copy().reset_index(drop=True)

    raw = swing.detect_pivot_candidates(active)
    structural, internal = swing.tag_internal_candidates(raw)
    structural = swing.add_swing_diagnostics(structural)

    thrusts = swing._leg_thrusts(structural)
    stats = swing.reference_statistics(thrusts)
    reference, _ = swing.select_nearest_actual_leg(thrusts, stats["rms"])
    if reference is None:
        raise RuntimeError("Could not derive Reference Leg")

    major, removed = swing.select_major_swings(active, structural, reference)
    return {
        "gap": gap,
        "df": active,
        "raw": raw,
        "structural": structural,
        "internal": internal,
        "stats": stats,
        "reference": float(reference),
        "major": major,
        "removed": removed,
    }


def _write_outputs(swing, result, build, output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)
    df = result["df"]
    major = result["major"]

    rows = []
    for leg_no, leg in enumerate(build.legs, start=1):
        si = int(leg.start["index"])
        ei = int(leg.end["index"])
        rows.append(
            {
                "leg_no": leg_no,
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

    legs_csv = output_dir / "PriceActionAI_Leg_v0_XAUUSD_M30_500.csv"
    pd.DataFrame(rows).to_csv(legs_csv, index=False)

    fig = go.Figure()
    fig.add_trace(
        go.Candlestick(
            x=df["time"],
            open=df["open"],
            high=df["high"],
            low=df["low"],
            close=df["close"],
            name="XAUUSD M30",
        )
    )

    for leg_no, leg in enumerate(build.legs, start=1):
        si = int(leg.start["index"])
        ei = int(leg.end["index"])
        fig.add_trace(
            go.Scatter(
                x=[df.iloc[si]["time"], df.iloc[ei]["time"]],
                y=[float(leg.start["price"]), float(leg.end["price"])],
                mode="lines",
                line={"width": 3},
                name=leg.direction,
                showlegend=False,
                hovertemplate=(
                    f"Leg {leg_no}<br>{leg.direction}<br>"
                    f"Active Bars: {leg.active_bar_count}<br>"
                    f"Net Thrust: {leg.net_thrust:.2f}<extra></extra>"
                ),
            )
        )

    fig.update_layout(
        title=(
            f"PriceActionAI Gold Primary Validation | XAUUSD M30 | "
            f"Bars={len(df)} | Major={len(major)} | Legs={len(build.legs)} | "
            f"Reference={result['reference']:.2f}"
        ),
        xaxis_title="Time",
        yaxis_title="Price",
        xaxis_rangeslider_visible=False,
        height=900,
    )
    html = output_dir / "PriceActionAI_Leg_v0_XAUUSD_M30_500.html"
    fig.write_html(str(html), include_plotlyjs=True, full_html=True, auto_open=False)

    summary = {
        "symbol": SYMBOL,
        "timeframe": TIMEFRAME,
        "snapshot_bars": int(len(df)),
        "start_time": str(df.iloc[0]["time"]),
        "end_time": str(df.iloc[-1]["time"]),
        "segments": int(len(result["gap"]["segments"])),
        "unexpected_gaps": int(len(result["gap"]["unexpected_gaps"])),
        "raw_pivots": int(len(result["raw"])),
        "structural_swings": int(len(result["structural"])),
        "major_swings": int(len(major)),
        "confirmed_legs": int(len(build.legs)),
        "upstream_errors": int(len(build.errors)),
        "reference": float(result["reference"]),
        "leg_count_invariant_ok": bool(len(build.legs) == max(0, len(major) - 1)),
        "alternation_ok": bool(all(a["kind"] != b["kind"] for a, b in zip(major[:-1], major[1:]))),
        "positive_measurements_ok": bool(all(l.active_bar_count > 0 and l.net_thrust > 0 for l in build.legs)),
    }
    summary["contract_pass"] = bool(
        summary["unexpected_gaps"] == 0
        and summary["upstream_errors"] == 0
        and summary["leg_count_invariant_ok"]
        and summary["alternation_ok"]
        and summary["positive_measurements_ok"]
    )

    summary_json = output_dir / "PriceActionAI_Leg_v0_XAUUSD_M30_500_summary.json"
    summary_json.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary, legs_csv, html, summary_json


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--count", type=int, default=DEFAULT_COUNT)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "artifacts")
    args = parser.parse_args()

    swing = _load_module("swing_v1_gold_validation", SWING_SRC)
    leg_v0 = _load_module("leg_v0_gold_validation", LEG_SRC)
    full = _load_gold_csv(args.source, args.count)
    result = _run_pipeline(swing, full)
    build = leg_v0.build_confirmed_legs(result["major"])
    summary, *_ = _write_outputs(swing, result, build, args.output_dir)

    print("================ GOLD PRIMARY VALIDATION ================")
    for key, value in summary.items():
        print(f"{key:26}: {value}")
    print("=========================================================")

    if not summary["contract_pass"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
