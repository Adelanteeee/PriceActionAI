from __future__ import annotations
import base64, json, zlib, sys
from pathlib import Path
import pandas as pd

PKG = Path(__file__).resolve().parent / 'btpkg'
sys.path.insert(0, str(PKG))

from rolling_backtest import run_timeframe, pooled_metrics, VERSIONS
from research_engine import setup_config_from_json
from trade_engine import TradeConfig

# Complete three-calendar-month window available on every tested timeframe.
START = pd.Timestamp('2026-06-02 00:00:00')
END = pd.Timestamp('2026-09-02 00:00:00')
BASE = 'https://raw.githubusercontent.com/simom1/XAUUSD-history/main/Gold-Cash/XAUUSD'
TFS = ('M5','M15','M30','H1','H4','D1')


def load_tf(tf: str) -> pd.DataFrame:
    url = f'{BASE}/XAUUSD_{tf}.csv'
    df = pd.read_csv(url)
    df.columns = [str(c).strip().lower() for c in df.columns]
    if 'datetime' in df.columns and 'time' not in df.columns:
        df = df.rename(columns={'datetime':'time'})
    t = pd.to_datetime(df['time'], errors='coerce')
    m = t.between(START, END)
    out = df.loc[m].copy()
    out['time'] = t.loc[m]
    out = out.sort_values('time').drop_duplicates('time').reset_index(drop=True)
    return out


def equity_events(trades, initial=10000.0, risk=0.03):
    closed = [t for t in trades if t.get('status') in ('WIN','LOSS')]
    closed = sorted(closed, key=lambda x: str(x.get('close_time','')))
    bal = float(initial)
    events = [[None, bal]]
    for t in closed:
        bal *= 1.0 + risk * float(t['r_multiple'])
        events.append([t.get('close_time'), bal])
    return events


def main():
    setup_cfg = setup_config_from_json(PKG / 'SETUP_CONFIG.json')
    trade_cfg = TradeConfig(
        pip_size=0.01,
        entry_offset_pips=15.0,
        stop_offset_pips=20.0,
        risk_fraction=0.03,
        reward_r=1.33,
        same_bar_conflict='stop_first',
    )
    all_trades = {v: [] for v in VERSIONS}
    by_tf = {}
    data_info = {}

    for tf in TFS:
        df = load_tf(tf)
        print(f'RUN {tf}: rows={len(df)} from={df.time.iloc[0] if len(df) else None} to={df.time.iloc[-1] if len(df) else None}', flush=True)
        data_info[tf] = {
            'rows': int(len(df)),
            'first_time': str(df.time.iloc[0]) if len(df) else None,
            'last_time': str(df.time.iloc[-1]) if len(df) else None,
        }
        res = run_timeframe(df, tf, setup_cfg, trade_cfg, context_bars=220, min_context_bars=30, initial_balance=10000.0)
        by_tf[tf] = {}
        for v in VERSIONS:
            by_tf[tf][v] = {
                'metrics': res[v]['metrics'],
                'signal_count': len(res[v]['signals']),
            }
            all_trades[v].extend(res[v]['trades'])
            print(f'  {v}: signals={len(res[v]["signals"])} closed={res[v]["metrics"]["closed_trades"]}', flush=True)

    pooled = {}
    for v in VERSIONS:
        m = pooled_metrics(all_trades[v], initial_balance=10000.0, risk_fraction=0.03)
        pooled[v] = {
            'metrics': m,
            'equity_events': equity_events(all_trades[v]),
            'all_order_count': len(all_trades[v]),
        }

    payload = {
        'period': {'start': str(START), 'end': str(END)},
        'source': BASE,
        'trade_config': trade_cfg.to_dict(),
        'data_info': data_info,
        'by_timeframe': by_tf,
        'pooled': pooled,
        'pooling_note': 'All six timeframe closed outcomes are sorted by close_time and compounded at 3% of then-current balance; overlapping-position margin/exposure is not simulated.',
    }
    raw = json.dumps(payload, separators=(',',':'), allow_nan=True).encode()
    packed = base64.b64encode(zlib.compress(raw, 9)).decode()
    print('RESULT_ZLIB_B64=' + packed, flush=True)
    Path('backtest_result.json').write_text(json.dumps(payload, indent=2, allow_nan=True), encoding='utf-8')


if __name__ == '__main__':
    main()
