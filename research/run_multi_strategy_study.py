import sys, os, csv, math
from collections import defaultdict
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from research.find_high_profit_strategy import load_data, simulate_strategy

print("================================================================================")
print("     MULTI-STRATEGY QUANT RESEARCH ON RECORDED L2 DOM DATA (NOV 1 - 5, 2026)    ")
print("================================================================================")

# 1. Baseline Pure DOM Absorption (Fading without Trend)
def logic_baseline(bars, i, trades):
    curr = bars[i]
    if curr['spreadAvg'] > 0.14: return None
    
    recent_h = max(bars[k]['high'] for k in range(i-15, i))
    recent_l = min(bars[k]['low'] for k in range(i-15, i))
    tol = (recent_h - recent_l) * 0.08

    if curr['close'] >= recent_h - tol and curr['imbalance'] <= -0.02:
        return {'side': 'Sell', 'sl_dist': 2.5, 'tp_dist': 5.0, 'use_be': True}
    if curr['close'] <= recent_l + tol and curr['imbalance'] >= 0.02:
        return {'side': 'Buy', 'sl_dist': 2.5, 'tp_dist': 5.0, 'use_be': True}
    return None

# 2. Trend-Aligned Liquidity Pullback (Only trade WITH Trend + Order Flow Absorption)
def logic_trend_pullback(bars, i, trades):
    curr = bars[i]
    if curr['spreadAvg'] > 0.14: return None
    
    close = curr['close']
    vwap = curr['vwapDay']
    ema20 = curr['ema20']
    ema50 = curr['ema50']
    ema200 = curr['ema200']
    delta = curr.get('delta', 0.0)
    prev_delta = bars[i-1].get('delta', 0.0)
    sd = curr.get('sdDay', 3.5)
    lower_band = vwap - (sd * 1.0)
    upper_band = vwap + (sd * 1.0)

    recent_l = min(bars[k]['low'] for k in range(i-15, i))
    recent_h = max(bars[k]['high'] for k in range(i-15, i))

    # Directional cooldown: if last 2 trades were same direction losses, pause 30 mins
    if len(trades) >= 2:
        t1, t2 = trades[-1], trades[-2]
        if t1['pnl'] < 0 and t2['pnl'] < 0 and t1['side'] == t2['side']:
            # Check elapsed bars
            # simplify: don't enter in the losing direction
            forbidden_side = t1['side']
        else:
            forbidden_side = None
    else:
        forbidden_side = None

    # UPTREND REGIME: EMA50 > EMA200 AND close > EMA50
    is_uptrend = (ema50 > ema200) and (close > ema50 or close > vwap)
    # DOWNTREND REGIME: EMA50 < EMA200 AND close < EMA50
    is_downtrend = (ema50 < ema200) and (close < ema50 or close < vwap)

    # In Uptrend: ONLY BUY DIPS
    if is_uptrend and forbidden_side != 'Buy':
        # Dip into lower band or recent low with positive delta absorption
        if (curr['low'] <= lower_band or curr['low'] <= recent_l + (recent_h - recent_l)*0.15) and (delta >= 5 and prev_delta <= 5):
            return {'side': 'Buy', 'sl_dist': 2.8, 'tp_dist': 6.5, 'use_be': True}

    # In Downtrend: ONLY SELL RALLIES
    if is_downtrend and forbidden_side != 'Sell':
        # Rally into upper band or recent high with negative delta absorption
        if (curr['high'] >= upper_band or curr['high'] >= recent_h - (recent_h - recent_l)*0.15) and (delta <= -5 and prev_delta >= -5):
            return {'side': 'Sell', 'sl_dist': 2.8, 'tp_dist': 6.5, 'use_be': True}

    return None

# 3. Liquidity Sweep & Stop Run Reversal (SMC Trap)
def logic_liquidity_sweep(bars, i, trades):
    curr = bars[i]
    if curr['spreadAvg'] > 0.14: return None
    
    # 30-bar swing extremes
    h30 = max(bars[k]['high'] for k in range(i-30, i))
    l30 = min(bars[k]['low'] for k in range(i-30, i))
    delta = curr.get('delta', 0.0)

    # Bull trap: swept above 30-bar high but closed back inside with heavy sell delta
    if curr['high'] > h30 and curr['close'] < h30 and delta <= -12:
        return {'side': 'Sell', 'sl_dist': max(1.8, curr['high'] - curr['close'] + 0.5), 'tp_dist': 5.5, 'use_be': True}

    # Bear trap: swept below 30-bar low but closed back inside with heavy buy delta
    if curr['low'] < l30 and curr['close'] > l30 and delta >= 12:
        return {'side': 'Buy', 'sl_dist': max(1.8, curr['close'] - curr['low'] + 0.5), 'tp_dist': 5.5, 'use_be': True}

    return None

# 4. Momentum Trend Breakout + Order Book Support
def logic_momentum_breakout(bars, i, trades):
    curr = bars[i]
    if curr['spreadAvg'] > 0.14: return None
    
    h20 = max(bars[k]['high'] for k in range(i-20, i))
    l20 = min(bars[k]['low'] for k in range(i-20, i))
    delta = curr.get('delta', 0.0)
    imb = curr.get('imbalance', 0.0)
    ema20 = curr['ema20']
    ema50 = curr['ema50']

    # Bullish Breakout: New 20-bar high with aggressive buying delta (> +15) and Bid Wall support (imb > +0.02)
    if curr['close'] > h20 and delta >= 15 and imb >= 0.015 and ema20 > ema50:
        return {'side': 'Buy', 'sl_dist': 2.5, 'tp_dist': 7.5, 'use_be': True}

    # Bearish Breakout: New 20-bar low with aggressive selling delta (< -15) and Ask Wall (imb < -0.015)
    if curr['close'] < l20 and delta <= -15 and imb <= -0.015 and ema20 < ema50:
        return {'side': 'Sell', 'sl_dist': 2.5, 'tp_dist': 7.5, 'use_be': True}

    return None

# RUN ON XAUUSD
xau_bars = load_data('XAUUSD')
print(f"\n==================== XAUUSD (Total Bars: {len(xau_bars)}) ====================")

strats = [
    ("1. Baseline Fading (Original)", logic_baseline),
    ("2. Trend-Aligned Liquidity Pullback", logic_trend_pullback),
    ("3. Liquidity Sweep & Stop Run (SMC Trap)", logic_liquidity_sweep),
    ("4. Momentum Trend Breakout", logic_momentum_breakout)
]

for name, fn in strats:
    res = simulate_strategy(xau_bars, fn, symbol='XAUUSD')
    print(f"\n{name}:")
    print(f"  Trades: {res['trades']} | Win Rate: {res['win_rate']}% ({res['wins']}W / {res['losses']}L)")
    print(f"  Gross Profit: +${res['gross_win']} | Gross Loss: -${res['gross_loss']}")
    print(f"  Net Profit: +${res['net_pnl']} USD | Profit Factor: {res['pf']} | Max DD: ${res['max_dd']} USD")
