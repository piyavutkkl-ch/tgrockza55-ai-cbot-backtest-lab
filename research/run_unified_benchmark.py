"""
Unified arXiv Quant Strategies Backtest Runner & Benchmark
----------------------------------------------------------
Evaluates the core quantitative trading strategies synthesized from arXiv q-fin
against the continuous live DOM dataset from conversation "Resuming DOM Scraping Project".
"""

import os
import sys
import json
sys.path.append(r'd:\cbot-atgvt\research')
from optimize_all_strategies import (
    load_market_data, sim_dom_absorption, sim_delta_divergence, sim_vwap_scalp, sim_ny_value
)

def sim_quant_kalman_filtered(data, vel_thresh=4.0, tp_dist=50.0, sl_dist=35.0, max_hold=30, point_val=0.01, spread_cost=0.15, comm=0.0):
    from optimize_all_strategies import calc_metrics
    trades = []
    pos = None
    
    kalman_pos = data[0]['close']
    kalman_vel = 0.0
    p00 = 1.0; p11 = 1.0
    
    for i in range(1, len(data)):
        d = data[i]
        c = d['close']
        h = d['high']
        l = d['low']
        imb = d['imbalance']
        
        # Kalman update
        z = c
        x0_pred = kalman_pos + kalman_vel
        p00_pred = p00 + p11 + 0.001
        p11_pred = p11 + 0.001
        res = z - x0_pred
        s = p00_pred + 0.1
        k0 = p00_pred / s
        k1 = p11_pred / s
        kalman_pos = x0_pred + k0 * res
        kalman_vel = kalman_vel + k1 * res
        p00 = (1 - k0) * p00_pred
        p11 = (1 - k1) * p11_pred
        
        if pos is not None:
            side = pos['side']
            exit_p = None
            reason = None
            if side == 'Buy':
                if h >= pos['tp']: exit_p = pos['tp']; reason = 'TP'
                elif l <= pos['sl']: exit_p = pos['sl']; reason = 'SL'
            else:
                if l <= pos['tp']: exit_p = pos['tp']; reason = 'TP'
                elif h >= pos['sl']: exit_p = pos['sl']; reason = 'SL'
                
            if exit_p is None and (i - pos['idx']) >= max_hold:
                exit_p = c
                reason = 'TIME'
                
            if exit_p is not None:
                trades.append({
                    'side': side, 'entry_p': pos['entry_p'], 'exit_p': exit_p,
                    'reason': reason, 'spread_cost': spread_cost
                })
                pos = None
                continue
                
        if pos is None:
            if kalman_vel >= vel_thresh and imb >= 0.01:
                pos = {'side': 'Buy', 'entry_p': c, 'tp': c + tp_dist, 'sl': c - sl_dist, 'idx': i}
            elif kalman_vel <= -vel_thresh and imb <= -0.01:
                pos = {'side': 'Sell', 'entry_p': c, 'tp': c - tp_dist, 'sl': c + sl_dist, 'idx': i}
                
    return calc_metrics(trades, point_val=point_val, spread_cost=spread_cost, comm_per_trade=comm)

def sim_quant_unified_master(data, lookback=25, imb_thresh=0.02, delta_thresh=25.0, tp_dist=50.0, sl_dist=35.0, max_hold=45, point_val=0.01, spread_cost=0.15, comm=0.0):
    from optimize_all_strategies import calc_metrics
    trades = []
    pos = None
    
    kalman_pos = data[0]['close']
    kalman_vel = 0.0
    p00 = 1.0; p11 = 1.0
    
    for i in range(lookback, len(data)):
        d = data[i]
        c = d['close']
        h = d['high']
        l = d['low']
        imb = d['imbalance']
        delta = d['delta']
        
        # Kalman update
        z = c
        x0_pred = kalman_pos + kalman_vel
        p00_pred = p00 + p11 + 0.001
        p11_pred = p11 + 0.001
        res = z - x0_pred
        s = p00_pred + 0.1
        k0 = p00_pred / s
        k1 = p11_pred / s
        kalman_pos = x0_pred + k0 * res
        kalman_vel = kalman_vel + k1 * res
        p00 = (1 - k0) * p00_pred
        p11 = (1 - k1) * p11_pred
        
        if pos is not None:
            side = pos['side']
            exit_p = None
            reason = None
            if side == 'Buy':
                if h >= pos['tp']: exit_p = pos['tp']; reason = 'TP'
                elif l <= pos['sl']: exit_p = pos['sl']; reason = 'SL'
            else:
                if l <= pos['tp']: exit_p = pos['tp']; reason = 'TP'
                elif h >= pos['sl']: exit_p = pos['sl']; reason = 'SL'
                
            if exit_p is None and (i - pos['idx']) >= max_hold:
                exit_p = c
                reason = 'TIME'
                
            if exit_p is not None:
                trades.append({
                    'side': side, 'entry_p': pos['entry_p'], 'exit_p': exit_p,
                    'reason': reason, 'spread_cost': spread_cost
                })
                pos = None
                continue
                
        if pos is None:
            window = data[i-lookback:i]
            w_high = max(x['high'] for x in window)
            w_low = min(x['low'] for x in window)
            w_range = w_high - w_low
            if w_range <= 0: continue
            
            # Regime classification
            avg_range = sum(x['high'] - x['low'] for x in window) / lookback
            is_trending = (h - l) > avg_range * 1.3
            
            if is_trending:
                # Fast momentum trend ride
                if kalman_vel > 6.0 and imb > 0.01:
                    pos = {'side': 'Buy', 'entry_p': c, 'tp': c + tp_dist * 1.2, 'sl': c - sl_dist, 'idx': i}
                elif kalman_vel < -6.0 and imb < -0.01:
                    pos = {'side': 'Sell', 'entry_p': c, 'tp': c - tp_dist * 1.2, 'sl': c + sl_dist, 'idx': i}
            else:
                # Choppy mean-reversion with DOM Wall Absorption & CVD exhaustion
                if (c <= w_low + w_range * 0.15 and imb >= imb_thresh) or (c <= w_low + w_range * 0.18 and delta >= delta_thresh):
                    pos = {'side': 'Buy', 'entry_p': c, 'tp': c + tp_dist, 'sl': c - sl_dist, 'idx': i}
                elif (c >= w_high - w_range * 0.15 and imb <= -imb_thresh) or (c >= w_high - w_range * 0.18 and delta <= -delta_thresh):
                    pos = {'side': 'Sell', 'entry_p': c, 'tp': c - tp_dist, 'sl': c + sl_dist, 'idx': i}
                    
    return calc_metrics(trades, point_val=point_val, spread_cost=spread_cost, comm_per_trade=comm)

def run_benchmark():
    print("==========================================================================")
    print("      UNIFIED QUANT RESEARCH STRATEGIES BENCHMARK ON REAL LIVE DOM        ")
    print("==========================================================================")
    
    btc_data = load_market_data('BTCUSD')
    eth_data = load_market_data('ETHUSD')
    gold_data = load_market_data('GOLD-PERP')
    
    # BTCUSD Tests
    print("\n[BTCUSD - 935 Bars / Real DOM Level 2]")
    btc_abs = sim_dom_absorption(btc_data, lookback=25, imb_thresh=0.02, tp_dist=50.0, sl_dist=35.0, point_val=0.01, spread_cost=0.15)
    btc_cvd = sim_delta_divergence(btc_data, lookback=15, delta_thresh=40.0, tp_dist=100.0, sl_dist=25.0, max_hold=25, point_val=0.01, spread_cost=0.15)
    btc_kalman = sim_quant_kalman_filtered(btc_data, vel_thresh=5.0, tp_dist=50.0, sl_dist=35.0, point_val=0.01, spread_cost=0.15)
    btc_master = sim_quant_unified_master(btc_data, lookback=25, imb_thresh=0.02, delta_thresh=35.0, tp_dist=50.0, sl_dist=35.0, point_val=0.01, spread_cost=0.15)
    
    for name, r in [('DOM_ABSORPTION', btc_abs), ('CVD_DELTA_DIVERGENCE', btc_cvd), ('KALMAN_FILTERED', btc_kalman), ('QUANT_MASTER (5-Tier)', btc_master)]:
        print(f"  {name:24s} | Trades: {r['trades']:2d} | WinRate: {r['win_rate']:4.1f}% | NetPnL: ${r['net_pnl']:+6.2f} | PF: {r['profit_factor']:4.2f} | MaxDD: ${r['max_dd']:4.2f}")
        
    # ETHUSD Tests
    print("\n[ETHUSD - 935 Bars / Real DOM Level 2]")
    eth_abs = sim_dom_absorption(eth_data, lookback=10, imb_thresh=0.04, tp_dist=2.5, sl_dist=1.5, point_val=0.10, spread_cost=0.20)
    eth_kalman = sim_quant_kalman_filtered(eth_data, vel_thresh=0.5, tp_dist=2.5, sl_dist=1.5, point_val=0.10, spread_cost=0.20)
    eth_master = sim_quant_unified_master(eth_data, lookback=10, imb_thresh=0.04, delta_thresh=15.0, tp_dist=2.5, sl_dist=1.5, point_val=0.10, spread_cost=0.20)
    
    for name, r in [('DOM_ABSORPTION', eth_abs), ('KALMAN_FILTERED', eth_kalman), ('QUANT_MASTER (5-Tier)', eth_master)]:
        print(f"  {name:24s} | Trades: {r['trades']:2d} | WinRate: {r['win_rate']:4.1f}% | NetPnL: ${r['net_pnl']:+6.2f} | PF: {r['profit_factor']:4.2f} | MaxDD: ${r['max_dd']:4.2f}")

    # GOLD-PERP Tests
    print("\n[GOLD-PERP - 834 Bars / Real DOM Level 2]")
    gold_ny = sim_ny_value(gold_data, mode='FADE', buffer_dist=1.0, tp_dist=4.0, sl_dist=2.5, max_hold=60, point_val=1.00, spread_cost=1.39, comm=0.08)
    gold_master = sim_quant_unified_master(gold_data, lookback=20, imb_thresh=0.015, delta_thresh=2.0, tp_dist=4.0, sl_dist=2.5, point_val=1.00, spread_cost=1.39, comm=0.08)
    
    for name, r in [('NY_VALUE (VA Fade)', gold_ny), ('QUANT_MASTER (5-Tier)', gold_master)]:
        print(f"  {name:24s} | Trades: {r['trades']:2d} | WinRate: {r['win_rate']:4.1f}% | NetPnL: ${r['net_pnl']:+6.2f} | PF: {r['profit_factor']:4.2f} | MaxDD: ${r['max_dd']:4.2f}")

    # Save benchmark results
    out = {
        'BTCUSD': {'DOM_ABSORPTION': btc_abs, 'CVD_DELTA_DIVERGENCE': btc_cvd, 'KALMAN_FILTERED': btc_kalman, 'QUANT_MASTER': btc_master},
        'ETHUSD': {'DOM_ABSORPTION': eth_abs, 'KALMAN_FILTERED': eth_kalman, 'QUANT_MASTER': eth_master},
        'GOLD-PERP': {'NY_VALUE': gold_ny, 'QUANT_MASTER': gold_master}
    }
    with open('d:/cbot-atgvt/data/quant_unified_benchmark.json', 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

if __name__ == '__main__':
    run_benchmark()
