import sys, os, csv, math
from collections import defaultdict
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')

base = r'C:\Users\Strong Baesus PC1\AppData\Local\BacktestLab\live\XAUUSD'

min_file = os.path.join(base, 'min-2026-11.csv')
flow_file = os.path.join(base, 'flow-2026-11.csv')
tick_file = os.path.join(base, 'tick-2026-11-02.csv')
book_file = os.path.join(base, 'book-2026-11-02.csv')

print("================================================================================")
print("           XAUUSD EMPIRICAL MICROSTRUCTURE RESEARCH: 2026-11-02                 ")
print("================================================================================")

# 1. MIN BARS ANALYSIS
bars = []
with open(min_file, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for r in reader:
        # filter only today's bars (or all recorded in this batch)
        bars.append({
            'time': r['time'],
            'open': float(r['open']),
            'high': float(r['high']),
            'low': float(r['low']),
            'close': float(r['close']),
            'range': float(r['high']) - float(r['low']),
            'ticks': int(r['ticks']) if r['ticks'] else 0,
            'tickVolume': int(r['tickVolume']) if r['tickVolume'] else 0,
            'spreadAvg': float(r['spreadAvg']) if r['spreadAvg'] else 0.0,
            'spreadMax': float(r['spreadMax']) if r['spreadMax'] else 0.0,
            'imbalance': float(r['imbalance']) if r['imbalance'] else 0.0,
        })

print(f"Total M1 Bars Recorded: {len(bars)}")
print(f"Time Range: {bars[0]['time']} to {bars[-1]['time']}")

closes = [b['close'] for b in bars]
highs = [b['high'] for b in bars]
lows = [b['low'] for b in bars]
ranges = [b['range'] for b in bars]
spreads = [b['spreadAvg'] for b in bars]

min_p = min(lows)
max_p = max(highs)
print(f"Price Extremes Today: Low = ${min_p:.2f} | High = ${max_p:.2f} | Total Day Range = ${max_p - min_p:.2f} USD")

# SPREAD STATISTICS
spreads_np = np.array(spreads)
print("\n--- SPREAD DISTRIBUTION (The Hurdle to Beat) ---")
print(f"Min Spread:    ${np.min(spreads_np):.3f}")
print(f"25th %-tile:   ${np.percentile(spreads_np, 25):.3f}")
print(f"Median Spread: ${np.median(spreads_np):.3f}")
print(f"Mean Spread:   ${np.mean(spreads_np):.3f}")
print(f"75th %-tile:   ${np.percentile(spreads_np, 75):.3f}")
print(f"90th %-tile:   ${np.percentile(spreads_np, 90):.3f}")
print(f"99th %-tile:   ${np.percentile(spreads_np, 99):.3f}")
print(f"Max Spread:    ${np.max(spreads_np):.3f}")

# CANDLE RANGE (M1 Opportunity Size)
ranges_np = np.array(ranges)
print("\n--- M1 BAR RANGE (OPPORTUNITY SIZE) ---")
print(f"Min Range:     ${np.min(ranges_np):.2f}")
print(f"25th %-tile:   ${np.percentile(ranges_np, 25):.2f}")
print(f"Median Range:  ${np.median(ranges_np):.2f}")
print(f"Mean Range:    ${np.mean(ranges_np):.2f}")
print(f"75th %-tile:   ${np.percentile(ranges_np, 75):.2f}")
print(f"90th %-tile:   ${np.percentile(ranges_np, 90):.2f}")
print(f"Max Range:     ${np.max(ranges_np):.2f}")

# EDGE RATIO: Range / Spread
median_spread = np.median(spreads_np)
median_range = np.median(ranges_np)
edge_ratio = median_range / median_spread
print(f"\n--- INTRADAY EDGE RATIO (Bar Range vs Spread Friction) ---")
print(f"Median 1-Min Bar Range: ${median_range:.2f}")
print(f"Median Spread:          ${median_spread:.3f}")
print(f"Edge Factor (Range/Spread): {edge_ratio:.1f}x")
print(f"-> Meaning: A typical 1-minute bar moves {edge_ratio:.1f} TIMES larger than the spread friction!")
print(f"-> In dollar terms: Overcoming a ${median_spread:.2f} spread requires capturing just ~{(median_spread/median_range)*100:.1f}% of a single M1 bar!")

# 2. FLOW DATA (DELTA & CVD & VWAP)
flow = {}
with open(flow_file, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for r in reader:
        flow[r['time']] = {
            'delta': float(r['delta']) if r['delta'] else 0.0,
            'cvd': float(r['cvd']) if r['cvd'] else 0.0,
            'vwapDay': float(r['vwapDay']) if r['vwapDay'] else 0.0,
            'poc': float(r['poc']) if r['poc'] else 0.0,
            'high60': float(r['high60']) if r['high60'] else 0.0,
            'low60': float(r['low60']) if r['low60'] else 0.0,
        }

# Merge Flow into Bars
for b in bars:
    fl = flow.get(b['time'], {})
    b['delta'] = fl.get('delta', 0.0)
    b['cvd'] = fl.get('cvd', 0.0)
    b['vwapDay'] = fl.get('vwapDay', b['close'])
    b['poc'] = fl.get('poc', b['close'])

# 3. IDENTIFY KEY TURNING POINTS (SWINGS) TODAY
# Find major swing highs and swing lows (lookback 15 bars each side)
swing_highs = []
swing_lows = []

for i in range(15, len(bars) - 15):
    curr_h = bars[i]['high']
    curr_l = bars[i]['low']
    
    is_high = True
    for j in range(i - 15, i + 16):
        if j != i and bars[j]['high'] > curr_h:
            is_high = False
            break
    if is_high:
        # Measure subsequent drop over next 15 bars
        future_low = min(bars[k]['low'] for k in range(i + 1, min(i + 20, len(bars))))
        drop = curr_h - future_low
        swing_highs.append({
            'index': i,
            'time': bars[i]['time'],
            'high': curr_h,
            'drop': drop,
            'bar': bars[i]
        })

    is_low = True
    for j in range(i - 15, i + 16):
        if j != i and bars[j]['low'] < curr_l:
            is_low = False
            break
    if is_low:
        # Measure subsequent rally over next 15 bars
        future_high = max(bars[k]['high'] for k in range(i + 1, min(i + 20, len(bars))))
        rally = future_high - curr_l
        swing_lows.append({
            'index': i,
            'time': bars[i]['time'],
            'low': curr_l,
            'rally': rally,
            'bar': bars[i]
        })

print("\n================================================================================")
print(f"  FOUND {len(swing_highs)} MAJOR SWING HIGHS & {len(swing_lows)} MAJOR SWING LOWS TODAY")
print("================================================================================")

# Sort by move size (cleanest reversals)
swing_highs.sort(key=lambda x: x['drop'], reverse=True)
swing_lows.sort(key=lambda x: x['rally'], reverse=True)

print("\n--- TOP 3 SWING HIGHS (Cleanest Sell Opportunities) ---")
for idx, sh in enumerate(swing_highs[:3]):
    b = sh['bar']
    print(f"\n[TOP #{idx+1} SELL SWING] Time: {sh['time']} | Peak High: ${sh['high']:.2f} | Drop: ${sh['drop']:.2f} USD")
    print(f"  Spread at High: ${b['spreadAvg']:.3f} (Max ${b['spreadMax']:.3f})")
    print(f"  DOM Imbalance: {b['imbalance']:+.3f}")
    print(f"  Bar Delta: {b['delta']:+.0f} | CVD: {b['cvd']:+.0f}")
    print(f"  VWAP: ${b['vwapDay']:.2f} (Price vs VWAP: ${sh['high'] - b['vwapDay']:+.2f})")
    
    # Inspect 3 bars before and 3 bars after
    i = sh['index']
    print("  Pre-turn bars & Post-turn progression:")
    for k in range(max(0, i-2), min(len(bars), i+4)):
        tag = "==> PEAK" if k == i else ("Pre " if k < i else "Post")
        bk = bars[k]
        print(f"    [{tag}] {bk['time']} | C: ${bk['close']:.2f} | H: ${bk['high']:.2f} | L: ${bk['low']:.2f} | Delta: {bk['delta']:+.0f} | Imb: {bk['imbalance']:+.3f}")

print("\n--- TOP 3 SWING LOWS (Cleanest Buy Opportunities) ---")
for idx, sl in enumerate(swing_lows[:3]):
    b = sl['bar']
    print(f"\n[TOP #{idx+1} BUY SWING] Time: {sl['time']} | Bottom Low: ${sl['low']:.2f} | Rally: ${sl['rally']:.2f} USD")
    print(f"  Spread at Low: ${b['spreadAvg']:.3f} (Max ${b['spreadMax']:.3f})")
    print(f"  DOM Imbalance: {b['imbalance']:+.3f}")
    print(f"  Bar Delta: {b['delta']:+.0f} | CVD: {b['cvd']:+.0f}")
    print(f"  VWAP: ${b['vwapDay']:.2f} (Price vs VWAP: ${sl['low'] - b['vwapDay']:+.2f})")

    i = sl['index']
    print("  Pre-turn bars & Post-turn progression:")
    for k in range(max(0, i-2), min(len(bars), i+4)):
        tag = "==> BOTTOM" if k == i else ("Pre " if k < i else "Post")
        bk = bars[k]
        print(f"    [{tag}] {bk['time']} | C: ${bk['close']:.2f} | H: ${bk['high']:.2f} | L: ${bk['low']:.2f} | Delta: {bk['delta']:+.0f} | Imb: {bk['imbalance']:+.3f}")
