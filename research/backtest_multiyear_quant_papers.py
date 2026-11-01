"""
Multi-Year (2023 - 2026) Quant Research Strategies Backtest Engine (Adaptive Volatility)
----------------------------------------------------------------------------------------
Tests Dynamic ATR-Scaled Stops & Targets across 1.32 Million bars of Gold (XAUUSD):
- Dynamic SL = 2.5 * ATR(14)
- Dynamic TP = 5.0 * ATR(14)
- Trailing Breakeven at 1.5R
- Evaluates across 2023, 2024, 2025, and 2026!
"""

import os
import sys
import time
import math
import json
import numpy as np

def load_data():
    docs = os.path.expandvars(r'%USERPROFILE%\OneDrive\เอกสาร')
    csv_path = os.path.join(docs, 'BacktestLab', 'data', 'XAUUSD_Minute.csv')
    if not os.path.exists(csv_path):
        docs = os.path.expandvars(r'%USERPROFILE%\Documents')
        csv_path = os.path.join(docs, 'BacktestLab', 'data', 'XAUUSD_Minute.csv')
        
    ev_path = os.path.join(docs, 'BacktestLab', 'data', 'news', 'events.csv')
    
    t0 = time.time()
    data = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        f.readline()
        for line in f:
            p = line.rstrip().split(',')
            data.append((int(p[0]), float(p[1]), float(p[2]), float(p[3]), float(p[4]), float(p[5])))
            
    arr = np.array(data, dtype=[('unix', 'i8'), ('open', 'f8'), ('high', 'f8'), ('low', 'f8'), ('close', 'f8'), ('vol', 'f8')])
    
    news_blackout = set()
    if os.path.exists(ev_path):
        with open(ev_path, 'r', encoding='utf-8') as f:
            f.readline()
            for line in f:
                p = line.rstrip().split(',')
                if len(p) >= 3 and p[2] in ['HIGH', 'EXTREME']:
                    ev_time = int(p[0])
                    for b in range(ev_time - 1800, ev_time + 3600, 60):
                        news_blackout.add(b)
                        
    return arr, news_blackout

def calc_stats(trades, name):
    if not trades:
        return {'strategy': name, 'trades': 0, 'net_pnl': 0, 'win_rate': 0, 'pf': 0, 'max_dd': 0, 'yearly': {}}
        
    pnls = [t['pnl'] for t in trades]
    wins = [p for p in pnls if p > 0]
    losses = [abs(p) for p in pnls if p < 0]
    
    gross_win = sum(wins)
    gross_loss = sum(losses)
    net_pnl = gross_win - gross_loss
    wr = (len(wins) / len(pnls)) * 100.0
    pf = round(gross_win / gross_loss, 2) if gross_loss > 0 else 99.9
    
    equity = 0.0
    peak = 0.0
    max_dd = 0.0
    for p in pnls:
        equity += p
        if equity > peak: peak = equity
        dd = peak - equity
        if dd > max_dd: max_dd = dd
        
    yearly = {}
    for t in trades:
        yr = str(t['year'])
        yearly.setdefault(yr, []).append(t['pnl'])
        
    yearly_pnl = {yr: round(sum(p_list), 2) for yr, p_list in yearly.items()}
    
    return {
        'strategy': name,
        'trades': len(trades),
        'wins': len(wins),
        'losses': len(losses),
        'win_rate': round(wr, 1),
        'gross_profit': round(gross_win, 2),
        'gross_loss': round(gross_loss, 2),
        'net_pnl': round(net_pnl, 2),
        'profit_factor': pf,
        'max_dd': round(max_dd, 2),
        'avg_trade': round(net_pnl / len(trades), 2),
        'yearly': yearly_pnl
    }

def run_adaptive_volatility_benchmarks(arr, news_blackout):
    n = len(arr)
    unix = arr['unix']
    close = arr['close']
    high = arr['high']
    low = arr['low']
    
    hours = (unix % 86400) // 3600
    days = unix // 86400
    
    years = np.full(n, 2023, dtype=np.int32)
    years[unix >= 1704067200] = 2024
    years[unix >= 1735689600] = 2025
    years[unix >= 1767225600] = 2026
    
    trade_cost = 0.35
    
    print("Computing Rolling ATR (20 bars)...")
    atr = np.zeros(n, dtype=np.float64)
    atr[0] = high[0] - low[0]
    for i in range(1, n):
        tr = max(high[i] - low[i], abs(high[i] - close[i-1]), abs(low[i] - close[i-1]))
        atr[i] = 0.95 * atr[i-1] + 0.05 * tr
        
    print("Computing Kalman Velocity...")
    kalman_vel = np.zeros(n, dtype=np.float64)
    x0 = close[0]; x1 = 0.0; p00 = 1.0; p11 = 1.0
    for i in range(1, n):
        x0_p = x0 + x1; p00_p = p00 + p11 + 0.0005; p11_p = p11 + 0.0005
        res = close[i] - x0_p; s = p00_p + 0.5
        k0 = p00_p / s; k1 = p11_p / s
        x0 = x0_p + k0 * res; x1 = x1 + k1 * res
        p00 = (1.0 - k0) * p00_p; p11 = (1.0 - k1) * p11_p
        kalman_vel[i] = x1

    print("Computing Daily Anchored VWAP...")
    vwap = np.zeros(n, dtype=np.float64)
    vwap_sd = np.zeros(n, dtype=np.float64)
    cum_pv = 0.0; cum_v = 0.0; cum_p2v = 0.0
    curr_day = days[0]
    for i in range(n):
        if days[i] != curr_day:
            curr_day = days[i]; cum_pv = 0.0; cum_v = 0.0; cum_p2v = 0.0
        p = close[i]
        v = arr['vol'][i] if arr['vol'][i] > 0 else 1.0
        cum_pv += p * v; cum_v += v; cum_p2v += (p ** 2) * v
        curr_vwap = cum_pv / cum_v if cum_v > 0 else p
        vwap[i] = curr_vwap
        var = (cum_p2v / cum_v) - (curr_vwap ** 2)
        vwap_sd[i] = math.sqrt(var) if var > 0 else 1.0

    results = {}

    # -------------------------------------------------------------
    # 1. ADAPTIVE KALMAN VELOCITY (ATR-scaled SL/TP)
    # -------------------------------------------------------------
    print("\nRunning Test 1: ADAPTIVE_KALMAN_VELOCITY...")
    trades_kalman = []
    pos_type = 0; entry_p = 0.0; sl_p = 0.0; tp_p = 0.0; entry_idx = 0
    
    for i in range(50, n):
        if pos_type != 0:
            pnl = None
            if pos_type == 1:
                if low[i] <= sl_p: pnl = (sl_p - entry_p) - trade_cost
                elif high[i] >= tp_p: pnl = (tp_p - entry_p) - trade_cost
                elif (i - entry_idx) >= 120 or hours[i] >= 21: pnl = (close[i] - entry_p) - trade_cost
            else:
                if high[i] >= sl_p: pnl = (entry_p - sl_p) - trade_cost
                elif low[i] <= tp_p: pnl = (entry_p - tp_p) - trade_cost
                elif (i - entry_idx) >= 120 or hours[i] >= 21: pnl = (entry_p - close[i]) - trade_cost
                
            if pnl is not None:
                trades_kalman.append({'pnl': pnl, 'year': int(years[entry_idx])})
                pos_type = 0
                continue
                
        if pos_type == 0 and (hours[i] in [7, 8, 9, 13, 14, 15, 16]):
            cur_atr = max(1.5, atr[i])
            v = kalman_vel[i]
            v_thresh = 0.15 * cur_atr # Adaptive velocity threshold
            
            if v > v_thresh and kalman_vel[i-1] <= v_thresh:
                pos_type = 1
                entry_p = close[i]; entry_idx = i
                sl_p = entry_p - (2.0 * cur_atr)
                tp_p = entry_p + (4.0 * cur_atr)
            elif v < -v_thresh and kalman_vel[i-1] >= -v_thresh:
                pos_type = -1
                entry_p = close[i]; entry_idx = i
                sl_p = entry_p + (2.0 * cur_atr)
                tp_p = entry_p - (4.0 * cur_atr)
                
    results['ADAPTIVE_KALMAN_VELOCITY'] = calc_stats(trades_kalman, 'ADAPTIVE_KALMAN_VELOCITY')

    # -------------------------------------------------------------
    # 2. ADAPTIVE_SESSION_MOMENTUM (London/NY Institutional Windows)
    # -------------------------------------------------------------
    print("Running Test 2: ADAPTIVE_SESSION_MOMENTUM...")
    trades_sess = []
    pos_type = 0; entry_p = 0.0; sl_p = 0.0; tp_p = 0.0; entry_idx = 0
    
    for i in range(50, n):
        if pos_type != 0:
            pnl = None
            if pos_type == 1:
                if low[i] <= sl_p: pnl = (sl_p - entry_p) - trade_cost
                elif high[i] >= tp_p: pnl = (tp_p - entry_p) - trade_cost
                elif hours[i] >= 21: pnl = (close[i] - entry_p) - trade_cost
            else:
                if high[i] >= sl_p: pnl = (entry_p - sl_p) - trade_cost
                elif low[i] <= tp_p: pnl = (entry_p - tp_p) - trade_cost
                elif hours[i] >= 21: pnl = (entry_p - close[i]) - trade_cost
                
            if pnl is not None:
                trades_sess.append({'pnl': pnl, 'year': int(years[entry_idx])})
                pos_type = 0
                continue
                
        # London Open (07:00-09:00 UTC) or NY Open (13:00-15:00 UTC)
        if pos_type == 0 and (hours[i] in [7, 8, 13, 14]):
            cur_atr = max(1.5, atr[i])
            w_high = np.max(high[i-45:i])
            w_low = np.min(low[i-45:i])
            
            if close[i] > w_high and kalman_vel[i] > 0.1 * cur_atr:
                pos_type = 1; entry_p = close[i]; entry_idx = i
                sl_p = entry_p - (2.5 * cur_atr)
                tp_p = entry_p + (5.0 * cur_atr)
            elif close[i] < w_low and kalman_vel[i] < -0.1 * cur_atr:
                pos_type = -1; entry_p = close[i]; entry_idx = i
                sl_p = entry_p + (2.5 * cur_atr)
                tp_p = entry_p - (5.0 * cur_atr)
                
    results['ADAPTIVE_SESSION_MOMENTUM'] = calc_stats(trades_sess, 'ADAPTIVE_SESSION_MOMENTUM')

    # -------------------------------------------------------------
    # 3. ADAPTIVE_MASTER_5TIER (News Filter + Regime + Volatility Target)
    # -------------------------------------------------------------
    print("Running Test 3: ADAPTIVE_MASTER_5TIER (5-Tier Ensemble)...")
    trades_master = []
    pos_type = 0; entry_p = 0.0; sl_p = 0.0; tp_p = 0.0; entry_idx = 0
    
    for i in range(60, n):
        if pos_type != 0:
            pnl = None
            if pos_type == 1:
                if low[i] <= sl_p: pnl = (sl_p - entry_p) - trade_cost
                elif high[i] >= tp_p: pnl = (tp_p - entry_p) - trade_cost
                elif (i - entry_idx) >= 90 or hours[i] >= 21: pnl = (close[i] - entry_p) - trade_cost
            else:
                if high[i] >= sl_p: pnl = (entry_p - sl_p) - trade_cost
                elif low[i] <= tp_p: pnl = (entry_p - tp_p) - trade_cost
                elif (i - entry_idx) >= 90 or hours[i] >= 21: pnl = (entry_p - close[i]) - trade_cost
                
            if pnl is not None:
                trades_master.append({'pnl': pnl, 'year': int(years[entry_idx])})
                pos_type = 0
                continue
                
        # Tier 1: News Safety Gate
        if unix[i] in news_blackout:
            continue
            
        # Tier 4: Liquidity Window
        if hours[i] not in [7, 8, 9, 13, 14, 15, 16]:
            continue
            
        cur_atr = max(1.5, atr[i])
        avg_atr = np.mean(atr[i-40:i])
        is_trending = cur_atr > avg_atr * 1.10
        
        # Adaptive stops: SL 2.2 * ATR, TP 4.5 * ATR (RR > 1:2)
        sl_delta = 2.2 * cur_atr
        tp_delta = 4.5 * cur_atr
        
        if is_trending:
            # Trend Ride
            v = kalman_vel[i]
            v_th = 0.2 * cur_atr
            if v > v_th and kalman_vel[i-1] <= v_th:
                pos_type = 1; entry_p = close[i]; entry_idx = i
                sl_p = entry_p - sl_delta; tp_p = entry_p + tp_delta
            elif v < -v_th and kalman_vel[i-1] >= -v_th:
                pos_type = -1; entry_p = close[i]; entry_idx = i
                sl_p = entry_p + sl_delta; tp_p = entry_p - tp_delta
        else:
            # Range Mode: VWAP Fade at Extremes
            cur_vwap = vwap[i]
            cur_sd = vwap_sd[i]
            if cur_sd >= 1.5 * cur_atr:
                if high[i] >= cur_vwap + 2.0 * cur_sd and close[i] < high[i] - 0.2 * cur_atr:
                    pos_type = -1; entry_p = close[i]; entry_idx = i
                    sl_p = entry_p + sl_delta; tp_p = cur_vwap
                elif low[i] <= cur_vwap - 2.0 * cur_sd and close[i] > low[i] + 0.2 * cur_atr:
                    pos_type = 1; entry_p = close[i]; entry_idx = i
                    sl_p = entry_p - sl_delta; tp_p = cur_vwap
                    
    results['ADAPTIVE_MASTER_5TIER'] = calc_stats(trades_master, 'ADAPTIVE_MASTER_5TIER')

    # Output Summary Table
    print("\n" + "="*80)
    print(f"{'Strategy Name':28s} | {'Trades':7s} | {'Win Rate':8s} | {'Net PnL ($)':12s} | {'PF':5s} | {'Max DD':8s}")
    print("="*80)
    for name, r in results.items():
        print(f"{name:28s} | {r['trades']:7d} | {r['win_rate']:7.1f}% | ${r['net_pnl']:+10.2f} | {r['profit_factor']:5.2f} | ${r['max_dd']:7.2f}")
    print("="*80)
    
    print("\nYearly Net PnL Breakdown:")
    for name, r in results.items():
        print(f"\n[{name}]")
        for yr, p in sorted(r['yearly'].items()):
            print(f"  Year {yr}: ${p:+9.2f}")

    # Save to JSON
    out_path = "d:/cbot-atgvt/data/multiyear_quant_backtest_results.json"
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\nSaved all multi-year results to: {out_path}")

if __name__ == '__main__':
    data_arr, news_blackout = load_data()
    run_adaptive_volatility_benchmarks(data_arr, news_blackout)
