import os
import sys
import csv
import math
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

def load_xau_live_bars():
    base_dir = os.path.expandvars(r'%LOCALAPPDATA%\BacktestLab\live\XAUUSD')
    bars = []
    
    for fn in ['min-2026-10.csv', 'min-2026-11.csv']:
        fp = os.path.join(base_dir, fn)
        if not os.path.exists(fp):
            continue
        with open(fp, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for r in reader:
                try:
                    dt = datetime.strptime(r['time'], '%Y-%m-%d %H:%M')
                    c = float(r['close'])
                    h = float(r['high'])
                    l = float(r['low'])
                    o = float(r['open'])
                    sp = float(r['spreadAvg'])
                    imb = float(r['imbalance']) if r.get('imbalance') else 0.0
                    vol = float(r.get('tickVolume', 1))
                    bars.append({
                        'dt': dt,
                        'time': r['time'],
                        'date': r['time'].split(' ')[0],
                        'open': o,
                        'high': h,
                        'low': l,
                        'close': c,
                        'spread': sp,
                        'imbalance': imb,
                        'volume': vol
                    })
                except Exception:
                    pass
                    
    # Sort and deduplicate
    bars.sort(key=lambda x: x['dt'])
    unique_bars = []
    seen = set()
    for b in bars:
        if b['time'] not in seen:
            seen.add(b['time'])
            unique_bars.append(b)
            
    # Calculate ATR and Session
    for i in range(len(unique_bars)):
        b = unique_bars[i]
        # ATR 14
        if i == 0:
            b['atr'] = b['high'] - b['low']
        else:
            prev = unique_bars[i-1]
            tr = max(b['high'] - b['low'], abs(b['high'] - prev['close']), abs(b['low'] - prev['close']))
            b['atr'] = (prev['atr'] * 13 + tr) / 14.0
            
        # Session
        hr = b['dt'].hour
        if 0 <= hr < 8:
            b['session'] = 'ASIA'
        elif 8 <= hr < 13:
            b['session'] = 'LONDON'
        elif 13 <= hr < 21:
            b['session'] = 'NY'
        else:
            b['session'] = 'OVERNIGHT'
            
        # News Void Gate (FOMC: Nov 5 18:00-22:00, NFP: Nov 6 12:30-16:00)
        dt_str = b['time']
        is_fomc = ('2026-11-05 18:00' <= dt_str <= '2026-11-05 22:00')
        is_nfp = ('2026-11-06 12:30' <= dt_str <= '2026-11-06 16:00')
        b['is_news_void'] = (is_fomc or is_nfp)
        
    return unique_bars

def simulate(bars, name, entry_fn, sl_mult=2.0, tp_mult=2.5, use_be=True, news_gate=True, session_filter=None):
    trades = []
    in_pos = False
    side = None
    entry_p = 0.0
    sl = 0.0
    tp = 0.0
    entry_i = 0
    be_active = False
    
    for i in range(30, len(bars)):
        b = bars[i]
        
        if in_pos:
            high = b['high']
            low = b['low']
            close = b['close']
            atr = b['atr']
            
            # Breakeven lock
            if use_be and not be_active:
                if side == 'BUY' and high >= entry_p + (1.0 * atr):
                    sl = entry_p + (b['spread'] * 0.5)
                    be_active = True
                elif side == 'SELL' and low <= entry_p - (1.0 * atr):
                    sl = entry_p - (b['spread'] * 0.5)
                    be_active = True
                    
            hit_tp = False
            hit_sl = False
            exit_p = close
            
            if side == 'BUY':
                if high >= tp:
                    hit_tp = True
                    exit_p = tp
                elif low <= sl:
                    hit_sl = True
                    exit_p = sl
            else:
                if low <= tp:
                    hit_tp = True
                    exit_p = tp
                elif high >= sl:
                    hit_sl = True
                    exit_p = sl
                    
            # 60 bar timeout
            if (i - entry_i >= 60) and not hit_tp and not hit_sl:
                exit_p = close
                hit_tp = (side == 'BUY' and exit_p > entry_p) or (side == 'SELL' and exit_p < entry_p)
                hit_sl = not hit_tp
                
            if hit_tp or hit_sl:
                diff = (exit_p - entry_p) if side == 'BUY' else (entry_p - exit_p)
                # Gold: $1 per $1 movement on 1 oz (0.01 lot)
                cost = (b['spread'] * 1.0) + 0.05
                net_pnl = diff - cost
                
                trades.append({
                    'entry_time': bars[entry_i]['time'],
                    'exit_time': b['time'],
                    'side': side,
                    'pnl': net_pnl,
                    'is_win': net_pnl > 0,
                    'date': b['date']
                })
                in_pos = False
                continue
                
        if not in_pos:
            if news_gate and b['is_news_void']:
                continue
            if session_filter and b['session'] != session_filter:
                continue
            if b['spread'] > 0.35: # Spread shield
                continue
                
            sig = entry_fn(bars, i)
            if sig in ['BUY', 'SELL']:
                in_pos = True
                side = sig
                entry_p = b['close']
                entry_i = i
                be_active = False
                atr = b['atr']
                
                if side == 'BUY':
                    sl = entry_p - (sl_mult * atr)
                    tp = entry_p + (tp_mult * atr)
                else:
                    sl = entry_p + (sl_mult * atr)
                    tp = entry_p - (tp_mult * atr)
                    
    if not trades:
        return {'strat': name, 'trades': 0, 'win_rate': 0, 'pf': 0, 'pnl': 0, 'pos_days': 0, 'total_days': 0, 'daily_win_rate': 0}
        
    wins = [t for t in trades if t['pnl'] > 0]
    losses = [t for t in trades if t['pnl'] < 0]
    gw = sum(t['pnl'] for t in wins)
    gl = abs(sum(t['pnl'] for t in losses))
    pf = (gw / gl) if gl > 0 else 999.0
    pnl = sum(t['pnl'] for t in trades)
    wr = len(wins) / len(trades) * 100
    
    daily = {}
    for t in trades:
        d = t['date']
        daily[d] = daily.get(d, 0.0) + t['pnl']
        
    pos_days = sum(1 for p in daily.values() if p > 0)
    total_days = len(daily)
    dwr = (pos_days / total_days * 100) if total_days > 0 else 0
    
    return {
        'strat': name,
        'trades': len(trades),
        'wins': len(wins),
        'losses': len(losses),
        'win_rate': round(wr, 1),
        'pf': round(pf, 2),
        'pnl': round(pnl, 2),
        'daily_win_rate': round(dwr, 1),
        'pos_days': pos_days,
        'total_days': total_days,
        'daily': daily
    }

def main():
    bars = load_xau_live_bars()
    print(f"Loaded {len(bars)} continuous M1 bars of XAUUSD (from {bars[0]['time']} to {bars[-1]['time']})")
    
    # 1. AMT Value Area Fade (Rolling 60 bars 15% - 85% range)
    def entry_amt(bars, i):
        window = bars[max(0, i-60):i]
        lows = sorted([x['low'] for x in window])
        highs = sorted([x['high'] for x in window])
        val = lows[int(len(lows)*0.15)]
        vah = highs[int(len(highs)*0.85)]
        b = bars[i]
        if b['close'] <= val and b['imbalance'] > 0.01:
            return 'BUY'
        elif b['close'] >= vah and b['imbalance'] < -0.01:
            return 'SELL'
        return None
        
    # 2. DOM Wall Absorption
    def entry_dom(bars, i):
        b = bars[i]
        if b['imbalance'] >= 0.04:
            return 'BUY'
        elif b['imbalance'] <= -0.04:
            return 'SELL'
        return None

    # 3. SMC Displacement CHoCH (Breakout + Imbalance confirmation)
    def entry_smc_choch(bars, i):
        b = bars[i]
        prev = bars[i-1]
        body = abs(b['close'] - b['open'])
        if body > 1.0 * b['atr'] and b['close'] > prev['high'] and b['imbalance'] > 0.015:
            return 'BUY'
        elif body > 1.0 * b['atr'] and b['close'] < prev['low'] and b['imbalance'] < -0.015:
            return 'SELL'
        return None

    # 4. Hybrid: AMT + CHoCH Confirmation (The 4 Pillars implementation on XAU)
    def entry_hybrid_4pillars(bars, i):
        window = bars[max(0, i-60):i]
        lows = sorted([x['low'] for x in window])
        highs = sorted([x['high'] for x in window])
        val = lows[int(len(lows)*0.20)]
        vah = highs[int(len(highs)*0.80)]
        b = bars[i]
        prev = bars[i-1]
        
        # At Value Area boundary + CHoCH reversal candle
        if b['close'] <= val and b['close'] > prev['high'] and b['imbalance'] > 0.01:
            return 'BUY'
        elif b['close'] >= vah and b['close'] < prev['low'] and b['imbalance'] < -0.01:
            return 'SELL'
        return None

    tests = [
        ("4-PILLARS HYBRID (AMT + CHoCH + News Gate · London+NY)", entry_hybrid_4pillars, 2.0, 3.0, True, True, None),
        ("4-PILLARS HYBRID (AMT + CHoCH + News Gate · NY Session)", entry_hybrid_4pillars, 2.0, 3.0, True, True, 'NY'),
        ("AMT_VALUE_AREA (London + NY + News Gate)", entry_amt, 2.0, 2.5, True, True, None),
        ("AMT_VALUE_AREA (NY Session + News Gate)", entry_amt, 2.0, 2.5, True, True, 'NY'),
        ("SMC_CHOCH (London + NY + News Gate)", entry_smc_choch, 1.8, 2.8, True, True, None),
        ("SMC_CHOCH (NY Session + News Gate)", entry_smc_choch, 1.8, 2.8, True, True, 'NY'),
        ("DOM_ABSORPTION (London + NY + News Gate)", entry_dom, 2.0, 2.5, True, True, None),
        ("DOM_ABSORPTION (NY Session + News Gate)", entry_dom, 2.0, 2.5, True, True, 'NY'),
        ("NO NEWS GATE: DOM_ABSORPTION (Baseline Raw)", entry_dom, 2.0, 2.5, True, False, None),
    ]
    
    results = []
    for name, fn, sl, tp, be, nv, sess in tests:
        res = simulate(bars, name, fn, sl_mult=sl, tp_mult=tp, use_be=be, news_gate=nv, session_filter=sess)
        results.append(res)
        
    print("\n=== XAUUSD STRATEGY EVALUATION (100% REAL LIVE SCRAPED DATA) ===")
    print(f"{'Strategy':<56} | {'Trades':<6} | {'WinRate':<7} | {'PF':<5} | {'PnL ($)':<8} | {'Daily Win%':<10}")
    print("-" * 105)
    for r in sorted(results, key=lambda x: x['pnl'], reverse=True):
        print(f"{r['strat']:<56} | {r['trades']:<6} | {r['win_rate']:<6.1f}% | {r['pf']:<5.2f} | {r['pnl']:<8.2f} | {r['daily_win_rate']:<6.1f}% ({r['pos_days']}/{r['total_days']})")
        
    # Print day by day for top strategy
    top = max(results, key=lambda x: x['pnl'])
    print(f"\nTop Strategy [{top['strat']}] Daily PnL Breakdown:")
    for d, pnl in sorted(top.get('daily', {}).items()):
        print(f"  {d}: ${pnl:+.2f} USD")

if __name__ == '__main__':
    main()
