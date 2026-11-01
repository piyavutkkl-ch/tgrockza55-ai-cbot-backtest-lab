import sys
import csv
sys.path.append(r'd:\cbot-atgvt\research')
from test_vwap_scalp import btc_min, btc_flow

# Backtest: Trend Pullback (Fibo 50-61.8% + VWAP) during idle periods
def backtest_trend_pullback(min_rows, flow_map, spread_cost=0.15):
    trades = []
    position = None
    trade_id = 0
    
    for i in range(25, len(min_rows)):
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
        
        # Check trend via VWAP
        if t in flow_map:
            vwap = float(flow_map[t].get('vwapDay', c))
            
            # Find recent swing high and low in last 20 bars
            h20 = max(float(min_rows[j]['high']) for j in range(i-20, i))
            l20 = min(float(min_rows[j]['low']) for j in range(i-20, i))
            swing_range = h20 - l20
            
            if swing_range >= 80.0: # Minimum swing size on BTC
                # Bullish Pullback: Price is above VWAP (uptrend), but has pulled back to 50%-65% of the swing
                fibo_50 = h20 - (swing_range * 0.50)
                fibo_65 = h20 - (swing_range * 0.65)
                
                imb = float(row.get('imbalance', 0)) if 'imbalance' in row else 0.0
                
                if c >= vwap and l <= fibo_50 and c >= fibo_65 and imb >= -0.005:
                    trade_id += 1
                    tp_target = h20
                    sl_target = l20 - 10.0
                    if (tp_target - c) >= 45.0 and (c - sl_target) <= 30.0:
                        position = {
                            'id': trade_id, 'side': 'Buy', 'entry_p': c, 'entry_t': t,
                            'tp': tp_target, 'sl': sl_target, 'idx': i
                        }
                        continue
                        
                # Bearish Pullback: Price is below VWAP (downtrend), but has bounced up to 50%-65% of the swing
                fibo_bounce_50 = l20 + (swing_range * 0.50)
                fibo_bounce_65 = l20 + (swing_range * 0.65)
                
                if c <= vwap and h >= fibo_bounce_50 and c <= fibo_bounce_65 and imb <= 0.005:
                    trade_id += 1
                    tp_target = l20
                    sl_target = h20 + 10.0
                    if (c - tp_target) >= 45.0 and (sl_target - c) <= 30.0:
                        position = {
                            'id': trade_id, 'side': 'Sell', 'entry_p': c, 'entry_t': t,
                            'tp': tp_target, 'sl': sl_target, 'idx': i
                        }
                        continue

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

r = backtest_trend_pullback(btc_min, btc_flow)
print(f"=== Trend Fibo Pullback on BTCUSD during Idle ===")
print(f"Trades = {r['count']}, Win Rate = {r['win_rate']:.1f}%, Net PnL = +${r['net_pnl']:.2f}, PF = {r['pf']:.2f}")
for tr in r['trades']:
    print(f"  Trade #{tr['id']:2d} | {tr['entry_t']} -> {tr['exit_t']} | {tr['side']:4s} | Net=+${tr['net']:5.2f} | Reason={tr['reason']} ({tr['dur']}m)")
