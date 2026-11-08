import sys, os, csv, math
from collections import defaultdict
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from research.find_high_profit_strategy import load_data
from research.exhaustive_extrema_quant_search import run_backtest_engine

symbols = ['XAUUSD', 'GOLD-PERP', 'BTCUSD', 'ETHUSD']

print("="*90)
print("     EXTREMA REVERSAL BENCHMARK: ANCHORED VWAP + DELTA ABSORPTION")
print("="*90)

for sym in symbols:
    bars = load_data(sym)
    n = len(bars)
    start_t = bars[0]['time']
    end_t = bars[-1]['time']
    
    sl_base = 4.0 if 'XAU' in sym or 'GOLD' in sym else (80.0 if 'BTC' in sym else 6.0)
    
    print(f"\n>>> SYMBOL: {sym} ({n} bars, {start_t} to {end_t}) <<<")
    print(f"{'SD Mult':<8} | {'SL':<8} | {'RR':<5} | {'BE (R)':<8} | {'Trades':<8} | {'Win Rate':<10} | {'Net PnL (USD)':<15} | {'PF':<6} | {'Max DD':<8}")
    print("-" * 90)

    best_pnl = -9999
    best_cfg = None

    for sd_mult in [0.8, 1.0, 1.2, 1.5]:
        for rr in [2.0, 2.5, 3.0]:
            for be_r in [0.0, 1.0]:
                res = run_backtest_engine(bars, symbol=sym,
                                          trigger_type='VWAP_ABS',
                                          delta_thresh=5.0 if 'XAU' in sym or 'GOLD' in sym else 10.0,
                                          sl=sl_base,
                                          rr=rr,
                                          be_trigger_r=be_r,
                                          macro_trend=True,
                                          circuit_breaker=True)
                if res['trades'] >= 5:
                    if res['net_pnl'] > best_pnl:
                        best_pnl = res['net_pnl']
                        best_cfg = (sd_mult, sl_base, rr, be_r, res)
                    print(f"{sd_mult:<8.1f} | ${sl_base:<7.1f} | {rr:<5.1f} | {be_r:<8.1f} | {res['trades']:<8} | {res['win_rate']:>5.1f}%    | ${res['net_pnl']:>+12.2f}    | {res['pf']:<6.2f} | ${res['max_dd']:<7.2f}")

    if best_cfg:
        b_sd, b_sl, b_rr, b_be, b_res = best_cfg
        print(f"\n  ★ BEST CONFIG FOR {sym}: SD={b_sd}, SL=${b_sl}, RR={b_rr}, BE={b_be} -> Net PnL: ${b_res['net_pnl']:+.2f} USD, PF: {b_res['pf']}, WR: {b_res['win_rate']}%, DD: ${b_res['max_dd']}")
