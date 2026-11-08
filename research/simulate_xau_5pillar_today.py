import sys, os, csv
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')

base = r'C:\Users\Strong Baesus PC1\AppData\Local\BacktestLab\live\XAUUSD'
min_file = os.path.join(base, 'min-2026-11.csv')
flow_file = os.path.join(base, 'flow-2026-11.csv')

# Load and merge data
bars = {}
with open(min_file, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for r in reader:
        t = r['time']
        bars[t] = {
            'time': t,
            'open': float(r['open']),
            'high': float(r['high']),
            'low': float(r['low']),
            'close': float(r['close']),
            'spreadAvg': float(r['spreadAvg']) if r['spreadAvg'] else 0.12,
            'spreadMax': float(r['spreadMax']) if r['spreadMax'] else 0.15,
            'imbalance': float(r['imbalance']) if r['imbalance'] else 0.0,
            'bidVol': float(r['bidVol']) if r['bidVol'] else 0.0,
            'askVol': float(r['askVol']) if r['askVol'] else 0.0,
        }

with open(flow_file, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for r in reader:
        t = r['time']
        if t in bars:
            bars[t]['delta'] = float(r['delta']) if r['delta'] else 0.0
            bars[t]['cvd'] = float(r['cvd']) if r['cvd'] else 0.0
            bars[t]['vwapDay'] = float(r['vwapDay']) if r['vwapDay'] else bars[t]['close']
            bars[t]['sdDay'] = float(r['sdDay']) if r['sdDay'] else 3.5
            bars[t]['poc'] = float(r['poc']) if r['poc'] else bars[t]['close']

sorted_bars = [bars[k] for k in sorted(bars.keys())]
print(f"Loaded {len(sorted_bars)} chronological XAUUSD bars.")

def run_simulation(bars, config):
    vwap_sd_mult = config.get('vwap_sd_mult', 1.2)
    sl_usd = config.get('sl_usd', 2.0)
    rr = config.get('rr', 2.2) # TP = sl_usd * rr
    spread_gate = config.get('spread_gate', 0.14)
    use_be = config.get('use_be', True)
    be_trigger_r = config.get('be_trigger_r', 1.0)
    lot_size = 0.01

    trades = []
    equity = 100.0
    equity_curve = [{'time': bars[0]['time'], 'equity': equity}]
    pos = None

    for i in range(20, len(bars)):
        curr = bars[i]
        t = curr['time']
        close = curr['close']
        high = curr['high']
        low = curr['low']
        spread = curr['spreadAvg']
        delta = curr.get('delta', 0.0)
        cvd = curr.get('cvd', 0.0)
        vwap = curr.get('vwapDay', close)
        sd = curr.get('sdDay', 3.5)

        # 1. Manage open position
        if pos is not None:
            side = pos['side']
            entry = pos['entry']
            cur_sl = pos['sl']
            cur_tp = pos['tp']

            # Check Breakeven trailing
            if use_be and not pos['be_locked']:
                if side == 'Buy' and (high - entry) >= (pos['init_sl'] * be_trigger_r):
                    pos['sl'] = entry + spread + 0.05 # lock in +$0.05 after spread!
                    pos['be_locked'] = True
                elif side == 'Sell' and (entry - low) >= (pos['init_sl'] * be_trigger_r):
                    pos['sl'] = entry - spread - 0.05
                    pos['be_locked'] = True

            exit_trade = False
            exit_price = 0.0
            reason = ""

            if side == 'Buy':
                # Exit at Bid
                if low <= pos['sl']:
                    exit_trade = True
                    exit_price = pos['sl']
                    reason = "Breakeven" if pos['be_locked'] else "StopLoss"
                elif high >= pos['tp']:
                    exit_trade = True
                    exit_price = pos['tp']
                    reason = "TakeProfit"

                if exit_trade:
                    # Profit for 0.01 lot of XAUUSD:
                    # 1 standard lot of XAU = 100 oz. 0.01 lot = 1 oz.
                    # Price difference of $1.00 USD on 1 oz = $1.00 USD profit!
                    pnl = (exit_price - entry) * 1.0 # 0.01 lot = 1 unit of gold
                    equity += pnl
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
                # Exit at Ask = price + spread
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
            # Spread gate check
            if spread > spread_gate:
                continue

            # VWAP Bands
            upper_band = vwap + (sd * vwap_sd_mult)
            lower_band = vwap - (sd * vwap_sd_mult)

            # Rolling extremes (last 15 bars)
            recent_high = max(bars[k]['high'] for k in range(i-15, i))
            recent_low = min(bars[k]['low'] for k in range(i-15, i))

            # Previous bar delta
            prev_delta = bars[i-1].get('delta', 0.0)

            # BUY SIGNAL:
            # 1. Price is stretched below VWAP lower band OR near 15m low
            # 2. Delta exhaustion: Previous bar was selling, but current bar Delta flips positive (>= +5)
            buy_signal = (low <= lower_band or low <= recent_low) and (delta >= 5) and (prev_delta <= 5)

            # SELL SIGNAL:
            # 1. Price is stretched above VWAP upper band OR near 15m high
            # 2. Delta exhaustion: Previous bar was buying, but current bar Delta flips negative (<= -5)
            sell_signal = (high >= upper_band or high >= recent_high) and (delta <= -5) and (prev_delta >= -5)

            if buy_signal:
                entry = close + spread # Buy at Ask
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
            elif sell_signal:
                entry = close # Sell at Bid
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

    # Summary
    n_trades = len(trades)
    if n_trades == 0:
        return {'trades': 0, 'win_rate': 0.0, 'net_pnl': 0.0, 'trade_list': []}

    wins = [t for t in trades if t['pnl'] > 0]
    losses = [t for t in trades if t['pnl'] < 0]
    evens = [t for t in trades if t['pnl'] == 0]

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
        'evens': len(evens),
        'win_rate': round(win_rate, 1),
        'net_pnl': round(net_pnl, 2),
        'gross_profit': round(gross_profit, 2),
        'gross_loss': round(gross_loss, 2),
        'pf': round(pf, 2),
        'max_dd': round(max_dd, 2),
        'trade_list': trades,
        'equity_curve': equity_curve
    }

# Test grid across different SL / Target combinations
print("\n--- SIMULATION RESULTS: XAUUSD 5-PILLAR MODEL ON TODAY'S 870 BARS ---")
print(f"{'SL ($)':<8} | {'RR':<5} | {'Trades':<7} | {'WinRate':<8} | {'Net PnL ($)':<12} | {'PF':<6} | {'MaxDD ($)':<9}")
print("-" * 65)

best_res = None
best_pnl = -999

for sl in [1.5, 1.8, 2.0, 2.5, 3.0]:
    for rr in [1.5, 1.8, 2.0, 2.2, 2.5]:
        cfg = {
            'vwap_sd_mult': 1.2,
            'sl_usd': sl,
            'rr': rr,
            'spread_gate': 0.14,
            'use_be': True,
            'be_trigger_r': 1.0
        }
        res = run_simulation(sorted_bars, cfg)
        if res['trades'] > 0:
            print(f"${sl:<7.1f} | {rr:<5.1f} | {res['trades']:<7} | {res['win_rate']:<7.1f}% | ${res['net_pnl']:<11.2f} | {res['pf']:<6.2f} | ${res['max_dd']:<8.2f}")
            if res['net_pnl'] > best_pnl:
                best_pnl = res['net_pnl']
                best_res = (cfg, res)

print("\n================================================================================")
cfg_b, res_b = best_res
print(f"OPTIMAL CONFIGURATION: SL=${cfg_b['sl_usd']} | RR={cfg_b['rr']} (TP=${cfg_b['sl_usd']*cfg_b['rr']:.2f})")
print(f"Total Trades: {res_b['trades']} | Win Rate: {res_b['win_rate']}% ({res_b['wins']}W / {res_b['losses']}L / {res_b['evens']}BE)")
print(f"Net Profit: +${res_b['net_pnl']} USD | Profit Factor: {res_b['pf']} | Max DD: ${res_b['max_dd']} USD")
print("================================================================================")

print("\n--- DETAILED TRADE AUDIT (Every single trade of the best model) ---")
for tr in res_b['trade_list']:
    print(f"Trade #{tr['id']:02d} | {tr['side']:<4} | In: {tr['time_in']} @ ${tr['entry']:.2f} | Out: {tr['time_out']} @ ${tr['exit']:.2f} | {tr['reason']:<11} | PnL: ${tr['pnl']:+.2f} | Spread: ${tr['spread']:.3f} | Eq: ${tr['equity']:.2f}")
