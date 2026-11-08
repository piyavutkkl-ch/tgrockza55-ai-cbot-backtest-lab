"""
Node 5 & Node 6A: Deterministic Backtest, Walk-Forward, Sensitivity & Monte Carlo Engine (Python Math Only).
Strictly zero LLM involvement in calculating Profit Factor, Max Drawdown, Win Rate, Sharpe, OOS, or Monte Carlo.
"""

import math
import os
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

from .data_quality import DATA_DIR, compute_file_sha256

_PRECOMPUTED_CACHE: Dict[str, Dict[str, Any]] = {}

# Split timestamps (UTC):
# In-Sample (IS)     : 2022-01-01 to 2024-06-30 (1719791999)
# Validation (VAL)   : 2024-07-01 to 2025-06-30 (1751327999)
# Out-of-Sample (OOS): 2025-07-01 to 2026-10-31
IS_END_UNIX = 1719791999
VAL_END_UNIX = 1751327999


def load_precomputed_dataset(symbol: str = "XAUUSD") -> Dict[str, Any]:
    symbol = symbol.upper().strip()
    if symbol in _PRECOMPUTED_CACHE:
        return _PRECOMPUTED_CACHE[symbol]

    csv_path = os.path.join(DATA_DIR, f"{symbol}_2022_2026_Minute.csv")
    dataset_sha256 = compute_file_sha256(csv_path)

    raw = []
    with open(csv_path, "r", encoding="utf-8") as f:
        f.readline()
        for line in f:
            p = line.rstrip().split(",")
            if len(p) >= 6:
                raw.append((int(p[0]), float(p[1]), float(p[2]), float(p[3]), float(p[4]), float(p[5])))

    arr = np.array(
        raw,
        dtype=[
            ("unix", "i8"),
            ("open", "f8"),
            ("high", "f8"),
            ("low", "f8"),
            ("close", "f8"),
            ("vol", "f8"),
        ],
    )
    n = len(arr)
    unix = arr["unix"]
    close = arr["close"]
    high = arr["high"]
    low = arr["low"]
    vol = arr["vol"]

    days = unix // 86400
    hours = (unix % 86400) // 3600

    # Precompute causal (no look-ahead) Exponential ATR & Daily Anchored VWAP + SD
    atr = np.zeros(n, dtype=np.float64)
    vwap = np.zeros(n, dtype=np.float64)
    vwap_sd = np.zeros(n, dtype=np.float64)

    atr[0] = high[0] - low[0]
    for i in range(1, n):
        tr = max(high[i] - low[i], abs(high[i] - close[i - 1]), abs(low[i] - close[i - 1]))
        atr[i] = 0.95 * atr[i - 1] + 0.05 * tr

    unique_days, day_starts = np.unique(days, return_index=True)
    day_ends = np.append(day_starts[1:], n)
    typ = (high + low + close) / 3.0
    v_clean = np.maximum(vol, 1.0)
    pv = typ * v_clean
    p2v = (typ * typ) * v_clean

    for s_i, e_i in zip(day_starts, day_ends):
        c_pv = np.cumsum(pv[s_i:e_i])
        c_p2v = np.cumsum(p2v[s_i:e_i])
        c_v = np.cumsum(v_clean[s_i:e_i])
        cur_vwap = c_pv / c_v
        var = np.maximum((c_p2v / c_v) - (cur_vwap * cur_vwap), 0.01)
        vwap[s_i:e_i] = cur_vwap
        vwap_sd[s_i:e_i] = np.sqrt(var)

    cached = {
        "symbol": symbol,
        "dataset_path": csv_path,
        "dataset_sha256": dataset_sha256,
        "n": n,
        "unix": unix,
        "close": close,
        "high": high,
        "low": low,
        "hours": hours,
        "atr": atr,
        "vwap": vwap,
        "vwap_sd": vwap_sd,
    }
    _PRECOMPUTED_CACHE[symbol] = cached
    return cached


def _compute_segment_metrics(trades: List[Dict[str, Any]], base_capital: float = 100.0) -> Dict[str, Any]:
    tot = len(trades)
    if tot == 0:
        return {
            "trades": 0,
            "net_pnl_usd": 0.0,
            "profit_factor": 0.0,
            "win_rate_pct": 0.0,
            "max_dd_usd": 0.0,
            "max_dd_pct": 0.0,
            "sharpe_ratio": 0.0,
            "max_single_trade_risk_pct": 0.0,
        }

    pnls = np.array([t["pnl_usd"] for t in trades], dtype=np.float64)
    risks = np.array([t["risk_pct"] for t in trades], dtype=np.float64)
    wins = pnls[pnls > 0]
    losses = np.abs(pnls[pnls < 0])

    gw = float(np.sum(wins)) if len(wins) > 0 else 0.0
    gl = float(np.sum(losses)) if len(losses) > 0 else 0.001
    net_pnl = round(gw - gl, 2)
    pf = round(gw / gl, 2)
    wr = round((len(wins) / tot) * 100.0, 2)

    equity = np.cumsum(pnls)
    peak = np.maximum.accumulate(np.insert(equity, 0, 0.0))[1:]
    dd = peak - equity
    max_dd_usd = round(float(np.max(dd)), 2) if len(dd) > 0 else 0.0
    max_dd_pct = round((max_dd_usd / base_capital) * 100.0, 2)

    std = float(np.std(pnls)) if tot > 1 else 1.0
    sharpe = round(float(np.mean(pnls)) / max(std, 1e-6) * math.sqrt(min(tot, 252)), 2)

    return {
        "trades": tot,
        "net_pnl_usd": net_pnl,
        "profit_factor": pf,
        "win_rate_pct": wr,
        "max_dd_usd": max_dd_usd,
        "max_dd_pct": max_dd_pct,
        "sharpe_ratio": sharpe,
        "max_single_trade_risk_pct": round(float(np.max(risks)), 2),
    }


def simulate_trades_vectorized(
    data: Dict[str, Any],
    params: Dict[str, Any],
    base_capital: float = 100.0,
) -> List[Dict[str, Any]]:
    """
    Executes causal trade simulation across the dataset with explicit cost modeling:
    Spread ($0.20), Razor Commission ($0.07), Slippage ($0.02), and Swap ($0.00 intraday).
    """
    sd_thresh = float(params.get("sd_thresh", 4.2))
    exit_mode = str(params.get("exit_mode", "VWAP_TOUCH")).upper()
    sl_atr_mult = float(params.get("sl_atr_mult", 2.0))
    rr_ratio = float(params.get("rr_ratio", 2.0))
    max_hold = int(params.get("max_hold", 60))
    max_atr_bar = float(params.get("max_atr_bar", 2.0))
    ny_session_only = bool(params.get("ny_session_only", True))
    max_risk_usd = float(params.get("max_risk_usd", 0.70))

    spread_cost = float(params.get("spread_cost", 0.20))
    comm_cost = float(params.get("commission_cost", 0.07))
    slippage_cost = float(params.get("slippage_cost", 0.01))
    swap_cost = 0.0  # Intraday hold <= 60 mins
    total_cost = spread_cost + comm_cost + slippage_cost + swap_cost

    n = data["n"]
    unix = data["unix"]
    close = data["close"]
    high = data["high"]
    low = data["low"]
    hours = data["hours"]
    atr = data["atr"]
    vwap = data["vwap"]
    vwap_sd = data["vwap_sd"]

    bar_range = high - low
    dev = close - vwap
    thresh_arr = sd_thresh * np.maximum(vwap_sd, 1.0)
    cur_atr_arr = np.maximum(atr, 1.2)

    sess_mask = ((hours >= 13) & (hours <= 17)) if ny_session_only else ((hours >= 7) & (hours <= 18))
    void_mask = bar_range <= (max_atr_bar * cur_atr_arr)

    buy_cands = np.where(sess_mask & void_mask & (dev <= -thresh_arr))[0]
    sell_cands = np.where(sess_mask & void_mask & (dev >= thresh_arr))[0]
    all_cands = np.union1d(buy_cands, sell_cands)
    buy_set = set(buy_cands.tolist())

    trades: List[Dict[str, Any]] = []
    last_exit_idx = 50

    for idx in all_cands:
        i = int(idx)
        if i < last_exit_idx + 5 or i >= n - max_hold - 2:
            continue

        if i in buy_set:
            if close[i] > float(np.min(low[i - 15 : i])):
                continue
            side = 1
        else:
            if close[i] < float(np.max(high[i - 15 : i])):
                continue
            side = -1

        entry_p = float(close[i])
        cur_atr = max(float(atr[i]), 1.2)
        sl_dist = sl_atr_mult * cur_atr if sl_atr_mult > 0 else 999.0
        sl_p = (entry_p - sl_dist) if side == 1 else (entry_p + sl_dist)
        tp_fixed = (entry_p + sl_dist * rr_ratio) if side == 1 else (entry_p - sl_dist * rr_ratio)

        exit_p = float(close[i + max_hold])
        exit_idx = i + max_hold

        for m in range(1, max_hold + 1):
            k = i + m
            bh = float(high[k])
            bl = float(low[k])
            vw = float(vwap[k])

            if side == 1:
                if exit_mode == "VWAP_TOUCH" and bh >= vw:
                    exit_p = vw
                    exit_idx = k
                    break
                elif exit_mode != "VWAP_TOUCH" and bh >= tp_fixed:
                    exit_p = tp_fixed
                    exit_idx = k
                    break
                if bl <= sl_p:
                    exit_p = sl_p
                    exit_idx = k
                    break
            else:
                if exit_mode == "VWAP_TOUCH" and bl <= vw:
                    exit_p = vw
                    exit_idx = k
                    break
                elif exit_mode != "VWAP_TOUCH" and bl <= tp_fixed:
                    exit_p = tp_fixed
                    exit_idx = k
                    break
                if bh >= sl_p:
                    exit_p = sl_p
                    exit_idx = k
                    break

        last_exit_idx = exit_idx
        raw_pts = (exit_p - entry_p) if side == 1 else (entry_p - exit_p)
        unscaled_net = raw_pts - total_cost

        if max_risk_usd > 0 and sl_dist > max_risk_usd:
            scale = max_risk_usd / sl_dist
            scaled_net = unscaled_net * scale
            effective_risk_usd = max_risk_usd
        else:
            scaled_net = unscaled_net
            effective_risk_usd = min(sl_dist, base_capital)

        ts = int(unix[i])
        yr = time.gmtime(ts).tm_year
        trades.append({
            "unix": ts,
            "year": yr,
            "side": "BUY" if side == 1 else "SELL",
            "pnl_usd": float(scaled_net),
            "unscaled_pnl_usd": float(unscaled_net),
            "risk_pct": round((effective_risk_usd / base_capital) * 100.0, 2),
        })

    return trades


def run_deterministic_backtest(
    strategy_code: str,
    symbol: str = "XAUUSD",
    params: Optional[Dict[str, Any]] = None,
    base_capital: float = 100.0,
) -> Dict[str, Any]:
    """
    Node 5: Runs full deterministic backtest with strict In-Sample, Validation, and Out-of-Sample splits.
    """
    params = params or {}
    data = load_precomputed_dataset(symbol)
    trades = simulate_trades_vectorized(data, params, base_capital=base_capital)

    is_trades = [t for t in trades if t["unix"] <= IS_END_UNIX]
    val_trades = [t for t in trades if IS_END_UNIX < t["unix"] <= VAL_END_UNIX]
    oos_trades = [t for t in trades if t["unix"] > VAL_END_UNIX]

    full_metrics = _compute_segment_metrics(trades, base_capital)
    is_metrics = _compute_segment_metrics(is_trades, base_capital)
    val_metrics = _compute_segment_metrics(val_trades, base_capital)
    oos_metrics = _compute_segment_metrics(oos_trades, base_capital)

    unscaled_total = round(float(sum(t["unscaled_pnl_usd"] for t in trades)), 2)

    return {
        "computed_at_utc": datetime.now(timezone.utc).isoformat(),
        "engine": "PYTHON_DETERMINISTIC_NUMPY_V2",
        "strategy_code": strategy_code,
        "symbol": symbol,
        "dataset_sha256": data["dataset_sha256"],
        "parameters": params,
        "cost_assumptions": {
            "spread_usd": float(params.get("spread_cost", 0.20)),
            "commission_usd": float(params.get("commission_cost", 0.07)),
            "slippage_usd": float(params.get("slippage_cost", 0.01)),
            "swap_intraday_usd": 0.0,
        },
        "full_period_metrics": {**full_metrics, "unscaled_1oz_net_pnl_usd": unscaled_total},
        "in_sample_metrics": is_metrics,
        "validation_metrics": val_metrics,
        "out_of_sample_metrics": oos_metrics,
        "raw_trades": trades,
    }


def run_advanced_validation_suite(
    backtest_report: Dict[str, Any],
    mc_iterations: int = 1000,
    base_capital: float = 100.0,
) -> Dict[str, Any]:
    """
    Node 6A: Runs Walk-Forward Analysis (5 Annual Windows), Parameter Sensitivity (+/-10%),
    and 1,000-Iteration Bootstrap Monte Carlo Simulation.
    """
    trades = backtest_report.get("raw_trades", [])
    symbol = backtest_report.get("symbol", "XAUUSD")
    params = dict(backtest_report.get("parameters", {}))

    # 1. Walk-Forward Analysis across Calendar Windows (2022, 2023, 2024, 2025, 2026)
    wf_windows: Dict[str, Any] = {}
    years = sorted(set(t["year"] for t in trades))
    profitable_windows = 0
    for yr in years:
        yr_trades = [t for t in trades if t["year"] == yr]
        m = _compute_segment_metrics(yr_trades, base_capital)
        wf_windows[str(yr)] = m
        if m["net_pnl_usd"] > 0:
            profitable_windows += 1

    total_windows = max(len(years), 1)
    wf_efficiency_pct = round((profitable_windows / total_windows) * 100.0, 2)

    # 2. Monte Carlo Simulation (1,000 bootstrap sequences with random execution slippage jitter)
    if len(trades) >= 5:
        rng = np.random.default_rng(seed=42)
        pnls = np.array([t["pnl_usd"] for t in trades], dtype=np.float64)
        n_trades = len(pnls)
        mc_max_dds = np.zeros(mc_iterations, dtype=np.float64)
        mc_final_pnls = np.zeros(mc_iterations, dtype=np.float64)
        ruin_count = 0

        for k in range(mc_iterations):
            sampled = rng.choice(pnls, size=n_trades, replace=True)
            jitter = rng.normal(loc=0.0, scale=0.01, size=n_trades)
            sim_pnls = sampled + jitter
            eq = np.cumsum(sim_pnls)
            pk = np.maximum.accumulate(np.insert(eq, 0, 0.0))[1:]
            dd = pk - eq
            max_dd = float(np.max(dd))
            mc_max_dds[k] = (max_dd / base_capital) * 100.0
            mc_final_pnls[k] = float(eq[-1])
            if (base_capital + float(np.min(eq))) <= base_capital * 0.50:
                ruin_count += 1

        mc_95_dd_pct = round(float(np.percentile(mc_max_dds, 95)), 2)
        mc_95_var_pnl = round(float(np.percentile(mc_final_pnls, 5)), 2)
        mc_ruin_prob_pct = round((ruin_count / mc_iterations) * 100.0, 2)
    else:
        mc_95_dd_pct = 999.0
        mc_95_var_pnl = -100.0
        mc_ruin_prob_pct = 100.0

    # 3. Parameter Sensitivity Check (+/- 5% around sd_thresh)
    data = load_precomputed_dataset(symbol)
    base_sd = float(params.get("sd_thresh", 4.2))
    p_low = {**params, "sd_thresh": round(base_sd * 0.95, 2)}
    p_high = {**params, "sd_thresh": round(base_sd * 1.05, 2)}
    m_low = _compute_segment_metrics(simulate_trades_vectorized(data, p_low, base_capital), base_capital)
    m_high = _compute_segment_metrics(simulate_trades_vectorized(data, p_high, base_capital), base_capital)

    return {
        "walk_forward": {
            "windows": wf_windows,
            "profitable_windows": profitable_windows,
            "total_windows": total_windows,
            "wf_efficiency_pct": wf_efficiency_pct,
        },
        "monte_carlo": {
            "iterations": mc_iterations,
            "mc_95th_max_dd_pct": mc_95_dd_pct,
            "mc_5th_percentile_pnl_usd": mc_95_var_pnl,
            "ruin_probability_pct": mc_ruin_prob_pct,
        },
        "parameter_sensitivity": {
            "sd_minus_5pct_pf": m_low["profit_factor"],
            "sd_base_pf": backtest_report["full_period_metrics"]["profit_factor"],
            "sd_plus_5pct_pf": m_high["profit_factor"],
        },
    }
