"""
Causal Dual-HTF & Microstructure Data Loader (Step 2)
=====================================================
Fuses Tier 1 Sanitized Live Microstructure (M1 + L2 DOM 25 levels + Order Flow + Real Spread)
with Tier 2 cTrader Real Multi-Timeframe OHLCV (m5, m15, h1, h4) scoped to the live window
plus an HTF warmup buffer.

Strict Guarantees:
1. Zero Future Lookahead:
   - Closed HTF bar index k satisfies `tf_open_ts[k] + tf_sec <= m1_ts[i] + 60`.
   - Developing HTF bar accumulates strictly M1 bars inside `[bucket_start .. i]`.
   - Rolling session-normalized Z-scores look strictly at bars `<= i`.
2. Conservative Gap Guard:
   - Any horizon `[i+1 .. i+h]` bridging a weekend or >10m data outage is marked invalid (`False`),
     preventing artificial weekend price jumps from inflating MFE/MAE or probabilities.
"""

from __future__ import annotations

import bisect
import math
import sys
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Deque, Dict, List, Optional, Tuple

import numpy as np
from numpy.lib.stride_tricks import sliding_window_view

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from research.hybrid_data_merger import HybridDataMerger, classify_session_zone
from research.session_regime_forensics import ASSET_SPECS

TF_SECONDS: Dict[str, int] = {
    "m1": 60,
    "m5": 300,
    "m15": 900,
    "h1": 3600,
    "h4": 14400,
}

HORIZONS: Tuple[int, ...] = (5, 15, 30, 60)


def _f(val: Any, default: float = 0.0) -> float:
    if val is None or val == "":
        return default
    try:
        x = float(val)
        return x if math.isfinite(x) else default
    except (ValueError, TypeError):
        return default


def _nan_f(val: Any) -> float:
    if val is None or val == "":
        return float("nan")
    try:
        x = float(val)
        return x if math.isfinite(x) else float("nan")
    except (ValueError, TypeError):
        return float("nan")


def parse_ts_unix(bar: Dict[str, Any]) -> int:
    ts = bar.get("ts_unix")
    if ts is not None:
        return int(ts)
    t_str = str(bar.get("time", "")).strip()
    dt = datetime.strptime(t_str[:16], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
    return int(dt.timestamp())


def resample_m1_to_tf(m1_bars: List[Dict[str, Any]], tf_sec: int) -> List[Dict[str, Any]]:
    """Causally aggregates M1 OHLCV bars into higher-timeframe buckets."""
    buckets: Dict[int, Dict[str, Any]] = {}
    for b in m1_bars:
        ts = parse_ts_unix(b)
        b_ts = (ts // tf_sec) * tf_sec
        o = _f(b.get("open"))
        h = _f(b.get("high"), o)
        l = _f(b.get("low"), o)
        c = _f(b.get("close"), o)
        v = _f(b.get("tickVolume"), 0.0)
        cur = buckets.get(b_ts)
        if cur is None:
            dt_str = datetime.fromtimestamp(b_ts, tz=timezone.utc).strftime("%Y-%m-%d %H:%M")
            buckets[b_ts] = {
                "ts_unix": b_ts,
                "time": dt_str,
                "open": o,
                "high": h,
                "low": l,
                "close": c,
                "tickVolume": v,
            }
        else:
            if h > cur["high"]:
                cur["high"] = h
            if l < cur["low"]:
                cur["low"] = l
            cur["close"] = c
            cur["tickVolume"] += v
    return [buckets[k] for k in sorted(buckets.keys())]


def compute_causal_tf_indicators(
    bars: List[Dict[str, Any]],
    symbol: str,
    is_m1: bool = False,
) -> Dict[str, Any]:
    """
    Computes purely backward-looking technical indicators, volatility regimes,
    macro regimes, and (for M1) session-normalized microstructure Z-scores.
    """
    n = len(bars)
    spec = ASSET_SPECS.get(symbol, ASSET_SPECS["XAUUSD"])
    default_sp = float(spec["default_spread"])
    min_atr_floor = float(spec["min_atr"]) * 0.25

    ts_unix = np.zeros(n, dtype=np.int64)
    time_strs: List[str] = [""] * n
    op = np.zeros(n, dtype=np.float64)
    hi = np.zeros(n, dtype=np.float64)
    lo = np.zeros(n, dtype=np.float64)
    cl = np.zeros(n, dtype=np.float64)
    vol = np.zeros(n, dtype=np.float64)

    ema20 = np.zeros(n, dtype=np.float64)
    ema50 = np.zeros(n, dtype=np.float64)
    ema200 = np.zeros(n, dtype=np.float64)
    atr14 = np.zeros(n, dtype=np.float64)
    atr60_mean = np.zeros(n, dtype=np.float64)
    rsi14 = np.full(n, 50.0, dtype=np.float64)
    macd_hist = np.zeros(n, dtype=np.float64)
    stoch_k = np.full(n, 50.0, dtype=np.float64)
    adx14 = np.zeros(n, dtype=np.float64)
    body_ratio = np.zeros(n, dtype=np.float64)
    upper_wick_ratio = np.zeros(n, dtype=np.float64)
    lower_wick_ratio = np.zeros(n, dtype=np.float64)
    range_atr = np.zeros(n, dtype=np.float64)
    prev_hh20 = np.zeros(n, dtype=np.float64)
    prev_ll20 = np.zeros(n, dtype=np.float64)

    macro_regime = np.empty(n, dtype=object)
    vol_regime = np.empty(n, dtype=object)
    session_zone = np.empty(n, dtype=object)

    # Microstructure & reference level arrays (M1)
    has_l2_dom = np.zeros(n, dtype=bool)
    has_order_flow = np.zeros(n, dtype=bool)
    has_real_spread = np.zeros(n, dtype=bool)
    is_live_full = np.zeros(n, dtype=bool)

    spread_avg = np.full(n, np.nan, dtype=np.float64)
    spread_max = np.full(n, np.nan, dtype=np.float64)
    imbalance = np.full(n, np.nan, dtype=np.float64)
    delta = np.full(n, np.nan, dtype=np.float64)
    cvd = np.full(n, np.nan, dtype=np.float64)
    bid_vol = np.full(n, np.nan, dtype=np.float64)
    ask_vol = np.full(n, np.nan, dtype=np.float64)
    vwap_day = np.zeros(n, dtype=np.float64)
    sd_day = np.ones(n, dtype=np.float64)
    vwap_session = np.zeros(n, dtype=np.float64)

    poc = np.full(n, np.nan, dtype=np.float64)
    vah = np.full(n, np.nan, dtype=np.float64)
    val = np.full(n, np.nan, dtype=np.float64)
    prev_high = np.full(n, np.nan, dtype=np.float64)
    prev_low = np.full(n, np.nan, dtype=np.float64)
    day_high = np.full(n, np.nan, dtype=np.float64)
    day_low = np.full(n, np.nan, dtype=np.float64)
    asia_high = np.full(n, np.nan, dtype=np.float64)
    asia_low = np.full(n, np.nan, dtype=np.float64)
    high60 = np.full(n, np.nan, dtype=np.float64)
    low60 = np.full(n, np.nan, dtype=np.float64)

    vol_z_session = np.zeros(n, dtype=np.float64)
    spread_z_session = np.zeros(n, dtype=np.float64)
    delta_z_session = np.zeros(n, dtype=np.float64)
    imb_z_session = np.zeros(n, dtype=np.float64)
    range_z_session = np.zeros(n, dtype=np.float64)
    vwap_z = np.zeros(n, dtype=np.float64)
    cvd_slope5 = np.zeros(n, dtype=np.float64)
    price_slope5 = np.zeros(n, dtype=np.float64)
    accel_atr = np.zeros(n, dtype=np.float64)

    # Round 2 Deep Microstructure arrays
    depth_updates = np.full(n, np.nan, dtype=np.float64)
    depth_z_session = np.zeros(n, dtype=np.float64)
    ladder_bid = np.full(n, np.nan, dtype=np.float64)
    ladder_ask = np.full(n, np.nan, dtype=np.float64)
    ladder_asym = np.full(n, np.nan, dtype=np.float64)
    ladder_asym_z_session = np.zeros(n, dtype=np.float64)
    book_vol_total = np.full(n, np.nan, dtype=np.float64)
    book_vol_z_session = np.zeros(n, dtype=np.float64)
    spread_spike_ratio = np.ones(n, dtype=np.float64)
    imb_z_delta = np.zeros(n, dtype=np.float64)
    live_sweep_high = np.zeros(n, dtype=bool)
    live_sweep_low = np.zeros(n, dtype=bool)

    if n == 0:
        return {
            "n": 0,
            "ts_unix": ts_unix,
            "time_strs": time_strs,
            "open": op,
            "high": hi,
            "low": lo,
            "close": cl,
            "volume": vol,
            "ema20": ema20,
            "ema50": ema50,
            "ema200": ema200,
            "atr14": atr14,
            "atr60_mean": atr60_mean,
            "rsi14": rsi14,
            "macd_hist": macd_hist,
            "stoch_k": stoch_k,
            "adx14": adx14,
            "body_ratio": body_ratio,
            "upper_wick_ratio": upper_wick_ratio,
            "lower_wick_ratio": lower_wick_ratio,
            "range_atr": range_atr,
            "prev_hh20": prev_hh20,
            "prev_ll20": prev_ll20,
            "macro_regime": macro_regime,
            "vol_regime": vol_regime,
            "session_zone": session_zone,
            "has_l2_dom": has_l2_dom,
            "has_order_flow": has_order_flow,
            "has_real_spread": has_real_spread,
            "is_live_full": is_live_full,
            "spread_avg": spread_avg,
            "spread_max": spread_max,
            "imbalance": imbalance,
            "delta": delta,
            "cvd": cvd,
            "bid_vol": bid_vol,
            "ask_vol": ask_vol,
            "vwap_day": vwap_day,
            "sd_day": sd_day,
            "vwap_session": vwap_session,
            "poc": poc,
            "vah": vah,
            "val": val,
            "prev_high": prev_high,
            "prev_low": prev_low,
            "day_high": day_high,
            "day_low": day_low,
            "asia_high": asia_high,
            "asia_low": asia_low,
            "high60": high60,
            "low60": low60,
            "vol_z_session": vol_z_session,
            "spread_z_session": spread_z_session,
            "delta_z_session": delta_z_session,
            "imb_z_session": imb_z_session,
            "range_z_session": range_z_session,
            "vwap_z": vwap_z,
            "cvd_slope5": cvd_slope5,
            "price_slope5": price_slope5,
            "accel_atr": accel_atr,
            "depth_updates": depth_updates,
            "depth_z_session": depth_z_session,
            "ladder_bid": ladder_bid,
            "ladder_ask": ladder_ask,
            "ladder_asym": ladder_asym,
            "ladder_asym_z_session": ladder_asym_z_session,
            "book_vol_total": book_vol_total,
            "book_vol_z_session": book_vol_z_session,
            "spread_spike_ratio": spread_spike_ratio,
            "imb_z_delta": imb_z_delta,
            "live_sweep_high": live_sweep_high,
            "live_sweep_low": live_sweep_low,
        }

    # Causal rolling helpers
    tr_win: Deque[float] = deque(maxlen=14)
    atr_win60: Deque[float] = deque(maxlen=60)
    atr_win240_raw: Deque[float] = deque()
    atr_win240_sorted: List[float] = []
    live_sp_hist: Deque[float] = deque(maxlen=120)

    # Session-separated rolling rings (maxlen 120 per zone) for Z-scores
    sess_vol_hist: Dict[str, Deque[float]] = defaultdict(lambda: deque(maxlen=120))
    sess_sp_hist: Dict[str, Deque[float]] = defaultdict(lambda: deque(maxlen=120))
    sess_delta_hist: Dict[str, Deque[float]] = defaultdict(lambda: deque(maxlen=120))
    sess_imb_hist: Dict[str, Deque[float]] = defaultdict(lambda: deque(maxlen=120))
    sess_rng_hist: Dict[str, Deque[float]] = defaultdict(lambda: deque(maxlen=120))
    sess_du_hist: Dict[str, Deque[float]] = defaultdict(lambda: deque(maxlen=120))
    sess_bvol_hist: Dict[str, Deque[float]] = defaultdict(lambda: deque(maxlen=120))
    sess_lasym_hist: Dict[str, Deque[float]] = defaultdict(lambda: deque(maxlen=120))
    dx_win: Deque[float] = deque(maxlen=14)
    stoch_raw_win: Deque[float] = deque(maxlen=3)

    e20 = _f(bars[0].get("close"))
    e50 = e20
    e200 = e20
    e12 = e20
    e26 = e20
    macd_sig = 0.0
    prev_c = e20
    prev_h = _f(bars[0].get("high"), e20)
    prev_l = _f(bars[0].get("low"), e20)
    tr_s = max(prev_h - prev_l, min_atr_floor)
    pdm_s = 0.0
    mdm_s = 0.0
    avg_gain = 0.0
    avg_loss = 0.0

    cur_day = ""
    cum_pv = 0.0
    cum_v = 0.0
    day_var_m2 = 0.0
    day_count = 0

    def _causal_z(hist: Deque[float], val: float) -> float:
        if len(hist) < 15:
            return 0.0
        arr = np.fromiter(hist, dtype=np.float64, count=len(hist))
        mu = float(arr.mean())
        sd = float(arr.std())
        if sd <= 1e-9:
            return 0.0
        return (val - mu) / sd

    for i, b in enumerate(bars):
        t_unix = parse_ts_unix(b)
        t_str = str(b.get("time") or "")
        if not t_str:
            t_str = datetime.fromtimestamp(t_unix, tz=timezone.utc).strftime("%Y-%m-%d %H:%M")

        o = _f(b.get("open"))
        h = _f(b.get("high"), o)
        l = _f(b.get("low"), o)
        c = _f(b.get("close"), o)
        v = _f(b.get("tickVolume"), 0.0)

        ts_unix[i] = t_unix
        time_strs[i] = t_str
        op[i] = o
        hi[i] = h
        lo[i] = l
        cl[i] = c
        vol[i] = v

        # EMAs & MACD
        if i == 0:
            e20 = e50 = e200 = e12 = e26 = c
            macd_sig = 0.0
        else:
            e20 = c * (2.0 / 21.0) + e20 * (19.0 / 21.0)
            e50 = c * (2.0 / 51.0) + e50 * (49.0 / 51.0)
            e200 = c * (2.0 / 201.0) + e200 * (199.0 / 201.0)
            e12 = c * (2.0 / 13.0) + e12 * (11.0 / 13.0)
            e26 = c * (2.0 / 27.0) + e26 * (25.0 / 27.0)
            macd_line = e12 - e26
            macd_sig = macd_line * (2.0 / 10.0) + macd_sig * (8.0 / 10.0)
        ema20[i] = e20
        ema50[i] = e50
        ema200[i] = e200
        macd_hist[i] = (e12 - e26) - macd_sig

        # ATR14 & ATR60 mean
        tr = max(h - l, abs(h - prev_c), abs(l - prev_c))
        tr_win.append(tr)
        cur_atr = max(sum(tr_win) / len(tr_win), min_atr_floor)
        atr14[i] = cur_atr
        atr_win60.append(cur_atr)
        cur_atr60 = sum(atr_win60) / len(atr_win60)
        atr60_mean[i] = cur_atr60

        # Vol regime via causal O(log 240) rolling window
        if len(atr_win240_raw) >= 240:
            old_v = atr_win240_raw.popleft()
            rm_idx = bisect.bisect_left(atr_win240_sorted, old_v)
            if rm_idx < len(atr_win240_sorted):
                atr_win240_sorted.pop(rm_idx)
        atr_win240_raw.append(cur_atr)
        bisect.insort(atr_win240_sorted, cur_atr)
        if len(atr_win240_sorted) < 20:
            vol_regime[i] = "NORMAL"
        else:
            rank_pos = bisect.bisect_right(atr_win240_sorted, cur_atr) / len(atr_win240_sorted)
            if rank_pos <= 0.33:
                vol_regime[i] = "LOW"
            elif rank_pos >= 0.67:
                vol_regime[i] = "HIGH"
            else:
                vol_regime[i] = "NORMAL"

        # Wilder RSI14
        chg = c - prev_c if i > 0 else 0.0
        gain = chg if chg > 0 else 0.0
        loss = -chg if chg < 0 else 0.0
        if i == 0:
            avg_gain = gain
            avg_loss = loss
        elif i < 14:
            avg_gain = (avg_gain * i + gain) / (i + 1)
            avg_loss = (avg_loss * i + loss) / (i + 1)
        else:
            avg_gain = (avg_gain * 13.0 + gain) / 14.0
            avg_loss = (avg_loss * 13.0 + loss) / 14.0
        if avg_loss <= 1e-12:
            rsi14[i] = 100.0 if avg_gain > 0 else 50.0
        else:
            rs = avg_gain / avg_loss
            rsi14[i] = 100.0 - (100.0 / (1.0 + rs))

        # Wilder ADX14
        up_move = h - prev_h
        down_move = prev_l - l
        pdm = up_move if (up_move > down_move and up_move > 0) else 0.0
        mdm = down_move if (down_move > up_move and down_move > 0) else 0.0
        if i == 0:
            tr_s = max(tr, 1e-6)
            pdm_s = pdm
            mdm_s = mdm
        else:
            tr_s = (tr_s * 13.0 + tr) / 14.0
            pdm_s = (pdm_s * 13.0 + pdm) / 14.0
            mdm_s = (mdm_s * 13.0 + mdm) / 14.0
        pdi = 100.0 * pdm_s / max(tr_s, 1e-6)
        mdi = 100.0 * mdm_s / max(tr_s, 1e-6)
        dx = 100.0 * abs(pdi - mdi) / max(pdi + mdi, 1e-6)
        dx_win.append(dx)
        cur_adx = sum(dx_win) / len(dx_win)
        adx14[i] = cur_adx

        # Candle geometry
        rng = max(h - l, 1e-9)
        body_ratio[i] = abs(c - o) / rng
        upper_wick_ratio[i] = max(0.0, h - max(o, c)) / rng
        lower_wick_ratio[i] = max(0.0, min(o, c) - l) / rng
        range_atr[i] = (h - l) / cur_atr

        # Lookback HH20/LL20 strictly prior to bar i (`[i-20 : i]`)
        if i > 0:
            p_hh20 = float(hi[max(0, i - 20) : i].max())
            p_ll20 = float(lo[max(0, i - 20) : i].min())
        else:
            p_hh20, p_ll20 = h, l
        prev_hh20[i] = p_hh20
        prev_ll20[i] = p_ll20

        # Stochastic 14 smoothed 3
        hh14 = float(hi[max(0, i - 13) : i + 1].max())
        ll14 = float(lo[max(0, i - 13) : i + 1].min())
        raw_k = 100.0 * (c - ll14) / max(hh14 - ll14, 1e-9)
        stoch_raw_win.append(raw_k)
        stoch_k[i] = sum(stoch_raw_win) / len(stoch_raw_win)

        # Bollinger bandwidth on last 20 closes
        w20 = cl[max(0, i - 19) : i + 1]
        bb_mid = float(w20.mean())
        bb_sd = float(w20.std())
        bb_bw = (4.0 * bb_sd) / max(abs(bb_mid), 1e-6)

        # Session classification
        sz = b.get("session_zone")
        if not sz:
            sz, _ = classify_session_zone(datetime.fromtimestamp(t_unix, tz=timezone.utc))
        session_zone[i] = sz

        # Fallback intraday VWAP
        day_str = t_str[:10]
        if day_str != cur_day:
            cur_day = day_str
            cum_pv = 0.0
            cum_v = 0.0
            day_var_m2 = 0.0
            day_count = 0
        v_eff = max(v, 1.0)
        cum_pv += ((h + l + c) / 3.0) * v_eff
        cum_v += v_eff
        day_count += 1
        fb_vwap = cum_pv / cum_v if cum_v > 0 else c
        day_var_m2 += (c - fb_vwap) ** 2
        fb_sd = max(math.sqrt(day_var_m2 / max(1, day_count)), cur_atr * 1.2)

        l2 = bool(b.get("has_l2_dom")) and bool(b.get("has_real_spread"))
        sp_val = _f(b.get("spreadAvg"), default_sp) if l2 else default_sp
        if l2 and sp_val > 0:
            live_sp_hist.append(sp_val)
        med_sp = float(np.median(np.fromiter(live_sp_hist, dtype=np.float64))) if live_sp_hist else default_sp

        next_imp = str(b.get("nextImpact", "")).upper()
        last_imp = str(b.get("lastImpact", "")).upper()
        min_to_next = _f(b.get("minToNext"), 999.0)
        min_since_last = _f(b.get("minSinceLast"), 999.0)
        is_news_void = (min_to_next <= 30.0 and next_imp in ("HIGH", "EXTREME")) or (
            min_since_last <= 15.0 and last_imp in ("HIGH", "EXTREME")
        )
        is_thin = l2 and (sp_val > max(med_sp * 2.2, float(spec["rollover_spread_warn"]) * 0.95))

        if is_news_void or is_thin:
            macro_regime[i] = "THIN_OR_NEWS"
        elif cur_adx >= 24.0 and e50 > e200 and c > e50:
            macro_regime[i] = "TREND_BULL"
        elif cur_adx >= 24.0 and e50 < e200 and c < e50:
            macro_regime[i] = "TREND_BEAR"
        elif (c > p_hh20 or c < p_ll20) and (cur_atr >= cur_atr60 * 1.15 or bb_bw >= 0.0032):
            macro_regime[i] = "BREAKOUT"
        else:
            macro_regime[i] = "RANGE"

        if is_m1:
            has_l2 = bool(b.get("has_l2_dom"))
            has_sp = bool(b.get("has_real_spread"))
            has_of = bool(b.get("has_order_flow"))
            has_l2_dom[i] = has_l2
            has_real_spread[i] = has_sp
            has_order_flow[i] = has_of
            is_live_full[i] = has_l2 and has_sp and has_of

            if has_sp:
                spread_avg[i] = _nan_f(b.get("spreadAvg"))
                spread_max[i] = _nan_f(b.get("spreadMax"))
            if has_l2:
                imbalance[i] = _nan_f(b.get("imbalance"))
                bid_vol[i] = _nan_f(b.get("bidVol"))
                ask_vol[i] = _nan_f(b.get("askVol"))
            if has_of:
                delta[i] = _nan_f(b.get("delta"))
                cvd[i] = _nan_f(b.get("cvd"))

            vw_val = _f(b.get("vwapDay"), 0.0)
            vwap_day[i] = vw_val if vw_val > 0 else fb_vwap
            sd_val = _f(b.get("sdDay"), 0.0)
            sd_day[i] = sd_val if sd_val > 0 else fb_sd
            vws_val = _f(b.get("vwapSession"), 0.0)
            vwap_session[i] = vws_val if vws_val > 0 else vwap_day[i]

            poc[i] = _nan_f(b.get("poc"))
            vah[i] = _nan_f(b.get("vah"))
            val[i] = _nan_f(b.get("val"))
            prev_high[i] = _nan_f(b.get("prevHigh"))
            prev_low[i] = _nan_f(b.get("prevLow"))
            day_high[i] = _nan_f(b.get("dayHigh"))
            day_low[i] = _nan_f(b.get("dayLow"))
            asia_high[i] = _nan_f(b.get("asiaHigh"))
            asia_low[i] = _nan_f(b.get("asiaLow"))
            high60[i] = _nan_f(b.get("high60"))
            low60[i] = _nan_f(b.get("low60"))

            vwap_z[i] = (c - vwap_day[i]) / max(sd_day[i], cur_atr * 0.5, 1e-6)

            # Session-normalized rolling Z-scores (computed BEFORE appending i -> strictly causal)
            vol_z_session[i] = _causal_z(sess_vol_hist[sz], v)
            sess_vol_hist[sz].append(v)

            range_z_session[i] = _causal_z(sess_rng_hist[sz], range_atr[i])
            sess_rng_hist[sz].append(range_atr[i])

            if has_sp and math.isfinite(spread_avg[i]):
                spread_z_session[i] = _causal_z(sess_sp_hist[sz], spread_avg[i])
                sess_sp_hist[sz].append(spread_avg[i])
                if spread_avg[i] > 0 and math.isfinite(spread_max[i]):
                    spread_spike_ratio[i] = spread_max[i] / spread_avg[i]

            if has_l2:
                if math.isfinite(imbalance[i]):
                    imb_z_session[i] = _causal_z(sess_imb_hist[sz], imbalance[i])
                    sess_imb_hist[sz].append(imbalance[i])
                    if i > 0 and has_l2_dom[i - 1]:
                        imb_z_delta[i] = imb_z_session[i] - imb_z_session[i - 1]
                du = _nan_f(b.get("depthUpdates"))
                depth_updates[i] = du
                if math.isfinite(du) and du > 0:
                    depth_z_session[i] = _causal_z(sess_du_hist[sz], du)
                    sess_du_hist[sz].append(du)
                bv = bid_vol[i]
                av = ask_vol[i]
                if math.isfinite(bv) and math.isfinite(av) and (bv + av) > 0:
                    btot = bv + av
                    book_vol_total[i] = btot
                    book_vol_z_session[i] = _causal_z(sess_bvol_hist[sz], btot)
                    sess_bvol_hist[sz].append(btot)

            if has_of:
                if math.isfinite(delta[i]):
                    delta_z_session[i] = _causal_z(sess_delta_hist[sz], delta[i])
                    # Causal 5-bar CVD slope normalized by recent session delta std
                    if i >= 4 and has_order_flow[i - 4] and math.isfinite(cvd[i - 4]):
                        d_arr = np.fromiter(sess_delta_hist[sz], dtype=np.float64) if len(sess_delta_hist[sz]) >= 5 else None
                        d_sd = max(float(d_arr.std()), 1.0) if d_arr is not None else max(float(spec["delta_th"]), 1.0)
                        cvd_slope5[i] = (cvd[i] - cvd[i - 4]) / d_sd
                    sess_delta_hist[sz].append(delta[i])
                lb = _nan_f(b.get("ladderBid"))
                la = _nan_f(b.get("ladderAsk"))
                ladder_bid[i] = lb
                ladder_ask[i] = la
                if math.isfinite(lb) and math.isfinite(la) and (lb + la) > 0:
                    asym = (la - lb) / (la + lb)
                    ladder_asym[i] = asym
                    ladder_asym_z_session[i] = _causal_z(sess_lasym_hist[sz], asym)
                    sess_lasym_hist[sz].append(asym)
                sw_str = str(b.get("sweep") or "").upper()
                if sw_str:
                    sw_tokens = {tok.strip() for tok in sw_str.replace(",", "|").split("|") if tok.strip()}
                    live_sweep_high[i] = bool(sw_tokens & {"RH", "PH", "AH"})
                    live_sweep_low[i] = bool(sw_tokens & {"RL", "PL", "AL"})

            if i >= 4:
                price_slope5[i] = (c - cl[i - 4]) / cur_atr
            if i >= 2:
                accel_atr[i] = (c - 2.0 * cl[i - 1] + cl[i - 2]) / cur_atr

        prev_c = c
        prev_h = h
        prev_l = l

    return {
        "n": n,
        "symbol": symbol,
        "ts_unix": ts_unix,
        "time_strs": time_strs,
        "open": op,
        "high": hi,
        "low": lo,
        "close": cl,
        "volume": vol,
        "ema20": ema20,
        "ema50": ema50,
        "ema200": ema200,
        "atr14": atr14,
        "atr60_mean": atr60_mean,
        "rsi14": rsi14,
        "macd_hist": macd_hist,
        "stoch_k": stoch_k,
        "adx14": adx14,
        "body_ratio": body_ratio,
        "upper_wick_ratio": upper_wick_ratio,
        "lower_wick_ratio": lower_wick_ratio,
        "range_atr": range_atr,
        "prev_hh20": prev_hh20,
        "prev_ll20": prev_ll20,
        "macro_regime": macro_regime,
        "vol_regime": vol_regime,
        "session_zone": session_zone,
        "has_l2_dom": has_l2_dom,
        "has_order_flow": has_order_flow,
        "has_real_spread": has_real_spread,
        "is_live_full": is_live_full,
        "spread_avg": spread_avg,
        "spread_max": spread_max,
        "imbalance": imbalance,
        "delta": delta,
        "cvd": cvd,
        "bid_vol": bid_vol,
        "ask_vol": ask_vol,
        "vwap_day": vwap_day,
        "sd_day": sd_day,
        "vwap_session": vwap_session,
        "poc": poc,
        "vah": vah,
        "val": val,
        "prev_high": prev_high,
        "prev_low": prev_low,
        "day_high": day_high,
        "day_low": day_low,
        "asia_high": asia_high,
        "asia_low": asia_low,
        "high60": high60,
        "low60": low60,
        "vol_z_session": vol_z_session,
        "spread_z_session": spread_z_session,
        "delta_z_session": delta_z_session,
        "imb_z_session": imb_z_session,
        "range_z_session": range_z_session,
        "vwap_z": vwap_z,
        "cvd_slope5": cvd_slope5,
        "price_slope5": price_slope5,
        "accel_atr": accel_atr,
        "depth_updates": depth_updates,
        "depth_z_session": depth_z_session,
        "ladder_bid": ladder_bid,
        "ladder_ask": ladder_ask,
        "ladder_asym": ladder_asym,
        "ladder_asym_z_session": ladder_asym_z_session,
        "book_vol_total": book_vol_total,
        "book_vol_z_session": book_vol_z_session,
        "spread_spike_ratio": spread_spike_ratio,
        "imb_z_delta": imb_z_delta,
        "live_sweep_high": live_sweep_high,
        "live_sweep_low": live_sweep_low,
    }


def align_dual_htf_to_m1(
    m1_data: Dict[str, Any],
    tf_data_map: Dict[str, Dict[str, Any]],
) -> Dict[str, Dict[str, Any]]:
    """
    Produces dual causal HTF alignments for every M1 bar i:
      1. `closed_idx`: largest HTF bar k with `tf_ts[k] + tf_sec <= m1_ts[i] + 60` (guaranteed closed).
      2. `dev_*`: Developing HTF candle strictly accumulated from M1 bars `[bucket_start .. i]`.
    Zero future lookahead guaranteed by construction.
    """
    n_m1 = m1_data["n"]
    m1_ts = m1_data["ts_unix"]
    m1_o = m1_data["open"]
    m1_h = m1_data["high"]
    m1_l = m1_data["low"]
    m1_c = m1_data["close"]
    m1_atr = m1_data["atr14"]

    aligned: Dict[str, Dict[str, Any]] = {}
    for tf in ("m5", "m15", "h1", "h4"):
        tf_sec = TF_SECONDS[tf]
        tf_data = tf_data_map.get(tf)
        closed_idx = np.full(n_m1, -1, dtype=np.int64)

        dev_open = np.zeros(n_m1, dtype=np.float64)
        dev_high = np.zeros(n_m1, dtype=np.float64)
        dev_low = np.zeros(n_m1, dtype=np.float64)
        dev_close = np.zeros(n_m1, dtype=np.float64)
        dev_body_ratio = np.zeros(n_m1, dtype=np.float64)
        dev_upper_wick_ratio = np.zeros(n_m1, dtype=np.float64)
        dev_lower_wick_ratio = np.zeros(n_m1, dtype=np.float64)
        dev_ret_atr = np.zeros(n_m1, dtype=np.float64)
        dev_pos_in_range = np.full(n_m1, 0.5, dtype=np.float64)

        tf_ts = tf_data["ts_unix"] if (tf_data and tf_data["n"] > 0) else np.zeros(0, dtype=np.int64)
        tf_atr = tf_data["atr14"] if (tf_data and tf_data["n"] > 0) else np.zeros(0, dtype=np.float64)
        n_tf = len(tf_ts)
        tf_scale = math.sqrt(tf_sec / 60.0)

        ptr = -1
        cur_bucket = -1
        d_o = d_h = d_l = d_c = 0.0

        for i in range(n_m1):
            dec_ts = int(m1_ts[i]) + 60
            while ptr + 1 < n_tf and int(tf_ts[ptr + 1]) + tf_sec <= dec_ts:
                ptr += 1
            if ptr >= 0 and int(tf_ts[ptr]) + tf_sec <= dec_ts:
                closed_idx[i] = ptr

            b_start = (int(m1_ts[i]) // tf_sec) * tf_sec
            if b_start != cur_bucket:
                cur_bucket = b_start
                d_o = float(m1_o[i])
                d_h = float(m1_h[i])
                d_l = float(m1_l[i])
                d_c = float(m1_c[i])
            else:
                if m1_h[i] > d_h:
                    d_h = float(m1_h[i])
                if m1_l[i] < d_l:
                    d_l = float(m1_l[i])
                d_c = float(m1_c[i])

            dev_open[i] = d_o
            dev_high[i] = d_h
            dev_low[i] = d_l
            dev_close[i] = d_c

            d_rng = max(d_h - d_l, 1e-9)
            dev_body_ratio[i] = abs(d_c - d_o) / d_rng
            dev_upper_wick_ratio[i] = max(0.0, d_h - max(d_o, d_c)) / d_rng
            dev_lower_wick_ratio[i] = max(0.0, min(d_o, d_c) - d_l) / d_rng
            dev_pos_in_range[i] = (d_c - d_l) / d_rng

            ref_atr = float(tf_atr[ptr]) if (ptr >= 0 and ptr < n_tf) else float(m1_atr[i]) * tf_scale
            dev_ret_atr[i] = (d_c - d_o) / max(ref_atr, 1e-9)

        aligned[tf] = {
            "closed_idx": closed_idx,
            "dev_open": dev_open,
            "dev_high": dev_high,
            "dev_low": dev_low,
            "dev_close": dev_close,
            "dev_body_ratio": dev_body_ratio,
            "dev_upper_wick_ratio": dev_upper_wick_ratio,
            "dev_lower_wick_ratio": dev_lower_wick_ratio,
            "dev_ret_atr": dev_ret_atr,
            "dev_pos_in_range": dev_pos_in_range,
        }
    return aligned


def precompute_forward_outcomes(
    m1_data: Dict[str, Any],
    horizons: Tuple[int, ...] = HORIZONS,
) -> Dict[int, Dict[str, np.ndarray]]:
    """
    Precomputes vectorized next-bar-open forward returns, MFE, MAE, and first-passage
    order (`+0.75 ATR` hit strictly before `-0.75 ATR`) across multiple bar horizons.
    Marks outcomes spanning weekend/outage gaps invalid.
    """
    n = m1_data["n"]
    ts = m1_data["ts_unix"]
    op = m1_data["open"]
    hi = m1_data["high"]
    lo = m1_data["low"]
    cl = m1_data["close"]
    atr = m1_data["atr14"]

    outcomes: Dict[int, Dict[str, np.ndarray]] = {}
    for h in horizons:
        valid = np.zeros(n, dtype=bool)
        fwd_ret_atr = np.full(n, np.nan, dtype=np.float64)
        mfe_long = np.full(n, np.nan, dtype=np.float64)
        mae_long = np.full(n, np.nan, dtype=np.float64)
        mfe_short = np.full(n, np.nan, dtype=np.float64)
        mae_short = np.full(n, np.nan, dtype=np.float64)
        mfe_first_long = np.zeros(n, dtype=bool)
        mfe_first_short = np.zeros(n, dtype=bool)

        m = n - h
        if m > 0:
            next_op = op[1 : m + 1]
            entry_atr = atr[:m]
            safe_atr = np.maximum(entry_atr, 1e-9)

            entry_gap = ts[1 : m + 1] - ts[:m]
            span_gap = ts[h : m + h] - ts[1 : m + 1]
            v_slice = (entry_gap <= 600) & (span_gap <= h * 180)
            valid[:m] = v_slice

            win_hi = sliding_window_view(hi[1:], h)  # shape (m, h)
            win_lo = sliding_window_view(lo[1:], h)  # shape (m, h)

            fwd_ret_atr[:m] = (cl[h : m + h] - next_op) / safe_atr

            hi_max = win_hi.max(axis=1)
            lo_min = win_lo.min(axis=1)

            mfe_long[:m] = np.maximum(0.0, hi_max - next_op) / safe_atr
            mae_long[:m] = np.maximum(0.0, next_op - lo_min) / safe_atr
            mfe_short[:m] = np.maximum(0.0, next_op - lo_min) / safe_atr
            mae_short[:m] = np.maximum(0.0, hi_max - next_op) / safe_atr

            thresh = 0.75 * safe_atr[:, None]
            tp_long = win_hi >= (next_op[:, None] + thresh)
            sl_long = win_lo <= (next_op[:, None] - thresh)
            has_tp_l = tp_long.any(axis=1)
            has_sl_l = sl_long.any(axis=1)
            idx_tp_l = np.where(has_tp_l, tp_long.argmax(axis=1), h + 1)
            idx_sl_l = np.where(has_sl_l, sl_long.argmax(axis=1), h + 1)
            mfe_first_long[:m] = v_slice & has_tp_l & (idx_tp_l < idx_sl_l)

            tp_short = win_lo <= (next_op[:, None] - thresh)
            sl_short = win_hi >= (next_op[:, None] + thresh)
            has_tp_s = tp_short.any(axis=1)
            has_sl_s = sl_short.any(axis=1)
            idx_tp_s = np.where(has_tp_s, tp_short.argmax(axis=1), h + 1)
            idx_sl_s = np.where(has_sl_s, sl_short.argmax(axis=1), h + 1)
            mfe_first_short[:m] = v_slice & has_tp_s & (idx_tp_s < idx_sl_s)

        outcomes[h] = {
            "valid": valid,
            "fwd_ret_atr": fwd_ret_atr,
            "mfe_long_atr": mfe_long,
            "mae_long_atr": mae_long,
            "mfe_short_atr": mfe_short,
            "mae_short_atr": mae_short,
            "mfe_first_long": mfe_first_long,
            "mfe_first_short": mfe_first_short,
        }
    return outcomes


def build_scalping_mtf_dataset_from_bars(
    symbol: str,
    m1_bars: List[Dict[str, Any]],
    htf_bars_map: Optional[Dict[str, List[Dict[str, Any]]]] = None,
    summary: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Assembles full causal indicators, Dual-HTF alignments, and multi-horizon outcomes from bar lists."""
    m1_data = compute_causal_tf_indicators(m1_bars, symbol=symbol, is_m1=True)

    tf_data_map: Dict[str, Dict[str, Any]] = {}
    tf_sources: Dict[str, str] = {}
    for tf in ("m5", "m15", "h1", "h4"):
        tf_sec = TF_SECONDS[tf]
        ext_bars = (htf_bars_map or {}).get(tf) or []
        if len(ext_bars) >= 20:
            tf_data_map[tf] = compute_causal_tf_indicators(ext_bars, symbol=symbol, is_m1=False)
            tf_sources[tf] = "CTRADER_MCP"
        else:
            res_bars = resample_m1_to_tf(m1_bars, tf_sec)
            tf_data_map[tf] = compute_causal_tf_indicators(res_bars, symbol=symbol, is_m1=False)
            tf_sources[tf] = "M1_RESAMPLED"

    aligned_htf = align_dual_htf_to_m1(m1_data, tf_data_map)
    outcomes = precompute_forward_outcomes(m1_data, horizons=HORIZONS)

    live_indices = np.flatnonzero(m1_data["has_l2_dom"] & m1_data["has_real_spread"])
    is_cutoff_idx = int(live_indices[int(len(live_indices) * 0.60)]) if len(live_indices) >= 10 else int(m1_data["n"] * 0.60)
    is_cutoff_ts = int(m1_data["ts_unix"][min(is_cutoff_idx, max(0, m1_data["n"] - 1))]) if m1_data["n"] > 0 else 0

    return {
        "symbol": symbol,
        "summary": summary or {},
        "tf_sources": tf_sources,
        "m1": m1_data,
        "htf": tf_data_map,
        "aligned_htf": aligned_htf,
        "outcomes": outcomes,
        "is_cutoff_idx": is_cutoff_idx,
        "is_cutoff_ts": is_cutoff_ts,
        "spec": ASSET_SPECS.get(symbol, ASSET_SPECS["XAUUSD"]),
    }


def load_scalping_mtf_dataset(
    symbol: str,
    fetch_ctrader: bool = True,
    htf_warmup_days: int = 21,
    merger: Optional[HybridDataMerger] = None,
) -> Dict[str, Any]:
    """
    Loads sanitized Tier 1 + Tier 2 M1 dataset via HybridDataMerger and enriches
    with Tier 2 cTrader Real Multi-TF OHLCV (m5, m15, h1, h4) scoped to live window + warmup.
    """
    mg = merger if merger is not None else HybridDataMerger()
    merged = mg.load_merged_dataset(symbol, fetch_ctrader=fetch_ctrader)
    m1_bars = merged["bars"]

    htf_bars_map: Dict[str, List[Dict[str, Any]]] = {}
    if m1_bars and fetch_ctrader and hasattr(mg.mcp, "fetch_and_cache_trendbars"):
        first_dt = datetime.fromtimestamp(parse_ts_unix(m1_bars[0]), tz=timezone.utc) - timedelta(days=htf_warmup_days)
        last_dt = datetime.fromtimestamp(parse_ts_unix(m1_bars[-1]), tz=timezone.utc) + timedelta(hours=1)
        for tf in ("m5", "m15", "h1", "h4"):
            try:
                htf_bars_map[tf] = mg.mcp.fetch_and_cache_trendbars(symbol, tf, first_dt, last_dt)
            except Exception:
                htf_bars_map[tf] = []

    return build_scalping_mtf_dataset_from_bars(
        symbol=symbol,
        m1_bars=m1_bars,
        htf_bars_map=htf_bars_map,
        summary=merged["summary"],
    )
