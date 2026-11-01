"""
Comprehensive Multi-Method Max-Profit Backtester for All 13 Quant Engine Modules
--------------------------------------------------------------------------------
Systematically evaluates multiple advanced algorithmic methods for each module:
- Module 01: DeepLOB (Methods: Standard, Smart DOM Exit, Depth Slope, Dual Extreme)
- Module 02: OFI Impact (Methods: Raw Flow, Z-Score Normalized, OFI Acceleration, Imbalance Confirm)
- Module 03: Avellaneda MM (Methods: Base Fade, Volatility-Widened, Strict Inventory, Trend Veto)
- Module 04: VWAP Slicer (Methods: Fixed SD Fade, Asymmetric Band, VWAP Flat Slope, Micro Time-Exit)
- Module 05: Hawkes Burst (Methods: Tick Jump, Volume-Weighted Hawkes, CVD Delta Confirm, HMM Trend Veto)
- Module 06: Gold Intraday (Methods: VAH/VAL Break, POC Fade, Overlap Delta Thrust, 60m Trailing)
- Module 07: HMM Regime (Methods: Dual Router, Transition Shock Veto, Volatility Expansion Ride)
- Module 08: Lead-Lag CVD (Methods: Bearish/Bullish Divergence, Extreme Delta 50, CVD Slope Flip)
- Module 09: Kalman Zero-Lag (Methods: Zero Crossing, Acceleration Filter, ATR-Normalized Hurdle)
- Module 10: Diffusion Sim (Methods: Drift Hurdle, Barrier Hitting > 65%, Local Vol Adjusted)
- Module 11: News Gate (Methods: Range Spike Gate, Spread-to-ATR Gate, Post-News Consolidation)
- Module 12: Kelly Risk (Methods: Dynamic ATR 1.5x/3.0x, Asymmetric 2.0x/2.8x, Trailing Kelly Stop)
- Module 13: Rough Vol (Methods: Fixed Hurst Envelope, Dual Memory Kernel, Roughness Snapback)
- Module 14: Master Pipeline (Methods: Standard 5-Tier, Top-Alpha Multi-Engine Vote, Dynamic Kelly Master)

Datasets: Real continuous Live DOM & Order Flow (BTCUSD, ETHUSD) + Active Gold Data
"""

import os
import sys
import math
import json
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')
sys.path.append(r'd:\cbot-atgvt\research')
from optimize_all_strategies import load_market_data

def run_backtest_method(data, engine_id, method_name, method_params, asset_cfg):
    point_val = asset_cfg.get('point_val', 0.01)
    spread_cost = asset_cfg.get('spread_cost', 0.16)
    comm = asset_cfg.get('comm', 0.0)
    
    n = len(data)
    trades = []
    pos = None
    
    # State trackers
    kalman_pos = data[0]['close']
    kalman_vel = 0.0
    prev_kalman_vel = 0.0
    p00 = 1.0; p11 = 1.0
    hawkes_intensity = 1.0
    cum_ofi = 0.0
    inventory_q = 0
    prev_bid = data[0]['close']
    prev_ask = data[0]['close'] + spread_cost
    last_exit_idx = -10
    ofi_history = []
    
    lookback = int(method_params.get('lookback', 20))
    max_hold = int(method_params.get('max_hold', 35))
    base_sl = float(method_params.get('sl_dist', 35.0))
    base_tp = float(method_params.get('tp_dist', 70.0))
    
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
        
        # 1. State Updates
        # Kalman
        z = c
        x0_p = kalman_pos + kalman_vel
        p00_p = p00 + p11 + 0.001
        p11_p = p11 + 0.001
        res = z - x0_p
        s_k = p00_p + 0.2
        k0 = p00_p / s_k
        k1 = p11_p / s_k
        kalman_pos = x0_p + k0 * res
        prev_kalman_vel = kalman_vel
        kalman_vel = kalman_vel + k1 * res
        p00 = (1 - k0) * p00_p
        p11 = (1 - k1) * p11_p
        
        # Hawkes
        decay_beta = method_params.get('decay_beta', 0.18)
        hawkes_intensity = 0.2 + (hawkes_intensity - 0.2) * math.exp(-decay_beta) + (0.5 * (ticks / avg_ticks))
        
        # OFI
        curr_bid = c - spread / 2.0
        curr_ask = c + spread / 2.0
        d_b = curr_bid if curr_bid >= prev_bid else -curr_bid
        d_a = curr_ask if curr_ask <= prev_ask else -curr_ask
        step_ofi = (d_b - d_a) * (1.0 + imb * 5.0)
        cum_ofi = 0.82 * cum_ofi + step_ofi
        prev_bid = curr_bid; prev_ask = curr_ask
        ofi_history.append(cum_ofi)
        if len(ofi_history) > lookback: ofi_history.pop(0)
        ofi_std = max(np.std(ofi_history), 1.0)
        ofi_z = cum_ofi / ofi_std
        
        # 2. Check Exits (if in position)
        if pos is not None:
            side = pos['side']
            entry_p = pos['entry_p']
            sl = pos['sl']
            tp = pos['tp']
            entry_i = pos['idx']
            hold_time = i - entry_i
            
            exit_p = None
            reason = None
            
            # Smart DOM Exit check
            if method_params.get('use_smart_dom_exit', False):
                pts_curr = (c - entry_p) if side == 'BUY' else (entry_p - c)
                if pts_curr > (base_sl * 0.8): # in profit
                    if side == 'BUY' and imb <= -0.035:
                        exit_p = c; reason = 'SMART_DOM_WALL_EXIT'
                    elif side == 'SELL' and imb >= 0.035:
                        exit_p = c; reason = 'SMART_DOM_WALL_EXIT'
                        
            # Trailing Stop check
            if exit_p is None and method_params.get('use_trailing_stop', False):
                trail_pts = avg_range * 1.2
                if side == 'BUY':
                    if h - entry_p > trail_pts:
                        new_sl = h - trail_pts
                        if new_sl > pos['sl']: pos['sl'] = new_sl
                else:
                    if entry_p - l > trail_pts:
                        new_sl = l + trail_pts
                        if new_sl < pos['sl']: pos['sl'] = new_sl
                        
            # Standard TP / SL / Max Hold
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
                    'pnl': round(pnl, 2), 'reason': reason, 'hold': hold_time
                })
                inventory_q += (-1 if side == 'BUY' else 1)
                pos = None
                last_exit_idx = i
                continue
                
        # 3. Check Entries
        if pos is None and (i - last_exit_idx >= 1):
            signal = None
            dyn_sl = base_sl
            dyn_tp = base_tp
            
            # =================================================================
            # MODULE 01: DEEPLOB (Spatial L2 Order Book Depth Imbalance)
            # =================================================================
            if engine_id == 'ENGINE_01_DEEPLOB':
                tol = method_params.get('range_tol', 0.15)
                imb_th = method_params.get('imb_thresh', 0.02)
                
                if method_name == 'METHOD_1A_STANDARD_WALL':
                    if c <= w_low + w_range * tol and imb >= imb_th: signal = 'BUY'
                    elif c >= w_high - w_range * tol and imb <= -imb_th: signal = 'SELL'
                elif method_name == 'METHOD_1B_SMART_DOM_EXIT':
                    if c <= w_low + w_range * tol and imb >= imb_th: signal = 'BUY'
                    elif c >= w_high - w_range * tol and imb <= -imb_th: signal = 'SELL'
                elif method_name == 'METHOD_1C_EXTREME_DEPTH_ABSORPTION':
                    # Tight 10% extreme band + high imbalance wall
                    if c <= w_low + w_range * 0.10 and imb >= 0.03: signal = 'BUY'
                    elif c >= w_high - w_range * 0.10 and imb <= -0.03: signal = 'SELL'
                elif method_name == 'METHOD_1D_DUAL_CONFIRM_DELTA':
                    # Level 2 wall + Delta volume rejection
                    if c <= w_low + w_range * tol and imb >= imb_th and delta > 0: signal = 'BUY'
                    elif c >= w_high - w_range * tol and imb <= -imb_th and delta < 0: signal = 'SELL'
                if signal:
                    dyn_sl = method_params.get('sl_dist', base_sl)
                    dyn_tp = dyn_sl * method_params.get('rr_ratio', 2.6)

            # =================================================================
            # MODULE 02: OFI IMPACT (Cont & Stoikov Order Flow Imbalance)
            # =================================================================
            elif engine_id == 'ENGINE_02_OFI_IMPACT':
                z_th = method_params.get('z_thresh', 1.8)
                if method_name == 'METHOD_2A_RAW_OFI_FLOW':
                    if cum_ofi > 20: signal = 'BUY'
                    elif cum_ofi < -20: signal = 'SELL'
                elif method_name == 'METHOD_2B_Z_SCORE_NORMALIZED':
                    if ofi_z >= z_th: signal = 'BUY'
                    elif ofi_z <= -z_th: signal = 'SELL'
                elif method_name == 'METHOD_2C_OFI_ACCELERATION':
                    # Velocity of OFI
                    d_ofi = ofi_history[-1] - ofi_history[-2] if len(ofi_history) >= 2 else 0
                    if ofi_z >= z_th and d_ofi > 0: signal = 'BUY'
                    elif ofi_z <= -z_th and d_ofi < 0: signal = 'SELL'
                elif method_name == 'METHOD_2D_OFI_IMBALANCE_HYBRID':
                    if ofi_z >= 1.6 and imb >= 0.02: signal = 'BUY'
                    elif ofi_z <= -1.6 and imb <= -0.02: signal = 'SELL'
                if signal:
                    dyn_sl = method_params.get('sl_dist', base_sl)
                    dyn_tp = dyn_sl * method_params.get('rr_ratio', 2.5)

            # =================================================================
            # MODULE 03: AVELLANEDA MM (Reservation Price Market Making)
            # =================================================================
            elif engine_id == 'ENGINE_03_AVELLANEDA_MM':
                gamma = method_params.get('gamma', 0.05)
                res_mid = w_mean_c - (inventory_q * gamma * avg_range)
                spread_f = method_params.get('spread_factor', 0.6)
                half_spread = max(avg_range * spread_f, spread)
                
                if method_name == 'METHOD_3A_STANDARD_QUOTE':
                    if c < (res_mid - half_spread) and inventory_q < 2: signal = 'BUY'
                    elif c > (res_mid + half_spread) and inventory_q > -2: signal = 'SELL'
                elif method_name == 'METHOD_3B_WIDE_VOLATILITY_BAND':
                    # Wide half-spread 1.0x ATR to eliminate spread friction
                    hs_wide = avg_range * 1.0
                    if c < (res_mid - hs_wide) and inventory_q < 2: signal = 'BUY'
                    elif c > (res_mid + hs_wide) and inventory_q > -2: signal = 'SELL'
                elif method_name == 'METHOD_3C_STRICT_INVENTORY_LIMIT_1':
                    if c < (res_mid - half_spread) and inventory_q == 0: signal = 'BUY'
                    elif c > (res_mid + half_spread) and inventory_q == 0: signal = 'SELL'
                elif method_name == 'METHOD_3D_TREND_VETO_CHOP_ONLY':
                    # Only quote when candle range is quiet
                    if (h - l) < avg_range * 1.2:
                        if c < (res_mid - half_spread) and inventory_q < 2: signal = 'BUY'
                        elif c > (res_mid + half_spread) and inventory_q > -2: signal = 'SELL'
                if signal:
                    dyn_sl = half_spread * 1.2
                    dyn_tp = half_spread * 2.0

            # =================================================================
            # MODULE 04: VWAP SLICER (Anchored VWAP 1.5 SD Mean Reversion)
            # =================================================================
            elif engine_id == 'ENGINE_04_VWAP_SLICER':
                sd_b = method_params.get('sd_band', 1.5)
                if method_name == 'METHOD_4A_FIXED_SD_FADE':
                    if c <= cur_vwap - sd_b * cur_sd: signal = 'BUY'
                    elif c >= cur_vwap + sd_b * cur_sd: signal = 'SELL'
                elif method_name == 'METHOD_4B_VWAP_PLUS_BOOK_CONFIRM':
                    if c <= cur_vwap - sd_b * cur_sd and imb >= 0.005: signal = 'BUY'
                    elif c >= cur_vwap + sd_b * cur_sd and imb <= -0.005: signal = 'SELL'
                elif method_name == 'METHOD_4C_FLAT_VWAP_SLOPE':
                    # VWAP slope is flat (true mean-reverting environment)
                    vwap_diff = cur_vwap - data[i-5]['vwap'] if data[i-5]['vwap'] > 0 else 0
                    if abs(vwap_diff) < avg_range * 0.1:
                        if c <= cur_vwap - sd_b * cur_sd and imb >= 0.005: signal = 'BUY'
                        elif c >= cur_vwap + sd_b * cur_sd and imb <= -0.005: signal = 'SELL'
                elif method_name == 'METHOD_4D_MICRO_TIME_HOLD_25':
                    if c <= cur_vwap - sd_b * cur_sd and imb >= 0.005: signal = 'BUY'
                    elif c >= cur_vwap + sd_b * cur_sd and imb <= -0.005: signal = 'SELL'
                if signal:
                    dyn_tp = abs(c - cur_vwap)
                    dyn_sl = max(cur_sd * 1.0, base_sl * 0.7)

            # =================================================================
            # MODULE 05: HAWKES BURST (Self-Exciting Point Process Cascades)
            # =================================================================
            elif engine_id == 'ENGINE_05_HAWKES_BURST':
                int_th = method_params.get('intensity_thresh', 2.2)
                del_th = method_params.get('delta_thresh', 40.0)
                if method_name == 'METHOD_5A_TICK_BURST':
                    if hawkes_intensity >= int_th:
                        if delta > 0: signal = 'BUY'
                        elif delta < 0: signal = 'SELL'
                elif method_name == 'METHOD_5B_HIGH_DELTA_BURST':
                    if hawkes_intensity >= int_th and abs(delta) >= del_th:
                        if delta > 0 and cvd > 0: signal = 'BUY'
                        elif delta < 0 and cvd < 0: signal = 'SELL'
                elif method_name == 'METHOD_5C_EXPANSION_REGIME_BURST':
                    # Only trigger Hawkes momentum during volatility expansion
                    if (h - l) > avg_range * 1.3 and hawkes_intensity >= 2.0:
                        if delta > del_th: signal = 'BUY'
                        elif delta < -del_th: signal = 'SELL'
                elif method_name == 'METHOD_5D_BURST_TRAILING_RUNNER':
                    if hawkes_intensity >= 2.0 and delta > del_th: signal = 'BUY'
                    elif hawkes_intensity >= 2.0 and delta < -del_th: signal = 'SELL'
                if signal:
                    dyn_sl = method_params.get('sl_dist', base_sl)
                    dyn_tp = dyn_sl * method_params.get('rr_ratio', 2.5)

            # =================================================================
            # MODULE 06: GOLD INTRADAY / AUCTION (Session Liquidity Window)
            # =================================================================
            elif engine_id == 'ENGINE_06_GOLD_INTRADAY':
                h_utc = int(d['time'].split(' ')[1].split(':')[0]) if ' ' in d['time'] else 0
                if method_name == 'METHOD_6A_NY_OPEN_BREAKOUT':
                    if h_utc in [13, 14, 15]: # NY Open 13:00 UTC
                        if c >= w_high - w_range * 0.05 and delta > 0: signal = 'BUY'
                        elif c <= w_low + w_range * 0.05 and delta < 0: signal = 'SELL'
                elif method_name == 'METHOD_6B_ACTIVE_OVERLAP_WINDOW':
                    if h_utc in [7, 8, 13, 14, 15]:
                        if c >= w_high - w_range * 0.04 and delta > 0: signal = 'BUY'
                        elif c <= w_low + w_range * 0.04 and delta < 0: signal = 'SELL'
                elif method_name == 'METHOD_6C_AUCTION_VALUE_FADE':
                    # Fade at session value boundaries back to POC
                    vah = d['vah'] if d['vah'] > 0 else d['prev_vah']
                    val = d['val'] if d['val'] > 0 else d['prev_val']
                    if vah > 0 and val > 0:
                        if c >= vah and imb <= -0.02: signal = 'SELL'
                        elif c <= val and imb >= 0.02: signal = 'BUY'
                elif method_name == 'METHOD_6D_SESSION_TRAILING_60M':
                    if h_utc in [7, 8, 13, 14, 15] and c >= w_high - w_range * 0.05: signal = 'BUY'
                    elif h_utc in [7, 8, 13, 14, 15] and c <= w_low + w_range * 0.05: signal = 'SELL'
                if signal:
                    dyn_sl = method_params.get('sl_dist', base_sl)
                    dyn_tp = dyn_sl * method_params.get('rr_ratio', 2.5)

            # =================================================================
            # MODULE 07: HMM REGIME (Markov Switching Multi-State Switcher)
            # =================================================================
            elif engine_id == 'ENGINE_07_HMM_REGIME':
                vol_exp = method_params.get('vol_expansion_ratio', 1.8)
                is_trending = (h - l) > avg_range * vol_exp
                if method_name == 'METHOD_7A_DUAL_ROUTER':
                    if is_trending:
                        if kalman_vel > avg_range * 0.28: signal = 'BUY'
                        elif kalman_vel < -avg_range * 0.28: signal = 'SELL'
                    else:
                        if c <= w_low + w_range * 0.08 and imb >= 0.02: signal = 'BUY'
                        elif c >= w_high - w_range * 0.08 and imb <= -0.02: signal = 'SELL'
                elif method_name == 'METHOD_7B_TREND_ONLY_STATE':
                    if is_trending:
                        if kalman_vel > avg_range * 0.25: signal = 'BUY'
                        elif kalman_vel < -avg_range * 0.25: signal = 'SELL'
                elif method_name == 'METHOD_7C_CHOP_ONLY_STATE':
                    if not is_trending:
                        if c <= w_low + w_range * 0.08 and imb >= 0.025: signal = 'BUY'
                        elif c >= w_high - w_range * 0.08 and imb <= -0.025: signal = 'SELL'
                elif method_name == 'METHOD_7D_PROBABILITY_WEIGHTED':
                    prob_trend = min(max(((h - l) / avg_range) - 1.0, 0.0), 1.0)
                    if prob_trend > 0.6:
                        if kalman_vel > 0: signal = 'BUY'
                        else: signal = 'SELL'
                    elif prob_trend < 0.3:
                        if c <= w_low + w_range * 0.1 and imb >= 0.02: signal = 'BUY'
                        elif c >= w_high - w_range * 0.1 and imb <= -0.02: signal = 'SELL'
                if signal:
                    dyn_sl = method_params.get('sl_dist', base_sl)
                    dyn_tp = dyn_sl * method_params.get('rr_ratio', 2.0)

            # =================================================================
            # MODULE 08: LEAD-LAG CVD (Cumulative Delta Divergence & Absorption)
            # =================================================================
            elif engine_id == 'ENGINE_08_LEAD_LAG':
                del_th = method_params.get('delta_exhaust_thresh', 55.0)
                band = method_params.get('extreme_band', 0.06)
                if method_name == 'METHOD_8A_EXTREME_DELTA_EXHAUSTION':
                    if c >= w_high - w_range * band and delta < -del_th: signal = 'SELL'
                    elif c <= w_low + w_range * band and delta > del_th: signal = 'BUY'
                elif method_name == 'METHOD_8B_CVD_PRICE_DIVERGENCE':
                    # Price tests extreme, but CVD is opposing
                    if c >= w_high - w_range * 0.08 and cvd < 0 and delta < -20: signal = 'SELL'
                    elif c <= w_low + w_range * 0.08 and cvd > 0 and delta > 20: signal = 'BUY'
                elif method_name == 'METHOD_8C_DELTA_SLOPE_REVERSAL':
                    d_del = delta - data[i-1]['delta']
                    if c >= w_high - w_range * band and d_del < -30: signal = 'SELL'
                    elif c <= w_low + w_range * band and d_del > 30: signal = 'BUY'
                elif method_name == 'METHOD_8D_LEAD_LAG_TRAILING_TARGET':
                    if c >= w_high - w_range * band and delta < -del_th: signal = 'SELL'
                    elif c <= w_low + w_range * band and delta > del_th: signal = 'BUY'
                if signal:
                    dyn_sl = method_params.get('sl_dist', base_sl)
                    dyn_tp = dyn_sl * method_params.get('rr_ratio', 2.5)

            # =================================================================
            # MODULE 09: KALMAN ZERO-LAG (State-Space Velocity Filter)
            # =================================================================
            elif engine_id == 'ENGINE_09_KALMAN_ZEROLAG':
                v_norm = kalman_vel / avg_range
                v_th = method_params.get('v_thresh', 0.25)
                if method_name == 'METHOD_9A_ZERO_CROSSING':
                    if kalman_vel > 0 and prev_kalman_vel <= 0: signal = 'BUY'
                    elif kalman_vel < 0 and prev_kalman_vel >= 0: signal = 'SELL'
                elif method_name == 'METHOD_9B_VELOCITY_HURDLE_FILTER':
                    if v_norm > v_th and imb >= 0.02: signal = 'BUY'
                    elif v_norm < -v_th and imb <= -0.02: signal = 'SELL'
                elif method_name == 'METHOD_9C_ACCELERATION_CONFIRM':
                    accel = kalman_vel - prev_kalman_vel
                    if v_norm > 0.15 and accel > 0 and imb >= 0.015: signal = 'BUY'
                    elif v_norm < -0.15 and accel < 0 and imb <= -0.015: signal = 'SELL'
                elif method_name == 'METHOD_9D_ZERO_LAG_RUNNER':
                    if v_norm > v_th and imb >= 0.02: signal = 'BUY'
                    elif v_norm < -v_th and imb <= -0.02: signal = 'SELL'
                if signal:
                    dyn_sl = method_params.get('sl_dist', base_sl)
                    dyn_tp = dyn_sl * method_params.get('rr_ratio', 2.5)

            # =================================================================
            # MODULE 10: DIFFUSION SIM (Stochastic Barrier Stopping Time)
            # =================================================================
            elif engine_id == 'ENGINE_10_DIFFUSION_SIM':
                mu = (c - w_closes[0]) / lookback
                sigma = max(np.std(w_closes), 0.01)
                d_th = method_params.get('drift_hurdle', 0.04) * avg_range
                band = method_params.get('band_pct', 0.18)
                imb_th = method_params.get('imb_thresh', 0.025)
                
                # Analytical barrier probability
                sl_pts = base_sl; tp_pts = base_sl * 2.0
                prob_up = (1.0 - math.exp(-2.0 * max(mu, 0.001) * sl_pts / (sigma**2))) / max((1.0 - math.exp(-2.0 * max(mu, 0.001) * (tp_pts + sl_pts) / (sigma**2))), 0.0001)
                
                if method_name == 'METHOD_10A_DRIFT_BARRIER':
                    if mu > d_th and c <= w_low + w_range * band and imb >= imb_th: signal = 'BUY'
                    elif mu < -d_th and c >= w_high - w_range * band and imb <= -imb_th: signal = 'SELL'
                elif method_name == 'METHOD_10B_PROBABILITY_HURDLE_65':
                    if prob_up > 0.65 and imb >= imb_th: signal = 'BUY'
                    elif (1.0 - prob_up) > 0.65 and imb <= -imb_th: signal = 'SELL'
                elif method_name == 'METHOD_10C_LOCAL_VOL_ADAPTIVE':
                    if mu > 0.02 * avg_range and imb >= imb_th and (h - l) < avg_range * 1.2: signal = 'BUY'
                    elif mu < -0.02 * avg_range and imb <= -imb_th and (h - l) < avg_range * 1.2: signal = 'SELL'
                elif method_name == 'METHOD_10D_BARRIER_OPTIMAL_STOP':
                    if mu > d_th and imb >= imb_th: signal = 'BUY'
                    elif mu < -d_th and imb <= -imb_th: signal = 'SELL'
                if signal:
                    dyn_sl = base_sl
                    dyn_tp = base_tp

            # =================================================================
            # MODULE 11: NEWS GATE (Volatility Spike Blackout & Safety Gate)
            # =================================================================
            elif engine_id == 'ENGINE_11_NEWS_GATE':
                gate_r = method_params.get('atr_gate_ratio', 1.8)
                band = method_params.get('fade_band', 0.08)
                imb_th = method_params.get('imb_thresh', 0.02)
                
                if method_name == 'METHOD_11A_RANGE_SPIKE_GATE':
                    if (h - l) <= avg_range * gate_r:
                        if c <= w_low + w_range * band and imb >= imb_th: signal = 'BUY'
                        elif c >= w_high - w_range * band and imb <= -imb_th: signal = 'SELL'
                elif method_name == 'METHOD_11B_SPREAD_TO_ATR_GATE':
                    # Strict Gate: Spread must be < 0.35x ATR
                    if (spread / avg_range) < 0.35 and (h - l) <= avg_range * 1.5:
                        if c <= w_low + w_range * band and imb >= imb_th: signal = 'BUY'
                        elif c >= w_high - w_range * band and imb <= -imb_th: signal = 'SELL'
                elif method_name == 'METHOD_11C_POST_NEWS_ABSORPTION':
                    # Enter after a spike has settled
                    prev_spike = (data[i-1]['high'] - data[i-1]['low']) > avg_range * 1.8
                    if prev_spike and (h - l) < avg_range * 1.2:
                        if imb >= 0.03: signal = 'BUY'
                        elif imb <= -0.03: signal = 'SELL'
                elif method_name == 'METHOD_11D_NEWS_GATE_SMART_EXIT':
                    if (h - l) <= avg_range * gate_r:
                        if c <= w_low + w_range * band and imb >= imb_th: signal = 'BUY'
                        elif c >= w_high - w_range * band and imb <= -imb_th: signal = 'SELL'
                if signal:
                    dyn_sl = method_params.get('sl_dist', base_sl)
                    dyn_tp = dyn_sl * method_params.get('rr_ratio', 2.5)

            # =================================================================
            # MODULE 12: KELLY SIZING (Dynamic ATR Kelly Volatility Risk)
            # =================================================================
            elif engine_id == 'ENGINE_12_KELLY_SIZING':
                atr_mult = method_params.get('atr_sl_mult', 2.0)
                rr = method_params.get('rr_ratio', 2.8)
                band = method_params.get('range_pct', 0.15)
                imb_th = method_params.get('imb_thresh', 0.03)
                
                if method_name == 'METHOD_12A_ASYMMETRIC_KELLY_2_8':
                    dyn_sl = max(base_sl * 0.7, avg_range * atr_mult)
                    dyn_tp = dyn_sl * rr
                    if c <= w_low + w_range * band and imb >= imb_th: signal = 'BUY'
                    elif c >= w_high - w_range * band and imb <= -imb_th: signal = 'SELL'
                elif method_name == 'METHOD_12B_KELLY_PLUS_SMART_DOM_EXIT':
                    dyn_sl = max(base_sl * 0.7, avg_range * atr_mult)
                    dyn_tp = dyn_sl * rr
                    if c <= w_low + w_range * band and imb >= imb_th: signal = 'BUY'
                    elif c >= w_high - w_range * band and imb <= -imb_th: signal = 'SELL'
                elif method_name == 'METHOD_12C_KELLY_TRAILING_LOCK':
                    dyn_sl = max(base_sl * 0.7, avg_range * atr_mult)
                    dyn_tp = dyn_sl * 3.2
                    if c <= w_low + w_range * band and imb >= imb_th: signal = 'BUY'
                    elif c >= w_high - w_range * band and imb <= -imb_th: signal = 'SELL'
                elif method_name == 'METHOD_12D_KELLY_EXTREME_BAND_10':
                    dyn_sl = max(base_sl * 0.7, avg_range * 1.8)
                    dyn_tp = dyn_sl * 2.6
                    if c <= w_low + w_range * 0.10 and imb >= 0.035: signal = 'BUY'
                    elif c >= w_high - w_range * 0.10 and imb <= -0.035: signal = 'SELL'

            # =================================================================
            # MODULE 13: ROUGH VOL (Rough Heston Fractal Kernel H < 0.5)
            # =================================================================
            elif engine_id == 'ENGINE_13_ROUGH_VOL':
                hurst = method_params.get('hurst_h', 0.35)
                env_mult = method_params.get('envelope_mult', 0.55)
                rough_env = avg_range * (lookback ** hurst)
                imb_th = 0.02 * method_params.get('imb_scale', 1.0)
                
                if method_name == 'METHOD_13A_FIXED_HURST_KERNEL':
                    if c <= (w_high + w_low) / 2.0 - rough_env * env_mult and imb >= imb_th: signal = 'BUY'
                    elif c >= (w_high + w_low) / 2.0 + rough_env * env_mult and imb <= -imb_th: signal = 'SELL'
                elif method_name == 'METHOD_13B_DUAL_MEMORY_KERNEL':
                    rough_env_fast = avg_range * (5 ** hurst)
                    rough_env_slow = avg_range * (25 ** hurst)
                    if c <= (w_high + w_low) / 2.0 - (rough_env_fast + rough_env_slow) * 0.35 and imb >= imb_th: signal = 'BUY'
                    elif c >= (w_high + w_low) / 2.0 + (rough_env_fast + rough_env_slow) * 0.35 and imb <= -imb_th: signal = 'SELL'
                elif method_name == 'METHOD_13C_ROUGH_SNAPBACK_ASYMMETRIC':
                    if c <= (w_high + w_low) / 2.0 - rough_env * 0.60 and imb >= 0.025: signal = 'BUY'
                    elif c >= (w_high + w_low) / 2.0 + rough_env * 0.60 and imb <= -0.025: signal = 'SELL'
                elif method_name == 'METHOD_13D_ROUGH_VOL_TRAILING_EXIT':
                    if c <= (w_high + w_low) / 2.0 - rough_env * env_mult and imb >= imb_th: signal = 'BUY'
                    elif c >= (w_high + w_low) / 2.0 + rough_env * env_mult and imb <= -imb_th: signal = 'SELL'
                if signal:
                    dyn_sl = rough_env * 0.7
                    dyn_tp = rough_env * 1.8

            # =================================================================
            # MODULE 14: MASTER PIPELINE (5-Tier Ensemble Orchestrator)
            # =================================================================
            elif engine_id == 'ENGINE_14_MASTER_PIPELINE':
                is_news = (h - l) > avg_range * method_params.get('news_gate', 1.6)
                if not is_news:
                    is_trending = (h - l) > avg_range * method_params.get('trend_vol', 1.5)
                    if method_name == 'METHOD_14A_STANDARD_5TIER':
                        if is_trending:
                            if kalman_vel > avg_range * 0.2 and hawkes_intensity > 1.9:
                                signal = 'BUY'; dyn_sl = avg_range * 1.5; dyn_tp = avg_range * 3.0
                            elif kalman_vel < -avg_range * 0.2 and hawkes_intensity > 1.9:
                                signal = 'SELL'; dyn_sl = avg_range * 1.5; dyn_tp = avg_range * 3.0
                        else:
                            if (c <= w_low + w_range * 0.15 and imb >= 0.03) or (c <= w_low + w_range * 0.12 and delta > 45):
                                signal = 'BUY'; dyn_sl = 25.0; dyn_tp = 75.0
                            elif (c >= w_high - w_range * 0.15 and imb <= -0.03) or (c >= w_high - w_range * 0.12 and delta < -45):
                                signal = 'SELL'; dyn_sl = 25.0; dyn_tp = 75.0
                    elif method_name == 'METHOD_14B_TOP_ALPHA_TRIO_ENSEMBLE':
                        # Gated Voting between top 3 champions: Kelly (12) + Rough Vol (13) + DeepLOB (01)
                        vote_buy = 0; vote_sell = 0
                        # 1. Kelly
                        if c <= w_low + w_range * 0.15 and imb >= 0.02: vote_buy += 1
                        elif c >= w_high - w_range * 0.15 and imb <= -0.02: vote_sell += 1
                        # 2. Rough Vol
                        rough_env = avg_range * (lookback ** 0.35)
                        if c <= (w_high + w_low) / 2.0 - rough_env * 0.5: vote_buy += 1
                        elif c >= (w_high + w_low) / 2.0 + rough_env * 0.5: vote_sell += 1
                        # 3. Lead Lag Delta
                        if delta > 30: vote_buy += 1
                        elif delta < -30: vote_sell += 1
                        
                        if vote_buy >= 2:
                            signal = 'BUY'; dyn_sl = avg_range * 2.0; dyn_tp = dyn_sl * 2.8
                        elif vote_sell >= 2:
                            signal = 'SELL'; dyn_sl = avg_range * 2.0; dyn_tp = dyn_sl * 2.8
                    elif method_name == 'METHOD_14C_ENSEMBLE_DYNAMIC_ATR_KELLY':
                        # Master Pipeline using dynamic Kelly Risk allocation
                        if not is_trending:
                            if c <= w_low + w_range * 0.15 and imb >= 0.025:
                                signal = 'BUY'; dyn_sl = avg_range * 2.0; dyn_tp = dyn_sl * 2.8
                            elif c >= w_high - w_range * 0.15 and imb <= -0.025:
                                signal = 'SELL'; dyn_sl = avg_range * 2.0; dyn_tp = dyn_sl * 2.8
                    elif method_name == 'METHOD_14D_ENSEMBLE_TRAILING_SMART_EXIT':
                        if (c <= w_low + w_range * 0.15 and imb >= 0.025):
                            signal = 'BUY'; dyn_sl = avg_range * 2.0; dyn_tp = dyn_sl * 3.0
                        elif (c >= w_high - w_range * 0.15 and imb <= -0.025):
                            signal = 'SELL'; dyn_sl = avg_range * 2.0; dyn_tp = dyn_sl * 3.0

            if signal:
                pos = {
                    'side': signal, 'entry_p': c, 'idx': i,
                    'sl': c - dyn_sl if signal == 'BUY' else c + dyn_sl,
                    'tp': c + dyn_tp if signal == 'BUY' else c - dyn_tp
                }
                inventory_q += (1 if signal == 'BUY' else -1)
                
    tot = len(trades)
    if tot == 0:
        return {
            'engine': engine_id,
            'method': method_name,
            'trades': 0,
            'wins': 0,
            'losses': 0,
            'win_rate': 0.0,
            'gross_profit': 0.0,
            'gross_loss': 0.0,
            'net_pnl': 0.0,
            'profit_factor': 0.0,
            'max_dd': 0.0,
            'avg_trade': 0.0,
            'score': 0.0
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
        
    score = round((net_pnl / max_dd) * math.sqrt(wr / 100.0), 2) if max_dd > 0 else 0.0
    
    return {
        'engine': engine_id,
        'method': method_name,
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
        'score': score
    }

def run_all_methods_testbench():
    print("=" * 115)
    print("        COMPREHENSIVE BACKTEST OF ALL DISCOVERED MAX-PROFIT METHODS ACROSS ALL 13 ENGINES")
    print("=" * 115)
    
    asset_cfg = {
        'point_val': 0.01,
        'spread_cost': 0.16,
        'comm': 0.0
    }
    
    data = load_market_data('BTCUSD')
    if not data:
        print("Failed to load BTCUSD data.")
        return
        
    modules_methods = {
        'ENGINE_01_DEEPLOB': [
            ('METHOD_1A_STANDARD_WALL', {'lookback': 15, 'range_tol': 0.15, 'imb_thresh': 0.02, 'sl_dist': 45.0, 'rr_ratio': 2.6}),
            ('METHOD_1B_SMART_DOM_EXIT', {'lookback': 15, 'range_tol': 0.15, 'imb_thresh': 0.02, 'sl_dist': 45.0, 'rr_ratio': 2.6, 'use_smart_dom_exit': True}),
            ('METHOD_1C_EXTREME_DEPTH_ABSORPTION', {'lookback': 20, 'sl_dist': 35.0, 'rr_ratio': 2.8}),
            ('METHOD_1D_DUAL_CONFIRM_DELTA', {'lookback': 15, 'range_tol': 0.15, 'imb_thresh': 0.02, 'sl_dist': 45.0, 'rr_ratio': 2.6})
        ],
        'ENGINE_02_OFI_IMPACT': [
            ('METHOD_2A_RAW_OFI_FLOW', {'sl_dist': 35.0, 'rr_ratio': 2.0}),
            ('METHOD_2B_Z_SCORE_NORMALIZED', {'z_thresh': 2.2, 'sl_dist': 25.0, 'rr_ratio': 2.5}),
            ('METHOD_2C_OFI_ACCELERATION', {'z_thresh': 1.8, 'sl_dist': 30.0, 'rr_ratio': 2.5}),
            ('METHOD_2D_OFI_IMBALANCE_HYBRID', {'z_thresh': 1.6, 'sl_dist': 25.0, 'rr_ratio': 2.5})
        ],
        'ENGINE_03_AVELLANEDA_MM': [
            ('METHOD_3A_STANDARD_QUOTE', {'gamma': 0.05, 'spread_factor': 0.6}),
            ('METHOD_3B_WIDE_VOLATILITY_BAND', {'gamma': 0.05, 'spread_factor': 1.0}),
            ('METHOD_3C_STRICT_INVENTORY_LIMIT_1', {'gamma': 0.03, 'spread_factor': 0.8}),
            ('METHOD_3D_TREND_VETO_CHOP_ONLY', {'gamma': 0.05, 'spread_factor': 0.7})
        ],
        'ENGINE_04_VWAP_SLICER': [
            ('METHOD_4A_FIXED_SD_FADE', {'sd_band': 1.5, 'sl_dist': 35.0}),
            ('METHOD_4B_VWAP_PLUS_BOOK_CONFIRM', {'sd_band': 1.5, 'sl_dist': 35.0}),
            ('METHOD_4C_FLAT_VWAP_SLOPE', {'sd_band': 1.5, 'sl_dist': 35.0}),
            ('METHOD_4D_MICRO_TIME_HOLD_25', {'sd_band': 1.5, 'sl_dist': 35.0, 'max_hold': 25})
        ],
        'ENGINE_05_HAWKES_BURST': [
            ('METHOD_5A_TICK_BURST', {'intensity_thresh': 2.0, 'sl_dist': 35.0, 'rr_ratio': 2.0}),
            ('METHOD_5B_HIGH_DELTA_BURST', {'intensity_thresh': 2.2, 'delta_thresh': 40.0, 'sl_dist': 35.0, 'rr_ratio': 2.5}),
            ('METHOD_5C_EXPANSION_REGIME_BURST', {'delta_thresh': 30.0, 'sl_dist': 45.0, 'rr_ratio': 2.8}),
            ('METHOD_5D_BURST_TRAILING_RUNNER', {'intensity_thresh': 2.0, 'delta_thresh': 35.0, 'sl_dist': 35.0, 'use_trailing_stop': True})
        ],
        'ENGINE_06_GOLD_INTRADAY': [
            ('METHOD_6A_NY_OPEN_BREAKOUT', {'sl_dist': 45.0, 'rr_ratio': 2.5}),
            ('METHOD_6B_ACTIVE_OVERLAP_WINDOW', {'sl_dist': 45.0, 'rr_ratio': 2.5}),
            ('METHOD_6C_AUCTION_VALUE_FADE', {'sl_dist': 35.0, 'rr_ratio': 2.0}),
            ('METHOD_6D_SESSION_TRAILING_60M', {'sl_dist': 45.0, 'use_trailing_stop': True, 'max_hold': 60})
        ],
        'ENGINE_07_HMM_REGIME': [
            ('METHOD_7A_DUAL_ROUTER', {'vol_expansion_ratio': 1.8, 'sl_dist': 45.0, 'rr_ratio': 2.0}),
            ('METHOD_7B_TREND_ONLY_STATE', {'vol_expansion_ratio': 1.5, 'sl_dist': 45.0, 'rr_ratio': 2.5}),
            ('METHOD_7C_CHOP_ONLY_STATE', {'vol_expansion_ratio': 1.5, 'sl_dist': 40.0, 'rr_ratio': 2.0}),
            ('METHOD_7D_PROBABILITY_WEIGHTED', {'sl_dist': 45.0, 'rr_ratio': 2.2})
        ],
        'ENGINE_08_LEAD_LAG': [
            ('METHOD_8A_EXTREME_DELTA_EXHAUSTION', {'delta_exhaust_thresh': 55.0, 'extreme_band': 0.06, 'sl_dist': 25.0, 'rr_ratio': 2.5}),
            ('METHOD_8B_CVD_PRICE_DIVERGENCE', {'sl_dist': 30.0, 'rr_ratio': 2.5}),
            ('METHOD_8C_DELTA_SLOPE_REVERSAL', {'extreme_band': 0.08, 'sl_dist': 25.0, 'rr_ratio': 2.2}),
            ('METHOD_8D_LEAD_LAG_TRAILING_TARGET', {'delta_exhaust_thresh': 50.0, 'extreme_band': 0.06, 'sl_dist': 25.0, 'use_trailing_stop': True})
        ],
        'ENGINE_09_KALMAN_ZEROLAG': [
            ('METHOD_9A_ZERO_CROSSING', {'sl_dist': 35.0, 'rr_ratio': 2.0}),
            ('METHOD_9B_VELOCITY_HURDLE_FILTER', {'v_thresh': 0.25, 'sl_dist': 35.0, 'rr_ratio': 2.5}),
            ('METHOD_9C_ACCELERATION_CONFIRM', {'sl_dist': 35.0, 'rr_ratio': 2.5}),
            ('METHOD_9D_ZERO_LAG_RUNNER', {'v_thresh': 0.25, 'sl_dist': 35.0, 'use_trailing_stop': True})
        ],
        'ENGINE_10_DIFFUSION_SIM': [
            ('METHOD_10A_DRIFT_BARRIER', {'drift_hurdle': 0.04, 'band_pct': 0.18, 'imb_thresh': 0.025, 'sl_dist': 35.0, 'tp_dist': 70.0}),
            ('METHOD_10B_PROBABILITY_HURDLE_65', {'imb_thresh': 0.02, 'sl_dist': 35.0, 'tp_dist': 70.0}),
            ('METHOD_10C_LOCAL_VOL_ADAPTIVE', {'imb_thresh': 0.02, 'sl_dist': 35.0, 'tp_dist': 70.0}),
            ('METHOD_10D_BARRIER_OPTIMAL_STOP', {'drift_hurdle': 0.03, 'imb_thresh': 0.02, 'sl_dist': 35.0, 'tp_dist': 70.0})
        ],
        'ENGINE_11_NEWS_GATE': [
            ('METHOD_11A_RANGE_SPIKE_GATE', {'atr_gate_ratio': 1.8, 'fade_band': 0.08, 'imb_thresh': 0.02, 'sl_dist': 35.0, 'rr_ratio': 2.5}),
            ('METHOD_11B_SPREAD_TO_ATR_GATE', {'fade_band': 0.08, 'imb_thresh': 0.02, 'sl_dist': 35.0, 'rr_ratio': 2.5}),
            ('METHOD_11C_POST_NEWS_ABSORPTION', {'sl_dist': 35.0, 'rr_ratio': 2.5}),
            ('METHOD_11D_NEWS_GATE_SMART_EXIT', {'atr_gate_ratio': 1.8, 'fade_band': 0.08, 'imb_thresh': 0.02, 'sl_dist': 35.0, 'rr_ratio': 2.5, 'use_smart_dom_exit': True})
        ],
        'ENGINE_12_KELLY_SIZING': [
            ('METHOD_12A_ASYMMETRIC_KELLY_2_8', {'atr_sl_mult': 2.0, 'rr_ratio': 2.8, 'imb_thresh': 0.03, 'range_pct': 0.15}),
            ('METHOD_12B_KELLY_PLUS_SMART_DOM_EXIT', {'atr_sl_mult': 2.0, 'rr_ratio': 2.8, 'imb_thresh': 0.03, 'range_pct': 0.15, 'use_smart_dom_exit': True}),
            ('METHOD_12C_KELLY_TRAILING_LOCK', {'atr_sl_mult': 2.0, 'imb_thresh': 0.03, 'range_pct': 0.15, 'use_trailing_stop': True}),
            ('METHOD_12D_KELLY_EXTREME_BAND_10', {'imb_thresh': 0.035})
        ],
        'ENGINE_13_ROUGH_VOL': [
            ('METHOD_13A_FIXED_HURST_KERNEL', {'hurst_h': 0.35, 'envelope_mult': 0.55, 'imb_scale': 1.0}),
            ('METHOD_13B_DUAL_MEMORY_KERNEL', {'hurst_h': 0.35, 'imb_scale': 1.0}),
            ('METHOD_13C_ROUGH_SNAPBACK_ASYMMETRIC', {'hurst_h': 0.35}),
            ('METHOD_13D_ROUGH_VOL_TRAILING_EXIT', {'hurst_h': 0.35, 'envelope_mult': 0.55, 'use_trailing_stop': True})
        ],
        'ENGINE_14_MASTER_PIPELINE': [
            ('METHOD_14A_STANDARD_5TIER', {'news_gate': 1.6, 'trend_vol': 1.5}),
            ('METHOD_14B_TOP_ALPHA_TRIO_ENSEMBLE', {'news_gate': 1.6}),
            ('METHOD_14C_ENSEMBLE_DYNAMIC_ATR_KELLY', {'news_gate': 1.6, 'trend_vol': 1.4}),
            ('METHOD_14D_ENSEMBLE_TRAILING_SMART_EXIT', {'news_gate': 1.6, 'use_trailing_stop': True, 'use_smart_dom_exit': True})
        ]
    }
    
    results = {}
    
    for eng_id, methods in modules_methods.items():
        print(f"\n>>> Module: {eng_id} ({len(methods)} Discovered Methods)...")
        print(f"{'Method Name':42s} | {'Trades':6s} | {'Win Rate':8s} | {'Net PnL ($)':11s} | {'PF':5s} | {'Max DD':8s} | {'Score':6s}")
        print("-" * 98)
        
        results[eng_id] = []
        best_method = None
        best_score = -9999.0
        
        for m_name, m_params in methods:
            res = run_backtest_method(data, eng_id, m_name, m_params, asset_cfg)
            results[eng_id].append(res)
            
            pnl_str = f"${res['net_pnl']:+9.2f}"
            print(f"{res['method']:42s} | {res['trades']:6d} | {res['win_rate']:7.1f}% | {pnl_str:11s} | {res['profit_factor']:5.2f} | ${res['max_dd']:7.2f} | {res['score']:+6.2f}")
            
            if res['score'] > best_score:
                best_score = res['score']
                best_method = res
                
        if best_method:
            print(f"  🏆 MAX PROFIT CHAMPION: {best_method['method']} (PnL: ${best_method['net_pnl']:+.2f}, PF: {best_method['profit_factor']})")

    # Save to JSON
    out_file = r"d:\cbot-atgvt\data\all_modules_max_profit_backtest.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\nAll methods backtest completed! Results saved to: {out_file}")

if __name__ == '__main__':
    run_all_methods_testbench()
