import math
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import pandas as pd
import numpy as np
import corrected_v63_runner as r


def _market(rows):
    return pd.DataFrame(rows, columns=['time','bid_open','bid_high','bid_low','bid_close','ask_open','ask_high','ask_low','ask_close'])


def test_news_csv_is_shifted_from_server_utc_plus_3_to_utc():
    # 2025-01-10 NFP is 13:30 UTC; source CSV stores 16:30 broker-server time.
    assert np.datetime64('2025-01-10T13:30:00') in r.NEWS


def test_litefinance_xauusd_contract_and_margin_are_locked():
    assert r.CONTRACT_SIZE == 100.0
    assert r.MIN_LOT == 0.01
    assert r.LOT_STEP == 0.01
    assert r.MARGIN_RATE == 0.002
    assert r.ECN_COMMISSION_PER_LOT == 5.0


def test_long_pending_market_passed_uses_ask_not_bid():
    m=_market([
        [pd.Timestamp('2025-01-02 10:00'),100,100.2,99.8,100,101,101.2,100.8,101],
        [pd.Timestamp('2025-01-02 10:01'),100,100.2,99.8,100,101,101.2,100.8,101],
    ])
    cand={'dir':'LONG','entry':100.5,'sl':90.5,'tp':113.8,'ztime':pd.Timestamp('2024-12-30'),'signal_time':pd.Timestamp('2025-01-02 09:59')}
    ev={pd.Timestamp('2025-01-02 10:00'):(cand,None)}
    out=r.simulate(m,ev,1,1000,10)
    assert out['closed']==0
    assert out['ending_balance']==1000


def test_equity_drawdown_records_open_trade_adverse_excursion():
    m=_market([
        [pd.Timestamp('2025-01-02 10:00'),100,101,99.8,100.5,100.1,101.1,99.9,100.6],
        [pd.Timestamp('2025-01-02 10:01'),100.5,101,95,100.8,100.6,101.1,95.1,100.9],
        [pd.Timestamp('2025-01-02 10:02'),100.8,101.5,100.5,101.2,100.9,101.6,100.6,101.3],
    ])
    cand={'dir':'LONG','entry':100.9,'sl':80.9,'tp':127.5,'ztime':pd.Timestamp('2024-12-30'),'signal_time':pd.Timestamp('2025-01-02 09:59')}
    ev={pd.Timestamp('2025-01-02 10:00'):(cand,None)}
    out=r.simulate(m,ev,1,1000,10)
    assert out['closed']==1
    assert out['max_equity_drawdown_pct']>0.1


def test_size_order_uses_1_to_500_margin_not_old_1_to_100_proxy():
    cand={'entry':2500.0,'sl':2495.0}
    lot,loss,target,margin=r.size_order(cand,200.0,200.0,0)
    assert lot==0.01
    assert math.isclose(loss,5.0,abs_tol=1e-9)
    assert math.isclose(margin,5.0,abs_tol=1e-9)


def test_short_pending_market_passed_uses_bid_not_ask():
    m=_market([
        [pd.Timestamp('2025-01-02 10:00'),100,100.2,99.8,100,101,101.2,100.8,101],
        [pd.Timestamp('2025-01-02 10:01'),100,100.2,99.8,100,101,101.2,100.8,101],
    ])
    cand={'dir':'SHORT','entry':100.5,'sl':110.5,'tp':87.2,'ztime':pd.Timestamp('2024-12-30'),'signal_time':pd.Timestamp('2025-01-02 09:59')}
    ev={pd.Timestamp('2025-01-02 10:00'):(cand,None)}
    out=r.simulate(m,ev,1,1000,10)
    assert out['closed']==0
    assert out['ending_balance']==1000


def test_short_stop_is_checked_on_ask_side():
    m=_market([
        [pd.Timestamp('2025-01-02 10:00'),101.0,101.2,100.4,100.8,101.2,101.4,100.6,101.0],
        [pd.Timestamp('2025-01-02 10:01'),101.0,101.3,100.8,101.0,101.2,101.6,101.0,101.2],
    ])
    cand={'dir':'SHORT','entry':100.5,'sl':101.5,'tp':99.17,'ztime':pd.Timestamp('2024-12-30'),'signal_time':pd.Timestamp('2025-01-02 09:59')}
    ev={pd.Timestamp('2025-01-02 10:00'):(cand,None)}
    out=r.simulate(m,ev,1,1000,10)
    # 0.30 lot * $1.00 * 100 oz = $30 stop loss, plus $1.50 ECN commission.
    assert out['closed']==1
    assert math.isclose(out['ending_balance'],968.5,abs_tol=1e-9)

if __name__=='__main__':
    tests=[v for k,v in sorted(globals().items()) if k.startswith('test_')]
    for f in tests:
        f(); print('PASS', f.__name__)
    print(f'{len(tests)}/{len(tests)} PASS')
