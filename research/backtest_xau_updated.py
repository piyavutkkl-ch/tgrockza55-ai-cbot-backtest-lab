import sys, os, csv
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from research.find_high_profit_strategy import load_data
from research.test_trend_filter_full import test_5pillar_full

bars = load_data('XAUUSD')
print(f"Loaded XAUUSD total bars: {len(bars)}")
print(f"Date range: {bars[0]['time']} to {bars[-1]['time']}")
print(f"Start Price: {bars[0]['close']} | End Price: {bars[-1]['close']} (Change: {bars[-1]['close'] - bars[0]['close']:+.2f} USD)")

# 1. Run Baseline (Without Trend Filter)
res_baseline = test_5pillar_full(bars, trend_filter=False)

# 2. Run Champion (With Macro Trend Filter)
res_champ = test_5pillar_full(bars, trend_filter=True)

print("\n" + "="*80)
print("                    XAUUSD FULL BACKTEST BENCHMARK RESULTS")
print("="*80)
print(f"{'Metric':<30} | {'Baseline (No Trend Filter)':<25} | {'Champion (Macro Trend Shield)':<25}")
print("-"*80)
print(f"{'Total Trades':<30} | {res_baseline['trades']:<25} | {res_champ['trades']:<25}")
print(f"{'Win Rate':<30} | {res_baseline['win_rate']}% ({res_baseline['wins']}W / {res_baseline['losses']}L) | {res_champ['win_rate']}% ({res_champ['wins']}W / {res_champ['losses']}L)")
print(f"{'Net Profit (USD)':<30} | ${res_baseline['net_pnl']:<24.2f} | ${res_champ['net_pnl']:<24.2f}")
print(f"{'Profit Factor (PF)':<30} | {res_baseline['pf']:<25.2f} | {res_champ['pf']:<25.2f}")
print(f"{'Max Drawdown':<30} | ${res_baseline['max_dd']:<24.2f} | ${res_champ['max_dd']:<24.2f}")
print(f"{'Gross Wins':<30} | ${res_baseline['gross_win']:<24.2f} | ${res_champ['gross_win']:<24.2f}")
print(f"{'Gross Losses':<30} | ${res_baseline['gross_loss']:<24.2f} | ${res_champ['gross_loss']:<24.2f}")
print("="*80)

# Day by day breakdown for Champion Model
by_day = defaultdict(lambda: {'wins': 0, 'losses': 0, 'bes': 0, 'pnl': 0.0, 'trades': 0, 'gross_win': 0.0, 'gross_loss': 0.0})
for tr in res_champ['trade_list']:
    day = tr['time_in'][:10]
    by_day[day]['trades'] += 1
    if tr['pnl'] > 0:
        by_day[day]['wins'] += 1
        by_day[day]['gross_win'] += tr['pnl']
    elif tr['pnl'] < 0:
        by_day[day]['losses'] += 1
        by_day[day]['gross_loss'] += abs(tr['pnl'])
    else:
        by_day[day]['bes'] += 1
    by_day[day]['pnl'] += tr['pnl']

print("\n--- CHAMPION MODEL: DAY-BY-DAY BREAKDOWN ---")
print(f"{'Date':<12} | {'Trades':<8} | {'Win Rate':<10} | {'W / L':<10} | {'Net PnL (USD)':<15} | {'Profit Factor':<12}")
print("-"*75)
for day in sorted(by_day.keys()):
    d = by_day[day]
    wr = d['wins'] / d['trades'] * 100 if d['trades'] > 0 else 0
    pf = (d['gross_win'] / d['gross_loss']) if d['gross_loss'] > 0 else 99.0
    print(f"{day:<12} | {d['trades']:<8} | {wr:>5.1f}%    | {d['wins']}W / {d['losses']}L    | ${d['pnl']:>+12.2f}  | {pf:>6.2f}")

print("\n--- LATEST TRADES (Nov 4 - Nov 5) ---")
recent_trades = [tr for tr in res_champ['trade_list'] if tr['time_in'] >= '2026-11-04']
for tr in recent_trades:
    print(f"Trade #{tr['id']:02d} | {tr['time_in']} -> {tr['time_out']} | {tr['side']:<4} | In: {tr['entry']:.2f} Out: {tr['exit']:.2f} | PnL: ${tr['pnl']:>+5.2f} | Reason: {tr['reason']}")

# Parameter Sweep on the updated data: What if SL=3.5, 4.0 or RR=2.5, 3.0?
print("\n" + "="*80)
print("             PARAMETER FINE-TUNING ON UPDATED GOLD DATA")
print("="*80)
for sl in [2.5, 3.0, 3.5, 4.0]:
    for rr in [1.5, 2.0, 2.5, 3.0]:
        res = test_5pillar_full(bars, sl=sl, rr=rr, trend_filter=True)
        print(f"SL: ${sl:.1f} | RR: {rr:.1f} (TP: ${sl*rr:.1f}) -> Trades: {res['trades']:<3} | WR: {res['win_rate']:>4.1f}% | Net: ${res['net_pnl']:>+6.2f} USD | PF: {res['pf']:>4.2f} | DD: ${res['max_dd']:>5.2f}")
