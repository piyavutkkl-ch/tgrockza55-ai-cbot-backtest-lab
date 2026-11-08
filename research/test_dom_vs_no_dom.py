import sys, os, csv

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from research.find_high_profit_strategy import load_data

bars = load_data('XAUUSD')

def run_experiment(bars, use_delta=True, use_dom=False, use_pure_price=False):
    lot_multiplier = 1.0 # 0.01 lot XAU
    sl = 3.0
    rr = 2.0
    max_losses = 2
    cooldown = 30
    
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
        prev_delta = bars[i-1].get('delta', 0.0)
        imb = curr.get('imbalance', 0.0)
        vwap = curr.get('vwapDay', close)
        sd = curr.get('sdDay', 3.5)
        ema50 = curr.get('ema50', close)
        ema200 = curr.get('ema200', close)

        # 1. Manage position
        if pos is not None:
            side = pos['side']
            entry = pos['entry']

            # Breakeven lock at +1.0R
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
                    pnl = (exit_price - entry) * lot_multiplier
                    equity += pnl
                    if reason == "StopLoss":
                        consec_buy_losses += 1
                        if consec_buy_losses >= max_losses: buy_cooldown_until = i + cooldown
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
                        if consec_sell_losses >= max_losses: sell_cooldown_until = i + cooldown
                    else:
                        consec_sell_losses = 0

                    trades.append({'side': 'Sell', 'pnl': round(pnl, 2), 'reason': reason, 'equity': round(equity, 2)})
                    equity_curve.append({'time': t, 'equity': round(equity, 2)})
                    pos = None

        # 2. Entry signal
        if pos is None:
            if spread > 0.15: continue

            upper_band = vwap + (sd * 1.2)
            lower_band = vwap - (sd * 1.2)
            recent_high = max(bars[k]['high'] for k in range(i-15, i))
            recent_low = min(bars[k]['low'] for k in range(i-15, i))

            # Base price location
            buy_signal = (low <= lower_band or low <= recent_low)
            sell_signal = (high >= upper_band or high >= recent_high)

            # Option A: With Delta (Order Flow execution)
            if use_delta:
                buy_signal = buy_signal and (delta >= 5 and prev_delta <= 5)
                sell_signal = sell_signal and (delta <= -5 and prev_delta >= -5)

            # Option B: With DOM (L2 Limit Order Imbalance)
            if use_dom:
                buy_signal = buy_signal and (imb >= 0.02)
                sell_signal = sell_signal and (imb <= -0.02)

            # Option C: Pure Price (Reversal pinbar / close confirmation)
            if use_pure_price:
                # Buy when bar closes green after touching low
                buy_signal = buy_signal and (close > curr['open'])
                # Sell when bar closes red after touching high
                sell_signal = sell_signal and (close < curr['open'])

            # Macro Trend Filter
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

print("================================================================================")
print("     EXPERIMENT: DOES THIS STRATEGY REQUIRE DOM (LEVEL 2 ORDER BOOK)?           ")
print("================================================================================")

# 1. With Order Flow Delta (No DOM required)
res_delta = run_experiment(bars, use_delta=True, use_dom=False, use_pure_price=False)
print(f"1. With Volume Delta ONLY (No DOM needed - uses Ticks/Tape):")
print(f"   Trades: {res_delta['trades']} | Win Rate: {res_delta['win_rate']}% ({res_delta['wins']}W / {res_delta['losses']}L)")
print(f"   Net PnL: +${res_delta['net_pnl']} USD | Profit Factor: {res_delta['pf']} | Max DD: ${res_delta['max_dd']} USD")

# 2. Pure Price Action + VWAP (No Delta, No DOM at all!)
res_price = run_experiment(bars, use_delta=False, use_dom=False, use_pure_price=True)
print(f"\n2. Pure Price Action + VWAP (NO DOM, NO Delta - works on standard bars):")
print(f"   Trades: {res_price['trades']} | Win Rate: {res_price['win_rate']}% ({res_price['wins']}W / {res_price['losses']}L)")
print(f"   Net PnL: +${res_price['net_pnl']} USD | Profit Factor: {res_price['pf']} | Max DD: ${res_price['max_dd']} USD")

# 3. Adding DOM Level 2 Imbalance on top
res_dom = run_experiment(bars, use_delta=True, use_dom=True, use_pure_price=False)
print(f"\n3. With Volume Delta + DOM Level 2 (Both active):")
print(f"   Trades: {res_dom['trades']} | Win Rate: {res_dom['win_rate']}% ({res_dom['wins']}W / {res_dom['losses']}L)")
print(f"   Net PnL: +${res_dom['net_pnl']} USD | Profit Factor: {res_dom['pf']} | Max DD: ${res_dom['max_dd']} USD")
