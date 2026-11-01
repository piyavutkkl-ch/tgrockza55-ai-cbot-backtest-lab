import sys
sys.stdout.reconfigure(encoding='utf-8')
from optimize_all_strategies import load_market_data

for sym in ['BTCUSD', 'ETHUSD', 'GOLD-PERP']:
    d = load_market_data(sym)
    if not d:
        print(f"No data for {sym}")
        continue
    ranges = [x['high'] - x['low'] for x in d]
    ticks = [x['ticks'] for x in d]
    imbs = [x['imbalance'] for x in d]
    deltas = [x['delta'] for x in d]
    cvds = [x['cvd'] for x in d]
    spreads = [x['spread'] for x in d]
    print(f"=== {sym} ({len(d)} bars) ===")
    print(f"Price: {d[0]['close']} -> {d[-1]['close']}")
    print(f"Mean Range: {sum(ranges)/len(ranges):.3f}, Max Range: {max(ranges):.3f}")
    print(f"Mean Ticks: {sum(ticks)/len(ticks):.1f}, Max Ticks: {max(ticks):.1f}")
    print(f"Mean Abs Imb: {sum(abs(x) for x in imbs)/len(imbs):.4f}, Max Abs Imb: {max(abs(x) for x in imbs):.4f}")
    print(f"Mean Abs Delta: {sum(abs(x) for x in deltas)/len(deltas):.2f}, Max Abs Delta: {max(abs(x) for x in deltas):.2f}")
    print(f"Min/Max CVD: {min(cvds):.2f} / {max(cvds):.2f}")
    print(f"Mean Spread: {sum(spreads)/len(spreads):.3f}")
