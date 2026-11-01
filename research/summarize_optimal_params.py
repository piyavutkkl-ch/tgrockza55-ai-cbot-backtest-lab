import json

with open(r"d:\cbot-atgvt\data\exhaustive_13_engines_optimization.json", "r", encoding="utf-8") as f:
    data = json.load(f)

for sym, engines in data.items():
    print(f"\n==================== SYMBOL: {sym} ====================")
    for eng_id, res in engines.items():
        base = res['baseline_metrics']
        opt = res['optimized_metrics']
        params = res['optimal_parameters']
        gain = res['improvement_pnl']
        print(f"\n[{eng_id}]")
        print(f"  Baseline:  PnL: ${base['net_pnl']:+6.2f} | PF: {base['profit_factor']:4.2f} | WR: {base['win_rate']:4.1f}% | Trades: {base['trades']}")
        print(f"  OPTIMIZED: PnL: ${opt['net_pnl']:+6.2f} | PF: {opt['profit_factor']:4.2f} | WR: {opt['win_rate']:4.1f}% | Trades: {opt['trades']} | GAIN: ${gain:+6.2f}")
        print(f"  Optimal Parameters: {params}")
