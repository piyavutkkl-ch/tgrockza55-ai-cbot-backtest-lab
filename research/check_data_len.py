import sys
import os
sys.path.append(r'd:\cbot-atgvt\research')
from optimize_all_strategies import load_market_data

for sym in ['BTCUSD', 'ETHUSD', 'GOLD-PERP', 'XAUUSD']:
    try:
        d = load_market_data(sym)
        if d:
            print(f"{sym}: {len(d)} minute bars loaded (From {d[0]['time']} to {d[-1]['time']})")
        else:
            print(f"{sym}: 0 rows loaded")
    except Exception as e:
        print(f"{sym}: Error {e}")
