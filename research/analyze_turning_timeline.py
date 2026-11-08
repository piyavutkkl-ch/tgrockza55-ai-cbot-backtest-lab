import sys, os, csv, math
from collections import defaultdict
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from research.find_high_profit_strategy import load_data

bars = load_data('XAUUSD')

def find_extrema_deep(bars, min_move=4.0, forward_bars=30, lookback_bars=15):
    bottoms = []
    tops = []
    n = len(bars)
    
    for i in range(lookback_bars + 2, n - forward_bars - 2):
        curr = bars[i]
        curr_low = curr['low']
        curr_high = curr['high']
        
        past_lows = [bars[j]['low'] for j in range(i - lookback_bars, i)]
        future_highs = [bars[j]['high'] for j in range(i + 1, i + 1 + forward_bars)]
        future_lows = [bars[j]['low'] for j in range(i + 1, i + 1 + forward_bars)]
        
        # Check swing low
        if curr_low <= min(past_lows):
            max_rebound = max(future_highs) - curr_low
            if max_rebound >= min_move:
                bottoms.append(i)

        # Check swing high
        past_highs = [bars[j]['high'] for j in range(i - lookback_bars, i)]
        if curr_high >= max(past_highs):
            max_drop = curr_high - min(future_lows)
            if max_drop >= min_move:
                tops.append(i)
                
    return bottoms, tops

bottoms, tops = find_extrema_deep(bars, min_move=4.0)

print(f"Total bottoms: {len(bottoms)}, tops: {len(tops)}")

def print_timeline(indices, label):
    print(f"\n{'='*75}")
    print(f"   SEQUENCE TIMELINE AROUND {label} (Average values)")
    print(f"{'='*75}")
    print(f"{'Offset':<8} | {'Delta':<8} | {'Delta Change':<14} | {'Price vs Low':<14} | {'Imbalance':<10} | {'Wick %':<8}")
    print("-" * 75)
    
    for offset in [-2, -1, 0, 1, 2]:
        deltas = []
        delta_diffs = []
        price_diffs = []
        imbs = []
        wicks = []
        
        for idx in indices:
            b_curr = bars[idx + offset]
            b_prev = bars[idx + offset - 1]
            d = b_curr.get('delta', 0.0)
            d_prev = b_prev.get('delta', 0.0)
            deltas.append(d)
            delta_diffs.append(d - d_prev)
            imbs.append(b_curr.get('imbalance', 0.0))
            
            ref_price = bars[idx]['low'] if 'BOTTOM' in label else bars[idx]['high']
            price_diffs.append(b_curr['close'] - ref_price)
            
            h = b_curr['high']
            l = b_curr['low']
            o = b_curr['open']
            c = b_curr['close']
            candle_len = max(h - l, 0.01)
            if 'BOTTOM' in label:
                wick = min(o, c) - l
            else:
                wick = h - max(o, c)
            wicks.append(wick / candle_len)
            
        avg_d = np.mean(deltas)
        avg_dd = np.mean(delta_diffs)
        avg_pd = np.mean(price_diffs)
        avg_imb = np.mean(imbs)
        avg_wick = np.mean(wicks) * 100
        
        name = "PEAK/VALLEY (0)" if offset == 0 else f"Bar {offset:+d}"
        print(f"{name:<8} | {avg_d:>+6.1f} | {avg_dd:>+12.1f} | {avg_pd:>+12.2f} | {avg_imb:>+8.3f} | {avg_wick:>6.1f}%")

print_timeline(bottoms, "SWING LOWS (BOTTOMS)")
print_timeline(tops, "SWING HIGHS (TOPS)")
