import importlib.util
from pathlib import Path
import pandas as pd

MODULE_PATH = Path(__file__).resolve().parents[1] / 'price_action_ai_v1_7_5_offline_temporal_gate.py'
spec = importlib.util.spec_from_file_location('pai_v172', MODULE_PATH)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

def sw(i,k,p):
    return {'index':i,'time':pd.Timestamp('2026-01-01')+pd.Timedelta(hours=i),'kind':k,'price':float(p),'atr':5.0,'prominence_atr':1.0}

def df(n=30):
    rows=[]
    for i in range(n):
        o=100+i*0.1; c=o+(0.2 if i%2==0 else -0.1)
        rows.append({'open':o,'high':max(o,c)+0.5,'low':min(o,c)-0.5,'close':c})
    return pd.DataFrame(rows)

def test_bearish_merge_carries_forward_higher_sh_origin():
    xs=[sw(0,'SH',200),sw(3,'SL',150),sw(6,'SH',220),sw(9,'SL',130)]
    out,_=m.select_major_swings(df(),xs,reference_leg=200.0)
    assert [(x['kind'],x['price']) for x in out]==[('SH',220.0),('SL',130.0)], out

def test_bullish_merge_carries_forward_lower_sl_origin():
    xs=[sw(0,'SL',100),sw(3,'SH',150),sw(6,'SL',80),sw(9,'SH',175)]
    out,_=m.select_major_swings(df(),xs,reference_leg=200.0)
    assert [(x['kind'],x['price']) for x in out]==[('SL',80.0),('SH',175.0)], out

if __name__=='__main__':
    failed=[]
    for n in [n for n in globals() if n.startswith('test_')]:
        try: globals()[n](); print('PASS',n)
        except Exception as e: failed.append((n,e)); print('FAIL',n,e)
    if failed: raise SystemExit(1)
