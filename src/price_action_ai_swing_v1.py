from __future__ import annotations

import argparse
import math
import os
import sys
import webbrowser
from pathlib import Path
from copy import deepcopy

import pandas as pd
import plotly.graph_objects as go


# ============================================================
# PriceActionAI Visual Research Prototype v1.7.3 EXTREME CARRY-FORWARD
# Sprint 1 — Swing Engine
# Goal: Preserve structural pivots -> tag internal candidates -> RMS-nearest actual Reference -> Major Swing
# ============================================================

VERSION = "1.7.5-clean-baseline"
CANDLE_COUNT = 200
SUPPORTED_TIMEFRAMES = ("M5", "M15", "M30", "H1")

# Pivot candidate baseline (carried forward from v1.2)
PIVOT_LEFT = 2
PIVOT_RIGHT = 2
ATR_PERIOD = 14
MIN_PROMINENCE_ATR = 0.60

# Structural Swing Validation — EXPERIMENTAL v1.3
# A counter-move lasting 1-4 candles can be breathing / pressure drop,
# not a structural correction, IF price resumes and breaks the previous
# directional extreme. Near-total reversals are protected from merging.
MAX_INTERNAL_BARS = 4
MAX_INTERNAL_RETRACE_RATIO = 0.80

# Reference Leg / Major Swing experiment
# A counter-move needs at least this many ACTIVE bars before it can be
# evaluated as an independent correction. Shorter moves remain internal.
MIN_CORRECTION_BARS = 5
REFERENCE_CLUSTER_TOLERANCE = 0.18
MAJOR_REJECT_RATIO = 0.50
MAJOR_ACCEPT_RATIO = 0.70
MID_QUALITY_THRESHOLD = 0.60

# Balance Tagging experiment (Sprint 1 only; NOT the final Range Engine)
BALANCE_MIN_PIVOTS = 5
BALANCE_MIN_GROSS_TO_SPAN = 2.20
BALANCE_MAX_NET_EFFICIENCY = 0.45
BALANCE_MAX_SPAN_TO_MEDIAN_LEG = 2.80


def normalize_timeframe(value: str) -> str:
    if value is None:
        return "M5"
    cleaned = str(value).strip().upper().replace(" ", "")
    aliases = {"5":"M5","5M":"M5","M5":"M5","15":"M15","15M":"M15","M15":"M15","30":"M30","30M":"M30","M30":"M30","60":"H1","60M":"H1","1H":"H1","H1":"H1"}
    if cleaned not in aliases:
        raise ValueError(f"Unsupported timeframe '{value}'. Use one of: M5, M15, M30, H1.")
    return aliases[cleaned]


def _load_mt5():
    try:
        import MetaTrader5 as mt5
    except ImportError:
        print("\n[ERROR] Python package MetaTrader5 is not installed.")
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
        print("\n[ERROR] MT5 is open but no account was detected.")
        mt5.shutdown(); sys.exit(1)
    print("\n============================================================")
    print(" PriceActionAI v1.7.5 | Locked Swing v1")
    print("============================================================")
    print("MT5 connection : OK")
    print("Account        :", account.login)
    print("Server         :", account.server)
    print("Balance        :", account.balance)
    print("============================================================\n")


def find_symbol(mt5, requested: str):
    symbols = mt5.symbols_get()
    if symbols is None:
        return None
    names = [s.name for s in symbols]
    requested = (requested or "XAUUSD").strip(); req_u = requested.upper()
    for name in names:
        if name.upper() == req_u:
            return name
    alias_groups = {"XAUUSD":("XAUUSD","GOLD"),"GOLD":("XAUUSD","GOLD"),"NASDAQ":("NASDAQ","NAS100","US100","USTEC","NDX","NQ100","NQ"),"NAS100":("NAS100","NASDAQ","US100","USTEC","NDX","NQ100","NQ"),"US100":("US100","NASDAQ","NAS100","USTEC","NDX","NQ100","NQ")}
    keys = alias_groups.get(req_u, (req_u,))
    for key in keys:
        starts = [name for name in names if name.upper().startswith(key)]
        if starts: return sorted(starts, key=len)[0]
    for key in keys:
        contains = [name for name in names if key in name.upper()]
        if contains: return sorted(contains, key=len)[0]
    return None


def resolve_mt5_timeframe(mt5, timeframe_name: str):
    timeframe_name = normalize_timeframe(timeframe_name)
    return getattr(mt5, {"M5":"TIMEFRAME_M5","M15":"TIMEFRAME_M15","M30":"TIMEFRAME_M30","H1":"TIMEFRAME_H1"}[timeframe_name])


def get_candles(mt5, symbol, timeframe_name, count=CANDLE_COUNT):
    timeframe = resolve_mt5_timeframe(mt5, timeframe_name)
    if not mt5.symbol_select(symbol, True):
        print(f"[ERROR] Could not select symbol: {symbol}"); return None
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
    if rates is None or len(rates) == 0:
        print("[ERROR] No candle data received."); print("MT5 error:", mt5.last_error()); return None
    df = pd.DataFrame(rates); df["time"] = pd.to_datetime(df["time"], unit="s")
    return df.reset_index(drop=True)


def calculate_atr(df, period=ATR_PERIOD):
    prev_close = df["close"].shift(1)
    tr = pd.concat([df["high"]-df["low"], (df["high"]-prev_close).abs(), (df["low"]-prev_close).abs()], axis=1).max(axis=1)
    return tr.rolling(period, min_periods=1).mean()


def enforce_alternation(candidates):
    filtered=[]
    for candidate in candidates:
        candidate=deepcopy(candidate)
        if not filtered: filtered.append(candidate); continue
        last=filtered[-1]
        if candidate["kind"]==last["kind"]:
            replace=(candidate["kind"]=="SH" and candidate["price"]>last["price"]) or (candidate["kind"]=="SL" and candidate["price"]<last["price"])
            if replace: filtered[-1]=candidate
            continue
        if candidate["index"]==last["index"]:
            if len(filtered)>=2:
                previous=filtered[-2]; old_move=abs(last["price"]-previous["price"]); new_move=abs(candidate["price"]-previous["price"])
                if new_move>old_move: filtered[-1]=candidate
            continue
        filtered.append(candidate)
    return filtered


def detect_pivot_candidates(df,left=PIVOT_LEFT,right=PIVOT_RIGHT,atr_period=ATR_PERIOD,min_prominence_atr=MIN_PROMINENCE_ATR):
    if len(df)<left+right+1: return []
    atr=calculate_atr(df,atr_period); candidates=[]
    for i in range(left,len(df)-right):
        window=df.iloc[i-left:i+right+1]; current_atr=float(atr.iloc[i])
        if not math.isfinite(current_atr) or current_atr<=0: continue
        current_high=float(df.iloc[i]["high"]); current_low=float(df.iloc[i]["low"])
        is_local_high=current_high>=float(window["high"].max()); is_local_low=current_low<=float(window["low"].min())
        high_excursion=current_high-float(window["low"].min()); low_excursion=float(window["high"].max())-current_low; min_excursion=min_prominence_atr*current_atr
        if is_local_high and high_excursion>=min_excursion:
            candidates.append({"index":i,"time":df.iloc[i]["time"],"kind":"SH","price":current_high,"atr":current_atr,"prominence_atr":high_excursion/current_atr})
        if is_local_low and low_excursion>=min_excursion:
            candidates.append({"index":i,"time":df.iloc[i]["time"],"kind":"SL","price":current_low,"atr":current_atr,"prominence_atr":low_excursion/current_atr})
    candidates.sort(key=lambda x:(x["index"],0 if x["kind"]=="SL" else 1))
    return enforce_alternation(candidates)


def _retrace_ratio(a,b,c):
    impulse=abs(float(b["price"])-float(a["price"]))
    if impulse<=0:return float("inf")
    return abs(float(c["price"])-float(b["price"]))/impulse


def tag_internal_candidates(swings,max_internal_bars=MAX_INTERNAL_BARS,max_retrace_ratio=MAX_INTERNAL_RETRACE_RATIO):
    result=[deepcopy(s) for s in swings]; candidate_keys=set()
    for i in range(len(result)-3):
        a,b,c,d=result[i:i+4]
        bullish=(a["kind"]=="SL" and b["kind"]=="SH" and c["kind"]=="SL" and d["kind"]=="SH" and float(d["price"])>float(b["price"]))
        bearish=(a["kind"]=="SH" and b["kind"]=="SL" and c["kind"]=="SH" and d["kind"]=="SL" and float(d["price"])<float(b["price"]))
        counter_bars=int(c["index"])-int(b["index"]); retrace_ratio=_retrace_ratio(a,b,c)
        if (bullish or bearish) and 0<counter_bars<=max_internal_bars and retrace_ratio<=max_retrace_ratio:
            reason=f"internal candidate | bars={counter_bars} | retrace={retrace_ratio:.1%}"
            for pos in (i+1,i+2):
                result[pos]["internal_candidate"]=True
                reasons=result[pos].setdefault("internal_candidate_reasons",[])
                if reason not in reasons: reasons.append(reason)
                result[pos]["internal_candidate_reason"]=reason
                candidate_keys.add((int(result[pos]["index"]),result[pos]["kind"]))
    candidates=[deepcopy(s) for s in result if (int(s["index"]),s["kind"]) in candidate_keys]
    return result,candidates


def add_swing_diagnostics(swings):
    return [deepcopy(s) for s in swings]


def _leg_thrusts(swings):
    return [abs(float(b["price"])-float(a["price"])) for a,b in zip(swings[:-1],swings[1:]) if abs(float(b["price"])-float(a["price"]))>0]


def reference_statistics(values):
    clean=[float(v) for v in values if math.isfinite(float(v)) and float(v)>0]
    if not clean:return {"mean":0.0,"median":0.0,"rms":0.0}
    s=sorted(clean); n=len(s); median=s[n//2] if n%2 else (s[n//2-1]+s[n//2])/2
    return {"mean":sum(clean)/n,"median":median,"rms":math.sqrt(sum(v*v for v in clean)/n)}


def select_nearest_actual_leg(values,target):
    clean=[float(v) for v in values if math.isfinite(float(v)) and float(v)>0]
    if not clean or target is None or not math.isfinite(float(target)) or float(target)<=0:return None,[]
    target=float(target); selected=min(clean,key=lambda v:(abs(v-target),v))
    return selected,[selected]


def move_quality(df,start_idx,end_idx,direction):
    lo=min(int(start_idx),int(end_idx)); hi=max(int(start_idx),int(end_idx))
    if hi<=lo:return 0.0
    seg=df.iloc[lo:hi+1]
    if len(seg)<2:return 0.0
    ranges=(seg["high"]-seg["low"]).replace(0,float("nan")); bodies=(seg["close"]-seg["open"]).abs()
    body_eff=float((bodies/ranges).fillna(0).mean())
    signed=(seg["close"]-seg["open"])*float(direction); directional=float((signed>0).mean())
    start=float(seg.iloc[0]["close"]); end=float(seg.iloc[-1]["close"]); net=abs(end-start); gross=float(seg["close"].diff().abs().sum())
    efficiency=net/gross if gross>0 else 0.0
    return max(0.0,min(1.0,0.4*body_eff+0.3*directional+0.3*efficiency))


def classify_leg_against_reference(df,a,b,reference_leg):
    thrust=abs(float(b["price"])-float(a["price"])); ratio=thrust/reference_leg if reference_leg and reference_leg>0 else 0.0; direction=1 if float(b["price"])>float(a["price"]) else -1
    quality=move_quality(df,a["index"],b["index"],direction)
    if ratio<MAJOR_REJECT_RATIO:status="REJECT"
    elif ratio<MAJOR_ACCEPT_RATIO:status="ACCEPT" if quality>=MID_QUALITY_THRESHOLD else "REJECT"
    else:status="ACCEPT"
    return {"thrust":thrust,"ratio":ratio,"quality":quality,"status":status}


def select_major_swings(df,swings,reference_leg):
    result=[deepcopy(s) for s in swings]; removed=[]; changed=True
    while changed and len(result)>=4:
        changed=False
        for i in range(len(result)-4,-1,-1):
            a,b,c,d=result[i:i+4]
            bullish=(a["kind"]=="SL" and b["kind"]=="SH" and c["kind"]=="SL" and d["kind"]=="SH" and float(d["price"])>float(b["price"]))
            bearish=(a["kind"]=="SH" and b["kind"]=="SL" and c["kind"]=="SH" and d["kind"]=="SL" and float(d["price"])<float(b["price"]))
            if not (bullish or bearish):continue
            counter_bars=int(c["index"])-int(b["index"]); counter=classify_leg_against_reference(df,b,c,reference_leg)
            temporal_internal=0<counter_bars<MIN_CORRECTION_BARS
            if not temporal_internal and counter["status"]!="REJECT":continue
            if temporal_internal:
                reason=f"temporal internal continuation | bars={counter_bars} < {MIN_CORRECTION_BARS} | ref={reference_leg:.6f} | counter={counter['thrust']:.6f} ({counter['ratio']:.1%}) | quality={counter['quality']:.2f}"
            else:
                reason=f"reference-leg internal continuation | bars={counter_bars} | ref={reference_leg:.6f} | counter={counter['thrust']:.6f} ({counter['ratio']:.1%}) | quality={counter['quality']:.2f}"
            carry_c=float(c["price"])<float(a["price"]) if bullish else float(c["price"])>float(a["price"])
            if carry_c:
                origin=deepcopy(c); origin["extreme_carry_forward"]=True; origin["extreme_carry_reason"]=reason; dropped_items=(a,b); result[i]=origin
            else:dropped_items=(b,c)
            for item in dropped_items:
                r=deepcopy(item); r["major_filter_reason"]=reason; r["filter_reason"]=reason; removed.append(r)
            del result[i+1:i+3]; changed=True; break
    return enforce_alternation(result),removed


MIN_REFERENCE_LEGS=3
WEEKEND_MAX_GAP_DAYS=4
GAP_TOLERANCE_BARS=3
_TIMEFRAME_MINUTES={"M5":5,"M15":15,"M30":30,"H1":60}
_FX_CODES={"USD","EUR","GBP","JPY","CHF","AUD","NZD","CAD","NOK","SEK","DKK","SGD","HKD","CNH","CNY","MXN","ZAR","TRY","PLN","HUF","CZK"}


def timeframe_delta(timeframe):return pd.Timedelta(minutes=_TIMEFRAME_MINUTES[normalize_timeframe(timeframe)])
def _crosses_weekend(start,end):
    day=start.normalize(); last=end.normalize()
    while day<=last:
        if day.weekday()>=5:return True
        day+=pd.Timedelta(days=1)
    return False

def _gap_signature(prev,curr,expected):return (prev.strftime("%H:%M"),curr.strftime("%H:%M"),max(1,int(round((curr-prev)/expected))))

def classify_time_gaps(df,timeframe):
    from collections import Counter
    if len(df)<2:return {"scheduled":[],"unexpected":[]}
    expected=timeframe_delta(timeframe); times=pd.to_datetime(df["time"]).reset_index(drop=True); candidates=[]
    for i in range(1,len(times)):
        prev,curr=times.iloc[i-1],times.iloc[i]; delta=curr-prev
        if delta>expected*1.5:candidates.append({"previous_index":i-1,"new_segment_index":i,"previous_time":prev,"current_time":curr,"delta":delta,"signature":_gap_signature(prev,curr,expected)})
    sig_counts=Counter(c["signature"] for c in candidates); scheduled=[]; unexpected=[]
    for gap in candidates:
        delta=gap["delta"]; prev=gap["previous_time"]; curr=gap["current_time"]
        if delta<=expected*GAP_TOLERANCE_BARS:gap["reason"]="TOLERATED_BAR_GAP"; scheduled.append(gap)
        elif _crosses_weekend(prev,curr) and delta<=pd.Timedelta(days=WEEKEND_MAX_GAP_DAYS):gap["reason"]="SCHEDULED_WEEKEND"; scheduled.append(gap)
        elif sig_counts[gap["signature"]]>=2:gap["reason"]="RECURRING_SESSION_CLOSURE"; scheduled.append(gap)
        else:gap["reason"]="UNEXPECTED_DATA_GAP"; unexpected.append(gap)
    return {"scheduled":scheduled,"unexpected":unexpected}


def segment_on_unexpected_gaps(df,timeframe):
    ordered=df.copy(); ordered["time"]=pd.to_datetime(ordered["time"]); ordered=ordered.sort_values("time").reset_index(drop=True); ordered["source_index"]=range(len(ordered))
    gaps=classify_time_gaps(ordered,timeframe); boundaries=[g["new_segment_index"] for g in gaps["unexpected"]]; starts=[0]+boundaries; ends=boundaries+[len(ordered)]
    segments=[ordered.iloc[s:e].copy().reset_index(drop=True) for s,e in zip(starts,ends)] or [ordered]
    return {"segments":segments,"active_segment":segments[-1].copy().reset_index(drop=True),"scheduled_gaps":gaps["scheduled"],"unexpected_gaps":gaps["unexpected"]}


def reference_data_status(thrusts,min_legs=MIN_REFERENCE_LEGS):
    valid=[float(x) for x in thrusts if x is not None and math.isfinite(float(x)) and float(x)>0]
    return "OK" if len(valid)>=int(min_legs) else "INSUFFICIENT_DATA"

def _looks_like_fx(symbol,path=""):
    clean="".join(ch for ch in str(symbol).upper() if ch.isalpha())
    if "FOREX" in str(path).upper():return True
    return len(clean)>=6 and clean[:3] in _FX_CODES and clean[3:6] in _FX_CODES

def symbol_display_spec(symbol,symbol_info):
    digits=int(getattr(symbol_info,"digits",5) if symbol_info is not None else 5); point=float(getattr(symbol_info,"point",10**(-digits)) if symbol_info is not None else 10**(-digits)); path=str(getattr(symbol_info,"path","") if symbol_info is not None else ""); is_fx=_looks_like_fx(symbol,path); pip_size=point*10 if is_fx and digits in (3,5) else (point if is_fx else None)
    return {"symbol":symbol,"digits":digits,"point":point,"is_fx":is_fx,"pip_size":pip_size}
def raw_to_pips(value,spec):return None if not spec.get("pip_size") else float(value)/float(spec["pip_size"])
def format_delta(value,spec):return f"{float(value):.{int(spec['digits'])}f}" if spec.get("is_fx") else f"{float(value):.6f}"
def atr_normalized(value,atr_value):return None if atr_value is None or float(atr_value)<=0 else float(value)/float(atr_value)

def _pivot_key(p):return (int(p["index"]),str(p["kind"]),round(float(p["price"]),12))
def audit_counts(structural,major,major_removed):
    structural_keys=[_pivot_key(p) for p in structural]; structural_set=set(structural_keys); major_set={_pivot_key(p) for p in major if _pivot_key(p) in structural_set}; removed_set=set()
    for item in major_removed:
        pivot=item.get("pivot") if isinstance(item,dict) and isinstance(item.get("pivot"),dict) else item
        if isinstance(pivot,dict) and all(k in pivot for k in ("index","kind","price")):
            key=_pivot_key(pivot)
            if key in structural_set:removed_set.add(key)
    accounted=major_set|removed_set; leftover=[k for k in structural_keys if k not in accounted]; pos={k:i for i,k in enumerate(structural_keys)}; last=max([pos[k] for k in accounted if k in pos],default=-1); provisional=[k for k in leftover if pos[k]>last]; unaccounted=[k for k in leftover if k not in provisional]
    return {"structural":len(structural_set),"major_unique":len(major_set),"removed_events":len(major_removed),"removed_unique":len(removed_set),"right_edge_provisional":len(provisional),"right_edge_provisional_keys":provisional,"unaccounted":len(unaccounted),"unaccounted_keys":unaccounted,"invariant_ok":len(major_set)+len(removed_set)+len(provisional)+len(unaccounted)==len(structural_set) and len(unaccounted)==0}
def structural_filter_audit(raw_count,structural_count):
    removed=max(0,int(raw_count)-int(structural_count)); return {"raw":int(raw_count),"structural":int(structural_count),"removed":removed,"label":"NO_STRUCTURAL_REMOVAL" if removed==0 else "STRUCTURAL_FILTER_APPLIED"}

_REQUIRED_SNAPSHOT_COLUMNS=("time","open","high","low","close")
def load_snapshot_file(path):
    df=pd.read_csv(Path(path).expanduser().resolve()); missing=[c for c in _REQUIRED_SNAPSHOT_COLUMNS if c not in df.columns]
    if missing:raise ValueError("Snapshot is missing required columns: "+", ".join(missing))
    out=df.copy(); out["time"]=pd.to_datetime(out["time"],errors="coerce")
    for col in ("open","high","low","close"):out[col]=pd.to_numeric(out[col],errors="coerce")
    return out.sort_values("time").reset_index(drop=True)

def _load_core():
    return sys.modules[__name__]


def _build_chart(df,symbol,timeframe,structural,major,summary):
    fig=go.Figure(); x=list(range(len(df))); labels=df["time"].dt.strftime("%Y-%m-%d %H:%M")
    fig.add_trace(go.Candlestick(x=x,open=df["open"],high=df["high"],low=df["low"],close=df["close"],customdata=labels,name=symbol))
    sh=[p for p in structural if p.get("kind")=="SH"]; sl=[p for p in structural if p.get("kind")=="SL"]
    if sh:fig.add_trace(go.Scatter(x=[p["index"] for p in sh],y=[p["price"] for p in sh],mode="markers",marker=dict(symbol="triangle-down",size=7,opacity=0.4),name="Structural SH (all)"))
    if sl:fig.add_trace(go.Scatter(x=[p["index"] for p in sl],y=[p["price"] for p in sl],mode="markers",marker=dict(symbol="triangle-up",size=7,opacity=0.4),name="Structural SL (all)"))
    if major:fig.add_trace(go.Scatter(x=[p["index"] for p in major],y=[p["price"] for p in major],mode="lines+markers",name="Major Swing Path"))
    fig.update_layout(title=f"PriceActionAI {VERSION} | {symbol} | {timeframe} | Snapshot {len(df)}",xaxis_title="Active Market Bars (scheduled closures compressed)",yaxis_title="Price",xaxis_rangeslider_visible=False,template="plotly_dark")
    fig.add_annotation(x=0.01,y=0.99,xref="paper",yref="paper",text=summary,showarrow=False,align="left",xanchor="left",yanchor="top",bgcolor="rgba(0,0,0,0.62)")
    return fig


def parse_args():
    p=argparse.ArgumentParser(); p.add_argument("--symbol",default=None); p.add_argument("--timeframe",default="M30"); p.add_argument("--count",type=int,default=200); p.add_argument("--snapshot-file",default=None); p.add_argument("--output-dir",default=None); p.add_argument("--no-open",action="store_true"); return p.parse_args()

def main():
    args=parse_args(); timeframe=normalize_timeframe(args.timeframe); outdir=Path(args.output_dir).resolve() if args.output_dir else Path.cwd(); outdir.mkdir(parents=True,exist_ok=True); mt5=None
    try:
        if args.snapshot_file:
            full_df=load_snapshot_file(args.snapshot_file); symbol=args.symbol or "SNAPSHOT"; spec=symbol_display_spec(symbol,None); source="FIXED_CSV_SNAPSHOT"
        else:
            mt5=_load_mt5(); connect_mt5(mt5); symbol=find_symbol(mt5,args.symbol or "XAUUSD"); info=mt5.symbol_info(symbol); spec=symbol_display_spec(symbol,info); full_df=get_candles(mt5,symbol,timeframe,max(20,args.count)); source="MT5_LIVE_FETCH"
        gap=segment_on_unexpected_gaps(full_df,timeframe); df=gap["active_segment"].copy().reset_index(drop=True); raw=detect_pivot_candidates(df); structural,internal=tag_internal_candidates(raw); structural=add_swing_diagnostics(structural); thrusts=_leg_thrusts(structural); status=reference_data_status(thrusts)
        if status=="OK":
            stats=reference_statistics(thrusts); ref,_=select_nearest_actual_leg(thrusts,stats["rms"]); major,removed=select_major_swings(df,structural,ref)
        else:
            stats={"mean":0.0,"median":0.0,"rms":0.0}; ref=0.0; major=[]; removed=[]
        audit=audit_counts(structural,major,removed); summary="<br>".join([f"DATA SOURCE: {source}",f"STATUS: {status}",f"RAW PIVOTS: {len(raw)}",f"STRUCTURAL: {len(structural)}",f"MAJOR UNIQUE: {audit['major_unique']}",f"COUNT INVARIANT: {'OK' if audit['invariant_ok'] else 'ERROR'}",f"REFERENCE: {format_delta(ref,spec)}",f"BALANCE: PARKED"])
        fig=_build_chart(df,symbol,timeframe,structural,major,summary); safe="".join(c if c.isalnum() or c in "-_" else "_" for c in symbol); html=outdir/f"PriceActionAI_{VERSION}_{safe}_{timeframe}.html"; fig.write_html(str(html),include_plotlyjs=True,full_html=True,auto_open=False)
        print(f"Status                  : {status}"); print(f"Snapshot bars           : {len(full_df)}"); print(f"Segments                : {len(gap['segments'])}"); print(f"Active segment bars     : {len(df)}"); print(f"Unexpected gaps         : {len(gap['unexpected_gaps'])}")
        for g in gap["unexpected_gaps"]:print(f"  GAP RESET: {g['previous_time']} -> {g['current_time']} | {g['delta']}")
        print(f"Major unique            : {audit['major_unique']}"); print(f"Count invariant         : {'OK' if audit['invariant_ok'] else 'ERROR'}"); print(f"Reference raw           : {format_delta(ref,spec)}"); print(f"Offline HTML            : {html}")
        if not args.no_open:
            try:webbrowser.open(html.resolve().as_uri(),new=2)
            except Exception:pass
    finally:
        if mt5 is not None:mt5.shutdown()

if __name__=="__main__":main()
