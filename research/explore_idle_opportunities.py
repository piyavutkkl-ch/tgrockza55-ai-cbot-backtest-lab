import os
import csv
import gzip
import math

base = os.path.expandvars(r'%LOCALAPPDATA%\BacktestLab\live')

def load_data(sym):
    min_rows = []
    flow_rows = {}
    
    # Load min
    for fname in [f'min-2026-10.csv', f'min-2026-11.csv']:
        p = os.path.join(base, sym, fname)
        if os.path.exists(p):
            with open(p, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for r in reader:
                    min_rows.append(r)
                    
    # Load flow
    for fname in [f'flow-2026-10.csv', f'flow-2026-11.csv']:
        p = os.path.join(base, sym, fname)
        if os.path.exists(p):
            with open(p, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for r in reader:
                    flow_rows[r['time']] = r
                    
    return min_rows, flow_rows

btc_min, btc_flow = load_data('BTCUSD')
eth_min, eth_flow = load_data('ETHUSD')

print(f"Total BTC minutes loaded: {len(btc_min)}")
print(f"Total ETH minutes loaded: {len(eth_min)}")

# Analyze volatility, swing size, and VWAP deviation distribution
for sym, rows, flows in [('BTCUSD', btc_min, btc_flow), ('ETHUSD', eth_min, eth_flow)]:
    print(f"\n==================== {sym} IDLE PERIOD DYNAMICS ====================")
    swings = []
    vwap_devs = []
    cvd_velocities = []
    
    for i in range(15, len(rows)):
        c = float(rows[i]['close'])
        h = max(float(rows[j]['high']) for j in range(i-14, i+1))
        l = min(float(rows[j]['low']) for j in range(i-14, i+1))
        rng = h - l
        swings.append(rng)
        
        t = rows[i]['time']
        if t in flows:
            fl = flows[t]
            vwap = float(fl.get('vwapDay', c))
            dev = c - vwap
            vwap_devs.append(dev)
            
            # CVD change in last 5 min
            t_prev = rows[i-5]['time']
            if t_prev in flows:
                prev_cvd = float(flows[t_prev].get('cvd', 0))
                curr_cvd = float(fl.get('cvd', 0))
                cvd_velocities.append(curr_cvd - prev_cvd)
                
    avg_swing = sum(swings) / len(swings) if swings else 0
    max_swing = max(swings) if swings else 0
    min_swing = min(swings) if swings else 0
    print(f"Rolling 15m Range (Swings): Avg = ${avg_swing:.2f}, Min = ${min_swing:.2f}, Max = ${max_swing:.2f}")
    if vwap_devs:
        avg_dev = sum(abs(d) for d in vwap_devs) / len(vwap_devs)
        max_dev = max(abs(d) for d in vwap_devs)
        print(f"VWAP Distance: Avg Abs = ${avg_dev:.2f}, Max = ${max_dev:.2f}")
    if cvd_velocities:
        avg_cvd_v = sum(abs(v) for v in cvd_velocities) / len(cvd_velocities)
        max_cvd_v = max(abs(v) for v in cvd_velocities)
        print(f"5-min CVD Delta Velocity: Avg Abs = {avg_cvd_v:.1f}, Max = {max_cvd_v:.1f}")
