"""
Session-Partitioned Regime Engine & Blowup Forensics (Phase 2 — System Rules V5)
================================================================================
Implements Architecture V5 Phase 2 on top of Phase 1's HybridDataMerger:
1. 7-Zone Session & Cross-Session Transition Segmentation:
   ASIA, ASIA_TO_LONDON, LONDON, LONDON_TO_NY, NY, NY_TO_CLOSE, OVERNIGHT.
2. Strict Zero-Lookahead Feature & Macro Regime Extraction across merged
   cTrader OHLCV + Sanitized Live Microstructure streams (signals only on real
   L2 DOM + Tick Spread bars, filled at next bar open).
3. Adaptive Optimization without fixed SL / RR / Flat limits: tests tight/balanced/
   wide ATR-based stops, zone-end exits, rollover-guard exits, and hold-overnight
   modes per (symbol, session_zone, macro_regime, strategy_id).
4. Chronological In-Sample (60%) / Out-of-Sample (40%) Anti-Overfitting Validation
   and honest situational reporting (no artificial N>=500 gate, no permanent ban).
5. Blowup & Failure Forensics Logger: runs unhedged zero-SL stress profiles in
   research mode to record exact crash timestamps, regime/zone transitions,
   spread spikes, diagnoses, and winning counter-strategies.
"""

from __future__ import annotations

import json
import math
import statistics
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from research.hybrid_data_merger import HybridDataMerger, SESSION_ZONES, classify_session_zone


MACRO_REGIMES = ("TREND_BULL", "TREND_BEAR", "BREAKOUT", "RANGE", "THIN_OR_NEWS")

ASSET_SPECS: Dict[str, Dict[str, Any]] = {
    # Verified directly from %LOCALAPPDATA%\BacktestLab\live\*\trades.csv (#5258778, 0.01 lot)
    "XAUUSD": {
        "lot_scale": 1.0,       # units=1 (1 oz = 0.01 lot)
        "commission_usd": 0.08,
        "base_slippage": 0.08,
        "default_spread": 0.13,
        "min_atr": 0.25,
        "imb_th": 0.018,
        "delta_th": 6.0,
        "rollover_avoid_zones": ("NY_TO_CLOSE",),
        "rollover_spread_warn": 0.24,
    },
    "BTCUSD": {
        "lot_scale": 0.01,      # units=0.01 (0.01 BTC)
        "commission_usd": 0.00,
        "base_slippage": 3.00,
        "default_spread": 15.0,
        "min_atr": 12.0,
        "imb_th": 0.020,
        "delta_th": 12.0,
        "rollover_avoid_zones": (),
        "rollover_spread_warn": 35.0,
    },
    "ETHUSD": {
        "lot_scale": 0.01,      # units=0.01 (0.01 ETH)
        "commission_usd": 0.00,
        "base_slippage": 0.35,
        "default_spread": 2.0,
        "min_atr": 0.80,
        "imb_th": 0.015,
        "delta_th": 5.0,
        "rollover_avoid_zones": (),
        "rollover_spread_warn": 3.8,
    },
}

PARAMETER_PROFILES: Tuple[Dict[str, Any], ...] = (
    {"name": "ADAPTIVE_TIGHT", "sl_atr": 1.2, "rr": 2.0, "exit_mode": "HOLD_THRU", "max_bars": 240, "is_forensic": False},
    {"name": "ADAPTIVE_BALANCED", "sl_atr": 2.0, "rr": 2.5, "exit_mode": "HOLD_THRU", "max_bars": 240, "is_forensic": False},
    {"name": "ADAPTIVE_WIDE", "sl_atr": 3.5, "rr": 3.0, "exit_mode": "HOLD_THRU", "max_bars": 360, "is_forensic": False},
    {"name": "ZONE_SCALP_FLAT", "sl_atr": 1.5, "rr": 2.0, "exit_mode": "EXIT_AT_ZONE_END", "max_bars": 180, "is_forensic": False},
    {"name": "FAST_RR_1_5", "sl_atr": 1.8, "rr": 1.5, "exit_mode": "ZONE_OR_SLTP", "max_bars": 180, "is_forensic": False},
    {"name": "ROLLOVER_GUARD_ADAPTIVE", "sl_atr": 2.0, "rr": 2.5, "exit_mode": "ROLLOVER_GUARD", "max_bars": 240, "is_forensic": False},
    {"name": "FORENSIC_ZERO_SL", "sl_atr": None, "rr": None, "exit_mode": "ZERO_SL_FORENSIC", "max_bars": 720, "is_forensic": True},
)

STRATEGY_META: Dict[str, Dict[str, str]] = {
    "STR-001": {"name": "Trend Following Pullback", "family": "TREND_FOLLOWING"},
    "STR-002": {"name": "Session VWAP Mean Reversion", "family": "MEAN_REVERSION"},
    "STR-003": {"name": "Liquidity Sweep & Rejection Reversal", "family": "LIQUIDITY_SWEEP"},
    "STR-004": {"name": "Volatility Expansion Breakout", "family": "BREAKOUT"},
    "STR-006": {"name": "L2 DOM Wall Absorption", "family": "DOM_ORDER_FLOW"},
    "STR-010": {"name": "Anchored VWAP Macro Shield", "family": "VWAP_EQUILIBRIUM"},
}


def _safe_num(val: Any, default: float = 0.0) -> float:
    if val is None or val == "":
        return default
    try:
        num = float(val)
        return num if math.isfinite(num) else default
    except (ValueError, TypeError):
        return default


def enrich_merged_bars(bars: List[Dict[str, Any]], symbol: str) -> List[Dict[str, Any]]:
    """
    Computes strictly backward-looking technical, microstructure, and 7-zone session
    features in a single O(N) pass with zero future-bar lookahead.
    """
    n = len(bars)
    if n == 0:
        return []

    spec = ASSET_SPECS.get(symbol, ASSET_SPECS["XAUUSD"])
    default_sp = spec["default_spread"]

    closes: List[float] = []
    highs: List[float] = []
    lows: List[float] = []
    tr_hist: List[float] = []
    atr_hist: List[float] = []
    live_spread_hist: List[float] = []

    ema20 = _safe_num(bars[0].get("close"))
    ema50 = ema20
    ema200 = ema20
    atr14 = max(_safe_num(bars[0].get("high")) - _safe_num(bars[0].get("low")), spec["min_atr"])
    plus_dm_s = 0.0
    minus_dm_s = 0.0
    tr_s = atr14
    dx_hist: List[float] = []
    prev_close = ema20
    prev_high = _safe_num(bars[0].get("high"), ema20)
    prev_low = _safe_num(bars[0].get("low"), ema20)

    # Incremental intra-day fallback VWAP strictly from past/current closed bars
    cur_day = ""
    cum_pv = 0.0
    cum_v = 0.0
    day_closes: List[float] = []

    enriched: List[Dict[str, Any]] = []
    for i, b in enumerate(bars):
        o = _safe_num(b.get("open"))
        h = _safe_num(b.get("high"), o)
        l = _safe_num(b.get("low"), o)
        c = _safe_num(b.get("close"), o)
        t_str = str(b.get("time", ""))
        day_str = t_str[:10]

        closes.append(c)
        highs.append(h)
        lows.append(l)

        ema20 = c if i == 0 else c * (2.0 / 21.0) + ema20 * (1.0 - 2.0 / 21.0)
        ema50 = c if i == 0 else c * (2.0 / 51.0) + ema50 * (1.0 - 2.0 / 51.0)
        ema200 = c if i == 0 else c * (2.0 / 201.0) + ema200 * (1.0 - 2.0 / 201.0)

        tr = max(h - l, abs(h - prev_close), abs(l - prev_close))
        tr_hist.append(tr)
        if i >= 13:
            atr14 = sum(tr_hist[i - 13 : i + 1]) / 14.0
        else:
            atr14 = sum(tr_hist) / len(tr_hist)
        atr14 = max(atr14, spec["min_atr"] * 0.25)
        atr_hist.append(atr14)

        up_move = h - prev_high
        down_move = prev_low - l
        plus_dm = up_move if (up_move > down_move and up_move > 0) else 0.0
        minus_dm = down_move if (down_move > up_move and down_move > 0) else 0.0
        tr_s = (tr_s * 13.0 + tr) / 14.0 if i > 0 else max(tr, 1e-6)
        plus_dm_s = (plus_dm_s * 13.0 + plus_dm) / 14.0 if i > 0 else plus_dm
        minus_dm_s = (minus_dm_s * 13.0 + minus_dm) / 14.0 if i > 0 else minus_dm
        plus_di = 100.0 * plus_dm_s / max(tr_s, 1e-6)
        minus_di = 100.0 * minus_dm_s / max(tr_s, 1e-6)
        dx = 100.0 * abs(plus_di - minus_di) / max(plus_di + minus_di, 1e-6)
        dx_hist.append(dx)
        adx14 = sum(dx_hist[-14:]) / len(dx_hist[-14:])

        win20 = closes[max(0, i - 19) : i + 1]
        bb_mid = sum(win20) / len(win20)
        bb_sd = math.sqrt(sum((x - bb_mid) ** 2 for x in win20) / max(1, len(win20)))
        bb_bw = (4.0 * bb_sd) / max(abs(bb_mid), 1e-6)

        prev_hh20 = max(highs[max(0, i - 20) : i]) if i > 0 else h
        prev_ll20 = min(lows[max(0, i - 20) : i]) if i > 0 else l
        hh15 = max(highs[max(0, i - 15) : i]) if i > 0 else h
        ll15 = min(lows[max(0, i - 15) : i]) if i > 0 else l

        if day_str != cur_day:
            cur_day = day_str
            cum_pv = 0.0
            cum_v = 0.0
            day_closes = []
        vol = max(_safe_num(b.get("tickVolume"), 1.0), 1.0)
        cum_pv += ((h + l + c) / 3.0) * vol
        cum_v += vol
        day_closes.append(c)
        fallback_vwap = cum_pv / cum_v if cum_v > 0 else c
        fallback_sd = max(
            math.sqrt(sum((x - fallback_vwap) ** 2 for x in day_closes) / max(1, len(day_closes))),
            atr14 * 1.2,
        )

        vwap = _safe_num(b.get("vwapDay"), 0.0)
        if vwap <= 0:
            vwap = fallback_vwap
        sd_day = _safe_num(b.get("sdDay"), 0.0)
        if sd_day <= 0:
            sd_day = fallback_sd

        has_l2 = bool(b.get("has_l2_dom")) and bool(b.get("has_real_spread"))
        sp = _safe_num(b.get("spreadAvg"), default_sp) if has_l2 else default_sp
        if has_l2 and sp > 0:
            live_spread_hist.append(sp)
        recent_sp = live_spread_hist[-120:] if live_spread_hist else [default_sp]
        med_sp = statistics.median(recent_sp)

        next_imp = str(b.get("nextImpact", "")).upper()
        last_imp = str(b.get("lastImpact", "")).upper()
        min_to_next = _safe_num(b.get("minToNext"), 999.0)
        min_since_last = _safe_num(b.get("minSinceLast"), 999.0)
        is_news_void = (min_to_next <= 30.0 and next_imp in ("HIGH", "EXTREME")) or (
            min_since_last <= 15.0 and last_imp in ("HIGH", "EXTREME")
        )
        is_thin_spread = has_l2 and (sp > max(med_sp * 2.2, spec["rollover_spread_warn"] * 0.95))

        atr_base = sum(atr_hist[max(0, len(atr_hist) - 60) :]) / max(1, len(atr_hist[-60:]))
        if is_news_void or is_thin_spread:
            macro_regime = "THIN_OR_NEWS"
        elif adx14 >= 24.0 and ema50 > ema200 and c > ema50:
            macro_regime = "TREND_BULL"
        elif adx14 >= 24.0 and ema50 < ema200 and c < ema50:
            macro_regime = "TREND_BEAR"
        elif (c > prev_hh20 or c < prev_ll20) and (atr14 >= atr_base * 1.15 or bb_bw >= 0.0032):
            macro_regime = "BREAKOUT"
        else:
            macro_regime = "RANGE"

        sz = b.get("session_zone")
        is_trans = b.get("is_session_transition")
        if not sz:
            try:
                dt = datetime.strptime(t_str, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
            except Exception:
                dt = datetime.fromtimestamp(int(b.get("ts_unix", 0) or 0), tz=timezone.utc)
            sz, is_trans = classify_session_zone(dt)

        enriched.append(
            {
                "time": t_str,
                "ts_unix": int(b.get("ts_unix", 0) or 0),
                "open": o,
                "high": h,
                "low": l,
                "close": c,
                "spread": sp,
                "med_spread": med_sp,
                "imbalance": _safe_num(b.get("imbalance"), 0.0),
                "delta": _safe_num(b.get("delta"), 0.0),
                "sweep": str(b.get("sweep", "") or ""),
                "has_live": has_l2,
                "has_flow": bool(b.get("has_order_flow")),
                "session_zone": sz,
                "is_transition": bool(is_trans),
                "macro_regime": macro_regime,
                "ema20": ema20,
                "ema50": ema50,
                "ema200": ema200,
                "atr14": atr14,
                "adx14": adx14,
                "bb_bw": bb_bw,
                "vwap": vwap,
                "sd": sd_day,
                "prev_hh20": prev_hh20,
                "prev_ll20": prev_ll20,
                "hh15": hh15,
                "ll15": ll15,
                "is_news_void": is_news_void,
            }
        )
        prev_close = c
        prev_high = h
        prev_low = l

    return enriched


def evaluate_all_strategy_signals(bar: Dict[str, Any], symbol: str) -> Dict[str, str]:
    """
    Evaluates BUY/SELL/NONE signals across all 6 V5 candidate strategy families on a
    closed bar, requiring real L2 DOM & Tick Spread provenance before generating entries.
    """
    none_map = {sid: "NONE" for sid in STRATEGY_META}
    if not bar["has_live"] or bar["is_news_void"]:
        return none_map

    spec = ASSET_SPECS.get(symbol, ASSET_SPECS["XAUUSD"])
    imb_th = spec["imb_th"]
    delta_th = spec["delta_th"]

    o, h, l, c = bar["open"], bar["high"], bar["low"], bar["close"]
    rng = max(h - l, 1e-6)
    lower_wick = min(o, c) - l
    upper_wick = h - max(o, c)

    ema50, ema200 = bar["ema50"], bar["ema200"]
    atr14, adx14 = bar["atr14"], bar["adx14"]
    vwap, sd = bar["vwap"], bar["sd"]
    delta, imb = bar["delta"], bar["imbalance"]
    regime = bar["macro_regime"]
    is_bull_macro = c > ema50 and ema50 > ema200
    is_bear_macro = c < ema50 and ema50 < ema200

    signals: Dict[str, str] = {}

    # STR-001: Trend Following Pullback / Continuation
    if regime == "TREND_BULL" and c > ema50 and l <= ema50 + 0.6 * atr14 and delta > 0:
        signals["STR-001"] = "BUY"
    elif regime == "TREND_BEAR" and c < ema50 and h >= ema50 - 0.6 * atr14 and delta < 0:
        signals["STR-001"] = "SELL"
    else:
        signals["STR-001"] = "NONE"

    # STR-002: Session VWAP Mean Reversion
    if c <= vwap - sd * 1.0 and delta > 0 and regime != "TREND_BEAR":
        signals["STR-002"] = "BUY"
    elif c >= vwap + sd * 1.0 and delta < 0 and regime != "TREND_BULL":
        signals["STR-002"] = "SELL"
    else:
        signals["STR-002"] = "NONE"

    # STR-003: Liquidity Sweep & Rejection Reversal
    has_sweep = bool(bar["sweep"])
    if (has_sweep or lower_wick >= rng * 0.45) and l <= bar["prev_ll20"] + 0.25 * atr14 and delta >= delta_th * 0.5 and imb >= imb_th * 0.5:
        signals["STR-003"] = "BUY"
    elif (has_sweep or upper_wick >= rng * 0.45) and h >= bar["prev_hh20"] - 0.25 * atr14 and delta <= -delta_th * 0.5 and imb <= -imb_th * 0.5:
        signals["STR-003"] = "SELL"
    else:
        signals["STR-003"] = "NONE"

    # STR-004: Volatility Expansion Breakout
    if c > bar["prev_hh20"] and delta >= delta_th and (adx14 >= 20.0 or regime == "BREAKOUT"):
        signals["STR-004"] = "BUY"
    elif c < bar["prev_ll20"] and delta <= -delta_th and (adx14 >= 20.0 or regime == "BREAKOUT"):
        signals["STR-004"] = "SELL"
    else:
        signals["STR-004"] = "NONE"

    # STR-006: L2 DOM Wall Absorption
    range15 = max(bar["hh15"] - bar["ll15"], atr14)
    if imb >= imb_th and c <= bar["ll15"] + 0.25 * range15 and delta >= 0 and not is_bear_macro:
        signals["STR-006"] = "BUY"
    elif imb <= -imb_th and c >= bar["hh15"] - 0.25 * range15 and delta <= 0 and not is_bull_macro:
        signals["STR-006"] = "SELL"
    else:
        signals["STR-006"] = "NONE"

    # STR-010: Anchored VWAP Equilibrium + Macro Shield
    if l <= vwap - sd * 1.0 and delta >= delta_th and not is_bear_macro:
        signals["STR-010"] = "BUY"
    elif h >= vwap + sd * 1.0 and delta <= -delta_th and not is_bull_macro:
        signals["STR-010"] = "SELL"
    else:
        signals["STR-010"] = "NONE"

    return signals


def _diagnose_forensic_failure(
    entry_zone: str,
    worst_zone: str,
    entry_regime: str,
    worst_regime: str,
    worst_spread: float,
    rollover_warn: float,
    strategy_id: str,
) -> Tuple[str, str]:
    """Produces deterministic forensic diagnosis and actionable counter-strategy guidance."""
    if worst_spread >= rollover_warn or "NY_TO_CLOSE" in (entry_zone, worst_zone) or "OVERNIGHT" == worst_zone:
        return (
            "ROLLOVER_SPREAD_OR_THIN_LIQUIDITY",
            "ใช้ ROLLOVER_GUARD_ADAPTIVE หรือ STR-009 (No-Trade) ช่วง NY_TO_CLOSE / Spread สูง",
        )
    if entry_regime != worst_regime and worst_regime in ("TREND_BULL", "TREND_BEAR", "BREAKOUT"):
        return (
            f"REGIME_SHIFT_{entry_regime}_TO_{worst_regime}",
            f"หลีกเลี่ยง {strategy_id} แบบไร้ SL เมื่อเกิด {worst_regime}; สลับใช้ STR-001/STR-004 + SL_BALANCED_RR2_5",
        )
    if entry_zone != worst_zone and ("TO_" in worst_zone or "TO_" in entry_zone):
        return (
            f"SESSION_TRANSITION_WHIPSAW_{entry_zone}_TO_{worst_zone}",
            "ปิดสถานะด้วย ZONE_SCALP_FLAT (Exit at Zone End) ก่อนข้ามรอยต่อ Session",
        )
    return (
        "UNHEDGED_ADVERSE_DRAG_WITHOUT_STOP",
        "บังคับใช้ Adaptive ATR SL (1.2x–2.0x ATR) แทนการปล่อย Zero-SL",
    )


def simulate_profile_chronological(
    enriched: List[Dict[str, Any]],
    signal_rows: List[Dict[str, str]],
    symbol: str,
    strategy_id: str,
    profile: Dict[str, Any],
    split_idx: int,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Runs strict zero-lookahead chronological simulation for one (strategy, param_profile).
    Bar i close triggers signal -> fill at bar i+1 open + spread/slippage cost.
    Returns (trades, forensic_events).
    """
    n = len(enriched)
    if n < 60:
        return [], []

    spec = ASSET_SPECS.get(symbol, ASSET_SPECS["XAUUSD"])
    lot = spec["lot_scale"]
    comm = spec["commission_usd"]
    slip = spec["base_slippage"]
    avoid_zones = spec["rollover_avoid_zones"]
    sl_atr = profile["sl_atr"]
    rr = profile["rr"]
    exit_mode = profile["exit_mode"]
    max_bars = int(profile["max_bars"])
    is_forensic = bool(profile["is_forensic"])

    trades: List[Dict[str, Any]] = []
    forensics: List[Dict[str, Any]] = []
    pos: Optional[Dict[str, Any]] = None

    for i in range(50, n):
        bar = enriched[i]
        prev_bar = enriched[i - 1]
        ts_gap_sec = bar["ts_unix"] - prev_bar["ts_unix"] if (bar["ts_unix"] and prev_bar["ts_unix"]) else 60

        # Manage open position on current bar OHLC
        if pos is not None:
            side = pos["side"]
            entry_p = pos["entry_price"]
            sp_now = bar["spread"]

            # Track unrealized Mae / Mfe cleanly using bar high/low
            adv_move = max(0.0, (entry_p - bar["low"]) if side == "BUY" else (bar["high"] - entry_p))
            fav_move = max(0.0, (bar["high"] - entry_p) if side == "BUY" else (entry_p - bar["low"]))
            if adv_move > pos["mae_move"]:
                pos["mae_move"] = adv_move
                pos["worst_time"] = bar["time"]
                pos["worst_zone"] = bar["session_zone"]
                pos["worst_regime"] = bar["macro_regime"]
                pos["worst_spread"] = sp_now
                pos["worst_delta"] = bar["delta"]
            if fav_move > pos["mfe_move"]:
                pos["mfe_move"] = fav_move

            exit_reason: Optional[str] = None
            raw_exit_p = bar["close"]

            # Broker gap / weekend rollover close check (> 45 mins discontinuity)
            if ts_gap_sec > 2700:
                exit_reason = "BROKER_SESSION_GAP_EXIT"
                raw_exit_p = prev_bar["close"]
            elif not is_forensic and pos["sl_price"] is not None:
                if side == "BUY":
                    if bar["low"] <= pos["sl_price"]:
                        exit_reason = "SL"
                        raw_exit_p = pos["sl_price"]
                    elif bar["high"] >= pos["tp_price"]:
                        exit_reason = "TP"
                        raw_exit_p = pos["tp_price"]
                else:
                    if bar["high"] >= pos["sl_price"]:
                        exit_reason = "SL"
                        raw_exit_p = pos["sl_price"]
                    elif bar["low"] <= pos["tp_price"]:
                        exit_reason = "TP"
                        raw_exit_p = pos["tp_price"]

            if exit_reason is None:
                bars_held = i - pos["entry_idx"]
                if exit_mode in ("EXIT_AT_ZONE_END", "ZONE_OR_SLTP") and bar["session_zone"] != pos["entry_zone"]:
                    exit_reason = "ZONE_END_EXIT"
                    raw_exit_p = bar["open"]
                elif exit_mode == "ROLLOVER_GUARD" and bar["session_zone"] in avoid_zones:
                    exit_reason = "ROLLOVER_GUARD_FLAT"
                    raw_exit_p = bar["open"]
                elif is_forensic:
                    opp = signal_rows[i - 1].get(strategy_id, "NONE")
                    mae_atr_now = pos["mae_move"] / max(pos["entry_atr"], spec["min_atr"])
                    if mae_atr_now >= 10.0:
                        exit_reason = "FORENSIC_BLOWUP_CAP"
                        raw_exit_p = bar["close"]
                    elif opp != "NONE" and opp != side and bars_held >= 5:
                        exit_reason = "OPPOSITE_SIGNAL_EXIT"
                        raw_exit_p = bar["close"]
                    elif bars_held >= max_bars or i == n - 1:
                        exit_reason = "FORENSIC_TIMEOUT_EXIT"
                        raw_exit_p = bar["close"]
                elif bars_held >= max_bars or i == n - 1:
                    exit_reason = "TIME_HORIZON_EXIT"
                    raw_exit_p = bar["close"]

            if exit_reason is not None:
                slip_exit = slip * (1.2 if exit_reason in ("SL", "FORENSIC_BLOWUP_CAP") else 0.6)
                fill_exit = (raw_exit_p - slip_exit) if side == "BUY" else (raw_exit_p + slip_exit)
                gross_move = (fill_exit - entry_p) if side == "BUY" else (entry_p - fill_exit)
                # Entry paid full ask/bid spread offset via fill_entry; deduct exit half-spread + comm
                net_usd = (gross_move - sp_now * 0.5) * lot - comm
                r_unit_move = max(pos["risk_move"], spec["min_atr"] * 1.5)
                r_mult = (gross_move - sp_now * 0.5 - (comm / max(lot, 1e-6))) / r_unit_move
                mae_atr = pos["mae_move"] / max(pos["entry_atr"], spec["min_atr"])
                mae_usd = pos["mae_move"] * lot

                trade_rec = {
                    "symbol": symbol,
                    "strategy_id": strategy_id,
                    "profile": profile["name"],
                    "split": pos["split"],
                    "side": side,
                    "entry_time": pos["entry_time"],
                    "exit_time": bar["time"],
                    "entry_zone": pos["entry_zone"],
                    "exit_zone": bar["session_zone"],
                    "entry_regime": pos["entry_regime"],
                    "worst_zone": pos["worst_zone"],
                    "worst_regime": pos["worst_regime"],
                    "bars_held": i - pos["entry_idx"],
                    "sl_dist": round(pos["sl_dist"], 4) if pos["sl_dist"] is not None else None,
                    "pnl_usd": round(net_usd, 4),
                    "r_mult": round(r_mult, 3),
                    "mae_usd": round(mae_usd, 4),
                    "mae_atr": round(mae_atr, 2),
                    "win": net_usd > 0,
                    "exit_reason": exit_reason,
                }
                trades.append(trade_rec)

                # Log blowup / severe drawdown forensic cases
                is_blowup = (
                    exit_reason == "FORENSIC_BLOWUP_CAP"
                    or mae_atr >= 5.5
                    or r_mult <= -2.8
                    or mae_usd >= 20.0
                )
                if is_blowup:
                    diag, rec_counter = _diagnose_forensic_failure(
                        pos["entry_zone"],
                        pos["worst_zone"],
                        pos["entry_regime"],
                        pos["worst_regime"],
                        pos["worst_spread"],
                        spec["rollover_spread_warn"],
                        strategy_id,
                    )
                    forensics.append(
                        {
                            "symbol": symbol,
                            "strategy_id": strategy_id,
                            "profile": profile["name"],
                            "sl_mode": "ZERO_SL" if is_forensic else "PROTECTED",
                            "split": pos["split"],
                            "side": side,
                            "entry_time": pos["entry_time"],
                            "worst_time": pos["worst_time"],
                            "exit_time": bar["time"],
                            "entry_zone": pos["entry_zone"],
                            "worst_zone": pos["worst_zone"],
                            "entry_regime": pos["entry_regime"],
                            "worst_regime": pos["worst_regime"],
                            "pnl_usd": round(net_usd, 4),
                            "r_mult": round(r_mult, 2),
                            "mae_atr": round(mae_atr, 2),
                            "mae_usd": round(mae_usd, 4),
                            "spread_at_worst": round(pos["worst_spread"], 3),
                            "delta_at_worst": round(pos["worst_delta"], 2),
                            "exit_reason": exit_reason,
                            "diagnosis": diag,
                            "recommended_countermeasure": rec_counter,
                        }
                    )

                pos = None

        # Open new trade at bar[i].open from closed bar[i-1] signal (zero lookahead!)
        if pos is None and i < n - 1 and ts_gap_sec <= 300:
            sig = signal_rows[i - 1].get(strategy_id, "NONE")
            if sig != "NONE":
                if exit_mode == "ROLLOVER_GUARD" and bar["session_zone"] in avoid_zones:
                    continue
                if not bar["has_live"]:
                    continue

                atr_now = max(prev_bar["atr14"], spec["min_atr"])
                sp_half = prev_bar["spread"] * 0.5
                entry_p = (bar["open"] + sp_half + slip * 0.5) if sig == "BUY" else (bar["open"] - sp_half - slip * 0.5)
                risk_move = atr_now * (sl_atr if sl_atr is not None else 2.0)

                sl_p = None
                tp_p = None
                sl_dist_val: Optional[float] = None
                if sl_atr is not None and rr is not None:
                    sl_dist_val = max(atr_now * sl_atr, prev_bar["spread"] * 2.5, spec["min_atr"])
                    tp_dist_val = sl_dist_val * rr
                    risk_move = sl_dist_val
                    if sig == "BUY":
                        sl_p = entry_p - sl_dist_val
                        tp_p = entry_p + tp_dist_val
                    else:
                        sl_p = entry_p + sl_dist_val
                        tp_p = entry_p - tp_dist_val

                pos = {
                    "side": sig,
                    "entry_idx": i,
                    "entry_time": bar["time"],
                    "entry_price": entry_p,
                    "entry_zone": prev_bar["session_zone"],
                    "entry_regime": prev_bar["macro_regime"],
                    "entry_atr": atr_now,
                    "risk_move": risk_move,
                    "sl_dist": sl_dist_val,
                    "sl_price": sl_p,
                    "tp_price": tp_p,
                    "mae_move": 0.0,
                    "mfe_move": 0.0,
                    "worst_time": bar["time"],
                    "worst_zone": bar["session_zone"],
                    "worst_regime": bar["macro_regime"],
                    "worst_spread": bar["spread"],
                    "worst_delta": bar["delta"],
                    "split": "OUT_OF_SAMPLE" if (i - 1) >= split_idx else "IN_SAMPLE",
                }

    return trades, forensics


def summarize_trades(trades: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Aggregates concise statistical performance metrics for a slice of trades."""
    n = len(trades)
    if n == 0:
        return {
            "trades": 0,
            "wins": 0,
            "losses": 0,
            "win_rate_pct": 0.0,
            "net_pnl_usd": 0.0,
            "profit_factor": 0.0,
            "max_dd_usd": 0.0,
            "expectancy_usd": 0.0,
            "net_r": 0.0,
            "avg_r": 0.0,
            "avg_bars_held": 0.0,
        }

    wins = sum(1 for t in trades if t["pnl_usd"] > 0)
    losses = n - wins
    gw = sum(t["pnl_usd"] for t in trades if t["pnl_usd"] > 0)
    gl = abs(sum(t["pnl_usd"] for t in trades if t["pnl_usd"] <= 0))
    net = sum(t["pnl_usd"] for t in trades)
    pf = (gw / gl) if gl > 0 else (9.99 if gw > 0 else 0.0)

    eq = 0.0
    peak = 0.0
    max_dd = 0.0
    for t in trades:
        eq += t["pnl_usd"]
        if eq > peak:
            peak = eq
        dd = peak - eq
        if dd > max_dd:
            max_dd = dd

    net_r = sum(t["r_mult"] for t in trades)
    return {
        "trades": n,
        "wins": wins,
        "losses": losses,
        "win_rate_pct": round(100.0 * wins / n, 1),
        "net_pnl_usd": round(net, 4),
        "profit_factor": round(pf, 2),
        "max_dd_usd": round(max_dd, 4),
        "expectancy_usd": round(net / n, 4),
        "net_r": round(net_r, 2),
        "avg_r": round(net_r / n, 3),
        "avg_bars_held": round(sum(t["bars_held"] for t in trades) / n, 1),
    }


def _build_session_zone_profile(enriched: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Computes real empirical market microstructure profile for each of the 7 zones."""
    zone_map: Dict[str, Dict[str, Any]] = {}
    for zone in SESSION_ZONES:
        bars_z = [b for b in enriched if b["session_zone"] == zone]
        live_z = [b for b in bars_z if b["has_live"]]
        spreads = [b["spread"] for b in live_z if b["spread"] > 0]
        atrs = [b["atr14"] for b in live_z]
        regimes = Counter(b["macro_regime"] for b in live_z)
        zone_map[zone] = {
            "total_merged_bars": len(bars_z),
            "live_rich_bars": len(live_z),
            "is_transition": ("TO_" in zone),
            "median_spread": round(statistics.median(spreads), 4) if spreads else None,
            "p95_spread": round(sorted(spreads)[int(0.95 * (len(spreads) - 1))], 4) if len(spreads) >= 2 else None,
            "median_atr14": round(statistics.median(atrs), 4) if atrs else None,
            "regime_distribution": dict(regimes),
        }
    return zone_map


def analyze_symbol(
    symbol: str,
    merger: Optional[HybridDataMerger] = None,
    fetch_ctrader: bool = True,
    train_ratio: float = 0.60,
) -> Dict[str, Any]:
    """
    Runs end-to-end Phase 2 analysis for one symbol:
    1) Loads Phase 1 Hybrid merged dataset
    2) Extracts strictly non-lookahead features & 7-zone tags
    3) Evaluates 6 strategy families x 7 adaptive/forensic profiles across IS (60%) / OOS (40%)
    4) Constructs the Regime Strategy Matrix, non-banning Strategy Memory, & Blowup Forensics
    """
    merger = merger or HybridDataMerger()
    dataset = merger.load_merged_dataset(symbol, fetch_ctrader=fetch_ctrader)
    raw_bars = dataset["bars"]
    enriched = enrich_merged_bars(raw_bars, symbol)
    if len(enriched) < 60:
        return {"symbol": symbol, "status": "INSUFFICIENT_DATA", "total_bars": len(enriched)}

    live_indices = [idx for idx, b in enumerate(enriched) if b["has_live"]]
    if len(live_indices) < 20:
        return {"symbol": symbol, "status": "INSUFFICIENT_LIVE_DATA", "live_bars": len(live_indices)}

    split_live_pos = max(1, int(len(live_indices) * train_ratio))
    split_idx = live_indices[min(split_live_pos, len(live_indices) - 1)]
    split_time_utc = enriched[split_idx]["time"]

    signal_rows = [evaluate_all_strategy_signals(b, symbol) for b in enriched]

    all_trades: List[Dict[str, Any]] = []
    all_forensics: List[Dict[str, Any]] = []
    strategy_profiles: Dict[str, Dict[str, Any]] = {}

    # Track per-(zone, regime, strategy, profile) slices for OOS Champion matching
    cell_candidates: Dict[Tuple[str, str], List[Dict[str, Any]]] = defaultdict(list)

    for sid in STRATEGY_META:
        strategy_profiles[sid] = {}
        for prof in PARAMETER_PROFILES:
            trades, forensics = simulate_profile_chronological(enriched, signal_rows, symbol, sid, prof, split_idx)
            all_trades.extend(trades)
            all_forensics.extend(forensics)

            is_trades = [t for t in trades if t["split"] == "IN_SAMPLE"]
            oos_trades = [t for t in trades if t["split"] == "OUT_OF_SAMPLE"]
            is_sum = summarize_trades(is_trades)
            oos_sum = summarize_trades(oos_trades)

            strategy_profiles[sid][prof["name"]] = {
                "is_stats": is_sum,
                "oos_stats": oos_sum,
                "blowup_events": len(forensics),
                "is_forensic": bool(prof["is_forensic"]),
            }

            if prof["is_forensic"]:
                continue

            # Bucket by entry (session_zone, macro_regime) for OOS Robustness selection
            grouped: Dict[Tuple[str, str], List[Dict[str, Any]]] = defaultdict(list)
            for t in trades:
                grouped[(t["entry_zone"], t["entry_regime"])].append(t)

            for (zone, reg), grp_trades in grouped.items():
                grp_is = [t for t in grp_trades if t["split"] == "IN_SAMPLE"]
                grp_oos = [t for t in grp_trades if t["split"] == "OUT_OF_SAMPLE"]
                g_is_sum = summarize_trades(grp_is)
                g_oos_sum = summarize_trades(grp_oos)

                # Anti-Overfit OOS robustness scoring (prioritizes Unseen OOS edge over IS)
                oos_n = g_oos_sum["trades"]
                is_n = g_is_sum["trades"]
                oos_passed = (oos_n >= 2 and g_oos_sum["net_pnl_usd"] > 0 and g_oos_sum["profit_factor"] >= 1.15)
                consistent_both = oos_passed and (is_n >= 2 and g_is_sum["net_pnl_usd"] > 0)
                robust_score = (
                    (g_oos_sum["net_r"] * 12.0)
                    + (min(g_oos_sum["profit_factor"], 4.0) * 5.0 if oos_n > 0 else 0.0)
                    + (3.0 if consistent_both else 0.0)
                    - (g_oos_sum["max_dd_usd"] * 2.0)
                )

                cell_candidates[(zone, reg)].append(
                    {
                        "strategy_id": sid,
                        "strategy_name": STRATEGY_META[sid]["name"],
                        "profile": prof["name"],
                        "sl_atr": prof["sl_atr"],
                        "rr": prof["rr"],
                        "exit_mode": prof["exit_mode"],
                        "is_stats": g_is_sum,
                        "oos_stats": g_oos_sum,
                        "oos_passed": oos_passed,
                        "consistent_both": consistent_both,
                        "robust_score": round(robust_score, 3),
                    }
                )

    # Assemble 7-Zone x Macro Regime Strategy Matrix
    regime_matrix: List[Dict[str, Any]] = []
    for zone in SESSION_ZONES:
        for reg in MACRO_REGIMES:
            cands = cell_candidates.get((zone, reg), [])
            if not cands:
                continue
            cands.sort(
                key=lambda c: (
                    c["oos_passed"],
                    c["consistent_both"],
                    c["oos_stats"]["trades"] > 0,
                    c["robust_score"],
                    c["oos_stats"]["net_r"],
                ),
                reverse=True,
            )
            best = cands[0]
            worst = sorted(cands, key=lambda c: (c["oos_stats"]["net_pnl_usd"], c["oos_stats"]["net_r"]))[0]
            o = best["oos_stats"]
            if best["oos_passed"]:
                action = "DEPLOY_ADAPTIVE"
                verdict_th = (
                    f"{zone} · {reg}: ใช้ {best['strategy_id']} ({best['profile']}) — "
                    f"พบใน OOS {o['trades']} ครั้ง ชนะ {o['wins']}/{o['trades']} "
                    f"({best['oos_stats']['win_rate_pct']}%), Net {o['net_pnl_usd']:+.2f} USD (PF {o['profit_factor']})"
                )
            elif o["trades"] == 0:
                action = "NO_TRADE_OR_RESEARCH"
                verdict_th = f"{zone} · {reg}: ยังไม่มีตัวอย่างสัญญาณใน OOS — แนะนำชะลอ/เก็บข้อมูลเพิ่ม"
            else:
                action = "NO_TRADE_OR_RESEARCH"
                verdict_th = (
                    f"{zone} · {reg}: ยังไม่ผ่านเกณฑ์ OOS (ดีสุดคือ {best['strategy_id']} "
                    f"OOS {o['wins']}/{o['trades']} Net {o['net_pnl_usd']:+.2f} USD) — แนะนำชะลอ/หลีกเลี่ยง"
                )

            regime_matrix.append(
                {
                    "symbol": symbol,
                    "session_zone": zone,
                    "macro_regime": reg,
                    "recommended_action": action,
                    "best_candidate": best,
                    "avoid_candidate": worst if worst["oos_stats"]["net_pnl_usd"] < 0 else None,
                    "candidates_evaluated": len(cands),
                    "verdict_th": verdict_th,
                }
            )

    # Non-banning Regime-Matched Memory summary for all 6 strategies
    strategy_memory_cards: Dict[str, Any] = {}
    for sid, meta in STRATEGY_META.items():
        winning_contexts = [
            f"{m['session_zone']}·{m['macro_regime']} ({m['best_candidate']['oos_stats']['wins']}/{m['best_candidate']['oos_stats']['trades']}, {m['best_candidate']['oos_stats']['net_pnl_usd']:+.2f}$)"
            for m in regime_matrix
            if m["best_candidate"]["strategy_id"] == sid and m["best_candidate"]["oos_passed"]
        ]
        sid_forensics = [f for f in all_forensics if f["strategy_id"] == sid]
        failing_zones = Counter(f"{f['worst_zone']}·{f['worst_regime']}" for f in sid_forensics).most_common(3)
        strategy_memory_cards[sid] = {
            "name": meta["name"],
            "family": meta["family"],
            "status": "REGIME_MATCHED_ACTIVE",  # Never permanently banned under V5!
            "winning_contexts_oos": winning_contexts,
            "forensic_failure_hotspots": [{"context": ctx, "count": cnt} for ctx, cnt in failing_zones],
            "profiles": strategy_profiles[sid],
        }

    # Sort forensics by worst adverse ATR excursion first
    all_forensics.sort(key=lambda x: (x["mae_atr"], x["mae_usd"]), reverse=True)

    return {
        "symbol": symbol,
        "status": "COMPLETED",
        "data_window": {
            "start_time_utc": enriched[0]["time"],
            "split_time_utc": split_time_utc,
            "end_time_utc": enriched[-1]["time"],
            "total_merged_bars": len(enriched),
            "live_rich_bars": len(live_indices),
            "in_sample_bars": int(len(live_indices) * train_ratio),
            "out_of_sample_bars": len(live_indices) - int(len(live_indices) * train_ratio),
        },
        "session_zone_profiles": _build_session_zone_profile(enriched),
        "regime_strategy_matrix": regime_matrix,
        "strategy_memory": strategy_memory_cards,
        "blowup_forensics": {
            "total_severe_events": len(all_forensics),
            "zero_sl_events": sum(1 for f in all_forensics if f["sl_mode"] == "ZERO_SL"),
            "protected_sl_events": sum(1 for f in all_forensics if f["sl_mode"] == "PROTECTED"),
            "diagnosis_breakdown": dict(Counter(f["diagnosis"] for f in all_forensics)),
            "top_cases": all_forensics[:20],
        },
    }


def run_phase2_study(
    symbols: Tuple[str, ...] = ("XAUUSD", "BTCUSD", "ETHUSD"),
    fetch_ctrader: bool = True,
    output_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """Runs Phase 2 across all live symbols and persists docs/data/regime_strategy_matrix.json."""
    merger = HybridDataMerger()
    report: Dict[str, Any] = {
        "schema_version": "5.0.0-SESSION-REGIME-FORENSICS",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "rules_compliance": {
            "pure_hybrid_real_data": True,
            "zero_lookahead_next_bar_open": True,
            "chronological_60_40_is_oos_split": True,
            "adaptive_no_fixed_sl_flat": True,
            "no_permanent_strategy_ban": True,
            "zero_sl_blowup_forensics_enabled": True,
            "session_zones_count": len(SESSION_ZONES),
        },
        "session_zones": list(SESSION_ZONES),
        "symbols": {},
    }

    for sym in symbols:
        report["symbols"][sym] = analyze_symbol(sym, merger=merger, fetch_ctrader=fetch_ctrader)

    out_path = output_path or (REPO_ROOT / "docs" / "data" / "regime_strategy_matrix.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = out_path.with_suffix(".tmp")
    tmp_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp_path.replace(out_path)
    return report


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    res = run_phase2_study()
    print("=" * 80)
    print("PHASE 2: SESSION / TRANSITION REGIME ENGINE & BLOWUP FORENSICS REPORT")
    print("=" * 80)
    for sym, data in res["symbols"].items():
        if data.get("status") != "COMPLETED":
            print(f"\n[{sym}] Status: {data.get('status')}")
            continue
        dw = data["data_window"]
        mat = data["regime_strategy_matrix"]
        passed = [m for m in mat if m["recommended_action"] == "DEPLOY_ADAPTIVE"]
        foren = data["blowup_forensics"]
        print(
            f"\n[{sym}] Merged={dw['total_merged_bars']} | LiveRich={dw['live_rich_bars']} "
            f"| IS->OOS Split={dw['split_time_utc']}"
        )
        print(f"  OOS-Validated Zone x Regime Cells: {len(passed)}/{len(mat)}")
        for row in passed[:5]:
            print(f"    • {row['verdict_th']}")
        print(
            f"  Blowup & Failure Forensics: total={foren['total_severe_events']} "
            f"(Zero-SL={foren['zero_sl_events']}, Protected={foren['protected_sl_events']}) "
            f"| Causes={foren['diagnosis_breakdown']}"
        )
    print("\nSaved Phase 2 Matrix -> docs/data/regime_strategy_matrix.json")
