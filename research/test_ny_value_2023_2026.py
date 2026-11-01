"""
Backtest Auction Market Theory Value Area Breakout (NY_VALUE + Quant Kalman)
Across 1.32 Million bars of Gold (XAUUSD) from January 2023 to late 2026.
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
                    for b in range(ev_time - 1800, ev_time + 7200, 60): # 30m before to 120m after
                        news_blackout.add(b)
                        
    return arr, news_blackout

def run_ny_value_backtest(arr, news_blackout):
    n = len(arr)
    unix = arr['unix']
    close = arr['close']
    high = arr['high']
    low = arr['low']
    vol = arr['vol']
    
    days = unix // 86400
    hours = (unix % 86400) // 3600
    mins = (unix % 3600) // 60
    
    years = np.full(n, 2023, dtype=np.int32)
    years[unix >= 1704067200] = 2024
    years[unix >= 1735689600] = 2025
    years[unix >= 1767225600] = 2026
    
    trade_cost = 0.35 # Commission + Spread on 1 oz Gold
    
    # 1. Precalculate Daily Value Area (70% range of previous day based on Volume Profile)
    # Group bars by day
    day_indices = {}
    for i in range(n):
        day_indices.setdefault(days[i], []).append(i)
        
    sorted_days = sorted(day_indices.keys())
    day_va = {} # day -> (val, vah, poc)
    
    for d in sorted_days:
        idxs = day_indices[d]
        d_close = close[idxs]
        d_vol = vol[idxs]
        
        # Simple Volume Profile 70% Value Area
        min_p = np.min(low[idxs])
        max_p = np.max(high[idxs])
        d_range = max_p - min_p
        
        if d_range > 0 and len(idxs) > 60:
            # Approx 70% value area around mean
            mean_p = np.average(d_close, weights=d_vol if np.sum(d_vol) > 0 else None)
            std_p = np.sqrt(np.average((d_close - mean_p)**2, weights=d_vol if np.sum(d_vol) > 0 else None))
            val = mean_p - 1.04 * std_p # approx 70% distribution
            vah = mean_p + 1.04 * std_p
            day_va[d] = (val, vah)
            
    # 2. Kalman Filter Precomputation
    kalman_vel = np.zeros(n, dtype=np.float64)
    x0 = close[0]; x1 = 0.0; p00 = 1.0; p11 = 1.0
    for i in range(1, n):
        x0_p = x0 + x1; p00_p = p00 + p11 + 0.0005; p11_p = p11 + 0.0005
        res = close[i] - x0_p; s = p00_p + 0.5
        k0 = p00_p / s; k1 = p11_p / s
        x0 = x0_p + k0 * res; x1 = x1 + k1 * res
        p00 = (1.0 - k0) * p00_p; p11 = (1.0 - k1) * p11_p
        kalman_vel[i] = x1

    # 3. Simulate Trades
    trades = []
    hold_mins = 60
    sl_dist = 12.0
    
    for i in range(100, n - hold_mins):
        # Decision point: exactly 13:00 UTC (hour 12, min 59 or hour 13, min 0)
        if hours[i] == 13 and mins[i] == 0:
            # Check news blackout
            if unix[i] in news_blackout:
                continue
                
            curr_d = days[i]
            prev_d = curr_d - 1
            # Look up previous day VA
            while prev_d not in day_va and prev_d > curr_d - 5:
                prev_d -= 1
                
            if prev_d not in day_va:
                continue
                
            val, vah = day_va[prev_d]
            c = close[i]
            
            signal = None
            if c > vah and kalman_vel[i] > 0.0:
                signal = 'BUY'
            elif c < val and kalman_vel[i] < 0.0:
                signal = 'SELL'
                
            if signal:
                entry_p = c
                exit_i = i + hold_mins
                exit_p = close[exit_i]
                reason = 'HOLD_60M'
                
                # Check intra-bar SL
                for step in range(i + 1, exit_i + 1):
                    if signal == 'BUY' and low[step] <= entry_p - sl_dist:
                        exit_p = entry_p - sl_dist
                        reason = 'SL'
                        break
                    elif signal == 'SELL' and high[step] >= entry_p + sl_dist:
                        exit_p = entry_p + sl_dist
                        reason = 'SL'
                        break
                        
                pts = (exit_p - entry_p) if signal == 'BUY' else (entry_p - exit_p)
                pnl = pts - trade_cost
                
                trades.append({
                    'signal': signal,
                    'year': int(years[i]),
                    'pnl': round(pnl, 2),
                    'reason': reason
                })

    # Stats
    pnls = [t['pnl'] for t in trades]
    wins = [p for p in pnls if p > 0]
    losses = [abs(p) for p in pnls if p < 0]
    
    gross_win = sum(wins)
    gross_loss = sum(losses)
    net_pnl = gross_win - gross_loss
    wr = (len(wins) / len(pnls)) * 100.0 if pnls else 0.0
    pf = round(gross_win / gross_loss, 2) if gross_loss > 0 else 99.9
    
    yearly = {}
    for t in trades:
        yr = str(t['year'])
        yearly.setdefault(yr, []).append(t['pnl'])
        
    print("="*75)
    print("  NY VALUE AREA BREAKOUT (AUCTION MARKET THEORY + KALMAN CONFIRMATION)  ")
    print("  PERIOD: 2023 - 2026 (1.32 MILLION M1 BARS OF GOLD)                    ")
    print("="*75)
    print(f"Total Trades:     {len(trades)}")
    print(f"Win Rate:         {wr:.1f}%")
    print(f"Gross Profit:     ${gross_win:,.2f}")
    print(f"Gross Loss:       ${gross_loss:,.2f}")
    print(f"Net Profit:       ${net_pnl:+,.2f} USD")
    print(f"Profit Factor:    {pf:.2f}")
    
    print("\nYearly Net PnL:")
    for yr in sorted(yearly.keys()):
        y_pnls = yearly[yr]
        y_win = sum(1 for p in y_pnls if p > 0)
        y_wr = (y_win / len(y_pnls)) * 100.0 if y_pnls else 0
        print(f"  Year {yr}: Trades: {len(y_pnls):3d} | WinRate: {y_wr:4.1f}% | Net PnL: ${sum(y_pnls):+8.2f} USD")
    print("="*75)

if __name__ == '__main__':
    arr, news_blackout = load_data()
    run_ny_value_backtest(arr, news_blackout)
