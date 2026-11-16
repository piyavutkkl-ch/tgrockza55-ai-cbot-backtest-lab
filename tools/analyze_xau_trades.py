import os
import csv

p = os.path.expandvars(r'%LOCALAPPDATA%\BacktestLab\live\XAUUSD\trades.csv')
trades = []
with open(p, 'r', encoding='utf-8') as f:
    reader = csv.reader(f)
    header = next(reader)
    for r in reader:
        if len(r) >= 18 and r[1] == 'CLOSE':
            try:
                net_pnl = float(r[16]) if r[16] else 0.0
                trades.append({
                    'time': r[0],
                    'side': r[3],
                    'lot': r[4],
                    'price': r[6],
                    'pnl': net_pnl,
                    'balance': float(r[17]) if len(r) > 17 and r[17] else 0.0
                })
            except Exception as e:
                pass

print(f'Total closed trades in XAUUSD: {len(trades)}')
wins = [t for t in trades if t['pnl'] > 0]
losses = [t for t in trades if t['pnl'] < 0]
total_pnl = sum(t['pnl'] for t in trades)
gross_win = sum(t['pnl'] for t in wins)
gross_loss = abs(sum(t['pnl'] for t in losses))
pf = (gross_win / gross_loss) if gross_loss > 0 else 999.0
win_rate = (len(wins) / len(trades) * 100) if trades else 0.0

print(f'Wins: {len(wins)}, Losses: {len(losses)}, Win Rate: {win_rate:.1f}%')
print(f'Gross Win: ${gross_win:.2f}, Gross Loss: ${gross_loss:.2f}, PF: {pf:.2f}')
print(f'Total Net PnL: ${total_pnl:.2f}')

# Breakdown by day
by_day = {}
for t in trades:
    d = t['time'].split(' ')[0]
    by_day[d] = by_day.get(d, 0.0) + t['pnl']

print('\nPnL by Day on XAUUSD:')
for d, pnl in sorted(by_day.items()):
    print(f'  {d}: ${pnl:+.2f} USD')

print('\nRecent 10 trades on XAUUSD:')
for t in trades[-10:]:
    tm = t['time']
    sd = t['side']
    pnl = t['pnl']
    bal = t['balance']
    print(f'  {tm} | {sd} | PnL: ${pnl:+.2f} | Bal: ${bal:.2f}')
