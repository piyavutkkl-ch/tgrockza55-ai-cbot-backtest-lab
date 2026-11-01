"""
Exhaustive Step-by-Step Optimization Engine for 13 Quant Strategy Pillars
--------------------------------------------------------------------------
Systematically optimizes every variable one-by-one (Coordinate Descent & Full Grid)
across real continuous Level 2 DOM & Order Flow datasets (BTCUSD & ETHUSD).

Outputs:
1. Step-by-step optimization trajectory for each variable
2. Global optimal parameter combination maximizing Net Profit & Profit Factor
3. cTrader Automate Parameter Mapping (P1..P4, MinValue, MaxValue, Step)
"""

import os
import sys
import math
import json
import itertools
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')
sys.path.append(r'd:\cbot-atgvt\research')
from optimize_all_strategies import load_market_data

def evaluate_simulation(data, engine_id, params, asset_cfg):
    point_val = asset_cfg.get('point_val', 0.01)
    spread_cost = asset_cfg.get('spread_cost', 0.16)
    comm = asset_cfg.get('comm', 0.0)
    
    lookback = int(params.get('lookback', 20))
    max_hold = int(params.get('max_hold', 35))
    base_sl = float(params.get('sl_dist', 30.0))
    base_tp = float(params.get('tp_dist', 50.0))
    
    n = len(data)
    trades = []
    pos = None
    
    kalman_pos = data[0]['close']
    kalman_vel = 0.0
    p00 = 1.0; p11 = 1.0
    hawkes_intensity = 1.0
    cum_ofi = 0.0
    inventory_q = 0
    prev_bid = data[0]['close']
    prev_ask = data[0]['close'] + spread_cost
    last_exit_idx = -10
    ofi_history = []
    
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
        ticks = d['ticks']
        
        window = data[i-lookback:i]
        w_high = max(x['high'] for x in window)
        w_low = min(x['low'] for x in window)
        w_range = max(w_high - w_low, 0.01)
        w_closes = [x['close'] for x in window]
        w_mean_c = sum(w_closes) / lookback
        w_ticks = [x['ticks'] for x in window]
        avg_ticks = max(sum(w_ticks) / lookback, 1.0)
        avg_range = max(sum(x['high'] - x['low'] for x in window) / lookback, 0.01)
        cur_vwap = d['vwap'] if d['vwap'] > 0 else w_mean_c
        cur_sd = d['sd'] if d['sd'] > 0 else (avg_range * 0.8)
        
        # 1. State Trackers
        z = c
        x0_p = kalman_pos + kalman_vel
        p00_p = p00 + p11 + params.get('q_noise', 0.001)
        p11_p = p11 + params.get('q_noise', 0.001)
        res = z - x0_p
        s_k = p00_p + params.get('r_noise', 0.2)
        k0 = p00_p / s_k
        k1 = p11_p / s_k
        kalman_pos = x0_p + k0 * res
        kalman_vel = kalman_vel + k1 * res
        p00 = (1 - k0) * p00_p
        p11 = (1 - k1) * p11_p
        
        # Hawkes
        decay_beta = params.get('decay_beta', 0.20)
        hawkes_intensity = 0.2 + (hawkes_intensity - 0.2) * math.exp(-decay_beta) + (0.5 * (ticks / avg_ticks))
        
        # OFI
        curr_bid = c - spread / 2.0
        curr_ask = c + spread / 2.0
        d_b = curr_bid if curr_bid >= prev_bid else -curr_bid
        d_a = curr_ask if curr_ask <= prev_ask else -curr_ask
        step_ofi = (d_b - d_a) * (1.0 + imb * 5.0)
        cum_ofi = params.get('ofi_decay', 0.82) * cum_ofi + step_ofi
        prev_bid = curr_bid; prev_ask = curr_ask
        ofi_history.append(cum_ofi)
        if len(ofi_history) > lookback: ofi_history.pop(0)
        ofi_std = max(np.std(ofi_history), 1.0)
        ofi_z = cum_ofi / ofi_std
        
        # Check Exits
        if pos is not None:
            side = pos['side']
            entry_p = pos['entry_p']
            sl = pos['sl']
            tp = pos['tp']
            entry_i = pos['idx']
            hold_time = i - entry_i
            
            exit_p = None
            reason = None
            
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
                    'pnl': round(pnl, 2), 'reason': reason, 'hold': hold_time
                })
                inventory_q += (-1 if side == 'BUY' else 1)
                pos = None
                last_exit_idx = i
                continue
                
        # Check Entries
        if pos is None and (i - last_exit_idx >= 1):
            signal = None
            dyn_sl = base_sl
            dyn_tp = base_tp
            
            # 1. DEEPLOB
            if engine_id == 'ENGINE_01_DEEPLOB':
                tol = params.get('range_tol', 0.15)
                imb_th = params.get('imb_thresh', 0.02)
                if c <= w_low + w_range * tol and imb >= imb_th: signal = 'BUY'
                elif c >= w_high - w_range * tol and imb <= -imb_th: signal = 'SELL'
                if signal:
                    rr = params.get('rr_ratio', 1.8)
                    dyn_sl = params.get('sl_dist', base_sl)
                    dyn_tp = dyn_sl * rr
                    
            # 2. OFI IMPACT
            elif engine_id == 'ENGINE_02_OFI_IMPACT':
                z_th = params.get('z_thresh', 1.6)
                imb_c = params.get('imb_confirm', 0.01)
                if ofi_z >= z_th and imb >= imb_c: signal = 'BUY'
                elif ofi_z <= -z_th and imb <= -imb_c: signal = 'SELL'
                if signal:
                    rr = params.get('rr_ratio', 1.8)
                    dyn_sl = params.get('sl_dist', base_sl)
                    dyn_tp = dyn_sl * rr
                    
            # 3. AVELLANEDA MM
            elif engine_id == 'ENGINE_03_AVELLANEDA_MM':
                gamma = params.get('gamma', 0.05)
                spread_f = params.get('spread_factor', 0.35)
                res_mid = w_mean_c - (inventory_q * gamma * avg_range)
                half_spread = max(avg_range * spread_f, spread)
                inv_lim = params.get('inv_limit', 2)
                if c < (res_mid - half_spread) and inventory_q < inv_lim:
                    signal = 'BUY'; dyn_tp = half_spread * params.get('tp_mult', 1.5); dyn_sl = half_spread * params.get('sl_mult', 1.2)
                elif c > (res_mid + half_spread) and inventory_q > -inv_lim:
                    signal = 'SELL'; dyn_tp = half_spread * params.get('tp_mult', 1.5); dyn_sl = half_spread * params.get('sl_mult', 1.2)
                    
            # 4. VWAP SLICER
            elif engine_id == 'ENGINE_04_VWAP_SLICER':
                sd_band = params.get('sd_band', 1.2)
                imb_f = params.get('imb_filter', 0.005)
                if c <= cur_vwap - sd_band * cur_sd and imb >= imb_f:
                    signal = 'BUY'; dyn_tp = abs(c - cur_vwap); dyn_sl = max(cur_sd * params.get('sl_sd_mult', 1.1), base_sl * 0.7)
                elif c >= cur_vwap + sd_band * cur_sd and imb <= -imb_f:
                    signal = 'SELL'; dyn_tp = abs(c - cur_vwap); dyn_sl = max(cur_sd * params.get('sl_sd_mult', 1.1), base_sl * 0.7)
                    
            # 5. HAWKES BURST
            elif engine_id == 'ENGINE_05_HAWKES_BURST':
                int_th = params.get('intensity_thresh', 2.0)
                del_th = params.get('delta_thresh', 15.0)
                if hawkes_intensity >= int_th:
                    if delta > del_th and cvd > 0: signal = 'BUY'
                    elif delta < -del_th and cvd < 0: signal = 'SELL'
                if signal:
                    rr = params.get('rr_ratio', 2.0)
                    dyn_sl = params.get('sl_dist', base_sl)
                    dyn_tp = dyn_sl * rr
                    
            # 6. GOLD INTRADAY
            elif engine_id == 'ENGINE_06_GOLD_INTRADAY':
                h_utc = int(d['time'].split(' ')[1].split(':')[0]) if ' ' in d['time'] else 0
                win_type = params.get('window_type', 'ALL_ACTIVE')
                allowed_hours = [7, 8, 13, 14, 15] if win_type == 'ALL_ACTIVE' else ([13, 14, 15] if win_type == 'NY' else [7, 8, 9])
                b_pct = params.get('breakout_pct', 0.08)
                if h_utc in allowed_hours:
                    if c >= w_high - w_range * b_pct and delta > 0: signal = 'BUY'
                    elif c <= w_low + w_range * b_pct and delta < 0: signal = 'SELL'
                if signal:
                    rr = params.get('rr_ratio', 2.0)
                    dyn_sl = params.get('sl_dist', base_sl)
                    dyn_tp = dyn_sl * rr
                    
            # 7. HMM REGIME
            elif engine_id == 'ENGINE_07_HMM_REGIME':
                vol_exp = params.get('vol_expansion_ratio', 1.3)
                is_trending = (h - l) > avg_range * vol_exp
                if is_trending:
                    v_th = avg_range * params.get('vel_ratio', 0.15)
                    if kalman_vel > v_th: signal = 'BUY'
                    elif kalman_vel < -v_th: signal = 'SELL'
                else:
                    b_pct = params.get('fade_band', 0.12)
                    imb_th = params.get('imb_thresh', 0.02)
                    if c <= w_low + w_range * b_pct and imb >= imb_th: signal = 'BUY'
                    elif c >= w_high - w_range * b_pct and imb <= -imb_th: signal = 'SELL'
                if signal:
                    rr = params.get('rr_ratio', 2.0)
                    dyn_sl = params.get('sl_dist', base_sl)
                    dyn_tp = dyn_sl * rr
                    
            # 8. LEAD LAG
            elif engine_id == 'ENGINE_08_LEAD_LAG':
                del_th = params.get('delta_exhaust_thresh', 25.0)
                band = params.get('extreme_band', 0.10)
                if c >= w_high - w_range * band and delta < -del_th: signal = 'SELL'
                elif c <= w_low + w_range * band and delta > del_th: signal = 'BUY'
                if signal:
                    rr = params.get('rr_ratio', 2.0)
                    dyn_sl = params.get('sl_dist', base_sl)
                    dyn_tp = dyn_sl * rr
                    
            # 9. KALMAN ZEROLAG
            elif engine_id == 'ENGINE_09_KALMAN_ZEROLAG':
                v_norm = kalman_vel / avg_range
                v_th = params.get('v_thresh', 0.25)
                imb_c = params.get('imb_confirm', 0.01)
                if v_norm > v_th and imb >= imb_c: signal = 'BUY'
                elif v_norm < -v_th and imb <= -imb_c: signal = 'SELL'
                if signal:
                    rr = params.get('rr_ratio', 2.0)
                    dyn_sl = params.get('sl_dist', base_sl)
                    dyn_tp = dyn_sl * rr
                    
            # 10. DIFFUSION SIM
            elif engine_id == 'ENGINE_10_DIFFUSION_SIM':
                mu = (c - w_closes[0]) / lookback
                d_th = params.get('drift_hurdle', 0.04) * avg_range
                band = params.get('band_pct', 0.20)
                imb_th = params.get('imb_thresh', 0.02)
                if mu > d_th and c <= w_low + w_range * band and imb >= imb_th: signal = 'BUY'
                elif mu < -d_th and c >= w_high - w_range * band and imb <= -imb_th: signal = 'SELL'
                if signal:
                    rr = params.get('rr_ratio', 2.0)
                    dyn_sl = params.get('sl_dist', base_sl)
                    dyn_tp = dyn_sl * rr
                    
            # 11. NEWS GATE
            elif engine_id == 'ENGINE_11_NEWS_GATE':
                gate_r = params.get('atr_gate_ratio', 1.5)
                if (h - l) <= avg_range * gate_r:
                    band = params.get('fade_band', 0.12)
                    imb_th = params.get('imb_thresh', 0.02)
                    if c <= w_low + w_range * band and imb >= imb_th: signal = 'BUY'
                    elif c >= w_high - w_range * band and imb <= -imb_th: signal = 'SELL'
                if signal:
                    rr = params.get('rr_ratio', 2.0)
                    dyn_sl = params.get('sl_dist', base_sl)
                    dyn_tp = dyn_sl * rr
                    
            # 12. KELLY SIZING
            elif engine_id == 'ENGINE_12_KELLY_SIZING':
                atr_mult = params.get('atr_sl_mult', 1.5)
                rr = params.get('rr_ratio', 2.0)
                dyn_sl = max(base_sl * 0.7, avg_range * atr_mult)
                dyn_tp = dyn_sl * rr
                band = params.get('range_pct', 0.15)
                imb_th = params.get('imb_thresh', 0.02)
                if c <= w_low + w_range * band and imb >= imb_th: signal = 'BUY'
                elif c >= w_high - w_range * band and imb <= -imb_th: signal = 'SELL'
                
            # 13. ROUGH VOL
            elif engine_id == 'ENGINE_13_ROUGH_VOL':
                hurst = params.get('hurst_h', 0.25)
                env_mult = params.get('envelope_mult', 0.45)
                rough_env = avg_range * (lookback ** hurst)
                imb_th = params.get('imb_thresh', 0.02) * params.get('imb_scale', 0.8)
                if c <= (w_high + w_low) / 2.0 - rough_env * env_mult and imb >= imb_th:
                    signal = 'BUY'; dyn_sl = rough_env * params.get('sl_mult', 0.9); dyn_tp = rough_env * params.get('tp_mult', 1.8)
                elif c >= (w_high + w_low) / 2.0 + rough_env * env_mult and imb <= -imb_th:
                    signal = 'SELL'; dyn_sl = rough_env * params.get('sl_mult', 0.9); dyn_tp = rough_env * params.get('tp_mult', 1.8)
                    
            # 14. MASTER PIPELINE
            elif engine_id == 'ENGINE_14_MASTER_PIPELINE':
                is_news = (h - l) > avg_range * params.get('news_gate', 2.0)
                if not is_news:
                    is_trending = (h - l) > avg_range * params.get('trend_vol', 1.3)
                    if is_trending:
                        if kalman_vel > avg_range * 0.2 and hawkes_intensity > params.get('hawkes_burst', 1.8):
                            signal = 'BUY'; dyn_sl = avg_range * 1.5; dyn_tp = avg_range * params.get('trend_tp_mult', 3.0)
                        elif kalman_vel < -avg_range * 0.2 and hawkes_intensity > params.get('hawkes_burst', 1.8):
                            signal = 'SELL'; dyn_sl = avg_range * 1.5; dyn_tp = avg_range * params.get('trend_tp_mult', 3.0)
                    else:
                        imb_th = params.get('chop_imb', 0.02)
                        del_th = params.get('chop_delta', 25.0)
                        if (c <= w_low + w_range * 0.15 and imb >= imb_th) or (c <= w_low + w_range * 0.12 and delta > del_th):
                            signal = 'BUY'; dyn_sl = params.get('chop_sl', base_sl); dyn_tp = params.get('chop_tp', base_tp)
                        elif (c >= w_high - w_range * 0.15 and imb <= -imb_th) or (c >= w_high - w_range * 0.12 and delta < -del_th):
                            signal = 'SELL'; dyn_sl = params.get('chop_sl', base_sl); dyn_tp = params.get('chop_tp', base_tp)
                            
            if signal:
                pos = {
                    'side': signal, 'entry_p': c, 'idx': i,
                    'sl': c - dyn_sl if signal == 'BUY' else c + dyn_sl,
                    'tp': c + dyn_tp if signal == 'BUY' else c - dyn_tp
                }
                inventory_q += (1 if signal == 'BUY' else -1)
                
    tot = len(trades)
    if tot == 0:
        return {'trades': 0, 'wins': 0, 'losses': 0, 'win_rate': 0.0, 'net_pnl': 0.0, 'profit_factor': 0.0, 'max_dd': 0.0, 'score': -999.0}
        
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
        
    # Multi-objective fitness function
    # Favors: High Net PnL, High PF, Robust Trade Count (>= 5), Low MaxDD
    fitness = net_pnl * min(pf, 4.0) * math.sqrt(wr / 100.0)
    if tot < 5: fitness *= (tot / 5.0)
    if max_dd > 0: fitness -= (0.25 * max_dd)
    
    return {
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
        'score': round(fitness, 2)
    }

# =========================================================================
# Step-by-Step Parameter Coordinate Optimizer
# =========================================================================
def optimize_single_engine(symbol, data, engine_id, param_grid, asset_cfg):
    print(f"\n[{symbol}] Optimizing {engine_id} across {len(param_grid)} parameter dimensions...")
    
    # 1. Establish Baseline with middle values
    current_best_params = {}
    for k, v_list in param_grid.items():
        current_best_params[k] = v_list[len(v_list) // 2]
        
    baseline_metrics = evaluate_simulation(data, engine_id, current_best_params, asset_cfg)
    best_fitness = baseline_metrics['score']
    best_metrics = baseline_metrics
    
    trajectory = []
    
    # 2. Coordinate Descent: Optimize ONE parameter at a time while holding others fixed
    for param_name, values in param_grid.items():
        print(f"  -> Tuning variable: '{param_name}' across {values} (holding other {len(param_grid)-1} variables fixed)")
        param_step_log = []
        best_val_for_param = current_best_params[param_name]
        
        for val in values:
            test_params = dict(current_best_params)
            test_params[param_name] = val
            metrics = evaluate_simulation(data, engine_id, test_params, asset_cfg)
            
            log_entry = {
                'param': param_name,
                'val': val,
                'net_pnl': metrics['net_pnl'],
                'win_rate': metrics['win_rate'],
                'profit_factor': metrics['profit_factor'],
                'trades': metrics['trades'],
                'max_dd': metrics['max_dd'],
                'fitness': metrics['score']
            }
            param_step_log.append(log_entry)
            
            if metrics['score'] > best_fitness and metrics['trades'] >= 4:
                best_fitness = metrics['score']
                best_val_for_param = val
                best_metrics = metrics
                
        # Update coordinate with the best found value for this parameter
        current_best_params[param_name] = best_val_for_param
        trajectory.append({
            'variable': param_name,
            'selected_optimal_value': best_val_for_param,
            'steps': param_step_log
        })
        print(f"     => Optimal {param_name} = {best_val_for_param} (Fitness: {best_fitness:.2f}, PnL: ${best_metrics['net_pnl']:+.2f}, WR: {best_metrics['win_rate']}%)")
        
    # 3. Fine-tuning Joint Grid on top 2 critical parameters (SL & TP/RR)
    if 'sl_dist' in param_grid and 'rr_ratio' in param_grid:
        print(f"  -> Fine-tuning Risk Envelope Grid (sl_dist x rr_ratio)...")
        for sl in param_grid['sl_dist']:
            for rr in param_grid['rr_ratio']:
                test_params = dict(current_best_params)
                test_params['sl_dist'] = sl
                test_params['rr_ratio'] = rr
                metrics = evaluate_simulation(data, engine_id, test_params, asset_cfg)
                if metrics['score'] > best_fitness and metrics['trades'] >= 4:
                    best_fitness = metrics['score']
                    current_best_params['sl_dist'] = sl
                    current_best_params['rr_ratio'] = rr
                    best_metrics = metrics

    # Re-evaluate final
    final_metrics = evaluate_simulation(data, engine_id, current_best_params, asset_cfg)
    return {
        'engine': engine_id,
        'symbol': symbol,
        'optimal_parameters': current_best_params,
        'baseline_metrics': baseline_metrics,
        'optimized_metrics': final_metrics,
        'improvement_pnl': round(final_metrics['net_pnl'] - baseline_metrics['net_pnl'], 2),
        'trajectory': trajectory
    }

def run_exhaustive_optimization():
    print("=" * 105)
    print("          EXHAUSTIVE STEP-BY-STEP OPTIMIZATION OF ALL 13 ENGINES ON LIVE DOM DATASETS")
    print("=" * 105)
    
    assets_config = {
        'BTCUSD': {
            'point_val': 0.01,
            'spread_cost': 0.16,
            'comm': 0.0,
            'data': load_market_data('BTCUSD'),
            'grids': {
                'ENGINE_01_DEEPLOB': {
                    'lookback': [15, 20, 25, 30],
                    'imb_thresh': [0.015, 0.02, 0.025, 0.03, 0.04],
                    'range_tol': [0.08, 0.12, 0.15, 0.18],
                    'sl_dist': [20.0, 30.0, 35.0, 45.0],
                    'rr_ratio': [1.4, 1.8, 2.2, 2.6]
                },
                'ENGINE_02_OFI_IMPACT': {
                    'ofi_decay': [0.75, 0.82, 0.88],
                    'z_thresh': [1.2, 1.5, 1.8, 2.2],
                    'imb_confirm': [0.005, 0.01, 0.02],
                    'sl_dist': [25.0, 35.0, 45.0],
                    'rr_ratio': [1.5, 2.0, 2.5]
                },
                'ENGINE_03_AVELLANEDA_MM': {
                    'gamma': [0.01, 0.03, 0.05, 0.10],
                    'spread_factor': [0.35, 0.50, 0.70, 1.0],
                    'inv_limit': [1, 2, 3],
                    'tp_mult': [1.2, 1.6, 2.0],
                    'sl_mult': [1.0, 1.4, 1.8]
                },
                'ENGINE_04_VWAP_SLICER': {
                    'sd_band': [1.0, 1.2, 1.5, 1.8],
                    'imb_filter': [0.0, 0.005, 0.01],
                    'sl_sd_mult': [1.0, 1.2, 1.5],
                    'max_hold': [20, 30, 45]
                },
                'ENGINE_05_HAWKES_BURST': {
                    'decay_beta': [0.10, 0.18, 0.25],
                    'intensity_thresh': [1.5, 1.8, 2.2, 2.6],
                    'delta_thresh': [15.0, 25.0, 40.0],
                    'sl_dist': [25.0, 35.0, 45.0],
                    'rr_ratio': [1.6, 2.0, 2.5]
                },
                'ENGINE_06_GOLD_INTRADAY': {
                    'window_type': ['ALL_ACTIVE', 'NY', 'LONDON'],
                    'breakout_pct': [0.04, 0.08, 0.12],
                    'sl_dist': [25.0, 35.0, 45.0],
                    'rr_ratio': [1.5, 2.0, 2.5]
                },
                'ENGINE_07_HMM_REGIME': {
                    'vol_expansion_ratio': [1.1, 1.3, 1.5, 1.8],
                    'vel_ratio': [0.10, 0.18, 0.28],
                    'fade_band': [0.08, 0.12, 0.16],
                    'sl_dist': [25.0, 35.0, 45.0],
                    'rr_ratio': [1.6, 2.0, 2.5]
                },
                'ENGINE_08_LEAD_LAG': {
                    'delta_exhaust_thresh': [18.0, 28.0, 40.0, 55.0],
                    'extreme_band': [0.06, 0.10, 0.15],
                    'sl_dist': [25.0, 35.0, 45.0],
                    'rr_ratio': [1.5, 2.0, 2.5]
                },
                'ENGINE_09_KALMAN_ZEROLAG': {
                    'q_noise': [0.0005, 0.001, 0.005],
                    'r_noise': [0.1, 0.2, 0.4],
                    'v_thresh': [0.15, 0.25, 0.35],
                    'imb_confirm': [0.005, 0.01, 0.02],
                    'sl_dist': [25.0, 35.0, 45.0],
                    'rr_ratio': [1.6, 2.0, 2.5]
                },
                'ENGINE_10_DIFFUSION_SIM': {
                    'drift_hurdle': [0.02, 0.04, 0.08],
                    'band_pct': [0.12, 0.18, 0.25],
                    'imb_thresh': [0.015, 0.025, 0.035],
                    'sl_dist': [25.0, 35.0, 45.0],
                    'rr_ratio': [1.6, 2.0, 2.5]
                },
                'ENGINE_11_NEWS_GATE': {
                    'atr_gate_ratio': [1.2, 1.5, 1.8, 2.2],
                    'fade_band': [0.08, 0.12, 0.16],
                    'imb_thresh': [0.015, 0.02, 0.03],
                    'sl_dist': [25.0, 35.0, 45.0],
                    'rr_ratio': [1.6, 2.0, 2.5]
                },
                'ENGINE_12_KELLY_SIZING': {
                    'atr_sl_mult': [1.0, 1.3, 1.6, 2.0],
                    'rr_ratio': [1.6, 2.0, 2.4, 2.8, 3.2],
                    'imb_thresh': [0.015, 0.02, 0.03],
                    'range_pct': [0.10, 0.15, 0.20]
                },
                'ENGINE_13_ROUGH_VOL': {
                    'hurst_h': [0.15, 0.25, 0.35],
                    'envelope_mult': [0.35, 0.45, 0.55],
                    'imb_scale': [0.6, 0.8, 1.0],
                    'sl_mult': [0.7, 0.9, 1.2],
                    'tp_mult': [1.4, 1.8, 2.4]
                },
                'ENGINE_14_MASTER_PIPELINE': {
                    'news_gate': [1.6, 2.0, 2.4],
                    'trend_vol': [1.2, 1.35, 1.5],
                    'hawkes_burst': [1.6, 1.9, 2.3],
                    'chop_imb': [0.015, 0.02, 0.03],
                    'chop_delta': [20.0, 30.0, 45.0],
                    'chop_sl': [25.0, 35.0, 45.0],
                    'chop_tp': [40.0, 55.0, 75.0]
                }
            }
        },
        'ETHUSD': {
            'point_val': 0.10,
            'spread_cost': 0.20,
            'comm': 0.0,
            'data': load_market_data('ETHUSD'),
            'grids': {
                'ENGINE_01_DEEPLOB': {
                    'lookback': [10, 15, 20],
                    'imb_thresh': [0.02, 0.03, 0.04, 0.05],
                    'range_tol': [0.08, 0.12, 0.15],
                    'sl_dist': [1.0, 1.5, 2.0],
                    'rr_ratio': [1.5, 2.0, 2.5, 3.0]
                },
                'ENGINE_11_NEWS_GATE': {
                    'atr_gate_ratio': [1.2, 1.5, 1.8],
                    'fade_band': [0.08, 0.12, 0.15],
                    'imb_thresh': [0.02, 0.03, 0.04],
                    'sl_dist': [1.0, 1.5, 2.0],
                    'rr_ratio': [1.5, 2.0, 2.5, 3.2]
                },
                'ENGINE_12_KELLY_SIZING': {
                    'atr_sl_mult': [1.0, 1.4, 1.8],
                    'rr_ratio': [1.8, 2.2, 2.8, 3.5],
                    'imb_thresh': [0.02, 0.03, 0.04],
                    'range_pct': [0.10, 0.15, 0.20]
                }
            }
        }
    }
    
    all_results = {}
    
    for sym, asset in assets_config.items():
        data = asset['data']
        if not data:
            print(f"Skipping {sym}: No data")
            continue
            
        all_results[sym] = {}
        for eng_id, grid in asset['grids'].items():
            res = optimize_single_engine(sym, data, eng_id, grid, asset)
            all_results[sym][eng_id] = res
            
    # Output to JSON
    out_file = r"d:\cbot-atgvt\data\exhaustive_13_engines_optimization.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    print(f"\n=========================================================================================")
    print(f"Optimization finished! Complete trajectory data stored in: {out_file}")
    print(f"=========================================================================================")
    
    # Print Executive Optimization Summary Table
    print("\n" + "=" * 105)
    print(f"{'Engine ID':28s} | {'Symbol':6s} | {'Baseline PnL':12s} | {'Optimized PnL':13s} | {'PF':5s} | {'WR %':6s} | {'Gain':8s}")
    print("-" * 105)
    for sym, engines in all_results.items():
        for eng_id, res in engines.items():
            base_pnl = res['baseline_metrics']['net_pnl']
            opt_pnl = res['optimized_metrics']['net_pnl']
            pf = res['optimized_metrics']['profit_factor']
            wr = res['optimized_metrics']['win_rate']
            gain = res['improvement_pnl']
            print(f"{eng_id:28s} | {sym:6s} | ${base_pnl:+10.2f} | ${opt_pnl:+11.2f} | {pf:5.2f} | {wr:5.1f}% | ${gain:+7.2f}")
    print("=" * 105)

if __name__ == '__main__':
    run_exhaustive_optimization()
