"""
Dynamic Liquidity Zones, Causal Swing Pivots & Touch Counter (Step 3)
=====================================================================
Provides zero-lookahead market structure and fuzzy liquidity zone tracking:
- Causal swing highs/lows confirmed strictly `pivot_right` bars later (`i == p + pivot_right`).
- Dynamic zone clustering within +-0.25 ATR with hysteresis-based touch counting
  (must exit by >=0.35 ATR before another touch increments `touch_count`).
- Emits structural milestone masks + anchor prices (`sweep_low`, `sweep_high`,
  `false_breakout_up`, `false_breakout_down`, `reclaim_low`, `reclaim_high`,
  `retest_support_2x`, `retest_resist_2x`, `higher_low`, `lower_high`,
  `bos_bull`, `bos_bear`, `choch_bull`, `choch_bear`, `near_support`, `near_resistance`).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import numpy as np


@dataclass
class LiquidityZone:
    price: float
    zone_type: str  # "SUPPORT" or "RESIST"
    created_bar: int
    touch_count: int = 1
    equal_level: bool = False
    in_zone: bool = False
    exited: bool = False
    last_touch_bar: int = -1
    strength: float = 1.0


class DynamicLevelMemory:
    """Maintains bounded causal active support/resistance zones with touch counting."""

    def __init__(self, max_zones_per_side: int = 20) -> None:
        self.max_zones_per_side = max_zones_per_side
        self.support_zones: List[LiquidityZone] = []
        self.resist_zones: List[LiquidityZone] = []

    def add_confirmed_pivot(self, price: float, zone_type: str, bar_idx: int, atr: float) -> LiquidityZone:
        zones = self.support_zones if zone_type == "SUPPORT" else self.resist_zones
        cluster_band = 0.25 * atr
        for z in reversed(zones):
            if abs(z.price - price) <= cluster_band:
                z.price = 0.5 * (z.price + price)
                z.equal_level = True
                z.strength += 1.0
                if z.exited or (bar_idx - z.last_touch_bar >= 4):
                    z.touch_count += 1
                    z.last_touch_bar = bar_idx
                    z.exited = False
                    z.in_zone = False
                return z

        nz = LiquidityZone(
            price=float(price),
            zone_type=zone_type,
            created_bar=bar_idx,
            touch_count=1,
            equal_level=False,
            in_zone=False,
            exited=False,
            last_touch_bar=bar_idx,
            strength=1.0,
        )
        zones.append(nz)
        if len(zones) > self.max_zones_per_side:
            zones.pop(0)
        return nz


def extract_level_structure(
    tf_data: Dict[str, Any],
    pivot_left: int = 3,
    pivot_right: int = 3,
    is_m1_live: bool = False,
) -> Dict[str, np.ndarray]:
    """
    Extracts strictly causal structural milestones and level anchors for a TF series.
    All arrays returned have length `n` and `dtype=bool` (except `*_anchor` floats).
    """
    n = int(tf_data["n"])
    op = tf_data["open"]
    hi = tf_data["high"]
    lo = tf_data["low"]
    cl = tf_data["close"]
    atr = tf_data["atr14"]

    out_keys = (
        "sweep_low",
        "sweep_high",
        "false_breakout_up",
        "false_breakout_down",
        "reclaim_low",
        "reclaim_high",
        "retest_support_2x",
        "retest_resist_2x",
        "higher_low",
        "lower_high",
        "bos_bull",
        "bos_bear",
        "choch_bull",
        "choch_bear",
        "near_support",
        "near_resistance",
        "confirmed_swing_high",
        "confirmed_swing_low",
    )
    res: Dict[str, np.ndarray] = {k: np.zeros(n, dtype=bool) for k in out_keys}
    res["anchor_bull"] = np.copy(lo)
    res["anchor_bear"] = np.copy(hi)

    if n == 0:
        return res

    memory = DynamicLevelMemory(max_zones_per_side=18)

    last_sw_h: Optional[float] = None
    prev_sw_h: Optional[float] = None
    last_sw_l: Optional[float] = None
    prev_sw_l: Optional[float] = None
    sw_h_broken = False
    sw_l_broken = False
    struct_bias = 0  # +1 bull, -1 bear

    last_bull_sweep_bar = -999
    last_bull_sweep_lvl = 0.0
    last_bear_sweep_bar = -999
    last_bear_sweep_lvl = 0.0

    ref_high_keys = ("day_high", "prev_high", "asia_high", "high60", "vah") if is_m1_live else ()
    ref_low_keys = ("day_low", "prev_low", "asia_low", "low60", "val") if is_m1_live else ()

    for i in range(n):
        cur_o = float(op[i])
        cur_h = float(hi[i])
        cur_l = float(lo[i])
        cur_c = float(cl[i])
        cur_atr = max(float(atr[i]), 1e-9)

        band = 0.25 * cur_atr
        exit_dist = 0.35 * cur_atr
        pierce_min = 0.15 * cur_atr

        # 1. Check strict causal pivot confirmation at bar i (`p = i - pivot_right`)
        if i >= pivot_left + pivot_right:
            p = i - pivot_right
            win_h = hi[p - pivot_left : i + 1]
            if float(hi[p]) == float(win_h.max()) and int(win_h.argmax()) == pivot_left:
                sw_h = float(hi[p])
                res["confirmed_swing_high"][i] = True
                prev_sw_h = last_sw_h
                last_sw_h = sw_h
                sw_h_broken = False
                memory.add_confirmed_pivot(sw_h, "RESIST", i, cur_atr)
                if prev_sw_h is not None and sw_h < prev_sw_h - 0.05 * cur_atr:
                    res["lower_high"][i] = True
                    res["anchor_bear"][i] = sw_h

            win_l = lo[p - pivot_left : i + 1]
            if float(lo[p]) == float(win_l.min()) and int(win_l.argmin()) == pivot_left:
                sw_l = float(lo[p])
                res["confirmed_swing_low"][i] = True
                prev_sw_l = last_sw_l
                last_sw_l = sw_l
                sw_l_broken = False
                memory.add_confirmed_pivot(sw_l, "SUPPORT", i, cur_atr)
                if prev_sw_l is not None and sw_l > prev_sw_l + 0.05 * cur_atr:
                    res["higher_low"][i] = True
                    res["anchor_bull"][i] = sw_l

        # 2. Check dynamic resistance zones for touches, sweeps, false breakouts, proximity
        best_res_anchor = cur_h
        for z in memory.resist_zones:
            if abs(cur_c - z.price) <= exit_dist or cur_h >= z.price - exit_dist:
                if abs(cur_c - z.price) <= 0.35 * cur_atr:
                    res["near_resistance"][i] = True

            # Hysteresis exit: must pull back below resistance by >= 0.35 ATR
            if cur_c < z.price - exit_dist and cur_h < z.price - 0.10 * cur_atr:
                z.exited = True
                z.in_zone = False

            # Zone re-entry / touch
            if z.exited and not z.in_zone and cur_h >= z.price - band:
                z.in_zone = True
                z.exited = False
                z.touch_count += 1
                z.last_touch_bar = i
                if z.touch_count >= 2 and cur_c < z.price - 0.05 * cur_atr:
                    res["retest_resist_2x"][i] = True
                    best_res_anchor = z.price

            # Liquidity sweep above resistance & close back below
            if cur_h >= z.price + pierce_min and cur_c < z.price:
                res["sweep_high"][i] = True
                best_res_anchor = z.price

            # False breakout up (closed above within prior 1..3 bars, now closes back below)
            if i >= 2:
                prev_closed_above = any(float(cl[j]) > z.price + 0.05 * cur_atr for j in range(max(0, i - 3), i))
                if prev_closed_above and cur_c < z.price - 0.05 * cur_atr:
                    res["false_breakout_up"][i] = True
                    best_res_anchor = z.price

        # Also check M1 live reference high levels (dayHigh, prevHigh, asiaHigh, high60, vah)
        for rk in ref_high_keys:
            rv = float(tf_data[rk][i])
            if math.isfinite(rv) and rv > 0:
                if abs(cur_c - rv) <= 0.35 * cur_atr:
                    res["near_resistance"][i] = True
                if cur_h >= rv + pierce_min and cur_c < rv:
                    res["sweep_high"][i] = True
                    best_res_anchor = rv
                if i >= 2:
                    if any(float(cl[j]) > rv + 0.05 * cur_atr for j in range(max(0, i - 3), i)) and cur_c < rv - 0.05 * cur_atr:
                        res["false_breakout_up"][i] = True
                        best_res_anchor = rv

        if res["sweep_high"][i] or res["false_breakout_up"][i]:
            res["anchor_bear"][i] = best_res_anchor
            last_bear_sweep_bar = i
            last_bear_sweep_lvl = best_res_anchor

        # 3. Check dynamic support zones for touches, sweeps, false breakouts, proximity
        best_sup_anchor = cur_l
        for z in memory.support_zones:
            if abs(cur_c - z.price) <= 0.35 * cur_atr:
                res["near_support"][i] = True

            if cur_c > z.price + exit_dist and cur_l > z.price + 0.10 * cur_atr:
                z.exited = True
                z.in_zone = False

            if z.exited and not z.in_zone and cur_l <= z.price + band:
                z.in_zone = True
                z.exited = False
                z.touch_count += 1
                z.last_touch_bar = i
                if z.touch_count >= 2 and cur_c > z.price + 0.05 * cur_atr:
                    res["retest_support_2x"][i] = True
                    best_sup_anchor = z.price

            if cur_l <= z.price - pierce_min and cur_c > z.price:
                res["sweep_low"][i] = True
                best_sup_anchor = z.price

            if i >= 2:
                prev_closed_below = any(float(cl[j]) < z.price - 0.05 * cur_atr for j in range(max(0, i - 3), i))
                if prev_closed_below and cur_c > z.price + 0.05 * cur_atr:
                    res["false_breakout_down"][i] = True
                    best_sup_anchor = z.price

        for rk in ref_low_keys:
            rv = float(tf_data[rk][i])
            if math.isfinite(rv) and rv > 0:
                if abs(cur_c - rv) <= 0.35 * cur_atr:
                    res["near_support"][i] = True
                if cur_l <= rv - pierce_min and cur_c > rv:
                    res["sweep_low"][i] = True
                    best_sup_anchor = rv
                if i >= 2:
                    if any(float(cl[j]) < rv - 0.05 * cur_atr for j in range(max(0, i - 3), i)) and cur_c > rv + 0.05 * cur_atr:
                        res["false_breakout_down"][i] = True
                        best_sup_anchor = rv

        if res["sweep_low"][i] or res["false_breakout_down"][i]:
            res["anchor_bull"][i] = best_sup_anchor
            last_bull_sweep_bar = i
            last_bull_sweep_lvl = best_sup_anchor

        # 4. Reclaim events (bullish reclaim after recent sweep_low/false_breakout_down; bearish mirror)
        if 0 <= (i - last_bull_sweep_bar) <= 5 and cur_c > last_bull_sweep_lvl + 0.10 * cur_atr and cur_c > cur_o:
            res["reclaim_low"][i] = True
            res["anchor_bull"][i] = last_bull_sweep_lvl
        if 0 <= (i - last_bear_sweep_bar) <= 5 and cur_c < last_bear_sweep_lvl - 0.10 * cur_atr and cur_c < cur_o:
            res["reclaim_high"][i] = True
            res["anchor_bear"][i] = last_bear_sweep_lvl

        # 5. Market Structure Breaks (BOS & CHoCH strictly on close beyond confirmed swing)
        if last_sw_h is not None and not sw_h_broken and cur_c > last_sw_h + 0.15 * cur_atr:
            if struct_bias == -1:
                res["choch_bull"][i] = True
            else:
                res["bos_bull"][i] = True
            res["anchor_bull"][i] = last_sw_h
            struct_bias = 1
            sw_h_broken = True

        if last_sw_l is not None and not sw_l_broken and cur_c < last_sw_l - 0.15 * cur_atr:
            if struct_bias == 1:
                res["choch_bear"][i] = True
            else:
                res["bos_bear"][i] = True
            res["anchor_bear"][i] = last_sw_l
            struct_bias = -1
            sw_l_broken = True

    return res
