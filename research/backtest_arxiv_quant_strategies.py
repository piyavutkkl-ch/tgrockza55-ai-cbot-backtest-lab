"""
arXiv Quant Strategies Backtest Testbench
-----------------------------------------
Backtests newly synthesized quantitative strategies against live continuous
DOM & Order Flow datasets collected in conversation "Resuming DOM Scraping Project":
- BTCUSD (931 bars + Level 2 DOM + Flow)
- ETHUSD (931 bars + Level 2 DOM + Flow)
- GOLD-PERP / XAUUSD (831 to 1027 bars + Level 2 DOM + Flow)

Strategies Evaluated:
1. QUANT_OFI (Cont-Kukanov-Stoikov Order Flow Imbalance)
2. QUANT_KALMAN (State-Space Zero-Lag Velocity & Trend)
3. QUANT_HAWKES (Bacry Self-Exciting Burst Momentum)
4. DOM_ABSORPTION (Baseline Level 2 Wall Reversal)
5. QUANT_MASTER (5-Tier Hierarchical Multi-Engine Pipeline)
"""

import os
import sys
import json
import math
from collections import defaultdict

sys.path.append(r'd:\cbot-atgvt\research')
from optimize_all_strategies import load_market_data

def run_backtest_engine(symbol, data, strategy_name, **params):
    trades = []
    equity = 0.0
    equity_curve = [0.0]
    pos = None # {type, entry_price, entry_idx, sl, tp, size}
    
    spread_cost = params.get('spread_cost', 0.15)
    comm = params.get('comm', 0.0)
    point_val = params.get('point_val', 0.01)
    
    # State variables for strategies
    kalman_pos = data[0]['close']
    kalman_vel = 0.0
    prev_vel = 0.0
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
        spread = bar['spread'] or spread_cost
        
        # 1. Update Kalman Filter
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
        
        kalman_cross_up = (kalman_vel > 0 and prev_vel <= 0)
        kalman_cross_down = (kalman_vel < 0 and prev_vel >= 0)
        prev_vel = kalman_vel
        
        # 2. Update Hawkes Intensity
        # simulate tick cluster arrival from delta / ticks
        tick_count = bar['ticks']
        hawkes_intensity = 0.2 + (hawkes_intensity - 0.2) * math.exp(-0.2) + (tick_count / 150.0)
        
        # 3. Update OFI
        curr_bid = c - spread / 2.0
        curr_ask = c + spread / 2.0
        d_bid = curr_bid if curr_bid >= prev_bid else -curr_bid
        d_ask = curr_ask if curr_ask <= prev_ask else -curr_ask
        step_ofi = (d_bid - d_ask) * (1.0 + imb)
        cum_ofi = 0.85 * cum_ofi + step_ofi
        prev_bid = curr_bid
        prev_ask = curr_ask
        
        # 4. Check Position Exits if in position
        if pos is not None:
            entry_p = pos['entry_price']
            side = pos['type']
            sl = pos['sl']
            tp = pos['tp']
            entry_i = pos['entry_idx']
            hold_time = i - entry_i
            
            pnl = None
            exit_reason = None
            
            exit_p = None
            exit_reason = None
            
            if side == 'BUY':
                if l <= sl:
                    exit_p = sl
                    exit_reason = 'SL'
                elif h >= tp:
                    exit_p = tp
                    exit_reason = 'TP'
                elif hold_time >= params.get('max_hold', 30):
                    exit_p = c
                    exit_reason = 'TIME_CUT'
            else: # SELL
                if h >= sl:
                    exit_p = sl
                    exit_reason = 'SL'
                elif l <= tp:
                    exit_p = tp
                    exit_reason = 'TP'
                elif hold_time >= params.get('max_hold', 30):
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
                
        # 5. Check Strategy Entry Signals (if flat)
        if pos is None and (i - last_exit_idx >= 1):
            lookback = params.get('lookback', 20)
            if i < lookback: continue
            
            high_n = max(data[j]['high'] for j in range(i - lookback, i))
            low_n = min(data[j]['low'] for j in range(i - lookback, i))
            avg_range = sum(data[j]['high'] - data[j]['low'] for j in range(i - lookback, i)) / lookback
            
            sl_dist = params.get('sl_dist', 35.0)
            tp_dist = params.get('tp_dist', 70.0)
            
            signal = None
            
            # --- STRATEGY 1: QUANT_OFI ---
            if strategy_name == 'QUANT_OFI':
                ofi_thresh = params.get('ofi_thresh', 15.0)
                if cum_ofi >= ofi_thresh and imb >= 0.02:
                    signal = 'BUY'
                elif cum_ofi <= -ofi_thresh and imb <= -0.02:
                    signal = 'SELL'
                    
            # --- STRATEGY 2: QUANT_KALMAN ---
            elif strategy_name == 'QUANT_KALMAN':
                if kalman_cross_up and imb >= -0.01:
                    signal = 'BUY'
                elif kalman_cross_down and imb <= 0.01:
                    signal = 'SELL'
                    
            # --- STRATEGY 3: QUANT_HAWKES ---
            elif strategy_name == 'QUANT_HAWKES':
                burst_thresh = params.get('burst_thresh', 1.8)
                if hawkes_intensity >= burst_thresh:
                    if delta > 10 and cvd > 0: signal = 'BUY'
                    elif delta < -10 and cvd < 0: signal = 'SELL'
                    
            # --- STRATEGY 4: DOM_ABSORPTION (Baseline Wall Reversal) ---
            elif strategy_name == 'DOM_ABSORPTION':
                imb_thresh = params.get('imb_thresh', 0.02)
                # At High with Ask Wall -> Sell
                if c >= high_n - avg_range * 0.15 and imb <= -imb_thresh:
                    signal = 'SELL'
                # At Low with Bid Wall -> Buy
                elif c <= low_n + avg_range * 0.15 and imb >= imb_thresh:
                    signal = 'BUY'
                    
            # --- STRATEGY 5: QUANT_MASTER (5-Tier Ensemble) ---
            elif strategy_name == 'QUANT_MASTER':
                current_range = h - l
                is_trending = current_range > avg_range * 1.15
                
                if is_trending:
                    # Trend Mode: OFI + Kalman + Hawkes
                    if (cum_ofi > 10 or hawkes_intensity > 2.0) and kalman_cross_up:
                        signal = 'BUY'
                    elif (cum_ofi < -10 or hawkes_intensity > 2.0) and kalman_cross_down:
                        signal = 'SELL'
                else:
                    # Choppy Range Mode: DOM Absorption
                    if c <= low_n + avg_range * 0.20 and imb >= 0.03:
                        signal = 'BUY'
                    elif c >= high_n - avg_range * 0.20 and imb <= -0.03:
                        signal = 'SELL'
            
            if signal:
                if signal == 'BUY':
                    pos = {
                        'type': 'BUY',
                        'entry_price': c,
                        'entry_idx': i,
                        'sl': c - sl_dist,
                        'tp': c + tp_dist
                    }
                elif signal == 'SELL':
                    pos = {
                        'type': 'SELL',
                        'entry_price': c,
                        'entry_idx': i,
                        'sl': c + sl_dist,
                        'tp': c - tp_dist
                    }

    # Metrics computation
    total_trades = len(trades)
    if total_trades == 0:
        return {
            'strategy': strategy_name,
            'symbol': symbol,
            'trades': 0,
            'net_pnl': 0.0,
            'win_rate': 0.0,
            'profit_factor': 0.0,
            'max_dd': 0.0
        }
        
    wins = [t['pnl'] for t in trades if t['pnl'] > 0]
    losses = [abs(t['pnl']) for t in trades if t['pnl'] < 0]
    
    gross_profit = sum(wins)
    gross_loss = sum(losses)
    net_pnl = gross_profit - gross_loss
    win_rate = (len(wins) / total_trades) * 100.0
    profit_factor = round(gross_profit / gross_loss, 2) if gross_loss > 0 else 99.9
    
    # Max Drawdown
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
        'avg_trade_pnl': round(net_pnl / total_trades, 2)
    }

def main():
    print("==========================================================================")
    print("      ARXIV QUANT STRATEGIES BACKTEST BENCHMARK (LIVE DOM DATA)           ")
    print("==========================================================================")
    
    symbols_config = {
        'BTCUSD': {
            'point_val': 0.01,
            'spread_cost': 0.15,
            'comm': 0.0,
            'sl_dist': 35.0,
            'tp_dist': 60.0,
            'max_hold': 30
        },
        'ETHUSD': {
            'point_val': 0.10,
            'spread_cost': 0.20,
            'comm': 0.0,
            'sl_dist': 2.0,
            'tp_dist': 3.5,
            'max_hold': 25
        },
        'GOLD-PERP': {
            'point_val': 1.00,
            'spread_cost': 1.39,
            'comm': 0.08,
            'sl_dist': 3.0,
            'tp_dist': 5.5,
            'max_hold': 45
        }
    }
    
    strategies_to_test = [
        'DOM_ABSORPTION',
        'QUANT_OFI',
        'QUANT_KALMAN',
        'QUANT_HAWKES',
        'QUANT_MASTER'
    ]
    
    all_results = {}
    
    for sym, cfg in symbols_config.items():
        print(f"\n>>> Loading dataset for {sym}...")
        data = load_market_data(sym)
        if not data:
            print(f"No data found for {sym}")
            continue
            
        print(f"Loaded {len(data)} continuous minute bars. Running tests across 5 strategies...")
        all_results[sym] = []
        
        for strat in strategies_to_test:
            res = run_backtest_engine(
                sym, data, strat,
                point_val=cfg['point_val'],
                spread_cost=cfg['spread_cost'],
                comm=cfg['comm'],
                sl_dist=cfg['sl_dist'],
                tp_dist=cfg['tp_dist'],
                max_hold=cfg['max_hold']
            )
            all_results[sym].append(res)
            print(f"  [{strat:16s}] Trades: {res['trades']:2d} | WinRate: {res['win_rate']:4.1f}% | NetPnL: ${res['net_pnl']:+6.2f} | PF: {res['profit_factor']:4.2f} | MaxDD: ${res['max_dd']:5.2f}")

    # Save to JSON
    out_json = "d:/cbot-atgvt/data/arxiv_quant_backtest_results.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    print(f"\nAll benchmark results saved to: {out_json}")

if __name__ == '__main__':
    main()
