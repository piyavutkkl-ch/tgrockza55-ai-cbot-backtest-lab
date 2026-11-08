import sys, os, csv, math
from collections import defaultdict
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from research.find_high_profit_strategy import load_data, simulate_strategy

def test_duo_engine_hybrid(symbol, bars):
    is_gold = 'XAU' in symbol or 'GOLD' in symbol
    is_btc = 'BTC' in symbol
    is_eth = 'ETH' in symbol

    # Asset specific thresholds
    spread_limit = 0.15 if is_gold else (22.0 if is_btc else 2.3)
    sl_usd = 3.0 if is_gold else (65.0 if is_btc else 2.2)
    tp_mult = 2.4 # RR 1:2.4
    lot_multiplier = 1.0 if is_gold else 0.01

    def logic_duo_engine(b_list, i, trades):
        curr = b_list[i]
        spread = curr['spreadAvg']
        if spread > spread_limit: return None

        close = curr['close']
        vwap = curr['vwapDay']
        sd = curr.get('sdDay', 3.5 if is_gold else 50.0)
        ema20 = curr['ema20']
        ema50 = curr['ema50']
        ema200 = curr['ema200']
        delta = curr.get('delta', 0.0)
        prev_delta = b_list[i-1].get('delta', 0.0)
        imb = curr.get('imbalance', 0.0)

        # Circuit breaker: freeze direction on 2 consecutive losses
        if len(trades) >= 2:
            t1, t2 = trades[-1], trades[-2]
            if t1['pnl'] < 0 and t2['pnl'] < 0 and t1['side'] == t2['side']:
                # Cooldown 25 bars
                bars_since = i - [idx for idx, b in enumerate(b_list) if b['time'] == t1['time_out']][0] if any(b['time'] == t1['time_out'] for b in b_list) else 99
                if bars_since < 25:
                    forbidden = t1['side']
                else:
                    forbidden = None
            else:
                forbidden = None
        else:
            forbidden = None

        # Lookbacks
        h15 = max(b_list[k]['high'] for k in range(i-15, i))
        l15 = min(b_list[k]['low'] for k in range(i-15, i))

        # Regime classification
        trend_up = (ema50 > ema200) and (close > ema50) and (ema20 > ema50)
        trend_down = (ema50 < ema200) and (close < ema50) and (ema20 < ema50)

        # ENGINE A: TREND MOMENTUM & BREAKOUT
        if trend_up and forbidden != 'Buy':
            # Breakout with delta acceleration OR Pullback to EMA20/VWAP with delta bounce
            pullback_buy = (curr['low'] <= ema20 or curr['low'] <= vwap) and (delta >= (8 if is_gold else 5) and prev_delta <= 0)
            breakout_buy = (close >= h15) and (delta >= (15 if is_gold else 10)) and (imb >= 0.01)
            if pullback_buy or breakout_buy:
                return {'side': 'Buy', 'sl_dist': sl_usd, 'tp_dist': sl_usd * tp_mult, 'use_be': True}

        if trend_down and forbidden != 'Sell':
            pullback_sell = (curr['high'] >= ema20 or curr['high'] >= vwap) and (delta <= -(8 if is_gold else 5) and prev_delta >= 0)
            breakout_sell = (close <= l15) and (delta <= -(15 if is_gold else 10)) and (imb <= -0.01)
            if pullback_sell or breakout_sell:
                return {'side': 'Sell', 'sl_dist': sl_usd, 'tp_dist': sl_usd * tp_mult, 'use_be': True}

        # ENGINE B: STATISTICAL MEAN REVERSION (Only in consolidation / overextension)
        if not trend_up and not trend_down:
            # Overextended above VWAP + 1.8 SD
            if close >= vwap + (sd * 1.6) and delta <= -10 and forbidden != 'Sell':
                return {'side': 'Sell', 'sl_dist': sl_usd, 'tp_dist': sl_usd * 2.0, 'use_be': True}
            # Overextended below VWAP - 1.8 SD
            if close <= vwap - (sd * 1.6) and delta >= 10 and forbidden != 'Buy':
                return {'side': 'Buy', 'sl_dist': sl_usd, 'tp_dist': sl_usd * 2.0, 'use_be': True}

        return None

    res = simulate_strategy(bars, logic_duo_engine, symbol=symbol)
    return res

print("\n================================================================================")
print("     BENCHMARKING DUO-ENGINE HYBRID MODEL ON ALL 4 ASSETS (FULL DATASET)       ")
print("================================================================================")

for sym in ['XAUUSD', 'GOLD-PERP', 'BTCUSD', 'ETHUSD']:
    bars = load_data(sym)
    res = test_duo_engine_hybrid(sym, bars)
    print(f"\nAsset: {sym} (Bars: {len(bars)} | Range: {bars[0]['time']} to {bars[-1]['time']})")
    print(f"  Total Trades: {res['trades']} | Win Rate: {res['win_rate']}% ({res['wins']}W / {res['losses']}L)")
    print(f"  Gross Profit: +${res['gross_win']} USD | Gross Loss: -${res['gross_loss']} USD")
    print(f"  Net PnL: +${res['net_pnl']} USD | Profit Factor: {res['pf']} | Max DD: ${res['max_dd']} USD")
