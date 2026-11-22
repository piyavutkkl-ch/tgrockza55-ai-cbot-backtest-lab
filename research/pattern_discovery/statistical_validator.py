"""
Statistical Validation, Cost-Realistic Simulation & Anti-Overfit Engine (Step 5)
================================================================================
Pure Python + NumPy statistical evaluation suite implementing:
- Independent Episode De-clustering (cooldown grouping to prevent pseudoreplication).
- Exact Binomial / Normal p-values, Wilson 95% Lower Bound, and Benjamini-Hochberg FDR.
- Regime-Matched Baseline Lift across (session_zone, macro_regime).
- 3-State Directional Probability analysis (Bullish / Bearish / Neutral) across
  4 bar horizons (5, 15, 30, 60) strictly separated from Trade Simulation Win Rate.
- Cost-realistic Trade Simulation at next-bar open + real spread + slippage + commission
  with conservative intra-bar SL-first tie-breaking.
- Strict Chronological IS (60%) / OOS (40%) + 3-Fold Rolling Walk-Forward +
  Market Regime / 7-Zone Session / Volatility breakdowns.
"""

from __future__ import annotations

import math
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from research.pattern_discovery.data_loader import HORIZONS

SL_TP_GRID: Tuple[Tuple[float, float], ...] = (
    (1.0, 1.5),
    (1.2, 2.0),
    (1.5, 2.0),
    (1.5, 2.5),
    (2.0, 3.0),
)

DIR_THRESH_ATR = 0.50


def decluster_indices(indices: np.ndarray, cooldown_bars: int = 10) -> np.ndarray:
    """Groups overlapping triggers within `cooldown_bars` into independent episodes."""
    if len(indices) == 0:
        return np.zeros(0, dtype=np.int64)
    idx_sorted = np.sort(indices)
    kept: List[int] = []
    last = -cooldown_bars - 1
    for x in idx_sorted:
        xi = int(x)
        if xi - last >= cooldown_bars:
            kept.append(xi)
            last = xi
    return np.array(kept, dtype=np.int64)


def wilson_lower_bound(wins: int, n: int, z: float = 1.96) -> float:
    """Lower bound of the Wilson score confidence interval."""
    if n <= 0:
        return 0.0
    p = max(0.0, min(1.0, wins / n))
    denom = 1.0 + (z * z) / n
    center = p + (z * z) / (2.0 * n)
    rad = z * math.sqrt((p * (1.0 - p) + (z * z) / (4.0 * n)) / n)
    return max(0.0, (center - rad) / denom)


def binomial_p_value_gt(wins: int, n: int, p0: float) -> float:
    """One-sided binomial p-value P(X >= wins | X ~ Bin(n, p0))."""
    if n <= 0:
        return 1.0
    if wins <= 0:
        return 1.0
    if wins > n:
        return 0.0
    p_clamped = max(1e-6, min(1.0 - 1e-6, float(p0)))
    if n <= 60:
        total = 0.0
        q = 1.0 - p_clamped
        for k in range(wins, n + 1):
            total += math.comb(n, k) * (p_clamped ** k) * (q ** (n - k))
        return min(1.0, max(0.0, total))
    mu = n * p_clamped
    sd = math.sqrt(n * p_clamped * (1.0 - p_clamped))
    if sd <= 1e-12:
        return 0.0 if wins > mu else 1.0
    z = (wins - 0.5 - mu) / sd
    return min(1.0, max(0.0, 0.5 * math.erfc(z / math.sqrt(2.0))))


def pnl_one_sided_p_value(pnls: List[float]) -> float:
    """Normal/t approximation one-sided p-value for H1: mean(pnls) > 0."""
    n = len(pnls)
    if n < 3:
        return 1.0
    arr = np.array(pnls, dtype=np.float64)
    mu = float(arr.mean())
    sd = float(arr.std(ddof=1))
    if sd <= 1e-12:
        return 0.0 if mu > 0 else 1.0
    t_stat = mu / (sd / math.sqrt(n))
    return min(1.0, max(0.0, 0.5 * math.erfc(t_stat / math.sqrt(2.0))))


def benjamini_hochberg_fdr(p_values: List[float]) -> List[float]:
    """Benjamini-Hochberg FDR adjustment returning q-values in input order."""
    m = len(p_values)
    if m == 0:
        return []
    indexed = sorted(enumerate(p_values), key=lambda x: x[1])
    q_vals = [1.0] * m
    prev_q = 1.0
    for rank_idx in range(m - 1, -1, -1):
        orig_idx, p = indexed[rank_idx]
        rank = rank_idx + 1
        raw_q = min(1.0, max(0.0, float(p) * m / rank))
        cur_q = min(prev_q, raw_q)
        q_vals[orig_idx] = round(cur_q, 6)
        prev_q = cur_q
    return q_vals


def compute_regime_baselines(dataset: Dict[str, Any]) -> Dict[Tuple[str, str], Dict[int, Dict[str, float]]]:
    """
    Computes empirical 3-state directional base rates (Bullish / Bearish / Neutral)
    across valid Tier 1 live bars for every (session_zone, macro_regime) and horizon.
    """
    m1 = dataset["m1"]
    live_mask = m1["has_l2_dom"] & m1["has_real_spread"]
    sz = m1["session_zone"]
    mr = m1["macro_regime"]
    outcomes = dataset["outcomes"]

    baselines: Dict[Tuple[str, str], Dict[int, Dict[str, float]]] = {}
    all_groups: Dict[Tuple[str, str], List[int]] = defaultdict(list)

    for idx in np.flatnonzero(live_mask):
        all_groups[(str(sz[idx]), str(mr[idx]))].append(int(idx))
        all_groups[("_ALL_", "_ALL_")].append(int(idx))

    for key, idxs in all_groups.items():
        arr_idx = np.array(idxs, dtype=np.int64)
        h_map: Dict[int, Dict[str, float]] = {}
        for h in HORIZONS:
            out_h = outcomes[h]
            v = out_h["valid"][arr_idx]
            valid_idx = arr_idx[v]
            if len(valid_idx) == 0:
                h_map[h] = {"n": 0, "p_bull": 0.3333, "p_bear": 0.3333, "p_neutral": 0.3334}
                continue
            rets = out_h["fwd_ret_atr"][valid_idx]
            n_v = len(rets)
            bull = int(np.sum(rets >= DIR_THRESH_ATR))
            bear = int(np.sum(rets <= -DIR_THRESH_ATR))
            neut = n_v - bull - bear
            h_map[h] = {
                "n": n_v,
                "p_bull": bull / n_v,
                "p_bear": bear / n_v,
                "p_neutral": neut / n_v,
            }
        baselines[key] = h_map

    return baselines


def _compute_3state_for_indices(
    dataset: Dict[str, Any],
    indices: np.ndarray,
    horizon: int,
    baselines: Dict[Tuple[str, str], Dict[int, Dict[str, float]]],
) -> Dict[str, float]:
    out_h = dataset["outcomes"][horizon]
    m1 = dataset["m1"]
    sz = m1["session_zone"]
    mr = m1["macro_regime"]

    if len(indices) == 0:
        return {
            "n_valid": 0,
            "p_bull": 0.0,
            "p_bear": 0.0,
            "p_neutral": 0.0,
            "base_bull": 0.3333,
            "base_bear": 0.3333,
            "lift_bull": 0.0,
            "lift_bear": 0.0,
            "avg_move_atr": 0.0,
            "avg_mfe_long_atr": 0.0,
            "avg_mae_long_atr": 0.0,
            "avg_mfe_short_atr": 0.0,
            "avg_mae_short_atr": 0.0,
            "max_mfe_long_atr": 0.0,
            "max_mae_long_atr": 0.0,
            "max_mfe_short_atr": 0.0,
            "max_mae_short_atr": 0.0,
            "pct_mfe_first_long": 0.0,
            "pct_mfe_first_short": 0.0,
        }

    v = out_h["valid"][indices]
    v_idx = indices[v]
    n_v = len(v_idx)
    if n_v == 0:
        return {
            "n_valid": 0,
            "p_bull": 0.0,
            "p_bear": 0.0,
            "p_neutral": 0.0,
            "base_bull": 0.3333,
            "base_bear": 0.3333,
            "lift_bull": 0.0,
            "lift_bear": 0.0,
            "avg_move_atr": 0.0,
            "avg_mfe_long_atr": 0.0,
            "avg_mae_long_atr": 0.0,
            "avg_mfe_short_atr": 0.0,
            "avg_mae_short_atr": 0.0,
            "max_mfe_long_atr": 0.0,
            "max_mae_long_atr": 0.0,
            "max_mfe_short_atr": 0.0,
            "max_mae_short_atr": 0.0,
            "pct_mfe_first_long": 0.0,
            "pct_mfe_first_short": 0.0,
        }

    rets = out_h["fwd_ret_atr"][v_idx]
    bull_c = int(np.sum(rets >= DIR_THRESH_ATR))
    bear_c = int(np.sum(rets <= -DIR_THRESH_ATR))
    neut_c = n_v - bull_c - bear_c

    p_bull = bull_c / n_v
    p_bear = bear_c / n_v
    p_neut = neut_c / n_v

    global_base = baselines.get(("_ALL_", "_ALL_"), {}).get(horizon, {"p_bull": 0.3333, "p_bear": 0.3333})
    base_b_sum = 0.0
    base_s_sum = 0.0
    for idx in v_idx:
        kb = baselines.get((str(sz[idx]), str(mr[idx])), {}).get(horizon)
        if kb and kb.get("n", 0) >= 20:
            base_b_sum += kb["p_bull"]
            base_s_sum += kb["p_bear"]
        else:
            base_b_sum += global_base["p_bull"]
            base_s_sum += global_base["p_bear"]

    base_bull = base_b_sum / n_v
    base_bear = base_s_sum / n_v

    mfe_l = out_h["mfe_long_atr"][v_idx]
    mae_l = out_h["mae_long_atr"][v_idx]
    mfe_s = out_h["mfe_short_atr"][v_idx]
    mae_s = out_h["mae_short_atr"][v_idx]

    return {
        "n_valid": n_v,
        "bull_count": bull_c,
        "bear_count": bear_c,
        "neutral_count": neut_c,
        "p_bull": round(p_bull, 4),
        "p_bear": round(p_bear, 4),
        "p_neutral": round(p_neut, 4),
        "base_bull": round(base_bull, 4),
        "base_bear": round(base_bear, 4),
        "lift_bull": round(p_bull - base_bull, 4),
        "lift_bear": round(p_bear - base_bear, 4),
        "avg_move_atr": round(float(np.mean(rets)), 4),
        "avg_mfe_long_atr": round(float(np.mean(mfe_l)), 4),
        "avg_mae_long_atr": round(float(np.mean(mae_l)), 4),
        "avg_mfe_short_atr": round(float(np.mean(mfe_s)), 4),
        "avg_mae_short_atr": round(float(np.mean(mae_s)), 4),
        "max_mfe_long_atr": round(float(np.max(mfe_l)), 4),
        "max_mae_long_atr": round(float(np.max(mae_l)), 4),
        "max_mfe_short_atr": round(float(np.max(mfe_s)), 4),
        "max_mae_short_atr": round(float(np.max(mae_s)), 4),
        "pct_mfe_first_long": round(float(np.mean(out_h["mfe_first_long"][v_idx])), 4),
        "pct_mfe_first_short": round(float(np.mean(out_h["mfe_first_short"][v_idx])), 4),
    }


def simulate_trades(
    dataset: Dict[str, Any],
    trigger_indices: np.ndarray,
    direction: str,
    sl_atr: float,
    tp_atr: float,
    max_hold: int = 60,
) -> Dict[str, Any]:
    """
    Executes causal trade simulation at next-bar open + real spread + slippage + commission
    with conservative SL-before-TP tie-break. Never looks into future bars for sizing or fill.
    """
    m1 = dataset["m1"]
    spec = dataset["spec"]
    n = int(m1["n"])

    lot = float(spec["lot_scale"])
    comm = float(spec["commission_usd"])
    slip = float(spec["base_slippage"])
    default_sp = float(spec["default_spread"])
    min_atr = float(spec["min_atr"])

    ts = m1["ts_unix"]
    op = m1["open"]
    hi = m1["high"]
    lo = m1["low"]
    cl = m1["close"]
    atr = m1["atr14"]
    sp_arr = m1["spread_avg"]
    has_sp = m1["has_real_spread"]
    sz = m1["session_zone"]
    mr = m1["macro_regime"]
    vr = m1["vol_regime"]

    pnls: List[float] = []
    hold_bars_list: List[int] = []
    regimes_out: List[str] = []
    sessions_out: List[str] = []
    vols_out: List[str] = []

    is_buy = direction == "BUY"
    last_exit_idx = -1

    for raw_i in trigger_indices:
        i = int(raw_i)
        if i <= last_exit_idx:
            continue
        if i + 1 >= n:
            break
        if int(ts[i + 1]) - int(ts[i]) > 600:
            continue

        cur_atr = max(float(atr[i]), min_atr)
        sp_in = float(sp_arr[i]) if (has_sp[i] and math.isfinite(float(sp_arr[i]))) else default_sp
        entry_p = float(op[i + 1]) + sp_in * 0.5 + slip * 0.5 if is_buy else float(op[i + 1]) - sp_in * 0.5 - slip * 0.5

        sl_dist = sl_atr * cur_atr
        tp_dist = tp_atr * cur_atr
        sl_p = entry_p - sl_dist if is_buy else entry_p + sl_dist
        tp_p = entry_p + tp_dist if is_buy else entry_p - tp_dist

        exit_idx = min(i + max_hold, n - 1)
        reason = "TIMEOUT"
        raw_exit = float(cl[exit_idx])

        for j in range(i + 1, min(i + max_hold, n - 1) + 1):
            if j > i + 1 and int(ts[j]) - int(ts[j - 1]) > 600:
                exit_idx = j - 1
                raw_exit = float(cl[j - 1])
                reason = "GAP_EXIT"
                break
            bh = float(hi[j])
            bl = float(lo[j])
            if is_buy:
                if bl <= sl_p:
                    exit_idx = j
                    raw_exit = sl_p
                    reason = "SL"
                    break
                if bh >= tp_p:
                    exit_idx = j
                    raw_exit = tp_p
                    reason = "TP"
                    break
            else:
                if bh >= sl_p:
                    exit_idx = j
                    raw_exit = sl_p
                    reason = "SL"
                    break
                if bl <= tp_p:
                    exit_idx = j
                    raw_exit = tp_p
                    reason = "TP"
                    break

        sp_out = float(sp_arr[exit_idx]) if (has_sp[exit_idx] and math.isfinite(float(sp_arr[exit_idx]))) else default_sp
        slip_exit = slip * (1.2 if reason == "SL" else 0.6)
        fill_exit = (raw_exit - slip_exit) if is_buy else (raw_exit + slip_exit)
        gross = (fill_exit - entry_p) if is_buy else (entry_p - fill_exit)
        net_usd = (gross - sp_out * 0.5) * lot - comm

        pnls.append(net_usd)
        hold_bars_list.append(max(1, exit_idx - i))
        regimes_out.append(str(mr[i]))
        sessions_out.append(str(sz[i]))
        vols_out.append(str(vr[i]))
        last_exit_idx = exit_idx

    nt = len(pnls)
    if nt == 0:
        return {
            "trades": 0,
            "wins": 0,
            "losses": 0,
            "win_rate": 0.0,
            "wilson_lb_95": 0.0,
            "expectancy_usd": 0.0,
            "profit_factor": 0.0,
            "net_pnl_usd": 0.0,
            "max_dd_usd": 0.0,
            "avg_holding_bars": 0.0,
            "pnl_p_value": 1.0,
            "pnls": [],
            "regimes": [],
            "sessions": [],
            "vols": [],
        }

    wins = sum(1 for p in pnls if p > 0)
    losses = nt - wins
    g_win = sum(p for p in pnls if p > 0)
    g_loss = abs(sum(p for p in pnls if p < 0))
    net = sum(pnls)

    if g_loss > 1e-9:
        pf = g_win / g_loss
    elif g_win > 0:
        pf = 99.0
    else:
        pf = 0.0

    eq = 0.0
    peak = 0.0
    max_dd = 0.0
    for p in pnls:
        eq += p
        if eq > peak:
            peak = eq
        dd = peak - eq
        if dd > max_dd:
            max_dd = dd

    return {
        "trades": nt,
        "wins": wins,
        "losses": losses,
        "win_rate": round(wins / nt, 4),
        "wilson_lb_95": round(wilson_lower_bound(wins, nt), 4),
        "expectancy_usd": round(net / nt, 4),
        "profit_factor": round(pf, 3),
        "net_pnl_usd": round(net, 2),
        "max_dd_usd": round(max_dd, 2),
        "avg_holding_bars": round(sum(hold_bars_list) / nt, 1),
        "pnl_p_value": round(pnl_one_sided_p_value(pnls), 6),
        "pnls": pnls,
        "regimes": regimes_out,
        "sessions": sessions_out,
        "vols": vols_out,
    }


def _group_breakdown(pnls: List[float], labels: List[str]) -> Dict[str, Dict[str, Any]]:
    buckets: Dict[str, List[float]] = defaultdict(list)
    for p, lbl in zip(pnls, labels):
        buckets[lbl].append(p)
    out: Dict[str, Dict[str, Any]] = {}
    for k, vals in sorted(buckets.items()):
        nt = len(vals)
        w = sum(1 for x in vals if x > 0)
        gw = sum(x for x in vals if x > 0)
        gl = abs(sum(x for x in vals if x < 0))
        net = sum(vals)
        pf = (gw / gl) if gl > 1e-9 else (99.0 if gw > 0 else 0.0)
        out[k] = {
            "trades": nt,
            "wins": w,
            "win_rate": round(w / nt, 4) if nt else 0.0,
            "net_pnl_usd": round(net, 2),
            "expectancy_usd": round(net / nt, 4) if nt else 0.0,
            "profit_factor": round(pf, 2),
        }
    return out


def evaluate_condition(
    dataset: Dict[str, Any],
    baselines: Dict[Tuple[str, str], Dict[int, Dict[str, float]]],
    trigger_indices: np.ndarray,
    preferred_dir: str,
    condition_meta: Dict[str, Any],
    cooldown_bars: int = 10,
) -> Dict[str, Any]:
    """
    Runs complete IS/OOS/Walk-Forward statistical validation and multi-horizon
    3-state directional analysis on an arbitrary causal trigger index array.
    """
    m1 = dataset["m1"]
    live_mask = m1["has_l2_dom"] & m1["has_real_spread"]
    live_total_bars = max(1, int(np.sum(live_mask)))
    cutoff_idx = int(dataset["is_cutoff_idx"])

    raw_count = int(len(trigger_indices))
    live_trig = np.array([int(i) for i in trigger_indices if 0 <= int(i) < m1["n"] and live_mask[int(i)]], dtype=np.int64)
    episodes = decluster_indices(live_trig, cooldown_bars=cooldown_bars)

    n_total = len(episodes)
    is_eps = episodes[episodes < cutoff_idx]
    oos_eps = episodes[episodes >= cutoff_idx]
    n_is = len(is_eps)
    n_oos = len(oos_eps)

    # Determine direction & primary horizon strictly on IS (fallback to overall only if IS < 5 and total >= 5)
    sample_for_dir = is_eps if n_is >= 5 else episodes
    best_h = 15
    chosen_dir = preferred_dir if preferred_dir in ("BUY", "SELL") else "BUY"
    best_score = -999.0

    for h in HORIZONS:
        st_dir = _compute_3state_for_indices(dataset, sample_for_dir, h, baselines)
        if st_dir["n_valid"] == 0:
            continue
        if preferred_dir == "BUY":
            sc = st_dir["lift_bull"]
            cand_dir = "BUY"
        elif preferred_dir == "SELL":
            sc = st_dir["lift_bear"]
            cand_dir = "SELL"
        else:
            if st_dir["lift_bull"] >= st_dir["lift_bear"]:
                sc = st_dir["lift_bull"]
                cand_dir = "BUY"
            else:
                sc = st_dir["lift_bear"]
                cand_dir = "SELL"
        if sc > best_score:
            best_score = sc
            best_h = h
            chosen_dir = cand_dir

    # Compute full 4-horizon 3-state directional probabilities (IS, OOS, ALL)
    horizons_oos: Dict[int, Dict[str, Any]] = {}
    horizons_all: Dict[int, Dict[str, Any]] = {}
    for h in HORIZONS:
        horizons_oos[h] = _compute_3state_for_indices(dataset, oos_eps, h, baselines)
        horizons_all[h] = _compute_3state_for_indices(dataset, episodes, h, baselines)

    primary_oos = horizons_oos[best_h]
    primary_all = horizons_all[best_h]
    primary_is = _compute_3state_for_indices(dataset, is_eps, best_h, baselines)

    if chosen_dir == "BUY":
        oos_dir_prob = primary_oos["p_bull"]
        oos_dir_base = primary_oos["base_bull"]
        oos_dir_lift = primary_oos["lift_bull"]
        oos_dir_hits = int(primary_oos.get("bull_count", 0))
        all_dir_prob = primary_all["p_bull"]
        all_dir_lift = primary_all["lift_bull"]
        avg_mfe = primary_all["avg_mfe_long_atr"]
        avg_mae = primary_all["avg_mae_long_atr"]
        max_mfe = primary_all["max_mfe_long_atr"]
        max_mae = primary_all["max_mae_long_atr"]
        mfe_first = primary_all["pct_mfe_first_long"]
    else:
        oos_dir_prob = primary_oos["p_bear"]
        oos_dir_base = primary_oos["base_bear"]
        oos_dir_lift = primary_oos["lift_bear"]
        oos_dir_hits = int(primary_oos.get("bear_count", 0))
        all_dir_prob = primary_all["p_bear"]
        all_dir_lift = primary_all["lift_bear"]
        avg_mfe = primary_all["avg_mfe_short_atr"]
        avg_mae = primary_all["avg_mae_short_atr"]
        max_mfe = primary_all["max_mfe_short_atr"]
        max_mae = primary_all["max_mae_short_atr"]
        mfe_first = primary_all["pct_mfe_first_short"]

    dir_p_value = binomial_p_value_gt(oos_dir_hits, int(primary_oos["n_valid"]), oos_dir_base) if primary_oos["n_valid"] > 0 else 1.0

    # Sweep SL/TP grid strictly on IS to freeze risk geometry
    best_sl, best_tp = (1.5, 2.5)
    best_is_sim: Optional[Dict[str, Any]] = None
    best_is_score = -1e9
    sim_is_eps = is_eps if n_is >= 5 else episodes

    for sl_a, tp_a in SL_TP_GRID:
        sim = simulate_trades(dataset, sim_is_eps, chosen_dir, sl_a, tp_a, max_hold=60)
        if sim["trades"] == 0:
            sc = -1e6
        else:
            sc = sim["expectancy_usd"] * math.sqrt(sim["trades"])
        if sc > best_is_score:
            best_is_score = sc
            best_sl, best_tp = sl_a, tp_a
            best_is_sim = sim

    is_sim = best_is_sim if n_is >= 5 else simulate_trades(dataset, is_eps, chosen_dir, best_sl, best_tp, max_hold=60)
    oos_sim = simulate_trades(dataset, oos_eps, chosen_dir, best_sl, best_tp, max_hold=60)
    all_sim = simulate_trades(dataset, episodes, chosen_dir, best_sl, best_tp, max_hold=60)

    # 3-Fold Rolling Walk-Forward using frozen (best_sl, best_tp) or train-adaptive fold
    wf_folds = []
    if n_total >= 12:
        cuts = [int(n_total * 0.25), int(n_total * 0.50), int(n_total * 0.75), n_total]
        for fi in range(3):
            tr_eps = episodes[: cuts[fi]]
            te_eps = episodes[cuts[fi] : cuts[fi + 1]]
            if len(te_eps) < 2:
                continue
            # Select fold parameters strictly on tr_eps
            f_sl, f_tp = best_sl, best_tp
            if len(tr_eps) >= 6:
                f_best_sc = -1e9
                for sl_a, tp_a in SL_TP_GRID:
                    tsim = simulate_trades(dataset, tr_eps, chosen_dir, sl_a, tp_a, max_hold=60)
                    sc = tsim["expectancy_usd"] * math.sqrt(max(1, tsim["trades"])) if tsim["trades"] > 0 else -1e6
                    if sc > f_best_sc:
                        f_best_sc = sc
                        f_sl, f_tp = sl_a, tp_a
            te_sim = simulate_trades(dataset, te_eps, chosen_dir, f_sl, f_tp, max_hold=60)
            wf_folds.append(
                {
                    "fold": fi + 1,
                    "trades": te_sim["trades"],
                    "win_rate": te_sim["win_rate"],
                    "expectancy_usd": te_sim["expectancy_usd"],
                    "net_pnl_usd": te_sim["net_pnl_usd"],
                    "sl_atr": f_sl,
                    "tp_atr": f_tp,
                }
            )
    wf_pos = sum(1 for f in wf_folds if f["expectancy_usd"] > 0)
    wf_avg_exp = round(sum(f["expectancy_usd"] for f in wf_folds) / len(wf_folds), 4) if wf_folds else 0.0

    # Breakdowns across OOS (for honest regime/session assessment) and ALL
    is_reg_bd = _group_breakdown(is_sim["pnls"], is_sim["regimes"])
    oos_reg_bd = _group_breakdown(oos_sim["pnls"], oos_sim["regimes"])
    oos_ses_bd = _group_breakdown(oos_sim["pnls"], oos_sim["sessions"])
    oos_vol_bd = _group_breakdown(oos_sim["pnls"], oos_sim["vols"])

    all_reg_bd = _group_breakdown(all_sim["pnls"], all_sim["regimes"])
    all_ses_bd = _group_breakdown(all_sim["pnls"], all_sim["sessions"])
    all_vol_bd = _group_breakdown(all_sim["pnls"], all_sim["vols"])

    # Asset-scaled expectancy floor so 0.01-lot lower-notional assets (e.g. ETHUSD)
    # are not artificially erased by XAU/BTC-sized dollar cutoffs.
    spec = dataset["spec"]
    unit_exp_floor = min(0.05, max(0.004, float(spec["min_atr"]) * float(spec["lot_scale"]) * 0.5))

    # Determine Regime-Specific OOS Edge (consistent positive IS & OOS in same regime/session)
    best_sub_regime = None
    best_sub_score = 0.0
    is_ses_bd = _group_breakdown(is_sim["pnls"], is_sim["sessions"])
    for rname, obd in oos_reg_bd.items():
        ibd = is_reg_bd.get(rname, {})
        if obd["trades"] >= 4 and obd["expectancy_usd"] > unit_exp_floor and obd["profit_factor"] >= 1.15 and ibd.get("expectancy_usd", 0.0) > 0:
            sc = obd["expectancy_usd"] * obd["trades"]
            if sc > best_sub_score:
                best_sub_score = sc
                best_sub_regime = f"REGIME:{rname}"
    for sname, obd in oos_ses_bd.items():
        ibd = is_ses_bd.get(sname, {})
        if obd["trades"] >= 4 and obd["expectancy_usd"] > unit_exp_floor and obd["profit_factor"] >= 1.15 and ibd.get("expectancy_usd", 0.0) > 0:
            sc = obd["expectancy_usd"] * obd["trades"]
            if sc > best_sub_score:
                best_sub_score = sc
                best_sub_regime = f"SESSION:{sname}"

    # Assign Validation Status & Reliability honestly
    is_exp = is_sim["expectancy_usd"]
    oos_exp = oos_sim["expectancy_usd"]
    oos_pf = oos_sim["profit_factor"]

    if n_total < 8 or oos_sim["trades"] < 3:
        val_status = "INSUFFICIENT_DATA"
        reliability = "UNTESTED" if n_total < 3 else "LOW"
    elif n_total < 20:
        if oos_exp > unit_exp_floor and is_exp > 0 and (oos_dir_lift > 0.02 or oos_pf >= 1.25):
            val_status = "RARE_HIGH_EDGE"
            reliability = "RARE_PRELIMINARY"
        elif is_exp > unit_exp_floor and oos_exp <= 0:
            val_status = "IS_ONLY_OVERFIT"
            reliability = "LOW"
        else:
            val_status = "NO_EDGE"
            reliability = "LOW"
    else:
        if oos_exp > 0.0 and oos_pf >= 1.05 and is_exp > 0.0 and (wf_pos >= 2 or oos_dir_lift > 0.02):
            val_status = "VALIDATED_OOS"
            if oos_sim["trades"] >= 20 and oos_pf >= 1.20 and wf_pos >= 2 and oos_sim["wilson_lb_95"] > 0.35:
                reliability = "HIGH"
            else:
                reliability = "MEDIUM"
        elif best_sub_regime is not None:
            val_status = "REGIME_SPECIFIC_EDGE"
            reliability = "MEDIUM" if n_oos >= 12 else "LOW"
        elif is_exp > 0.0 and oos_exp <= 0.0:
            val_status = "IS_ONLY_OVERFIT"
            reliability = "LOW"
        else:
            val_status = "NO_EDGE"
            reliability = "LOW"

    freq_per_day = round(n_total / max(1.0, live_total_bars / 1440.0), 2)

    return {
        **condition_meta,
        "symbol": dataset["symbol"],
        "direction": chosen_dir,
        "primary_horizon_bars": best_h,
        "raw_trigger_count": raw_count,
        "sample_size_total": n_total,
        "sample_size_is": n_is,
        "sample_size_oos": n_oos,
        "frequency_per_1000_bars": round(n_total * 1000.0 / live_total_bars, 2),
        "frequency_per_day": freq_per_day,
        "sl_atr": best_sl,
        "tp_atr": best_tp,
        "rr_ratio": round(best_tp / best_sl, 2),
        # Multi-horizon 3-state directional probabilities (strictly separated from Win Rate!)
        "probability": {
            "primary_horizon_bars": best_h,
            "is_primary": primary_is,
            "oos_primary": primary_oos,
            "all_primary": primary_all,
            "oos_dir_prob": round(oos_dir_prob, 4),
            "oos_base_prob": round(oos_dir_base, 4),
            "oos_dir_lift": round(oos_dir_lift, 4),
            "all_dir_prob": round(all_dir_prob, 4),
            "all_dir_lift": round(all_dir_lift, 4),
            "dir_p_value_oos": round(dir_p_value, 6),
            "horizons_oos": {
                f"h_{h}": {
                    "p_bull": horizons_oos[h]["p_bull"],
                    "p_bear": horizons_oos[h]["p_bear"],
                    "p_neutral": horizons_oos[h]["p_neutral"],
                    "avg_move_atr": horizons_oos[h]["avg_move_atr"],
                }
                for h in HORIZONS
            },
        },
        # Trade metrics (OOS primary + IS + Cumulative)
        "win_rate": {
            "is": is_sim["win_rate"],
            "oos": oos_sim["win_rate"],
            "all": all_sim["win_rate"],
            "oos_wilson_lb95": oos_sim["wilson_lb_95"],
        },
        "expectancy": {
            "is_usd": is_sim["expectancy_usd"],
            "oos_usd": oos_sim["expectancy_usd"],
            "all_usd": all_sim["expectancy_usd"],
            "net_pnl_oos_usd": oos_sim["net_pnl_usd"],
            "net_pnl_all_usd": all_sim["net_pnl_usd"],
            "max_dd_oos_usd": oos_sim["max_dd_usd"],
            "max_dd_all_usd": all_sim["max_dd_usd"],
            "avg_holding_bars_oos": oos_sim["avg_holding_bars"],
            "pnl_p_value_oos": oos_sim["pnl_p_value"],
        },
        "profit_factor": {
            "is": is_sim["profit_factor"],
            "oos": oos_sim["profit_factor"],
            "all": all_sim["profit_factor"],
        },
        "mfe_mae": {
            "avg_mfe_atr": avg_mfe,
            "avg_mae_atr": avg_mae,
            "max_mfe_atr": max_mfe,
            "max_mae_atr": max_mae,
            "pct_mfe_before_mae": mfe_first,
            "mfe_mae_ratio": round(avg_mfe / max(avg_mae, 1e-6), 2),
        },
        "walk_forward": {
            "folds": wf_folds,
            "positive_folds": wf_pos,
            "total_folds": len(wf_folds),
            "avg_expectancy_usd": wf_avg_exp,
        },
        "regime_breakdown": all_reg_bd,
        "regime_breakdown_oos": oos_reg_bd,
        "session_breakdown": all_ses_bd,
        "session_breakdown_oos": oos_ses_bd,
        "vol_breakdown": all_vol_bd,
        "best_sub_regime_oos": best_sub_regime,
        "validation_status": val_status,
        "reliability": reliability,
        # Single pre-specified positive test p-value used for Benjamini-Hochberg FDR
        "raw_fdr_p_value": oos_sim["pnl_p_value"] if oos_sim["trades"] >= 3 else 1.0,
    }
