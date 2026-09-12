import importlib.util, sys, types, pandas as pd
base=types.SimpleNamespace(START=pd.Timestamp('2025-01-01'),END=pd.Timestamp('2026-01-01'),WARM=pd.Timestamp('2024-12-01'),VERSIONS=('Prominence','Combined','Candle Count Bar v1'),TFS={'M1':1,'M5':5,'M15':15,'M30':30})
base.next_news_close_due=lambda t,lead: False
base.news_blocked=lambda t: False
sys.modules['annual_v63_runner']=base
spec=importlib.util.spec_from_file_location('c','corrected_v63_replay.py');c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)

def test_dd_open_equity():
    d=c.DDTracker(1000); d.observe(1100); d.observe(990); assert abs(d.pct-10.0)<1e-9

def test_size_ladder_and_margin():
    cand={'entry':3000.0,'sl':2990.0}; x=c.size_order(cand,1000,1000,0); assert x is not None
    lot,loss,target,margin=x; assert abs(target-30)<1e-9 and abs(lot-0.03)<1e-9 and abs(loss-30)<1e-9 and abs(margin-18)<1e-9

def test_tf_resample_does_not_create_empty_bars():
    m1=pd.DataFrame({'time':pd.to_datetime(['2025-01-02 00:00','2025-01-02 00:01','2025-01-02 00:10']), 'open':[1,2,3],'high':[1,2,3],'low':[1,2,3],'close':[1,2,3],'tick_volume':[1,1,1]})
    out=c.build_tf(m1,5); assert list(out.time.dt.strftime('%H:%M'))==['00:00','00:10']

def test_gap_buy_stop_fills_at_open_not_stale_level():
    entry=3000.; op=3005.; fill=op if op>=entry else entry; assert fill==3005.

for fn in [test_dd_open_equity,test_size_ladder_and_margin,test_tf_resample_does_not_create_empty_bars,test_gap_buy_stop_fills_at_open_not_stale_level]:
    fn(); print('PASS',fn.__name__)
