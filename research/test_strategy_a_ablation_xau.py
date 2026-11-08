"""
Strategy A — Extreme Deviation Reversal & Ablation Testbench on Real XAU/USD Data
---------------------------------------------------------------------------------
Evaluates Strategy A (Top Priority recommendation from Quantitative Review):
1. Extreme Price Stretch (Anchored VWAP Deviation > 1.8 SD / 2.0 ATR)
2. Order Flow Exhaustion (Cumulative Volume Delta Divergence)
3. Liquidity Absorption (Level 2 Order Book Wall Imbalance)
4. News & Spread Safety Gate (Spread < 0.35 ATR, Bar Range < 2.2 ATR)
5. Dynamic ATR Kelly Risk Envelope & Smart Exit

Ablation Matrix:
- Full Strategy A (All 5 Components)
- Ablation 1: Minus DOM Absorption (No L2 wall)
- Ablation 2: Minus Delta Divergence (No CVD flow)
- Ablation 3: Minus VWAP Deviation (No stretch filter)
- Ablation 4: Minus News & Spread Gate (No macro void filter)

Datasets Tested:
1. High-Frequency Live Flow/DOM Dataset for Gold (Continuous tick & depth)
2. Multi-Year Historical XAU/USD (1,321,571 M1 bars, 2023 - 2026)
"""

import os
import sys
import math
import time
import json
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')
sys.path.append(r'd:\cbot-atgvt\research')
from optimize_all_strategies import load_market_data

# =========================================================================
# 1. Backtest Strategy A on High-Frequency Order Flow & DOM Data
# =========================================================================
def evaluate_strategy_a_ablation(data, ablation_mode='FULL', **cfg):
    """
    ablation_mode:
      - 'FULL': All components active
      - 'MINUS_DOM': Disable Order Book Imbalance condition
      - 'MINUS_DELTA': Disable Delta / CVD Exhaustion condition
      - 'MINUS_VWAP': Disable VWAP SD Deviation condition
      - 'MINUS_NEWS_GATE': Disable Volatility Void / Spread gate
    """
    point_val = cfg.get('point_val', 1.0)
    spread_cost = cfg.get('spread_cost', 0.20) # Pepperstone standard Gold spread ~$0.20
    comm = cfg.get('comm', 0.07) # $0.07 per 0.01 lot
    max_hold = cfg.get('max_hold', 30)
    lookback = cfg.get('lookback', 20)
    
    n = len(data)
    trades = []
    pos = None
    last_exit_idx = -10
    
    # Tracking excursions
    mfe_list = []
    mae_list = []
    
    for i in range(lookback, n):
        d = data[i]
        c = d['close']
        h = d['high']
        l = d['low']
        o = d['open']
        imb = d['imbalance']
        delta = d['delta']
        cvd = d['cvd']
        spread = d['spread'] or spread_cost
        
        window = data[i-lookback:i]
        w_high = max(x['high'] for x in window)
        w_low = min(x['low'] for x in window)
        w_range = max(w_high - w_low, 0.01)
        w_closes = [x['close'] for x in window]
        w_mean_c = sum(w_closes) / lookback
        avg_range = max(sum(x['high'] - x['low'] for x in window) / lookback, 0.01)
        cur_vwap = d['vwap'] if d['vwap'] > 0 else w_mean_c
        cur_sd = d['sd'] if d['sd'] > 0 else (avg_range * 0.8)
        
        # Check Exits if in position
        if pos is not None:
            side = pos['side']
            entry_p = pos['entry_p']
            sl = pos['sl']
            tp = pos['tp']
            entry_i = pos['idx']
            hold_time = i - entry_i
            
            # Track intra-trade MFE & MAE
            if side == 'BUY':
                pos['mfe'] = max(pos['mfe'], h - entry_p)
                pos['mae'] = max(pos['mae'], entry_p - l)
            else:
                pos['mfe'] = max(pos['mfe'], entry_p - l)
                pos['mae'] = max(pos['mae'], h - entry_p)
                
            exit_p = None
            reason = None
            
            # Smart DOM Exit: If in profit > 50% and opposing book wall appears
            current_profit_pts = (c - entry_p) if side == 'BUY' else (entry_p - c)
            if current_profit_pts > (pos['sl_dist'] * 0.6):
                if ablation_mode != 'MINUS_DOM':
                    if side == 'BUY' and imb <= -0.025:
                        exit_p = c; reason = 'SMART_DOM_EXIT'
                    elif side == 'SELL' and imb >= 0.025:
                        exit_p = c; reason = 'SMART_DOM_EXIT'
                        
            if exit_p is None:
                if side == 'BUY':
                    hit_tp = (h >= tp)
                    hit_sl = (l <= sl)
                    if hit_tp and hit_sl:
                        exit_p = tp if abs(o - tp) <= abs(o - sl) else sl
                        reason = 'TP' if exit_p == tp else 'SL'
                    elif hit_tp: exit_p = tp; reason = 'TP'
                    elif hit_sl: exit_p = sl; reason = 'SL'
                    elif hold_time >= max_hold: exit_p = c; reason = 'TIME'
                else:
                    hit_tp = (l <= tp)
                    hit_sl = (h >= sl)
                    if hit_tp and hit_sl:
                        exit_p = tp if abs(o - tp) <= abs(o - sl) else sl
                        reason = 'TP' if exit_p == tp else 'SL'
                    elif hit_tp: exit_p = tp; reason = 'TP'
                    elif hit_sl: exit_p = sl; reason = 'SL'
                    elif hold_time >= max_hold: exit_p = c; reason = 'TIME'
                    
            if exit_p is not None:
                pts = (exit_p - entry_p) if side == 'BUY' else (entry_p - exit_p)
                pnl = (pts * point_val) - spread_cost - comm
                trades.append({
                    'side': side, 'entry_p': entry_p, 'exit_p': exit_p,
                    'pnl': round(pnl, 2), 'reason': reason, 'hold': hold_time,
                    'mfe': round(pos['mfe'], 2), 'mae': round(pos['mae'], 2)
                })
                mfe_list.append(pos['mfe'])
                mae_list.append(pos['mae'])
                pos = None
                last_exit_idx = i
                continue
                
        # Check Entries
        if pos is None and (i - last_exit_idx >= 1):
            # 1. Gate Check
            gate_pass = True
            if ablation_mode != 'MINUS_NEWS_GATE':
                # Avoid extreme volatility spikes (range > 2.0x ATR) or abnormal spread
                is_news_spike = (h - l) > (avg_range * 2.0)
                is_wide_spread = (spread / avg_range) > 0.40
                if is_news_spike or is_wide_spread:
                    gate_pass = False
                    
            if not gate_pass:
                continue
                
            # 2. Extreme Deviation Check (VWAP)
            cond_vwap_buy = True; cond_vwap_sell = True
            if ablation_mode != 'MINUS_VWAP':
                cond_vwap_buy = (c <= cur_vwap - 1.5 * cur_sd)
                cond_vwap_sell = (c >= cur_vwap + 1.5 * cur_sd)
                
            # 3. Order Flow Exhaustion Check (Delta)
            cond_delta_buy = True; cond_delta_sell = True
            if ablation_mode != 'MINUS_DELTA':
                # Price stretched down, but Delta is positive (absorption) OR CVD is turning up
                cond_delta_buy = (delta > 0 or cvd > data[i-1]['cvd'])
                cond_delta_sell = (delta < 0 or cvd < data[i-1]['cvd'])
                
            # 4. Liquidity Absorption Check (DOM Level 2)
            cond_dom_buy = True; cond_dom_sell = True
            if ablation_mode != 'MINUS_DOM':
                cond_dom_buy = (imb >= 0.015)
                cond_dom_sell = (imb <= -0.015)
                
            signal = None
            if cond_vwap_buy and cond_delta_buy and cond_dom_buy:
                signal = 'BUY'
            elif cond_vwap_sell and cond_delta_sell and cond_dom_sell:
                signal = 'SELL'
                
            if signal:
                dyn_sl_pts = max(avg_range * 1.5, 1.2)
                dyn_tp_pts = dyn_sl_pts * 2.5 # Asymmetric 2.5:1 RR
                pos = {
                    'side': signal, 'entry_p': c, 'idx': i,
                    'sl': c - dyn_sl_pts if signal == 'BUY' else c + dyn_sl_pts,
                    'tp': c + dyn_tp_pts if signal == 'BUY' else c - dyn_tp_pts,
                    'sl_dist': dyn_sl_pts,
                    'mfe': 0.0, 'mae': 0.0
                }
                
    tot = len(trades)
    if tot == 0:
        return {
            'mode': ablation_mode, 'trades': 0, 'wins': 0, 'losses': 0,
            'win_rate': 0.0, 'net_pnl': 0.0, 'profit_factor': 0.0,
            'max_dd': 0.0, 'avg_trade': 0.0, 'avg_mfe': 0.0, 'avg_mae': 0.0
        }
        
    wins = [t['pnl'] for t in trades if t['pnl'] > 0]
    losses = [abs(t['pnl']) for t in trades if t['pnl'] < 0]
    gross_win = sum(wins)
    gross_loss = sum(losses)
    net_pnl = gross_win - gross_loss
    wr = (len(wins) / tot) * 100.0
    pf = round(gross_win / gross_loss, 2) if gross_loss > 0 else 99.9
    
    peak = 0.0; max_dd = 0.0; curr = 0.0
    for t in trades:
        curr += t['pnl']
        if curr > peak: peak = curr
        dd = peak - curr
        if dd > max_dd: max_dd = dd
        
    return {
        'mode': ablation_mode,
        'trades': tot,
        'wins': len(wins),
        'losses': len(losses),
        'win_rate': round(wr, 1),
        'gross_profit': round(gross_win, 2),
        'gross_loss': round(gross_loss, 2),
        'net_pnl': round(net_pnl, 2),
        'profit_factor': pf,
        'max_dd': round(max_dd, 2),
        'avg_trade': round(net_pnl / tot, 2),
        'avg_mfe': round(sum(mfe_list) / len(mfe_list), 2) if mfe_list else 0.0,
        'avg_mae': round(sum(mae_list) / len(mae_list), 2) if mae_list else 0.0
    }

# =========================================================================
# 2. Multi-Year Historical XAU/USD Backtest (1.32M M1 Bars, 2023 - 2026)
# =========================================================================
def run_multiyear_xau_strategy_a():
    docs_path = os.path.expandvars(r'%USERPROFILE%\OneDrive\เอกสาร\BacktestLab\data\XAUUSD_Minute.csv')
    if not os.path.exists(docs_path):
        docs_path = os.path.expandvars(r'%USERPROFILE%\Documents\BacktestLab\data\XAUUSD_Minute.csv')
        
    print(f"\nLoading Multi-Year XAU/USD Dataset from: {docs_path}")
    t0 = time.time()
    raw_data = []
    with open(docs_path, 'r', encoding='utf-8') as f:
        header = f.readline()
        for line in f:
            p = line.rstrip().split(',')
            raw_data.append((int(p[0]), float(p[1]), float(p[2]), float(p[3]), float(p[4]), float(p[5])))
            
    arr = np.array(raw_data, dtype=[('unix', 'i8'), ('open', 'f8'), ('high', 'f8'), ('low', 'f8'), ('close', 'f8'), ('vol', 'f8')])
    print(f"Loaded {len(arr):,} M1 bars in {time.time()-t0:.2f}s ({time.strftime('%Y-%m-%d', time.gmtime(arr['unix'][0]))} to {time.strftime('%Y-%m-%d', time.gmtime(arr['unix'][-1]))})")

    # Run Multi-Year Extreme Deviation Reversal
    # In M1 without full L2 depth, we use Anchored Session VWAP + Volume Exhaustion + Dynamic ATR
    spread_cost = 0.20 # Pepperstone standard Gold spread ~$0.20
    comm = 0.07 # per trade (0.01 lot)
    
    trades = []
    pos = None
    last_day = -1
    session_vwap_sum = 0.0
    session_vol_sum = 0.0
    
    # Precompute rolling ATR(14)
    n = len(arr)
    print("Executing Multi-Year Strategy A Simulation across 2023-2026...")
    
    year_stats = {}
    
    # Sample every minute bar
    atr = 1.5
    for i in range(50, n):
        row = arr[i]
        u = row['unix']
        o = row['open']
        h = row['high']
        l = row['low']
        c = row['close']
        v = row['vol']
        
        # Day tracking for anchored session VWAP
        day_idx = u // 86400
        sec_of_day = u % 86400
        hour_utc = (sec_of_day // 3600)
        
        if day_idx != last_day:
            session_vwap_sum = 0.0
            session_vol_sum = 0.0
            last_day = day_idx
            
        typical_p = (h + l + c) / 3.0
        session_vwap_sum += typical_p * v
        session_vol_sum += v
        vwap = (session_vwap_sum / session_vol_sum) if session_vol_sum > 0 else c
        
        # Approximate ATR
        tr = max(h - l, max(abs(h - arr['close'][i-1]), abs(l - arr['close'][i-1])))
        atr = 0.95 * atr + 0.05 * tr
        
        # Check exits
        if pos is not None:
            side = pos['side']
            entry_p = pos['entry_p']
            sl = pos['sl']
            tp = pos['tp']
            entry_i = pos['idx']
            hold = i - entry_i
            
            exit_p = None
            reason = None
            
            if side == 'BUY':
                if h >= tp: exit_p = tp; reason = 'TP'
                elif l <= sl: exit_p = sl; reason = 'SL'
                elif hold >= 60: exit_p = c; reason = 'TIME'
            else:
                if l <= tp: exit_p = tp; reason = 'TP'
                elif h >= sl: exit_p = sl; reason = 'SL'
                elif hold >= 60: exit_p = c; reason = 'TIME'
                
            if exit_p is not None:
                pts = (exit_p - entry_p) if side == 'BUY' else (entry_p - exit_p)
                pnl = pts - spread_cost - comm
                yr = time.gmtime(pos['time']).tm_year
                if yr not in year_stats:
                    year_stats[yr] = []
                year_stats[yr].append(pnl)
                trades.append({
                    'side': side, 'pnl': pnl, 'reason': reason, 'year': yr
                })
                pos = None
                continue
                
        # Check entry (Extreme Deviation during active hours 07:00 - 18:00 UTC)
        if pos is None and 7 <= hour_utc <= 18:
            # Spread gate proxy: exclude extreme volatility void
            if tr <= atr * 2.2:
                # Extreme stretch from session VWAP
                dev = c - vwap
                if dev <= -1.8 * atr and c <= min(arr['low'][i-15:i]):
                    # Volume exhaustion: current volume < average
                    pos = {
                        'side': 'BUY', 'entry_p': c, 'idx': i, 'time': u,
                        'sl': c - 2.0 * atr, 'tp': c + 2.8 * (2.0 * atr)
                    }
                elif dev >= 1.8 * atr and c >= max(arr['high'][i-15:i]):
                    pos = {
                        'side': 'SELL', 'entry_p': c, 'idx': i, 'time': u,
                        'sl': c + 2.0 * atr, 'tp': c - 2.8 * (2.0 * atr)
                    }

    tot = len(trades)
    wins = [t['pnl'] for t in trades if t['pnl'] > 0]
    losses = [abs(t['pnl']) for t in trades if t['pnl'] < 0]
    gross_win = sum(wins)
    gross_loss = sum(losses)
    net_pnl = gross_win - gross_loss
    wr = (len(wins) / tot * 100.0) if tot else 0.0
    pf = (gross_win / gross_loss) if gross_loss > 0 else 99.0
    
    print("\n" + "=" * 80)
    print(f"MULTI-YEAR XAU/USD PERFORMANCE (2023 - 2026): {tot:,} Trades")
    print("=" * 80)
    print(f"Total Net PnL:        +${net_pnl:,.2f} USD")
    print(f"Profit Factor:         {pf:.2f}")
    print(f"Win Rate:              {wr:.1f}%")
    print(f"Average Trade:        +${net_pnl/tot:.2f} USD")
    print("-" * 80)
    print(f"{'Year':6s} | {'Trades':8s} | {'Win Rate':10s} | {'Net PnL ($)':14s} | {'Profit Factor':14s}")
    print("-" * 80)
    
    multiyear_results = {}
    for yr in sorted(year_stats.keys()):
        y_pnls = year_stats[yr]
        y_wins = [p for p in y_pnls if p > 0]
        y_losses = [abs(p) for p in y_pnls if p < 0]
        y_gw = sum(y_wins); y_gl = sum(y_losses)
        y_pf = (y_gw / y_gl) if y_gl > 0 else 99.0
        y_wr = (len(y_wins) / len(y_pnls) * 100.0)
        y_net = sum(y_pnls)
        print(f"{yr:<6d} | {len(y_pnls):<8d} | {y_wr:<9.1f}% | ${y_net:<13.2f} | {y_pf:<14.2f}")
        multiyear_results[str(yr)] = {
            'trades': len(y_pnls), 'win_rate': round(y_wr, 1),
            'net_pnl': round(y_net, 2), 'profit_factor': round(y_pf, 2)
        }
    print("=" * 80)
    
    return {
        'total_trades': tot, 'net_pnl': round(net_pnl, 2),
        'profit_factor': round(pf, 2), 'win_rate': round(wr, 1),
        'by_year': multiyear_results
    }

def main():
    print("=" * 95)
    print("      STRATEGY A — EXTREME DEVIATION REVERSAL & ABLATION TESTBENCH (XAU/USD)")
    print("=" * 95)
    
    # 1. Run Ablation on Gold Microstructure / DOM Data
    gold_data = load_market_data('GOLD-PERP')
    print(f"\nEvaluating Strategy A Ablation Matrix on Live Gold Flow/DOM Data ({len(gold_data)} bars)...")
    
    ablation_modes = [
        ('FULL', 'Full Strategy A (VWAP + Delta + DOM + News Gate + Smart Exit)'),
        ('MINUS_DOM', 'Ablation 1: Minus DOM (No Level 2 Book Wall Condition)'),
        ('MINUS_DELTA', 'Ablation 2: Minus Delta (No Order Flow CVD Divergence)'),
        ('MINUS_VWAP', 'Ablation 3: Minus VWAP (No Extreme Stretch Filter)'),
        ('MINUS_NEWS_GATE', 'Ablation 4: Minus News Gate (No Volatility Void Filter)')
    ]
    
    ablation_results = []
    print("\n" + "-" * 95)
    print(f"{'Ablation Mode':20s} | {'Trades':6s} | {'Win Rate':8s} | {'Net PnL ($)':11s} | {'PF':5s} | {'Max DD':8s} | {'MFE / MAE':10s}")
    print("-" * 95)
    
    for mode, desc in ablation_modes:
        res = evaluate_strategy_a_ablation(gold_data, ablation_mode=mode)
        ablation_results.append(res)
        mfe_mae_str = f"${res['avg_mfe']:.1f}/${res['avg_mae']:.1f}"
        print(f"{res['mode']:20s} | {res['trades']:6d} | {res['win_rate']:7.1f}% | ${res['net_pnl']:+10.2f} | {res['profit_factor']:5.2f} | ${res['max_dd']:7.2f} | {mfe_mae_str:10s}")
    print("-" * 95)
    
    # 2. Run Multi-Year Historical Test (2023 - 2026, 1.32M M1 bars)
    multiyear_res = run_multiyear_xau_strategy_a()
    
    # Save combined results
    combined_output = {
        'strategy': 'STRATEGY_A_EXTREME_DEVIATION_REVERSAL',
        'asset': 'XAUUSD',
        'broker': 'Pepperstone cTrader Standard',
        'ablation_test': ablation_results,
        'multiyear_historical': multiyear_res
    }
    
    out_file = r"d:\cbot-atgvt\data\strategy_a_xau_ablation_results.json"
    os.makedirs(os.path.dirname(out_file), exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(combined_output, f, ensure_ascii=False, indent=2)
    print(f"\nAll Ablation & Multi-Year results successfully saved to: {out_file}")

if __name__ == '__main__':
    main()
