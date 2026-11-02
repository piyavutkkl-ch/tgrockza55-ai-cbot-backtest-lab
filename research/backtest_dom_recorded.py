import csv
import sys
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

def load_dataset(symbol):
    min_path = f"C:\\Users\\Strong Baesus PC1\\AppData\\Local\\BacktestLab\\live\\{symbol}\\min-2026-11.csv"
    flow_path = f"C:\\Users\\Strong Baesus PC1\\AppData\\Local\\BacktestLab\\live\\{symbol}\\flow-2026-11.csv"

    bars = {}
    with open(min_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for r in reader:
            t = r['time']
            bars[t] = {
                'time': t,
                'open': float(r['open']),
                'high': float(r['high']),
                'low': float(r['low']),
                'close': float(r['close']),
                'spreadAvg': float(r['spreadAvg']) if r['spreadAvg'] else 15.0,
                'spreadMax': float(r['spreadMax']) if r['spreadMax'] else 20.0,
                'imbalance': float(r['imbalance']) if r['imbalance'] else 0.0,
                'bidVol': float(r['bidVol']) if r['bidVol'] else 0.0,
                'askVol': float(r['askVol']) if r['askVol'] else 0.0,
            }

    with open(flow_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for r in reader:
            t = r['time']
            if t in bars:
                bars[t]['delta'] = float(r['delta']) if r['delta'] else 0.0
                bars[t]['cvd'] = float(r['cvd']) if r['cvd'] else 0.0
                bars[t]['vwapDay'] = float(r['vwapDay']) if r['vwapDay'] else bars[t]['close']
                bars[t]['poc'] = float(r['poc']) if r['poc'] else bars[t]['close']

    # Sort chronological
    sorted_bars = [bars[k] for k in sorted(bars.keys())]
    return sorted_bars

def run_backtest(symbol, bars, mode="baseline", params=None):
    if params is None:
        params = {}

    lookback = params.get('lookback', 15)
    imb_thresh = params.get('imb_thresh', 0.03)
    sl_usd = params.get('sl_usd', 25.0)
    rr = params.get('rr', 2.0)
    spread_ceiling = params.get('spread_ceiling', 9999.0)
    use_delta = params.get('use_delta', False)
    use_vwap = params.get('use_vwap', False)
    use_be = params.get('use_be', False)
    lot_size = 0.01

    trades = []
    equity = 100.0
    equity_curve = [{'time': bars[0]['time'], 'equity': equity}]
    
    pos = None # {'side': 'Sell', 'entry': price, 'entry_time': t, 'sl': sl, 'tp': tp, 'spread': s, 'be_locked': False}

    for i in range(lookback + 5, len(bars)):
        curr = bars[i]
        t = curr['time']
        close = curr['close']
        high = curr['high']
        low = curr['low']
        spread = curr['spreadAvg']
        imbalance = curr['imbalance']
        delta = curr.get('delta', 0.0)
        cvd = curr.get('cvd', 0.0)
        vwap = curr.get('vwapDay', close)

        # 1. Manage open position
        if pos is not None:
            side = pos['side']
            entry = pos['entry']
            cur_sl = pos['sl']
            cur_tp = pos['tp']

            # Check breakeven
            if use_be and not pos['be_locked']:
                if side == 'Sell' and (entry - close) >= (pos['init_sl_dist'] * 1.0):
                    pos['sl'] = entry - (spread * 0.5) # lock in slight profit/cost
                    pos['be_locked'] = True
                elif side == 'Buy' and (close - entry) >= (pos['init_sl_dist'] * 1.0):
                    pos['sl'] = entry + (spread * 0.5)
                    pos['be_locked'] = True

            exit_trade = False
            exit_price = 0.0
            reason = ""

            if side == 'Sell':
                # Ask price is high + spread
                worst_ask = high + spread
                best_ask = low + spread

                if worst_ask >= pos['sl']:
                    exit_trade = True
                    exit_price = pos['sl']
                    reason = "StopLoss"
                elif best_ask <= pos['tp']:
                    exit_trade = True
                    exit_price = pos['tp']
                    reason = "TakeProfit"

                if exit_trade:
                    # Profit = (entry - exit) * lot_size
                    pnl = (entry - exit_price) * lot_size
                    equity += pnl
                    trades.append({
                        'time_in': pos['entry_time'],
                        'time_out': t,
                        'side': 'Sell',
                        'entry': entry,
                        'exit': exit_price,
                        'pnl': round(pnl, 2),
                        'reason': reason,
                        'spread': pos['spread'],
                        'equity': round(equity, 2)
                    })
                    equity_curve.append({'time': t, 'equity': round(equity, 2)})
                    pos = None

            elif side == 'Buy':
                # Bid price is low
                worst_bid = low
                best_bid = high

                if worst_bid <= pos['sl']:
                    exit_trade = True
                    exit_price = pos['sl']
                    reason = "StopLoss"
                elif best_bid >= pos['tp']:
                    exit_trade = True
                    exit_price = pos['tp']
                    reason = "TakeProfit"

                if exit_trade:
                    pnl = (exit_price - entry) * lot_size
                    equity += pnl
                    trades.append({
                        'time_in': pos['entry_time'],
                        'time_out': t,
                        'side': 'Buy',
                        'entry': entry,
                        'exit': exit_price,
                        'pnl': round(pnl, 2),
                        'reason': reason,
                        'spread': pos['spread'],
                        'equity': round(equity, 2)
                    })
                    equity_curve.append({'time': t, 'equity': round(equity, 2)})
                    pos = None

        # 2. Check new entry if flat
        if pos is None:
            # Check spread ceiling
            if spread > spread_ceiling:
                continue

            # Rolling extremes
            rolling_high = max(bars[j]['high'] for j in range(i - lookback, i))
            rolling_low = min(bars[j]['low'] for j in range(i - lookback, i))
            tol = (rolling_high - rolling_low) * 0.08

            # SELL Signal
            sell_cond = (close >= rolling_high - tol) and (imbalance <= -imb_thresh)
            if use_delta:
                sell_cond = sell_cond and (delta <= 0)
            if use_vwap:
                sell_cond = sell_cond and (close < vwap or close >= rolling_high) # exhaustion fade or below vwap

            # BUY Signal
            buy_cond = (close <= rolling_low + tol) and (imbalance >= imb_thresh)
            if use_delta:
                buy_cond = buy_cond and (delta >= 0)
            if use_vwap:
                buy_cond = buy_cond and (close > vwap or close <= rolling_low)

            if sell_cond:
                entry = close # Sell at Bid
                actual_sl_dist = max(sl_usd, 2.5 * spread) if mode != "baseline" else sl_usd
                sl = entry + actual_sl_dist
                tp = entry - (actual_sl_dist * rr)
                pos = {
                    'side': 'Sell',
                    'entry': entry,
                    'entry_time': t,
                    'sl': sl,
                    'tp': tp,
                    'init_sl_dist': actual_sl_dist,
                    'spread': spread,
                    'be_locked': False
                }
            elif buy_cond:
                entry = close + spread # Buy at Ask
                actual_sl_dist = max(sl_usd, 2.5 * spread) if mode != "baseline" else sl_usd
                sl = entry - actual_sl_dist
                tp = entry + (actual_sl_dist * rr)
                pos = {
                    'side': 'Buy',
                    'entry': entry,
                    'entry_time': t,
                    'sl': sl,
                    'tp': tp,
                    'init_sl_dist': actual_sl_dist,
                    'spread': spread,
                    'be_locked': False
                }

    # Summary metrics
    n_trades = len(trades)
    if n_trades == 0:
        return {'trades': 0, 'win_rate': 0, 'net_pnl': 0.0, 'pf': 0.0, 'max_dd': 0.0, 'trade_list': []}

    wins = [tr for tr in trades if tr['pnl'] > 0]
    losses = [tr for tr in trades if tr['pnl'] < 0]
    win_rate = len(wins) / n_trades * 100.0
    gross_profit = sum(tr['pnl'] for tr in wins)
    gross_loss = abs(sum(tr['pnl'] for tr in losses))
    net_pnl = gross_profit - gross_loss
    pf = (gross_profit / gross_loss) if gross_loss > 0 else 99.0

    # Max Drawdown
    peak = 100.0
    max_dd = 0.0
    for pt in equity_curve:
        eq = pt['equity']
        if eq > peak:
            peak = eq
        dd = peak - eq
        if dd > max_dd:
            max_dd = dd

    return {
        'symbol': symbol,
        'mode': mode,
        'trades': n_trades,
        'wins': len(wins),
        'losses': len(losses),
        'win_rate': round(win_rate, 1),
        'gross_profit': round(gross_profit, 2),
        'gross_loss': round(gross_loss, 2),
        'net_pnl': round(net_pnl, 2),
        'pf': round(pf, 2),
        'max_dd': round(max_dd, 2),
        'final_equity': round(equity, 2),
        'trade_list': trades,
        'equity_curve': equity_curve
    }

if __name__ == '__main__':
    for sym in ['BTCUSD', 'ETHUSD']:
        bars = load_dataset(sym)
        print(f"\n==================== {sym} (Bars: {len(bars)}) ====================")
        
        # 1. Baseline (Unfiltered - matches live forward run)
        if sym == 'BTCUSD':
            base_p = {'lookback': 15, 'imb_thresh': 0.03, 'sl_usd': 25.0, 'rr': 2.0, 'spread_ceiling': 999.0}
            up_p = {'lookback': 20, 'imb_thresh': 0.05, 'sl_usd': 45.0, 'rr': 2.5, 'spread_ceiling': 22.0, 'use_delta': True, 'use_vwap': True, 'use_be': True}
        else:
            base_p = {'lookback': 20, 'imb_thresh': 0.03, 'sl_usd': 1.0, 'rr': 3.5, 'spread_ceiling': 999.0}
            up_p = {'lookback': 25, 'imb_thresh': 0.04, 'sl_usd': 2.2, 'rr': 2.5, 'spread_ceiling': 2.2, 'use_delta': True, 'use_vwap': True, 'use_be': True}

        res_base = run_backtest(sym, bars, mode="baseline", params=base_p)
        print(f"BASELINE (Original): Trades={res_base['trades']} | WinRate={res_base['win_rate']}% ({res_base['wins']}W/{res_base['losses']}L) | NetPnL=${res_base['net_pnl']} | PF={res_base['pf']} | MaxDD=${res_base['max_dd']}")

        # 2. Upgraded Institutional V2
        res_up = run_backtest(sym, bars, mode="upgraded", params=up_p)
        print(f"UPGRADED V2 (Institutional): Trades={res_up['trades']} | WinRate={res_up['win_rate']}% ({res_up['wins']}W/{res_up['losses']}L) | NetPnL=${res_up['net_pnl']} | PF={res_up['pf']} | MaxDD=${res_up['max_dd']}")
