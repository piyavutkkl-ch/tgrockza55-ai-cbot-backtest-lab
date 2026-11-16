import os
import csv
from datetime import datetime

base = os.path.expandvars(r'%LOCALAPPDATA%\BacktestLab\live')

print("=" * 80)
print("      ALL LIVE SYMBOLS STATUS & RECENT TRADES REPORT")
print(f"      Checked at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)

for sym in ['BTCUSD', 'ETHUSD', 'XAUUSD', 'GOLD-PERP']:
    dir_p = os.path.join(base, sym)
    if not os.path.exists(dir_p):
        print(f"[{sym}] Directory not found")
        continue
    
    # Check minutes recorded
    min_files = [f for f in os.listdir(dir_p) if f.startswith('min-')]
    total_min = 0
    for mf in min_files:
        with open(os.path.join(dir_p, mf), 'r', encoding='utf-8') as fp:
            total_min += max(0, sum(1 for _ in fp) - 1)
            
    # Check trades
    tf = os.path.join(dir_p, 'trades.csv')
    trades = []
    if os.path.exists(tf):
        with open(tf, 'r', encoding='utf-8') as fp:
            trades = list(csv.DictReader(fp))
            
    print(f"\n--- {sym} ---")
    print(f"Continuous M1 Bars Recorded: {total_min} bars (~{total_min/60:.1f} hours)")
    print(f"Total Trade Events: {len(trades)} events")
    
    closes = [t for t in trades if t.get('event') == 'CLOSE']
    opens = [t for t in trades if t.get('event') == 'OPEN']
    print(f"Completed Trades (Closed): {len(closes)}")
    
    if closes:
        wins = [t for t in closes if float(t.get('net', 0) or 0) > 0]
        losses = [t for t in closes if float(t.get('net', 0) or 0) <= 0]
        net_usd = sum(float(t.get('net', 0) or 0) for t in closes)
        wr = len(wins) / len(closes) * 100 if closes else 0
        print(f"Win Rate: {wr:.1f}% ({len(wins)} wins / {len(losses)} losses) | Net PnL: ${net_usd:+.2f} USD")
        print("Last 3 Closed Trades:")
        for t in closes[-3:]:
            print(f"   - {t.get('time')} | {t.get('side')} at {t.get('price')} | Net: ${float(t.get('net',0) or 0):+.2f} | Reason: {t.get('reason')} | Balance: ${t.get('balance')}")
    else:
        print("No closed trades yet.")
