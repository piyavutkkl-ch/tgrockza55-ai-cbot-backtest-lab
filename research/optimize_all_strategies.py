"""
Comprehensive Multi-Market Quant Optimization Engine
-----------------------------------------------------
Optimizes 4 Core Strategies across BTCUSD, ETHUSD, and GOLD-PERP:
1. DOM_ABSORPTION (Level 2 Wall Reversal at Extremes)
2. MID_RANGE_VWAP_SCALP (Mean Reversion in Idle Zones)
3. NY_VALUE (Value Area Auction Theory: Breakout & Fade)
4. CVD_DELTA_DIVERGENCE (Order Flow & Cumulative Delta Exhaustion)

Evaluates on collected continuous live datasets (minute + flow).
Includes robust execution logic (no same-bar re-entry, realistic broker spreads & commissions).
"""

import os
import glob
import csv
import math
import json
from collections import defaultdict

BASE_DIR = os.path.expandvars(r'%LOCALAPPDATA%\BacktestLab\live')

def load_market_data(symbol):
    min_files = sorted(glob.glob(os.path.join(BASE_DIR, symbol, 'min-*.csv')))
    flow_files = sorted(glob.glob(os.path.join(BASE_DIR, symbol, 'flow-*.csv')))
    
    min_rows = []
    for mf in min_files:
        with open(mf, 'r', encoding='utf-8') as f:
            min_rows.extend(list(csv.DictReader(f)))
            
    flow_map = {}
    for ff in flow_files:
        with open(ff, 'r', encoding='utf-8') as f:
            for r in csv.DictReader(f):
                flow_map[r['time']] = r
                
    unique_min = {}
    for r in min_rows:
        unique_min[r['time']] = r
        
    sorted_times = sorted(unique_min.keys())
    clean_min = [unique_min[t] for t in sorted_times]
    
    data = []
    for r in clean_min:
        t = r['time']
        fl = flow_map.get(t, {})
        try:
            o = float(r['open'])
            h = float(r['high'])
            l = float(r['low'])
            c = float(r['close'])
            spread = float(r.get('spreadAvg', 0) or r.get('spread', 0) or 0)
            imb = float(r.get('imbalance', 0) or 0)
            ticks = float(r.get('ticks', 0) or 0)
            
            delta = float(fl.get('delta', 0) or 0)
            cvd = float(fl.get('cvd', 0) or 0)
            vwap = float(fl.get('vwapDay', 0) or 0)
            sd = float(fl.get('sdDay', 0) or 0)
            vah = float(fl.get('vah', 0) or 0)
            val = float(fl.get('val', 0) or 0)
            poc = float(fl.get('poc', 0) or 0)
            prev_vah = float(fl.get('prevVah', 0) or 0)
            prev_val = float(fl.get('prevVal', 0) or 0)
            prev_poc = float(fl.get('prevPoc', 0) or 0)
            
            data.append({
                'time': t, 'open': o, 'high': h, 'low': l, 'close': c,
                'spread': spread, 'imbalance': imb, 'ticks': ticks,
                'delta': delta, 'cvd': cvd, 'vwap': vwap, 'sd': sd,
                'vah': vah, 'val': val, 'poc': poc,
                'prev_vah': prev_vah, 'prev_val': prev_val, 'prev_poc': prev_poc
            })
        except (ValueError, TypeError):
            continue
            
    return data

def calc_metrics(trades, point_val=0.01, spread_cost=0.15, comm_per_trade=0.0):
    if not trades:
        return {
            'trades': 0, 'win_rate': 0.0, 'net_pnl': 0.0,
            'profit_factor': 0.0, 'max_dd': 0.0, 'avg_trade': 0.0,
            'wins': 0, 'losses': 0
        }
        
    wins = []
    losses = []
    equity = 0.0
    peak = 0.0
    max_dd = 0.0
    
    for tr in trades:
        pts = tr['exit_p'] - tr['entry_p'] if tr['side'] == 'Buy' else tr['entry_p'] - tr['exit_p']
        gross = pts * point_val
        sp = tr.get('spread_cost', spread_cost)
        net = gross - sp - comm_per_trade
        
        equity += net
        if equity > peak:
            peak = equity
        dd = peak - equity
        if dd > max_dd:
            max_dd = dd
            
        if net > 0:
            wins.append(net)
        else:
            losses.append(abs(net))
            
    tot_win = sum(wins)
    tot_loss = sum(losses)
    pf = (tot_win / tot_loss) if tot_loss > 0 else (99.0 if tot_win > 0 else 0.0)
    wr = (len(wins) / len(trades) * 100.0) if trades else 0.0
    net_pnl = tot_win - tot_loss
    avg_trade = net_pnl / len(trades) if trades else 0.0
    
    return {
        'trades': len(trades),
        'wins': len(wins),
        'losses': len(losses),
        'win_rate': round(wr, 1),
        'net_pnl': round(net_pnl, 2),
        'profit_factor': round(pf, 2),
        'max_dd': round(max_dd, 2),
        'avg_trade': round(avg_trade, 3)
    }

# ==========================================
# 1. DOM_ABSORPTION STRATEGY
# ==========================================
def sim_dom_absorption(data, lookback, imb_thresh, tp_dist, sl_dist, max_hold=60, point_val=0.01, spread_cost=0.15, comm=0.0):
    trades = []
    pos = None
    
    for i in range(lookback, len(data)):
        d = data[i]
        c = d['close']
        h = d['high']
        l = d['low']
        
        if pos is not None:
            side = pos['side']
            exit_p = None
            reason = None
            
            if side == 'Buy':
                if h >= pos['tp']: exit_p = pos['tp']; reason = 'TP'
                elif l <= pos['sl']: exit_p = pos['sl']; reason = 'SL'
            else:
                if l <= pos['tp']: exit_p = pos['tp']; reason = 'TP'
                elif h >= pos['sl']: exit_p = pos['sl']; reason = 'SL'
                
            if exit_p is None and (i - pos['idx']) >= max_hold:
                exit_p = c
                reason = 'TIME'
                
            if exit_p is not None:
                trades.append({
                    'side': side, 'entry_p': pos['entry_p'], 'exit_p': exit_p,
                    'reason': reason, 'spread_cost': spread_cost
                })
                pos = None
                continue  # Advance to next bar before re-evaluating
                
        if pos is None:
            window = data[i-lookback:i]
            w_high = max(x['high'] for x in window)
            w_low = min(x['low'] for x in window)
            w_range = w_high - w_low
            if w_range <= 0: continue
            
            imb = d['imbalance']
            
            if c >= w_high - (w_range * 0.15) and imb <= -imb_thresh:
                pos = {'side': 'Sell', 'entry_p': c, 'tp': c - tp_dist, 'sl': c + sl_dist, 'idx': i}
            elif c <= w_low + (w_range * 0.15) and imb >= imb_thresh:
                pos = {'side': 'Buy', 'entry_p': c, 'tp': c + tp_dist, 'sl': c - sl_dist, 'idx': i}
                
    return calc_metrics(trades, point_val=point_val, spread_cost=spread_cost, comm_per_trade=comm)

# ==========================================
# 2. MID_RANGE_VWAP_SCALP STRATEGY
# ==========================================
def sim_vwap_scalp(data, dev_thresh, tp_dist, sl_dist, max_hold=25, point_val=0.01, spread_cost=0.15, comm=0.0, lookback=15):
    trades = []
    pos = None
    
    for i in range(lookback, len(data)):
        d = data[i]
        c = d['close']
        h = d['high']
        l = d['low']
        vwap = d['vwap']
        if vwap <= 0: continue
        
        if pos is not None:
            side = pos['side']
            exit_p = None
            reason = None
            
            if side == 'Buy':
                if h >= pos['tp']: exit_p = pos['tp']; reason = 'TP'
                elif l <= pos['sl']: exit_p = pos['sl']; reason = 'SL'
            else:
                if l <= pos['tp']: exit_p = pos['tp']; reason = 'TP'
                elif h >= pos['sl']: exit_p = pos['sl']; reason = 'SL'
                
            if exit_p is None and (i - pos['idx']) >= max_hold:
                exit_p = c
                reason = 'TIME'
                
            if exit_p is not None:
                trades.append({
                    'side': side, 'entry_p': pos['entry_p'], 'exit_p': exit_p,
                    'reason': reason, 'spread_cost': spread_cost
                })
                pos = None
                continue  # Advance to next bar
                
        if pos is None:
            window = data[i-lookback:i]
            w_high = max(x['high'] for x in window)
            w_low = min(x['low'] for x in window)
            w_range = w_high - w_low
            
            # Mid-range exclusion: price must NOT be in outer 12% band
            if w_range > 0:
                edge_buf = w_range * 0.12
                if c >= (w_high - edge_buf) or c <= (w_low + edge_buf):
                    continue
                    
            dev = c - vwap
            if dev >= dev_thresh:
                # Price stretched up -> Sell back towards VWAP
                pos = {'side': 'Sell', 'entry_p': c, 'tp': c - tp_dist, 'sl': c + sl_dist, 'idx': i}
            elif dev <= -dev_thresh:
                # Price stretched down -> Buy back towards VWAP
                pos = {'side': 'Buy', 'entry_p': c, 'tp': c + tp_dist, 'sl': c - sl_dist, 'idx': i}
                
    return calc_metrics(trades, point_val=point_val, spread_cost=spread_cost, comm_per_trade=comm)

# ==========================================
# 3. NY_VALUE (VALUE AREA AUCTION) STRATEGY
# ==========================================
def sim_ny_value(data, mode, buffer_dist, tp_dist, sl_dist, max_hold=45, point_val=0.01, spread_cost=0.15, comm=0.0):
    trades = []
    pos = None
    
    for i in range(10, len(data)):
        d = data[i]
        c = d['close']
        h = d['high']
        l = d['low']
        vah = d['vah'] if d['vah'] > 0 else d['prev_vah']
        val = d['val'] if d['val'] > 0 else d['prev_val']
        poc = d['poc'] if d['poc'] > 0 else d['prev_poc']
        
        if vah <= 0 or val <= 0: continue
        
        if pos is not None:
            side = pos['side']
            exit_p = None
            reason = None
            
            if side == 'Buy':
                if h >= pos['tp']: exit_p = pos['tp']; reason = 'TP'
                elif l <= pos['sl']: exit_p = pos['sl']; reason = 'SL'
            else:
                if l <= pos['tp']: exit_p = pos['tp']; reason = 'TP'
                elif h >= pos['sl']: exit_p = pos['sl']; reason = 'SL'
                
            if exit_p is None and (i - pos['idx']) >= max_hold:
                exit_p = c
                reason = 'TIME'
                
            if exit_p is not None:
                trades.append({
                    'side': side, 'entry_p': pos['entry_p'], 'exit_p': exit_p,
                    'reason': reason, 'spread_cost': spread_cost
                })
                pos = None
                continue
                
        if pos is None:
            if mode == 'BREAKOUT':
                # Above VAH -> Ride continuation
                if c >= vah + buffer_dist:
                    pos = {'side': 'Buy', 'entry_p': c, 'tp': c + tp_dist, 'sl': c - sl_dist, 'idx': i}
                # Below VAL -> Ride continuation
                elif c <= val - buffer_dist:
                    pos = {'side': 'Sell', 'entry_p': c, 'tp': c - tp_dist, 'sl': c + sl_dist, 'idx': i}
            elif mode == 'FADE':
                # At VAH -> Fade back to POC
                if c >= vah - buffer_dist and c <= vah + buffer_dist:
                    pos = {'side': 'Sell', 'entry_p': c, 'tp': c - tp_dist, 'sl': c + sl_dist, 'idx': i}
                # At VAL -> Fade back to POC
                elif c <= val + buffer_dist and c >= val - buffer_dist:
                    pos = {'side': 'Buy', 'entry_p': c, 'tp': c + tp_dist, 'sl': c - sl_dist, 'idx': i}
                    
    return calc_metrics(trades, point_val=point_val, spread_cost=spread_cost, comm_per_trade=comm)

# ==========================================
# 4. CVD_DELTA_DIVERGENCE STRATEGY
# ==========================================
def sim_delta_divergence(data, lookback, delta_thresh, tp_dist, sl_dist, max_hold=35, point_val=0.01, spread_cost=0.15, comm=0.0):
    trades = []
    pos = None
    
    for i in range(lookback, len(data)):
        d = data[i]
        c = d['close']
        h = d['high']
        l = d['low']
        
        if pos is not None:
            side = pos['side']
            exit_p = None
            reason = None
            
            if side == 'Buy':
                if h >= pos['tp']: exit_p = pos['tp']; reason = 'TP'
                elif l <= pos['sl']: exit_p = pos['sl']; reason = 'SL'
            else:
                if l <= pos['tp']: exit_p = pos['tp']; reason = 'TP'
                elif h >= pos['sl']: exit_p = pos['sl']; reason = 'SL'
                
            if exit_p is None and (i - pos['idx']) >= max_hold:
                exit_p = c
                reason = 'TIME'
                
            if exit_p is not None:
                trades.append({
                    'side': side, 'entry_p': pos['entry_p'], 'exit_p': exit_p,
                    'reason': reason, 'spread_cost': spread_cost
                })
                pos = None
                continue
                
        if pos is None:
            window = data[i-lookback:i]
            max_h_prev = max(x['high'] for x in window[:-1])
            min_l_prev = min(x['low'] for x in window[:-1])
            
            delta = d['delta']
            cvd_change = d['cvd'] - window[0]['cvd']
            
            # Bearish Divergence: Price touches/exceeds high, but Delta or CVD is negative
            if h >= max_h_prev and (delta <= -delta_thresh or cvd_change < -delta_thresh * 1.5):
                pos = {'side': 'Sell', 'entry_p': c, 'tp': c - tp_dist, 'sl': c + sl_dist, 'idx': i}
            # Bullish Divergence: Price touches/exceeds low, but Delta or CVD is positive
            elif l <= min_l_prev and (delta >= delta_thresh or cvd_change > delta_thresh * 1.5):
                pos = {'side': 'Buy', 'entry_p': c, 'tp': c + tp_dist, 'sl': c - sl_dist, 'idx': i}
                
    return calc_metrics(trades, point_val=point_val, spread_cost=spread_cost, comm_per_trade=comm)

# ==========================================
# OPTIMIZATION WORKFLOW
# ==========================================
def optimize_markets():
    markets = {
        'BTCUSD': {
            'point_val': 0.01,
            'spread_cost': 0.15,
            'comm': 0.0,
            'dom': {
                'lb': [10, 15, 20, 25],
                'imb': [0.02, 0.03, 0.04],
                'tp': [40.0, 50.0, 65.0, 80.0],
                'sl': [20.0, 25.0, 35.0]
            },
            'vwap': {
                'dev': [60.0, 80.0, 100.0, 120.0, 150.0],
                'tp': [45.0, 65.0, 85.0],
                'sl': [30.0, 45.0, 60.0],
                'hold': [20, 30, 45]
            },
            'ny': {
                'mode': ['BREAKOUT', 'FADE'],
                'buf': [10.0, 20.0, 35.0],
                'tp': [50.0, 75.0, 100.0],
                'sl': [25.0, 40.0],
                'hold': [30, 60]
            },
            'delta': {
                'lb': [10, 15, 20],
                'thresh': [20.0, 40.0, 60.0],
                'tp': [50.0, 75.0, 100.0],
                'sl': [25.0, 35.0],
                'hold': [25, 40]
            }
        },
        'ETHUSD': {
            'point_val': 0.01,
            'spread_cost': 0.02, # ~$2 spread on 0.01 lot
            'comm': 0.0,
            'dom': {
                'lb': [10, 15, 20, 25],
                'imb': [0.02, 0.03, 0.04],
                'tp': [2.5, 3.5, 4.5, 5.5],
                'sl': [1.0, 1.5, 2.0]
            },
            'vwap': {
                'dev': [3.5, 4.0, 4.5, 5.0, 6.0],
                'tp': [2.2, 2.7, 3.5, 4.2],
                'sl': [2.5, 3.2, 3.8],
                'hold': [15, 25, 35]
            },
            'ny': {
                'mode': ['BREAKOUT', 'FADE'],
                'buf': [1.0, 2.0, 3.0],
                'tp': [3.0, 4.5, 6.0],
                'sl': [1.8, 2.5],
                'hold': [30, 60]
            },
            'delta': {
                'lb': [10, 15, 20],
                'thresh': [5.0, 10.0, 20.0],
                'tp': [3.0, 4.5, 6.0],
                'sl': [1.5, 2.5],
                'hold': [20, 35]
            }
        },
        'GOLD-PERP': {
            'point_val': 1.00, # 1 oz per 0.01 lot
            'spread_cost': 1.39, # ~$1.39 spread on 1 oz
            'comm': 0.08, # Razor commission
            'dom': {
                'lb': [10, 15, 20],
                'imb': [0.010, 0.015, 0.020, 0.025],
                'tp': [2.5, 3.5, 5.0, 6.5],
                'sl': [1.5, 2.0, 2.5]
            },
            'vwap': {
                'dev': [1.0, 1.5, 2.0, 2.8],
                'tp': [1.5, 2.2, 3.0],
                'sl': [1.5, 2.0, 2.5],
                'hold': [20, 30, 45]
            },
            'ny': {
                'mode': ['BREAKOUT', 'FADE'],
                'buf': [0.5, 1.0, 1.5],
                'tp': [2.5, 4.0, 6.0],
                'sl': [1.8, 2.5],
                'hold': [30, 60]
            },
            'delta': {
                'lb': [10, 15, 20],
                'thresh': [3.0, 8.0, 15.0],
                'tp': [2.5, 4.0, 6.0],
                'sl': [1.8, 2.5],
                'hold': [25, 40]
            }
        }
    }
    
    results = {}
    
    for symbol, cfg in markets.items():
        print(f"\n=======================================================")
        print(f"      OPTIMIZING MARKET: {symbol}")
        print(f"=======================================================")
        data = load_market_data(symbol)
        print(f"Dataset Size: {len(data)} continuous minutes.")
        
        pv = cfg['point_val']
        sc = cfg['spread_cost']
        comm = cfg['comm']
        results[symbol] = {}
        
        # 1. DOM_ABSORPTION
        best_dom = None
        best_dom_score = -999999
        d_cfg = cfg['dom']
        for lb in d_cfg['lb']:
            for imb in d_cfg['imb']:
                for tp in d_cfg['tp']:
                    for sl in d_cfg['sl']:
                        m = sim_dom_absorption(data, lb, imb, tp, sl, point_val=pv, spread_cost=sc, comm=comm)
                        if m['trades'] >= 5:
                            score = m['net_pnl'] * min(m['profit_factor'], 4.0)
                            if score > best_dom_score:
                                best_dom_score = score
                                best_dom = {'params': {'lb': lb, 'imb': imb, 'tp': tp, 'sl': sl}, 'metrics': m}
        results[symbol]['DOM_ABSORPTION'] = best_dom
        if best_dom:
            print(f"[DOM_ABSORPTION]      {best_dom['params']} | PnL: ${best_dom['metrics']['net_pnl']:>6.2f} | PF: {best_dom['metrics']['profit_factor']:>4.2f} | WR: {best_dom['metrics']['win_rate']:>5.1f}% | Trades: {best_dom['metrics']['trades']:>3}")
        else:
            print(f"[DOM_ABSORPTION]      No qualified configuration found.")

        # 2. MID_RANGE_VWAP_SCALP
        best_vwap = None
        best_vwap_score = -999999
        v_cfg = cfg['vwap']
        for dev in v_cfg['dev']:
            for tp in v_cfg['tp']:
                for sl in v_cfg['sl']:
                    for hold in v_cfg['hold']:
                        m = sim_vwap_scalp(data, dev, tp, sl, max_hold=hold, point_val=pv, spread_cost=sc, comm=comm)
                        if m['trades'] >= 5:
                            score = m['net_pnl'] * min(m['profit_factor'], 4.0)
                            if score > best_vwap_score:
                                best_vwap_score = score
                                best_vwap = {'params': {'dev': dev, 'tp': tp, 'sl': sl, 'hold': hold}, 'metrics': m}
        results[symbol]['MID_RANGE_VWAP_SCALP'] = best_vwap
        if best_vwap:
            print(f"[MID_RANGE_VWAP_SCALP] {best_vwap['params']} | PnL: ${best_vwap['metrics']['net_pnl']:>6.2f} | PF: {best_vwap['metrics']['profit_factor']:>4.2f} | WR: {best_vwap['metrics']['win_rate']:>5.1f}% | Trades: {best_vwap['metrics']['trades']:>3}")
        else:
            print(f"[MID_RANGE_VWAP_SCALP] No qualified configuration found.")

        # 3. NY_VALUE
        best_ny = None
        best_ny_score = -999999
        ny_cfg = cfg['ny']
        for mode in ny_cfg['mode']:
            for buf in ny_cfg['buf']:
                for tp in ny_cfg['tp']:
                    for sl in ny_cfg['sl']:
                        for hold in ny_cfg['hold']:
                            m = sim_ny_value(data, mode, buf, tp, sl, max_hold=hold, point_val=pv, spread_cost=sc, comm=comm)
                            if m['trades'] >= 4:
                                score = m['net_pnl'] * min(m['profit_factor'], 4.0)
                                if score > best_ny_score:
                                    best_ny_score = score
                                    best_ny = {'params': {'mode': mode, 'buf': buf, 'tp': tp, 'sl': sl, 'hold': hold}, 'metrics': m}
        results[symbol]['NY_VALUE'] = best_ny
        if best_ny:
            print(f"[NY_VALUE]            {best_ny['params']} | PnL: ${best_ny['metrics']['net_pnl']:>6.2f} | PF: {best_ny['metrics']['profit_factor']:>4.2f} | WR: {best_ny['metrics']['win_rate']:>5.1f}% | Trades: {best_ny['metrics']['trades']:>3}")
        else:
            print(f"[NY_VALUE]            No qualified configuration found.")

        # 4. CVD_DELTA_DIVERGENCE
        best_delta = None
        best_delta_score = -999999
        del_cfg = cfg['delta']
        for lb in del_cfg['lb']:
            for thresh in del_cfg['thresh']:
                for tp in del_cfg['tp']:
                    for sl in del_cfg['sl']:
                        for hold in del_cfg['hold']:
                            m = sim_delta_divergence(data, lb, thresh, tp, sl, max_hold=hold, point_val=pv, spread_cost=sc, comm=comm)
                            if m['trades'] >= 4:
                                score = m['net_pnl'] * min(m['profit_factor'], 4.0)
                                if score > best_delta_score:
                                    best_delta_score = score
                                    best_delta = {'params': {'lb': lb, 'thresh': thresh, 'tp': tp, 'sl': sl, 'hold': hold}, 'metrics': m}
        results[symbol]['CVD_DELTA_DIVERGENCE'] = best_delta
        if best_delta:
            print(f"[CVD_DELTA_DIVERGENCE] {best_delta['params']} | PnL: ${best_delta['metrics']['net_pnl']:>6.2f} | PF: {best_delta['metrics']['profit_factor']:>4.2f} | WR: {best_delta['metrics']['win_rate']:>5.1f}% | Trades: {best_delta['metrics']['trades']:>3}")
        else:
            print(f"[CVD_DELTA_DIVERGENCE] No qualified configuration found.")

    out_file = r'd:\cbot-atgvt\data\optimized_all_markets.json'
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nOptimization complete! Results written to: {out_file}")

if __name__ == '__main__':
    optimize_markets()
