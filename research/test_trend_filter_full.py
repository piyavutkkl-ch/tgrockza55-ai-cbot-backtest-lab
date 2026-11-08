import sys, os, csv

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from research.find_high_profit_strategy import load_data, simulate_strategy

bars = load_data('XAUUSD')
print(f"Loaded XAUUSD: {len(bars)} bars from {bars[0]['time']} to {bars[-1]['time']}")

# Run the 5-Pillar Model across the entire 4-day period
def test_5pillar_full(bars, vwap_sd_mult=1.2, sl=3.0, rr=2.0, max_losses=2, cooldown=30, trend_filter=True):
    lot_size = 0.01
    multiplier = 1.0
    
    trades = []
    equity = 100.0
    equity_curve = [{'time': bars[0]['time'], 'equity': equity}]
    pos = None

    consec_sell_losses = 0
    consec_buy_losses = 0
    sell_cooldown_until = -1
    buy_cooldown_until = -1

    for i in range(50, len(bars)):
        curr = bars[i]
        t = curr['time']
        close = curr['close']
        high = curr['high']
        low = curr['low']
        spread = curr['spreadAvg']
        delta = curr.get('delta', 0.0)
        vwap = curr.get('vwapDay', close)
        sd = curr.get('sdDay', 3.5)
        ema50 = curr.get('ema50', close)
        ema200 = curr.get('ema200', close)

        # 1. Manage position
        if pos is not None:
            side = pos['side']
            entry = pos['entry']
            cur_sl = pos['sl']
            cur_tp = pos['tp']

            # Breakeven Lock at 1.0R
            if not pos['be_locked']:
                if side == 'Buy' and (high - entry) >= pos['sl_dist']:
                    pos['sl'] = entry + spread + 0.05
                    pos['be_locked'] = True
                elif side == 'Sell' and (entry - low) >= pos['sl_dist']:
                    pos['sl'] = entry - spread - 0.05
                    pos['be_locked'] = True

            exit_trade = False
            exit_price = 0.0
            reason = ""

            if side == 'Buy':
                if low <= pos['sl']:
                    exit_trade = True
                    exit_price = pos['sl']
                    reason = "Breakeven" if pos['be_locked'] else "StopLoss"
                elif high >= pos['tp']:
                    exit_trade = True
                    exit_price = pos['tp']
                    reason = "TakeProfit"

                if exit_trade:
                    pnl = (exit_price - entry) * multiplier
                    equity += pnl
                    if reason == "StopLoss":
                        consec_buy_losses += 1
                        if consec_buy_losses >= max_losses:
                            buy_cooldown_until = i + cooldown
                    else:
                        consec_buy_losses = 0

                    trades.append({
                        'id': len(trades) + 1,
                        'time_in': pos['entry_time'],
                        'time_out': t,
                        'side': 'Buy',
                        'entry': round(entry, 2),
                        'exit': round(exit_price, 2),
                        'pnl': round(pnl, 2),
                        'reason': reason,
                        'spread': pos['spread'],
                        'equity': round(equity, 2)
                    })
                    equity_curve.append({'time': t, 'equity': round(equity, 2)})
                    pos = None

            elif side == 'Sell':
                worst_ask = high + spread
                best_ask = low + spread

                if worst_ask >= pos['sl']:
                    exit_trade = True
                    exit_price = pos['sl']
                    reason = "Breakeven" if pos['be_locked'] else "StopLoss"
                elif best_ask <= pos['tp']:
                    exit_trade = True
                    exit_price = pos['tp']
                    reason = "TakeProfit"

                if exit_trade:
                    pnl = (entry - exit_price) * multiplier
                    equity += pnl
                    if reason == "StopLoss":
                        consec_sell_losses += 1
                        if consec_sell_losses >= max_losses:
                            sell_cooldown_until = i + cooldown
                    else:
                        consec_sell_losses = 0

                    trades.append({
                        'id': len(trades) + 1,
                        'time_in': pos['entry_time'],
                        'time_out': t,
                        'side': 'Sell',
                        'entry': round(entry, 2),
                        'exit': round(exit_price, 2),
                        'pnl': round(pnl, 2),
                        'reason': reason,
                        'spread': pos['spread'],
                        'equity': round(equity, 2)
                    })
                    equity_curve.append({'time': t, 'equity': round(equity, 2)})
                    pos = None

        # 2. Check Entry
        if pos is None:
            if spread > 0.15: continue

            upper_band = vwap + (sd * vwap_sd_mult)
            lower_band = vwap - (sd * vwap_sd_mult)
            recent_high = max(bars[k]['high'] for k in range(i-15, i))
            recent_low = min(bars[k]['low'] for k in range(i-15, i))
            prev_delta = bars[i-1].get('delta', 0.0)

            buy_signal = (low <= lower_band or low <= recent_low) and (delta >= 5) and (prev_delta <= 5)
            sell_signal = (high >= upper_band or high >= recent_high) and (delta <= -5) and (prev_delta >= -5)

            # Trend Filter: don't short when massive bull trend (Price > EMA50 > EMA200)
            if trend_filter:
                if close > ema50 and ema50 > ema200:
                    sell_signal = False # strictly no counter-trend shorts in macro bull!
                elif close < ema50 and ema50 < ema200:
                    buy_signal = False # strictly no counter-trend longs in macro bear!

            if buy_signal and i >= buy_cooldown_until:
                entry = close + spread
                sl_dist = sl
                tp_dist = sl * rr
                pos = {
                    'side': 'Buy',
                    'entry': entry,
                    'entry_time': t,
                    'sl': entry - sl_dist,
                    'tp': entry + tp_dist,
                    'sl_dist': sl_dist,
                    'spread': spread,
                    'be_locked': False
                }
            elif sell_signal and i >= sell_cooldown_until:
                entry = close
                sl_dist = sl
                tp_dist = sl * rr
                pos = {
                    'side': 'Sell',
                    'entry': entry,
                    'entry_time': t,
                    'sl': entry + sl_dist,
                    'tp': entry - tp_dist,
                    'sl_dist': sl_dist,
                    'spread': spread,
                    'be_locked': False
                }

    n = len(trades)
    wins = [tr for tr in trades if tr['pnl'] > 0]
    losses = [tr for tr in trades if tr['pnl'] < 0]
    gross_win = sum(tr['pnl'] for tr in wins)
    gross_loss = abs(sum(tr['pnl'] for tr in losses))
    net_pnl = gross_win - gross_loss
    pf = (gross_win / gross_loss) if gross_loss > 0 else 99.0
    win_rate = len(wins) / n * 100.0 if n > 0 else 0

    peak = 100.0
    max_dd = 0.0
    for pt in equity_curve:
        if pt['equity'] > peak: peak = pt['equity']
        dd = peak - pt['equity']
        if dd > max_dd: max_dd = dd

    return {
        'trades': n,
        'wins': len(wins),
        'losses': len(losses),
        'win_rate': round(win_rate, 1),
        'gross_win': round(gross_win, 2),
        'gross_loss': round(gross_loss, 2),
        'net_pnl': round(net_pnl, 2),
        'pf': round(pf, 2),
        'max_dd': round(max_dd, 2),
        'equity_curve': equity_curve,
        'trade_list': trades
    }

print("\n--- BENCHMARK: WITHOUT TREND FILTER vs WITH MACRO TREND FILTER ---")
res_no_tf = test_5pillar_full(bars, trend_filter=False)
print(f"WITHOUT Trend Filter (Fades All):")
print(f"  Trades: {res_no_tf['trades']} | Win Rate: {res_no_tf['win_rate']}% ({res_no_tf['wins']}W / {res_no_tf['losses']}L)")
print(f"  Gross Win: +${res_no_tf['gross_win']} | Gross Loss: -${res_no_tf['gross_loss']}")
print(f"  Net PnL: +${res_no_tf['net_pnl']} USD | PF: {res_no_tf['pf']} | Max DD: ${res_no_tf['max_dd']} USD")

res_with_tf = test_5pillar_full(bars, trend_filter=True)
print(f"\nWITH Macro Trend Filter (No counter-trend fading into mega trend):")
print(f"  Trades: {res_with_tf['trades']} | Win Rate: {res_with_tf['win_rate']}% ({res_with_tf['wins']}W / {res_with_tf['losses']}L)")
print(f"  Gross Win: +${res_with_tf['gross_win']} | Gross Loss: -${res_with_tf['gross_loss']}")
print(f"  Net PnL: +${res_with_tf['net_pnl']} USD | PF: {res_with_tf['pf']} | Max DD: ${res_with_tf['max_dd']} USD")
