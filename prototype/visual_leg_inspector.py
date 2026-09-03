from __future__ import annotations

"""Standalone base inspector used by the parallel Trend visual validator.

This file preserves the descriptive-only Swing/Leg visual inspection role and adds
pinned locked-engine resolution so exported bundles do not require a separate
local PriceActionAI checkout. Engine files are verified by Git blob SHA before
loading; no Swing or Leg semantics are changed here.
"""

import argparse
import hashlib
import importlib.util
import json
import os
import sys
import urllib.request
import webbrowser
from pathlib import Path
from typing import Any, Iterable, Sequence

import pandas as pd
import plotly.graph_objects as go

TIMEFRAMES = ("M5", "M15", "M30", "H1")
DEFAULT_SYMBOL = "XAUUSD_o"
DEFAULT_TIMEFRAMES = ("M15",)
DEFAULT_BARS = 1200
OUTPUT_DIR_NAME = "PriceActionAI_Parallel_Visual_Leg_Inspector_Output"

PINNED_ENGINE_COMMIT = "b2595784edc09d88f436fe447354f35a3cf4a850"
REQUIRED_ENGINE_FILES = (
    "price_action_ai_swing_v1.py",
    "price_action_ai_swing_v1_locked.py",
    "price_action_ai_data_integrity_cr.py",
    "price_action_ai_leg_v0.py",
)
ENGINE_BLOB_SHA1 = {
    "price_action_ai_swing_v1.py": "b003769136665f51fbe5a05f253319648089aae1",
    "price_action_ai_swing_v1_locked.py": "e3c2ae1ea250bd4ec755f5f2d9a3d7b641ca6d2d",
    "price_action_ai_data_integrity_cr.py": "dba3cfcc3962c3b7e485f1284ed7fdace3dfdd60",
    "price_action_ai_leg_v0.py": "e4062ad8fc4efc806f15d25327fb4398f3aeec64",
}
ENGINE_RAW_BASE = (
    "https://raw.githubusercontent.com/Adelanteeee/PriceActionAI/"
    + PINNED_ENGINE_COMMIT
    + "/src/"
)

LOCKED_LEG_FEATURE_FIELDS = (
    "active_bar_count", "net_thrust", "gross_close_path", "net_close_displacement",
    "signed_close_displacement", "direction_agreement", "directional_efficiency",
    "aligned_close_steps", "opposing_close_steps", "flat_close_steps",
    "directional_continuity_ratio", "close_confirmation_ratio", "temporal_profile_tag",
    "gap_path_contribution", "gap_path_share", "gross_body_magnitude", "gross_candle_range",
    "body_strength_ratio", "gross_upper_shadow", "gross_lower_shadow", "gross_forward_shadow",
    "gross_backward_shadow", "gross_shadow_magnitude", "shadow_position_imbalance",
    "gross_overlap_magnitude", "gross_overlap_capacity", "overlap_ratio", "close_ols_slope",
    "directional_close_ols_slope", "normalized_directional_close_ols_slope",
    "gross_tick_activity", "mean_tick_activity",
)


def git_blob_sha(payload: bytes) -> str:
    header = f"blob {len(payload)}\0".encode("ascii")
    return hashlib.sha1(header + payload).hexdigest()


def _engine_root_is_valid(root: Path) -> bool:
    src = root / "src"
    for name in REQUIRED_ENGINE_FILES:
        path = src / name
        if not path.is_file():
            return False
        try:
            if git_blob_sha(path.read_bytes()) != ENGINE_BLOB_SHA1[name]:
                return False
        except OSError:
            return False
    return True


def _download_pinned_engine(target_root: Path) -> Path:
    src = target_root / "src"
    src.mkdir(parents=True, exist_ok=True)
    for name in REQUIRED_ENGINE_FILES:
        path = src / name
        expected = ENGINE_BLOB_SHA1[name]
        if path.is_file() and git_blob_sha(path.read_bytes()) == expected:
            continue
        url = ENGINE_RAW_BASE + name
        try:
            with urllib.request.urlopen(url, timeout=30) as response:
                payload = response.read()
        except Exception as exc:
            raise RuntimeError(f"Could not download pinned locked engine file {name}: {exc}") from exc
        actual = git_blob_sha(payload)
        if actual != expected:
            raise RuntimeError(
                f"Pinned engine integrity check failed for {name}: expected git blob {expected}, got {actual}."
            )
        path.write_bytes(payload)
    return target_root.resolve()


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def find_repo_root(explicit: str | None = None) -> Path:
    candidates = []
    if explicit:
        candidates.append(Path(explicit).expanduser().resolve())
    here = Path(__file__).resolve().parent
    candidates.extend([here, *here.parents])
    for root in candidates:
        if (root / "src" / "price_action_ai_swing_v1.py").exists() and (root / "src" / "price_action_ai_leg_v0.py").exists():
            return root
    raise FileNotFoundError("PriceActionAI repo root not found.")


def resolve_engine_root(explicit: str | None = None, *, allow_download: bool = True) -> tuple[Path, str]:
    here = Path(__file__).resolve().parent
    bundled_candidates = [(here / "_locked_engine").resolve(), (here.parent / "_locked_engine").resolve()]
    bundled = bundled_candidates[0]
    for candidate in bundled_candidates:
        if _engine_root_is_valid(candidate):
            return candidate, "BUNDLED_LOCKED_ENGINE"

    candidates = []
    if explicit:
        candidates.append(Path(explicit).expanduser().resolve())
    candidates.extend([here, *here.parents])
    for root in candidates:
        if _engine_root_is_valid(root):
            return root, "LOCAL_PRICEACTIONAI_REPO"

    if allow_download:
        return _download_pinned_engine(bundled), "PINNED_ENGINE_DOWNLOADED_AND_VERIFIED"
    raise FileNotFoundError("Locked PriceActionAI engine not found locally.")


def load_locked_engines(engine_root: Path):
    swing = _load_module("price_action_ai_swing_v1_parallel_inspector", engine_root / "src" / "price_action_ai_swing_v1.py")
    leg = _load_module("price_action_ai_leg_v0_parallel_inspector", engine_root / "src" / "price_action_ai_leg_v0.py")
    return swing, leg


def _load_mt5():
    try:
        import MetaTrader5 as mt5
    except ImportError as exc:
        raise RuntimeError("MetaTrader5 package is missing. Install with: pip install MetaTrader5 pandas plotly") from exc
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
    raise RuntimeError(f"Could not find broker symbol for '{requested}'.")


def mt5_timeframe(mt5, timeframe: str):
    return {"M5": mt5.TIMEFRAME_M5, "M15": mt5.TIMEFRAME_M15, "M30": mt5.TIMEFRAME_M30, "H1": mt5.TIMEFRAME_H1}[timeframe]


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
    return {"df": active, "gap": gap, "raw": raw, "structural": structural, "internal": internal, "stats": stats, "reference": float(reference), "major": major, "removed": removed}


def scheduled_gap_active_indices(active_df: pd.DataFrame, gap_result: dict[str, Any]) -> set[int]:
    if "source_index" not in active_df.columns:
        return set()
    source_to_active = {int(v): i for i, v in enumerate(active_df["source_index"].tolist())}
    mapped = set()
    for gap in gap_result.get("scheduled_gaps", []):
        source_index = int(gap["new_segment_index"])
        if source_index in source_to_active:
            mapped.add(int(source_to_active[source_index]))
    return mapped


def leg_engine_kwargs(df: pd.DataFrame, scheduled_gap_indices: set[int]) -> dict[str, Any]:
    return {
        "opens": [float(v) for v in df["open"].tolist()], "highs": [float(v) for v in df["high"].tolist()],
        "lows": [float(v) for v in df["low"].tolist()], "closes": [float(v) for v in df["close"].tolist()],
        "tick_volume": [int(v) for v in df["tick_volume"].tolist()] if "tick_volume" in df.columns else None,
        "scheduled_gap_after_indices": set(int(v) for v in scheduled_gap_indices),
    }


def _jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if hasattr(value, "item"):
        return value.item()
    return str(value)


def leg_feature_payload(leg_no: int, leg: Any, df: pd.DataFrame) -> dict[str, Any]:
    si, ei = int(leg.start["index"]), int(leg.end["index"])
    payload = {
        "leg_no": int(leg_no), "direction": str(leg.direction), "start_index": si,
        "start_time": str(df.iloc[si]["time"]), "start_kind": str(leg.start["kind"]), "start_price": float(leg.start["price"]),
        "end_index": ei, "end_time": str(df.iloc[ei]["time"]), "end_kind": str(leg.end["kind"]), "end_price": float(leg.end["price"]),
    }
    for field in LOCKED_LEG_FEATURE_FIELDS:
        payload[field] = _jsonable(getattr(leg, field, None))
    return payload


def active_bar_axis(timestamps: Iterable[object]) -> list[int]:
    return list(range(len(list(timestamps))))


def sample_time_ticks(timestamps: Sequence[object], max_ticks: int = 12) -> tuple[list[int], list[str]]:
    n = len(timestamps)
    if n == 0:
        return [], []
    if n <= max_ticks:
        idx = list(range(n))
    else:
        step = (n - 1) / float(max_ticks - 1)
        idx = sorted({round(i * step) for i in range(max_ticks)})
    return idx, [pd.Timestamp(timestamps[i]).strftime("%Y-%m-%d\n%H:%M") for i in idx]


def build_chart(symbol: str, timeframe: str, result: dict[str, Any], build) -> go.Figure:
    df = result["df"]
    fig = go.Figure()
    fig.add_trace(go.Candlestick(x=active_bar_axis(df["time"].tolist()), open=df["open"], high=df["high"], low=df["low"], close=df["close"], name=f"{symbol} {timeframe}", meta={"pai_kind": "candle"}))
    fig.add_trace(go.Scatter(x=[int(p["index"]) for p in result["major"]], y=[float(p["price"]) for p in result["major"]], mode="lines+markers+text", text=[p["kind"] for p in result["major"]], name="Locked Major Swing spine", meta={"pai_kind": "swing"}))
    for leg_no, leg in enumerate(build.legs, start=1):
        payload = leg_feature_payload(leg_no, leg, df)
        fig.add_trace(go.Scatter(x=[payload["start_index"], payload["end_index"]], y=[payload["start_price"], payload["end_price"]], mode="lines", line={"width": 6}, showlegend=False, name=f"Leg {leg_no}", meta={"pai_kind": "leg", "payload": payload}))
    tickvals, ticktext = sample_time_ticks(df["time"].tolist())
    fig.update_layout(title=f"PriceActionAI Parallel Visual Swing + Leg Inspector | {symbol} {timeframe}", xaxis_rangeslider_visible=False, hovermode="closest", clickmode="event+select", height=900)
    fig.update_xaxes(tickmode="array", tickvals=tickvals, ticktext=ticktext)
    return fig
