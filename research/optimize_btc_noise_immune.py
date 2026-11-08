import sys, os, csv
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from research.find_high_profit_strategy import load_data

bars = load_data('BTCUSD')

def test_btc_adaptive(bars, sl=150.0, rr=2.2, trend_filter=True, use_be=True):
    lot_multiplier = 0.01
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
        sd = curr.get('sdDay', 80.0)
        ema50 = curr.get('ema50', close)
        ema200 = curr.get('ema200', close)

        if pos is not None:
            side = pos['side']
            entry = pos['entry']

            # Breakeven lock
            if use_be and not pos['be_locked']:
                if side == 'Buy' and (high - entry) >= pos['sl_dist']:
                    pos['sl'] = entry + spread + 5.0
                    pos['be_locked'] = True
                elif side == 'Sell' and (entry - low) >= pos['sl_dist']:
                    pos['sl'] = entry - spread - 5.0
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
                        if consec_buy_losses >= 2: buy_cooldown_until = i + 30
                    else:
                        consec_buy_losses = 0

                    trades.append({'side': 'Buy', 'pnl': round(pnl, 2), 'reason': reason, 'equity': round(equity, 2)})
                    equity_curve.append({'time': t, 'equity': round(equity, 2)})
                    pos = None

            elif side == 'Sell':
                worst_ask = high + spread
                if worst_ask >= pos['sl']:
                    exit_trade = True
                    exit_price = pos['sl']
                    reason = "Breakeven" if pos['be_locked'] else "StopLoss"
                elif (low + spread) <= pos['tp']:
                    exit_trade = True
                    exit_price = pos['tp']
                    reason = "TakeProfit"

                if exit_trade:
                    pnl = (entry - exit_price) * lot_multiplier
                    equity += pnl
                    if reason == "StopLoss":
                        consec_sell_losses += 1
                        if consec_sell_losses >= 2: sell_cooldown_until = i + 30
                    else:
                        consec_sell_losses = 0

                    trades.append({'side': 'Sell', 'pnl': round(pnl, 2), 'reason': reason, 'equity': round(equity, 2)})
                    equity_curve.append({'time': t, 'equity': round(equity, 2)})
                    pos = None

        if pos is None:
            if spread > 20.0: continue # reject Asian night spikes

            upper_band = vwap + (sd * 1.5)
            lower_band = vwap - (sd * 1.5)
            recent_high = max(bars[k]['high'] for k in range(i-20, i))
            recent_low = min(bars[k]['low'] for k in range(i-20, i))
            prev_delta = bars[i-1].get('delta', 0.0)

            buy_signal = (low <= lower_band or low <= recent_low) and (delta >= 8) and (prev_delta <= 5)
            sell_signal = (high >= upper_band or high >= recent_high) and (delta <= -8) and (prev_delta >= -5)

            if trend_filter:
                if close > ema50 and ema50 > ema200: sell_signal = False
                elif close < ema50 and ema50 < ema200: buy_signal = False

            if buy_signal and i >= buy_cooldown_until:
                entry = close + spread
                pos = {'side': 'Buy', 'entry': entry, 'sl': entry - sl, 'tp': entry + (sl * rr), 'sl_dist': sl, 'be_locked': False}
            elif sell_signal and i >= sell_cooldown_until:
                entry = close
                pos = {'side': 'Sell', 'entry': entry, 'sl': entry + sl, 'tp': entry - (sl * rr), 'sl_dist': sl, 'be_locked': False}

    n = len(trades)
    if n == 0: return {'trades': 0, 'win_rate': 0, 'net_pnl': 0, 'pf': 0, 'max_dd': 0}
    wins = [tr for tr in trades if tr['pnl'] > 0]
    losses = [tr for tr in trades if tr['pnl'] < 0]
    gross_win = sum(tr['pnl'] for tr in wins)
    gross_loss = abs(sum(tr['pnl'] for tr in losses))
    net_pnl = gross_win - gross_loss
    pf = (gross_win / gross_loss) if gross_loss > 0 else 99.0

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
        'win_rate': round(len(wins)/n*100, 1),
        'gross_win': round(gross_win, 2),
        'gross_loss': round(gross_loss, 2),
        'net_pnl': round(net_pnl, 2),
        'pf': round(pf, 2),
        'max_dd': round(max_dd, 2)
    }

print("\n--- BTCUSD SWEEP: NOISE-IMMUNE SL SIZING (120 to 220 USD) ---")
print(f"{'SL ($)':<8} | {'RR':<5} | {'Trades':<7} | {'WinRate':<8} | {'Net PnL ($)':<12} | {'PF':<6} | {'MaxDD ($)':<9}")
print("-" * 65)

for sl in [120.0, 150.0, 180.0, 200.0, 220.0]:
    for rr in [1.8, 2.0, 2.2, 2.5]:
        res = test_btc_adaptive(bars, sl=sl, rr=rr, trend_filter=True, use_be=True)
        if res['trades'] > 0:
            print(f"${sl:<7.1f} | {rr:<5.1f} | {res['trades']:<7} | {res['win_rate']:<7.1f}% | ${res['net_pnl']:<11.2f} | {res['pf']:<6.2f} | ${res['max_dd']:<8.2f}")
