import sys
sys.path.append(r'd:\cbot-atgvt\research')
from optimize_all_strategies import load_market_data, sim_vwap_scalp

data = load_market_data('GOLD-PERP')
print(f"Total GOLD data bars: {len(data)}")

print("Testing Wide Target VWAP on GOLD-PERP (TP >= $3.00 to crush $1.39 spread):")
for dev in [2.0, 2.5, 3.0, 3.5, 4.0]:
    for tp in [3.0, 4.0, 5.0, 6.0]:
        for sl in [2.0, 3.0, 4.0]:
            for hold in [30, 45, 60]:
                m = sim_vwap_scalp(data, dev, tp, sl, max_hold=hold, point_val=1.00, spread_cost=1.39, comm=0.08)
                if m['trades'] >= 4 and m['net_pnl'] > 0:
                    print(f"dev={dev:>4.1f}, tp={tp:>4.1f}, sl={sl:>4.1f}, hold={hold:>2} | Trades: {m['trades']:>2}, WR: {m['win_rate']:>5.1f}%, Net: ${m['net_pnl']:>+6.2f}, PF: {m['profit_factor']:>4.2f}")
