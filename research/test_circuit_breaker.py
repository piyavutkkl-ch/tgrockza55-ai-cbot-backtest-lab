import sys, os, csv

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from research.simulate_xau_5pillar_today import sorted_bars

def run_simulation_with_circuit_breaker(bars, config):
    vwap_sd_mult = config.get('vwap_sd_mult', 1.2)
    sl_usd = config.get('sl_usd', 3.0)
    rr = config.get('rr', 2.0) # TP = sl_usd * rr
    spread_gate = config.get('spread_gate', 0.14)
    use_be = config.get('use_be', True)
    be_trigger_r = config.get('be_trigger_r', 1.0)
    max_consec_dir_loss = config.get('max_consec_dir_loss', 2)
    cooldown_bars = config.get('cooldown_bars', 30)

    trades = []
    equity = 100.0
    equity_curve = [{'time': bars[0]['time'], 'equity': equity}]
    pos = None

    consec_sell_losses = 0
    consec_buy_losses = 0
    sell_cooldown_until = -1
    buy_cooldown_until = -1

    for i in range(20, len(bars)):
        curr = bars[i]
        t = curr['time']
        close = curr['close']
        high = curr['high']
        low = curr['low']
        spread = curr['spreadAvg']
        delta = curr.get('delta', 0.0)
        vwap = curr.get('vwapDay', close)
        sd = curr.get('sdDay', 3.5)

        # 1. Manage open position
        if pos is not None:
            side = pos['side']
            entry = pos['entry']
            cur_sl = pos['sl']
            cur_tp = pos['tp']

            if use_be and not pos['be_locked']:
                if side == 'Buy' and (high - entry) >= (pos['init_sl'] * be_trigger_r):
                    pos['sl'] = entry + spread + 0.05
                    pos['be_locked'] = True
                elif side == 'Sell' and (entry - low) >= (pos['init_sl'] * be_trigger_r):
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
                    pnl = (exit_price - entry) * 1.0
                    equity += pnl
                    if reason == "StopLoss":
                        consec_buy_losses += 1
                        if consec_buy_losses >= max_consec_dir_loss:
                            buy_cooldown_until = i + cooldown_bars
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
                    pnl = (entry - exit_price) * 1.0
                    equity += pnl
                    if reason == "StopLoss":
                        consec_sell_losses += 1
                        if consec_sell_losses >= max_consec_dir_loss:
                            sell_cooldown_until = i + cooldown_bars
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

        # 2. Check Entry Signal if Flat
        if pos is None:
            if spread > spread_gate:
                continue

            upper_band = vwap + (sd * vwap_sd_mult)
            lower_band = vwap - (sd * vwap_sd_mult)
            recent_high = max(bars[k]['high'] for k in range(i-15, i))
            recent_low = min(bars[k]['low'] for k in range(i-15, i))
            prev_delta = bars[i-1].get('delta', 0.0)

            buy_signal = (low <= lower_band or low <= recent_low) and (delta >= 5) and (prev_delta <= 5)
            sell_signal = (high >= upper_band or high >= recent_high) and (delta <= -5) and (prev_delta >= -5)

            # Check cooldown circuit breaker
            if buy_signal and i >= buy_cooldown_until:
                entry = close + spread
                sl = entry - sl_usd
                tp = entry + (sl_usd * rr)
                pos = {
                    'side': 'Buy',
                    'entry': entry,
                    'entry_time': t,
                    'sl': sl,
                    'tp': tp,
                    'init_sl': sl_usd,
                    'spread': spread,
                    'be_locked': False
                }
            elif sell_signal and i >= sell_cooldown_until:
                entry = close
                sl = entry + sl_usd
                tp = entry - (sl_usd * rr)
                pos = {
                    'side': 'Sell',
                    'entry': entry,
                    'entry_time': t,
                    'sl': sl,
                    'tp': tp,
                    'init_sl': sl_usd,
                    'spread': spread,
                    'be_locked': False
                }

    n_trades = len(trades)
    wins = [t for t in trades if t['pnl'] > 0]
    losses = [t for t in trades if t['pnl'] < 0]
    gross_profit = sum(t['pnl'] for t in wins)
    gross_loss = abs(sum(t['pnl'] for t in losses))
    net_pnl = gross_profit - gross_loss
    pf = (gross_profit / gross_loss) if gross_loss > 0 else 99.0
    win_rate = len(wins) / n_trades * 100.0

    peak = 100.0
    max_dd = 0.0
    for pt in equity_curve:
        if pt['equity'] > peak: peak = pt['equity']
        dd = peak - pt['equity']
        if dd > max_dd: max_dd = dd

    return {
        'trades': n_trades,
        'wins': len(wins),
        'losses': len(losses),
        'win_rate': round(win_rate, 1),
        'net_pnl': round(net_pnl, 2),
        'gross_profit': round(gross_profit, 2),
        'gross_loss': round(gross_loss, 2),
        'pf': round(pf, 2),
        'max_dd': round(max_dd, 2),
        'trade_list': trades,
        'equity_curve': equity_curve
    }

cfg = {
    'vwap_sd_mult': 1.2,
    'sl_usd': 3.0,
    'rr': 2.0,
    'spread_gate': 0.14,
    'use_be': True,
    'be_trigger_r': 1.0,
    'max_consec_dir_loss': 2,
    'cooldown_bars': 30
}

res = run_simulation_with_circuit_breaker(sorted_bars, cfg)
print("================================================================================")
print("     WITH DIRECTIONAL CIRCUIT BREAKER (Freeze on 2 consecutive losses)          ")
print("================================================================================")
print(f"Total Trades: {res['trades']} | Win Rate: {res['win_rate']}% ({res['wins']}W / {res['losses']}L)")
print(f"Gross Profit: +${res['gross_profit']} | Gross Loss: -${res['gross_loss']}")
print(f"Net Profit: +${res['net_pnl']} USD | Profit Factor: {res['pf']} | Max DD: ${res['max_dd']} USD")
print("================================================================================")
print("\nLast 10 trades:")
for tr in res['trade_list'][-10:]:
    print(f"Trade #{tr['id']:02d} | {tr['side']:<4} | In: {tr['time_in']} @ ${tr['entry']:.2f} | Out: {tr['time_out']} @ ${tr['exit']:.2f} | {tr['reason']:<11} | PnL: ${tr['pnl']:+.2f} | Eq: ${tr['equity']:.2f}")
