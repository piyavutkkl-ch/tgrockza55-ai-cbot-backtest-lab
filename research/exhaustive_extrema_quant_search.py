import sys, os, csv, math
from itertools import product
from collections import defaultdict
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from research.find_high_profit_strategy import load_data

def run_backtest_engine(bars, symbol='XAUUSD',
                        trigger_type='HYBRID',      # 'DELTA_FLIP', 'DELTA_DIV', 'DOM_WALL', 'VWAP_ABS', 'HYBRID'
                        delta_thresh=5.0,
                        imb_thresh=0.01,
                        sl=3.0,
                        rr=2.0,
                        be_trigger_r=1.0,           # 0.0 = disabled
                        macro_trend=True,
                        circuit_breaker=True,
                        smart_dom_exit=False):
    lot_multiplier = 1.0 if 'XAU' in symbol or 'GOLD' in symbol else 0.01
    spread_max = 0.15 if 'XAU' in symbol else 0.35
    
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
        val = curr.get('val', low)
        vah = curr.get('vah', high)
        ema50 = curr.get('ema50', close)
        ema200 = curr.get('ema200', close)

        # 1. Manage active position
        if pos is not None:
            side = pos['side']
            entry = pos['entry']
            cur_sl = pos['sl']
            cur_tp = pos['tp']

            # Breakeven Lock
            if be_trigger_r > 0 and not pos['be_locked']:
                if side == 'Buy' and (high - entry) >= (pos['sl_dist'] * be_trigger_r):
                    pos['sl'] = entry + spread + 0.05
                    pos['be_locked'] = True
                elif side == 'Sell' and (entry - low) >= (pos['sl_dist'] * be_trigger_r):
                    pos['sl'] = entry - spread - 0.05
                    pos['be_locked'] = True

            exit_trade = False
            exit_price = 0.0
            reason = ""

            # Smart DOM / Opposite Delta Exit
            if smart_dom_exit:
                if side == 'Buy' and (close - entry) >= pos['sl_dist'] * 0.5:
                    if delta <= -15 or imb <= -0.05:
                        exit_trade = True
                        exit_price = close
                        reason = "SmartDOMExit"
                elif side == 'Sell' and (entry - close) >= pos['sl_dist'] * 0.5:
                    if delta >= 15 or imb >= 0.05:
                        exit_trade = True
                        exit_price = close + spread
                        reason = "SmartDOMExit"

            if not exit_trade:
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

                if circuit_breaker:
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

        # 2. Check Entry Signal if Flat
        if pos is None:
            if spread > spread_max:
                continue

            buy_signal = False
            sell_signal = False

            recent_low = min(bars[k]['low'] for k in range(i-15, i))
            recent_high = max(bars[k]['high'] for k in range(i-15, i))
            lower_band = vwap - (sd * 1.2)
            upper_band = vwap + (sd * 1.2)

            # Signal Trigger Selection
            if trigger_type == 'DELTA_FLIP':
                # Bar -1 was heavy selling, Bar 0 flips to aggressive buying
                buy_signal = (prev_delta <= -delta_thresh) and (delta >= delta_thresh)
                sell_signal = (prev_delta >= delta_thresh) and (delta <= -delta_thresh)

            elif trigger_type == 'DELTA_DIV':
                # Price made lower low, but delta ended strongly positive (Absorption)
                buy_signal = (low < prev['low']) and (delta >= delta_thresh)
                sell_signal = (high > prev['high']) and (delta <= -delta_thresh)

            elif trigger_type == 'DOM_WALL':
                # Order Book Wall Imbalance + Delta Confirmation
                buy_signal = (imb >= imb_thresh) and (delta >= 0) and (low <= recent_low or low <= lower_band)
                sell_signal = (imb <= -imb_thresh) and (delta <= 0) and (high >= recent_high or high >= upper_band)

            elif trigger_type == 'VWAP_ABS':
                # Mean Reversion at VWAP Bands + Delta Rebound
                buy_signal = (low <= lower_band) and (delta >= delta_thresh)
                sell_signal = (high >= upper_band) and (delta <= -delta_thresh)

            elif trigger_type == 'HYBRID':
                # Confluence: Location (Recent Low/High or VWAP Band) + Delta Absorption (Delta >= thresh and prev <= thresh)
                buy_signal = (low <= lower_band or low <= recent_low) and (delta >= delta_thresh) and (prev_delta <= delta_thresh)
                sell_signal = (high >= upper_band or high >= recent_high) and (delta <= -delta_thresh) and (prev_delta >= -delta_thresh)
                if imb_thresh > 0:
                    # In addition, ensure no adverse DOM Wall blocking
                    if imb < -0.05: buy_signal = False
                    if imb > 0.05: sell_signal = False

            elif trigger_type == 'EXTREMA_WICK_DELTA':
                # Extrema with Rejection Wick >= 25% + Delta Absorption
                candle_len = max(high - low, 0.01)
                lower_wick = (min(curr['open'], close) - low) / candle_len
                upper_wick = (high - max(curr['open'], close)) / candle_len
                
                buy_signal = (lower_wick >= 0.25) and (delta >= delta_thresh) and (low <= recent_low or low <= lower_band)
                sell_signal = (upper_wick >= 0.25) and (delta <= -delta_thresh) and (high >= recent_high or high >= upper_band)

            # Macro Trend Shield
            if macro_trend:
                if close > ema50 and ema50 > ema200:
                    sell_signal = False
                elif close < ema50 and ema50 < ema200:
                    buy_signal = False

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
                    'be_locked': False
                }

    n = len(trades)
    if n == 0:
        return {'trades': 0, 'wins': 0, 'losses': 0, 'win_rate': 0.0, 'net_pnl': 0.0, 'pf': 0.0, 'max_dd': 0.0, 'trades_list': []}
    
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

if __name__ == '__main__':
    bars = load_data('XAUUSD')
    print(f"Loaded {len(bars)} bars for XAUUSD")

    print("\n" + "="*95)
    print("      EXHAUSTIVE STRATEGY SEARCH: WHICH MECHANISM CAPTURES TURNING POINTS BEST?")
    print("="*95)

    triggers = ['DELTA_FLIP', 'DELTA_DIV', 'DOM_WALL', 'VWAP_ABS', 'HYBRID', 'EXTREMA_WICK_DELTA']
    sl_list = [2.5, 3.0, 3.5, 4.0]
    rr_list = [1.5, 2.0, 2.5, 3.0]
    be_list = [0.0, 1.0]

    results = []

    for trig in triggers:
        for sl in sl_list:
            for rr in rr_list:
                for be in be_list:
                    res = run_backtest_engine(bars, symbol='XAUUSD',
                                              trigger_type=trig,
                                              delta_thresh=5.0,
                                              sl=sl,
                                              rr=rr,
                                              be_trigger_r=be,
                                              macro_trend=True,
                                              circuit_breaker=True)
                    if res['trades'] >= 15: # minimum statistically meaningful trade sample
                        results.append({
                            'trigger': trig,
                            'sl': sl,
                            'rr': rr,
                            'be': be,
                            'trades': res['trades'],
                            'win_rate': res['win_rate'],
                            'net_pnl': res['net_pnl'],
                            'pf': res['pf'],
                            'max_dd': res['max_dd']
                        })

    # Sort by Net PnL descending
    results.sort(key=lambda x: x['net_pnl'], reverse=True)

    print(f"\nTop 15 Most Profitable Strategies on XAUUSD (Total tested: {len(results)} valid configurations):")
    print(f"{'Rank':<5} | {'Trigger Type':<20} | {'SL':<5} | {'RR':<4} | {'BE':<4} | {'Trades':<7} | {'Win Rate':<10} | {'Net PnL':<12} | {'PF':<6} | {'Max DD':<8}")
    print("-" * 95)
    for idx, r in enumerate(results[:15], 1):
        print(f"#{idx:<4} | {r['trigger']:<20} | ${r['sl']:<4.1f} | {r['rr']:<4.1f} | {r['be']:<4.1f} | {r['trades']:<7} | {r['win_rate']:>5.1f}%    | ${r['net_pnl']:>+8.2f}   | {r['pf']:<6.2f} | ${r['max_dd']:<7.2f}")
