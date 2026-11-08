import sys, os, csv

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from research.find_high_profit_strategy import load_data
from research.test_trend_filter_full import test_5pillar_full

bars_btc = load_data('BTCUSD')
print(f"Loaded BTCUSD: {len(bars_btc)} bars from {bars_btc[0]['time']} to {bars_btc[-1]['time']}")

# For BTCUSD:
# SL = 70 USD, RR = 2.0 (TP = 140 USD)
# Spread limit = 22.0 USD (spread ceiling to reject Asian night spikes)
# Multiplier for 0.01 lot = 0.01 (1 USD move on 0.01 lot = $0.01 USD)
# Let's run simulation customized for BTCUSD
def test_btc_full(bars, sl=70.0, rr=2.0, max_losses=2, cooldown=30, trend_filter=True):
    lot_multiplier = 0.01 # 0.01 lot BTC
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
        sd = curr.get('sdDay', 60.0)
        ema50 = curr.get('ema50', close)
        ema200 = curr.get('ema200', close)

        # 1. Manage position
        if pos is not None:
            side = pos['side']
            entry = pos['entry']

            # Breakeven Lock at 1.0R
            if not pos['be_locked']:
                if side == 'Buy' and (high - entry) >= pos['sl_dist']:
                    pos['sl'] = entry + spread + 2.0
                    pos['be_locked'] = True
                elif side == 'Sell' and (entry - low) >= pos['sl_dist']:
                    pos['sl'] = entry - spread - 2.0
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
                    pnl = (exit_price - entry) * lot_multiplier
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
                    pnl = (entry - exit_price) * lot_multiplier
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
            if spread > 20.0: continue # Spread ceiling

            upper_band = vwap + (sd * 1.2)
            lower_band = vwap - (sd * 1.2)
            recent_high = max(bars[k]['high'] for k in range(i-20, i))
            recent_low = min(bars[k]['low'] for k in range(i-20, i))
            prev_delta = bars[i-1].get('delta', 0.0)

            buy_signal = (low <= lower_band or low <= recent_low) and (delta >= 5) and (prev_delta <= 5)
            sell_signal = (high >= upper_band or high >= recent_high) and (delta <= -5) and (prev_delta >= -5)

            if trend_filter:
                if close > ema50 and ema50 > ema200:
                    sell_signal = False
                elif close < ema50 and ema50 < ema200:
                    buy_signal = False

            if buy_signal and i >= buy_cooldown_until:
                entry = close + spread
                pos = {
                    'side': 'Buy',
                    'entry': entry,
                    'entry_time': t,
                    'sl': entry - sl,
                    'tp': entry + (sl * rr),
                    'sl_dist': sl,
                    'spread': spread,
                    'be_locked': False
                }
            elif sell_signal and i >= sell_cooldown_until:
                entry = close
                pos = {
                    'side': 'Sell',
                    'entry': entry,
                    'entry_time': t,
                    'sl': entry + sl,
                    'tp': entry - (sl * rr),
                    'sl_dist': sl,
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
        'trade_list': trades
    }

print("\n--- BTCUSD RESULTS ON FULL 3,785 BARS (NOV 1 - 5, 2026) ---")
res_btc_notf = test_btc_full(bars_btc, trend_filter=False)
print(f"WITHOUT Trend Filter: Trades={res_btc_notf['trades']} | WinRate={res_btc_notf['win_rate']}% | NetPnL=${res_btc_notf['net_pnl']} | PF={res_btc_notf['pf']} | MaxDD=${res_btc_notf['max_dd']}")

res_btc_tf = test_btc_full(bars_btc, trend_filter=True)
print(f"WITH Macro Trend Filter: Trades={res_btc_tf['trades']} | WinRate={res_btc_tf['win_rate']}% ({res_btc_tf['wins']}W / {res_btc_tf['losses']}L) | NetPnL=${res_btc_tf['net_pnl']} | PF={res_btc_tf['pf']} | MaxDD=${res_btc_tf['max_dd']}")
