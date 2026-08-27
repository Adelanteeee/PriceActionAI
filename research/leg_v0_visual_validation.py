from pathlib import Path
import base64
import gzip
import importlib.util
import sys
import tempfile

import pandas as pd
import plotly.graph_objects as go

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "tests" / "data"
SWING_SRC = ROOT / "src" / "price_action_ai_swing_v1.py"
LEG_SRC = ROOT / "src" / "price_action_ai_leg_v0.py"
OUTDIR = ROOT / "artifacts"
FIXTURE = "NZDUSD_o_M30_500_20260827_0000"
SYMBOL = "NZDUSD_o"
TIMEFRAME = "M30"


def _load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _decoded_fixture(stem):
    encoded = (DATA / f"{stem}.csv.gz.b64").read_text(encoding="utf-8").strip()
    raw = gzip.decompress(base64.b64decode(encoded))
    outdir = Path(tempfile.gettempdir()) / "priceactionai_leg_v0_visual"
    outdir.mkdir(parents=True, exist_ok=True)
    path = outdir / f"{stem}.csv"
    path.write_bytes(raw)
    return path


def _pipeline(swing):
    full = swing.load_snapshot_file(_decoded_fixture(FIXTURE))
    gap = swing.segment_on_unexpected_gaps(full, TIMEFRAME)
    df = gap["active_segment"].copy().reset_index(drop=True)
    raw = swing.detect_pivot_candidates(df)
    structural, _ = swing.tag_internal_candidates(raw)
    structural = swing.add_swing_diagnostics(structural)
    thrusts = swing._leg_thrusts(structural)
    stats = swing.reference_statistics(thrusts)
    reference, _ = swing.select_nearest_actual_leg(thrusts, stats["rms"])
    major, removed = swing.select_major_swings(df, structural, reference)
    return df, gap, raw, structural, reference, major, removed


def main():
    swing = _load_module("swing_v1_leg_visual", SWING_SRC)
    leg_v0 = _load_module("leg_v0_visual", LEG_SRC)

    df, gap, raw, structural, reference, major, removed = _pipeline(swing)
    result = leg_v0.build_confirmed_legs(major)
    if result.errors:
        raise RuntimeError(f"Leg build returned upstream errors: {result.errors}")

    OUTDIR.mkdir(parents=True, exist_ok=True)
    html_path = OUTDIR / "PriceActionAI_Leg_v0_NZDUSD_M30_500.html"
    csv_path = OUTDIR / "PriceActionAI_Leg_v0_NZDUSD_M30_500.csv"

    spec = swing.symbol_display_spec(SYMBOL, None)

    rows = []
    for leg_no, leg in enumerate(result.legs, start=1):
        start_i = int(leg.start["index"])
        end_i = int(leg.end["index"])
        rows.append(
            {
                "leg_no": leg_no,
                "direction": leg.direction,
                "start_index": start_i,
                "start_time": df.iloc[start_i]["time"],
                "start_kind": leg.start["kind"],
                "start_price": float(leg.start["price"]),
                "end_index": end_i,
                "end_time": df.iloc[end_i]["time"],
                "end_kind": leg.end["kind"],
                "end_price": float(leg.end["price"]),
                "active_bar_count": int(leg.active_bar_count),
                "net_thrust_raw": float(leg.net_thrust),
                "net_thrust_pips": float(swing.raw_to_pips(leg.net_thrust, spec)),
            }
        )

    pd.DataFrame(rows).to_csv(csv_path, index=False)

    fig = go.Figure()
    fig.add_trace(
        go.Candlestick(
            x=df["time"],
            open=df["open"],
            high=df["high"],
            low=df["low"],
            close=df["close"],
            name="NZDUSD_o M30",
        )
    )

    sh = [p for p in major if p["kind"] == "SH"]
    sl = [p for p in major if p["kind"] == "SL"]
    if sh:
        fig.add_trace(
            go.Scatter(
                x=[df.iloc[int(p["index"])]["time"] for p in sh],
                y=[float(p["price"]) for p in sh],
                mode="markers+text",
                text=["SH"] * len(sh),
                textposition="top center",
                marker={"size": 7, "symbol": "triangle-down"},
                name="Major SH",
            )
        )
    if sl:
        fig.add_trace(
            go.Scatter(
                x=[df.iloc[int(p["index"])]["time"] for p in sl],
                y=[float(p["price"]) for p in sl],
                mode="markers+text",
                text=["SL"] * len(sl),
                textposition="bottom center",
                marker={"size": 7, "symbol": "triangle-up"},
                name="Major SL",
            )
        )

    bullish_legend = False
    bearish_legend = False
    for leg_no, leg in enumerate(result.legs, start=1):
        start_i = int(leg.start["index"])
        end_i = int(leg.end["index"])
        is_bull = leg.direction == "BULLISH"
        showlegend = (is_bull and not bullish_legend) or ((not is_bull) and not bearish_legend)
        if is_bull:
            bullish_legend = True
        else:
            bearish_legend = True
        thrust_pips = swing.raw_to_pips(leg.net_thrust, spec)
        hover = (
            f"Leg {leg_no}<br>"
            f"{leg.direction}<br>"
            f"Active Bars: {leg.active_bar_count}<br>"
            f"Net Thrust: {leg.net_thrust:.5f} ({thrust_pips:.1f} pips)<br>"
            f"Start: {leg.start['kind']} @ {float(leg.start['price']):.5f}<br>"
            f"End: {leg.end['kind']} @ {float(leg.end['price']):.5f}"
        )
        fig.add_trace(
            go.Scatter(
                x=[df.iloc[start_i]["time"], df.iloc[end_i]["time"]],
                y=[float(leg.start["price"]), float(leg.end["price"])],
                mode="lines",
                line={"width": 3},
                name="Bullish Confirmed Leg" if is_bull else "Bearish Confirmed Leg",
                legendgroup="bull" if is_bull else "bear",
                showlegend=showlegend,
                hovertemplate=hover + "<extra></extra>",
            )
        )

    title = (
        f"PriceActionAI Leg v0 Visual Validation | {SYMBOL} {TIMEFRAME} | "
        f"Bars={len(df)} | Major={len(major)} | Confirmed Legs={len(result.legs)} | "
        f"Reference={reference:.5f}"
    )
    fig.update_layout(
        title=title,
        xaxis_title="Time",
        yaxis_title="Price",
        xaxis_rangeslider_visible=False,
        hovermode="closest",
        height=900,
    )
    fig.write_html(str(html_path), include_plotlyjs=True, full_html=True, auto_open=False)

    print("================ LEG v0 VISUAL VALIDATION ================")
    print(f"Snapshot bars     : {len(df)}")
    print(f"Unexpected gaps   : {len(gap['unexpected_gaps'])}")
    print(f"Raw pivots        : {len(raw)}")
    print(f"Structural swings : {len(structural)}")
    print(f"Major swings      : {len(major)}")
    print(f"Confirmed legs    : {len(result.legs)}")
    print(f"Upstream errors   : {len(result.errors)}")
    print(f"Reference         : {reference:.5f}")
    print(f"HTML              : {html_path}")
    print(f"CSV               : {csv_path}")
    print("===========================================================")


if __name__ == "__main__":
    main()
