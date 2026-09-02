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


DEFAULT_SYMBOL = "XAUUSD_o"
DEFAULT_TIMEFRAME = "M15"
DEFAULT_BARS = 1000
TIMEFRAMES = ("M5", "M15", "M30", "H1")
DEFAULT_OUTPUT_DIR = "PriceActionAI_Parallel_Visual_Leg_Inspector"

LEG_FEATURE_FIELDS = (
    "active_bar_count",
    "net_thrust",
    "gross_close_path",
    "net_close_displacement",
    "signed_close_displacement",
    "direction_agreement",
    "directional_efficiency",
    "aligned_close_steps",
    "opposing_close_steps",
    "flat_close_steps",
    "directional_continuity_ratio",
    "close_confirmation_ratio",
    "temporal_profile_tag",
    "gap_path_contribution",
    "gap_path_share",
    "gross_body_magnitude",
    "gross_candle_range",
    "body_strength_ratio",
    "gross_upper_shadow",
    "gross_lower_shadow",
    "gross_forward_shadow",
    "gross_backward_shadow",
    "gross_shadow_magnitude",
    "shadow_position_imbalance",
    "gross_overlap_magnitude",
    "gross_overlap_capacity",
    "overlap_ratio",
    "close_ols_slope",
    "directional_close_ols_slope",
    "normalized_directional_close_ols_slope",
    "gross_tick_activity",
    "mean_tick_activity",
)

IDENTITY_FIELDS = (
    "leg_no",
    "direction",
    "start_index",
    "start_time",
    "start_kind",
    "start_price",
    "end_index",
    "end_time",
    "end_kind",
    "end_price",
)

CSV_FIELDS = IDENTITY_FIELDS + LEG_FEATURE_FIELDS


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


def leg_engine_kwargs(df: pd.DataFrame, scheduled_gap_indices: set[int]) -> dict[str, Any]:
    return {
        "opens": [float(v) for v in df["open"].tolist()],
        "highs": [float(v) for v in df["high"].tolist()],
        "lows": [float(v) for v in df["low"].tolist()],
        "closes": [float(v) for v in df["close"].tolist()],
        "tick_volume": [int(v) for v in df["tick_volume"].tolist()] if "tick_volume" in df.columns else None,
        "scheduled_gap_after_indices": set(int(v) for v in scheduled_gap_indices),
    }


def leg_feature_record(leg_no: int, leg: Any, df: pd.DataFrame) -> dict[str, Any]:
    si = int(leg.start["index"])
    ei = int(leg.end["index"])
    record: dict[str, Any] = {
        "leg_no": int(leg_no),
        "direction": str(leg.direction),
        "start_index": si,
        "start_time": str(pd.Timestamp(df.iloc[si]["time"])),
        "start_kind": str(leg.start["kind"]),
        "start_price": float(leg.start["price"]),
        "end_index": ei,
        "end_time": str(pd.Timestamp(df.iloc[ei]["time"])),
        "end_kind": str(leg.end["kind"]),
        "end_price": float(leg.end["price"]),
    }
    for field in LEG_FEATURE_FIELDS:
        record[field] = getattr(leg, field)
    return record


def output_paths(output_dir: Path, symbol: str, timeframe: str) -> tuple[Path, Path]:
    safe_symbol = symbol.replace("/", "_").replace("\\", "_")
    stem = f"PriceActionAI_Parallel_Leg_Inspector_{safe_symbol}_{timeframe}"
    return output_dir / f"{stem}.html", output_dir / f"{stem}.csv"


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
    here = Path(__file__).resolve()
    candidates.extend([here.parents[1], Path.cwd().resolve()])
    for root in candidates:
        if (
            (root / "src" / "price_action_ai_swing_v1.py").exists()
            and (root / "src" / "price_action_ai_leg_v0.py").exists()
        ):
            return root
    raise FileNotFoundError(
        "PriceActionAI repo root not found. Run this script from the repository or pass --repo-root <path>."
    )


def load_locked_engines(repo_root: Path):
    swing = _load_module(
        "price_action_ai_swing_parallel_inspector",
        repo_root / "src" / "price_action_ai_swing_v1.py",
    )
    leg = _load_module(
        "price_action_ai_leg_parallel_inspector",
        repo_root / "src" / "price_action_ai_leg_v0.py",
    )
    return swing, leg


def _load_mt5():
    try:
        import MetaTrader5 as mt5
    except ImportError as exc:
        raise RuntimeError(
            "MetaTrader5 package is missing. Install with: pip install MetaTrader5 pandas plotly"
        ) from exc
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


def mt5_timeframe(mt5, timeframe: str):
    mapping = {
        "M5": mt5.TIMEFRAME_M5,
        "M15": mt5.TIMEFRAME_M15,
        "M30": mt5.TIMEFRAME_M30,
        "H1": mt5.TIMEFRAME_H1,
    }
    return mapping[timeframe]


def get_candles(mt5, symbol: str, timeframe: str, count: int) -> pd.DataFrame:
    if not mt5.symbol_select(symbol, True):
        raise RuntimeError(f"Could not select MT5 symbol {symbol}. MT5 error: {mt5.last_error()}")
    rates = mt5.copy_rates_from_pos(symbol, mt5_timeframe(mt5, timeframe), 0, int(count))
    if rates is None or len(rates) == 0:
        raise RuntimeError(f"No {timeframe} candles received for {symbol}. MT5 error: {mt5.last_error()}")
    df = pd.DataFrame(rates)
    df["time"] = pd.to_datetime(df["time"], unit="s")
    return df.reset_index(drop=True)


def run_locked_swing_pipeline(swing, df: pd.DataFrame, timeframe: str, symbol: str) -> dict[str, Any]:
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


def scheduled_gap_active_indices(active_df: pd.DataFrame, gap_result: dict[str, Any]) -> set[int]:
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


def _major_trace(df: pd.DataFrame, major: list[dict[str, Any]]) -> go.Scatter:
    return go.Scatter(
        x=[int(p["index"]) for p in major],
        y=[float(p["price"]) for p in major],
        mode="lines+markers+text",
        text=[str(p["kind"]) for p in major],
        textposition=["top center" if p["kind"] == "SH" else "bottom center" for p in major],
        customdata=[[str(df.iloc[int(p["index"])]["time"]), str(p["kind"])] for p in major],
        hovertemplate=(
            "Swing %{customdata[1]}<br>"
            "Active Bar=%{x}<br>"
            "Time=%{customdata[0]}<br>"
            "Price=%{y}<extra></extra>"
        ),
        name="Locked Major Swing spine",
    )


def _compact_hover(record: dict[str, Any]) -> str:
    return (
        "Leg %{meta.leg_no} | %{meta.direction}<br>"
        "Bars=%{meta.active_bar_count}<br>"
        "Net Thrust=%{meta.net_thrust}<br>"
        "Continuity=%{meta.directional_continuity_ratio}<br>"
        "Efficiency=%{meta.directional_efficiency}<br>"
        "Body Strength=%{meta.body_strength_ratio}<br>"
        "Overlap=%{meta.overlap_ratio}<br>"
        "Norm Slope=%{meta.normalized_directional_close_ols_slope}<br>"
        "Mean Activity=%{meta.mean_tick_activity}<br>"
        "Click Leg for full inspector<extra></extra>"
    )


def _leg_trace(record: dict[str, Any]) -> go.Scatter:
    return go.Scatter(
        x=[record["start_index"], record["end_index"]],
        y=[record["start_price"], record["end_price"]],
        mode="lines+markers",
        line={"width": 5},
        marker={"size": 7},
        name=f"Leg {record['leg_no']}",
        showlegend=False,
        meta=record,
        hovertemplate=_compact_hover(record),
    )


def build_chart(
    symbol: str,
    timeframe: str,
    result: dict[str, Any],
    records: list[dict[str, Any]],
) -> go.Figure:
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
    for record in records:
        fig.add_trace(_leg_trace(record))

    tickvals, ticktext = sample_time_ticks(df["time"].tolist(), max_ticks=12)
    fig.update_layout(
        title=(
            f"PriceActionAI Parallel Prototype | Visual Swing + Leg Inspector | {symbol} {timeframe} | "
            f"Active Bars={len(df)} | Major={len(result['major'])} | Legs={len(records)} | "
            f"Reference={result['reference']:.5f} | UnexpectedGaps={len(result['gap']['unexpected_gaps'])}"
        ),
        xaxis_title="Active Market Bars (scheduled closures compressed)",
        yaxis_title="Price",
        xaxis_rangeslider_visible=False,
        hovermode="closest",
        clickmode="event+select",
        height=900,
        margin={"b": 80},
    )
    fig.update_xaxes(tickmode="array", tickvals=tickvals, ticktext=ticktext)
    return fig


def empty_test_figure_with_leg_trace(record: dict[str, Any]) -> go.Figure:
    full = {
        "leg_no": int(record.get("leg_no", 1)),
        "direction": str(record.get("direction", "BULLISH")),
        "start_index": 0,
        "start_time": "2026-09-01 10:00:00",
        "start_kind": "SL",
        "start_price": 1.0,
        "end_index": 1,
        "end_time": "2026-09-01 10:15:00",
        "end_kind": "SH",
        "end_price": 2.0,
    }
    for field in LEG_FEATURE_FIELDS:
        full[field] = record.get(field)
    return go.Figure(data=[_leg_trace(full)])


def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if hasattr(value, "item"):
        return value.item()
    return str(value)


def _records_json(records: list[dict[str, Any]]) -> str:
    normalized = {
        str(int(record["leg_no"])): {key: _json_safe(value) for key, value in record.items()}
        for record in records
    }
    return json.dumps(normalized, ensure_ascii=False, separators=(",", ":"))


def write_inspector_html(fig: go.Figure, records: list[dict[str, Any]], output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    html = fig.to_html(include_plotlyjs=True, full_html=True)
    payload = _records_json(records)
    inspector_markup = f"""
<div id="leg-inspector-panel" style="font-family:Arial,sans-serif;margin:0 24px 24px;padding:16px;border:1px solid #bbb;border-radius:8px;max-height:420px;overflow:auto;">
  <h3 style="margin-top:0;">Leg Inspector</h3>
  <div id="leg-inspector-hint">روی یک Leg در نمودار کلیک کن تا همهٔ Featureهای همان Leg اینجا نمایش داده شوند.</div>
  <table id="leg-inspector-table" style="width:100%;border-collapse:collapse;display:none;"><tbody></tbody></table>
</div>
<script>
(function() {{
  const recordsByLeg = {payload};
  const plots = document.querySelectorAll('.plotly-graph-div');
  if (!plots.length) return;
  const plot = plots[0];
  const table = document.getElementById('leg-inspector-table');
  const tbody = table.querySelector('tbody');
  const hint = document.getElementById('leg-inspector-hint');
  function showRecord(record) {{
    tbody.innerHTML = '';
    Object.keys(record).forEach(function(key) {{
      const tr = document.createElement('tr');
      const k = document.createElement('td');
      const v = document.createElement('td');
      k.textContent = key;
      v.textContent = record[key] === null ? 'NA' : String(record[key]);
      k.style.cssText = 'padding:4px 10px;border-bottom:1px solid #eee;font-weight:600;width:38%;';
      v.style.cssText = 'padding:4px 10px;border-bottom:1px solid #eee;';
      tr.appendChild(k); tr.appendChild(v); tbody.appendChild(tr);
    }});
    hint.style.display = 'none';
    table.style.display = 'table';
  }}
  plot.on('plotly_click', function(eventData) {{
    if (!eventData || !eventData.points || !eventData.points.length) return;
    const meta = eventData.points[0].data && eventData.points[0].data.meta;
    if (!meta || meta.leg_no === undefined || meta.leg_no === null) return;
    const record = recordsByLeg[String(meta.leg_no)];
    if (record) showRecord(record);
  }});
}})();
</script>
"""
    html = html.replace("</body>", inspector_markup + "\n</body>")
    output_path.write_text(html, encoding="utf-8")
    return output_path


def export_csv(records: list[dict[str, Any]], csv_path: Path) -> Path:
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(records, columns=list(CSV_FIELDS)).to_csv(csv_path, index=False)
    return csv_path


def run_once(
    *,
    repo_root: Path,
    mt5,
    symbol: str,
    timeframe: str,
    bars: int,
    output_dir: Path,
) -> dict[str, Any]:
    swing, leg_engine = load_locked_engines(repo_root)
    full = get_candles(mt5, symbol, timeframe, bars)
    result = run_locked_swing_pipeline(swing, full, timeframe, symbol)
    df = result["df"]
    scheduled_indices = scheduled_gap_active_indices(df, result["gap"])
    build = leg_engine.build_confirmed_legs(
        result["major"],
        **leg_engine_kwargs(df, scheduled_indices),
    )
    if build.errors:
        raise RuntimeError(f"Leg Engine returned {len(build.errors)} upstream invariant errors.")

    records = [leg_feature_record(i, leg, df) for i, leg in enumerate(build.legs, start=1)]
    html_path, csv_path = output_paths(output_dir, symbol, timeframe)
    fig = build_chart(symbol, timeframe, result, records)
    write_inspector_html(fig, records, html_path)
    export_csv(records, csv_path)

    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "requested_bars": int(bars),
        "active_bars": len(df),
        "major_swings": len(result["major"]),
        "legs": len(records),
        "reference": result["reference"],
        "scheduled_gaps": len(result["gap"].get("scheduled_gaps", [])),
        "unexpected_gaps": len(result["gap"].get("unexpected_gaps", [])),
        "html": html_path,
        "csv": csv_path,
    }


def _open_file(path: Path) -> None:
    path = path.resolve()
    if os.name == "nt" and hasattr(os, "startfile"):
        os.startfile(str(path))
    else:
        webbrowser.open_new_tab(path.as_uri())


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Parallel PriceActionAI visual inspector. Displays locked Swing + existing Leg measurements only; "
            "it does not classify Trend/Range/Correction or make trading decisions."
        )
    )
    parser.add_argument("--repo-root", default=None, help="PriceActionAI repository root.")
    parser.add_argument("--symbol", default=DEFAULT_SYMBOL, help="Broker gold symbol. Default: XAUUSD_o")
    parser.add_argument("--timeframe", default=DEFAULT_TIMEFRAME, choices=TIMEFRAMES)
    parser.add_argument("--bars", type=int, default=DEFAULT_BARS)
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--no-open", action="store_true", help="Generate files without opening the HTML.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    repo_root = find_repo_root(args.repo_root)
    mt5 = _load_mt5()
    try:
        connect_mt5(mt5)
        symbol = find_symbol(mt5, args.symbol)
        summary = run_once(
            repo_root=repo_root,
            mt5=mt5,
            symbol=symbol,
            timeframe=args.timeframe,
            bars=args.bars,
            output_dir=Path(args.output_dir).expanduser().resolve(),
        )
    finally:
        mt5.shutdown()

    print("\n============================================================")
    print(" PriceActionAI PARALLEL VISUAL SWING + LEG INSPECTOR")
    print(" Locked Swing/Leg semantics: UNCHANGED")
    print(" Classifications / thresholds / scores: NONE")
    print("============================================================")
    print(
        f"{summary['symbol']} {summary['timeframe']} | requested={summary['requested_bars']} | "
        f"active={summary['active_bars']} | major={summary['major_swings']} | legs={summary['legs']} | "
        f"reference={summary['reference']:.5f} | scheduled={summary['scheduled_gaps']} | "
        f"unexpected={summary['unexpected_gaps']}"
    )
    print(f"HTML: {summary['html']}")
    print(f"CSV : {summary['csv']}")
    print("============================================================\n")

    if not args.no_open:
        _open_file(Path(summary["html"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
