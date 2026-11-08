import sys, os, csv, math
from collections import defaultdict
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')

def load_data(symbol):
    base_local = r'C:\Users\Strong Baesus PC1\AppData\Local\BacktestLab\live'
    base_repo = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'live')
    base = base_local if os.path.exists(base_local) else base_repo
    min_file = os.path.join(base, symbol, 'min-2026-11.csv')
    flow_file = os.path.join(base, symbol, 'flow-2026-11.csv')

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
                bars[t]['vah'] = float(r['vah']) if r['vah'] else bars[t]['high']
                bars[t]['val'] = float(r['val']) if r['val'] else bars[t]['low']

    sorted_bars = [bars[k] for k in sorted(bars.keys())]

    # Precalculate EMAs: 20 and 50 and 200
    closes = [b['close'] for b in sorted_bars]
    def calc_ema(values, period):
        ema = [values[0]]
        k = 2.0 / (period + 1.0)
        for val in values[1:]:
            ema.append(val * k + ema[-1] * (1.0 - k))
        return ema

    ema20 = calc_ema(closes, 20)
    ema50 = calc_ema(closes, 50)
    ema200 = calc_ema(closes, 200)

    # ATR 14
    atrs = [1.0]
    for i in range(1, len(sorted_bars)):
        h = sorted_bars[i]['high']
        l = sorted_bars[i]['low']
        prev_c = sorted_bars[i-1]['close']
        tr = max(h - l, abs(h - prev_c), abs(l - prev_c))
        atrs.append(atrs[-1] * (13.0/14.0) + tr * (1.0/14.0))

    for i, b in enumerate(sorted_bars):
        b['ema20'] = ema20[i]
        b['ema50'] = ema50[i]
        b['ema200'] = ema200[i]
        b['atr'] = atrs[i]

    return sorted_bars

# General Simulator Engine
def simulate_strategy(bars, logic_func, symbol='XAUUSD', initial_equity=100.0):
    lot_size = 0.01
    multiplier = 1.0 if 'XAU' in symbol or 'GOLD' in symbol else 0.01
    
    trades = []
    equity = initial_equity
    equity_curve = [{'time': bars[0]['time'], 'equity': equity}]
    pos = None

    for i in range(50, len(bars)):
        curr = bars[i]
        t = curr['time']
        close = curr['close']
        high = curr['high']
        low = curr['low']
        spread = curr['spreadAvg']

        # 1. Manage open trade
        if pos is not None:
            side = pos['side']
            entry = pos['entry']
            cur_sl = pos['sl']
            cur_tp = pos['tp']

            # Breakeven Lock check
            if pos.get('use_be', True) and not pos['be_locked']:
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

        # 2. Check for signal if flat
        if pos is None:
            sig = logic_func(bars, i, trades)
            if sig is not None:
                # sig: {'side': 'Buy'/'Sell', 'sl_dist': float, 'tp_dist': float}
                side = sig['side']
                sl_dist = sig['sl_dist']
                tp_dist = sig['tp_dist']

                if side == 'Buy':
                    entry = close + spread
                    sl = entry - sl_dist
                    tp = entry + tp_dist
                    pos = {
                        'side': 'Buy',
                        'entry': entry,
                        'entry_time': t,
                        'sl': sl,
                        'tp': tp,
                        'sl_dist': sl_dist,
                        'spread': spread,
                        'be_locked': False,
                        'use_be': sig.get('use_be', True)
                    }
                elif side == 'Sell':
                    entry = close
                    sl = entry + sl_dist
                    tp = entry - tp_dist
                    pos = {
                        'side': 'Sell',
                        'entry': entry,
                        'entry_time': t,
                        'sl': sl,
                        'tp': tp,
                        'sl_dist': sl_dist,
                        'spread': spread,
                        'be_locked': False,
                        'use_be': sig.get('use_be', True)
                    }

    # Summary
    n = len(trades)
    if n == 0:
        return {'trades': 0, 'wins': 0, 'losses': 0, 'win_rate': 0.0, 'gross_win': 0.0, 'gross_loss': 0.0, 'net_pnl': 0.0, 'pf': 0.0, 'max_dd': 0.0, 'trade_list': [], 'equity_curve': equity_curve}
    
    wins = [tr for tr in trades if tr['pnl'] > 0]
    losses = [tr for tr in trades if tr['pnl'] < 0]
    gross_win = sum(tr['pnl'] for tr in wins)
    gross_loss = abs(sum(tr['pnl'] for tr in losses))
    net_pnl = gross_win - gross_loss
    pf = (gross_win / gross_loss) if gross_loss > 0 else 99.0
    win_rate = len(wins) / n * 100.0

    peak = initial_equity
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

print("Loaded test harness.")
