import sys
sys.path.append(r'd:\cbot-atgvt\research')
from test_vwap_scalp import backtest_vwap_scalp, btc_min, btc_flow

print("=== Testing BTCUSD Parameter Grid ===")
best_res = []
for dev in [20, 30, 40, 50, 60, 80]:
    for tp_r in [0.2, 0.3, 0.5, 0.7]:
        for sl_r in [0.4, 0.6, 0.8, 1.0]:
            r = backtest_vwap_scalp(btc_min, btc_flow, 'BTCUSD', dev, tp_r, sl_r, spread_cost=0.15)
            if r['count'] >= 5:
                best_res.append((r['net_pnl'], dev, tp_r, sl_r, r['count'], r['win_rate'], r['pf']))

best_res.sort(key=lambda x: x[0], reverse=True)
for net, dev, tp_r, sl_r, count, wr, pf in best_res[:15]:
    print(f"Dev={dev:2d} TP_R={tp_r:.1f} SL_R={sl_r:.1f} | Trades={count:2d} WR={wr:5.1f}% Net=+${net:5.2f} PF={pf:5.2f}")
