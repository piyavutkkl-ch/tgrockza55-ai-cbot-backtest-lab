import sys
sys.path.append(r'd:\cbot-atgvt\research')
from optimize_all_strategies import load_market_data, sim_vwap_scalp

data = load_market_data('ETHUSD')
print(f"Total ETH data bars: {len(data)}")

print("Testing Wide Target VWAP on ETH (TP >= $6.00 to crush $2.30 spread):")
for dev in [6.0, 8.0, 10.0, 12.0, 15.0]:
    for tp in [6.0, 8.0, 10.0, 12.0, 15.0]:
        for sl in [4.0, 6.0, 8.0]:
            for hold in [30, 45, 60]:
                m = sim_vwap_scalp(data, dev, tp, sl, max_hold=hold, point_val=0.01, spread_cost=0.023)
                if m['trades'] >= 5 and m['net_pnl'] > 0:
                    print(f"dev={dev:>4.1f}, tp={tp:>4.1f}, sl={sl:>4.1f}, hold={hold:>2} | Trades: {m['trades']:>2}, WR: {m['win_rate']:>5.1f}%, Net: ${m['net_pnl']:>+6.2f}, PF: {m['profit_factor']:>4.2f}")
