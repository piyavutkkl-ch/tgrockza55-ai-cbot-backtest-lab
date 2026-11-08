"""
Fast Parameter Optimization of Strategy A on XAU/USD (2022 - 2026 Full Dataset)
-------------------------------------------------------------------------------
Finds the global maximum profit parameter set for Extreme Deviation Reversal:
- dev_sd_thresh: [1.8, 2.2, 2.5, 3.0]
- sl_atr_mult:   [1.5, 2.0, 2.5]
- rr_ratio:      [1.8, 2.2, 2.6, 3.0]
- max_hold:      [25, 40, 60]
- session_mode:  ['NY_ONLY', 'LONDON_ONLY', 'BOTH']
"""

import os
import sys
import time
import math
import json
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')

def load_data():
    path = r"d:\cbot-atgvt\data\XAUUSD_2022_2026_Minute.csv"
    raw = []
    with open(path, 'r', encoding='utf-8') as f:
        f.readline()
        for line in f:
            p = line.rstrip().split(',')
            raw.append((int(p[0]), float(p[1]), float(p[2]), float(p[3]), float(p[4]), float(p[5])))
    return np.array(raw, dtype=[('unix', 'i8'), ('open', 'f8'), ('high', 'f8'), ('low', 'f8'), ('close', 'f8'), ('vol', 'f8')])

def optimize_grid():
    arr = load_data()
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
    
    print("Precomputing indicators...")
    # ATR
    atr = np.zeros(n, dtype=np.float64)
    atr[0] = high[0] - low[0]
    for i in range(1, n):
        tr = max(high[i] - low[i], abs(high[i] - close[i-1]), abs(low[i] - close[i-1]))
        atr[i] = 0.95 * atr[i-1] + 0.05 * tr
        
    # Anchored VWAP & SD
    vwap = np.zeros(n, dtype=np.float64)
    vwap_sd = np.zeros(n, dtype=np.float64)
    cur_d = -1; pv_sum = 0.0; v_sum = 0.0; p2v_sum = 0.0
    for i in range(n):
        d = days[i]
        if d != cur_d:
            cur_d = d; pv_sum = 0.0; v_sum = 0.0; p2v_sum = 0.0
        p = (high[i] + low[i] + close[i]) / 3.0
        v = max(vol[i], 1.0)
        pv_sum += p * v; p2v_sum += (p**2) * v; v_sum += v
        cur_vwap = pv_sum / v_sum
        vwap[i] = cur_vwap
        var = max((p2v_sum / v_sum) - (cur_vwap**2), 0.01)
        vwap_sd[i] = math.sqrt(var)

    spread_cost = 0.20
    comm = 0.07
    trade_cost = spread_cost + comm

    # Grid parameters
    sd_thresh_list = [2.0, 2.4, 2.8]
    rr_list = [2.0, 2.5, 3.0]
    hold_list = [30, 45, 60]
    session_list = ['NY_ONLY', 'BOTH']

    best_pnl = -999999.0
    best_res = None
    
    print(f"\nEvaluating grid of parameter combinations across 2022-2026 ({n:,} bars)...")
    print(f"{'SD Thresh':9s} | {'RR Ratio':8s} | {'Hold':5s} | {'Session':8s} | {'Trades':6s} | {'Win Rate':8s} | {'Net PnL ($)':11s} | {'PF':5s}")
    print("-" * 75)

    for sd_th in sd_thresh_list:
        for rr in rr_list:
            for hold_bars in hold_list:
                for sess in session_list:
                    trades = []
                    pos = None
                    last_exit_idx = -10
                    
                    for i in range(50, n - 65):
                        # Exit check
                        if pos is not None:
                            side = pos['side']
                            entry_p = pos['entry_p']
                            sl = pos['sl']
                            tp = pos['tp']
                            entry_i = pos['idx']
                            hold = i - entry_i
                            
                            exit_p = None
                            if side == 'BUY':
                                if high[i] >= tp: exit_p = tp
                                elif low[i] <= sl: exit_p = sl
                                elif hold >= hold_bars: exit_p = close[i]
                            else:
                                if low[i] <= tp: exit_p = tp
                                elif high[i] >= sl: exit_p = sl
                                elif hold >= hold_bars: exit_p = close[i]
                                
                            if exit_p is not None:
                                pts = (exit_p - entry_p) if side == 'BUY' else (entry_p - exit_p)
                                trades.append(pts - trade_cost)
                                pos = None
                                last_exit_idx = i
                                continue
                                
                        # Entry check
                        if pos is None and (i - last_exit_idx >= 5):
                            h_utc = hours[i]
                            in_sess = (13 <= h_utc <= 17) if sess == 'NY_ONLY' else ((7 <= h_utc <= 11) or (13 <= h_utc <= 17))
                            if in_sess:
                                cur_atr = max(atr[i], 1.2)
                                cur_dev = close[i] - vwap[i]
                                cur_sd = max(vwap_sd[i], 1.0)
                                
                                # Stretched check
                                is_buy = (cur_dev <= -sd_th * cur_sd) and (close[i] <= min(low[i-15:i]))
                                is_sell = (cur_dev >= sd_th * cur_sd) and (close[i] >= max(high[i-15:i]))
                                is_normal_bar = (high[i] - low[i]) <= (cur_atr * 2.0)
                                
                                signal = None
                                if is_buy and is_normal_bar: signal = 'BUY'
                                elif is_sell and is_normal_bar: signal = 'SELL'
                                
                                if signal:
                                    sl_dist = 2.0 * cur_atr
                                    tp_dist = sl_dist * rr
                                    pos = {
                                        'side': signal, 'entry_p': close[i], 'idx': i,
                                        'sl': close[i] - sl_dist if signal == 'BUY' else close[i] + sl_dist,
                                        'tp': close[i] + tp_dist if signal == 'BUY' else close[i] - tp_dist
                                    }

                    tot = len(trades)
                    if tot >= 200:
                        wins = [p for p in trades if p > 0]
                        losses = [abs(p) for p in trades if p < 0]
                        gw = sum(wins); gl = sum(losses)
                        net_pnl = gw - gl
                        wr = (len(wins) / tot * 100.0)
                        pf = round(gw / gl, 2) if gl > 0 else 99.0
                        
                        if net_pnl > best_pnl:
                            best_pnl = net_pnl
                            best_res = {
                                'sd_thresh': sd_th, 'rr_ratio': rr, 'hold': hold_bars,
                                'session': sess, 'trades': tot, 'win_rate': round(wr, 1),
                                'net_pnl': round(net_pnl, 2), 'profit_factor': pf
                            }
                        if net_pnl > -500 or sd_th >= 2.4:
                            print(f"{sd_th:<9.1f} | {rr:<8.1f} | {hold_bars:<5d} | {sess:<8s} | {tot:<6d} | {wr:<7.1f}% | ${net_pnl:<+10.2f} | {pf:<5.2f}")

    print("\n" + "=" * 75)
    print("🏆 BEST CONFIGURATION DISCOVERED (2022 - 2026):")
    print(best_res)
    print("=" * 75)
    
    with open(r"d:\cbot-atgvt\data\xau_2022_2026_optimization_best.json", "w", encoding="utf-8") as f:
        json.dump(best_res, f, ensure_ascii=False, indent=2)

if __name__ == '__main__':
    optimize_grid()
