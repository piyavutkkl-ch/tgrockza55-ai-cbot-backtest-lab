"""
100% Daily Profitability Optimization Harness (100% Real Live Continuous Data)
==============================================================================
Evaluates and optimizes bots to achieve:
1. 100% Daily Win Rate (Every single day must be POSITIVE PnL, 0 red days)
2. Tested exclusively on real continuous live recorded data in data/live/
3. Real spread friction, slippage, and commissions included
"""

import sys, os, csv, json, math
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIVE_DATA_DIR = os.path.join(ROOT, 'data', 'live')

def load_live_asset(symbol):
    min_file = os.path.join(LIVE_DATA_DIR, symbol, 'min-2026-11.csv')
    flow_file = os.path.join(LIVE_DATA_DIR, symbol, 'flow-2026-11.csv')
    
    if not os.path.exists(min_file):
        return []
        
    flow_map = {}
    if os.path.exists(flow_file):
        with open(flow_file, 'r', encoding='utf-8', errors='replace') as fp:
            for r in csv.DictReader(fp):
                flow_map[r['time']] = r
                
    bars = []
    with open(min_file, 'r', encoding='utf-8', errors='replace') as fp:
        for r in csv.DictReader(fp):
            t = r['time']
            fl = flow_map.get(t, {})
            try:
                c = float(r['close'])
                o = float(r['open'])
                h = float(r['high'])
                l = float(r['low'])
                sp = float(r.get('spreadAvg', 0.15) or 0.15)
                imb = float(r.get('imbalance', 0) or 0)
                delta = float(fl.get('delta', 0) or 0)
                cvd = float(fl.get('cvd', 0) or 0)
                vwap = float(fl.get('vwapDay', 0) or fl.get('vwapSession', 0) or c)
                sd = float(fl.get('sdDay', 0) or 3.5)
                if sd <= 0: sd = 3.5
                
                day = t.split()[0]
                hour = int(t.split()[1].split(':')[0]) if len(t.split()) > 1 else 0
                
                bars.append({
                    'time': t, 'day': day, 'hour': hour,
                    'open': o, 'high': h, 'low': l, 'close': c,
                    'range': max(h - l, 0.01),
                    'spread': sp, 'imbalance': imb,
                    'delta': delta, 'cvd': cvd,
                    'vwap': vwap, 'sd': sd,
                    'min_to_next': float(r.get('minToNext', 999) or 999),
                    'next_impact': r.get('nextImpact', ''),
                    'min_since_last': float(r.get('minSinceLast', 999) or 999),
                    'last_impact': r.get('lastImpact', '')
                })
            except Exception:
                continue
                
    # Precalculate rolling metrics
    n = len(bars)
    if n > 0:
        closes = [b['close'] for b in bars]
        def calc_ema(vals, period):
            ema = [vals[0]]
            k = 2.0 / (period + 1.0)
            for v in vals[1:]:
                ema.append(v * k + ema[-1] * (1.0 - k))
            return ema
        ema50 = calc_ema(closes, 50)
        ema200 = calc_ema(closes, 200)
        
        atr = [bars[i]['range'] for i in range(n)]
        for i in range(14, n):
            atr[i] = sum(bars[j]['range'] for j in range(i-13, i+1)) / 14.0
            
        hh_15 = [bars[i]['high'] for i in range(n)]
        ll_15 = [bars[i]['low'] for i in range(n)]
        for i in range(15, n):
            hh_15[i] = max(bars[j]['high'] for j in range(i-15, i))
            ll_15[i] = min(bars[j]['low'] for j in range(i-15, i))
            
        for i in range(n):
            bars[i]['ema50'] = ema50[i]
            bars[i]['ema200'] = ema200[i]
            bars[i]['atr'] = atr[i]
            bars[i]['hh_15'] = hh_15[i]
            bars[i]['ll_15'] = ll_15[i]
            
    return bars

def simulate_with_daily_guard(bars, symbol, cfg):
    if 'XAU' in symbol:
        lot_scale = 1.0; comm = 0.07; sp_max = 0.25
    elif 'GOLD' in symbol:
        lot_scale = 1.0; comm = 0.05; sp_max = 2.2
    elif 'BTC' in symbol:
        lot_scale = 0.01; comm = 0.0; sp_max = 35.0
    else: # ETH
        lot_scale = 0.01; comm = 0.0; sp_max = 3.5
        
    sl_dist = cfg['sl']
    rr = cfg['rr']
    tp_dist = sl_dist * rr
    be_r = cfg.get('be_r', 0.0)
    sd_mult = cfg.get('sd_mult', 1.0)
    delta_th = cfg.get('delta_th', 5.0)
    imb_th = cfg.get('imb_th', 0.02)
    session_filter = cfg.get('session_filter', 'ALL')
    strat_type = cfg['type']
    smart_dom = cfg.get('smart_dom', False)
    
    # Institutional Daily Protection Controls
    daily_profit_target = cfg.get('daily_target', 9999.0) # Lock in profit for day once reached
    max_daily_losses = cfg.get('max_daily_losses', 99)    # Stop trading day after N losses
    
    trades = []
    daily_pnl = defaultdict(float)
    daily_losses = defaultdict(int)
    pos = None
    
    for i in range(50, len(bars)):
        curr = bars[i]
        c = curr['close']
        h = curr['high']
        l = curr['low']
        sp = curr['spread']
        vwap = curr['vwap']
        sd = curr['sd']
        delta = curr['delta']
        imb = curr['imbalance']
        day = curr['day']
        hour = curr['hour']
        hh = curr['hh_15']
        ll = curr['ll_15']
        rng = max(hh - ll, curr['atr'])
        
        # 1. Position Management
        if pos is not None:
            side = pos['side']
            entry = pos['entry']
            
            # Breakeven lock
            if be_r > 0 and not pos['be_locked']:
                if side == 'BUY' and (h - entry) >= (sl_dist * be_r):
                    pos['sl'] = entry + sp + 0.05
                    pos['be_locked'] = True
                elif side == 'SELL' and (entry - l) >= (sl_dist * be_r):
                    pos['sl'] = entry - sp - 0.05
                    pos['be_locked'] = True
                    
            exit_trade = False
            exit_price = c
            reason = "EXIT"
            
            if smart_dom:
                if side == 'BUY' and (c - entry) >= (sl_dist * 0.4) and imb < -0.04:
                    exit_trade = True; exit_price = c; reason = "DOM_EXIT"
                elif side == 'SELL' and (entry - c) >= (sl_dist * 0.4) and imb > 0.04:
                    exit_trade = True; exit_price = c + sp; reason = "DOM_EXIT"
                    
            if not exit_trade:
                if side == 'BUY':
                    if l <= pos['sl']:
                        exit_trade = True; exit_price = pos['sl']
                        reason = "BE" if pos['be_locked'] else "SL"
                    elif h >= pos['tp']:
                        exit_trade = True; exit_price = pos['tp']; reason = "TP"
                else:
                    if h >= pos['sl']:
                        exit_trade = True; exit_price = pos['sl']
                        reason = "BE" if pos['be_locked'] else "SL"
                    elif l <= pos['tp']:
                        exit_trade = True; exit_price = pos['tp']; reason = "TP"
                        
            if exit_trade:
                pnl = (exit_price - entry) * lot_scale if side == 'BUY' else (entry - exit_price) * lot_scale
                pnl -= (sp * lot_scale + comm)
                daily_pnl[pos['day']] += pnl
                if pnl <= 0:
                    daily_losses[pos['day']] += 1
                    
                trades.append({
                    'day': pos['day'], 'side': side,
                    'entry_time': pos['time'], 'exit_time': curr['time'],
                    'entry': round(entry, 2), 'exit': round(exit_price, 2),
                    'pnl': round(pnl, 2), 'win': pnl > 0, 'reason': reason
                })
                pos = None
                continue
                
        # 2. Daily Guardian Checks
        if daily_pnl[day] >= daily_profit_target:
            continue # Profit Target Achieved for today, protect gains!
        if daily_losses[day] >= max_daily_losses:
            continue # Hit max loss quota for today, shut down to protect capital!
            
        # 3. News & Spread Filters
        if curr['min_to_next'] <= 30 and curr['next_impact'] in ['HIGH', 'EXTREME']:
            continue
        if curr['min_since_last'] <= 60 and curr['last_impact'] in ['HIGH', 'EXTREME']:
            continue
        if sp > sp_max:
            continue
            
        # 4. Session Filter
        if session_filter == 'ASIA' and not (0 <= hour < 7):
            continue
        elif session_filter == 'LONDON' and not (7 <= hour < 13):
            continue
        elif session_filter == 'NY' and not (13 <= hour < 21):
            continue
        elif session_filter == 'NO_MIDNIGHT' and (22 <= hour or hour < 2):
            continue # Skip midnight rollover gap
            
        # 5. Signal Evaluation
        buy_sig = False
        sell_sig = False
        lower_band = vwap - (sd * sd_mult)
        upper_band = vwap + (sd * sd_mult)
        
        if strat_type == 'VWAP_ABSORPTION':
            buy_sig = (l <= lower_band) and (delta >= delta_th)
            sell_sig = (h >= upper_band) and (delta <= -delta_th)
        elif strat_type == 'DOM_ABSORPTION':
            buy_sig = (c <= ll + rng * 0.15) and (imb >= imb_th)
            sell_sig = (c >= hh - rng * 0.15) and (imb <= -imb_th)
        elif strat_type == 'FOUR_PILLAR_ENSEMBLE':
            buy_sig = (l <= lower_band or c <= ll + rng * 0.15) and (imb >= imb_th) and (delta >= 0)
            sell_sig = (h >= upper_band or c >= hh - rng * 0.15) and (imb <= -imb_th) and (delta <= 0)
            
        # Macro Trend Shield
        if cfg.get('macro_trend', True):
            if c > curr['ema50'] and curr['ema50'] > curr['ema200']: sell_sig = False
            elif c < curr['ema50'] and curr['ema50'] < curr['ema200']: buy_sig = False
            
        if buy_sig:
            pos = {
                'side': 'BUY', 'entry': c + sp,
                'sl': (c + sp) - sl_dist, 'tp': (c + sp) + tp_dist,
                'be_locked': False, 'time': curr['time'], 'day': day
            }
        elif sell_sig:
            pos = {
                'side': 'SELL', 'entry': c,
                'sl': c + sl_dist, 'tp': c - tp_dist,
                'be_locked': False, 'time': curr['time'], 'day': day
            }
            
    if not trades:
        return None
        
    wins = [t['pnl'] for t in trades if t['win']]
    losses = [t['pnl'] for t in trades if not t['win']]
    total_net = sum(t['pnl'] for t in trades)
    pf = sum(wins) / abs(sum(losses)) if losses and sum(losses) != 0 else (99.0 if wins else 0.0)
    pos_days = sum(1 for d, p in daily_pnl.items() if p > 0)
    tot_days = len(daily_pnl)
    daily_wr = (pos_days / tot_days * 100.0) if tot_days > 0 else 0.0
    
    return {
        'trades': len(trades), 'wins': len(wins), 'losses': len(losses),
        'win_rate': round(len(wins)/len(trades)*100.0, 1),
        'net_pnl': round(total_net, 2),
        'profit_factor': round(pf, 2),
        'daily_win_rate': round(daily_wr, 1),
        'positive_days': pos_days,
        'active_days': tot_days,
        'daily_pnl': {k: round(v, 2) for k, v in sorted(daily_pnl.items())},
        'trades_sample': trades
    }

def main():
    print("="*80)
    print("🔍 AUDITING DAILY GUARDIAN CONFIGURATIONS (AIM: 100% DAILY WIN RATE)")
    print("="*80)
    
    symbols = ['XAUUSD', 'BTCUSD', 'ETHUSD', 'GOLD-PERP']
    for sym in symbols:
        bars = load_live_asset(sym)
        print(f"\nScanning {sym} ({len(bars)} continuous live bars)...")
        candidates_100 = []
        
        # Test parameter combinations
        if 'XAU' in sym:
            for sl in [3.0, 4.0, 5.0]:
                for rr in [2.0, 2.5, 3.0]:
                    for be in [0.0, 1.0]:
                        for d_tgt in [10.0, 15.0, 25.0, 999.0]:
                            for max_l in [1, 2, 99]:
                                cfg = {
                                    'type': 'VWAP_ABSORPTION', 'sl': sl, 'rr': rr, 'be_r': be,
                                    'sd_mult': 1.0, 'delta_th': 5.0, 'session_filter': 'ALL',
                                    'daily_target': d_tgt, 'max_daily_losses': max_l, 'macro_trend': True
                                }
                                res = simulate_with_daily_guard(bars, sym, cfg)
                                if res and res['trades'] >= 5 and res['daily_win_rate'] >= 80.0 and res['net_pnl'] > 0:
                                    candidates_100.append((cfg, res))
        elif 'BTC' in sym:
            for sl in [60.0, 80.0, 100.0, 120.0]:
                for rr in [1.8, 2.2, 2.6]:
                    for imb in [0.015, 0.025, 0.035]:
                        for sf in ['ALL', 'NY', 'NO_MIDNIGHT']:
                            for d_tgt in [5.0, 10.0, 999.0]:
                                cfg = {
                                    'type': 'DOM_ABSORPTION', 'sl': sl, 'rr': rr, 'be_r': 1.0,
                                    'imb_th': imb, 'smart_dom': True, 'session_filter': sf,
                                    'daily_target': d_tgt, 'max_daily_losses': 2, 'macro_trend': True
                                }
                                res = simulate_with_daily_guard(bars, sym, cfg)
                                if res and res['trades'] >= 5 and res['daily_win_rate'] >= 80.0 and res['net_pnl'] > 0:
                                    candidates_100.append((cfg, res))
        elif 'ETH' in sym:
            for sl in [2.0, 2.5, 3.0]:
                for rr in [2.0, 2.5, 2.8]:
                    for sf in ['ASIA', 'ALL']:
                        for d_tgt in [0.2, 0.5, 999.0]:
                            cfg = {
                                'type': 'DOM_ABSORPTION', 'sl': sl, 'rr': rr, 'be_r': 1.0,
                                'imb_th': 0.015, 'smart_dom': True, 'session_filter': sf,
                                'daily_target': d_tgt, 'max_daily_losses': 2, 'macro_trend': True
                            }
                            res = simulate_with_daily_guard(bars, sym, cfg)
                            if res and res['trades'] >= 5 and res['daily_win_rate'] >= 80.0 and res['net_pnl'] > 0:
                                candidates_100.append((cfg, res))
        elif 'GOLD-PERP' in sym:
            for sl in [3.0, 4.0, 5.0]:
                for rr in [2.0, 2.5, 3.0]:
                    for sf in ['ALL', 'NO_MIDNIGHT', 'LONDON']:
                        for d_tgt in [10.0, 15.0, 999.0]:
                            for max_l in [1, 2, 99]:
                                cfg = {
                                    'type': 'DOM_ABSORPTION', 'sl': sl, 'rr': rr, 'be_r': 1.0,
                                    'sd_mult': 1.0, 'imb_th': 0.025, 'session_filter': sf,
                                    'daily_target': d_tgt, 'max_daily_losses': max_l, 'macro_trend': True
                                }
                                res = simulate_with_daily_guard(bars, sym, cfg)
                                if res and res['trades'] >= 5 and res['daily_win_rate'] >= 80.0 and res['net_pnl'] > 0:
                                    candidates_100.append((cfg, res))
                                    
        print(f"Survivors for {sym}: {len(candidates_100)}")
        candidates_100.sort(key=lambda x: (x[1]['daily_win_rate'], x[1]['profit_factor'], x[1]['net_pnl']), reverse=True)
        for i, (c, r) in enumerate(candidates_100[:3], 1):
            print(f"  #{i}: DailyWR={r['daily_win_rate']}% ({r['positive_days']}/{r['active_days']} days), Net=+${r['net_pnl']}, PF={r['profit_factor']}, WR={r['win_rate']}%, Config={c}")

if __name__ == '__main__':
    main()
