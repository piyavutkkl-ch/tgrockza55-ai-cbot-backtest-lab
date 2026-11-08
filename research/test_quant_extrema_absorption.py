import sys, os, csv, math
from collections import defaultdict
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from research.find_high_profit_strategy import load_data

def run_qea(symbol='XAUUSD', sl=3.5, rr=2.5, vwap_sd=1.0, min_wick=0.20, delta_thresh=5.0, use_be=True, be_r=1.0):
    bars = load_data(symbol)
    lot_multiplier = 1.0 if 'XAU' in symbol or 'GOLD' in symbol else 0.01
    spread_max = 0.15 if 'XAU' in symbol else (0.35 if 'GOLD' in symbol else 25.0)

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
        prev = bars[i-1]
        t = curr['time']
        close = curr['close']
        high = curr['high']
        low = curr['low']
        spread = curr['spreadAvg']
        delta = curr.get('delta', 0.0)
        prev_delta = prev.get('delta', 0.0)
        imb = curr.get('imbalance', 0.0)
        vwap = curr.get('vwapDay', close)
        sd = curr.get('sdDay', 3.5)
        ema50 = curr.get('ema50', close)
        ema200 = curr.get('ema200', close)

        # 1. Manage active position
        if pos is not None:
            side = pos['side']
            entry = pos['entry']

            # Breakeven lock
            if use_be and not pos['be_locked']:
                if side == 'Buy' and (high - entry) >= (pos['sl_dist'] * be_r):
                    pos['sl'] = entry + spread + 0.05
                    pos['be_locked'] = True
                elif side == 'Sell' and (entry - low) >= (pos['sl_dist'] * be_r):
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
                pnl = (exit_price - entry) * lot_multiplier if side == 'Buy' else (entry - exit_price) * lot_multiplier
                equity += pnl

                if reason == "StopLoss":
                    if side == 'Buy':
                        consec_buy_losses += 1
                        if consec_buy_losses >= 2: buy_cooldown_until = i + 30
                    else:
                        consec_sell_losses += 1
                        if consec_sell_losses >= 2: sell_cooldown_until = i + 30
                elif pnl > 0:
                    if side == 'Buy': consec_buy_losses = 0
                    else: consec_sell_losses = 0

                trades.append({
                    'id': len(trades) + 1,
                    'time_in': pos['entry_time'],
                    'time_out': t,
                    'side': side,
                    'entry': round(entry, 2),
                    'exit': round(exit_price, 2),
                    'pnl': round(pnl, 2),
                    'reason': reason,
                    'equity': round(equity, 2)
                })
                equity_curve.append({'time': t, 'equity': round(equity, 2)})
                pos = None

        # 2. Check Entry
        if pos is None:
            if spread > spread_max: continue

            candle_len = max(high - low, 0.01)
            lower_wick = (min(curr['open'], close) - low) / candle_len
            upper_wick = (high - max(curr['open'], close)) / candle_len

            recent_low = min(bars[k]['low'] for k in range(i-15, i))
            recent_high = max(bars[k]['high'] for k in range(i-15, i))
            lower_band = vwap - (sd * vwap_sd)
            upper_band = vwap + (sd * vwap_sd)

            # Turning Point Entry Criteria:
            # BUY: At Lower Band or Recent Low + Rejection Wick >= 20% + Delta Flip/Absorption + No Ask Wall
            buy_signal = ((low <= lower_band) or (low <= recent_low)) and \
                         (lower_wick >= min_wick) and \
                         (delta >= delta_thresh) and \
                         (delta - prev_delta >= 4.0) and \
                         (imb >= -0.03)

            # SELL: At Upper Band or Recent High + Rejection Wick >= 20% + Delta Absorption + No Bid Wall
            sell_signal = ((high >= upper_band) or (high >= recent_high)) and \
                          (upper_wick >= min_wick) and \
                          (delta <= -delta_thresh) and \
                          (delta - prev_delta <= -4.0) and \
                          (imb <= 0.03)

            # Macro Trend Filter
            if close > ema50 and ema50 > ema200:
                sell_signal = False
            elif close < ema50 and ema50 < ema200:
                buy_signal = False

            if buy_signal and i >= buy_cooldown_until:
                entry = close + spread
                sl_dist = sl
                tp_dist = sl * rr
                pos = {
                    'side': 'Buy', 'entry': entry, 'entry_time': t,
                    'sl': entry - sl_dist, 'tp': entry + tp_dist,
                    'sl_dist': sl_dist, 'be_locked': False
                }
            elif sell_signal and i >= sell_cooldown_until:
                entry = close
                sl_dist = sl
                tp_dist = sl * rr
                pos = {
                    'side': 'Sell', 'entry': entry, 'entry_time': t,
                    'sl': entry + sl_dist, 'tp': entry - tp_dist,
                    'sl_dist': sl_dist, 'be_locked': False
                }

    n = len(trades)
    if n == 0:
        return {'symbol': symbol, 'trades': 0, 'wins': 0, 'losses': 0, 'win_rate': 0.0, 'net_pnl': 0.0, 'pf': 0.0, 'max_dd': 0.0, 'trade_list': []}
    
    wins = [tr for tr in trades if tr['pnl'] > 0]
    losses = [tr for tr in trades if tr['pnl'] < 0]
    gross_win = sum(tr['pnl'] for tr in wins)
    gross_loss = abs(sum(tr['pnl'] for tr in losses))
    net_pnl = gross_win - gross_loss
    pf = (gross_win / gross_loss) if gross_loss > 0 else 99.0
    win_rate = len(wins) / n * 100.0

    peak = 100.0
    max_dd = 0.0
    for pt in equity_curve:
        if pt['equity'] > peak: peak = pt['equity']
        dd = peak - pt['equity']
        if dd > max_dd: max_dd = dd

    return {
        'symbol': symbol,
        'trades': n,
        'wins': len(wins),
        'losses': len(losses),
        'win_rate': round(win_rate, 1),
        'gross_win': round(gross_win, 2),
        'gross_loss': round(gross_loss, 2),
        'net_pnl': round(net_pnl, 2),
        'pf': round(pf, 2),
        'max_dd': round(max_dd, 2),
        'trade_list': trades,
        'equity_curve': equity_curve
    }

print("Running Quant Extrema Absorption Strategy across assets...")
res_xau = run_qea('XAUUSD', sl=3.5, rr=2.5, vwap_sd=1.0, min_wick=0.20, delta_thresh=5.0)
print(f"XAUUSD: {res_xau['trades']} trades | WR {res_xau['win_rate']}% ({res_xau['wins']}W / {res_xau['losses']}L) | Net: +${res_xau['net_pnl']} USD | PF: {res_xau['pf']} | Max DD: ${res_xau['max_dd']}")

res_gold = run_qea('GOLD-PERP', sl=3.5, rr=2.5, vwap_sd=1.0, min_wick=0.20, delta_thresh=5.0)
print(f"GOLD-PERP: {res_gold['trades']} trades | WR {res_gold['win_rate']}% ({res_gold['wins']}W / {res_gold['losses']}L) | Net: +${res_gold['net_pnl']} USD | PF: {res_gold['pf']} | Max DD: ${res_gold['max_dd']}")
