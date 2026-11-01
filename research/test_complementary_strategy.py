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

# Backtest Complementary Strategy: CVD Momentum Breakout during Idle
def backtest_cvd_momentum(min_rows, flow_map, sym, cvd_thresh, tp_usd, sl_usd, spread_cost):
    trades = []
    position = None # {side, entry_p, entry_t, tp, sl, id}
    trade_id = 0
    equity = 100.0
    
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
                    
            # Max hold 30 mins
            if exit_p is None and (i - position['idx']) >= 30:
                exit_p = c
                reason = 'TIME_STOP'
                
            if exit_p is not None:
                if side == 'Buy':
                    gross = (exit_p - position['entry_p']) * (0.01 if 'BTC' in sym else 0.1)
                else:
                    gross = (position['entry_p'] - exit_p) * (0.01 if 'BTC' in sym else 0.1)
                net = gross - spread_cost
                equity += net
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

        # If already in position, do not open another
        if position is not None:
            continue
            
        # Entry logic: CVD Momentum Breakout
        # 1. Rolling 15m high/low
        h15 = max(float(min_rows[j]['high']) for j in range(i-15, i))
        l15 = min(float(min_rows[j]['low']) for j in range(i-15, i))
        
        # 2. CVD velocity in last 3 min
        if t in flow_map and min_rows[i-3]['time'] in flow_map:
            cvd_now = float(flow_map[t].get('cvd', 0))
            cvd_prev = float(flow_map[min_rows[i-3]['time']].get('cvd', 0))
            cvd_delta = cvd_now - cvd_prev
            
            # Buy breakout: price breaks above 15m high + strong positive CVD delta
            if c > h15 and cvd_delta >= cvd_thresh:
                trade_id += 1
                position = {
                    'id': trade_id,
                    'side': 'Buy',
                    'entry_p': c,
                    'entry_t': t,
                    'tp': c + tp_usd,
                    'sl': c - sl_usd,
                    'idx': i
                }
            # Sell breakout: price breaks below 15m low + strong negative CVD delta
            elif c < l15 and cvd_delta <= -cvd_thresh:
                trade_id += 1
                position = {
                    'id': trade_id,
                    'side': 'Sell',
                    'entry_p': c,
                    'entry_t': t,
                    'tp': c - tp_usd,
                    'sl': c + sl_usd,
                    'idx': i
                }
                
    wins = [tr for tr in trades if tr['net'] > 0]
    losses = [tr for tr in trades if tr['net'] <= 0]
    win_rate = (len(wins) / len(trades) * 100) if trades else 0
    total_net = sum(tr['net'] for tr in trades)
    gross_win = sum(tr['net'] for tr in wins)
    gross_loss = abs(sum(tr['net'] for tr in losses))
    pf = (gross_win / gross_loss) if gross_loss > 0 else 99.0
    
    return {
        'trades': trades,
        'count': len(trades),
        'win_rate': win_rate,
        'net_pnl': total_net,
        'pf': pf
    }

# Run parameter scans
print("Testing CVD Momentum Breakout on BTCUSD:")
for thresh in [150, 250, 400]:
    for tp in [60.0, 90.0, 120.0]:
        for sl in [30.0, 45.0]:
            res = backtest_cvd_momentum(btc_min, btc_flow, 'BTCUSD', thresh, tp, sl, spread_cost=0.15)
            if res['count'] >= 3 and res['net_pnl'] > 0:
                print(f"Thresh={thresh:3d} TP={tp:5.1f} SL={sl:4.1f} | Trades={res['count']:2d} WR={res['win_rate']:5.1f}% Net=+${res['net_pnl']:6.2f} PF={res['pf']:5.2f}")

print("\nTesting CVD Momentum Breakout on ETHUSD:")
for thresh in [50, 100, 150]:
    for tp in [4.0, 6.0, 8.0]:
        for sl in [2.0, 3.0]:
            res = backtest_cvd_momentum(eth_min, eth_flow, 'ETHUSD', thresh, tp, sl, spread_cost=0.03)
            if res['count'] >= 3 and res['net_pnl'] > 0:
                print(f"Thresh={thresh:3d} TP={tp:5.1f} SL={sl:4.1f} | Trades={res['count']:2d} WR={res['win_rate']:5.1f}% Net=+${res['net_pnl']:6.2f} PF={res['pf']:5.2f}")
