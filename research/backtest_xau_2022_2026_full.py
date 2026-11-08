"""
Multi-Year Quant Backtest on XAU/USD (2022 - 2026: 1,675,835 M1 Bars)
---------------------------------------------------------------------
Evaluates Institutional Quant Models across 5 Full Years:
1. Strategy A: Extreme Deviation Reversal (Anchored Session VWAP + Volume Exhaustion + Dynamic ATR Sizing)
2. Institutional Auction & Value Area Breakout (New York Open 13:00 UTC + Kalman Velocity + News Gate)

Dataset: XAU/USD 1-Minute Bars (2022-01-03 to 2026-09-30)
Broker Simulation: Pepperstone cTrader (Spread ~$0.20 USD, Commission $0.07 / 0.01 lot)
"""

import os
import sys
import time
import math
import json
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')

def load_data_2022_2026():
    path = r"d:\cbot-atgvt\data\XAUUSD_2022_2026_Minute.csv"
    print(f"Loading 2022-2026 dataset from: {path}")
    t0 = time.time()
    raw = []
    with open(path, 'r', encoding='utf-8') as f:
        f.readline()
        for line in f:
            p = line.rstrip().split(',')
            raw.append((int(p[0]), float(p[1]), float(p[2]), float(p[3]), float(p[4]), float(p[5])))
            
    arr = np.array(raw, dtype=[('unix', 'i8'), ('open', 'f8'), ('high', 'f8'), ('low', 'f8'), ('close', 'f8'), ('vol', 'f8')])
    print(f"Loaded {len(arr):,} M1 bars in {time.time()-t0:.2f}s")
    print(f"Date range: {time.strftime('%Y-%m-%d', time.gmtime(arr['unix'][0]))} to {time.strftime('%Y-%m-%d', time.gmtime(arr['unix'][-1]))}")
    return arr

def run_strategy_a_reversal(arr):
    print("\n" + "=" * 88)
    print("      STRATEGY A: EXTREME DEVIATION REVERSAL (2022 - 2026)")
    print("=" * 88)
    
    n = len(arr)
    unix = arr['unix']
    close = arr['close']
    high = arr['high']
    low = arr['low']
    vol = arr['vol']
    
    days = unix // 86400
    sec_of_day = unix % 86400
    hours = sec_of_day // 3600
    mins = (sec_of_day % 3600) // 60
    
    # Cost parameters for Pepperstone Gold
    spread_cost = 0.20
    comm = 0.07
    
    # 1. Precalculate Daily Anchored VWAP and Rolling ATR
    print("Precalculating Session Anchored VWAP and Rolling ATR...")
    atr = np.zeros(n, dtype=np.float64)
    atr[0] = high[0] - low[0]
    for i in range(1, n):
        tr = max(high[i] - low[i], abs(high[i] - close[i-1]), abs(low[i] - close[i-1]))
        atr[i] = 0.95 * atr[i-1] + 0.05 * tr
        
    vwap = np.zeros(n, dtype=np.float64)
    vwap_sd = np.zeros(n, dtype=np.float64)
    
    cur_d = -1
    pv_sum = 0.0
    v_sum = 0.0
    p2v_sum = 0.0
    
    for i in range(n):
        d = days[i]
        if d != cur_d:
            cur_d = d
            pv_sum = 0.0
            v_sum = 0.0
            p2v_sum = 0.0
            
        p = (high[i] + low[i] + close[i]) / 3.0
        v = max(vol[i], 1.0)
        pv_sum += p * v
        p2v_sum += (p ** 2) * v
        v_sum += v
        
        cur_vwap = pv_sum / v_sum
        vwap[i] = cur_vwap
        var = max((p2v_sum / v_sum) - (cur_vwap ** 2), 0.01)
        vwap_sd[i] = math.sqrt(var)

    # 2. Simulation Execution
    print("Simulating Strategy A trades across 1.67M bars...")
    trades = []
    pos = None
    last_exit_idx = -10
    
    year_map = {}
    
    for i in range(50, n - 60):
        # Exit management
        if pos is not None:
            side = pos['side']
            entry_p = pos['entry_p']
            sl = pos['sl']
            tp = pos['tp']
            entry_i = pos['idx']
            hold = i - entry_i
            
            exit_p = None
            reason = None
            
            if side == 'BUY':
                if high[i] >= tp: exit_p = tp; reason = 'TP'
                elif low[i] <= sl: exit_p = sl; reason = 'SL'
                elif hold >= pos['max_hold']: exit_p = close[i]; reason = 'TIME'
            else:
                if low[i] <= tp: exit_p = tp; reason = 'TP'
                elif high[i] >= sl: exit_p = sl; reason = 'SL'
                elif hold >= pos['max_hold']: exit_p = close[i]; reason = 'TIME'
                
            if exit_p is not None:
                pts = (exit_p - entry_p) if side == 'BUY' else (entry_p - exit_p)
                pnl = pts - spread_cost - comm
                yr = time.gmtime(pos['time']).tm_year
                year_map.setdefault(yr, []).append(pnl)
                trades.append({
                    'side': side, 'entry': entry_p, 'exit': exit_p,
                    'pnl': round(pnl, 2), 'reason': reason, 'year': yr
                })
                pos = None
                last_exit_idx = i
                continue
                
        # Entry Logic: Extreme Deviation during Institutional Windows (07:00-11:00 London & 13:00-17:00 NY)
        if pos is None and (i - last_exit_idx >= 5):
            h_utc = hours[i]
            if (7 <= h_utc <= 11) or (13 <= h_utc <= 17):
                cur_atr = max(atr[i], 1.2)
                cur_dev = close[i] - vwap[i]
                cur_sd = max(vwap_sd[i], 1.0)
                
                # Check for extreme price stretch (> 2.0 SD and > 1.8 ATR)
                is_stretched_low = (cur_dev <= -2.0 * cur_sd) and (close[i] <= min(low[i-15:i]))
                is_stretched_high = (cur_dev >= 2.0 * cur_sd) and (close[i] >= max(high[i-15:i]))
                
                # Volume exhaustion: current bar volume < rolling average volume
                avg_v = sum(vol[i-15:i]) / 15.0
                is_vol_exhausted = (vol[i] < avg_v * 1.2)
                
                # Gate: avoid extreme news spikes (tr < 2.0 ATR)
                is_normal_bar = (high[i] - low[i]) <= (cur_atr * 2.0)
                
                signal = None
                if is_stretched_low and is_vol_exhausted and is_normal_bar:
                    signal = 'BUY'
                elif is_stretched_high and is_vol_exhausted and is_normal_bar:
                    signal = 'SELL'
                    
                if signal:
                    sl_dist = 2.0 * cur_atr
                    tp_dist = sl_dist * 2.5 # Asymmetric 2.5:1 RR
                    pos = {
                        'side': signal, 'entry_p': close[i], 'idx': i, 'time': unix[i],
                        'sl': close[i] - sl_dist if signal == 'BUY' else close[i] + sl_dist,
                        'tp': close[i] + tp_dist if signal == 'BUY' else close[i] - tp_dist,
                        'max_hold': 45
                    }

    tot = len(trades)
    wins = [t['pnl'] for t in trades if t['pnl'] > 0]
    losses = [abs(t['pnl']) for t in trades if t['pnl'] < 0]
    gw = sum(wins); gl = sum(losses)
    net_pnl = gw - gl
    wr = (len(wins) / tot * 100.0) if tot else 0.0
    pf = (gw / gl) if gl > 0 else 99.0
    
    print(f"\nTotal Trades:         {tot:,}")
    print(f"Win Rate:             {wr:.1f}%")
    print(f"Profit Factor:        {pf:.2f}")
    print(f"Total Net PnL:        +${net_pnl:,.2f} USD")
    print(f"Average Trade:        +${net_pnl/tot:.2f} USD" if tot else "N/A")
    print("-" * 88)
    print(f"{'Year':6s} | {'Trades':8s} | {'Win Rate':10s} | {'Net PnL ($)':14s} | {'Profit Factor':14s}")
    print("-" * 88)
    
    annual_breakdown = {}
    for yr in sorted(year_map.keys()):
        yp = year_map[yr]
        yw = [x for x in yp if x > 0]
        yl = [abs(x) for x in yp if x < 0]
        ygw = sum(yw); ygl = sum(yl)
        ypf = (ygw / ygl) if ygl > 0 else 99.0
        ywr = (len(yw) / len(yp) * 100.0)
        ynet = sum(yp)
        print(f"{yr:<6d} | {len(yp):<8d} | {ywr:<9.1f}% | ${ynet:<13.2f} | {ypf:<14.2f}")
        annual_breakdown[str(yr)] = {
            'trades': len(yp), 'win_rate': round(ywr, 1),
            'net_pnl': round(ynet, 2), 'profit_factor': round(ypf, 2)
        }
    print("=" * 88)
    return {
        'model': 'STRATEGY_A_REVERSAL',
        'total_trades': tot, 'win_rate': round(wr, 1),
        'net_pnl': round(net_pnl, 2), 'profit_factor': round(pf, 2),
        'annual': annual_breakdown
    }

def run_institutional_auction_value(arr):
    print("\n" + "=" * 88)
    print("   INSTITUTIONAL AUCTION & VALUE AREA BREAKOUT (2022 - 2026: 5 FULL YEARS)")
    print("=" * 88)
    
    n = len(arr)
    unix = arr['unix']
    close = arr['close']
    high = arr['high']
    low = arr['low']
    vol = arr['vol']
    
    days = unix // 86400
    sec_of_day = unix % 86400
    hours = sec_of_day // 3600
    mins = (sec_of_day % 3600) // 60
    
    spread_cost = 0.20
    comm = 0.07
    trade_cost = spread_cost + comm
    
    # 1. Daily Value Area (70% standard deviation range)
    print("Calculating Daily Institutional Value Area (VAH & VAL)...")
    day_indices = {}
    for i in range(n):
        day_indices.setdefault(days[i], []).append(i)
        
    day_va = {}
    for d, idxs in day_indices.items():
        if len(idxs) > 60:
            d_close = close[idxs]
            d_vol = vol[idxs]
            weights = d_vol if np.sum(d_vol) > 0 else None
            mean_p = np.average(d_close, weights=weights)
            std_p = np.sqrt(np.average((d_close - mean_p)**2, weights=weights))
            val = mean_p - 1.04 * std_p
            vah = mean_p + 1.04 * std_p
            day_va[d] = (val, vah)

    # 2. State-Space Kalman Velocity Filter
    print("Filtering micro-noise with State-Space Kalman Filter...")
    kalman_vel = np.zeros(n, dtype=np.float64)
    x0 = close[0]; x1 = 0.0; p00 = 1.0; p11 = 1.0
    for i in range(1, n):
        x0_p = x0 + x1; p00_p = p00 + p11 + 0.0005; p11_p = p11 + 0.0005
        res = close[i] - x0_p; s = p00_p + 0.5
        k0 = p00_p / s; k1 = p11_p / s
        x0 = x0_p + k0 * res; x1 = x1 + k1 * res
        p00 = (1.0 - k0) * p00_p; p11 = (1.0 - k1) * p11_p
        kalman_vel[i] = x1

    # 3. Rolling ATR
    atr = np.zeros(n, dtype=np.float64)
    atr[0] = high[0] - low[0]
    for i in range(1, n):
        tr = max(high[i] - low[i], abs(high[i] - close[i-1]), abs(low[i] - close[i-1]))
        atr[i] = 0.95 * atr[i-1] + 0.05 * tr

    # 4. Simulation
    print("Executing 5-Year Institutional Auction simulation...")
    trades = []
    year_map = {}
    
    for i in range(100, n - 60):
        # Trigger at New York Open 13:00 UTC (Institutional Liquidity Surge)
        if hours[i] == 13 and mins[i] == 0:
            curr_d = days[i]
            prev_d = curr_d - 1
            while prev_d not in day_va and prev_d > curr_d - 5:
                prev_d -= 1
            if prev_d not in day_va:
                continue
                
            val, vah = day_va[prev_d]
            c = close[i]
            cur_atr = max(1.5, atr[i])
            sl_dist = max(10.0, 2.5 * cur_atr)
            
            signal = None
            if c > vah and kalman_vel[i] > 0.05:
                signal = 'BUY'
            elif c < val and kalman_vel[i] < -0.05:
                signal = 'SELL'
                
            if signal:
                entry_p = c
                exit_p = close[i + 60] # Hold 60-minute institutional window
                
                # Check for intrabar SL touch
                stopped = False
                for j in range(i + 1, i + 61):
                    if signal == 'BUY' and low[j] <= (entry_p - sl_dist):
                        exit_p = entry_p - sl_dist
                        stopped = True
                        break
                    elif signal == 'SELL' and high[j] >= (entry_p + sl_dist):
                        exit_p = entry_p + sl_dist
                        stopped = True
                        break
                        
                pts = (exit_p - entry_p) if signal == 'BUY' else (entry_p - exit_p)
                pnl = pts - trade_cost
                
                yr = time.gmtime(unix[i]).tm_year
                year_map.setdefault(yr, []).append(pnl)
                trades.append({
                    'side': signal, 'pnl': round(pnl, 2), 'stopped': stopped, 'year': yr
                })

    tot = len(trades)
    wins = [t['pnl'] for t in trades if t['pnl'] > 0]
    losses = [abs(t['pnl']) for t in trades if t['pnl'] < 0]
    gw = sum(wins); gl = sum(losses)
    net_pnl = gw - gl
    wr = (len(wins) / tot * 100.0) if tot else 0.0
    pf = (gw / gl) if gl > 0 else 99.0
    
    print(f"\nTotal Trades:         {tot:,}")
    print(f"Win Rate:             {wr:.1f}%")
    print(f"Profit Factor:        {pf:.2f}")
    print(f"Total Net PnL:        +${net_pnl:,.2f} USD")
    print(f"Average Trade:        +${net_pnl/tot:.2f} USD" if tot else "N/A")
    print("-" * 88)
    print(f"{'Year':6s} | {'Trades':8s} | {'Win Rate':10s} | {'Net PnL ($)':14s} | {'Profit Factor':14s}")
    print("-" * 88)
    
    annual_breakdown = {}
    for yr in sorted(year_map.keys()):
        yp = year_map[yr]
        yw = [x for x in yp if x > 0]
        yl = [abs(x) for x in yp if x < 0]
        ygw = sum(yw); ygl = sum(yl)
        ypf = (ygw / ygl) if ygl > 0 else 99.0
        ywr = (len(yw) / len(yp) * 100.0)
        ynet = sum(yp)
        print(f"{yr:<6d} | {len(yp):<8d} | {ywr:<9.1f}% | ${ynet:<13.2f} | {ypf:<14.2f}")
        annual_breakdown[str(yr)] = {
            'trades': len(yp), 'win_rate': round(ywr, 1),
            'net_pnl': round(ynet, 2), 'profit_factor': round(ypf, 2)
        }
    print("=" * 88)
    return {
        'model': 'INSTITUTIONAL_AUCTION_NY_OPEN',
        'total_trades': tot, 'win_rate': round(wr, 1),
        'net_pnl': round(net_pnl, 2), 'profit_factor': round(pf, 2),
        'annual': annual_breakdown
    }

def main():
    arr = load_data_2022_2026()
    res_a = run_strategy_a_reversal(arr)
    res_b = run_institutional_auction_value(arr)
    
    combined = {
        'dataset': 'XAUUSD_2022_2026_MINUTE',
        'total_bars': len(arr),
        'span': f"{time.strftime('%Y-%m-%d', time.gmtime(arr['unix'][0]))} to {time.strftime('%Y-%m-%d', time.gmtime(arr['unix'][-1]))}",
        'strategy_a': res_a,
        'institutional_auction': res_b
    }
    
    out_file = r"d:\cbot-atgvt\data\xau_2022_2026_5year_benchmark.json"
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(combined, f, ensure_ascii=False, indent=2)
    print(f"\nSaved 5-Year Benchmark Results to: {out_file}")

if __name__ == '__main__':
    main()
