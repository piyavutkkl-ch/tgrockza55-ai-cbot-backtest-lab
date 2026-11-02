import sys, os
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from research.backtest_dom_recorded import load_dataset, run_backtest

bars = load_dataset('XAUUSD')
print('XAU Bars:', len(bars))

best_pnl = -999.0
best_params = None
best_res = None

# Grid search for XAUUSD
for lb in [10, 15, 20, 30]:
    for imb in [0.02, 0.03, 0.04, 0.05]:
        for sp_ceil in [0.15, 0.20, 0.25]:
            for sl in [1.5, 2.0, 2.5, 3.5]:
                for rr in [1.5, 2.0, 2.5]:
                    for delta in [True, False]:
                        for vwap in [True, False]:
                            p = {
                                'lookback': lb,
                                'imb_thresh': imb,
                                'sl_usd': sl,
                                'rr': rr,
                                'spread_ceiling': sp_ceil,
                                'use_delta': delta,
                                'use_vwap': vwap,
                                'use_be': True
                            }
                            res = run_backtest('XAUUSD', bars, mode='upgraded', params=p)
                            if res['trades'] >= 3 and res['net_pnl'] > best_pnl:
                                best_pnl = res['net_pnl']
                                best_params = p
                                best_res = res

if best_res:
    print(f"BEST XAU: NetPnL=${best_res['net_pnl']} | Trades={best_res['trades']} | WinRate={best_res['win_rate']}% ({best_res['wins']}W/{best_res['losses']}L) | PF={best_res['pf']} | MaxDD=${best_res['max_dd']}")
    print("Params:", best_params)
else:
    print("No parameter set met >= 3 trades")
