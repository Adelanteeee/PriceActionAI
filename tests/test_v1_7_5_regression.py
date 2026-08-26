import importlib.util
import math
from pathlib import Path
import pandas as pd

MODULE_PATH = Path(__file__).resolve().parents[1] / 'price_action_ai_v1_7_5_offline_temporal_gate.py'
spec = importlib.util.spec_from_file_location('pai_v172', MODULE_PATH)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def sw(i,k,p):
    return {'index':i,'time':pd.Timestamp('2026-01-01')+pd.Timedelta(minutes=i*5),'kind':k,'price':float(p),'atr':2.0,'prominence_atr':1.0}


def test_timeframe_aliases():
    assert m.normalize_timeframe('5m') == 'M5'
    assert m.normalize_timeframe('15') == 'M15'
    assert m.normalize_timeframe('30m') == 'M30'
    assert m.normalize_timeframe('1h') == 'H1'


def test_alternation_keeps_more_extreme_same_type():
    xs=[sw(1,'SH',10),sw(2,'SH',12),sw(3,'SL',5),sw(4,'SL',6),sw(5,'SH',13)]
    out=m.enforce_alternation(xs)
    assert [(x['kind'],x['price']) for x in out]==[('SH',12.0),('SL',5.0),('SH',13.0)]


def test_reference_stats_known_values():
    vals=[30,30,30,40,70,120]
    s=m.reference_statistics(vals)
    assert math.isclose(s['mean'],53.3333333333,rel_tol=1e-9)
    assert math.isclose(s['median'],35.0,rel_tol=1e-9)
    assert math.isclose(s['rms'],math.sqrt(sum(v*v for v in vals)/6),rel_tol=1e-9)


def test_rms_snaps_to_actual_leg():
    vals=[30,30,30,40,70,120]
    s=m.reference_statistics(vals)
    ref,_=m.select_nearest_actual_leg(vals,s['rms'])
    assert ref==70.0


def test_snap_tie_prefers_smaller():
    ref,_=m.select_nearest_actual_leg([40,60],50)
    assert ref==40.0


def test_all_preserved_structural_legs_vote_reference():
    xs=[sw(0,'SL',100),sw(2,'SH',140),sw(4,'SL',110),sw(6,'SH',150)]
    tagged,candidates=m.tag_internal_candidates(xs)
    vals=m._leg_thrusts(tagged)
    assert vals==[40.0,30.0,40.0]
    assert len(candidates)==2


def test_major_rejects_small_counter_continuation():
    xs=[sw(0,'SL',100),sw(3,'SH',150),sw(6,'SL',145),sw(9,'SH',175)]
    rows=[]
    for i in range(20):
        o=100+i*0.2; c=o+0.1
        rows.append({'open':o,'high':c+0.5,'low':o-0.5,'close':c})
    df=pd.DataFrame(rows)
    out,removed=m.select_major_swings(df,xs,reference_leg=50)
    assert len(out)==2
    assert out[0]['kind']=='SL' and out[-1]['kind']=='SH' and out[-1]['price']==175.0
    assert len(removed)==2


def test_version_is_v175():
    assert m.VERSION.startswith('1.7.5')

if __name__=='__main__':
    tests=[n for n in globals() if n.startswith('test_')]
    failed=[]
    for n in tests:
        try:
            globals()[n](); print('PASS',n)
        except Exception as e:
            failed.append((n,e)); print('FAIL',n,e)
    if failed:
        raise SystemExit(1)
    print(f'PASS {len(tests)}/{len(tests)}')
