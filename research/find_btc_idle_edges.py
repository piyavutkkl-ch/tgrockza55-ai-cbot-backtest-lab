import os
import csv
import math

base = os.path.expandvars(r'%LOCALAPPDATA%\BacktestLab\live')

def load_data(sym):
    min_rows = []
    flow_map = {}
    for fn in ['min-2026-10.csv', 'min-2026-11.csv']:
        p = os.path.join(base, sym, fn)
        if os.path.exists(p):
            with open(p, 'r', encoding='utf-8') as f:
                min_rows.extend(list(csv.DictReader(f)))
    for fn in ['flow-2026-10.csv', 'flow-2026-11.csv']:
        p = os.path.join(base, sym, fn)
        if os.path.exists(p):
            with open(p, 'r', encoding='utf-8') as f:
                for r in csv.DictReader(f):
                    flow_map[r['time']] = r
    return min_rows, flow_map

btc_min, btc_flow = load_data('BTCUSD')

# Scan for profitable 15-minute forward moves > $60
fwd_moves = []
for i in range(20, len(btc_min) - 15):
    c0 = float(btc_min[i]['close'])
    max_up = max(float(btc_min[k]['high']) for k in range(i+1, i+16)) - c0
    max_down = c0 - min(float(btc_min[k]['low']) for k in range(i+1, i+16))
    
    t = btc_min[i]['time']
    fl = btc_flow.get(t, {})
    
    # Check features at bar i
    ticks = float(btc_min[i].get('ticks', 0))
    vol = float(btc_min[i].get('tickVolume', 0))
    imb = float(btc_min[i].get('imbalance', 0)) if 'imbalance' in btc_min[i] else 0.0
    delta = float(fl.get('delta', 0))
    cvd = float(fl.get('cvd', 0))
    
    # 3-bar price change
    c_prev3 = float(btc_min[i-3]['close'])
    ret3 = c0 - c_prev3
    
    # 3-bar delta change
    t_prev3 = btc_min[i-3]['time']
    delta3 = cvd - float(btc_flow.get(t_prev3, {}).get('cvd', cvd))
    
    fwd_moves.append({
        'i': i, 'time': t, 'close': c0,
        'max_up': max_up, 'max_down': max_down,
        'delta': delta, 'delta3': delta3, 'imb': imb,
        'ret3': ret3, 'ticks': ticks
    })

print(f"Total bars analyzed: {len(fwd_moves)}")

# What predicts a big UP move (> $60) vs big DOWN move (> $60)?
big_up = [m for m in fwd_moves if m['max_up'] >= 60.0 and m['max_down'] < 30.0]
big_down = [m for m in fwd_moves if m['max_down'] >= 60.0 and m['max_up'] < 30.0]

print(f"Clean Big UP moves (> $60 up, < $30 adverse): {len(big_up)}")
print(f"Clean Big DOWN moves (> $60 down, < $30 adverse): {len(big_down)}")

# Inspect feature averages
if big_up:
    avg_delta3_up = sum(m['delta3'] for m in big_up) / len(big_up)
    avg_ret3_up = sum(m['ret3'] for m in big_up) / len(big_up)
    avg_imb_up = sum(m['imb'] for m in big_up) / len(big_up)
    print(f"UP moves characteristics: Ret3 = ${avg_ret3_up:.1f}, Delta3 = {avg_delta3_up:.1f}, Imbalance = {avg_imb_up:+.3f}")

if big_down:
    avg_delta3_dn = sum(m['delta3'] for m in big_down) / len(big_down)
    avg_ret3_dn = sum(m['ret3'] for m in big_down) / len(big_down)
    avg_imb_dn = sum(m['imb'] for m in big_down) / len(big_down)
    print(f"DOWN moves characteristics: Ret3 = ${avg_ret3_dn:.1f}, Delta3 = {avg_delta3_dn:.1f}, Imbalance = {avg_imb_dn:+.3f}")

# Sample up moves:
print("\nSample clean UP moves:")
for m in big_up[:5]:
    print(f"  {m['time']} | Close={m['close']:.1f} | Up={m['max_up']:.1f} Dn={m['max_down']:.1f} | Ret3={m['ret3']:.1f} Delta3={m['delta3']:.1f} Imb={m['imb']:+.3f}")

print("\nSample clean DOWN moves:")
for m in big_down[:5]:
    print(f"  {m['time']} | Close={m['close']:.1f} | Dn={m['max_down']:.1f} Up={m['max_up']:.1f} | Ret3={m['ret3']:.1f} Delta3={m['delta3']:.1f} Imb={m['imb']:+.3f}")
