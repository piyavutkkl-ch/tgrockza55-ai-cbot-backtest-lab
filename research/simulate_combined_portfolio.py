"""
Full Multi-Market Combined Synergy Simulation
---------------------------------------------
Simulates the optimal strategy mix across BTCUSD, ETHUSD, and GOLD-PERP:
1. BTCUSD: DOM_ABSORPTION (Edge Reversal) + CVD_DELTA_DIVERGENCE (Exhaustion)
2. ETHUSD: DOM_ABSORPTION (Edge Reversal) + MID_RANGE_VWAP_SCALP (Mid-range Reversion)
3. GOLD-PERP: NY_VALUE (Value Area Mean Reversion)

Outputs full portfolio metrics, equity milestones, and synergy confirmation.
"""

import os
import sys
import json
sys.path.append(r'd:\cbot-atgvt\research')
from optimize_all_strategies import (
    load_market_data, sim_dom_absorption, sim_vwap_scalp,
    sim_ny_value, sim_delta_divergence
)

def simulate_portfolio():
    print("==============================================================")
    print("      UNIFIED MULTI-MARKET OPTIMIZED PORTFOLIO SIMULATION     ")
    print("==============================================================")
    
    # 1. BTCUSD
    btc_data = load_market_data('BTCUSD')
    btc_dom = sim_dom_absorption(btc_data, lookback=25, imb_thresh=0.02, tp_dist=50.0, sl_dist=35.0, point_val=0.01, spread_cost=0.15)
    btc_cvd = sim_delta_divergence(btc_data, lookback=15, delta_thresh=40.0, tp_dist=100.0, sl_dist=25.0, max_hold=25, point_val=0.01, spread_cost=0.15)
    
    # 2. ETHUSD (0.10 lot sizing for parity with BTC capital allocation)
    eth_data = load_market_data('ETHUSD')
    eth_dom = sim_dom_absorption(eth_data, lookback=10, imb_thresh=0.04, tp_dist=2.5, sl_dist=1.5, point_val=0.10, spread_cost=0.20)
    eth_vwap = sim_vwap_scalp(eth_data, dev_thresh=5.0, tp_dist=2.0, sl_dist=3.0, max_hold=15, point_val=0.10, spread_cost=0.20)
    
    # 3. GOLD-PERP (1 oz)
    gold_data = load_market_data('GOLD-PERP')
    gold_ny = sim_ny_value(gold_data, mode='FADE', buffer_dist=1.0, tp_dist=4.0, sl_dist=2.5, max_hold=60, point_val=1.00, spread_cost=1.39, comm=0.08)
    
    portfolio = {
        'BTCUSD': {
            'DOM_ABSORPTION': btc_dom,
            'CVD_DELTA_DIVERGENCE': btc_cvd,
            'subtotal_pnl': round(btc_dom['net_pnl'] + btc_cvd['net_pnl'], 2),
            'subtotal_trades': btc_dom['trades'] + btc_cvd['trades']
        },
        'ETHUSD': {
            'DOM_ABSORPTION': eth_dom,
            'MID_RANGE_VWAP_SCALP': eth_vwap,
            'subtotal_pnl': round(eth_dom['net_pnl'] + eth_vwap['net_pnl'], 2),
            'subtotal_trades': eth_dom['trades'] + eth_vwap['trades']
        },
        'GOLD-PERP': {
            'NY_VALUE_FADE': gold_ny,
            'subtotal_pnl': round(gold_ny['net_pnl'], 2),
            'subtotal_trades': gold_ny['trades']
        }
    }
    
    total_trades = portfolio['BTCUSD']['subtotal_trades'] + portfolio['ETHUSD']['subtotal_trades'] + portfolio['GOLD-PERP']['subtotal_trades']
    total_net = round(portfolio['BTCUSD']['subtotal_pnl'] + portfolio['ETHUSD']['subtotal_pnl'] + portfolio['GOLD-PERP']['subtotal_pnl'], 2)
    
    print("\n--- RESULTS BY MARKET ---")
    print(f"BTCUSD (0.01 lot):")
    print(f"  DOM_ABSORPTION:        Trades: {btc_dom['trades']}, WinRate: {btc_dom['win_rate']}%, PF: {btc_dom['profit_factor']}, PnL: ${btc_dom['net_pnl']:+.2f}")
    print(f"  CVD_DELTA_DIVERGENCE:  Trades: {btc_cvd['trades']}, WinRate: {btc_cvd['win_rate']}%, PF: {btc_cvd['profit_factor']}, PnL: ${btc_cvd['net_pnl']:+.2f}")
    print(f"  BTC Subtotal:          Trades: {portfolio['BTCUSD']['subtotal_trades']}, Net PnL: ${portfolio['BTCUSD']['subtotal_pnl']:+.2f}")
    
    print(f"\nETHUSD (0.10 lot):")
    print(f"  DOM_ABSORPTION:        Trades: {eth_dom['trades']}, WinRate: {eth_dom['win_rate']}%, PF: {eth_dom['profit_factor']}, PnL: ${eth_dom['net_pnl']:+.2f}")
    print(f"  MID_RANGE_VWAP_SCALP:  Trades: {eth_vwap['trades']}, WinRate: {eth_vwap['win_rate']}%, PF: {eth_vwap['profit_factor']}, PnL: ${eth_vwap['net_pnl']:+.2f}")
    print(f"  ETH Subtotal:          Trades: {portfolio['ETHUSD']['subtotal_trades']}, Net PnL: ${portfolio['ETHUSD']['subtotal_pnl']:+.2f}")
    
    print(f"\nGOLD-PERP (1 oz):")
    print(f"  NY_VALUE (VA Fade):    Trades: {gold_ny['trades']}, WinRate: {gold_ny['win_rate']}%, PF: {gold_ny['profit_factor']}, PnL: ${gold_ny['net_pnl']:+.2f}")
    
    print("\n==============================================================")
    print(f"  GRAND COMBINED PORTFOLIO PERFORMANCE (14.7 HOURS):")
    print(f"  Total Trades:       {total_trades}")
    print(f"  Grand Net PnL:      ${total_net:+.2f} USD")
    print(f"  Return on $100:     +{total_net:.1f}%")
    print("==============================================================")
    
    with open(r'd:\cbot-atgvt\data\portfolio_simulation_summary.json', 'w', encoding='utf-8') as f:
        json.dump(portfolio, f, indent=2, ensure_ascii=False)

if __name__ == '__main__':
    simulate_portfolio()
