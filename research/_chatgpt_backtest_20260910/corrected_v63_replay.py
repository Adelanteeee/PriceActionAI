from __future__ import annotations
import json, math, os
import numpy as np
import pandas as pd
import annual_v63_runner as base

MT5_M1_URL = 'https://raw.githubusercontent.com/simom1/XAUUSD-history/main/Gold-Cash/XAUUSD/XAUUSD_M1_2023_2026.csv'
CONTRACT_SIZE = 100.0
VOL_MIN = 0.01
VOL_MAX = 100.0
VOL_STEP = 0.01
MARGIN_PERCENT = 0.2
MAX_MARGIN_LOAD_PCT = 50.0
COMMISSION_PER_LOT = 5.0
START=base.START; END=base.END; WARM=base.WARM
VERSIONS=base.VERSIONS
TFS=base.TFS

def load_market_m1():
    df = pd.read_csv(MT5_M1_URL)
    df.columns = [str(c).strip().lower() for c in df.columns]
    required = {'time','open','high','low','close','tick_volume'}
    miss = required - set(df.columns)
    if miss:
        raise RuntimeError(f'MT5 source missing columns: {sorted(miss)}')
    df['time'] = pd.to_datetime(df['time'], errors='coerce', utc=True).dt.tz_localize(None)
    for c in ['open','high','low','close','tick_volume']:
        df[c] = pd.to_numeric(df[c], errors='coerce')
    df = df.dropna(subset=['time','open','high','low','close','tick_volume'])
    df = df[(df.time>=WARM)&(df.time<END)].copy()
    df = df[df.tick_volume>0].sort_values('time').drop_duplicates('time').reset_index(drop=True)
    if df.empty:
        raise RuntimeError('No MT5 M1 market bars after filtering')
    calendar = int((END-WARM).total_seconds()//60)
    if len(df) >= calendar*0.90:
        raise RuntimeError(f'M1 source still looks calendar-filled: rows={len(df)} calendar={calendar}')
    flat = (df.open.eq(df.high)&df.high.eq(df.low)&df.low.eq(df.close))
    print('DATA_SANITY', json.dumps({
        'rows': int(len(df)), 'calendar_minutes': calendar,
        'coverage_ratio': float(len(df)/calendar),
        'flat_rows': int(flat.sum()), 'flat_ratio': float(flat.mean()),
        'min_time': str(df.time.iloc[0]), 'max_time': str(df.time.iloc[-1]),
        'min_tick_volume': float(df.tick_volume.min())
    }), flush=True)
    return df

def build_tf(m1, mins):
    if mins == 1:
        return m1[['time','open','high','low','close','tick_volume']].copy()
    x=m1.set_index('time')
    out=x.resample(f'{mins}min', label='left', closed='left').agg(
        open=('open','first'), high=('high','max'), low=('low','min'), close=('close','last'), tick_volume=('tick_volume','sum')
    ).dropna(subset=['open','high','low','close']).reset_index()
    return out

def size_order(cand, balance, initial, level):
    entry=float(cand['entry']); sl=float(cand['sl']); dist=abs(entry-sl)
    if dist<=0: return None
    target=initial*0.03*(1.33**level)
    one_lot_risk=dist*CONTRACT_SIZE
    raw=target/one_lot_risk
    lot=math.floor(raw/VOL_STEP+1e-10)*VOL_STEP
    if lot<VOL_MIN: return None
    lot=min(lot,VOL_MAX)
    loss=lot*one_lot_risk
    tolerance=max(0.01,target*0.001)
    if loss>target+tolerance: return None
    required_margin=lot*CONTRACT_SIZE*entry*(MARGIN_PERCENT/100.0)
    equity=balance; free_margin=equity
    if required_margin>free_margin: return None
    load=100.0*required_margin/equity if equity>0 else 1e100
    if MAX_MARGIN_LOAD_PCT>0 and load>MAX_MARGIN_LOAD_PCT: return None
    equity_after_sl=equity-loss
    if equity_after_sl<=0: return None
    load_after=100.0*required_margin/equity_after_sl
    if MAX_MARGIN_LOAD_PCT>0 and load_after>MAX_MARGIN_LOAD_PCT: return None
    return lot,loss,target,required_margin

class DDTracker:
    def __init__(self, initial):
        self.peak=float(initial); self.max_dd=0.0
    def observe(self, equity):
        eq=float(equity)
        if eq>self.peak: self.peak=eq
        if self.peak>0: self.max_dd=max(self.max_dd,(self.peak-eq)/self.peak)
    @property
    def pct(self): return self.max_dd*100.0

def _pnl(direction, entry, price, lot):
    return ((price-entry) if direction=='LONG' else (entry-price))*lot*CONTRACT_SIZE

def simulate(m1, tf_df, events, tfmin, initial, lead=10):
    times=m1.time.to_numpy(); O=m1.open.to_numpy(float); H=m1.high.to_numpy(float); L=m1.low.to_numpy(float); C=m1.close.to_numpy(float)
    tf_opens=set(pd.Timestamp(x) for x in tf_df.time[(tf_df.time>=START)&(tf_df.time<END)].to_numpy())
    bal=float(initial); level=0; used={'LONG':None,'SHORT':None}; pending=None; pos=None
    dd=DDTracker(initial); closed=0; commissions=0.0
    def observe_close(close_price):
        if pos: dd.observe(bal + _pnl(pos['dir'],pos['entry'],close_price,pos['lot']))
        else: dd.observe(bal)
    def close_pos(price, protective=False, normalwin=False):
        nonlocal bal,level,pos,closed
        p=pos; pnl=_pnl(p['dir'],p['entry'],price,p['lot']); bal+=pnl
        if protective:
            if pnl<0 and level>0: level-=1
        elif normalwin and pnl>0: level+=1
        else:
            if pnl<0 and level>0: level-=1
        pos=None; closed+=1; dd.observe(bal)
    def open_position(p, fill, t):
        nonlocal bal,pos,commissions
        commission=COMMISSION_PER_LOT*p['lot']; bal-=commission; commissions+=commission; dd.observe(bal)
        pos={**p,'entry':fill,'riskdist':abs(fill-p['sl']),'best':fill,'entry_tf_open':p['start'],'bars':0,'launched':False}
    for idx,tv in enumerate(times):
        t=pd.Timestamp(tv)
        if t<START: continue
        if t>=END: break
        op=float(O[idx]); hi=float(H[idx]); lo=float(L[idx]); cl=float(C[idx])
        if pos:
            p=pos
            if p['dir']=='LONG':
                if op<=p['sl']: close_pos(op)
                elif op>=p['tp']: close_pos(op,normalwin=True)
            else:
                if op>=p['sl']: close_pos(op)
                elif op<=p['tp']: close_pos(op,normalwin=True)
        if pending and not pos:
            p=pending; hit_open=(op>=p['entry']) if p['dir']=='LONG' else (op<=p['entry'])
            if hit_open: open_position(p,op,t); pending=None
        if pos:
            if pos['dir']=='LONG': pos['best']=max(pos['best'],op)
            else: pos['best']=min(pos['best'],op)
            mfe=(pos['best']-pos['entry'] if pos['dir']=='LONG' else pos['entry']-pos['best'])/max(pos['riskdist'],1e-12)
            if mfe>=.33: pos['launched']=True
            if base.next_news_close_due(t,lead): close_pos(op,protective=True)
        blocked=base.news_blocked(t)
        if pending and (blocked or t>=pending['expiry']): pending=None
        if pos and (not pos['launched']) and t in tf_opens and t>pos['entry_tf_open']+pd.Timedelta(minutes=tfmin):
            pos['bars']+=1
            closeR=(op-pos['entry'] if pos['dir']=='LONG' else pos['entry']-op)/pos['riskdist']
            mfeR=(pos['best']-pos['entry'] if pos['dir']=='LONG' else pos['entry']-pos['best'])/pos['riskdist']
            exitnow=(pos['bars']==1 and closeR<=-.15) or (pos['bars']==2 and mfeR<.25 and closeR<=0) or (pos['bars']>=3 and mfeR<.33)
            if exitnow: close_pos(op,protective=True)
            elif pos and pos['bars']>=3: pos['launched']=True
        if pos:
            p=pos
            if p['dir']=='LONG': p['best']=max(p['best'],hi); stop=lo<=p['sl']; tp=hi>=p['tp']
            else: p['best']=min(p['best'],lo); stop=hi>=p['sl']; tp=lo<=p['tp']
            mfe=(p['best']-p['entry'] if p['dir']=='LONG' else p['entry']-p['best'])/p['riskdist']
            if mfe>=.33: p['launched']=True
            if stop: close_pos(p['sl'])
            elif tp: close_pos(p['tp'],normalwin=True)
        if pending and not pos:
            p=pending; hit=(hi>=p['entry']) if p['dir']=='LONG' else (lo<=p['entry'])
            if hit:
                open_position(p,p['entry'],t); pending=None
                if pos['dir']=='LONG': pos['best']=max(pos['best'],hi); stop=lo<=pos['sl']; tp=hi>=pos['tp']
                else: pos['best']=min(pos['best'],lo); stop=hi>=pos['sl']; tp=lo<=pos['tp']
                mfe=(pos['best']-pos['entry'] if pos['dir']=='LONG' else pos['entry']-pos['best'])/pos['riskdist']
                if mfe>=.33: pos['launched']=True
                if stop: close_pos(pos['sl'])
                elif tp: close_pos(pos['tp'],normalwin=True)
        if (not pos) and (not pending) and t in events and not blocked:
            cont,counter=events[t]; cand=None
            if cont and used[cont['dir']]!=cont['ztime']: cand=cont
            elif counter and used[counter['dir']]!=counter['ztime']: cand=counter
            if cand:
                if not ((cand['dir']=='LONG' and op>=cand['entry']) or (cand['dir']=='SHORT' and op<=cand['entry'])):
                    sz=size_order(cand,bal,initial,level)
                    if sz:
                        lot,loss,target,margin=sz; pending={**cand,'lot':lot,'expiry':t+pd.Timedelta(minutes=tfmin),'start':t}; used[cand['dir']]=cand['ztime']
                        hit=(hi>=pending['entry']) if pending['dir']=='LONG' else (lo<=pending['entry'])
                        if hit:
                            p=pending; open_position(p,p['entry'],t); pending=None
                            if pos['dir']=='LONG': pos['best']=max(pos['best'],hi); stop=lo<=pos['sl']; tp=hi>=pos['tp']
                            else: pos['best']=min(pos['best'],lo); stop=hi>=pos['sl']; tp=lo<=pos['tp']
                            mfe=(pos['best']-pos['entry'] if pos['dir']=='LONG' else pos['entry']-pos['best'])/pos['riskdist']
                            if mfe>=.33: pos['launched']=True
                            if stop: close_pos(pos['sl'])
                            elif tp: close_pos(pos['tp'],normalwin=True)
        observe_close(cl)
    if pos:
        last_i=np.searchsorted(times,np.datetime64(END))-1; close_pos(float(C[last_i]),protective=True)
    return {'ending_balance':bal,'max_equity_drawdown_pct':dd.pct,'closed':closed,'commission_paid':commissions}

def run(tf):
    mins=TFS[tf]; m1=load_market_m1(); tf_df=build_tf(m1,mins)
    print('TF_SANITY',tf,len(tf_df),tf_df.time.iloc[0],tf_df.time.iloc[-1],flush=True)
    ev=base.precompute(tf_df,mins,m1)
    result={'period':[str(START),str(END)],'tf':tf,'source':'simom1 MT5 M1 actual bars','margin_percent':MARGIN_PERCENT,'commission_per_lot':COMMISSION_PER_LOT,'results':{}}
    for v in VERSIONS:
        result['results'][v]={}
        for initial in (1000.0,200.0):
            result['results'][v][str(int(initial))]={}
            for lead in (10,60):
                r=simulate(m1,tf_df,ev[v],mins,initial,lead); result['results'][v][str(int(initial))][str(lead)]=r
                print('RES',tf,v,initial,'lead',lead,r,flush=True)
    out=f'corrected_result_{tf}.json'
    with open(out,'w') as f: json.dump(result,f,indent=2)
    print('FINAL_JSON='+json.dumps(result,separators=(',',':')),flush=True)

if __name__=='__main__':
    tf=os.environ.get('TF','M1')
    if tf not in TFS: raise SystemExit(f'bad TF {tf}')
    run(tf)
