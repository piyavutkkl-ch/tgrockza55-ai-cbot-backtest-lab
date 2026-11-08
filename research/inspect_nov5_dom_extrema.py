import sys, os, csv, gzip
from collections import defaultdict
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')

base = r'C:\Users\Strong Baesus PC1\AppData\Local\BacktestLab\live\XAUUSD'
book_file = os.path.join(base, 'book-2026-11-05.csv')
flow_file = os.path.join(base, 'flow-2026-11.csv')
min_file = os.path.join(base, 'min-2026-11.csv')

# Load Nov 5 M1 bars
nov5_bars = []
with open(min_file, 'r', encoding='utf-8') as f:
    r = csv.DictReader(f)
    for row in r:
        if row['time'].startswith('2026-11-05'):
            nov5_bars.append({
                'time': row['time'],
                'open': float(row['open']),
                'high': float(row['high']),
                'low': float(row['low']),
                'close': float(row['close']),
                'spread': float(row['spreadAvg']) if row['spreadAvg'] else 0.12,
                'imbalance': float(row['imbalance']) if row['imbalance'] else 0.0,
                'bidVol': float(row['bidVol']) if row['bidVol'] else 0.0,
                'askVol': float(row['askVol']) if row['askVol'] else 0.0,
            })

# Merge flow
with open(flow_file, 'r', encoding='utf-8') as f:
    r = csv.DictReader(f)
    flow_map = {row['time']: row for row in r if row['time'].startswith('2026-11-05')}
    for b in nov5_bars:
        fl = flow_map.get(b['time'])
        if fl:
            b['delta'] = float(fl['delta']) if fl['delta'] else 0.0
            b['cvd'] = float(fl['cvd']) if fl['cvd'] else 0.0
            b['vwap'] = float(fl['vwapDay']) if fl['vwapDay'] else b['close']
            b['sd'] = float(fl['sdDay']) if fl['sdDay'] else 3.5
            b['val'] = float(fl['val']) if fl['val'] else b['low']
            b['vah'] = float(fl['vah']) if fl['vah'] else b['high']
            b['ladderBid'] = float(fl['ladderBid']) if fl['ladderBid'] else 0.0
            b['ladderAsk'] = float(fl['ladderAsk']) if fl['ladderAsk'] else 0.0

print(f"Loaded {len(nov5_bars)} M1 bars for 2026-11-05")

# Find turning points on Nov 5
bottoms = []
tops = []
for i in range(15, len(nov5_bars) - 20):
    curr = nov5_bars[i]
    lows_past = [nov5_bars[j]['low'] for j in range(i-10, i)]
    highs_future = [nov5_bars[j]['high'] for j in range(i+1, i+20)]
    lows_future = [nov5_bars[j]['low'] for j in range(i+1, i+20)]
    highs_past = [nov5_bars[j]['high'] for j in range(i-10, i)]
    
    if curr['low'] <= min(lows_past) and (max(highs_future) - curr['low']) >= 4.0:
        bottoms.append((i, curr))
    if curr['high'] >= max(highs_past) and (curr['high'] - min(lows_future)) >= 4.0:
        tops.append((i, curr))

print(f"Nov 5 Turning Points: {len(bottoms)} bottoms, {len(tops)} tops")

# Let's inspect turning points and their DOM features
print("\n" + "="*85)
print("             SAMPLE TURNING POINTS ON NOV 5 WITH ORDER BOOK & TAPE")
print("="*85)
print(f"{'Type':<12} | {'Time':<16} | {'Price':<8} | {'Delta':<7} | {'LadderBid/Ask':<16} | {'Imbalance':<10} | {'VWAP Dist':<10}")
print("-" * 85)

for i, b in bottoms[:10]:
    v_dist = b['close'] - b.get('vwap', b['close'])
    lad = f"{b.get('ladderBid', 0):.2f}/{b.get('ladderAsk', 0):.2f}"
    print(f"{'BOTTOM':<12} | {b['time']:<16} | {b['low']:<8.2f} | {b.get('delta', 0):>+6.0f}  | {lad:<16} | {b.get('imbalance', 0):>+8.3f}   | {v_dist:>+8.2f}")

print("-" * 85)
for i, b in tops[:10]:
    v_dist = b['close'] - b.get('vwap', b['close'])
    lad = f"{b.get('ladderBid', 0):.2f}/{b.get('ladderAsk', 0):.2f}"
    print(f"{'TOP':<12} | {b['time']:<16} | {b['high']:<8.2f} | {b.get('delta', 0):>+6.0f}  | {lad:<16} | {b.get('imbalance', 0):>+8.3f}   | {v_dist:>+8.2f}")
