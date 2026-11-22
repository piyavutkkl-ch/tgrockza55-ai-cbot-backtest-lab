"""
Unit Tests for V5 Scalping & Intraday Pattern Discovery Engine (Step 8)
========================================================================
Verifies:
1. Strict Dual-HTF & LTF Zero-Lookahead via Future-Bar Mutation Invariance.
2. Causal Swing Pivot Confirmation Lag (`p + pivot_right`).
3. Episode De-clustering (`cooldown_bars=10`).
4. Price-Anchored Sequence Matching & Structural Invalidation Guard.
5. Microstructure Event Gating on CTRADER_OHLCV_ONLY bars (Zero Hallucination).
6. 3-State Directional Probability Conservation (`sum == 1.0`) & Exact 20-Field Schema.
"""

from __future__ import annotations

import math
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List

import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from research.hybrid_data_merger import classify_session_zone
from research.pattern_discovery.data_loader import (
    TF_SECONDS,
    build_scalping_mtf_dataset_from_bars,
    compute_causal_tf_indicators,
    resample_m1_to_tf,
)
from research.pattern_discovery.event_tokenizer import (
    project_htf_events_to_m1,
    tokenize_htf_events,
    tokenize_m1_events,
)
from research.pattern_discovery.level_memory import extract_level_structure
from research.pattern_discovery.library_builder import analyze_symbol_patterns
from research.pattern_discovery.round2_micro_session_miner import mine_session_specific_patterns
from research.pattern_discovery.sequence_mtf_miner import match_anchored_sequence, mine_single_conditions
from research.pattern_discovery.statistical_validator import compute_regime_baselines, decluster_indices

REQUIRED_20_FIELDS = (
    "rank",
    "condition_name",
    "condition_type",
    "timeframes",
    "pre_condition",
    "event_sequence",
    "entry_criteria",
    "direction",
    "expected_behavior",
    "probability",
    "win_rate",
    "expectancy",
    "profit_factor",
    "mfe_mae",
    "time_horizon",
    "frequency",
    "sample_size",
    "sl_tp",
    "reliability",
    "validation",
)


def _make_synthetic_m1_bars(n: int = 1200, live_from: int = 0) -> List[Dict[str, Any]]:
    start = datetime(2026, 11, 10, 0, 0, tzinfo=timezone.utc)
    bars: List[Dict[str, Any]] = []
    px = 3800.0
    cvd_acc = 0.0
    for i in range(n):
        dt = start + timedelta(minutes=i)
        ts_unix = int(dt.timestamp())
        sz, is_tr = classify_session_zone(dt)
        cyc = math.sin(i * 0.14) * 1.6 + math.cos(i * 0.04) * 0.8
        o = px
        c = px + cyc * 0.35 + (0.25 if (i % 19 == 0) else (-0.25 if i % 23 == 0 else 0.0))
        h = max(o, c) + 0.6 + (0.9 if i % 17 == 0 else 0.0)
        l = min(o, c) - 0.6 - (0.9 if i % 13 == 0 else 0.0)
        px = c

        is_live = i >= live_from
        delta_v = (i % 7 - 3) * 8.0 if is_live else None
        if delta_v is not None:
            cvd_acc += delta_v

        bars.append(
            {
                "time": dt.strftime("%Y-%m-%d %H:%M"),
                "ts_unix": ts_unix,
                "open": round(o, 3),
                "high": round(h, 3),
                "low": round(l, 3),
                "close": round(c, 3),
                "tickVolume": 100.0 + (i % 20) * 15.0,
                "spreadAvg": 0.12 + (i % 5) * 0.02 if is_live else None,
                "spreadMax": (0.18 + (0.25 if i % 29 == 0 else 0.0)) if is_live else None,
                "imbalance": math.sin(i * 0.3) * 0.08 if is_live else None,
                "depthUpdates": 180.0 + (i % 11) * 15.0 if is_live else None,
                "bidVol": 2000.0 + (i % 9) * 120.0 if is_live else None,
                "askVol": 2000.0 + ((i + 4) % 9) * 120.0 if is_live else None,
                "delta": delta_v,
                "cvd": cvd_acc if is_live else None,
                "vwapDay": 3800.0 if is_live else None,
                "sdDay": 1.8 if is_live else None,
                "vwapSession": 3800.0 if is_live else None,
                "poc": round(px, 2) if is_live else None,
                "vah": round(px + 2.5, 2) if is_live else None,
                "val": round(px - 2.5, 2) if is_live else None,
                "ladderBid": (1.1 + (i % 5) * 0.1) if is_live else None,
                "ladderAsk": (1.1 + ((i + 2) % 5) * 0.1) if is_live else None,
                "sweep": ("RL" if i % 41 == 0 else ("RH" if i % 43 == 0 else "")) if is_live else "",
                "has_l2_dom": is_live,
                "has_real_spread": is_live,
                "has_order_flow": is_live,
                "provenance": "HYBRID_FULL" if is_live else "CTRADER_OHLCV_ONLY",
                "session_zone": sz,
                "is_session_transition": is_tr,
            }
        )
    return bars


class TestPatternDiscovery(unittest.TestCase):
    def test_01_dual_htf_zero_lookahead_future_mutation(self):
        bars_a = _make_synthetic_m1_bars(n=1000, live_from=0)
        htf_a = {tf: resample_m1_to_tf(bars_a, TF_SECONDS[tf]) for tf in ("m5", "m15", "h1", "h4")}

        bars_b = [dict(b) for b in bars_a]
        t_cut = 620
        for i in range(t_cut + 1, len(bars_b)):
            bars_b[i]["open"] *= 10.0
            bars_b[i]["high"] *= 10.5
            bars_b[i]["low"] *= 9.5
            bars_b[i]["close"] *= 10.2
            bars_b[i]["tickVolume"] *= 50.0
            bars_b[i]["imbalance"] = -0.99
            bars_b[i]["delta"] = -9999.0
            bars_b[i]["depthUpdates"] = 9999.0
            bars_b[i]["bidVol"] = 10.0
            bars_b[i]["askVol"] = 99999.0
            bars_b[i]["ladderBid"] = 0.01
            bars_b[i]["ladderAsk"] = 99.0
        htf_b = {tf: resample_m1_to_tf(bars_b, TF_SECONDS[tf]) for tf in ("m5", "m15", "h1", "h4")}

        ds_a = build_scalping_mtf_dataset_from_bars("XAUUSD", bars_a, htf_bars_map=htf_a)
        ds_b = build_scalping_mtf_dataset_from_bars("XAUUSD", bars_b, htf_bars_map=htf_b)

        sl = slice(0, t_cut + 1)
        for k in (
            "atr14",
            "ema50",
            "rsi14",
            "vol_z_session",
            "delta_z_session",
            "imb_z_session",
            "depth_z_session",
            "ladder_asym_z_session",
            "book_vol_z_session",
            "spread_spike_ratio",
            "imb_z_delta",
        ):
            np.testing.assert_allclose(ds_a["m1"][k][sl], ds_b["m1"][k][sl], rtol=0.0, atol=1e-12)

        for tf in ("m5", "m15", "h1", "h4"):
            np.testing.assert_array_equal(ds_a["aligned_htf"][tf]["closed_idx"][sl], ds_b["aligned_htf"][tf]["closed_idx"][sl])
            np.testing.assert_allclose(ds_a["aligned_htf"][tf]["dev_ret_atr"][sl], ds_b["aligned_htf"][tf]["dev_ret_atr"][sl], rtol=0.0, atol=1e-12)

        lvl_a = extract_level_structure(ds_a["m1"], pivot_left=3, pivot_right=3, is_m1_live=True)
        lvl_b = extract_level_structure(ds_b["m1"], pivot_left=3, pivot_right=3, is_m1_live=True)
        ev_a = tokenize_m1_events(ds_a, lvl_a)
        ev_b = tokenize_m1_events(ds_b, lvl_b)
        for nm in ev_a:
            np.testing.assert_array_equal(ev_a[nm]["mask"][sl], ev_b[nm]["mask"][sl])

        ht_a = {tf: tokenize_htf_events(ds_a["htf"][tf], extract_level_structure(ds_a["htf"][tf], 2, 2)) for tf in ds_a["htf"]}
        ht_b = {tf: tokenize_htf_events(ds_b["htf"][tf], extract_level_structure(ds_b["htf"][tf], 2, 2)) for tf in ds_b["htf"]}
        proj_a = project_htf_events_to_m1(ds_a, ht_a)
        proj_b = project_htf_events_to_m1(ds_b, ht_b)
        for pk in proj_a:
            np.testing.assert_array_equal(proj_a[pk]["mask"][sl], proj_b[pk]["mask"][sl])

    def test_02_swing_pivot_confirmation_lag(self):
        bars = _make_synthetic_m1_bars(n=60, live_from=0)
        # Flatten highs and place one clear peak at index 20
        for i, b in enumerate(bars):
            base = 3800.0 - abs(i - 20) * 0.4
            b["open"] = base
            b["close"] = base + 0.05
            b["high"] = base + 0.15
            b["low"] = base - 0.15
        bars[20]["high"] = 3825.0

        tf_data = compute_causal_tf_indicators(bars, "XAUUSD", is_m1=True)
        lvl = extract_level_structure(tf_data, pivot_left=3, pivot_right=3)

        self.assertFalse(bool(lvl["confirmed_swing_high"][20]))
        self.assertFalse(bool(lvl["confirmed_swing_high"][21]))
        self.assertFalse(bool(lvl["confirmed_swing_high"][22]))
        self.assertTrue(bool(lvl["confirmed_swing_high"][23]))

    def test_03_episode_declustering(self):
        raw = np.array([10, 11, 12, 13, 25, 26], dtype=np.int64)
        dec = decluster_indices(raw, cooldown_bars=10)
        np.testing.assert_array_equal(dec, np.array([10, 25], dtype=np.int64))

    def test_04_price_anchored_sequence_and_invalidation(self):
        n = 80
        ts = np.arange(n, dtype=np.int64) * 60 + 1700000000
        cl = np.full(n, 3801.0, dtype=np.float64)
        hi = np.full(n, 3801.5, dtype=np.float64)
        lo = np.full(n, 3800.0, dtype=np.float64)
        atr = np.full(n, 1.0, dtype=np.float64)

        m1_data = {"n": n, "ts_unix": ts, "close": cl, "high": hi, "low": lo, "atr14": atr}

        sweep_mask = np.zeros(n, dtype=bool)
        reclaim_mask = np.zeros(n, dtype=bool)
        anchors = np.full(n, 3800.0, dtype=np.float64)

        # Case 1: valid gapped sequence 20 -> 26 (price stays >= 3800.0 > 3800 - 1.2*1.0)
        sweep_mask[20] = True
        reclaim_mask[26] = True

        # Case 2: invalidated sequence 50 -> 54 (bar 52 breaches 3798.0 < 3800 - 1.2)
        sweep_mask[50] = True
        lo[52] = 3798.0
        reclaim_mask[54] = True

        events = {
            "SWEEP_LOW": {"name": "SWEEP_LOW", "mask": sweep_mask, "anchor": anchors, "default_dir": "BUY", "requires_microstructure": False},
            "RECLAIM_LOW": {"name": "RECLAIM_LOW", "mask": reclaim_mask, "anchor": anchors, "default_dir": "BUY", "requires_microstructure": False},
        }
        out = match_anchored_sequence(m1_data, ["SWEEP_LOW", "RECLAIM_LOW"], events, max_gap=20)
        np.testing.assert_array_equal(out["indices"], np.array([26], dtype=np.int64))

    def test_05_microstructure_gating_on_ohlcv_only_bars(self):
        # First 120 bars lack L2 DOM & order flow (`CTRADER_OHLCV_ONLY`); bars 120..499 are live
        bars = _make_synthetic_m1_bars(n=500, live_from=120)
        ds = build_scalping_mtf_dataset_from_bars("BTCUSD", bars)
        lvl = extract_level_structure(ds["m1"], pivot_left=3, pivot_right=3, is_m1_live=True)
        ev = tokenize_m1_events(ds, lvl)

        micro_names = [nm for nm, e in ev.items() if e["requires_microstructure"]]
        self.assertGreaterEqual(len(micro_names), 24)
        for nm in micro_names:
            self.assertFalse(bool(ev[nm]["mask"][:120].any()), f"{nm} leaked onto CTRADER_OHLCV_ONLY gap bars!")

    def test_06_3state_probabilities_and_20_fields_schema(self):
        bars = _make_synthetic_m1_bars(n=1400, live_from=0)
        htf = {tf: resample_m1_to_tf(bars, TF_SECONDS[tf]) for tf in ("m5", "m15", "h1", "h4")}
        ds = build_scalping_mtf_dataset_from_bars("XAUUSD", bars, htf_bars_map=htf)

        out = analyze_symbol_patterns("XAUUSD", fetch_ctrader=False, preloaded_dataset=ds)
        conds = out["conditions"]
        self.assertGreater(len(conds), 10)
        self.assertGreater(out["summary_counts"]["round2_tested"], 0)

        for entry in conds[:15]:
            for field in REQUIRED_20_FIELDS:
                self.assertIn(field, entry, f"Missing required field {field!r} in {entry.get('condition_name')}")
            for hk, hvals in entry["probability"]["horizons_oos"].items():
                s = hvals["p_bull"] + hvals["p_bear"] + hvals["p_neutral"]
                if s > 0:
                    self.assertAlmostEqual(s, 1.0, delta=0.002, msg=f"Probability conservation violated on {hk}")

    def test_07_orderbook_flip_stack_and_spread_snapback_mechanics(self):
        n = 60
        ts = np.arange(n, dtype=np.int64) * 60 + 1700000000
        m1 = {
            "n": n,
            "open": np.full(n, 3800.0),
            "high": np.full(n, 3800.6),
            "low": np.full(n, 3799.6),
            "close": np.full(n, 3800.2),
            "atr14": np.full(n, 1.0),
            "atr60_mean": np.full(n, 1.0),
            "range_atr": np.full(n, 1.0),
            "body_ratio": np.full(n, 0.5),
            "upper_wick_ratio": np.full(n, 0.25),
            "lower_wick_ratio": np.full(n, 0.25),
            "prev_hh20": np.full(n, 3802.0),
            "prev_ll20": np.full(n, 3798.0),
            "rsi14": np.full(n, 50.0),
            "vwap_z": np.zeros(n),
            "vol_z_session": np.zeros(n),
            "spread_z_session": np.zeros(n),
            "delta_z_session": np.zeros(n),
            "imb_z_session": np.zeros(n),
            "imb_z_delta": np.zeros(n),
            "ladder_asym_z_session": np.zeros(n),
            "depth_z_session": np.zeros(n),
            "book_vol_z_session": np.zeros(n),
            "spread_spike_ratio": np.ones(n),
            "cvd_slope5": np.zeros(n),
            "price_slope5": np.zeros(n),
            "accel_atr": np.zeros(n),
            "imbalance": np.zeros(n),
            "delta": np.zeros(n),
            "poc": np.full(n, np.nan),
            "vah": np.full(n, np.nan),
            "val": np.full(n, np.nan),
            "live_sweep_low": np.zeros(n, dtype=bool),
            "live_sweep_high": np.zeros(n, dtype=bool),
            "has_l2_dom": np.ones(n, dtype=bool),
            "has_real_spread": np.ones(n, dtype=bool),
            "has_order_flow": np.ones(n, dtype=bool),
        }
        # DOM Flip Bull at bar 20: prior ask-heavy (-1.2) -> sudden bid-heavy (+1.1, delta +2.3)
        m1["imb_z_session"][19] = -1.2
        m1["imb_z_session"][20] = 1.1
        m1["imb_z_delta"][20] = 2.3
        # DOM Stack Bull completing 3rd bar at bar 32
        m1["imb_z_session"][30:33] = 0.95
        # Ladder Thin Ask at bar 35
        m1["ladder_asym_z_session"][35] = 1.8
        # Spread Blowout at bar 40 -> Snapback at bar 41
        m1["spread_z_session"][40] = 2.0
        m1["spread_spike_ratio"][40] = 1.8
        m1["spread_z_session"][41] = 0.2
        m1["spread_spike_ratio"][41] = 1.1

        zeros_b = np.zeros(n, dtype=bool)
        lvl = {k: zeros_b for k in (
            "sweep_low", "sweep_high", "false_breakout_up", "false_breakout_down",
            "reclaim_low", "reclaim_high", "retest_support_2x", "retest_resist_2x",
            "bos_bull", "bos_bear", "choch_bull", "choch_bear", "higher_low", "lower_high",
        )}
        lvl["anchor_bull"] = m1["low"]
        lvl["anchor_bear"] = m1["high"]

        ds = {"m1": m1, "spec": {"imb_th": 0.018}}
        ev = tokenize_m1_events(ds, lvl, jitter_scale=1.0)

        self.assertTrue(bool(ev["DOM_FLIP_BULL"]["mask"][20]))
        self.assertFalse(bool(ev["DOM_FLIP_BULL"]["mask"][19]))
        self.assertTrue(bool(ev["DOM_STACK_BULL"]["mask"][32]))
        self.assertFalse(bool(ev["DOM_STACK_BULL"]["mask"][31]))
        self.assertTrue(bool(ev["LADDER_THIN_ASK"]["mask"][35]))
        self.assertTrue(bool(ev["SPREAD_SNAPBACK"]["mask"][41]))
        self.assertFalse(bool(ev["SPREAD_SNAPBACK"]["mask"][40]))

    def test_08_session_specific_mining_strict_zone_isolation(self):
        # 2 full days (2880 M1 bars) so NY and ASIA each contain ample samples
        bars = _make_synthetic_m1_bars(n=2880, live_from=0)
        htf = {tf: resample_m1_to_tf(bars, TF_SECONDS[tf]) for tf in ("m5", "m15", "h1", "h4")}
        ds = build_scalping_mtf_dataset_from_bars("XAUUSD", bars, htf_bars_map=htf)

        lvl = extract_level_structure(ds["m1"], 3, 3, is_m1_live=True)
        ev = tokenize_m1_events(ds, lvl)
        baselines = compute_regime_baselines(ds)
        singles = mine_single_conditions(ds, ev, baselines)

        ses_out = mine_session_specific_patterns(ds, ev, {}, singles, baselines, existing_names=set())
        ses_conds = ses_out["session_conditions"]
        self.assertGreater(len(ses_conds), 0)

        sample = ses_conds[0]
        self.assertIn("session_lift_vs_allday", sample)
        self.assertIn("delta_oos_exp_vs_allday", sample["session_lift_vs_allday"])
        zone = sample["session_scope"]
        self.assertTrue(sample["condition_name"].startswith(f"SES[{zone}]: "))
        # Ensure all OOS session breakdown trades belong strictly to `zone`
        self.assertEqual(set(sample["session_breakdown_oos"].keys()), {zone})


if __name__ == "__main__":
    unittest.main()
