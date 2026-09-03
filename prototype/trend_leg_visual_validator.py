from __future__ import annotations

import argparse
import json
import os
import webbrowser
from pathlib import Path
from typing import Any, Iterable

import pandas as pd
import plotly.graph_objects as go

TIMEFRAMES = ("M5", "M15", "M30", "H1")
DEFAULT_SYMBOL = "XAUUSD_o"
DEFAULT_BARS = 1200
DEFAULT_OUTPUT_DIR = "PriceActionAI_Parallel_Trend_Leg_Visual_Validator_Output"
TERMINAL_THIRD_BOUNDARY = 2.0 / 3.0
MIN_TREND_REVIEW_BARS = 4

TREND_EVIDENCE_FIELDS = (
    "active_bar_count",
    "net_thrust",
    "normalized_directional_close_ols_slope",
    "body_strength_ratio",
    "directional_continuity_ratio",
    "directional_efficiency",
    "overlap_ratio",
    "mean_directional_close_location",
    "terminal_third_close_count",
    "defined_dcl_candle_count",
    "terminal_third_close_ratio",
    "trend_review_state",
)


def directional_close_location(direction: str, high: float, low: float, close: float) -> float | None:
    high = float(high)
    low = float(low)
    close = float(close)
    candle_range = high - low
    if candle_range == 0.0:
        return None
    if candle_range < 0.0:
        raise ValueError(f"Invalid candle range: high={high} < low={low}")

    direction = str(direction).upper()
    if direction == "BULLISH":
        value = (close - low) / candle_range
    elif direction == "BEARISH":
        value = (high - close) / candle_range
    else:
        raise ValueError(f"Unsupported Leg direction: {direction}")

    if -1e-12 <= value <= 1.0 + 1e-12:
        return min(1.0, max(0.0, float(value)))
    raise ValueError(
        f"Close outside candle range for DCL: direction={direction}, high={high}, low={low}, close={close}"
    )


def is_terminal_third(dcl: float | None) -> bool:
    return dcl is not None and float(dcl) >= TERMINAL_THIRD_BOUNDARY


def candle_close_evidence(direction: str, high: float, low: float, close: float) -> dict[str, Any]:
    dcl = directional_close_location(direction, high, low, close)
    return {
        "directional_close_location": dcl,
        "terminal_third": is_terminal_third(dcl) if dcl is not None else None,
    }


def trend_review_state(active_bar_count: int) -> str:
    return (
        "TF_ELIGIBLE_FOR_TREND_REVIEW"
        if int(active_bar_count) >= MIN_TREND_REVIEW_BARS
        else "TF_UNDERSAMPLED"
    )


def _owned_indices(record: dict[str, Any]) -> range:
    start = int(record["start_index"])
    end = int(record["end_index"])
    if end < start:
        raise ValueError(f"Invalid Leg indexes: {start}->{end}")
    return range(start + 1, end + 1)


def leg_close_evidence(record: dict[str, Any], df: pd.DataFrame) -> dict[str, Any]:
    direction = str(record["direction"]).upper()
    defined: list[float] = []
    terminal_count = 0
    per_candle: list[dict[str, Any]] = []

    for i in _owned_indices(record):
        row = df.iloc[i]
        evidence = candle_close_evidence(direction, row["high"], row["low"], row["close"])
        dcl = evidence["directional_close_location"]
        terminal = evidence["terminal_third"]
        per_candle.append(
            {
                "index": int(i),
                "directional_close_location": dcl,
                "terminal_third": terminal,
            }
        )
        if dcl is not None:
            defined.append(float(dcl))
            if terminal:
                terminal_count += 1

    defined_count = len(defined)
    return {
        "mean_directional_close_location": (
            sum(defined) / defined_count if defined_count else None
        ),
        "terminal_third_close_count": int(terminal_count),
        "defined_dcl_candle_count": int(defined_count),
        "terminal_third_close_ratio": (
            terminal_count / defined_count if defined_count else None
        ),
        "dcl_by_candle": per_candle,
    }


def trend_leg_record(base_record: dict[str, Any], df: pd.DataFrame) -> dict[str, Any]:
    record = dict(base_record)
    record.update(leg_close_evidence(record, df))
    record["trend_review_state"] = trend_review_state(int(record["active_bar_count"]))
    return record


def terminal_third_marker_trace(record: dict[str, Any], df: pd.DataFrame) -> go.Scatter:
    evidence = leg_close_evidence(record, df)
    xs: list[int] = []
    ys: list[float] = []
    custom: list[list[Any]] = []

    direction = str(record["direction"]).upper()
    for item in evidence["dcl_by_candle"]:
        if item["terminal_third"] is not True:
            continue
        i = int(item["index"])
        xs.append(i)
        y = float(df.iloc[i]["high"] if direction == "BULLISH" else df.iloc[i]["low"])
        ys.append(y)
        custom.append([str(df.iloc[i].get("time", "")), item["directional_close_location"]])

    return go.Scatter(
        x=xs,
        y=ys,
        mode="markers",
        marker={"size": 9, "symbol": "diamond"},
        showlegend=False,
        name=f"Leg {record.get('leg_no', '?')} terminal-third closes",
        meta={"pai_kind": "terminal_third_close", "leg_no": record.get("leg_no")},
        customdata=custom,
        hovertemplate=(
            "Terminal-third close<br>Active Bar=%{x}<br>"
            "Time=%{customdata[0]}<br>DCL=%{customdata[1]:.3f}<extra></extra>"
        ),
    )


def _load_base():
    try:
        from prototype import visual_leg_inspector as base
    except ImportError:
        import visual_leg_inspector as base
    return base


def trend_records(df: pd.DataFrame, legs: Iterable[Any], base_module=None) -> list[dict[str, Any]]:
    base = base_module or _load_base()
    records: list[dict[str, Any]] = []
    for leg_no, leg in enumerate(legs, start=1):
        records.append(trend_leg_record(base.leg_feature_record(leg_no, leg, df), df))
    return records


def build_trend_chart(symbol: str, timeframe: str, result: dict[str, Any], build, base_module=None) -> go.Figure:
    base = base_module or _load_base()
    fig = base.build_chart(symbol, timeframe, result, [
        base.leg_feature_record(i, leg, result["df"])
        for i, leg in enumerate(build.legs, start=1)
    ])
    df = result["df"]
    records = trend_records(df, build.legs, base)

    by_leg = {int(r["leg_no"]): r for r in records}
    for trace in fig.data:
        meta = getattr(trace, "meta", None)
        if isinstance(meta, dict) and meta.get("pai_kind") == "leg":
            payload = meta.get("payload") or {}
            leg_no = int(payload.get("leg_no", 0))
            if leg_no in by_leg:
                trace.meta = {"pai_kind": "leg", "payload": by_leg[leg_no]}

    for record in records:
        fig.add_trace(terminal_third_marker_trace(record, df))

    fig.update_layout(
        title=(
            f"PriceActionAI Parallel | Trend Leg Visual Validator v1 | {symbol} {timeframe} | "
            "Manual evidence review — no automatic Trend/Not-Trend classification"
        )
    )
    return fig


def _safe_json(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, list):
        return [_safe_json(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _safe_json(v) for k, v in value.items()}
    if hasattr(value, "item"):
        return value.item()
    return str(value)


def build_trend_inspector_html(symbol: str, timeframe: str, result: dict[str, Any], build, base_module=None) -> str:
    fig = build_trend_chart(symbol, timeframe, result, build, base_module)
    chart_html = fig.to_html(
        full_html=False,
        include_plotlyjs=True,
        config={"displaylogo": False, "responsive": True},
        div_id="pai-trend-leg-chart",
    )
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>PriceActionAI Trend Leg Visual Validator — {symbol} {timeframe}</title>
<style>
body{{font-family:Arial,sans-serif;margin:0;background:#f5f5f5;color:#111}}.wrapper{{display:grid;grid-template-columns:minmax(0,1fr) 380px;gap:12px;padding:12px}}.card,.panel{{background:white;border:1px solid #ddd;border-radius:8px}}.card{{overflow:hidden}}.panel{{padding:14px;max-height:92vh;overflow:auto;position:sticky;top:12px}}table{{width:100%;border-collapse:collapse;font-size:12px}}td{{border-bottom:1px solid #eee;padding:6px 4px;vertical-align:top}}td:first-child{{font-weight:600;width:58%;overflow-wrap:anywhere}}td:last-child{{text-align:right;overflow-wrap:anywhere}}.note{{font-size:12px;background:#fafafa;border:1px solid #e4e4e4;padding:8px;border-radius:6px;line-height:1.45}}@media(max-width:1000px){{.wrapper{{grid-template-columns:1fr}}.panel{{position:static;max-height:none}}}}
</style></head><body><div class="wrapper"><div class="card">{chart_html}</div><aside id="trend-panel" class="panel"><h2>Trend Leg Evidence</h2><p><strong>Click a Leg</strong> to inspect evidence.</p><p class="note">v1 is manual validation only. It does not output Trend/Not-Trend, score, weight, or learned threshold. Diamond markers identify closes in the directional terminal third.</p></aside></div>
<script>(function(){{const chart=document.getElementById('pai-trend-leg-chart');const panel=document.getElementById('trend-panel');function add(tag,text,parent){{const e=document.createElement(tag);e.textContent=text;parent.appendChild(e);return e}}function render(p){{panel.replaceChildren();add('h2','Leg '+p.leg_no+' — '+p.direction,panel);const n=add('p','Trend-review evidence only; human visual judgment remains the label.',panel);n.className='note';const t=document.createElement('table');Object.keys(p).filter(k=>k!=='dcl_by_candle').forEach(k=>{{const tr=document.createElement('tr');add('td',k,tr);add('td',p[k]===null?'NA':String(p[k]),tr);t.appendChild(tr)}});panel.appendChild(t)}}chart.on('plotly_click',function(ev){{if(!ev||!ev.points||!ev.points.length)return;const tr=ev.points[0].data;if(tr&&tr.meta&&tr.meta.pai_kind==='leg')render(tr.meta.payload)}})}})();</script></body></html>"""


def validate_one_timeframe(base, swing, leg_engine, mt5, symbol: str, timeframe: str, count: int, output_dir: Path) -> dict[str, Any]:
    full = base.get_candles(mt5, symbol, timeframe, count)
    result = base.run_locked_swing_pipeline(swing, full, timeframe, symbol)
    df = result["df"]
    gap_indices = base.scheduled_gap_active_indices(df, result["gap"])
    build = leg_engine.build_confirmed_legs(result["major"], **base.leg_engine_kwargs(df, gap_indices))
    records = trend_records(df, build.legs, base)

    safe_symbol = symbol.replace("/", "_").replace("\\", "_")
    prefix = f"PAI_TREND_LEG_VISUAL_VALIDATOR_{safe_symbol}_{timeframe}"
    html_path = output_dir / f"{prefix}.html"
    csv_path = output_dir / f"{prefix}.csv"
    json_path = output_dir / f"{prefix}.json"

    html_path.write_text(build_trend_inspector_html(symbol, timeframe, result, build, base), encoding="utf-8")
    csv_records = [{k: v for k, v in r.items() if k != "dcl_by_candle"} for r in records]
    pd.DataFrame(csv_records).to_csv(csv_path, index=False)
    json_path.write_text(json.dumps(_safe_json(records), indent=2, ensure_ascii=False), encoding="utf-8")

    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "active_bars": len(df),
        "major_swings": len(result["major"]),
        "legs": len(records),
        "tf_undersampled_legs": sum(r["trend_review_state"] == "TF_UNDERSAMPLED" for r in records),
        "tf_eligible_legs": sum(r["trend_review_state"] == "TF_ELIGIBLE_FOR_TREND_REVIEW" for r in records),
        "strategy_semantics": "NONE",
        "automatic_trend_label": "NONE",
        "html": str(html_path),
        "csv": str(csv_path),
        "json": str(json_path),
    }


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Manual Trend Leg visual validator layered on locked Swing/Leg engines.")
    p.add_argument("--repo-root", default=None)
    p.add_argument("--symbol", default=DEFAULT_SYMBOL)
    p.add_argument("--bars", type=int, default=DEFAULT_BARS)
    p.add_argument("--timeframes", nargs="+", choices=TIMEFRAMES, default=list(TIMEFRAMES))
    p.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    p.add_argument("--no-open", action="store_true")
    return p


def main() -> int:
    args = build_parser().parse_args()
    base = _load_base()
    repo_root = base.find_repo_root(args.repo_root)
    swing, leg_engine = base.load_locked_engines(repo_root)
    mt5 = base._load_mt5()
    summaries: list[dict[str, Any]] = []
    try:
        base.connect_mt5(mt5)
        symbol = base.find_symbol(mt5, args.symbol)
        out = Path(args.output_dir).resolve()
        out.mkdir(parents=True, exist_ok=True)
        for tf in args.timeframes:
            print(f"[TREND REVIEW] {symbol} {tf} | bars={args.bars}")
            summaries.append(validate_one_timeframe(base, swing, leg_engine, mt5, symbol, tf, args.bars, out))
        for s in summaries:
            print(f"{s['timeframe']} | Legs={s['legs']} | Eligible={s['tf_eligible_legs']} | Undersampled={s['tf_undersampled_legs']}")
        if not args.no_open:
            for s in summaries:
                path = Path(s["html"]).resolve()
                try:
                    if os.name == "nt" and hasattr(os, "startfile"):
                        os.startfile(str(path))
                    else:
                        webbrowser.open_new_tab(path.as_uri())
                except Exception as exc:
                    print(f"[WARN] Could not open {s['timeframe']}: {exc}")
        return 0
    finally:
        mt5.shutdown()


if __name__ == "__main__":
    raise SystemExit(main())
