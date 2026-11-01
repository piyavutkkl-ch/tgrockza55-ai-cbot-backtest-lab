import sys
import json


sys.stdout.reconfigure(encoding='utf-8')
from research.analyze_1hour_turning_points import load_data, pivot_data

records = load_data()
symbols, times, series, spread_series = pivot_data(records)
btc_p = series['BTCUSD']
btc_sp = spread_series['BTCUSD']
eth_p = series['ETHUSD']
eth_sp = spread_series['ETHUSD']
sol_p = series['SOLUSD']
sol_sp = spread_series['SOLUSD']
gold_p = series['GOLD-PERP']

print(f"Total Snapshots: {len(btc_p)}")

# 1. Test Momentum Trend Follower on BTCUSD:
# If BTCUSD moves > delta_thresh within lookback snapshots, follow the direction
best_mom = None
best_mom_net = -999999

results = []

for lookback in [2, 3, 5, 8]:
    for delta_thresh in [12.0, 15.0, 20.0, 25.0, 30.0]:
        for sl_usd in [12.0, 15.0, 20.0, 25.0]:
            for trail_usd in [10.0, 15.0, 20.0, 25.0]:
                trades = []
                net = 0.0
                i = lookback
                while i < len(btc_p) - 10:
                    delta = btc_p[i] - btc_p[i-lookback]
                    side = None
                    if delta >= delta_thresh:
                        side = 'BUY'
                    elif delta <= -delta_thresh:
                        side = 'SELL'
                    
                    if side:
                        entry = btc_p[i]
                        spread = btc_sp[i] * 0.1
                        best_diff = 0.0
                        gross = 0.0
                        exit_idx = i + 1
                        for j in range(i+1, min(i+35, len(btc_p))):
                            p = btc_p[j]
                            diff = (p - entry) if side == 'BUY' else (entry - p)
                            if diff > best_diff:
                                best_diff = diff
                            if best_diff > trail_usd and (best_diff - diff) >= (trail_usd * 0.5):
                                gross = best_diff - (trail_usd * 0.5)
                                exit_idx = j
                                break
                            if diff <= -sl_usd:
                                gross = -sl_usd
                                exit_idx = j
                                break
                        else:
                            gross = diff
                            exit_idx = min(i+35, len(btc_p)) - 1
                        
                        # Size = 0.05 BTC
                        pnl = (gross - spread) * 0.05
                        net += pnl
                        trades.append(pnl)
                        i = exit_idx + 1 # wait until trade finishes
                    else:
                        i += 1
                
                if len(trades) >= 3:
                    win_rate = len([t for t in trades if t > 0]) / len(trades) * 100
                    results.append({
                        "lookback": lookback,
                        "delta_thresh": delta_thresh,
                        "sl_usd": sl_usd,
                        "trail_usd": trail_usd,
                        "trades": len(trades),
                        "win_rate": round(win_rate, 1),
                        "net_usd": round(net, 2)
                    })
                    if net > best_mom_net:
                        best_mom_net = net
                        best_mom = results[-1]

results.sort(key=lambda x: x["net_usd"], reverse=True)
print("\n=== TOP 5 BTC MOMENTUM STRATEGIES (1 HOUR) ===")
for r in results[:5]:
    print(r)

# 2. Test Lead-Lag Strategy:
# When BTC makes an impulsive move (> $18 within 2 snapshots), does ETH follow?
# BTC leads ETH/SOL!
lead_lag_res = []
for lead_thresh in [15.0, 20.0, 25.0]:
    for hold_snaps in [3, 5, 8, 12]:
        trades_eth = []
        net_eth = 0.0
        i = 2
        while i < len(btc_p) - hold_snaps:
            btc_move = btc_p[i] - btc_p[i-2]
            if abs(btc_move) >= lead_thresh:
                side = 'BUY' if btc_move > 0 else 'SELL'
                # Enter ETH at i+1 (after seeing BTC lead impulse)
                entry_eth = eth_p[i+1]
                exit_eth = eth_p[min(i+1+hold_snaps, len(eth_p)-1)]
                spread_eth = eth_sp[i+1] * 0.01
                diff = (exit_eth - entry_eth) if side == 'BUY' else (entry_eth - exit_eth)
                # Size = 0.5 ETH
                pnl = (diff - spread_eth) * 0.5
                net_eth += pnl
                trades_eth.append(pnl)
                i += hold_snaps + 1
            else:
                i += 1
        if trades_eth:
            wr = len([t for t in trades_eth if t > 0]) / len(trades_eth) * 100
            lead_lag_res.append({
                "lead_thresh": lead_thresh,
                "hold_snaps": hold_snaps,
                "trades": len(trades_eth),
                "win_rate": round(wr, 1),
                "net_usd": round(net_eth, 2)
            })

lead_lag_res.sort(key=lambda x: x["net_usd"], reverse=True)
print("\n=== TOP 3 LEAD-LAG BTC->ETH STRATEGIES ===")
for r in lead_lag_res[:3]:
    print(r)
