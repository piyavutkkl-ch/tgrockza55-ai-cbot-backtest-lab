import sys
import csv
import math
sys.path.append(r'd:\cbot-atgvt\research')
from test_vwap_scalp import btc_min, btc_flow

# Backtest: Market Profile Value Area (VAH/VAL) Reversal on BTC during Idle
def backtest_value_area_reversal(min_rows, flow_map, tp_usd, sl_usd, spread_cost=0.15):
    trades = []
    position = None
    trade_id = 0
    
    for i in range(20, len(min_rows)):
        row = min_rows[i]
        t = row['time']
        c = float(row['close'])
        h = float(row['high'])
        l = float(row['low'])
        
        # Exit check
        if position is not None:
            side = position['side']
            exit_p = None
            reason = None
            
            if side == 'Buy':
                if h >= position['tp']: exit_p = position['tp']; reason = 'TP'
                elif l <= position['sl']: exit_p = position['sl']; reason = 'SL'
            else:
                if l <= position['tp']: exit_p = position['tp']; reason = 'TP'
                elif h >= position['sl']: exit_p = position['sl']; reason = 'SL'
                
            if exit_p is None and (i - position['idx']) >= 35:
                exit_p = c
                reason = 'TIME_STOP'
                
            if exit_p is not None:
                gross = (exit_p - position['entry_p']) * 0.01 if side == 'Buy' else (position['entry_p'] - exit_p) * 0.01
                net = gross - spread_cost
                trades.append({
                    'id': position['id'], 'entry_t': position['entry_t'], 'exit_t': t,
                    'side': side, 'net': net, 'reason': reason, 'dur': i - position['idx']
                })
                position = None
                continue

        if position is not None: continue
        
        if t in flow_map:
            fl = flow_map[t]
            vah = float(fl.get('vah', 0))
            val = float(fl.get('val', 0))
            poc = float(fl.get('poc', 0))
            imb = float(row.get('imbalance', 0)) if 'imbalance' in row else 0.0
            
            if vah > 0 and val > 0:
                # Test VAH rejection (Price touches VAH and rejects downwards)
                if abs(c - vah) <= 25 and c < vah and imb <= -0.02:
                    trade_id += 1
                    position = {
                        'id': trade_id, 'side': 'Sell', 'entry_p': c, 'entry_t': t,
                        'tp': c - tp_usd, 'sl': c + sl_usd, 'idx': i
                    }
                # Test VAL rejection (Price touches VAL and bounces upwards)
                elif abs(c - val) <= 25 and c > val and imb >= 0.02:
                    trade_id += 1
                    position = {
                        'id': trade_id, 'side': 'Buy', 'entry_p': c, 'entry_t': t,
                        'tp': c + tp_usd, 'sl': c - sl_usd, 'idx': i
                    }

    wins = [tr for tr in trades if tr['net'] > 0]
    losses = [tr for tr in trades if tr['net'] <= 0]
    win_rate = (len(wins) / len(trades) * 100) if trades else 0
    total_net = sum(tr['net'] for tr in trades)
    gross_win = sum(tr['net'] for tr in wins)
    gross_loss = abs(sum(tr['net'] for tr in losses))
    pf = (gross_win / gross_loss) if gross_loss > 0 else (99.0 if gross_win > 0 else 0)
    
    return {
        'trades': trades, 'count': len(trades), 'win_rate': win_rate,
        'net_pnl': total_net, 'pf': pf
    }

print("=== Value Area (VAH/VAL) Reversal on BTCUSD ===")
for tp in [50.0, 70.0, 90.0]:
    for sl in [25.0, 35.0, 45.0]:
        r = backtest_value_area_reversal(btc_min, btc_flow, tp, sl)
        print(f"TP={tp:4.1f} SL={sl:4.1f} | Trades={r['count']:2d} WR={r['win_rate']:5.1f}% Net=+${r['net_pnl']:5.2f} PF={r['pf']:5.2f}")
