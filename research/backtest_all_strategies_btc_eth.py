"""
Unified Comprehensive Backtest of All Known Strategies on Live BTCUSD and ETHUSD Data
--------------------------------------------------------------------------------------
Evaluates:
1. All 14 Quant Modules (56 distinct algorithmic methods from 141 arXiv papers)
2. All 4 Core cTrader Automate Production Bots (DOM_ABSORPTION, VWAP_SCALP, NY_VALUE, CVD_DIVERGENCE)
3. Strategy A (Extreme Deviation Reversal)

Datasets:
- BTCUSD: 1,770 continuous live M1 bars + Order Flow + DOM Imbalance
- ETHUSD: 1,769 continuous live M1 bars + Order Flow + DOM Imbalance
"""

import os
import sys
import math
import json

sys.stdout.reconfigure(encoding='utf-8')
sys.path.append(r'd:\cbot-atgvt\research')
from optimize_all_strategies import load_market_data

def evaluate_method(data, engine_id, method_name, method_params, asset_cfg):
    symbol = asset_cfg['symbol']
    spread_cost = asset_cfg['spread']
    price_unit = asset_cfg['price_unit']  # Base price scale for SL/TP
    delta_scale = asset_cfg['delta_scale'] # Multiplier for delta thresholds
    
    n = len(data)
    trades = []
    pos = None
    
    # State variables
    kalman_pos = data[0]['close']
    kalman_vel = 0.0
    hawkes_intensity = 1.0
    inventory_q = 0
    prev_bid = data[0]['close']
    prev_ask = data[0]['close'] + spread_cost
    last_exit_idx = -10
    ofi_history = []
    
    lookback = int(method_params.get('lookback', 20))
    max_hold = int(method_params.get('max_hold', 35))
    base_sl = float(method_params.get('sl_dist', 35.0)) / 35.0 * price_unit * 1.2
    base_tp = float(method_params.get('tp_dist', 70.0)) / 70.0 * price_unit * 2.8
    base_sl = max(base_sl, spread_cost * 1.5) # SL must be at least 1.5x spread
    base_tp = max(base_tp, spread_cost * 3.0) # TP must be at least 3.0x spread
    
    for i in range(lookback, n):
        d = data[i]
        c = d['close']
        h = d['high']
        l = d['low']
        o = d['open']
        imb = d['imbalance']
        delta = d['delta']
        cvd = d['cvd']
        spread = d['spread'] if d['spread'] > 0 else spread_cost
        ticks = d['ticks']
        
        window = data[i-lookback:i]
        w_high = max(x['high'] for x in window)
        w_low = min(x['low'] for x in window)
        w_range = max(w_high - w_low, 0.01 * price_unit)
        avg_range = sum(x['high'] - x['low'] for x in window) / lookback
        avg_range = max(avg_range, 0.01 * price_unit)
        
        # 1. Kalman Zero-Lag Filter
        kalman_err = c - kalman_pos
        kalman_pos += kalman_err * 0.45
        kalman_vel += kalman_err * 0.12
        kalman_pos += kalman_vel
        
        # 2. Hawkes Intensity
        decay = math.exp(-0.15)
        hawkes_intensity = 1.0 + (hawkes_intensity - 1.0) * decay + (0.5 if abs(c - o) > avg_range * 1.2 else 0.0)
        
        # 3. Order Flow Imbalance (OFI)
        current_bid = c
        current_ask = c + spread
        delta_w_bid = (current_bid - prev_bid)
        delta_w_ask = (current_ask - prev_ask)
        ofi_t = (ticks * (0.5 + imb)) * (1 if delta_w_bid >= 0 else -1) - (ticks * (0.5 - imb)) * (1 if delta_w_ask <= 0 else -1)
        ofi_history.append(ofi_t)
        prev_bid = current_bid
        prev_ask = current_ask
        
        # Manage open position
        if pos is not None:
            hold_time = i - pos['idx']
            pnl_gross = (c - pos['entry_p']) if pos['side'] == 'BUY' else (pos['entry_p'] - c)
            
            # Smart DOM Exit check
            hit_smart_dom = False
            if method_params.get('use_smart_dom_exit', False):
                if pnl_gross > 0.4 * (pos['tp'] - pos['entry_p'] if pos['side'] == 'BUY' else pos['entry_p'] - pos['tp']):
                    if pos['side'] == 'BUY' and imb <= -0.03: hit_smart_dom = True
                    elif pos['side'] == 'SELL' and imb >= 0.03: hit_smart_dom = True
                    
            # Trailing stop check
            if method_params.get('use_trailing_stop', False):
                trail_dist = avg_range * 1.3
                if pos['side'] == 'BUY':
                    pos['sl'] = max(pos['sl'], c - trail_dist)
                else:
                    pos['sl'] = min(pos['sl'], c + trail_dist)
            
            # Exit conditions
            is_sl = (l <= pos['sl']) if pos['side'] == 'BUY' else (h >= pos['sl'])
            is_tp = (h >= pos['tp']) if pos['side'] == 'BUY' else (l <= pos['tp'])
            is_time = hold_time >= max_hold
            
            if is_sl or is_tp or is_time or hit_smart_dom:
                exit_p = pos['sl'] if is_sl else (pos['tp'] if is_tp else c)
                raw_pnl = (exit_p - pos['entry_p']) if pos['side'] == 'BUY' else (pos['entry_p'] - exit_p)
                net_usd = (raw_pnl - spread) * asset_cfg['point_val']
                trades.append({
                    'entry_idx': pos['idx'], 'exit_idx': i,
                    'side': pos['side'], 'entry_p': pos['entry_p'], 'exit_p': exit_p,
                    'net_usd': net_usd, 'hold_time': hold_time,
                    'reason': 'SL' if is_sl else ('TP' if is_tp else ('DOM_EXIT' if hit_smart_dom else 'TIME'))
                })
                pos = None
                last_exit_idx = i
                continue
                
        # Signal Generation
        if pos is None and (i - last_exit_idx >= 2):
            signal = None
            dyn_sl = base_sl
            dyn_tp = base_tp
            
            # MODULE 01: DEEPLOB
            if engine_id == 'ENGINE_01_DEEPLOB':
                imb_th = method_params.get('imb_thresh', 0.02)
                rng_tol = method_params.get('range_tol', 0.15)
                if method_name == 'METHOD_1A_STANDARD_WALL':
                    if c <= w_low + w_range * rng_tol and imb >= imb_th: signal = 'BUY'
                    elif c >= w_high - w_range * rng_tol and imb <= -imb_th: signal = 'SELL'
                elif method_name == 'METHOD_1B_SMART_DOM_EXIT':
                    if c <= w_low + w_range * rng_tol and imb >= imb_th: signal = 'BUY'
                    elif c >= w_high - w_range * rng_tol and imb <= -imb_th: signal = 'SELL'
                elif method_name == 'METHOD_1C_EXTREME_DEPTH_ABSORPTION':
                    if c <= w_low + w_range * 0.10 and imb >= imb_th * 1.4: signal = 'BUY'
                    elif c >= w_high - w_range * 0.10 and imb <= -imb_th * 1.4: signal = 'SELL'
                elif method_name == 'METHOD_1D_DUAL_CONFIRM_DELTA':
                    if c <= w_low + w_range * rng_tol and imb >= imb_th and delta > 0: signal = 'BUY'
                    elif c >= w_high - w_range * rng_tol and imb <= -imb_th and delta < 0: signal = 'SELL'
                if signal:
                    dyn_sl = max(price_unit * 1.2, spread * 1.6)
                    dyn_tp = dyn_sl * method_params.get('rr_ratio', 2.6)

            # MODULE 02: OFI IMPACT
            elif engine_id == 'ENGINE_02_OFI_IMPACT':
                if len(ofi_history) >= 20:
                    ofi_win = ofi_history[-20:]
                    m_ofi = sum(ofi_win) / len(ofi_win)
                    s_ofi = math.sqrt(sum((x - m_ofi) ** 2 for x in ofi_win) / len(ofi_win)) or 1.0
                    z_ofi = (ofi_t - m_ofi) / s_ofi
                    z_th = method_params.get('z_thresh', 1.8)
                    ofi_cut = 35.0 * delta_scale
                    if method_name == 'METHOD_2A_RAW_OFI_FLOW':
                        if ofi_t > ofi_cut and cvd > 0: signal = 'BUY'
                        elif ofi_t < -ofi_cut and cvd < 0: signal = 'SELL'
                    elif method_name == 'METHOD_2B_Z_SCORE_NORMALIZED':
                        if z_ofi > z_th: signal = 'BUY'
                        elif z_ofi < -z_th: signal = 'SELL'
                    elif method_name == 'METHOD_2C_OFI_ACCELERATION':
                        z_prev = (ofi_win[-2] - m_ofi) / s_ofi if len(ofi_win) >= 2 else 0
                        if z_ofi > z_th and z_ofi > z_prev: signal = 'BUY'
                        elif z_ofi < -z_th and z_ofi < z_prev: signal = 'SELL'
                    elif method_name == 'METHOD_2D_OFI_IMBALANCE_HYBRID':
                        if z_ofi > z_th * 0.8 and imb > 0.015: signal = 'BUY'
                        elif z_ofi < -z_th * 0.8 and imb < -0.015: signal = 'SELL'
                    if signal:
                        dyn_sl = max(price_unit * 1.1, spread * 1.5)
                        dyn_tp = dyn_sl * method_params.get('rr_ratio', 2.5)

            # MODULE 03: AVELLANEDA MARKET MAKING
            elif engine_id == 'ENGINE_03_AVELLANEDA_MM':
                gamma = method_params.get('gamma', 0.05)
                s_factor = method_params.get('spread_factor', 0.7)
                half_spread = avg_range * s_factor
                res_p = c - inventory_q * gamma * (avg_range ** 2)
                if method_name == 'METHOD_3A_STANDARD_QUOTE':
                    if c <= res_p - half_spread: signal = 'BUY'
                    elif c >= res_p + half_spread: signal = 'SELL'
                elif method_name == 'METHOD_3B_WIDE_VOLATILITY_BAND':
                    if c <= res_p - half_spread * 1.3: signal = 'BUY'
                    elif c >= res_p + half_spread * 1.3: signal = 'SELL'
                elif method_name == 'METHOD_3C_STRICT_INVENTORY_LIMIT_1':
                    if abs(inventory_q) < 1:
                        if c <= res_p - half_spread: signal = 'BUY'
                        elif c >= res_p + half_spread: signal = 'SELL'
                elif method_name == 'METHOD_3D_TREND_VETO_CHOP_ONLY':
                    if (h - l) <= avg_range * 1.2:
                        if c <= res_p - half_spread: signal = 'BUY'
                        elif c >= res_p + half_spread: signal = 'SELL'
                if signal:
                    dyn_sl = max(avg_range * 1.6, spread * 1.6)
                    dyn_tp = max(avg_range * 2.2, spread * 2.5)

            # MODULE 04: VWAP SLICER
            elif engine_id == 'ENGINE_04_VWAP_SLICER':
                vwap = d['vwap'] if d['vwap'] > 0 else (c - avg_range)
                sd = d['sd'] if d['sd'] > 0 else avg_range
                sd_mult = method_params.get('sd_band', 1.4)
                upper = vwap + sd * sd_mult
                lower = vwap - sd * sd_mult
                if method_name in ['METHOD_4A_FIXED_SD_FADE', 'METHOD_4D_MICRO_TIME_HOLD_25']:
                    if c <= lower and imb >= 0.01: signal = 'BUY'
                    elif c >= upper and imb <= -0.01: signal = 'SELL'
                elif method_name == 'METHOD_4B_VWAP_PLUS_BOOK_CONFIRM':
                    if c <= lower and imb >= 0.02: signal = 'BUY'
                    elif c >= upper and imb <= -0.02: signal = 'SELL'
                elif method_name == 'METHOD_4C_FLAT_VWAP_SLOPE':
                    v_diff = abs(d['vwap'] - data[i-5]['vwap']) if i >= 5 and data[i-5]['vwap'] > 0 else 0
                    if v_diff < avg_range * 0.35:
                        if c <= lower and imb >= 0.015: signal = 'BUY'
                        elif c >= upper and imb <= -0.015: signal = 'SELL'
                if signal:
                    dyn_sl = max(price_unit * 1.2, spread * 1.6)
                    dyn_tp = max(abs(c - vwap) * 1.3, spread * 2.5)

            # MODULE 05: HAWKES BURST
            elif engine_id == 'ENGINE_05_HAWKES_BURST':
                int_th = method_params.get('intensity_thresh', 1.8)
                del_th = method_params.get('delta_thresh', 25.0) * delta_scale
                if method_name == 'METHOD_5A_TICK_BURST':
                    if hawkes_intensity >= int_th:
                        if delta > 10 * delta_scale: signal = 'BUY'
                        elif delta < -10 * delta_scale: signal = 'SELL'
                elif method_name in ['METHOD_5B_HIGH_DELTA_BURST', 'METHOD_5D_BURST_TRAILING_RUNNER']:
                    if hawkes_intensity >= int_th and abs(delta) >= del_th:
                        if delta > 0 and cvd > 0: signal = 'BUY'
                        elif delta < 0 and cvd < 0: signal = 'SELL'
                elif method_name == 'METHOD_5C_EXPANSION_REGIME_BURST':
                    if (h - l) > avg_range * 1.25 and hawkes_intensity >= 1.8:
                        if delta > del_th: signal = 'BUY'
                        elif delta < -del_th: signal = 'SELL'
                if signal:
                    dyn_sl = max(price_unit * 1.2, spread * 1.6)
                    dyn_tp = dyn_sl * method_params.get('rr_ratio', 2.5)

            # MODULE 06: INTRADAY AUCTION
            elif engine_id == 'ENGINE_06_GOLD_INTRADAY':
                h_utc = int(d['time'].split(' ')[1].split(':')[0]) if ' ' in d['time'] else 0
                if method_name == 'METHOD_6A_NY_OPEN_BREAKOUT':
                    if h_utc in [13, 14, 15, 16]:
                        if c >= w_high - w_range * 0.06 and delta > 0: signal = 'BUY'
                        elif c <= w_low + w_range * 0.06 and delta < 0: signal = 'SELL'
                elif method_name in ['METHOD_6B_ACTIVE_OVERLAP_WINDOW', 'METHOD_6D_SESSION_TRAILING_60M']:
                    if h_utc in [7, 8, 13, 14, 15, 16]:
                        if c >= w_high - w_range * 0.05 and delta > 0: signal = 'BUY'
                        elif c <= w_low + w_range * 0.05 and delta < 0: signal = 'SELL'
                elif method_name == 'METHOD_6C_AUCTION_VALUE_FADE':
                    vah = d['vah'] if d['vah'] > 0 else d['prev_vah']
                    val = d['val'] if d['val'] > 0 else d['prev_val']
                    if vah > 0 and val > 0:
                        if c >= vah and imb <= -0.015: signal = 'SELL'
                        elif c <= val and imb >= 0.015: signal = 'BUY'
                if signal:
                    dyn_sl = max(price_unit * 1.3, spread * 1.6)
                    dyn_tp = dyn_sl * method_params.get('rr_ratio', 2.5)

            # MODULE 07: HMM REGIME SWITCHER
            elif engine_id == 'ENGINE_07_HMM_REGIME':
                vol_exp = method_params.get('vol_expansion_ratio', 1.6)
                is_trending = (h - l) > avg_range * vol_exp
                if method_name == 'METHOD_7A_DUAL_ROUTER':
                    if is_trending:
                        if kalman_vel > avg_range * 0.22: signal = 'BUY'
                        elif kalman_vel < -avg_range * 0.22: signal = 'SELL'
                    else:
                        if c <= w_low + w_range * 0.10 and imb >= 0.018: signal = 'BUY'
                        elif c >= w_high - w_range * 0.10 and imb <= -0.018: signal = 'SELL'
                elif method_name == 'METHOD_7B_TREND_ONLY_STATE':
                    if is_trending:
                        if kalman_vel > avg_range * 0.20: signal = 'BUY'
                        elif kalman_vel < -avg_range * 0.20: signal = 'SELL'
                elif method_name == 'METHOD_7C_CHOP_ONLY_STATE':
                    if not is_trending:
                        if c <= w_low + w_range * 0.10 and imb >= 0.02: signal = 'BUY'
                        elif c >= w_high - w_range * 0.10 and imb <= -0.02: signal = 'SELL'
                elif method_name == 'METHOD_7D_PROBABILITY_WEIGHTED':
                    prob_trend = min(max(((h - l) / avg_range) - 1.0, 0.0), 1.0)
                    if prob_trend > 0.55:
                        if kalman_vel > 0: signal = 'BUY'
                        else: signal = 'SELL'
                    elif prob_trend < 0.35:
                        if c <= w_low + w_range * 0.12 and imb >= 0.018: signal = 'BUY'
                        elif c >= w_high - w_range * 0.12 and imb <= -0.018: signal = 'SELL'
                if signal:
                    dyn_sl = max(price_unit * 1.3, spread * 1.6)
                    dyn_tp = dyn_sl * method_params.get('rr_ratio', 2.4)

            # MODULE 08: LEAD-LAG CVD
            elif engine_id == 'ENGINE_08_LEAD_LAG':
                del_th = method_params.get('delta_exhaust_thresh', 40.0) * delta_scale
                band = method_params.get('extreme_band', 0.08)
                if method_name in ['METHOD_8A_EXTREME_DELTA_EXHAUSTION', 'METHOD_8D_LEAD_LAG_TRAILING_TARGET']:
                    if c >= w_high - w_range * band and delta < -del_th: signal = 'SELL'
                    elif c <= w_low + w_range * band and delta > del_th: signal = 'BUY'
                elif method_name == 'METHOD_8B_CVD_PRICE_DIVERGENCE':
                    if c >= w_high - w_range * 0.10 and cvd < 0 and delta < -12 * delta_scale: signal = 'SELL'
                    elif c <= w_low + w_range * 0.10 and cvd > 0 and delta > 12 * delta_scale: signal = 'BUY'
                elif method_name == 'METHOD_8C_DELTA_SLOPE_REVERSAL':
                    d_del = delta - data[i-1]['delta']
                    if c >= w_high - w_range * band and d_del < -18 * delta_scale: signal = 'SELL'
                    elif c <= w_low + w_range * band and d_del > 18 * delta_scale: signal = 'BUY'
                if signal:
                    dyn_sl = max(price_unit * 1.1, spread * 1.6)
                    dyn_tp = dyn_sl * method_params.get('rr_ratio', 2.5)

            # MODULE 09: KALMAN ZERO-LAG
            elif engine_id == 'ENGINE_09_KALMAN_ZEROLAG':
                v_th = method_params.get('v_thresh', 0.22) * avg_range
                if method_name == 'METHOD_9A_ZERO_CROSSING':
                    if kalman_vel > 0 and data[i-1].get('k_vel', 0) <= 0: signal = 'BUY'
                    elif kalman_vel < 0 and data[i-1].get('k_vel', 0) >= 0: signal = 'SELL'
                elif method_name in ['METHOD_9B_VELOCITY_HURDLE_FILTER', 'METHOD_9D_ZERO_LAG_RUNNER']:
                    if kalman_vel > v_th: signal = 'BUY'
                    elif kalman_vel < -v_th: signal = 'SELL'
                elif method_name == 'METHOD_9C_ACCELERATION_CONFIRM':
                    k_accel = kalman_vel - data[i-1].get('k_vel', 0)
                    if kalman_vel > 0 and k_accel > 0: signal = 'BUY'
                    elif kalman_vel < 0 and k_accel < 0: signal = 'SELL'
                d['k_vel'] = kalman_vel
                if signal:
                    dyn_sl = max(price_unit * 1.2, spread * 1.6)
                    dyn_tp = dyn_sl * method_params.get('rr_ratio', 2.4)

            # MODULE 10: DIFFUSION SIMULATION
            elif engine_id == 'ENGINE_10_DIFFUSION_SIM':
                drift = (c - data[i-5]['close']) / 5.0 if i >= 5 else 0
                drift_h = method_params.get('drift_hurdle', 0.035) * avg_range
                imb_th = method_params.get('imb_thresh', 0.018)
                if method_name in ['METHOD_10A_DRIFT_BARRIER', 'METHOD_10D_BARRIER_OPTIMAL_STOP']:
                    if drift > drift_h and imb >= imb_th: signal = 'BUY'
                    elif drift < -drift_h and imb <= -imb_th: signal = 'SELL'
                elif method_name == 'METHOD_10B_PROBABILITY_HURDLE_65':
                    p_up = 0.5 + (drift / (avg_range * 2.0))
                    if p_up >= 0.62 and imb >= imb_th: signal = 'BUY'
                    elif p_up <= 0.38 and imb <= -imb_th: signal = 'SELL'
                elif method_name == 'METHOD_10C_LOCAL_VOL_ADAPTIVE':
                    if drift > avg_range * 0.04 and imb >= imb_th: signal = 'BUY'
                    elif drift < -avg_range * 0.04 and imb <= -imb_th: signal = 'SELL'
                if signal:
                    dyn_sl = max(price_unit * 1.2, spread * 1.6)
                    dyn_tp = dyn_sl * 2.4

            # MODULE 11: NEWS GATE & SPREAD DEFENSE
            elif engine_id == 'ENGINE_11_NEWS_GATE':
                gate_ratio = method_params.get('atr_gate_ratio', 1.7)
                is_news_bar = (h - l) > avg_range * gate_ratio
                band = method_params.get('fade_band', 0.10)
                imb_th = method_params.get('imb_thresh', 0.018)
                if not is_news_bar:
                    if method_name in ['METHOD_11A_RANGE_SPIKE_GATE', 'METHOD_11D_NEWS_GATE_SMART_EXIT']:
                        if c <= w_low + w_range * band and imb >= imb_th: signal = 'BUY'
                        elif c >= w_high - w_range * band and imb <= -imb_th: signal = 'SELL'
                    elif method_name == 'METHOD_11B_SPREAD_TO_ATR_GATE':
                        if spread < avg_range * 0.85: # Allow realistic spread on crypto
                            if c <= w_low + w_range * band and imb >= imb_th: signal = 'BUY'
                            elif c >= w_high - w_range * band and imb <= -imb_th: signal = 'SELL'
                    elif method_name == 'METHOD_11C_POST_NEWS_ABSORPTION':
                        was_news = any((x['high'] - x['low']) > avg_range * 1.6 for x in window[-3:])
                        if was_news:
                            if c <= w_low + w_range * band and imb >= imb_th: signal = 'BUY'
                            elif c >= w_high - w_range * band and imb <= -imb_th: signal = 'SELL'
                if signal:
                    dyn_sl = max(price_unit * 1.2, spread * 1.6)
                    dyn_tp = dyn_sl * method_params.get('rr_ratio', 2.6)

            # MODULE 12: KELLY SIZING & ASYMMETRIC RR
            elif engine_id == 'ENGINE_12_KELLY_SIZING':
                atr_mult = method_params.get('atr_mult', 1.5)
                rr = method_params.get('rr_ratio', 2.8)
                band = method_params.get('extreme_band', 0.15)
                imb_th = method_params.get('imb_thresh', 0.018)
                dyn_sl = max(price_unit * 1.3, avg_range * atr_mult, spread * 1.6)
                dyn_tp = dyn_sl * rr
                if method_name in ['METHOD_12A_DYNAMIC_ATR_KELLY', 'METHOD_12B_ASYMMETRIC_KELLY_2_8', 'METHOD_12C_KELLY_TRAILING_LOCK', 'METHOD_12D_KELLY_EXTREME_BAND_10']:
                    if c <= w_low + w_range * band and imb >= imb_th: signal = 'BUY'
                    elif c >= w_high - w_range * band and imb <= -imb_th: signal = 'SELL'

            # MODULE 13: ROUGH VOLATILITY
            elif engine_id == 'ENGINE_13_ROUGH_VOL':
                hurst = method_params.get('hurst_h', 0.35)
                env_mult = method_params.get('envelope_mult', 0.50)
                rough_env = avg_range * (lookback ** hurst)
                imb_th = 0.018 * method_params.get('imb_scale', 1.0)
                if method_name in ['METHOD_13A_FIXED_HURST_KERNEL', 'METHOD_13D_ROUGH_VOL_TRAILING_EXIT']:
                    if c <= (w_high + w_low) / 2.0 - rough_env * env_mult and imb >= imb_th: signal = 'BUY'
                    elif c >= (w_high + w_low) / 2.0 + rough_env * env_mult and imb <= -imb_th: signal = 'SELL'
                elif method_name == 'METHOD_13B_DUAL_MEMORY_KERNEL':
                    r_fast = avg_range * (5 ** hurst); r_slow = avg_range * (25 ** hurst)
                    if c <= (w_high + w_low) / 2.0 - (r_fast + r_slow) * 0.32 and imb >= imb_th: signal = 'BUY'
                    elif c >= (w_high + w_low) / 2.0 + (r_fast + r_slow) * 0.32 and imb <= -imb_th: signal = 'SELL'
                elif method_name == 'METHOD_13C_ROUGH_SNAPBACK_ASYMMETRIC':
                    if c <= (w_high + w_low) / 2.0 - rough_env * 0.55 and imb >= 0.02: signal = 'BUY'
                    elif c >= (w_high + w_low) / 2.0 + rough_env * 0.55 and imb <= -0.02: signal = 'SELL'
                if signal:
                    dyn_sl = max(rough_env * 0.8, spread * 1.6)
                    dyn_tp = max(rough_env * 2.2, spread * 3.0)

            # MODULE 14: MASTER PIPELINE
            elif engine_id == 'ENGINE_14_MASTER_PIPELINE':
                is_news = (h - l) > avg_range * 1.6
                if not is_news:
                    is_trending = (h - l) > avg_range * 1.4
                    if method_name == 'METHOD_14A_STANDARD_5TIER':
                        if is_trending:
                            if kalman_vel > avg_range * 0.2 and hawkes_intensity > 1.8:
                                signal = 'BUY'; dyn_sl = max(avg_range * 1.6, spread * 1.6); dyn_tp = dyn_sl * 2.6
                            elif kalman_vel < -avg_range * 0.2 and hawkes_intensity > 1.8:
                                signal = 'SELL'; dyn_sl = max(avg_range * 1.6, spread * 1.6); dyn_tp = dyn_sl * 2.6
                        else:
                            if (c <= w_low + w_range * 0.15 and imb >= 0.025) or (c <= w_low + w_range * 0.12 and delta > 20 * delta_scale):
                                signal = 'BUY'; dyn_sl = max(price_unit * 1.2, spread * 1.6); dyn_tp = dyn_sl * 2.6
                            elif (c >= w_high - w_range * 0.15 and imb <= -0.025) or (c >= w_high - w_range * 0.12 and delta < -20 * delta_scale):
                                signal = 'SELL'; dyn_sl = max(price_unit * 1.2, spread * 1.6); dyn_tp = dyn_sl * 2.6
                    elif method_name in ['METHOD_14B_TOP_ALPHA_TRIO_ENSEMBLE', 'METHOD_14C_ENSEMBLE_DYNAMIC_ATR_KELLY', 'METHOD_14D_ENSEMBLE_TRAILING_SMART_EXIT']:
                        vote_buy = 0; vote_sell = 0
                        if c <= w_low + w_range * 0.15 and imb >= 0.018: vote_buy += 1
                        elif c >= w_high - w_range * 0.15 and imb <= -0.018: vote_sell += 1
                        rough_env = avg_range * (lookback ** 0.35)
                        if c <= (w_high + w_low) / 2.0 - rough_env * 0.45: vote_buy += 1
                        elif c >= (w_high + w_low) / 2.0 + rough_env * 0.45: vote_sell += 1
                        if delta > 15 * delta_scale: vote_buy += 1
                        elif delta < -15 * delta_scale: vote_sell += 1
                        if vote_buy >= 2:
                            signal = 'BUY'; dyn_sl = max(avg_range * 1.6, spread * 1.6); dyn_tp = dyn_sl * 2.8
                        elif vote_sell >= 2:
                            signal = 'SELL'; dyn_sl = max(avg_range * 1.6, spread * 1.6); dyn_tp = dyn_sl * 2.8

            # CORE BOT: DOM_ABSORPTION (Production cTrader Strategy)
            elif engine_id == 'CORE_BOT_DOM_ABSORPTION':
                wall_imb = 0.022
                if c <= w_low + w_range * 0.15 and imb >= wall_imb: signal = 'BUY'
                elif c >= w_high - w_range * 0.15 and imb <= -wall_imb: signal = 'SELL'
                if signal:
                    dyn_sl = max(price_unit * 1.2, spread * 1.6)
                    dyn_tp = dyn_sl * 2.2

            # CORE BOT: MID_RANGE_VWAP_SCALP
            elif engine_id == 'CORE_BOT_MID_RANGE_VWAP':
                vwap = d['vwap'] if d['vwap'] > 0 else c
                if c <= vwap - avg_range * 1.1: signal = 'BUY'
                elif c >= vwap + avg_range * 1.1: signal = 'SELL'
                if signal:
                    dyn_sl = max(avg_range * 1.5, spread * 1.6)
                    dyn_tp = max(avg_range * 2.4, spread * 2.5)

            # CORE BOT: NY_VALUE_AREA
            elif engine_id == 'CORE_BOT_NY_VALUE':
                vah = d['vah'] if d['vah'] > 0 else d['prev_vah']
                val = d['val'] if d['val'] > 0 else d['prev_val']
                if vah > 0 and val > 0:
                    if c > vah and delta > 10 * delta_scale: signal = 'BUY'
                    elif c < val and delta < -10 * delta_scale: signal = 'SELL'
                if signal:
                    dyn_sl = max(avg_range * 1.6, spread * 1.6)
                    dyn_tp = max(avg_range * 2.8, spread * 2.8)

            # CORE BOT: CVD_DELTA_DIVERGENCE
            elif engine_id == 'CORE_BOT_CVD_DIVERGENCE':
                if c >= w_high - w_range * 0.08 and cvd < 0: signal = 'SELL'
                elif c <= w_low + w_range * 0.08 and cvd > 0: signal = 'BUY'
                if signal:
                    dyn_sl = max(price_unit * 1.2, spread * 1.6)
                    dyn_tp = dyn_sl * 2.4

            # STRATEGY A: EXTREME_DEVIATION_REVERSAL
            elif engine_id == 'STRATEGY_A_EXTREME_REVERSAL':
                vwap = d['vwap'] if d['vwap'] > 0 else c
                sd = d['sd'] if d['sd'] > 0 else avg_range
                is_news = (h - l) > avg_range * 2.0
                if not is_news and sd > 0:
                    z = (c - vwap) / sd
                    if z <= -3.0: signal = 'BUY'
                    elif z >= 3.0: signal = 'SELL'
                if signal:
                    dyn_sl = max(avg_range * 1.8, spread * 1.6)
                    dyn_tp = max(abs(c - vwap), spread * 2.5) # Exit at VWAP Touch

            if signal:
                pos = {
                    'side': signal, 'entry_p': c, 'idx': i,
                    'sl': c - dyn_sl if signal == 'BUY' else c + dyn_sl,
                    'tp': c + dyn_tp if signal == 'BUY' else c - dyn_tp
                }
                inventory_q += (1 if signal == 'BUY' else -1)

            # CORE BOT: NY_VALUE_AREA
            elif engine_id == 'CORE_BOT_NY_VALUE':
                vah = d['vah'] if d['vah'] > 0 else d['prev_vah']
                val = d['val'] if d['val'] > 0 else d['prev_val']
                if vah > 0 and val > 0:
                    if c > vah and delta > 15: signal = 'BUY'
                    elif c < val and delta < -15: signal = 'SELL'
                if signal:
                    dyn_sl = avg_range * 1.8
                    dyn_tp = avg_range * 3.0

            # CORE BOT: CVD_DELTA_DIVERGENCE
            elif engine_id == 'CORE_BOT_CVD_DIVERGENCE':
                if c >= w_high - w_range * 0.08 and cvd < 0: signal = 'SELL'
                elif c <= w_low + w_range * 0.08 and cvd > 0: signal = 'BUY'
                if signal:
                    dyn_sl = 30.0 * point_scale
                    dyn_tp = 65.0 * point_scale

            # STRATEGY A: EXTREME_DEVIATION_REVERSAL
            elif engine_id == 'STRATEGY_A_EXTREME_REVERSAL':
                vwap = d['vwap'] if d['vwap'] > 0 else c
                sd = d['sd'] if d['sd'] > 0 else avg_range
                is_news = (h - l) > avg_range * 2.0
                if not is_news and sd > 0:
                    z = (c - vwap) / sd
                    if z <= -3.8: signal = 'BUY'
                    elif z >= 3.8: signal = 'SELL'
                if signal:
                    dyn_sl = avg_range * 2.0
                    dyn_tp = abs(c - vwap) # Exit at VWAP Touch

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
            'engine': engine_id, 'method': method_name, 'symbol': symbol,
            'trades': 0, 'win_rate': 0.0, 'net_pnl': 0.0, 'profit_factor': 0.0,
            'max_dd': 0.0, 'avg_trade': 0.0, 'score': 0.0
        }
        
    wins = [t for t in trades if t['net_usd'] > 0]
    losses = [t for t in trades if t['net_usd'] <= 0]
    wr = len(wins) / tot * 100.0
    gross_win = sum(t['net_usd'] for t in wins)
    gross_loss = abs(sum(t['net_usd'] for t in losses))
    net_pnl = gross_win - gross_loss
    pf = round(gross_win / gross_loss, 2) if gross_loss > 0 else (99.0 if gross_win > 0 else 0.0)
    
    # Calculate Max Drawdown
    equity = 0.0
    peak = 0.0
    max_dd = 0.0
    for t in trades:
        equity += t['net_usd']
        if equity > peak: peak = equity
        dd = peak - equity
        if dd > max_dd: max_dd = dd
        
    score = round((net_pnl / max_dd) * math.sqrt(wr / 100.0), 2) if max_dd > 0 else 0.0
    
    return {
        'engine': engine_id,
        'method': method_name,
        'symbol': symbol,
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

def main():
    print("=" * 110)
    print("   TESTING ALL STRATEGIES ON LIVE BTCUSD & ETHUSD DATASETS (1,770 BARS EACH)")
    print("=" * 110)
    
    assets = {
        'BTCUSD': {
            'symbol': 'BTCUSD',
            'spread': 16.0,        # $16 spread on BTC
            'point_val': 0.01,     # $0.01 per point per 0.01 lot
            'price_unit': 40.0,    # 1 ATR unit (~$40)
            'delta_scale': 1.0     # Reference delta scale
        },
        'ETHUSD': {
            'symbol': 'ETHUSD',
            'spread': 2.05,        # $2.05 spread on ETH
            'point_val': 0.01,     # $0.01 per point per 0.01 lot
            'price_unit': 2.6,     # 1 ATR unit (~$2.6)
            'delta_scale': 0.35    # ETH volume/delta scale
        }
    }
    
    # Define all strategy modules and methods
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
            ('METHOD_12A_DYNAMIC_ATR_KELLY', {'atr_mult': 1.5, 'rr_ratio': 2.5, 'extreme_band': 0.15, 'imb_thresh': 0.02}),
            ('METHOD_12B_ASYMMETRIC_KELLY_2_8', {'atr_mult': 1.5, 'rr_ratio': 2.8, 'extreme_band': 0.15, 'imb_thresh': 0.02}),
            ('METHOD_12C_KELLY_TRAILING_LOCK', {'atr_mult': 1.5, 'rr_ratio': 3.2, 'extreme_band': 0.15, 'imb_thresh': 0.02, 'use_trailing_stop': True}),
            ('METHOD_12D_KELLY_EXTREME_BAND_10', {'atr_mult': 1.8, 'rr_ratio': 2.6, 'extreme_band': 0.10, 'imb_thresh': 0.035})
        ],
        'ENGINE_13_ROUGH_VOL': [
            ('METHOD_13A_FIXED_HURST_KERNEL', {'hurst_h': 0.35, 'envelope_mult': 0.55}),
            ('METHOD_13B_DUAL_MEMORY_KERNEL', {'hurst_h': 0.35}),
            ('METHOD_13C_ROUGH_SNAPBACK_ASYMMETRIC', {'hurst_h': 0.35}),
            ('METHOD_13D_ROUGH_VOL_TRAILING_EXIT', {'hurst_h': 0.35, 'envelope_mult': 0.55, 'use_trailing_stop': True})
        ],
        'ENGINE_14_MASTER_PIPELINE': [
            ('METHOD_14A_STANDARD_5TIER', {'trend_vol': 1.5, 'news_gate': 1.6}),
            ('METHOD_14B_TOP_ALPHA_TRIO_ENSEMBLE', {}),
            ('METHOD_14C_ENSEMBLE_DYNAMIC_ATR_KELLY', {}),
            ('METHOD_14D_ENSEMBLE_TRAILING_SMART_EXIT', {'use_trailing_stop': True})
        ],
        'CORE_PROD_ROBOTS': [
            ('CORE_BOT_DOM_ABSORPTION', {}),
            ('CORE_BOT_MID_RANGE_VWAP', {}),
            ('CORE_BOT_NY_VALUE', {}),
            ('CORE_BOT_CVD_DIVERGENCE', {})
        ],
        'STRATEGY_A_REVERSAL': [
            ('STRATEGY_A_EXTREME_REVERSAL', {})
        ]
    }
    
    all_results = {}
    
    for sym, cfg in assets.items():
        data = load_market_data(sym)
        if not data:
            print(f"Failed to load data for {sym}")
            continue
            
        print(f"\n>>> Running Backtest on {sym} ({len(data)} continuous live bars, spread={cfg['spread']})...")
        sym_results = []
        
        for mod_name, methods in modules_methods.items():
            for m_name, m_params in methods:
                eng_id = mod_name if not mod_name.startswith('CORE_') and not mod_name.startswith('STRATEGY_') else m_name
                res = evaluate_method(data, eng_id, m_name, m_params, cfg)
                sym_results.append(res)
                
        # Sort by Net PnL descending
        sym_results.sort(key=lambda x: (x['net_pnl'], x['profit_factor']), reverse=True)
        all_results[sym] = sym_results
        
        print(f"\n--- TOP 10 STRATEGIES ON {sym} ---")
        print(f"{'Method / Engine':38s} | {'Trades':6s} | {'Win Rate':8s} | {'Net PnL ($)':11s} | {'PF':5s} | {'Max DD ($)':10s} | {'Score':6s}")
        print("-" * 95)
        for r in sym_results[:10]:
            print(f"{r['method']:38s} | {r['trades']:6d} | {r['win_rate']:7.1f}% | {r['net_pnl']:+10.2f} | {r['profit_factor']:5.2f} | {r['max_dd']:10.2f} | {r['score']:6.2f}")
            
    # Save results to json
    out_json = r"d:\cbot-atgvt\data\btc_eth_all_strategies_backtest.json"
    with open(out_json, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    print(f"\nSaved complete results to: {out_json}")

if __name__ == '__main__':
    main()
