import sys
sys.path.append(r'd:\cbot-atgvt\research')
from optimize_all_strategies import load_market_data, sim_vwap_scalp

data = load_market_data('ETHUSD')
print(f"Total ETH data bars: {len(data)}")

for dev in [3.0, 4.0, 5.0, 6.0, 8.0]:
    for tp in [2.5, 3.5, 4.5, 6.0]:
        for sl in [1.5, 2.5, 3.5]:
            m = sim_vwap_scalp(data, dev, tp, sl, max_hold=25, point_val=0.01, spread_cost=0.023)
            if m['trades'] >= 5:
                print(f"dev={dev:>4.1f}, tp={tp:>4.1f}, sl={sl:>4.1f} | Trades: {m['trades']:>3}, WR: {m['win_rate']:>5.1f}%, Net: ${m['net_pnl']:>6.2f}, PF: {m['profit_factor']:>4.2f}")
