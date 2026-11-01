import sys
import csv
import json
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

def run_comprehensive_backtest(csv_path):
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # Group by timestamp
    snapshots = {}
    for r in rows:
        t = r['timestamp_utc']
        sym = r['symbol']
        if t not in snapshots:
            snapshots[t] = {}
        snapshots[t][sym] = {
            'bid': float(r['bid']),
            'ask': float(r['ask']),
            'mid': float(r['mid']),
            'spread': float(r['spread'])
        }

    times = sorted(snapshots.keys())
    valid_times = [t for t in times if len(snapshots[t]) == 4]
    
    btc_p = [snapshots[t]['BTCUSD']['mid'] for t in valid_times]
    btc_sp = [snapshots[t]['BTCUSD']['spread'] for t in valid_times]
    eth_p = [snapshots[t]['ETHUSD']['mid'] for t in valid_times]
    eth_sp = [snapshots[t]['ETHUSD']['spread'] for t in valid_times]
    gold_p = [snapshots[t]['GOLD-PERP']['mid'] for t in valid_times]
    gold_sp = [snapshots[t]['GOLD-PERP']['spread'] for t in valid_times]
    sol_p = [snapshots[t]['SOLUSD']['mid'] for t in valid_times]
    sol_sp = [snapshots[t]['SOLUSD']['spread'] for t in valid_times]

    t_start = datetime.fromisoformat(valid_times[0])
    t_end = datetime.fromisoformat(valid_times[-1])
    duration_hours = (t_end - t_start).total_seconds() / 3600.0

    print(f"Dataset Summary:")
    print(f"Total Snapshots: {len(valid_times)}")
    print(f"Duration: {duration_hours:.2f} hours ({duration_hours*60:.1f} minutes)")
    print(f"BTC Price Range: ${min(btc_p):.2f} - ${max(btc_p):.2f} (Delta: ${max(btc_p)-min(btc_p):.2f})")
    print(f"Gold Price Range: ${min(gold_p):.2f} - ${max(gold_p):.2f} (Delta: ${max(gold_p)-min(gold_p):.2f})")
    print(f"ETH Price Range: ${min(eth_p):.2f} - ${max(eth_p):.2f} (Delta: ${max(eth_p)-min(eth_p):.2f})")
    print(f"SOL Price Range: ${min(sol_p):.2f} - ${max(sol_p):.2f} (Delta: ${max(sol_p)-min(sol_p):.2f})")
    print("-" * 50)

    # 1. Backtest Strategy: BTC -> ETH Lead-Lag
    print("\n--- 1. BACKTEST: BTC -> ETH Lead-Lag (Full 2.5h Dataset) ---")
    best_eth = None
    best_eth_net = -999999
    eth_results = []
    
    for lead_thresh in [15.0, 20.0, 25.0, 30.0]:
        for hold_snaps in [2, 3, 5, 8, 12]:
            trades = []
            i = 2
            while i < len(btc_p) - hold_snaps:
                btc_move = btc_p[i] - btc_p[i-2]
                if abs(btc_move) >= lead_thresh:
                    side = 'BUY' if btc_move > 0 else 'SELL'
                    entry_eth = eth_p[i+1]
                    exit_eth = eth_p[min(i+1+hold_snaps, len(eth_p)-1)]
                    spread_usd = eth_sp[i+1] * 0.01 # spread
                    diff = (exit_eth - entry_eth) if side == 'BUY' else (entry_eth - exit_eth)
                    pnl = (diff - spread_usd) * 0.5 # 0.5 ETH contract
                    trades.append(pnl)
                    i += hold_snaps + 1
                else:
                    i += 1
            if trades:
                wins = [t for t in trades if t > 0]
                losses = [t for t in trades if t <= 0]
                wr = len(wins) / len(trades) * 100
                net = sum(trades)
                gross_win = sum(wins)
                gross_loss = abs(sum(losses)) if losses else 0.001
                pf = gross_win / gross_loss
                res = {
                    'lead_thresh': lead_thresh,
                    'hold_snaps': hold_snaps,
                    'trades': len(trades),
                    'win_rate': round(wr, 1),
                    'net_pnl': round(net, 2),
                    'profit_factor': round(pf, 2)
                }
                eth_results.append(res)
                if net > best_eth_net:
                    best_eth_net = net
                    best_eth = res

    eth_results.sort(key=lambda x: x['net_pnl'], reverse=True)
    for r in eth_results[:4]:
        print(r)

    # 2. Backtest Strategy: GOLD-PERP Mean Reversion
    print("\n--- 2. BACKTEST: GOLD-PERP Mean Reversion (Full 2.5h Dataset) ---")
    best_gold = None
    best_gold_net = -999999
    gold_results = []

    for ma_len in [8, 10, 15, 20]:
        for dev_thresh in [0.6, 0.8, 1.0, 1.2]:
            for tp in [0.8, 1.2, 1.5, 2.0]:
                for sl in [0.8, 1.2, 1.5, 2.0]:
                    trades = []
                    i = ma_len
                    while i < len(gold_p) - 10:
                        ma = sum(gold_p[i-ma_len:i]) / ma_len
                        dev = gold_p[i] - ma
                        side = None
                        if dev >= dev_thresh:
                            side = 'SELL'
                        elif dev <= -dev_thresh:
                            side = 'BUY'
                        
                        if side:
                            entry = gold_p[i]
                            spread = gold_sp[i] * 0.01
                            gross = 0.0
                            exit_idx = i + 1
                            for j in range(i+1, min(i+35, len(gold_p))):
                                p = gold_p[j]
                                diff = (p - entry) if side == 'BUY' else (entry - p)
                                if diff >= tp:
                                    gross = tp
                                    exit_idx = j
                                    break
                                if diff <= -sl:
                                    gross = -sl
                                    exit_idx = j
                                    break
                            else:
                                gross = diff
                                exit_idx = min(i+35, len(gold_p)) - 1
                            
                            pnl = (gross - spread) * 1.0 # 1 oz Gold
                            trades.append(pnl)
                            i = exit_idx + 1
                        else:
                            i += 1
                    
                    if trades:
                        wins = [t for t in trades if t > 0]
                        losses = [t for t in trades if t <= 0]
                        wr = len(wins) / len(trades) * 100
                        net = sum(trades)
                        gross_win = sum(wins)
                        gross_loss = abs(sum(losses)) if losses else 0.001
                        pf = gross_win / gross_loss
                        res = {
                            'ma_len': ma_len,
                            'dev_thresh': dev_thresh,
                            'tp': tp,
                            'sl': sl,
                            'trades': len(trades),
                            'win_rate': round(wr, 1),
                            'net_pnl': round(net, 2),
                            'profit_factor': round(pf, 2)
                        }
                        gold_results.append(res)
                        if net > best_gold_net:
                            best_gold_net = net
                            best_gold = res

    gold_results.sort(key=lambda x: x['net_pnl'], reverse=True)
    for r in gold_results[:4]:
        print(r)

    # 3. Combined Portfolio Equity Curve
    print("\n--- 3. COMBINED PORTFOLIO BACKTEST ---")
    print(f"Best ETH Lead-Lag: {best_eth}")
    print(f"Best Gold Mean-Rev: {best_gold}")
    combined_net = best_eth['net_pnl'] + best_gold['net_pnl']
    print(f"Combined 2.5h Net Profit: +${combined_net:.2f} USD")

if __name__ == '__main__':
    run_comprehensive_backtest(r'd:\cbot-atgvt\data\live_multi_market_feed.csv')
