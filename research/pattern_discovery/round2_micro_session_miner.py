"""
Iteration Round 2 Miner: Order Book Imbalance, 7-Zone Session Mining & XAU/BTC Microstructure
=============================================================================================
Builds on Round 1 without modifying Round 1's discovery signatures:
1. Order Book Imbalance & Microstructure Sequences (2-4 steps) using L2 DOM flips,
   stacking, 25-level ladder asymmetry, depth churn, spread snapback, and Value Area.
2. 7-Zone Session-Specific Pattern Mining evaluating strictly session-scoped triggers
   and measuring exact `session_lift_vs_allday`.
3. XAUUSD & BTCUSD Deep Microstructure x Multi-Timeframe Fusion (`mine_micro_mtf_fusion`).
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np

from research.pattern_discovery.sequence_mtf_miner import (
    _dirs_compatible,
    match_anchored_sequence,
)
from research.pattern_discovery.statistical_validator import evaluate_condition

ACTIVE_SESSIONS_BY_SYMBOL: Dict[str, Tuple[str, ...]] = {
    "XAUUSD": ("ASIA", "ASIA_TO_LONDON", "LONDON", "LONDON_TO_NY", "NY", "NY_TO_CLOSE"),
    "BTCUSD": ("ASIA", "LONDON", "LONDON_TO_NY", "NY", "OVERNIGHT"),
    "ETHUSD": ("LONDON", "LONDON_TO_NY", "NY"),
}

CURATED_ORDERBOOK_SEQUENCES: Tuple[Tuple[List[str], str, str], ...] = (
    # Flip & Stack (2-3 steps)
    (["SWEEP_LOW", "DOM_FLIP_BULL"], "BUY", "Sweep Low ตามด้วย Order Book พลิกเป็น Bid-heavy ฉับพลัน"),
    (["SWEEP_LOW", "DOM_FLIP_BULL", "DISPLACEMENT_BULL"], "BUY", "Sweep Low -> DOM Flip Bull -> แท่ง Impulse พุ่งขึ้น"),
    (["SWEEP_HIGH", "DOM_FLIP_BEAR"], "SELL", "Sweep High ตามด้วย Order Book พลิกเป็น Ask-heavy ฉับพลัน"),
    (["SWEEP_HIGH", "DOM_FLIP_BEAR", "DISPLACEMENT_BEAR"], "SELL", "Sweep High -> DOM Flip Bear -> แท่ง Impulse ทุบลง"),
    (["DOM_STACK_BULL", "BREAKOUT_UP"], "BUY", "L2 Bid Stacking 3 นาทีต่อเนื่อง -> เบรก High ขึ้น"),
    (["DOM_STACK_BEAR", "BREAKOUT_DOWN"], "SELL", "L2 Ask Stacking 3 นาทีต่อเนื่อง -> หลุด Low ลง"),
    (["DOM_STACK_BULL", "LADDER_THIN_ASK"], "BUY", "L2 Bid Stacking -> ฝั่ง Ask 25 ชั้นบางลง เปิดทางวิ่งขึ้น"),
    (["DOM_STACK_BEAR", "LADDER_THIN_BID"], "SELL", "L2 Ask Stacking -> ฝั่ง Bid 25 ชั้นบางลง เปิดทางทิ้งตัว"),
    (["DOM_FLIP_BULL", "LADDER_THIN_ASK", "EXPANSION"], "BUY", "DOM Flip Bull -> Ask Vacuum -> แท่งขยายตัวพุ่งขึ้น"),
    (["DOM_FLIP_BEAR", "LADDER_THIN_BID", "EXPANSION"], "SELL", "DOM Flip Bear -> Bid Vacuum -> แท่งขยายตัวทุบลง"),
    # Iceberg & Vacuum
    (["DEPTH_ICEBERG_BATTLE", "DOM_IMBALANCE_BULL", "DISPLACEMENT_BULL"], "BUY", "ปะทะ Quote Churn สูง -> ชนะด้วย Bid Imbalance -> Impulse ขึ้น"),
    (["DEPTH_ICEBERG_BATTLE", "DOM_IMBALANCE_BEAR", "DISPLACEMENT_BEAR"], "SELL", "ปะทะ Quote Churn สูง -> ชนะด้วย Ask Imbalance -> Impulse ลง"),
    (["DEPTH_ICEBERG_BATTLE", "CVD_SURGE_BULL"], "BUY", "ปะทะคำสั่งหนาแน่น -> Order Flow Delta ฝั่งซื้อระเบิดนำ"),
    (["DEPTH_ICEBERG_BATTLE", "CVD_SURGE_BEAR"], "SELL", "ปะทะคำสั่งหนาแน่น -> Order Flow Delta ฝั่งขายระเบิดนำ"),
    (["COMPRESSION", "LADDER_THIN_ASK", "BREAKOUT_UP"], "BUY", "บีบอัดแคบ -> Ask Ladder บาง -> เบรกขึ้นบน"),
    (["COMPRESSION", "LADDER_THIN_BID", "BREAKOUT_DOWN"], "SELL", "บีบอัดแคบ -> Bid Ladder บาง -> เบรกหลุดล่าง"),
    # Spread Snapback
    (["SPREAD_EXPANSION", "SPREAD_SNAPBACK", "DOM_ABSORPTION_BUY"], "BUY", "Spread ถ่าง -> Snapback สภาพคล่องกลับ -> Bid Absorption รับขึ้น"),
    (["SPREAD_EXPANSION", "SPREAD_SNAPBACK", "DOM_ABSORPTION_SELL"], "SELL", "Spread ถ่าง -> Snapback สภาพคล่องกลับ -> Ask Absorption ตบลง"),
    (["LIQUIDITY_PULL_SHOCK", "SPREAD_SNAPBACK", "RECLAIM_LOW"], "BUY", "Liquidity Pull Shock -> สเปรดหดกลับ -> Reclaim เหนือแนวรับ"),
    (["LIQUIDITY_PULL_SHOCK", "SPREAD_SNAPBACK", "RECLAIM_HIGH"], "SELL", "Liquidity Pull Shock -> สเปรดหดกลับ -> Reclaim ต่ำกว่าแนวต้าน"),
    # Value Area & Native Flow CSV Sweeps
    (["VA_REJECT_VAL", "DOM_IMBALANCE_BULL"], "BUY", "ปฏิเสธหลุด Value Area Low (VAL) พร้อม Bid Imbalance"),
    (["VA_REJECT_VAH", "DOM_IMBALANCE_BEAR"], "SELL", "ปฏิเสธเบรก Value Area High (VAH) พร้อม Ask Imbalance"),
    (["VA_REJECT_VAL", "DELTA_DIVERGENCE_BULL", "POC_RECLAIM_BULL"], "BUY", "VAL Rejection -> Bullish Delta Divergence -> Reclaim POC ขึ้น"),
    (["VA_REJECT_VAH", "DELTA_DIVERGENCE_BEAR", "POC_RECLAIM_BEAR"], "SELL", "VAH Rejection -> Bearish Delta Divergence -> หลุด POC ลง"),
    (["FLOW_SWEEP_LOW", "DOM_FLIP_BULL"], "BUY", "Native Flow Sweep Low -> L2 DOM Flip Bull"),
    (["FLOW_SWEEP_HIGH", "DOM_FLIP_BEAR"], "SELL", "Native Flow Sweep High -> L2 DOM Flip Bear"),
    (["FLOW_SWEEP_LOW", "RECLAIM_LOW+DOM_IMBALANCE_BULL"], "BUY", "Native Flow Sweep Low -> Reclaim พร้อม L2 Bid Imbalance"),
    (["FLOW_SWEEP_HIGH", "RECLAIM_HIGH+DOM_IMBALANCE_BEAR"], "SELL", "Native Flow Sweep High -> Reclaim พร้อม L2 Ask Imbalance"),
)

CURATED_MICRO_MTF_FUSION: Tuple[Tuple[str, str, str, str, str], ...] = (
    ("H1_TREND_BULL", "M15_PULLBACK_BULL", "DOM_FLIP_BULL", "BUY", "H1 ขาขึ้น + M15 ย่อพักตัว + M1 DOM Flip กลับฝั่งซื้อ"),
    ("H1_TREND_BEAR", "M15_PULLBACK_BEAR", "DOM_FLIP_BEAR", "SELL", "H1 ขาลง + M15 ดีดรีเทสต์ + M1 DOM Flip กลับฝั่งขาย"),
    ("H1_TREND_BULL", "M15_PULLBACK_BULL", "DOM_STACK_BULL", "BUY", "H1 ขาขึ้น + M15 ย่อพักตัว + M1 Bid Stacking ต่อเนื่อง"),
    ("H1_TREND_BEAR", "M15_PULLBACK_BEAR", "DOM_STACK_BEAR", "SELL", "H1 ขาลง + M15 ดีดรีเทสต์ + M1 Ask Stacking ต่อเนื่อง"),
    ("H1_RANGE", "M15_SWEEP_LOW", "DOM_FLIP_BULL", "BUY", "H1 กรอบ Range + M15 Sweep Low + M1 DOM Flip Bull"),
    ("H1_RANGE", "M15_SWEEP_HIGH", "DOM_FLIP_BEAR", "SELL", "H1 กรอบ Range + M15 Sweep High + M1 DOM Flip Bear"),
    ("H1_NEAR_SUPPORT", "DEV_H1_REJECTION_BULL", "LADDER_THIN_ASK", "BUY", "H1 แนวรับ + แท่ง H1 กำลังทิ้งไส้ล่าง + M1 Ask Ladder บาง"),
    ("H1_NEAR_RESIST", "DEV_H1_REJECTION_BEAR", "LADDER_THIN_BID", "SELL", "H1 แนวต้าน + แท่ง H1 กำลังทิ้งไส้บน + M1 Bid Ladder บาง"),
    ("H1_RANGE", "", "VA_REJECT_VAL", "BUY", "H1 Range + M1 Reject หลุด VAL กลับเข้ากรอบ"),
    ("H1_RANGE", "", "VA_REJECT_VAH", "SELL", "H1 Range + M1 Reject เหนือ VAH กลับลงกรอบ"),
    ("M15_SWEEP_LOW", "", "DOM_FLIP_BULL", "BUY", "M15 Sweep Low + M1 L2 DOM Flip Bull"),
    ("M15_SWEEP_HIGH", "", "DOM_FLIP_BEAR", "SELL", "M15 Sweep High + M1 L2 DOM Flip Bear"),
    ("M15_SWEEP_LOW", "", "VA_REJECT_VAL", "BUY", "M15 Sweep Low + M1 VAL Rejection"),
    ("M15_SWEEP_HIGH", "", "VA_REJECT_VAH", "SELL", "M15 Sweep High + M1 VAH Rejection"),
    ("H1_TREND_BULL", "", "LADDER_THIN_ASK", "BUY", "H1 ขาขึ้น + M1 Ask Ladder บางเปิดทางขึ้น"),
    ("H1_TREND_BEAR", "", "LADDER_THIN_BID", "SELL", "H1 ขาลง + M1 Bid Ladder บางเปิดทางลง"),
)


def _step_valid(step_spec: str, events: Dict[str, Dict[str, Any]]) -> bool:
    return all(p.strip() in events for p in step_spec.split("+") if p.strip())


def mine_orderbook_sequences(
    dataset: Dict[str, Any],
    events: Dict[str, Dict[str, Any]],
    single_results: List[Dict[str, Any]],
    baselines: Dict[Any, Any],
    existing_names: Optional[Set[str]] = None,
    max_gap: int = 18,
) -> Dict[str, Any]:
    """
    Mines Order Book Imbalance, Liquidity Ladder, Iceberg Battle, Spread Snapback &
    Value Area Multi-Step Sequences (2-4 steps) tagged as Round 2.
    """
    m1 = dataset["m1"]
    single_by_name = {r["condition_name"]: r for r in single_results}
    existing = existing_names or set()
    seq_cache: Dict[Tuple[str, ...], Dict[str, Any]] = {}

    def _eval_ob_seq(steps: List[str], pref_dir: str, desc: str) -> Optional[Dict[str, Any]]:
        key = tuple(steps)
        if key in seq_cache:
            return seq_cache[key]
        cname_str = " -> ".join(steps)
        full_name = f"SEQ: {cname_str}"
        if full_name in existing:
            return None

        matched = match_anchored_sequence(m1, steps, events, max_gap=max_gap)
        meta = {
            "condition_name": full_name,
            "condition_type": "Sequential",
            "timeframes": ["M1"],
            "pre_condition": f"Order Book Anchor at {steps[0]} (Live L2 DOM / Flow gated)",
            "event_sequence": list(steps),
            "formatted_sequence": f"M1 OrderBook Sequence [{cname_str}] -> Next-Bar Open Entry -> Expected Outcome",
            "entry_criteria": desc,
            "requires_microstructure": True,
            "data_tier_provenance": "MICROSTRUCTURE_LIVE",
            "discovery_round": 2,
            "session_scope": "ALL",
            "sequence_timing": {
                "avg_gap_bars": matched["avg_gap_bars"],
                "avg_atr_speed": matched["avg_atr_speed"],
                "pct_immediate": matched["pct_immediate"],
            },
        }
        ev = evaluate_condition(dataset, baselines, matched["indices"], pref_dir, meta, cooldown_bars=10)
        seq_cache[key] = ev
        return ev

    # 1. Curated 28 Order Book sequences
    for steps, pdir, desc in CURATED_ORDERBOOK_SEQUENCES:
        if all(_step_valid(s, events) for s in steps):
            if len(steps) >= 3:
                p2 = steps[:2]
                if all("+" not in p for p in p2) and tuple(p2) not in seq_cache and f"SEQ: {' -> '.join(p2)}" not in existing:
                    _eval_ob_seq(p2, pdir, f"OrderBook Prefix {p2[0]} -> {p2[1]}")
            _eval_ob_seq(steps, pdir, desc)

    # 2. Data-Driven Order Book Sequence Mining (2-step -> 3-step)
    micro_singles = [
        r for r in single_results
        if events[r["condition_name"]]["requires_microstructure"] and r["sample_size_is"] >= 10
    ]
    micro_singles.sort(
        key=lambda r: (abs(r["probability"]["is_primary"].get("lift_bull", 0.0) - r["probability"]["is_primary"].get("lift_bear", 0.0)) + max(0.0, r["expectancy"]["is_usd"])),
        reverse=True,
    )
    top_micro = micro_singles[:10]

    struct_singles = [
        r for r in single_results
        if (events[r["condition_name"]]["tier"] == "MILESTONE" or events[r["condition_name"]]["requires_microstructure"])
        and r["sample_size_is"] >= 12
    ]
    struct_singles.sort(key=lambda r: r["expectancy"]["is_usd"], reverse=True)
    top_b = struct_singles[:8]

    promising_2: List[Dict[str, Any]] = []
    for a in top_micro:
        na = a["condition_name"]
        da = events[na]["default_dir"]
        for b in top_b:
            nb = b["condition_name"]
            if nb == na:
                continue
            db = events[nb]["default_dir"]
            if not _dirs_compatible(da, db):
                continue
            pref = da if da in ("BUY", "SELL") else db
            ev2 = _eval_ob_seq([na, nb], pref, f"Data-mined OrderBook 2-step: {na} -> {nb}")
            if ev2 is not None and ev2["sample_size_total"] >= 12 and ev2["expectancy"]["is_usd"] > 0.0:
                promising_2.append(ev2)

    promising_2.sort(key=lambda r: r["expectancy"]["is_usd"], reverse=True)
    for p2 in promising_2[:10]:
        s2 = p2["event_sequence"]
        dp = p2["direction"]
        for c in top_b[:6]:
            nc = c["condition_name"]
            if nc == s2[-1]:
                continue
            if _dirs_compatible(dp, events[nc]["default_dir"]):
                _eval_ob_seq([s2[0], s2[1], nc], dp, f"Data-mined OrderBook 3-step: {s2[0]} -> {s2[1]} -> {nc}")

    out_list = list(seq_cache.values())

    # 3. Ablation Incremental Lift annotation
    for seq_res in out_list:
        steps = seq_res["event_sequence"]
        first_base = single_by_name.get(steps[0].split("+")[0])
        prev_prefix = seq_cache.get(tuple(steps[:-1])) if len(steps) >= 3 else first_base
        oos_p = seq_res["probability"]["oos_dir_prob"]
        oos_e = seq_res["expectancy"]["oos_usd"]
        dp_prev = round(oos_p - prev_prefix["probability"]["oos_dir_prob"], 4) if prev_prefix else None
        de_prev = round(oos_e - prev_prefix["expectancy"]["oos_usd"], 4) if prev_prefix else None
        dp_base = round(oos_p - first_base["probability"]["oos_dir_prob"], 4) if first_base else None
        de_base = round(oos_e - first_base["expectancy"]["oos_usd"], 4) if first_base else None
        seq_res["ablation_lift"] = {
            "base_event": steps[0],
            "prev_step": " -> ".join(steps[:-1]),
            "delta_oos_prob_vs_prev": dp_prev,
            "delta_oos_exp_vs_prev": de_prev,
            "delta_oos_prob_vs_base": dp_base,
            "delta_oos_exp_vs_base": de_base,
            "adds_predictive_power": bool((de_prev or 0.0) > 0.0 or (dp_prev or 0.0) > 0.02),
        }

    # 4. Order Book Branching Patterns
    by_pref: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for r in out_list:
        if r["sample_size_total"] >= 8:
            by_pref[" -> ".join(r["event_sequence"][:-1])].append(r)

    ob_branches: List[Dict[str, Any]] = []
    for pref, children in by_pref.items():
        if len(children) < 2:
            continue
        dirs = {c["direction"] for c in children}
        exps = [c["expectancy"]["oos_usd"] for c in children]
        if len(dirs) >= 2 or (max(exps) - min(exps) >= 0.25):
            ob_branches.append(
                {
                    "shared_prefix": pref,
                    "branches": [
                        {
                            "next_step": c["event_sequence"][-1],
                            "direction": c["direction"],
                            "sample_size": c["sample_size_total"],
                            "oos_dir_prob": c["probability"]["oos_dir_prob"],
                            "oos_expectancy_usd": c["expectancy"]["oos_usd"],
                            "validation_status": c["validation_status"],
                        }
                        for c in sorted(children, key=lambda x: x["expectancy"]["oos_usd"], reverse=True)[:4]
                    ],
                }
            )
    ob_branches.sort(key=lambda g: len(g["branches"]), reverse=True)

    return {
        "orderbook_sequences": out_list,
        "orderbook_branching_patterns": ob_branches[:8],
    }


def mine_micro_mtf_fusion(
    dataset: Dict[str, Any],
    events: Dict[str, Dict[str, Any]],
    htf_projected: Dict[str, Dict[str, Any]],
    baselines: Dict[Any, Any],
    existing_names: Optional[Set[str]] = None,
) -> List[Dict[str, Any]]:
    """
    Evaluates deep Tier 2 HTF/MTF x Tier 1 Order Book Microstructure Fusion setups
    for XAUUSD & BTCUSD.
    """
    existing = existing_names or set()
    results: List[Dict[str, Any]] = []

    for htf_k, mtf_k, ltf_k, pdir, desc in CURATED_MICRO_MTF_FUSION:
        if htf_k not in htf_projected or ltf_k not in events:
            continue
        if mtf_k and mtf_k not in htf_projected:
            continue

        hk = htf_projected[htf_k]
        lk = events[ltf_k]
        if mtf_k:
            mk = htf_projected[mtf_k]
            mask = hk["mask"] & mk["mask"] & lk["mask"]
            tfs = sorted({hk["tf"].upper(), mk["tf"].upper(), "M1"})
            seq_tokens = [htf_k, mtf_k, f"M1_{ltf_k}"]
            cname = f"MTF: {htf_k} -> {mtf_k} -> M1_{ltf_k}"
            pre = f"{hk['desc']} + {mk['desc']}"
            fmt = f"{htf_k} -> {mtf_k} -> M1 [{ltf_k}] -> Next-Bar Open Entry -> Expected Outcome"
        else:
            mask = hk["mask"] & lk["mask"]
            tfs = sorted({hk["tf"].upper(), "M1"})
            seq_tokens = [htf_k, f"M1_{ltf_k}"]
            cname = f"MTF: {htf_k} -> M1_{ltf_k}"
            pre = hk["desc"]
            fmt = f"{htf_k} -> M1 [{ltf_k}] -> Next-Bar Open Entry -> Expected Outcome"

        if cname in existing:
            continue

        idxs = np.flatnonzero(mask)
        meta = {
            "condition_name": cname,
            "condition_type": "Multi-TF",
            "timeframes": tfs,
            "pre_condition": pre,
            "event_sequence": seq_tokens,
            "formatted_sequence": fmt,
            "entry_criteria": desc,
            "requires_microstructure": True,
            "data_tier_provenance": "MICROSTRUCTURE_LIVE",
            "discovery_round": 2,
            "session_scope": "ALL",
            "sequence_timing": {"avg_gap_bars": 0.0, "avg_atr_speed": 0.0, "pct_immediate": 1.0},
        }
        ev = evaluate_condition(dataset, baselines, idxs, pdir, meta, cooldown_bars=12)
        results.append(ev)

    return results


def _reconstruct_candidate_indices(
    candidate: Dict[str, Any],
    m1: Dict[str, Any],
    events: Dict[str, Dict[str, Any]],
    htf_projected: Dict[str, Dict[str, Any]],
) -> np.ndarray:
    ctype = candidate["condition_type"]
    steps = candidate["event_sequence"]
    if ctype == "Single":
        nm = steps[0]
        return np.flatnonzero(events[nm]["mask"]) if nm in events else np.zeros(0, dtype=np.int64)
    if ctype == "Sequential":
        if all(_step_valid(s, events) for s in steps):
            return match_anchored_sequence(m1, steps, events, max_gap=20)["indices"]
        return np.zeros(0, dtype=np.int64)
    # Multi-TF
    ltf_raw = steps[-1].replace("M1_", "")
    if ltf_raw not in events:
        return np.zeros(0, dtype=np.int64)
    mask = events[ltf_raw]["mask"].copy()
    for htok in steps[:-1]:
        if htok not in htf_projected:
            return np.zeros(0, dtype=np.int64)
        mask &= htf_projected[htok]["mask"]
    return np.flatnonzero(mask)


def mine_session_specific_patterns(
    dataset: Dict[str, Any],
    events: Dict[str, Dict[str, Any]],
    htf_projected: Dict[str, Dict[str, np.ndarray]],
    all_base_results: List[Dict[str, Any]],
    baselines: Dict[Any, Any],
    existing_names: Optional[Set[str]] = None,
) -> Dict[str, Any]:
    """
    Round 2 7-Zone Session-Specific Mining:
    Masks promising Single, Sequential & MTF candidates strictly inside each session zone
    and measures IS/OOS 60/40, 3-Fold Walk-Forward & `session_lift_vs_allday`.
    """
    m1 = dataset["m1"]
    sym = str(dataset["symbol"])
    sz_arr = m1["session_zone"]
    existing = existing_names or set()

    if sym in ACTIVE_SESSIONS_BY_SYMBOL:
        target_zones = ACTIVE_SESSIONS_BY_SYMBOL[sym]
    else:
        # Synthetic/unknown symbol fallback: pick zones with >= 40 bars
        zone_counts: Dict[str, int] = defaultdict(int)
        for z in sz_arr:
            zone_counts[str(z)] += 1
        target_zones = tuple(z for z, c in zone_counts.items() if c >= 40)

    # Select candidate pool strictly using IS metrics (no OOS peeking!)
    singles_all = [r for r in all_base_results if r["condition_type"] == "Single"]
    seqs_all = [r for r in all_base_results if r["condition_type"] == "Sequential"]
    mtfs_all = [r for r in all_base_results if r["condition_type"] == "Multi-TF"]

    def _is_rank_key(r: Dict[str, Any]) -> Tuple[int, float]:
        return (1 if r.get("requires_microstructure") else 0, r["expectancy"]["is_usd"] * np.sqrt(max(1, r["sample_size_is"])))

    min_is_s = 25 if len(singles_all) > 10 and any(r["sample_size_is"] >= 25 for r in singles_all) else 5
    min_is_q = 20 if any(r["sample_size_is"] >= 20 for r in seqs_all) else 5
    min_is_m = 20 if any(r["sample_size_is"] >= 20 for r in mtfs_all) else 5

    s_pool = sorted([r for r in singles_all if r["sample_size_is"] >= min_is_s], key=_is_rank_key, reverse=True)[:14]
    q_pool = sorted([r for r in seqs_all if r["sample_size_is"] >= min_is_q], key=_is_rank_key, reverse=True)[:10]
    m_pool = sorted([r for r in mtfs_all if r["sample_size_is"] >= min_is_m], key=_is_rank_key, reverse=True)[:8]

    pool = s_pool + q_pool + m_pool
    idx_cache: Dict[str, np.ndarray] = {}
    for cand in pool:
        idx_cache[cand["condition_name"]] = _reconstruct_candidate_indices(cand, m1, events, htf_projected)

    session_results: List[Dict[str, Any]] = []
    by_zone: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

    for zone in target_zones:
        zone_mask = (sz_arr == zone)
        if int(np.sum(zone_mask)) < 30:
            continue

        for cand in pool:
            base_name = cand["condition_name"]
            full_name = f"SES[{zone}]: {base_name}"
            if full_name in existing:
                continue

            raw_idx = idx_cache[base_name]
            if len(raw_idx) == 0:
                continue
            z_idx = raw_idx[zone_mask[raw_idx]]
            if len(z_idx) < 12:
                continue

            is_micro = bool(cand.get("requires_microstructure", False))
            ctype_ses = "Session-Micro" if is_micro else "Session-Specific"
            meta = {
                "condition_name": full_name,
                "condition_type": ctype_ses,
                "timeframes": list(cand["timeframes"]),
                "pre_condition": f"[{zone} Session Only] {cand['pre_condition']}",
                "event_sequence": list(cand["event_sequence"]),
                "formatted_sequence": f"[{zone}] {cand['formatted_sequence']}",
                "entry_criteria": f"เฉพาะช่วง {zone}: {cand['entry_criteria']}",
                "requires_microstructure": is_micro,
                "data_tier_provenance": cand.get("data_tier_provenance", "HYBRID_LIVE_M1"),
                "discovery_round": 2,
                "session_scope": zone,
                "base_condition_ref": base_name,
                "base_condition_type": cand["condition_type"],
                "sequence_timing": cand.get("sequence_timing", {"avg_gap_bars": 0.0, "avg_atr_speed": 0.0, "pct_immediate": 1.0}),
            }
            ev = evaluate_condition(dataset, baselines, z_idx, cand["direction"], meta, cooldown_bars=10)

            allday_exp = float(cand["expectancy"]["oos_usd"])
            ses_exp = float(ev["expectancy"]["oos_usd"])
            ev["session_lift_vs_allday"] = {
                "allday_oos_exp_usd": allday_exp,
                "session_oos_exp_usd": ses_exp,
                "delta_oos_exp_vs_allday": round(ses_exp - allday_exp, 4),
                "allday_oos_pf": cand["profit_factor"]["oos"],
                "session_oos_pf": ev["profit_factor"]["oos"],
                "improves_over_allday": ses_exp > allday_exp,
            }
            session_results.append(ev)
            by_zone[zone].append(ev)

    # Build Session Playbook selecting best pattern per zone
    status_prio = {
        "VALIDATED_OOS": 5,
        "REGIME_SPECIFIC_EDGE": 4,
        "RARE_HIGH_EDGE": 3,
        "IS_ONLY_OVERFIT": 2,
        "NO_EDGE": 1,
        "INSUFFICIENT_DATA": 0,
    }
    session_playbook: Dict[str, Dict[str, Any]] = {}
    for zone, zrows in by_zone.items():
        if not zrows:
            continue
        best = max(
            zrows,
            key=lambda r: (
                status_prio.get(r["validation_status"], 0),
                r["expectancy"]["oos_usd"] * np.sqrt(max(1, r["sample_size_oos"])),
            ),
        )
        session_playbook[zone] = {
            "best_condition": best["condition_name"],
            "condition_type": best["condition_type"],
            "direction": best["direction"],
            "sample_size": best["sample_size_total"],
            "sample_is_oos": f"{best['sample_size_is']}/{best['sample_size_oos']}",
            "oos_win_rate": best["win_rate"]["oos"],
            "oos_expectancy_usd": best["expectancy"]["oos_usd"],
            "oos_profit_factor": best["profit_factor"]["oos"],
            "allday_oos_exp_usd": best["session_lift_vs_allday"]["allday_oos_exp_usd"],
            "delta_oos_exp_vs_allday": best["session_lift_vs_allday"]["delta_oos_exp_vs_allday"],
            "validation_status": best["validation_status"],
            "sl_atr": best["sl_atr"],
            "tp_atr": best["tp_atr"],
        }

    return {
        "session_conditions": session_results,
        "session_playbook": session_playbook,
    }
