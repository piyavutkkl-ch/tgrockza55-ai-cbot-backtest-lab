import os
import sys
import csv
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

LIVE_BASE = os.path.expandvars(r'%LOCALAPPDATA%\BacktestLab\live')

for sym in ['BTCUSD', 'ETHUSD', 'XAUUSD']:
    p = os.path.join(LIVE_BASE, sym, 'trades.csv')
    if not os.path.exists(p):
        continue
    with open(p, 'r', encoding='utf-8') as f:
        rows = list(csv.DictReader(f))
    
    opens = {r['id']: r for r in rows if r.get('event') == 'OPEN'}
    closes = [r for r in rows if r.get('event') == 'CLOSE']
    
    print(f"\n==================== {sym} FORENSIC ({len(closes)} closed deals) ====================")
    total_net = sum(float(c.get('net', 0) or 0) for c in closes)
    wins = [c for c in closes if float(c.get('net', 0) or 0) > 0]
    losses = [c for c in closes if float(c.get('net', 0) or 0) < 0]
    print(f"Total Net PnL: ${total_net:.2f} | Wins: {len(wins)} | Losses: {len(losses)} | WinRate: {len(wins)/len(closes)*100:.1f}%")
    
    # Read min file to check price range and spread
    min_file = os.path.join(LIVE_BASE, sym, 'min-2026-11.csv')
    spreads = []
    if os.path.exists(min_file):
        with open(min_file, 'r', encoding='utf-8') as mf:
            m_rows = list(csv.DictReader(mf))
            spreads = [float(r['spreadAvg']) for r in m_rows if r.get('spreadAvg')]
    if spreads:
        print(f"Spread stats: Min=${min(spreads):.2f}, Median=${sorted(spreads)[len(spreads)//2]:.2f}, Max=${max(spreads):.2f}")

    for idx, c in enumerate(closes, 1):
        op = opens.get(c['id'], {})
        entry_p = float(op.get('price', 0) or 0)
        exit_p = float(c.get('price', 0) or 0)
        net = float(c.get('net', 0) or 0)
        spread = float(c.get('spread', 0) or op.get('spread', 0) or 0)
        slippage = float(c.get('slippage', 0) or 0)
        reason = c.get('reason', '')
        open_time = op.get('time', '')
        close_time = c.get('time', '')
        
        # Calculate price delta
        price_delta = exit_p - entry_p if c.get('side') == 'Buy' else entry_p - exit_p
        
        print(f"Deal #{idx} [ID:{c['id']}]: Side={c['side']} | Entry=${entry_p:.2f} -> Exit=${exit_p:.2f} (Δ={price_delta:+.2f}) | Net=${net:+.2f} | Reason={reason} | Spread=${spread:.2f} | Slip=${slippage:+.2f} | Open={open_time} -> Close={close_time}")
