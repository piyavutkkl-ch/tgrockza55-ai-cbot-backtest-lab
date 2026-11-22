"""
Two-Tier Causal Event Tokenizer & MTF Context Projector (Step 4)
================================================================
Converts raw continuous price/volume/microstructure & DynamicLevelMemory arrays into:
1. 42 Atomic M1 Events:
   - 24 Structural Milestones (Tier A)
   - 18 Microstructure & Momentum Modifiers (Tier B, with strict L2 DOM / Flow / Spread gating)
2. HTF Context & MTF Setup Tokens (m5, m15, h1, h4) + Causal Developing HTF flags.

Supports `jitter_scale` (e.g. 0.85, 1.0, 1.15) for +-15% parameter stability testing.
"""

from __future__ import annotations

from typing import Any, Dict

import numpy as np


def _shift_true(arr: np.ndarray, k: int) -> np.ndarray:
    out = np.zeros_like(arr, dtype=bool)
    if k < len(arr):
        out[k:] = arr[:-k]
    return out


def tokenize_m1_events(
    dataset: Dict[str, Any],
    level_struct: Dict[str, np.ndarray],
    jitter_scale: float = 1.0,
) -> Dict[str, Dict[str, Any]]:
    """Builds 42 strictly causal M1 atomic event masks and metadata."""
    m1 = dataset["m1"]
    spec = dataset["spec"]
    n = int(m1["n"])
    if n == 0:
        return {}

    op = m1["open"]
    hi = m1["high"]
    lo = m1["low"]
    cl = m1["close"]
    atr = np.maximum(m1["atr14"], 1e-9)
    atr60 = np.maximum(m1["atr60_mean"], 1e-9)
    rng = np.maximum(hi - lo, 1e-9)
    body = np.abs(cl - op)

    bull_candle = cl > op
    bear_candle = cl < op

    live_ok = m1["has_l2_dom"] & m1["has_real_spread"] & m1["has_order_flow"]
    dom_ok = m1["has_l2_dom"] & m1["has_real_spread"]

    imb = np.nan_to_num(m1["imbalance"], nan=0.0)
    delta = np.nan_to_num(m1["delta"], nan=0.0)
    imb_z = np.nan_to_num(m1["imb_z_session"], nan=0.0)
    delta_z = np.nan_to_num(m1["delta_z_session"], nan=0.0)
    spread_z = np.nan_to_num(m1["spread_z_session"], nan=0.0)
    vol_z = np.nan_to_num(m1["vol_z_session"], nan=0.0)
    cvd_s5 = np.nan_to_num(m1["cvd_slope5"], nan=0.0)
    px_s5 = np.nan_to_num(m1["price_slope5"], nan=0.0)
    accel = np.nan_to_num(m1["accel_atr"], nan=0.0)
    vwap_z = np.nan_to_num(m1["vwap_z"], nan=0.0)
    rsi = m1["rsi14"]
    u_wick = m1["upper_wick_ratio"]
    l_wick = m1["lower_wick_ratio"]
    r_atr = m1["range_atr"]
    hh20 = m1["prev_hh20"]
    ll20 = m1["prev_ll20"]

    js = float(jitter_scale)
    events: Dict[str, Dict[str, Any]] = {}

    def _add(
        name: str,
        mask: np.ndarray,
        tier: str,
        category: str,
        default_dir: str,
        requires_micro: bool,
        anchor: np.ndarray,
        desc: str,
    ) -> None:
        m_clean = np.asarray(mask, dtype=bool)
        if requires_micro:
            m_clean = m_clean & dom_ok
        events[name] = {
            "name": name,
            "mask": m_clean,
            "anchor": np.asarray(anchor, dtype=np.float64),
            "tier": tier,  # MILESTONE | MODIFIER
            "category": category,
            "default_dir": default_dir,  # BUY | SELL | AUTO
            "requires_microstructure": requires_micro,
            "desc": desc,
        }

    # --- TIER A: 24 STRUCTURAL MILESTONES ---
    abull = level_struct["anchor_bull"]
    abear = level_struct["anchor_bear"]

    _add("SWEEP_LOW", level_struct["sweep_low"], "MILESTONE", "Liquidity", "BUY", False, abull, "ไส้เทียนแทงทะลุแนวรับ/Low แล้วปิดกลับเหนือแนว")
    _add("SWEEP_HIGH", level_struct["sweep_high"], "MILESTONE", "Liquidity", "SELL", False, abear, "ไส้เทียนแทงทะลุแนวต้าน/High แล้วปิดกลับต่ำกว่าแนว")
    _add("FALSE_BREAKOUT_UP", level_struct["false_breakout_up"], "MILESTONE", "Liquidity", "SELL", False, abear, "ปิดทะลุแนวต้านก่อนถูกตบกลับเข้ากรอบใน 1–3 แท่ง")
    _add("FALSE_BREAKOUT_DOWN", level_struct["false_breakout_down"], "MILESTONE", "Liquidity", "BUY", False, abull, "ปิดหลุดแนวรับก่อนถูกดึงกลับเข้ากรอบใน 1–3 แท่ง")
    _add("RECLAIM_LOW", level_struct["reclaim_low"], "MILESTONE", "Liquidity", "BUY", False, abull, "แท่งเทียนปิดยึดเหนือระดับที่ถูก Sweep/หลุด ลงไปได้")
    _add("RECLAIM_HIGH", level_struct["reclaim_high"], "MILESTONE", "Liquidity", "SELL", False, abear, "แท่งเทียนปิดกดต่ำกว่าระดับที่ถูก Sweep/ทะลุ ขึ้นไปได้")
    _add("RETEST_SUPPORT_2X", level_struct["retest_support_2x"], "MILESTONE", "Liquidity", "BUY", False, abull, "ราคากลับมาทดสอบแนวรับเดิมซ้ำ >=2 ครั้งแล้วเด้งกลับ")
    _add("RETEST_RESIST_2X", level_struct["retest_resist_2x"], "MILESTONE", "Liquidity", "SELL", False, abear, "ราคากลับมาทดสอบแนวต้านเดิมซ้ำ >=2 ครั้งแล้วถูกปฏิเสธ")
    _add("BOS_BULL", level_struct["bos_bull"], "MILESTONE", "Market Structure", "BUY", False, abull, "ปิดแท่งทะลุ Swing High ต่อเนื่องตามโครงสร้างขาขึ้น")
    _add("BOS_BEAR", level_struct["bos_bear"], "MILESTONE", "Market Structure", "SELL", False, abear, "ปิดแท่งหลุด Swing Low ต่อเนื่องตามโครงสร้างขาลง")
    _add("CHOCH_BULL", level_struct["choch_bull"], "MILESTONE", "Market Structure", "BUY", False, abull, "เปลี่ยนโครงสร้าง (CHoCH) ทะลุ Swing High หลังเป็นขาลง")
    _add("CHOCH_BEAR", level_struct["choch_bear"], "MILESTONE", "Market Structure", "SELL", False, abear, "เปลี่ยนโครงสร้าง (CHoCH) หลุด Swing Low หลังเป็นขาขึ้น")
    _add("HIGHER_LOW", level_struct["higher_low"], "MILESTONE", "Market Structure", "BUY", False, abull, "ยืนยันจุดต่ำสุดยกสูงขึ้น (Higher Low Pivot Confirmed)")
    _add("LOWER_HIGH", level_struct["lower_high"], "MILESTONE", "Market Structure", "SELL", False, abear, "ยืนยันจุดสูงสุดลดต่ำลง (Lower High Pivot Confirmed)")

    disp_bull = bull_candle & (body >= 1.1 * js * atr) & (((cl - lo) / rng) >= 0.72)
    disp_bear = bear_candle & (body >= 1.1 * js * atr) & (((hi - cl) / rng) >= 0.72)
    _add("DISPLACEMENT_BULL", disp_bull, "MILESTONE", "Price Action", "BUY", False, op, "แท่ง Impulse ขาขึ้นเนื้อเทียนแข็งแรง >=1.1 ATR")
    _add("DISPLACEMENT_BEAR", disp_bear, "MILESTONE", "Price Action", "SELL", False, op, "แท่ง Impulse ขาลงเนื้อเทียนแข็งแรง >=1.1 ATR")

    brk_up = bull_candle & (cl > hh20 + 0.10 * js * atr)
    brk_dn = bear_candle & (cl < ll20 - 0.10 * js * atr)
    brk_up[0] = False
    brk_dn[0] = False
    _add("BREAKOUT_UP", brk_up, "MILESTONE", "Price Action", "BUY", False, hh20, "ราคาปิดเบรก High รอบ 20 แท่งขึ้นไป")
    _add("BREAKOUT_DOWN", brk_dn, "MILESTONE", "Price Action", "SELL", False, ll20, "ราคาปิดเบรก Low รอบ 20 แท่งลงมา")

    comp = (atr < 0.72 * js * atr60) & (r_atr < 0.85 * js)
    expn = r_atr >= 1.60 * js
    _add("COMPRESSION", comp, "MILESTONE", "Volatility", "AUTO", False, cl, "ความผันผวนหดตัวแคบ (ATR14 < 0.72x ค่าเฉลี่ย 60 แท่ง)")
    _add("EXPANSION", expn, "MILESTONE", "Volatility", "AUTO", False, op, "แท่งเทียนขยายตัวแรง >= 1.60 ATR")

    rej_bull = (l_wick >= min(0.85, 0.55 * js)) & (r_atr >= 0.80 * js)
    rej_bear = (u_wick >= min(0.85, 0.55 * js)) & (r_atr >= 0.80 * js)
    _add("REJECTION_BULL", rej_bull, "MILESTONE", "Price Action", "BUY", False, lo, "แท่งเทียนทิ้งไส้ล่างยาวปฏิเสธแรงขาย >=55%")
    _add("REJECTION_BEAR", rej_bear, "MILESTONE", "Price Action", "SELL", False, hi, "แท่งเทียนทิ้งไส้บนยาวปฏิเสธแรงซื้อ >=55%")

    prev3_bull = _shift_true(bull_candle, 1) & _shift_true(bull_candle, 2) & _shift_true(bull_candle, 3)
    prev3_bear = _shift_true(bear_candle, 1) & _shift_true(bear_candle, 2) & _shift_true(bear_candle, 3)
    exh_top = prev3_bull & (u_wick >= 0.35 * js) & ((rsi >= 65.0) | (vwap_z >= 1.5 * js))
    exh_bot = prev3_bear & (l_wick >= 0.35 * js) & ((rsi <= 35.0) | (vwap_z <= -1.5 * js))
    _add("EXHAUSTION_TOP", exh_top, "MILESTONE", "Momentum", "SELL", False, hi, "แรงซื้อปลายคลื่นเริ่มแผ่ว (3 แท่งเขียว + ไส้บน + Overbought)")
    _add("EXHAUSTION_BOT", exh_bot, "MILESTONE", "Momentum", "BUY", False, lo, "แรงขายปลายคลื่นเริ่มแผ่ว (3 แท่งแดง + ไส้ล่าง + Oversold)")

    # --- TIER B: 18 MICROSTRUCTURE & MOMENTUM MODIFIERS ---
    dom_abs_buy = live_ok & (imb_z >= 1.2 * js) & ((delta < 0) | (cl >= op)) & (l_wick >= 0.25)
    dom_abs_sell = live_ok & (imb_z <= -1.2 * js) & ((delta > 0) | (cl <= op)) & (u_wick >= 0.25)
    _add("DOM_ABSORPTION_BUY", dom_abs_buy, "MODIFIER", "Microstructure", "BUY", True, lo, "Bid Wall L2 ดูดซับแรงขายพร้อมไส้รับ (Live DOM + Order Flow)")
    _add("DOM_ABSORPTION_SELL", dom_abs_sell, "MODIFIER", "Microstructure", "SELL", True, hi, "Ask Wall L2 ดูดซับแรงซื้อพร้อมไส้ต้าน (Live DOM + Order Flow)")

    imb_th = float(spec["imb_th"])
    _add("DOM_IMBALANCE_BULL", dom_ok & (imb_z >= 1.5 * js) & (imb > imb_th), "MODIFIER", "Microstructure", "BUY", True, lo, "ความไม่สมดุล Bid L2 สูงผิดปกติเทียบ Session เดียวกัน")
    _add("DOM_IMBALANCE_BEAR", dom_ok & (imb_z <= -1.5 * js) & (imb < -imb_th), "MODIFIER", "Microstructure", "SELL", True, hi, "ความไม่สมดุล Ask L2 สูงผิดปกติเทียบ Session เดียวกัน")

    div_bull = live_ok & (px_s5 < -0.30 * js) & (cvd_s5 > 0.0) & (delta_z >= 0.8 * js)
    div_bear = live_ok & (px_s5 > 0.30 * js) & (cvd_s5 < 0.0) & (delta_z <= -0.8 * js)
    _add("DELTA_DIVERGENCE_BULL", div_bull, "MODIFIER", "Microstructure", "BUY", True, lo, "ราคาทำ Low ต่ำลงแต่ CVD/Delta สวนขึ้น (Absorption Divergence)")
    _add("DELTA_DIVERGENCE_BEAR", div_bear, "MODIFIER", "Microstructure", "SELL", True, hi, "ราคาดัน High สูงขึ้นแต่ CVD/Delta ไหลลง (Distribution Divergence)")

    _add("CVD_SURGE_BULL", live_ok & (delta_z >= 1.8 * js), "MODIFIER", "Microstructure", "BUY", True, lo, "Order Flow Delta พุ่งฝั่งซื้อ >+1.8 Z-Score ของ Session")
    _add("CVD_SURGE_BEAR", live_ok & (delta_z <= -1.8 * js), "MODIFIER", "Microstructure", "SELL", True, hi, "Order Flow Delta พุ่งฝั่งขาย <-1.8 Z-Score ของ Session")
    _add("SPREAD_EXPANSION", dom_ok & (spread_z >= 1.8 * js), "MODIFIER", "Microstructure", "AUTO", True, cl, "สเปรดจริงถ่างตัว >+1.8 Z-Score ของ Session")

    _add("VOL_SPIKE_SESSION", vol_z >= 1.8 * js, "MODIFIER", "Volume", "AUTO", False, cl, "Tick Volume พุ่ง >+1.8 Z-Score เมื่อเทียบกับ Session เดียวกัน")
    _add("VWAP_EXTREME_HIGH", vwap_z >= 2.0 * js, "MODIFIER", "VWAP", "SELL", False, hi, "ราคาวิ่งห่างเหนือ VWAP วัน >= +2.0 SD")
    _add("VWAP_EXTREME_LOW", vwap_z <= -2.0 * js, "MODIFIER", "VWAP", "BUY", False, lo, "ราคาวิ่งห่างต่ำกว่า VWAP วัน <= -2.0 SD")

    _add("RSI_OVERBOUGHT", rsi >= min(95.0, 70.0 + 3.0 * (js - 1.0)), "MODIFIER", "Momentum", "SELL", False, hi, "RSI(14) อยู่ในเขต Overbought")
    _add("RSI_OVERSOLD", rsi <= max(5.0, 30.0 - 3.0 * (js - 1.0)), "MODIFIER", "Momentum", "BUY", False, lo, "RSI(14) อยู่ในเขต Oversold")
    _add("PRICE_ACCEL_UP", accel >= 0.9 * js, "MODIFIER", "Momentum", "BUY", False, op, "ความเร่งราคาขาขึ้นฉับพลัน >= +0.9 ATR")
    _add("PRICE_ACCEL_DOWN", accel <= -0.9 * js, "MODIFIER", "Momentum", "SELL", False, op, "ความเร่งราคาขาลงฉับพลัน <= -0.9 ATR")

    c4_bull = bull_candle & _shift_true(bull_candle, 1) & _shift_true(bull_candle, 2) & _shift_true(bull_candle, 3)
    c4_bear = bear_candle & _shift_true(bear_candle, 1) & _shift_true(bear_candle, 2) & _shift_true(bear_candle, 3)
    _add("CONSEC_BULL_RUN", c4_bull, "MODIFIER", "Price Action", "BUY", False, cl, "ปิดบวกต่อเนื่อง 4 แท่งติดกัน")
    _add("CONSEC_BEAR_RUN", c4_bear, "MODIFIER", "Price Action", "SELL", False, cl, "ปิดลบต่อเนื่อง 4 แท่งติดกัน")

    # --- TIER C (ROUND 2): 15 DEEP ORDER BOOK MICROSTRUCTURE & AUCTION EVENTS ---
    imb_delta = np.nan_to_num(m1["imb_z_delta"], nan=0.0)
    lasym_z = np.nan_to_num(m1["ladder_asym_z_session"], nan=0.0)
    depth_z = np.nan_to_num(m1["depth_z_session"], nan=0.0)
    bvol_z = np.nan_to_num(m1["book_vol_z_session"], nan=0.0)
    sp_ratio = np.nan_to_num(m1["spread_spike_ratio"], nan=1.0)

    poc_raw = m1["poc"]
    vah_raw = m1["vah"]
    val_raw = m1["val"]
    poc_valid = np.isfinite(poc_raw) & (poc_raw > 0)
    vah_valid = np.isfinite(vah_raw) & (vah_raw > 0)
    val_valid = np.isfinite(val_raw) & (val_raw > 0)
    poc_arr = np.nan_to_num(poc_raw, nan=0.0)
    vah_arr = np.nan_to_num(vah_raw, nan=0.0)
    val_arr = np.nan_to_num(val_raw, nan=0.0)
    poc_safe = np.where(poc_valid, poc_arr, cl)
    vah_safe = np.where(vah_valid, vah_arr, hi)
    val_safe = np.where(val_valid, val_arr, lo)

    # 1-2. Order Book Imbalance Flip (rapid Ask-heavy -> Bid-heavy reversal, or vice versa)
    dom_flip_bull = dom_ok & (_shift_true(imb_z <= -0.6 * js, 1) | _shift_true(imb_z <= -0.6 * js, 2)) & (imb_z >= 0.8 * js) & (imb_delta >= 1.5 * js)
    dom_flip_bear = dom_ok & (_shift_true(imb_z >= 0.6 * js, 1) | _shift_true(imb_z >= 0.6 * js, 2)) & (imb_z <= -0.8 * js) & (imb_delta <= -1.5 * js)
    _add("DOM_FLIP_BULL", dom_flip_bull, "MODIFIER", "Microstructure", "BUY", True, lo, "L2 Order Book พลิกฝั่งฉับพลันจาก Ask-heavy -> Bid-heavy (DOM Flip Bull)")
    _add("DOM_FLIP_BEAR", dom_flip_bear, "MODIFIER", "Microstructure", "SELL", True, hi, "L2 Order Book พลิกฝั่งฉับพลันจาก Bid-heavy -> Ask-heavy (DOM Flip Bear)")

    # 3-4. Multi-bar L2 DOM Stacking (3 consecutive bars biased >= +-0.75 Z)
    stack_b_bar = dom_ok & (imb_z >= 0.75 * js)
    stack_s_bar = dom_ok & (imb_z <= -0.75 * js)
    _add("DOM_STACK_BULL", stack_b_bar & _shift_true(stack_b_bar, 1) & _shift_true(stack_b_bar, 2), "MODIFIER", "Microstructure", "BUY", True, lo, "L2 Bid Stacking กดดันฝั่งซื้อต่อเนื่อง 3 นาทีซ้อน")
    _add("DOM_STACK_BEAR", stack_s_bar & _shift_true(stack_s_bar, 1) & _shift_true(stack_s_bar, 2), "MODIFIER", "Microstructure", "SELL", True, hi, "L2 Ask Stacking กดดันฝั่งขายต่อเนื่อง 3 นาทีซ้อน")

    # 5-6. 25-Level Liquidity Ladder Asymmetry (Thin Ask / Bid vacuum)
    _add("LADDER_THIN_ASK", live_ok & (lasym_z >= 1.4 * js), "MODIFIER", "Microstructure", "BUY", True, lo, "สเปกตรัม L2 Ladder ฝั่ง Ask บางผิดปกติ (ทางโล่งฝั่งขึ้น)")
    _add("LADDER_THIN_BID", live_ok & (lasym_z <= -1.4 * js), "MODIFIER", "Microstructure", "SELL", True, hi, "สเปกตรัม L2 Ladder ฝั่ง Bid บางผิดปกติ (ทางโล่งฝั่งลง)")

    # 7. Depth Iceberg Battle (high L2 quote churn inside tight price candle)
    _add("DEPTH_ICEBERG_BATTLE", dom_ok & (depth_z >= 1.3 * js) & (r_atr <= 0.95 / max(js, 0.5)), "MILESTONE", "Microstructure", "AUTO", True, cl, "เกิดการชนกำแพงคำสั่ง L2 หนาแน่น (Depth Churn สูงแต่ราคาไม่ขยับ)")

    # 8. Liquidity Pull Shock (book depth dries up while intra-bar spread spikes)
    _add("LIQUIDITY_PULL_SHOCK", dom_ok & (bvol_z <= -1.3 * js) & (sp_ratio >= 1.45 * js), "MILESTONE", "Microstructure", "AUTO", True, cl, "ผู้ดูแลสภาพคล่องถอน Bid/Ask L2 ออกกะทันหันพร้อม Spread ถ่าง")

    # 9. Spread Snapback (spread recovers sharply within 1-3 bars after intra-bar blowout)
    blowout = dom_ok & ((spread_z >= 1.4 * js) | (sp_ratio >= 1.50 * js))
    recent_blowout_1_3 = _shift_true(blowout, 1) | _shift_true(blowout, 2) | _shift_true(blowout, 3)
    _add("SPREAD_SNAPBACK", dom_ok & recent_blowout_1_3 & (spread_z <= 0.45) & (sp_ratio <= 1.30), "MILESTONE", "Microstructure", "AUTO", True, cl, "Spread หดกลับเข้าสู่ภาวะปกติหลังพึ่งถ่างตัว (LP Liquidity Returned)")

    # 10-11. Native Flow CSV Sweep Flags Confirmed by Order Flow / Imbalance
    _add("FLOW_SWEEP_LOW", live_ok & m1["live_sweep_low"] & ((delta_z >= 0.0) | (imb_z >= 0.5 * js)), "MILESTONE", "Microstructure", "BUY", True, lo, "Sweep ระดับสำคัญด้านล่าง (RL/PL/AL) พร้อมแรงรับ Delta/Imbalance")
    _add("FLOW_SWEEP_HIGH", live_ok & m1["live_sweep_high"] & ((delta_z <= 0.0) | (imb_z <= -0.5 * js)), "MILESTONE", "Microstructure", "SELL", True, hi, "Sweep ระดับสำคัญด้านบน (RH/PH/AH) พร้อมแรงต้าน Delta/Imbalance")

    # 12-15. Auction Market Live Value Area (VAH/VAL/POC) Reclaims & Rejections
    _add("VA_REJECT_VAL", live_ok & val_valid & (lo < val_arr - 0.05 * js * atr) & (cl > val_arr), "MILESTONE", "VWAP", "BUY", True, val_safe, "ราคาแทงทะลุ Value Area Low (VAL) แล้วดึงปิดกลับเข้ากรอบมูลค่า")
    _add("VA_REJECT_VAH", live_ok & vah_valid & (hi > vah_arr + 0.05 * js * atr) & (cl < vah_arr), "MILESTONE", "VWAP", "SELL", True, vah_safe, "ราคาแทงทะลุ Value Area High (VAH) แล้วถูกตบปิดกลับเข้ากรอบมูลค่า")

    prev_below_poc = _shift_true(poc_valid & (cl < poc_arr), 1)
    prev_above_poc = _shift_true(poc_valid & (cl > poc_arr), 1)
    _add("POC_RECLAIM_BULL", live_ok & poc_valid & prev_below_poc & (cl > poc_arr + 0.05 * atr) & (delta_z >= 0.5 * js), "MILESTONE", "VWAP", "BUY", True, poc_safe, "ยึดคืนเหนือเส้น Point of Control (POC) พร้อม Order Flow ฝั่งซื้อ")
    _add("POC_RECLAIM_BEAR", live_ok & poc_valid & prev_above_poc & (cl < poc_arr - 0.05 * atr) & (delta_z <= -0.5 * js), "MILESTONE", "VWAP", "SELL", True, poc_safe, "หลุดต่ำกว่าเส้น Point of Control (POC) พร้อม Order Flow ฝั่งขาย")

    return events


def tokenize_htf_events(
    tf_data: Dict[str, Any],
    tf_level: Dict[str, np.ndarray],
) -> Dict[str, np.ndarray]:
    """Computes native higher-timeframe context & setup masks for m5/m15/h1/h4."""
    n = int(tf_data["n"])
    if n == 0:
        return {}
    cl = tf_data["close"]
    op = tf_data["open"]
    ema20 = tf_data["ema20"]
    ema50 = tf_data["ema50"]
    ema200 = tf_data["ema200"]
    atr = np.maximum(tf_data["atr14"], 1e-9)
    rsi = tf_data["rsi14"]
    adx = tf_data["adx14"]
    u_wick = tf_data["upper_wick_ratio"]
    l_wick = tf_data["lower_wick_ratio"]
    r_atr = tf_data["range_atr"]
    mr = tf_data["macro_regime"]

    bull = cl > op
    bear = cl < op

    trend_bull = (mr == "TREND_BULL") | ((ema20 > ema50) & (cl > ema50) & (adx >= 18.0))
    trend_bear = (mr == "TREND_BEAR") | ((ema20 < ema50) & (cl < ema50) & (adx >= 18.0))
    in_range = (mr == "RANGE")

    pb_bull = trend_bull & (cl < ema20 + 0.35 * atr) & (cl >= ema50 - 0.5 * atr) & ((l_wick >= 0.30) | bear)
    pb_bear = trend_bear & (cl > ema20 - 0.35 * atr) & (cl <= ema50 + 0.5 * atr) & ((u_wick >= 0.30) | bull)

    return {
        "TREND_BULL": trend_bull,
        "TREND_BEAR": trend_bear,
        "RANGE": in_range,
        "NEAR_SUPPORT": tf_level["near_support"],
        "NEAR_RESIST": tf_level["near_resistance"],
        "EXHAUSTION_TOP": (rsi >= 66.0) & (u_wick >= 0.35) & (r_atr >= 0.7),
        "EXHAUSTION_BOT": (rsi <= 34.0) & (l_wick >= 0.35) & (r_atr >= 0.7),
        "REJECTION_BULL": (l_wick >= 0.45) & (r_atr >= 0.8),
        "REJECTION_BEAR": (u_wick >= 0.45) & (r_atr >= 0.8),
        "SWEEP_LOW": tf_level["sweep_low"],
        "SWEEP_HIGH": tf_level["sweep_high"],
        "BOS_BULL": tf_level["bos_bull"],
        "BOS_BEAR": tf_level["bos_bear"],
        "CHOCH_BULL": tf_level["choch_bull"],
        "CHOCH_BEAR": tf_level["choch_bear"],
        "FALSE_BREAK_UP": tf_level["false_breakout_up"],
        "FALSE_BREAK_DOWN": tf_level["false_breakout_down"],
        "PULLBACK_BULL": pb_bull,
        "PULLBACK_BEAR": pb_bear,
        "FAILED_RETEST_TOP": tf_level["retest_resist_2x"],
        "FAILED_RETEST_BOT": tf_level["retest_support_2x"],
        "LOWER_HIGH": tf_level["lower_high"],
        "HIGHER_LOW": tf_level["higher_low"],
    }


def project_htf_events_to_m1(
    dataset: Dict[str, Any],
    htf_tokens: Dict[str, Dict[str, np.ndarray]],
) -> Dict[str, Dict[str, Any]]:
    """
    Projects causal closed HTF states & developing HTF states onto the M1 timeline.
    For MTF setups (`m5`, `m15`), retains active setup signal for latest 2 closed bars
    and emits exact `event_bar_ts` for Cross-TF temporal ordering tests.
    """
    n_m1 = int(dataset["m1"]["n"])
    aligned = dataset["aligned_htf"]
    htf_map = dataset["htf"]

    projected: Dict[str, Dict[str, Any]] = {}
    if n_m1 == 0:
        return projected

    def _proj(tf: str, key: str, lookback_closed_bars: int = 1) -> tuple[np.ndarray, np.ndarray]:
        c_idx = aligned[tf]["closed_idx"]
        native = htf_tokens.get(tf, {}).get(key)
        tf_ts = htf_map[tf]["ts_unix"]
        out_mask = np.zeros(n_m1, dtype=bool)
        ev_ts = np.zeros(n_m1, dtype=np.int64)
        if native is None or len(native) == 0:
            return out_mask, ev_ts
        valid_c = c_idx >= 0
        for lag in range(lookback_closed_bars):
            shifted = np.maximum(c_idx - lag, 0)
            hit = valid_c & ((c_idx - lag) >= 0) & native[shifted]
            newly = hit & (~out_mask)
            out_mask |= hit
            ev_ts[newly] = tf_ts[shifted[newly]]
        return out_mask, ev_ts

    def _reg(tf: str, name: str, key: str, lookback: int, desc: str) -> None:
        m, ets = _proj(tf, key, lookback_closed_bars=lookback)
        projected[name] = {"name": name, "tf": tf, "mask": m, "event_ts": ets, "desc": desc}

    # Context H4 / H1
    for tf in ("h4", "h1"):
        up = tf.upper()
        _reg(tf, f"{up}_TREND_BULL", "TREND_BULL", 1, f"{up} อยู่ในแนวโน้มขาขึ้น")
        _reg(tf, f"{up}_TREND_BEAR", "TREND_BEAR", 1, f"{up} อยู่ในแนวโน้มขาลง")
        _reg(tf, f"{up}_RANGE", "RANGE", 1, f"{up} อยู่ในกรอบ Sideway/Range")
        _reg(tf, f"{up}_NEAR_SUPPORT", "NEAR_SUPPORT", 1, f"{up} อยู่ใกล้โซนแนวรับสำคัญ")
        _reg(tf, f"{up}_NEAR_RESIST", "NEAR_RESIST", 1, f"{up} อยู่ใกล้โซนแนวต้านสำคัญ")
        _reg(tf, f"{up}_EXHAUSTION_TOP", "EXHAUSTION_TOP", 1, f"{up} แรงซื้อปลายคลื่นแผ่ว")
        _reg(tf, f"{up}_EXHAUSTION_BOT", "EXHAUSTION_BOT", 1, f"{up} แรงขายปลายคลื่นแผ่ว")
        _reg(tf, f"{up}_REJECTION_BULL", "REJECTION_BULL", 1, f"{up} แท่งปิดทิ้งไส้ล่างปฏิเสธขาลง")
        _reg(tf, f"{up}_REJECTION_BEAR", "REJECTION_BEAR", 1, f"{up} แท่งปิดทิ้งไส้บนปฏิเสธขาขึ้น")

    # Setup M15 / M5 (keep recent 2 closed bars for active setup propagation + event_ts)
    for tf in ("m15", "m5"):
        up = tf.upper()
        _reg(tf, f"{up}_TREND_BULL", "TREND_BULL", 1, f"{up} แนวโน้มขาขึ้น")
        _reg(tf, f"{up}_TREND_BEAR", "TREND_BEAR", 1, f"{up} แนวโน้มขาลง")
        _reg(tf, f"{up}_SWEEP_LOW", "SWEEP_LOW", 2, f"{up} เกิด Liquidity Sweep ด้านล่าง")
        _reg(tf, f"{up}_SWEEP_HIGH", "SWEEP_HIGH", 2, f"{up} เกิด Liquidity Sweep ด้านบน")
        _reg(tf, f"{up}_BOS_BULL", "BOS_BULL", 2, f"{up} เกิด Bullish BOS")
        _reg(tf, f"{up}_BOS_BEAR", "BOS_BEAR", 2, f"{up} เกิด Bearish BOS")
        _reg(tf, f"{up}_CHOCH_BULL", "CHOCH_BULL", 2, f"{up} เกิด Bullish CHoCH")
        _reg(tf, f"{up}_CHOCH_BEAR", "CHOCH_BEAR", 2, f"{up} เกิด Bearish CHoCH")
        _reg(tf, f"{up}_FALSE_BREAK_UP", "FALSE_BREAK_UP", 2, f"{up} เกิด False Breakout ด้านบน")
        _reg(tf, f"{up}_FALSE_BREAK_DOWN", "FALSE_BREAK_DOWN", 2, f"{up} เกิด False Breakdown ด้านล่าง")
        _reg(tf, f"{up}_PULLBACK_BULL", "PULLBACK_BULL", 2, f"{up} ย่อตัวในแนวโน้มขาขึ้น")
        _reg(tf, f"{up}_PULLBACK_BEAR", "PULLBACK_BEAR", 2, f"{up} ดีดตัวในแนวโน้มขาลง")
        _reg(tf, f"{up}_FAILED_RETEST_TOP", "FAILED_RETEST_TOP", 2, f"{up} ทดสอบ High ไม่ผ่าน >=2 ครั้ง")
        _reg(tf, f"{up}_FAILED_RETEST_BOT", "FAILED_RETEST_BOT", 2, f"{up} ทดสอบ Low ไม่หลุด >=2 ครั้ง")
        _reg(tf, f"{up}_LOWER_HIGH", "LOWER_HIGH", 2, f"{up} ทำ Lower High")
        _reg(tf, f"{up}_HIGHER_LOW", "HIGHER_LOW", 2, f"{up} ทำ Higher Low")

    # Developing HTF Causal Signals (as-of-now H1 / M15 without waiting for HTF bar close)
    m1_ts = dataset["m1"]["ts_unix"]
    for tf in ("m15", "h1"):
        up = tf.upper()
        al = aligned[tf]
        dev_rej_bull = (al["dev_lower_wick_ratio"] >= 0.45) & (al["dev_pos_in_range"] >= 0.55)
        dev_rej_bear = (al["dev_upper_wick_ratio"] >= 0.45) & (al["dev_pos_in_range"] <= 0.45)
        dev_imp_bull = (al["dev_ret_atr"] >= 0.65) & (al["dev_body_ratio"] >= 0.55)
        dev_imp_bear = (al["dev_ret_atr"] <= -0.65) & (al["dev_body_ratio"] >= 0.55)

        projected[f"DEV_{up}_REJECTION_BULL"] = {"name": f"DEV_{up}_REJECTION_BULL", "tf": tf, "mask": dev_rej_bull, "event_ts": m1_ts, "desc": f"แท่ง {up} ที่กำลังก่อตัวทิ้งไส้ล่างปฏิเสธ (Causal as-of-now)"}
        projected[f"DEV_{up}_REJECTION_BEAR"] = {"name": f"DEV_{up}_REJECTION_BEAR", "tf": tf, "mask": dev_rej_bear, "event_ts": m1_ts, "desc": f"แท่ง {up} ที่กำลังก่อตัวทิ้งไส้บนปฏิเสธ (Causal as-of-now)"}
        projected[f"DEV_{up}_IMPULSE_BULL"] = {"name": f"DEV_{up}_IMPULSE_BULL", "tf": tf, "mask": dev_imp_bull, "event_ts": m1_ts, "desc": f"แท่ง {up} ที่กำลังก่อตัวพุ่งขึ้นแรง >=0.65 ATR (Causal)"}
        projected[f"DEV_{up}_IMPULSE_BEAR"] = {"name": f"DEV_{up}_IMPULSE_BEAR", "tf": tf, "mask": dev_imp_bear, "event_ts": m1_ts, "desc": f"แท่ง {up} ที่กำลังก่อตัวทิ้งดิ่ง >=0.65 ATR (Causal)"}

    return projected
