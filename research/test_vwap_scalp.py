import os
import csv
import math

base = os.path.expandvars(r'%LOCALAPPDATA%\BacktestLab\live')

def load_dataset(sym):
    min_rows = []
    flow_map = {}
    for fn in ['min-2026-10.csv', 'min-2026-11.csv']:
        p = os.path.join(base, sym, fn)
        if os.path.exists(p):
            with open(p, 'r', encoding='utf-8') as f:
                min_rows.extend(list(csv.DictReader(f)))
    for fn in ['flow-2026-10.csv', 'flow-2026-11.csv']:
        p = os.path.join(base, sym, fn)
        if os.path.exists(p):
            with open(p, 'r', encoding='utf-8') as f:
                for r in csv.DictReader(f):
                    flow_map[r['time']] = r
    return min_rows, flow_map

btc_min, btc_flow = load_dataset('BTCUSD')
eth_min, eth_flow = load_dataset('ETHUSD')

# Backtest: Mid-Range VWAP Reversion Scalp during DOM_ABSORPTION Idle periods
def backtest_vwap_scalp(min_rows, flow_map, sym, dev_thresh, tp_ratio, sl_ratio, spread_cost):
    trades = []
    position = None
    trade_id = 0
    
    for i in range(20, len(min_rows)):
        row = min_rows[i]
        t = row['time']
        c = float(row['close'])
        h = float(row['high'])
        l = float(row['low'])
        
        # Check open position exit
        if position is not None:
            side = position['side']
            exit_p = None
            reason = None
            
            if side == 'Buy':
                if h >= position['tp']:
                    exit_p = position['tp']
                    reason = 'TP'
                elif l <= position['sl']:
                    exit_p = position['sl']
                    reason = 'SL'
            else: # Sell
                if l <= position['tp']:
                    exit_p = position['tp']
                    reason = 'TP'
                elif h >= position['sl']:
                    exit_p = position['sl']
                    reason = 'SL'
                    
            # Max hold 25 mins
            if exit_p is None and (i - position['idx']) >= 25:
                exit_p = c
                reason = 'TIME_STOP'
                
            if exit_p is not None:
                if side == 'Buy':
                    gross = (exit_p - position['entry_p']) * (0.01 if 'BTC' in sym else 0.1)
                else:
                    gross = (position['entry_p'] - exit_p) * (0.01 if 'BTC' in sym else 0.1)
                net = gross - spread_cost
                trades.append({
                    'id': position['id'],
                    'entry_t': position['entry_t'],
                    'exit_t': t,
                    'side': side,
                    'entry_p': position['entry_p'],
                    'exit_p': exit_p,
                    'net': net,
                    'reason': reason,
                    'dur': i - position['idx']
                })
                position = None
                continue

        if position is not None:
            continue
            
        # Entry logic: Mid-Range VWAP Mean Reversion
        # Avoid the extreme edges (where DOM_ABSORPTION operates!)
        h15 = max(float(min_rows[j]['high']) for j in range(i-15, i))
        l15 = min(float(min_rows[j]['low']) for j in range(i-15, i))
        
        # Condition: price is NOT near 15m high/low (more than 10% away from edges)
        range_15 = h15 - l15
        if range_15 <= 0: continue
        
        edge_buffer = range_15 * 0.12
        if c >= h15 - edge_buffer or c <= l15 + edge_buffer:
            # This is DOM_ABSORPTION territory, skip!
            continue
            
        if t in flow_map:
            vwap = float(flow_map[t].get('vwapDay', c))
            dist = c - vwap
            
            # If price stretched above VWAP by dev_thresh -> Sell back toward VWAP
            if dist >= dev_thresh:
                trade_id += 1
                tp_dist = dist * tp_ratio
                sl_dist = dist * sl_ratio
                position = {
                    'id': trade_id,
                    'side': 'Sell',
                    'entry_p': c,
                    'entry_t': t,
                    'tp': c - tp_dist,
                    'sl': c + sl_dist,
                    'idx': i
                }
            # If price stretched below VWAP by dev_thresh -> Buy back toward VWAP
            elif dist <= -dev_thresh:
                trade_id += 1
                tp_dist = abs(dist) * tp_ratio
                sl_dist = abs(dist) * sl_ratio
                position = {
                    'id': trade_id,
                    'side': 'Buy',
                    'entry_p': c,
                    'entry_t': t,
                    'tp': c + tp_dist,
                    'sl': c - sl_dist,
                    'idx': i
                }

    wins = [tr for tr in trades if tr['net'] > 0]
    losses = [tr for tr in trades if tr['net'] <= 0]
    win_rate = (len(wins) / len(trades) * 100) if trades else 0
    total_net = sum(tr['net'] for tr in trades)
    gross_win = sum(tr['net'] for tr in wins)
    gross_loss = abs(sum(tr['net'] for tr in losses))
    pf = (gross_win / gross_loss) if gross_loss > 0 else (99.0 if gross_win > 0 else 0)
    
    return {
        'trades': trades,
        'count': len(trades),
        'win_rate': win_rate,
        'net_pnl': total_net,
        'pf': pf
    }

print("=== Scanning Mid-Range VWAP Scalp on BTCUSD ===")
for dev in [50, 75, 100, 125]:
    for tp_r in [0.4, 0.6, 0.8]:
        for sl_r in [0.5, 0.8, 1.0]:
            r = backtest_vwap_scalp(btc_min, btc_flow, 'BTCUSD', dev, tp_r, sl_r, spread_cost=0.15)
            if r['count'] >= 5 and r['net_pnl'] > 2.0:
                print(f"Dev={dev:3d} TP_R={tp_r:.1f} SL_R={sl_r:.1f} | Trades={r['count']:2d} WR={r['win_rate']:5.1f}% Net=+${r['net_pnl']:5.2f} PF={r['pf']:5.2f}")

print("\n=== Scanning Mid-Range VWAP Scalp on ETHUSD ===")
for dev in [3.0, 4.5, 6.0, 8.0]:
    for tp_r in [0.4, 0.6, 0.8]:
        for sl_r in [0.5, 0.8, 1.0]:
            r = backtest_vwap_scalp(eth_min, eth_flow, 'ETHUSD', dev, tp_r, sl_r, spread_cost=0.03)
            if r['count'] >= 5 and r['net_pnl'] > 2.0:
                print(f"Dev={dev:4.1f} TP_R={tp_r:.1f} SL_R={sl_r:.1f} | Trades={r['count']:2d} WR={r['win_rate']:5.1f}% Net=+${r['net_pnl']:5.2f} PF={r['pf']:5.2f}")
