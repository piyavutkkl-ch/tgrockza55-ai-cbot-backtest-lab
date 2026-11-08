"""
Testing Strategy A with Trend-Day Filter & Climax Absorption (2022 - 2026)
--------------------------------------------------------------------------
Filters:
1. Do not fade against a Strong Trend Day (abs(Close - Day_Open) > 1.5 * Day_ATR)
2. Climax Volume Absorption: Entry bar volume >= 1.2 * Avg_Volume (smart money absorption)
3. Exit at VWAP touch or SL 2.0x ATR
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

def test_regime_filtering():
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
    
    # ATR & Vol Avg
    atr = np.zeros(n, dtype=np.float64)
    vol_avg = np.zeros(n, dtype=np.float64)
    atr[0] = high[0] - low[0]
    vol_avg[0] = vol[0]
    for i in range(1, n):
        tr = max(high[i] - low[i], abs(high[i] - close[i-1]), abs(low[i] - close[i-1]))
        atr[i] = 0.95 * atr[i-1] + 0.05 * tr
        vol_avg[i] = 0.95 * vol_avg[i-1] + 0.05 * vol[i]
        
    # Anchored VWAP & Day Open
    vwap = np.zeros(n, dtype=np.float64)
    vwap_sd = np.zeros(n, dtype=np.float64)
    day_open = np.zeros(n, dtype=np.float64)
    cur_d = -1; pv_sum = 0.0; v_sum = 0.0; p2v_sum = 0.0; d_open = 0.0
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

    print(f"\n{'SD Thresh':9s} | {'Trend Gate':10s} | {'Vol Gate':8s} | {'Trades':6s} | {'Win Rate':8s} | {'Net PnL ($)':11s} | {'PF':5s}")
    print("-" * 75)

    experiments = [
        # (sd_thresh, trend_filter_on, vol_filter_on)
        (2.5, False, False),
        (2.5, True, False),
        (2.5, True, True),
        (2.8, False, False),
        (2.8, True, False),
        (2.8, True, True),
        (3.0, False, False),
        (3.0, True, False),
        (3.0, True, True),
    ]

    best_pnl = -999999.0
    best_exp = None

    for sd_th, trend_gate, vol_gate in experiments:
        trades = []
        pos = None
        last_exit_idx = -10
        
        for i in range(50, n - 65):
            # Exit check
            if pos is not None:
                side = pos['side']
                entry_p = pos['entry_p']
                sl = pos['sl']
                cur_v = vwap[i]
                entry_i = pos['idx']
                hold = i - entry_i
                
                exit_p = None
                if side == 'BUY':
                    if high[i] >= cur_v: exit_p = cur_v
                    elif low[i] <= sl: exit_p = sl
                    elif hold >= 60: exit_p = close[i]
                else:
                    if low[i] <= cur_v: exit_p = cur_v
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
                    
                    # Basic setup
                    is_buy = (cur_dev <= -sd_th * cur_sd) and (close[i] <= min(low[i-15:i]))
                    is_sell = (cur_dev >= sd_th * cur_sd) and (close[i] >= max(high[i-15:i]))
                    
                    # 1. News void gate
                    is_normal_bar = (high[i] - low[i]) <= (cur_atr * 2.0)
                    if not is_normal_bar:
                        continue
                        
                    # 2. Trend day gate: Don't counter-trade runaway trend
                    if trend_gate:
                        day_dist = close[i] - day_open[i]
                        # If market is down > 1.8 ATR from open, do not blindly buy falling knife
                        if is_buy and day_dist < -1.8 * cur_atr:
                            continue
                        # If market is up > 1.8 ATR from open, do not blindly short runaway rocket
                        if is_sell and day_dist > 1.8 * cur_atr:
                            continue
                            
                    # 3. Volume Climax absorption
                    if vol_gate:
                        if vol[i] < 1.1 * vol_avg[i]:
                            continue
                    
                    signal = None
                    if is_buy: signal = 'BUY'
                    elif is_sell: signal = 'SELL'
                    
                    if signal:
                        sl_dist = 2.0 * cur_atr
                        pos = {
                            'side': signal, 'entry_p': close[i], 'idx': i,
                            'sl': close[i] - sl_dist if signal == 'BUY' else close[i] + sl_dist
                        }

        tot = len(trades)
        if tot > 0:
            pnls = [t['pnl'] for t in trades]
            wins = [p for p in pnls if p > 0]
            losses = [abs(p) for p in pnls if p < 0]
            gw = sum(wins); gl = sum(losses)
            net_pnl = gw - gl
            wr = (len(wins) / tot * 100.0)
            pf = round(gw / gl, 2) if gl > 0 else 99.0
            
            tg_str = "YES" if trend_gate else "NO"
            vg_str = "YES" if vol_gate else "NO"
            print(f"{sd_th:<9.1f} | {tg_str:<10s} | {vg_str:<8s} | {tot:<6d} | {wr:<7.1f}% | ${net_pnl:<+10.2f} | {pf:<5.2f}")
            
            if net_pnl > best_pnl:
                best_pnl = net_pnl
                best_exp = (sd_th, trend_gate, vol_gate, tot, wr, net_pnl, pf, trades)

    if best_exp:
        sd_th, trend_gate, vol_gate, tot, wr, net_pnl, pf, trades = best_exp
        print("\n" + "=" * 75)
        print(f"🏆 BEST EXPERIMENT: SD={sd_th}, TrendGate={trend_gate}, VolGate={vol_gate}")
        print(f"Total Trades: {tot}, Win Rate: {wr:.1f}%, Net PnL: ${net_pnl:+.2f}, PF: {pf:.2f}")
        print("=" * 75)
        
        for yr in sorted(list(set(t['year'] for t in trades))):
            y_trades = [t['pnl'] for t in trades if t['year'] == yr]
            y_wins = [p for p in y_trades if p > 0]
            y_loss = [abs(p) for p in y_trades if p < 0]
            y_net = sum(y_wins) - sum(y_loss)
            y_wr = len(y_wins) / len(y_trades) * 100.0 if y_trades else 0
            y_pf = sum(y_wins) / sum(y_loss) if sum(y_loss) > 0 else 99.0
            print(f"Year {yr} | Trades: {len(y_trades):<4d} | WR: {y_wr:<5.1f}% | Net PnL: ${y_net:<+8.2f} | PF: {y_pf:<4.2f}")

if __name__ == '__main__':
    test_regime_filtering()
