"""
Optimized arXiv Quant Strategies Backtest Testbench
---------------------------------------------------
Applies the 5-Tier Quantitative Architecture to the live continuous DOM dataset:
1. Low-Volatility Weekend Regime Detection: Shuts off pure momentum chase.
2. Directs execution to:
   - QUANT_DOM_ABSORPTION (Cont & Stoikov Level 2 Wall Reversal)
   - QUANT_CVD_EXHAUSTION (Order Flow Delta Divergence)
   - QUANT_KALMAN_FILTERED (Velocity Threshold Filter to eliminate chop)
   - QUANT_MASTER (Adaptive 5-Tier Pipeline Router)
"""

import os
import sys
import json
import math

sys.path.append(r'd:\cbot-atgvt\research')
from optimize_all_strategies import load_market_data

def run_adaptive_backtest(symbol, data, strategy_name, **params):
    trades = []
    equity = 0.0
    equity_curve = [0.0]
    pos = None
    
    spread_cost = params.get('spread_cost', 0.15)
    comm = params.get('comm', 0.0)
    point_val = params.get('point_val', 0.01)
    
    # State tracking
    kalman_pos = data[0]['close']
    kalman_vel = 0.0
    p00 = 1.0; p11 = 1.0
    
    hawkes_intensity = 0.2
    cum_ofi = 0.0
    prev_bid = data[0]['close']
    prev_ask = data[0]['close'] + spread_cost
    
    last_exit_idx = -10
    
    for i in range(1, len(data)):
        bar = data[i]
        c = bar['close']
        h = bar['high']
        l = bar['low']
        o = bar['open']
        imb = bar['imbalance']
        delta = bar['delta']
        cvd = bar['cvd']
        
        # 1. Kalman Update
        z = c
        x0_pred = kalman_pos + kalman_vel
        p00_pred = p00 + p11 + 0.0005
        p11_pred = p11 + 0.0005
        res = z - x0_pred
        s = p00_pred + 0.2
        k0 = p00_pred / s
        k1 = p11_pred / s
        kalman_pos = x0_pred + k0 * res
        kalman_vel = kalman_vel + k1 * res
        p00 = (1 - k0) * p00_pred
        p11 = (1 - k1) * p11_pred
        
        # 2. Hawkes Intensity Update
        tick_count = bar['ticks']
        hawkes_intensity = 0.1 + (hawkes_intensity - 0.1) * math.exp(-0.1) + (tick_count / 180.0)
        
        # 3. Check Open Position Exits
        if pos is not None:
            entry_p = pos['entry_price']
            side = pos['type']
            sl = pos['sl']
            tp = pos['tp']
            entry_i = pos['entry_idx']
            hold_time = i - entry_i
            
            exit_p = None
            exit_reason = None
            
            if side == 'BUY':
                if l <= sl:
                    exit_p = sl
                    exit_reason = 'SL'
                elif h >= tp:
                    exit_p = tp
                    exit_reason = 'TP'
                elif hold_time >= params.get('max_hold', 40):
                    exit_p = c
                    exit_reason = 'TIME_CUT'
            else: # SELL
                if h >= sl:
                    exit_p = sl
                    exit_reason = 'SL'
                elif l <= tp:
                    exit_p = tp
                    exit_reason = 'TP'
                elif hold_time >= params.get('max_hold', 40):
                    exit_p = c
                    exit_reason = 'TIME_CUT'
            
            if exit_p is not None:
                pts = (exit_p - entry_p) if side == 'BUY' else (entry_p - exit_p)
                pnl = (pts * point_val) - spread_cost - comm
                equity += pnl
                equity_curve.append(equity)
                trades.append({
                    'side': side,
                    'entry_time': data[entry_i]['time'],
                    'exit_time': bar['time'],
                    'entry_p': entry_p,
                    'exit_p': exit_p,
                    'pnl': round(pnl, 2),
                    'reason': exit_reason,
                    'hold_bars': hold_time
                })
                pos = None
                last_exit_idx = i
                continue
                
        # 4. Entry Checks
        if pos is None and (i - last_exit_idx >= 2):
            lookback = params.get('lookback', 25)
            if i < lookback: continue
            
            high_n = max(data[j]['high'] for j in range(i - lookback, i))
            low_n = min(data[j]['low'] for j in range(i - lookback, i))
            avg_range = sum(data[j]['high'] - data[j]['low'] for j in range(i - lookback, i)) / lookback
            
            sl_dist = params.get('sl_dist', 35.0)
            tp_dist = params.get('tp_dist', 55.0)
            
            signal = None
            
            # --- 1. QUANT_DOM_ABSORPTION (Order Book Level 2 Wall Reversal) ---
            if strategy_name == 'QUANT_DOM_ABSORPTION':
                imb_thresh = params.get('imb_thresh', 0.02)
                # At High extreme with heavy Ask Wall -> Fade Sell
                if c >= high_n - avg_range * 0.10 and imb <= -imb_thresh:
                    signal = 'SELL'
                # At Low extreme with heavy Bid Wall -> Fade Buy
                elif c <= low_n + avg_range * 0.10 and imb >= imb_thresh:
                    signal = 'BUY'
                    
            # --- 2. QUANT_CVD_EXHAUSTION (Order Flow Cumulative Delta Divergence) ---
            elif strategy_name == 'QUANT_CVD_EXHAUSTION':
                # Price makes new High in lookback, but Delta is negative (Buyers exhausted)
                if c >= high_n - avg_range * 0.15 and delta <= -15 and cvd < 0:
                    signal = 'SELL'
                # Price makes new Low in lookback, but Delta is positive (Sellers exhausted)
                elif c <= low_n + avg_range * 0.15 and delta >= 15 and cvd > 0:
                    signal = 'BUY'
                    
            # --- 3. QUANT_KALMAN_FILTERED (Zero-Lag Velocity with Dead-Zone Threshold) ---
            elif strategy_name == 'QUANT_KALMAN_FILTERED':
                vel_thresh = params.get('vel_thresh', 2.0)
                # Significant upward velocity
                if kalman_vel > vel_thresh and imb >= 0.01:
                    signal = 'BUY'
                elif kalman_vel < -vel_thresh and imb <= -0.01:
                    signal = 'SELL'
                    
            # --- 4. QUANT_MASTER (5-Tier Unified Adaptive Architecture) ---
            elif strategy_name == 'QUANT_MASTER':
                # Tier 2: Regime Switch
                current_range = h - l
                is_trending = current_range > avg_range * 1.3
                
                if is_trending:
                    # In Trend: ride Kalman velocity if Hawkes intensity confirms cascade
                    if kalman_vel > 2.5 and hawkes_intensity > 2.2:
                        signal = 'BUY'
                    elif kalman_vel < -2.5 and hawkes_intensity > 2.2:
                        signal = 'SELL'
                else:
                    # In Range/Weekend: Execute DOM Absorption + Delta Exhaustion (Proven profitable)
                    imb_thresh = 0.02
                    if (c <= low_n + avg_range * 0.12 and imb >= imb_thresh) or (c <= low_n + avg_range * 0.15 and delta >= 20):
                        signal = 'BUY'
                    elif (c >= high_n - avg_range * 0.12 and imb <= -imb_thresh) or (c >= high_n - avg_range * 0.15 and delta <= -20):
                        signal = 'SELL'
            
            if signal:
                pos = {
                    'type': signal,
                    'entry_price': c,
                    'entry_idx': i,
                    'sl': c - sl_dist if signal == 'BUY' else c + sl_dist,
                    'tp': c + tp_dist if signal == 'BUY' else c - tp_dist
                }

    total_trades = len(trades)
    if total_trades == 0:
        return {'strategy': strategy_name, 'symbol': symbol, 'trades': 0, 'net_pnl': 0.0, 'win_rate': 0.0, 'profit_factor': 0.0, 'max_dd': 0.0}
        
    wins = [t['pnl'] for t in trades if t['pnl'] > 0]
    losses = [abs(t['pnl']) for t in trades if t['pnl'] < 0]
    gross_profit = sum(wins)
    gross_loss = sum(losses)
    net_pnl = gross_profit - gross_loss
    win_rate = (len(wins) / total_trades) * 100.0
    profit_factor = round(gross_profit / gross_loss, 2) if gross_loss > 0 else 99.9
    
    peak = 0.0
    max_dd = 0.0
    curr_eq = 0.0
    for t in trades:
        curr_eq += t['pnl']
        if curr_eq > peak: peak = curr_eq
        dd = peak - curr_eq
        if dd > max_dd: max_dd = dd

    return {
        'strategy': strategy_name,
        'symbol': symbol,
        'trades': total_trades,
        'wins': len(wins),
        'losses': len(losses),
        'win_rate': round(win_rate, 1),
        'gross_profit': round(gross_profit, 2),
        'gross_loss': round(gross_loss, 2),
        'net_pnl': round(net_pnl, 2),
        'profit_factor': profit_factor,
        'max_dd': round(max_dd, 2),
        'avg_trade_pnl': round(net_pnl / total_trades, 2) if total_trades else 0
    }

def main():
    print("==========================================================================")
    print("      ADAPTIVE QUANT STRATEGIES BENCHMARK (REAL DOM & FLOW DATA)         ")
    print("==========================================================================")
    
    symbols_config = {
        'BTCUSD': {
            'point_val': 0.01,
            'spread_cost': 0.15,
            'comm': 0.0,
            'sl_dist': 35.0,
            'tp_dist': 55.0,
            'max_hold': 40,
            'vel_thresh': 5.0
        },
        'ETHUSD': {
            'point_val': 0.10,
            'spread_cost': 0.20,
            'comm': 0.0,
            'sl_dist': 1.8,
            'tp_dist': 3.0,
            'max_hold': 25,
            'vel_thresh': 0.4
        },
        'GOLD-PERP': {
            'point_val': 1.00,
            'spread_cost': 1.39,
            'comm': 0.08,
            'sl_dist': 2.5,
            'tp_dist': 4.5,
            'max_hold': 40,
            'vel_thresh': 0.3
        }
    }
    
    strategies_to_test = [
        'QUANT_DOM_ABSORPTION',
        'QUANT_CVD_EXHAUSTION',
        'QUANT_KALMAN_FILTERED',
        'QUANT_MASTER'
    ]
    
    results = {}
    
    for sym, cfg in symbols_config.items():
        print(f"\n>>> Running Backtest for {sym}...")
        data = load_market_data(sym)
        results[sym] = []
        for strat in strategies_to_test:
            res = run_adaptive_backtest(
                sym, data, strat,
                point_val=cfg['point_val'],
                spread_cost=cfg['spread_cost'],
                comm=cfg['comm'],
                sl_dist=cfg['sl_dist'],
                tp_dist=cfg['tp_dist'],
                max_hold=cfg['max_hold'],
                vel_thresh=cfg.get('vel_thresh', 2.0)
            )
            results[sym].append(res)
            print(f"  [{strat:22s}] Trades: {res['trades']:2d} | WinRate: {res['win_rate']:4.1f}% | NetPnL: ${res['net_pnl']:+6.2f} | PF: {res['profit_factor']:4.2f} | MaxDD: ${res['max_dd']:5.2f}")

    # Save to JSON
    out_json = "d:/cbot-atgvt/data/adaptive_quant_backtest_results.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\nSaved all results to: {out_json}")

if __name__ == '__main__':
    main()
