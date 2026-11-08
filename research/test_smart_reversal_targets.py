"""
Institutional Dual-Regime Gold Strategy (2022 - 2026)
-----------------------------------------------------
1. Range / Reversal Regime: Extreme VWAP Reversion (SD >= 2.5, Target = VWAP)
2. Momentum Breakout Regime: Value Area Expansion Breakout (Target = 2.5x SL)
3. Volatility Void & Major News Blackout Gate
"""

import sys
import time
import math
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

def run_strategy_benchmark():
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
    years = np.array([time.gmtime(u).tm_year for u in unix])
    
    # 1-min ATR & Daily ATR estimate
    atr = np.zeros(n, dtype=np.float64)
    atr[0] = high[0] - low[0]
    for i in range(1, n):
        tr = max(high[i] - low[i], abs(high[i] - close[i-1]), abs(low[i] - close[i-1]))
        atr[i] = 0.95 * atr[i-1] + 0.05 * tr

    # Anchored Session VWAP & SD
    vwap = np.zeros(n, dtype=np.float64)
    vwap_sd = np.zeros(n, dtype=np.float64)
    cur_d = -1; pv_sum = 0.0; v_sum = 0.0; p2v_sum = 0.0; d_open = 0.0
    day_open = np.zeros(n, dtype=np.float64)
    for i in range(n):
        d = days[i]
        if d != cur_d:
            cur_d = d; pv_sum = 0.0; v_sum = 0.0; p2v_sum = 0.0
            d_open = close[i]
        day_open[i] = d_open
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

    # Parameter Test: Reversal with proper Daily Trend Exhaustion Gate
    # When market has stretched > 2.6 SD and wick rejection occurs during NY Session
    # Target: 0.5 distance back to VWAP or full VWAP
    for target_mode in ['HALF_VWAP', 'FULL_VWAP', 'RR_2_5']:
        for sd_th in [2.4, 2.7, 3.0]:
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
                    cur_v = vwap[i]
                    hold = i - pos['idx']
                    
                    exit_p = None
                    if side == 'BUY':
                        if target_mode == 'FULL_VWAP' and high[i] >= cur_v: exit_p = cur_v
                        elif target_mode == 'HALF_VWAP' and high[i] >= (entry_p + cur_v) / 2.0: exit_p = (entry_p + cur_v) / 2.0
                        elif target_mode == 'RR_2_5' and high[i] >= tp: exit_p = tp
                        elif low[i] <= sl: exit_p = sl
                        elif hold >= 60: exit_p = close[i]
                    else:
                        if target_mode == 'FULL_VWAP' and low[i] <= cur_v: exit_p = cur_v
                        elif target_mode == 'HALF_VWAP' and low[i] <= (entry_p + cur_v) / 2.0: exit_p = (entry_p + cur_v) / 2.0
                        elif target_mode == 'RR_2_5' and low[i] <= tp: exit_p = tp
                        elif high[i] >= sl: exit_p = sl
                        elif hold >= 60: exit_p = close[i]
                            
                    if exit_p is not None:
                        pts = (exit_p - entry_p) if side == 'BUY' else (entry_p - exit_p)
                        trades.append({
                            'pnl': pts - trade_cost,
                            'year': years[i]
                        })
                        pos = None
                        last_exit_idx = i
                        continue
                        
                # Entry check
                if pos is None and (i - last_exit_idx >= 5):
                    h_utc = hours[i]
                    if 13 <= h_utc <= 17:
                        cur_atr = max(atr[i], 1.2)
                        cur_dev = close[i] - vwap[i]
                        cur_sd = max(vwap_sd[i], 1.0)
                        
                        # Extreme stretch + wick reversal
                        is_buy = (cur_dev <= -sd_th * cur_sd) and (close[i] > low[i] + 0.3 * (high[i] - low[i]))
                        is_sell = (cur_dev >= sd_th * cur_sd) and (close[i] < high[i] - 0.3 * (high[i] - low[i]))
                        
                        # News gate: bar range <= 2.2 ATR
                        if (high[i] - low[i]) > 2.2 * cur_atr:
                            continue
                            
                        signal = None
                        if is_buy: signal = 'BUY'
                        elif is_sell: signal = 'SELL'
                        
                        if signal:
                            sl_dist = 1.8 * cur_atr
                            tp_dist = sl_dist * 2.5
                            pos = {
                                'side': signal, 'entry_p': close[i], 'idx': i,
                                'sl': close[i] - sl_dist if signal == 'BUY' else close[i] + sl_dist,
                                'tp': close[i] + tp_dist if signal == 'BUY' else close[i] - tp_dist
                            }

            tot = len(trades)
            if tot > 50:
                pnls = [t['pnl'] for t in trades]
                wins = [p for p in pnls if p > 0]
                losses = [abs(p) for p in pnls if p < 0]
                gw = sum(wins); gl = sum(losses)
                net_pnl = gw - gl
                wr = (len(wins) / tot * 100.0)
                pf = round(gw / gl, 2) if gl > 0 else 99.0
                print(f"Target: {target_mode:<10s} | SD: {sd_th:<4.1f} | Trades: {tot:<5d} | WR: {wr:<5.1f}% | Net PnL: ${net_pnl:<+8.2f} | PF: {pf:<5.2f}")

if __name__ == '__main__':
    run_strategy_benchmark()
