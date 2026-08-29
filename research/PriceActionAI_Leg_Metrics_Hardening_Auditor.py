from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


swing = _load("pai_swing_v1_ade12", ROOT / "src" / "price_action_ai_swing_v1.py")
data_cr = _load("pai_data_integrity_cr_ade12", ROOT / "src" / "price_action_ai_data_integrity_cr.py")
leg_engine = _load("pai_leg_v0_ade12", ROOT / "src" / "price_action_ai_leg_v0.py")

TIMEFRAMES = ("M5", "M15", "M30", "H1")


def _load_mt5():
    try:
        import MetaTrader5 as mt5
    except ImportError as exc:
        raise RuntimeError("Install MetaTrader5: pip install MetaTrader5 pandas") from exc
    return mt5


def _mt5_tf(mt5, timeframe: str):
    return {
        "M5": mt5.TIMEFRAME_M5,
        "M15": mt5.TIMEFRAME_M15,
        "M30": mt5.TIMEFRAME_M30,
        "H1": mt5.TIMEFRAME_H1,
    }[timeframe]


def fetch_once(mt5, symbol: str, timeframe: str, bars: int) -> pd.DataFrame:
    if not mt5.symbol_select(symbol, True):
        raise RuntimeError(f"Could not select {symbol}: {mt5.last_error()}")
    rates = mt5.copy_rates_from_pos(symbol, _mt5_tf(mt5, timeframe), 0, bars)
    if rates is None or len(rates) == 0:
        raise RuntimeError(f"No {timeframe} data: {mt5.last_error()}")
    df = pd.DataFrame(rates)
    df["time"] = pd.to_datetime(df["time"], unit="s")
    return df.reset_index(drop=True)


def run_swing(full_df: pd.DataFrame, symbol: str, timeframe: str):
    gap = data_cr.segment_on_unexpected_gaps(full_df.copy(), timeframe, symbol=symbol)
    df = gap["active_segment"].copy().reset_index(drop=True)
    raw = swing.detect_pivot_candidates(df)
    structural, internal = swing.tag_internal_candidates(raw)
    structural = swing.add_swing_diagnostics(structural)
    thrusts = swing._leg_thrusts(structural)
    status = swing.reference_data_status(thrusts)
    if status != "OK":
        return {"status": status, "df": df, "gap": gap, "major": [], "reference": None}
    stats = swing.reference_statistics(thrusts)
    reference, _ = swing.select_nearest_actual_leg(thrusts, stats["rms"])
    major, removed = swing.select_major_swings(df, structural, reference)
    major = swing.add_swing_diagnostics(major)
    return {
        "status": "OK",
        "df": df,
        "gap": gap,
        "raw": raw,
        "structural": structural,
        "internal": internal,
        "major": major,
        "removed": removed,
        "reference": float(reference),
    }


def scheduled_gap_after_indices(result) -> set[int]:
    active_sources = result["df"]["source_index"].astype(int).tolist()
    source_to_local = {source: local for local, source in enumerate(active_sources)}
    out: set[int] = set()
    for gap in result["gap"]["scheduled_gaps"]:
        source_index = int(gap["new_segment_index"])
        if source_index in source_to_local:
            out.add(source_to_local[source_index])
    return out


def build_rows(result):
    build = leg_engine.build_confirmed_legs(
        result["major"],
        closes=result["df"]["close"].tolist(),
        scheduled_gap_after_indices=scheduled_gap_after_indices(result),
    )
    rows = []
    for n, leg in enumerate(build.legs, start=1):
        rows.append({
            "leg_no": n,
            "leg_id": f"L{n:03d}",
            "direction": leg.direction,
            "start_index": int(leg.start["index"]),
            "start_time": result["df"].iloc[int(leg.start["index"])]["time"],
            "start_kind": leg.start["kind"],
            "start_price": float(leg.start["price"]),
            "end_index": int(leg.end["index"]),
            "end_time": result["df"].iloc[int(leg.end["index"])]["time"],
            "end_kind": leg.end["kind"],
            "end_price": float(leg.end["price"]),
            "active_bar_count": leg.active_bar_count,
            "net_thrust": leg.net_thrust,
            "gross_close_path": leg.gross_close_path,
            "net_close_displacement": leg.net_close_displacement,
            "signed_close_displacement": leg.signed_close_displacement,
            "direction_agreement": leg.direction_agreement,
            "directional_efficiency": leg.directional_efficiency,
            "close_confirmation_ratio": leg.close_confirmation_ratio,
            "temporal_profile_tag": leg.temporal_profile_tag,
            "gap_path_contribution": leg.gap_path_contribution,
            "gap_path_share": leg.gap_path_share,
        })
    return build, rows


def describe(values):
    clean = [float(v) for v in values if v is not None]
    if not clean:
        return (None, None, None, None)
    s = pd.Series(clean)
    return (float(s.min()), float(s.median()), float(s.mean()), float(s.max()))


def run_one(mt5, symbol: str, timeframe: str, bars: int, output_dir: Path):
    full_df = fetch_once(mt5, symbol, timeframe, bars)
    result = run_swing(full_df, symbol, timeframe)
    if result["status"] != "OK":
        raise RuntimeError(f"{timeframe}: {result['status']}")
    build, rows = build_rows(result)
    df_rows = pd.DataFrame(rows)
    df_rows.to_csv(output_dir / f"LEG_HARDENING_AUDIT_{symbol}_{timeframe}.csv", index=False)
    pd.DataFrame(result["gap"]["scheduled_gaps"] + result["gap"]["unexpected_gaps"]).to_csv(
        output_dir / f"GAPS_{symbol}_{timeframe}.csv", index=False
    )

    eff = describe(x.directional_efficiency for x in build.legs)
    conf = describe(x.close_confirmation_ratio for x in build.legs)
    mismatch = sum(x.direction_agreement is False for x in build.legs)
    gap_affected = sum((x.gap_path_share or 0.0) > 0.0 for x in build.legs)
    max_gap = max((x.gap_path_share or 0.0 for x in build.legs), default=0.0)
    tags = pd.Series([x.temporal_profile_tag for x in build.legs]).value_counts().to_dict()

    summary = {
        "timeframe": timeframe,
        "snapshot": len(full_df),
        "active": len(result["df"]),
        "scheduled": len(result["gap"]["scheduled_gaps"]),
        "unexpected": len(result["gap"]["unexpected_gaps"]),
        "major": len(result["major"]),
        "legs": len(build.legs),
        "reference": result["reference"],
        "integration_pass": len(build.errors) == 0 and len(build.legs) == max(0, len(result["major"]) - 1),
        "direction_mismatch": mismatch,
        "under_sampled": int(tags.get("UNDER_SAMPLED", 0)),
        "normal_temporal_profile": int(tags.get("NORMAL_TEMPORAL_PROFILE", 0)),
        "higher_tf_candidate": int(tags.get("HIGHER_TF_CANDIDATE", 0)),
        "gap_affected_legs": gap_affected,
        "max_gap_share": max_gap,
        "efficiency_min": eff[0], "efficiency_median": eff[1], "efficiency_mean": eff[2], "efficiency_max": eff[3],
        "confirmation_min": conf[0], "confirmation_median": conf[1], "confirmation_mean": conf[2], "confirmation_max": conf[3],
    }
    return summary


def main() -> int:
    p = argparse.ArgumentParser(description="ADE-12 Leg Metrics Hardening auditor")
    p.add_argument("--symbol", default="XAUUSD_o")
    p.add_argument("--bars", type=int, default=500)
    p.add_argument("--timeframes", nargs="+", choices=TIMEFRAMES, default=list(TIMEFRAMES))
    p.add_argument("--output-dir", default="ADE12_Leg_Metrics_Hardening_Output")
    args = p.parse_args()

    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    mt5 = _load_mt5()
    if not mt5.initialize():
        raise RuntimeError(f"Could not initialize MT5: {mt5.last_error()}")
    try:
        account = mt5.account_info()
        print("PriceActionAI | ADE-12 LEG METRICS HARDENING")
        if account is not None:
            print("Account:", account.login, "| Server:", account.server)
        summaries = [run_one(mt5, args.symbol, tf, args.bars, output_dir) for tf in args.timeframes]
        pd.DataFrame(summaries).to_csv(output_dir / "ADE12_HARDENING_SUMMARY.csv", index=False)
        for s in summaries:
            print(
                f"{s['timeframe']:>3} | Snapshot={s['snapshot']} | Active={s['active']} | "
                f"Scheduled={s['scheduled']} | Unexpected={s['unexpected']} | Major={s['major']} | "
                f"Legs={s['legs']} | Ref={s['reference']:.5f} | "
                f"Integration={'PASS' if s['integration_pass'] else 'FAIL'}"
            )
            print(
                f"    DirectionMismatch={s['direction_mismatch']} | "
                f"Temporal U/N/H={s['under_sampled']}/{s['normal_temporal_profile']}/{s['higher_tf_candidate']} | "
                f"GapAffectedLegs={s['gap_affected_legs']} | MaxGapShare={s['max_gap_share']:.3f}"
            )
        return 0 if all(s["integration_pass"] for s in summaries) else 1
    finally:
        mt5.shutdown()


if __name__ == "__main__":
    raise SystemExit(main())
