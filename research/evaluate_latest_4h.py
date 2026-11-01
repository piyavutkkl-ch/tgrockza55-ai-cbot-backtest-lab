import sys
import csv
import json
import math
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

with open(r'd:\cbot-atgvt\data\live_multi_market_feed.csv', 'r', encoding='utf-8') as f:
    rows = list(csv.DictReader(f))

snapshots = {}
for r in rows:
    t = r['timestamp_utc']
    sym = r['symbol']
    if t not in snapshots:
        snapshots[t] = {}
    snapshots[t][sym] = {
        'mid': float(r['mid']),
        'spread': float(r['spread']),
        'bid': float(r['bid']),
        'ask': float(r['ask'])
    }

times = [t for t in sorted(snapshots.keys()) if len(snapshots[t]) == 4]
t_start = datetime.fromisoformat(times[0])
t_end = datetime.fromisoformat(times[-1])
duration_hours = (t_end - t_start).total_seconds() / 3600.0

btc_p = [snapshots[t]['BTCUSD']['mid'] for t in times]
btc_sp = [snapshots[t]['BTCUSD']['spread'] for t in times]
gold_p = [snapshots[t]['GOLD-PERP']['mid'] for t in times]
gold_sp = [snapshots[t]['GOLD-PERP']['spread'] for t in times]
eth_p = [snapshots[t]['ETHUSD']['mid'] for t in times]
eth_sp = [snapshots[t]['ETHUSD']['spread'] for t in times]
sol_p = [snapshots[t]['SOLUSD']['mid'] for t in times]
sol_sp = [snapshots[t]['SOLUSD']['spread'] for t in times]

print("=" * 60)
print("4-HOUR LIVE RECORDING METRICS (DATA STATUS)")
print("=" * 60)
print(f"Total Snapshots: {len(times)} (Recorded across 4 symbols = {len(times)*4} records)")
print(f"Total Duration:  {duration_hours:.2f} hours ({duration_hours*60:.1f} minutes)")
print(f"Time Window:     {times[0]} to {times[-1]}")
print(f"BTCUSD Range:    ${min(btc_p):.2f} - ${max(btc_p):.2f} (Swing: ${max(btc_p)-min(btc_p):.2f}) | Current: ${btc_p[-1]:.2f}")
print(f"GOLD-PERP Range: ${min(gold_p):.2f} - ${max(gold_p):.2f} (Swing: ${max(gold_p)-min(gold_p):.2f}) | Current: ${gold_p[-1]:.2f}")
print(f"ETHUSD Range:    ${min(eth_p):.2f} - ${max(eth_p):.2f} (Swing: ${max(eth_p)-min(eth_p):.2f}) | Current: ${eth_p[-1]:.2f}")
print(f"SOLUSD Range:    ${min(sol_p):.2f} - ${max(sol_p):.2f} (Swing: ${max(sol_p)-min(sol_p):.2f}) | Current: ${sol_p[-1]:.2f}")
print("-" * 60)

# -------------------------------------------------------------
# STRATEGY 1: GOLD-PERP Mean-Reversion (Extended 4 Hours)
# -------------------------------------------------------------
print("\n[EVALUATION 1] GOLD-PERP Mean-Reversion (Ornstein-Uhlenbeck)")
gold_trades = []
for i in range(10, len(gold_p)-30):
    ma = sum(gold_p[i-10:i]) / 10.0
    dev = gold_p[i] - ma
    side = 'SELL' if dev >= 0.60 else ('BUY' if dev <= -0.60 else None)
    if side:
        entry = gold_p[i]
        sp = gold_sp[i] * 0.01
        gross = 0.0
        exit_idx = i + 1
        for j in range(i+1, min(i+35, len(gold_p))):
            p = gold_p[j]
            d = (p - entry) if side == 'BUY' else (entry - p)
            if d >= 1.50:
                gross = 1.50
                exit_idx = j
                break
            if d <= -0.80:
                gross = -0.80
                exit_idx = j
                break
        else:
            gross = d
            exit_idx = min(i+35, len(gold_p)) - 1
        pnl = (gross - sp) * 1.0 # 1 oz
        gold_trades.append({'time': times[i], 'side': side, 'entry': entry, 'pnl': pnl})
        i = exit_idx + 1
    else:
        i += 1

gold_wins = [t for t in gold_trades if t['pnl'] > 0]
gold_losses = [t for t in gold_trades if t['pnl'] <= 0]
gold_net = sum(t['pnl'] for t in gold_trades)
gold_wr = len(gold_wins) / len(gold_trades) * 100 if gold_trades else 0
gold_pf = sum(t['pnl'] for t in gold_wins) / abs(sum(t['pnl'] for t in gold_losses)) if gold_losses else 999.0

print(f"  Trades: {len(gold_trades)}")
print(f"  Win Rate: {gold_wr:.1f}% ({len(gold_wins)} W / {len(gold_losses)} L)")
print(f"  Net Profit: +${gold_net:.2f} USD")
print(f"  Profit Factor: {gold_pf:.2f}")

# -------------------------------------------------------------
# STRATEGY 2: BTCUSD RSI Extreme Reversal (Patched 4 Hours)
# -------------------------------------------------------------
print("\n[EVALUATION 2] BTCUSD RSI Extreme Reversal (Oscillator Overextension)")
def get_rsi(prices, period=10):
    rsi = [50.0] * len(prices)
    gains, losses = [], []
    for i in range(1, len(prices)):
        d = prices[i] - prices[i-1]
        gains.append(max(0, d))
        losses.append(max(0, -d))
    avg_g = sum(gains[:period]) / period
    avg_l = sum(losses[:period]) / period
    for i in range(period, len(prices)):
        avg_g = (avg_g * (period - 1) + gains[i-1]) / period
        avg_l = (avg_l * (period - 1) + losses[i-1]) / period
        rs = avg_g / avg_l if avg_l != 0 else 100.0
        rsi[i] = 100.0 - (100.0 / (1.0 + rs))
    return rsi

rsi10 = get_rsi(btc_p, 10)
btc_trades = []
i = 12
while i < len(btc_p) - 30:
    side = None
    if rsi10[i] <= 30 and rsi10[i-1] > 30: side = 'BUY'
    elif rsi10[i] >= 70 and rsi10[i-1] < 70: side = 'SELL'
    if side:
        entry = btc_p[i]
        sp = btc_sp[i] * 0.1
        gross = 0.0
        exit_idx = i + 1
        for j in range(i+1, min(i+35, len(btc_p))):
            p = btc_p[j]
            d = (p - entry) if side == 'BUY' else (entry - p)
            if d >= 40.0:
                gross = 40.0
                exit_idx = j
                break
            if d <= -20.0:
                gross = -20.0
                exit_idx = j
                break
        else:
            gross = d
            exit_idx = min(i+35, len(btc_p)) - 1
        pnl = (gross - sp) * 0.05
        btc_trades.append({'time': times[i], 'side': side, 'entry': entry, 'pnl': pnl})
        i = exit_idx + 1
    else:
        i += 1

btc_wins = [t for t in btc_trades if t['pnl'] > 0]
btc_losses = [t for t in btc_trades if t['pnl'] <= 0]
btc_net = sum(t['pnl'] for t in btc_trades)
btc_wr = len(btc_wins) / len(btc_trades) * 100 if btc_trades else 0
btc_pf = sum(t['pnl'] for t in btc_wins) / abs(sum(t['pnl'] for t in btc_losses)) if btc_losses else 999.0

print(f"  Trades: {len(btc_trades)}")
print(f"  Win Rate: {btc_wr:.1f}% ({len(btc_wins)} W / {len(btc_losses)} L)")
print(f"  Net Profit: +${btc_net:.2f} USD")
print(f"  Profit Factor: {btc_pf:.2f}")

# -------------------------------------------------------------
# STRATEGY 3: BTC -> ETH Latency Lead-Lag Impulse (4 Hours)
# -------------------------------------------------------------
print("\n[EVALUATION 3] BTC -> ETH Latency Lead-Lag (Filter: Impulses >= $35)")
eth_trades = []
i = 3
while i < len(btc_p) - 10:
    btc_move = btc_p[i] - btc_p[i-3]
    # Filter for significant BTC impulsive thrust >= $35
    if abs(btc_move) >= 35.0:
        side = 'BUY' if btc_move > 0 else 'SELL'
        entry_eth = eth_p[i+1]
        exit_eth = eth_p[min(i+6, len(eth_p)-1)]
        sp_eth = eth_sp[i+1] * 0.01
        diff = (exit_eth - entry_eth) if side == 'BUY' else (entry_eth - exit_eth)
        pnl = (diff - sp_eth) * 0.5 # 0.5 ETH
        eth_trades.append({'time': times[i], 'side': side, 'pnl': pnl})
        i += 7
    else:
        i += 1

eth_wins = [t for t in eth_trades if t['pnl'] > 0]
eth_losses = [t for t in eth_trades if t['pnl'] <= 0]
eth_net = sum(t['pnl'] for t in eth_trades)
eth_wr = len(eth_wins) / len(eth_trades) * 100 if eth_trades else 0
eth_pf = sum(t['pnl'] for t in eth_wins) / abs(sum(t['pnl'] for t in eth_losses)) if eth_losses else 999.0

print(f"  Trades: {len(eth_trades)}")
print(f"  Win Rate: {eth_wr:.1f}% ({len(eth_wins)} W / {len(eth_losses)} L)")
print(f"  Net Profit: +${eth_net:.2f} USD")
print(f"  Profit Factor: {eth_pf:.2f}")

# -------------------------------------------------------------
# COMBINED ENSEMBLE PORTFOLIO (Non-Conflicting 4-Hour Test)
# -------------------------------------------------------------
print("\n" + "=" * 60)
print("COMBINED NON-CONFLICTING ENSEMBLE PORTFOLIO")
print("=" * 60)
all_trades = gold_trades + btc_trades + eth_trades
all_trades.sort(key=lambda x: x['time'])
all_wins = [t for t in all_trades if t['pnl'] > 0]
all_losses = [t for t in all_trades if t['pnl'] <= 0]
total_net = sum(t['pnl'] for t in all_trades)
total_wr = len(all_wins) / len(all_trades) * 100 if all_trades else 0
total_pf = sum(t['pnl'] for t in all_wins) / abs(sum(t['pnl'] for t in all_losses)) if all_losses else 999.0

print(f"Total Portfolio Trades: {len(all_trades)}")
print(f"Overall Win Rate:       {total_wr:.1f}% ({len(all_wins)} ชนะ / {len(all_losses)} แพ้)")
print(f"Total Net PnL:          +${total_net:.2f} USD")
print(f"Portfolio Profit Factor:{total_pf:.2f}")
print("=" * 60)
