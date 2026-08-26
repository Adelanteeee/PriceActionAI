import importlib.util
from pathlib import Path
import pandas as pd

MODULE_PATH = Path(__file__).resolve().parents[1] / 'price_action_ai_v1_7_5_offline_temporal_gate.py'
spec = importlib.util.spec_from_file_location('pai', MODULE_PATH)
pai = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pai)


def sw(i, kind, price):
    return {'index': i, 'time': pd.Timestamp('2026-01-01') + pd.Timedelta(minutes=i), 'kind': kind, 'price': float(price), 'atr': 1.0, 'prominence_atr': 1.0}


def df(n=30):
    rows=[]
    for i in range(n):
        rows.append({'open':100.0,'high':101.0,'low':99.0,'close':100.5,'time':pd.Timestamp('2026-01-01')+pd.Timedelta(minutes=i)})
    return pd.DataFrame(rows)


def kinds_prices(xs):
    return [(x['kind'], x['price']) for x in xs]


def test_one_bar_countermove_cannot_be_independent_correction():
    swings=[sw(0,'SL',100), sw(6,'SH',160), sw(7,'SL',120), sw(10,'SH',170)]
    out,_=pai.select_major_swings(df(), swings, reference_leg=50)
    assert kinds_prices(out)==[('SL',100.0),('SH',170.0)]


def test_four_bar_countermove_defaults_internal_even_if_large():
    swings=[sw(0,'SL',100), sw(6,'SH',160), sw(10,'SL',120), sw(14,'SH',170)]
    out,_=pai.select_major_swings(df(), swings, reference_leg=50)
    assert kinds_prices(out)==[('SL',100.0),('SH',170.0)]


def test_five_bar_countermove_is_eligible_and_kept_if_reference_accepts():
    swings=[sw(0,'SL',100), sw(6,'SH',160), sw(11,'SL',120), sw(15,'SH',170)]
    out,_=pai.select_major_swings(df(), swings, reference_leg=50)
    assert kinds_prices(out)==[('SL',100.0),('SH',160.0),('SL',120.0),('SH',170.0)]


def test_five_bar_countermove_still_merges_if_reference_rejects():
    swings=[sw(0,'SL',100), sw(6,'SH',160), sw(11,'SL',145), sw(15,'SH',170)]
    out,_=pai.select_major_swings(df(), swings, reference_leg=50)
    assert kinds_prices(out)==[('SL',100.0),('SH',170.0)]
