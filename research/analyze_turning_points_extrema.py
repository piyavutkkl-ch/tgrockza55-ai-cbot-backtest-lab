import sys, os, csv, math
from collections import defaultdict
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from research.find_high_profit_strategy import load_data

bars = load_data('XAUUSD')
print(f"Loaded {len(bars)} M1 bars for XAUUSD ({bars[0]['time']} to {bars[-1]['time']})")

# 1. Identify Local Extrema (Swing Highs & Swing Lows)
# A swing low is confirmed if price rises by min_rebound within forward_bars.
# A swing high is confirmed if price falls by min_rebound within forward_bars.
def find_extrema(bars, min_move=4.0, forward_bars=30, lookback_bars=15):
    extrema = []
    n = len(bars)
    
    for i in range(lookback_bars, n - forward_bars):
        curr = bars[i]
        curr_low = curr['low']
        curr_high = curr['high']
        
        # Check if local low
        past_lows = [bars[j]['low'] for j in range(i - lookback_bars, i)]
        future_highs = [bars[j]['high'] for j in range(i + 1, i + 1 + forward_bars)]
        future_lows = [bars[j]['low'] for j in range(i + 1, i + 1 + forward_bars)]
        
        is_swing_low = False
        if curr_low <= min(past_lows):
            max_rebound = max(future_highs) - curr_low
            min_subsequent_drop = curr_low - min(future_lows)
            # Rebounded at least min_move without breaking significantly lower first
            if max_rebound >= min_move:
                is_swing_low = True
                extrema.append({
                    'type': 'BOTTOM (Swing Low)',
                    'index': i,
                    'time': curr['time'],
                    'price': curr_low,
                    'move': max_rebound,
                    'bar': curr
                })

        # Check if local high
        past_highs = [bars[j]['high'] for j in range(i - lookback_bars, i)]
        is_swing_high = False
        if curr_high >= max(past_highs):
            max_drop = curr_high - min(future_lows)
            if max_drop >= min_move:
                is_swing_high = True
                extrema.append({
                    'type': 'TOP (Swing High)',
                    'index': i,
                    'time': curr['time'],
                    'price': curr_high,
                    'move': max_drop,
                    'bar': curr
                })
                
    return extrema

extrema = find_extrema(bars, min_move=4.0, forward_bars=30, lookback_bars=15)
bottoms = [e for e in extrema if e['type'].startswith('BOTTOM')]
tops = [e for e in extrema if e['type'].startswith('TOP')]

print(f"Total Significant Turning Points identified: {len(extrema)} (Bottoms: {len(bottoms)}, Tops: {len(tops)})")

# 2. Analyze features at Bottoms and Tops
def analyze_turning_points(points, label):
    print(f"\n{'='*70}")
    print(f"   DETAILED FEATURE ANALYSIS AT {label} ({len(points)} turning points)")
    print(f"{'='*70}")
    
    delta_pos = 0
    delta_neg = 0
    delta_vals = []
    
    imb_pos = 0
    imb_neg = 0
    imb_vals = []
    
    below_vwap = 0
    above_vwap = 0
    vwap_devs = [] # in standard deviations
    
    below_val = 0
    above_vah = 0
    
    macro_bull = 0 # close > ema50 > ema200
    macro_bear = 0 # close < ema50 < ema200
    
    # Wick analysis (rejection wick ratio)
    wick_rejections = []
    
    for pt in points:
        b = pt['bar']
        d = b.get('delta', 0.0)
        imb = b.get('imbalance', 0.0)
        c = b['close']
        h = b['high']
        l = b['low']
        o = b['open']
        vwap = b.get('vwapDay', c)
        sd = b.get('sdDay', 3.5)
        val = b.get('val', l)
        vah = b.get('vah', h)
        ema50 = b.get('ema50', c)
        ema200 = b.get('ema200', c)
        
        delta_vals.append(d)
        if d > 0: delta_pos += 1
        elif d < 0: delta_neg += 1
        
        imb_vals.append(imb)
        if imb > 0.05: imb_pos += 1
        elif imb < -0.05: imb_neg += 1
        
        dev = (c - vwap) / sd if sd > 0 else 0
        vwap_devs.append(dev)
        if c < vwap: below_vwap += 1
        if c > vwap: above_vwap += 1
        
        if l <= val: below_val += 1
        if h >= vah: above_vah += 1
        
        if c > ema50 and ema50 > ema200: macro_bull += 1
        elif c < ema50 and ema50 < ema200: macro_bear += 1
        
        # Lower wick ratio for bottoms, upper wick ratio for tops
        candle_len = max(h - l, 0.01)
        if 'BOTTOM' in label:
            lower_wick = min(o, c) - l
            wick_rejections.append(lower_wick / candle_len)
        else:
            upper_wick = h - max(o, c)
            wick_rejections.append(upper_wick / candle_len)

    n = len(points)
    print(f"1. Volume Delta (Order Flow Tape):")
    print(f"   - Positive Delta: {delta_pos}/{n} ({delta_pos/n*100:.1f}%) | Negative Delta: {delta_neg}/{n} ({delta_neg/n*100:.1f}%)")
    print(f"   - Median Delta: {np.median(delta_vals):.1f} | Mean Delta: {np.mean(delta_vals):.1f}")
    
    print(f"\n2. DOM Imbalance (Level 2 Book Wall):")
    print(f"   - Positive Imb (> +0.05): {imb_pos}/{n} ({imb_pos/n*100:.1f}%) | Negative Imb (< -0.05): {imb_neg}/{n} ({imb_neg/n*100:.1f}%)")
    print(f"   - Median Imbalance: {np.median(imb_vals):.3f} | Mean Imbalance: {np.mean(imb_vals):.3f}")
    
    print(f"\n3. Anchored VWAP & Standard Deviation Bands:")
    print(f"   - Below VWAP: {below_vwap}/{n} ({below_vwap/n*100:.1f}%) | Above VWAP: {above_vwap}/{n} ({above_vwap/n*100:.1f}%)")
    print(f"   - Mean Z-Score from VWAP: {np.mean(vwap_devs):.2f} SD (Median: {np.median(vwap_devs):.2f} SD)")
    
    print(f"\n4. Market Profile Value Area:")
    print(f"   - Touching/Piercing VAL (Value Area Low): {below_val}/{n} ({below_val/n*100:.1f}%)")
    print(f"   - Touching/Piercing VAH (Value Area High): {above_vah}/{n} ({above_vah/n*100:.1f}%)")
    
    print(f"\n5. Macro Trend Context (EMA50 / EMA200):")
    print(f"   - In Macro Bull Trend (Close > EMA50 > EMA200): {macro_bull}/{n} ({macro_bull/n*100:.1f}%)")
    print(f"   - In Macro Bear Trend (Close < EMA50 < EMA200): {macro_bear}/{n} ({macro_bear/n*100:.1f}%)")
    
    print(f"\n6. Candle Rejection Wick:")
    print(f"   - Mean Wick Ratio: {np.mean(wick_rejections)*100:.1f}% of candle body")

analyze_turning_points(bottoms, "SWING LOWS (BOTTOMS / BUY POINTS)")
analyze_turning_points(tops, "SWING HIGHS (TOPS / SELL POINTS)")
