"""
3-Round Pattern Miner: Single Conditions, Price-Anchored Sequences & MTF Confluence (Step 6)
===========================================================================================
Implements:
- Round 1: Single-Condition Discovery (all 42 M1 atomic events).
- Round 2: Price-Anchored Multi-Step Sequence Mining (2 to N steps), with gap/speed
  tracking, invalidation rules, ablation incremental lift (A vs A->B vs A->B->C),
  Branching Patterns, and Converging Patterns.
- Round 3: Dual-HTF Multi-Timeframe Relationships (H4/H1 Context + M15/M5 Setup + M1 Trigger),
  temporal ordering checks, and empirical Confluence Proof (1 TF vs 2 TF vs 3+ TF).
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from research.pattern_discovery.statistical_validator import (
    compute_regime_baselines,
    evaluate_condition,
)


def _resolve_step(step_spec: str, events: Dict[str, Dict[str, Any]]) -> Tuple[np.ndarray, np.ndarray, str, bool]:
    """Resolves a step spec like `RECLAIM_LOW` or `RECLAIM_LOW+DOM_ABSORPTION_BUY`."""
    parts = [p.strip() for p in step_spec.split("+") if p.strip()]
    primary = events[parts[0]]
    mask = primary["mask"].copy()
    anchor = primary["anchor"]
    default_dir = primary["default_dir"]
    req_micro = bool(primary["requires_microstructure"])
    for p in parts[1:]:
        ev = events[p]
        mask = mask & ev["mask"]
        req_micro = req_micro or bool(ev["requires_microstructure"])
        if default_dir == "AUTO" and ev["default_dir"] in ("BUY", "SELL"):
            default_dir = ev["default_dir"]
    return mask, anchor, default_dir, req_micro


def match_anchored_sequence(
    m1_data: Dict[str, Any],
    steps: List[str],
    events: Dict[str, Dict[str, Any]],
    max_gap: int = 20,
) -> Dict[str, Any]:
    """
    Price-Anchored Milestone State Machine matching sequential chain E1 -> E2 -> ... -> Ek.
    Enforces:
      - Intervening bar gap in [1, max_gap] and wall-clock <= max_gap * 180s (blocks weekend bridges).
      - Spatial proximity to initial structural anchor (`|close - anchor0| <= 3.5 * atr0`).
      - Directional invalidation guard between steps for anchored bull/bear structures.
    Returns matched terminal trigger indices plus gap & ATR-speed telemetry.
    """
    n = int(m1_data["n"])
    if n == 0 or len(steps) < 2:
        return {"indices": np.zeros(0, dtype=np.int64), "avg_gap_bars": 0.0, "avg_atr_speed": 0.0, "pct_immediate": 0.0}

    ts = m1_data["ts_unix"]
    cl = m1_data["close"]
    hi = m1_data["high"]
    lo = m1_data["low"]
    atr = np.maximum(m1_data["atr14"], 1e-9)

    resolved = [_resolve_step(s, events) for s in steps]
    masks = [r[0] for r in resolved]
    anchor0_arr = resolved[0][1]
    chain_dir = resolved[0][2]
    req_micro = any(r[3] for r in resolved)

    # Check direction compatibility from any unambiguous step if step 0 is AUTO
    if chain_dir == "AUTO":
        for _, _, sd, _ in resolved:
            if sd in ("BUY", "SELL"):
                chain_dir = sd
                break

    starts = np.flatnonzero(masks[0])
    matched_idx: List[int] = []
    gaps: List[int] = []
    speeds: List[float] = []
    seen_terminals = set()

    for s0 in starts:
        idx0 = int(s0)
        anchor0 = float(anchor0_arr[idx0])
        atr0 = float(atr[idx0])
        cur_idx = idx0
        ok = True

        for step_k in range(1, len(steps)):
            m_k = masks[step_k]
            found = -1
            lim = min(n, cur_idx + max_gap + 1)
            for j in range(cur_idx + 1, lim):
                if int(ts[j]) - int(ts[cur_idx]) > max_gap * 180:
                    break
                # Invalidation guard against breaking anchor between milestones
                if chain_dir == "BUY" and float(lo[j]) < anchor0 - 1.2 * atr0:
                    break
                if chain_dir == "SELL" and float(hi[j]) > anchor0 + 1.2 * atr0:
                    break
                if m_k[j]:
                    if abs(float(cl[j]) - anchor0) <= 3.5 * atr0:
                        found = j
                        break
            if found < 0:
                ok = False
                break
            cur_idx = found

        if ok and cur_idx not in seen_terminals:
            seen_terminals.add(cur_idx)
            matched_idx.append(cur_idx)
            total_gap = cur_idx - idx0
            gaps.append(total_gap)
            spd = abs(float(cl[cur_idx]) - float(cl[idx0])) / max(total_gap * atr0, 1e-9)
            speeds.append(spd)

    n_m = len(matched_idx)
    return {
        "indices": np.array(matched_idx, dtype=np.int64),
        "requires_microstructure": req_micro,
        "avg_gap_bars": round(sum(gaps) / n_m, 2) if n_m else 0.0,
        "avg_atr_speed": round(sum(speeds) / n_m, 4) if n_m else 0.0,
        "pct_immediate": round(sum(1 for g in gaps if g <= 4) / n_m, 4) if n_m else 0.0,
    }


def mine_single_conditions(
    dataset: Dict[str, Any],
    events: Dict[str, Dict[str, Any]],
    baselines: Optional[Dict[Any, Any]] = None,
) -> List[Dict[str, Any]]:
    """Round 1: Evaluates all M1 Single Atomic Events."""
    if baselines is None:
        baselines = compute_regime_baselines(dataset)

    results: List[Dict[str, Any]] = []
    for name, ev in events.items():
        idxs = np.flatnonzero(ev["mask"])
        prov = "MICROSTRUCTURE_LIVE" if ev["requires_microstructure"] else "HYBRID_LIVE_M1"
        meta = {
            "condition_name": name,
            "condition_type": "Single",
            "timeframes": ["M1"],
            "pre_condition": "Live Microstructure M1 bar (L2 DOM + Real Spread verified)" if ev["requires_microstructure"] else "Cleaned M1 bar in Live Session Window",
            "event_sequence": [name],
            "formatted_sequence": f"M1 Trigger [{name}] -> Next-Bar Open Entry -> Expected Outcome",
            "entry_criteria": ev["desc"],
            "requires_microstructure": ev["requires_microstructure"],
            "data_tier_provenance": prov,
            "sequence_timing": {"avg_gap_bars": 0.0, "avg_atr_speed": 0.0, "pct_immediate": 1.0},
        }
        eval_res = evaluate_condition(dataset, baselines, idxs, ev["default_dir"], meta, cooldown_bars=10)
        results.append(eval_res)
    return results


CANONICAL_SEQUENCES: Tuple[Tuple[List[str], str, str], ...] = (
    (["SWEEP_LOW", "RECLAIM_LOW"], "BUY", "Sweep Low ตามด้วยแท่ง Reclaim เหนือแนวรับ"),
    (["SWEEP_LOW", "RECLAIM_LOW", "BOS_BULL"], "BUY", "Sweep Low -> Reclaim -> Bullish BOS ยืนยันโครงสร้าง"),
    (["SWEEP_LOW", "RECLAIM_LOW", "DISPLACEMENT_BULL"], "BUY", "Sweep Low -> Reclaim -> แท่ง Impulse ขาขึ้น"),
    (["SWEEP_LOW", "HIGHER_LOW", "BOS_BULL"], "BUY", "Sweep Low -> ยก Higher Low -> Bullish BOS"),
    (["SWEEP_LOW", "RETEST_SUPPORT_2X", "DISPLACEMENT_BULL"], "BUY", "Sweep Low -> ทดสอบ Low เดิม 2 ครั้งไม่หลุด -> ดีดแรง"),
    (["SWEEP_LOW", "RECLAIM_LOW+DOM_ABSORPTION_BUY"], "BUY", "Sweep Low -> Reclaim พร้อม L2 DOM Bid Absorption"),
    (["SWEEP_LOW", "HIGHER_LOW", "CHOCH_BULL"], "BUY", "Sweep Low -> Higher Low -> กลับตัว CHoCH ขาขึ้น"),
    (["SWEEP_HIGH", "RECLAIM_HIGH"], "SELL", "Sweep High ตามด้วยแท่ง Reclaim ต่ำกว่าแนวต้าน"),
    (["SWEEP_HIGH", "RECLAIM_HIGH", "BOS_BEAR"], "SELL", "Sweep High -> Reclaim -> Bearish BOS ยืนยันโครงสร้าง"),
    (["SWEEP_HIGH", "RECLAIM_HIGH", "DISPLACEMENT_BEAR"], "SELL", "Sweep High -> Reclaim -> แท่ง Impulse ขาลง"),
    (["SWEEP_HIGH", "LOWER_HIGH", "BOS_BEAR"], "SELL", "Sweep High -> กด Lower High -> Bearish BOS"),
    (["SWEEP_HIGH", "RETEST_RESIST_2X", "DISPLACEMENT_BEAR"], "SELL", "Sweep High -> ทดสอบ High เดิม 2 ครั้งไม่ผ่าน -> ทุบแรง"),
    (["SWEEP_HIGH", "RECLAIM_HIGH+DOM_ABSORPTION_SELL"], "SELL", "Sweep High -> Reclaim พร้อม L2 DOM Ask Absorption"),
    (["SWEEP_HIGH", "LOWER_HIGH", "CHOCH_BEAR"], "SELL", "Sweep High -> Lower High -> กลับตัว CHoCH ขาลง"),
    (["BREAKOUT_DOWN", "FALSE_BREAKOUT_DOWN", "RECLAIM_LOW"], "BUY", "Breakout ลงหลอก -> False Breakdown -> Reclaim กลับเข้ากรอบ"),
    (["BREAKOUT_DOWN", "FALSE_BREAKOUT_DOWN", "RECLAIM_LOW", "EXPANSION"], "BUY", "False Breakdown -> Reclaim -> Volatility Expansion ขึ้นต่อ"),
    (["BREAKOUT_UP", "FALSE_BREAKOUT_UP", "RECLAIM_HIGH"], "SELL", "Breakout ขึ้นหลอก -> False Breakout -> Reclaim หลุดกรอบลง"),
    (["BREAKOUT_UP", "FALSE_BREAKOUT_UP", "RECLAIM_HIGH", "EXPANSION"], "SELL", "False Breakout -> Reclaim -> Volatility Expansion ลงต่อ"),
    (["EXHAUSTION_BOT", "SWEEP_LOW", "RECLAIM_LOW"], "BUY", "แรงขายแผ่วปลายคลื่น -> Sweep Low -> Reclaim"),
    (["EXHAUSTION_BOT", "DELTA_DIVERGENCE_BULL", "DISPLACEMENT_BULL"], "BUY", "แรงขายแผ่ว -> Order Flow Divergence -> Impulse ขาขึ้น"),
    (["EXHAUSTION_TOP", "SWEEP_HIGH", "RECLAIM_HIGH"], "SELL", "แรงซื้อแผ่วปลายคลื่น -> Sweep High -> Reclaim"),
    (["EXHAUSTION_TOP", "DELTA_DIVERGENCE_BEAR", "DISPLACEMENT_BEAR"], "SELL", "แรงซื้อแผ่ว -> Order Flow Divergence -> Impulse ขาลง"),
    (["COMPRESSION", "BREAKOUT_UP", "RETEST_SUPPORT_2X"], "BUY", "บีบอัดตัวแคบ -> เบรกขึ้น -> รีเทสต์แนวรับไม่หลุด"),
    (["COMPRESSION", "BREAKOUT_DOWN", "RETEST_RESIST_2X"], "SELL", "บีบอัดตัวแคบ -> เบรกหลุด -> รีเทสต์แนวต้านไม่ผ่าน"),
    (["COMPRESSION", "BREAKOUT_UP+CVD_SURGE_BULL"], "BUY", "บีบอัดตัว -> เบรกขึ้นพร้อม Order Flow Delta Surge"),
    (["COMPRESSION", "BREAKOUT_DOWN+CVD_SURGE_BEAR"], "SELL", "บีบอัดตัว -> เบรกหลุดพร้อม Order Flow Delta Surge"),
    (["DISPLACEMENT_BULL", "RETEST_SUPPORT_2X", "DISPLACEMENT_BULL"], "BUY", "Impulse ขาขึ้น -> ย่อทดสอบ 2 รอบ -> Impulse ขึ้นต่อ"),
    (["DISPLACEMENT_BEAR", "RETEST_RESIST_2X", "DISPLACEMENT_BEAR"], "SELL", "Impulse ขาลง -> ดีดทดสอบ 2 รอบ -> Impulse ลงต่อ"),
    (["VWAP_EXTREME_LOW", "DOM_ABSORPTION_BUY", "RECLAIM_LOW"], "BUY", "ห่าง VWAP ล่างสุดขั้ว -> Bid Wall ดูดซับ -> Reclaim"),
    (["VWAP_EXTREME_HIGH", "DOM_ABSORPTION_SELL", "RECLAIM_HIGH"], "SELL", "ห่าง VWAP บนสุดขั้ว -> Ask Wall ดูดซับ -> Reclaim"),
)


def _dirs_compatible(d1: str, d2: str) -> bool:
    return d1 == "AUTO" or d2 == "AUTO" or d1 == d2


def mine_multi_step_sequences(
    dataset: Dict[str, Any],
    events: Dict[str, Dict[str, Any]],
    single_results: List[Dict[str, Any]],
    baselines: Dict[Any, Any],
    max_gap: int = 20,
) -> Dict[str, Any]:
    """
    Round 2: Mines canonical + data-driven hierarchical multi-step sequences (2 to 4 steps),
    performs Ablation Incremental Lift analysis (A vs A->B vs A->B->C), and extracts
    Branching and Converging sequence groups.
    """
    m1 = dataset["m1"]
    single_by_name = {r["condition_name"]: r for r in single_results}

    seq_cache: Dict[Tuple[str, ...], Dict[str, Any]] = {}

    def _eval_seq(steps: List[str], pref_dir: str, desc: str) -> Dict[str, Any]:
        key = tuple(steps)
        if key in seq_cache:
            return seq_cache[key]
        matched = match_anchored_sequence(m1, steps, events, max_gap=max_gap)
        req_micro = bool(matched["requires_microstructure"])
        prov = "MICROSTRUCTURE_LIVE" if req_micro else "HYBRID_LIVE_M1"
        cname = " -> ".join(steps)
        meta = {
            "condition_name": f"SEQ: {cname}",
            "condition_type": "Sequential",
            "timeframes": ["M1"],
            "pre_condition": f"Anchor at {steps[0]} (invalidated if structure breached before step {len(steps)})",
            "event_sequence": list(steps),
            "formatted_sequence": f"M1 Sequence [{cname}] -> Next-Bar Open Entry -> Expected Outcome",
            "entry_criteria": desc,
            "requires_microstructure": req_micro,
            "data_tier_provenance": prov,
            "sequence_timing": {
                "avg_gap_bars": matched["avg_gap_bars"],
                "avg_atr_speed": matched["avg_atr_speed"],
                "pct_immediate": matched["pct_immediate"],
            },
        }
        ev = evaluate_condition(dataset, baselines, matched["indices"], pref_dir, meta, cooldown_bars=10)
        seq_cache[key] = ev
        return ev

    # 1. Evaluate all canonical sequences
    for steps, pref_dir, desc in CANONICAL_SEQUENCES:
        if all((s.split("+")[0] in events and (len(s.split("+")) == 1 or s.split("+")[1] in events)) for s in steps):
            # Ensure prefix pairs exist in seq_cache for ablation comparison
            if len(steps) >= 3 and tuple(steps[:2]) not in seq_cache:
                p2 = steps[:2]
                if all("+" not in p for p in p2):
                    _eval_seq(p2, pref_dir, f"Prefix chain {p2[0]} -> {p2[1]}")
            _eval_seq(steps, pref_dir, desc)

    # 2. Data-Driven Hierarchical Mining (2-step -> 3-step -> 4-step)
    milestones = [
        r for r in single_results
        if events[r["condition_name"]]["tier"] == "MILESTONE" and r["sample_size_is"] >= 15
    ]
    milestones.sort(key=lambda r: abs(r["probability"]["is_primary"].get("lift_bull", 0.0) - r["probability"]["is_primary"].get("lift_bear", 0.0)), reverse=True)
    top_milestones = milestones[:10]

    modifiers = [
        r for r in single_results
        if r["sample_size_is"] >= 15
    ]
    modifiers.sort(key=lambda r: r["expectancy"]["is_usd"], reverse=True)
    top_steps = top_milestones[:8] + [r for r in modifiers[:6] if r not in top_milestones[:8]]

    promising_2step: List[Dict[str, Any]] = []
    for a in top_milestones[:8]:
        na = a["condition_name"]
        da = events[na]["default_dir"]
        for b in top_steps:
            nb = b["condition_name"]
            if nb == na:
                continue
            db = events[nb]["default_dir"]
            if not _dirs_compatible(da, db):
                continue
            pref = da if da in ("BUY", "SELL") else db
            ev2 = _eval_seq([na, nb], pref, f"Data-mined 2-step sequence: {na} followed by {nb}")
            if ev2["sample_size_total"] >= 12 and (
                ev2["expectancy"]["is_usd"] > a["expectancy"]["is_usd"] or ev2["expectancy"]["is_usd"] > 0.0
            ):
                promising_2step.append(ev2)

    promising_2step.sort(key=lambda r: r["expectancy"]["is_usd"], reverse=True)

    promising_3step: List[Dict[str, Any]] = []
    for p2 in promising_2step[:14]:
        s_pair = p2["event_sequence"]
        dp = p2["direction"]
        for c in top_steps[:8]:
            nc = c["condition_name"]
            if nc == s_pair[-1]:
                continue
            dc = events[nc]["default_dir"]
            if not _dirs_compatible(dp, dc):
                continue
            ev3 = _eval_seq([s_pair[0], s_pair[1], nc], dp, f"Data-mined 3-step extension: {s_pair[0]} -> {s_pair[1]} -> {nc}")
            if ev3["sample_size_total"] >= 8 and ev3["expectancy"]["is_usd"] > p2["expectancy"]["is_usd"]:
                promising_3step.append(ev3)

    promising_3step.sort(key=lambda r: r["expectancy"]["is_usd"], reverse=True)
    for p3 in promising_3step[:6]:
        s_tri = p3["event_sequence"]
        dp = p3["direction"]
        for d in top_milestones[:4]:
            nd = d["condition_name"]
            if nd == s_tri[-1]:
                continue
            if _dirs_compatible(dp, events[nd]["default_dir"]):
                _eval_seq([*s_tri, nd], dp, f"Data-mined 4-step chain: {' -> '.join(s_tri)} -> {nd}")

    all_seqs = list(seq_cache.values())

    # 3. Ablation / Incremental Lift Annotation (`A` vs `A->B` vs `A->B->C`)
    for seq_res in all_seqs:
        steps = seq_res["event_sequence"]
        first_base = single_by_name.get(steps[0].split("+")[0])
        prev_prefix = seq_cache.get(tuple(steps[:-1])) if len(steps) >= 3 else first_base

        oos_p = seq_res["probability"]["oos_dir_prob"]
        oos_e = seq_res["expectancy"]["oos_usd"]

        delta_p_prev = round(oos_p - prev_prefix["probability"]["oos_dir_prob"], 4) if prev_prefix else None
        delta_e_prev = round(oos_e - prev_prefix["expectancy"]["oos_usd"], 4) if prev_prefix else None
        delta_p_base = round(oos_p - first_base["probability"]["oos_dir_prob"], 4) if first_base else None
        delta_e_base = round(oos_e - first_base["expectancy"]["oos_usd"], 4) if first_base else None

        seq_res["ablation_lift"] = {
            "base_event": steps[0],
            "prev_step": " -> ".join(steps[:-1]),
            "delta_oos_prob_vs_prev": delta_p_prev,
            "delta_oos_exp_vs_prev": delta_e_prev,
            "delta_oos_prob_vs_base": delta_p_base,
            "delta_oos_exp_vs_base": delta_e_base,
            "adds_predictive_power": bool((delta_e_prev or 0.0) > 0.0 or (delta_p_prev or 0.0) > 0.02),
        }

    # 4. Extract Branching Patterns (same prefix A->B splitting to opposing or divergent C1 vs C2)
    by_prefix: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for r in all_seqs:
        if r["sample_size_total"] >= 8:
            pref = " -> ".join(r["event_sequence"][:-1])
            by_prefix[pref].append(r)

    branching_groups: List[Dict[str, Any]] = []
    for pref, children in by_prefix.items():
        if len(children) < 2:
            continue
        dirs = {c["direction"] for c in children}
        exps = [c["expectancy"]["oos_usd"] for c in children]
        if len(dirs) >= 2 or (max(exps) - min(exps) >= 0.30):
            branching_groups.append(
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
    branching_groups.sort(key=lambda g: len(g["branches"]), reverse=True)

    # 5. Extract Converging Patterns (distinct starting events yielding same positive directional outcome)
    converging_groups: Dict[str, List[Dict[str, Any]]] = {"BUY": [], "SELL": []}
    for direction in ("BUY", "SELL"):
        pos_cands = [
            r for r in all_seqs
            if r["direction"] == direction and r["sample_size_total"] >= 8 and (r["expectancy"]["oos_usd"] > 0 or r["probability"]["oos_dir_lift"] > 0.02)
        ]
        seen_starts = set()
        for c in sorted(pos_cands, key=lambda x: x["expectancy"]["oos_usd"], reverse=True):
            st0 = c["event_sequence"][0]
            if st0 not in seen_starts:
                seen_starts.add(st0)
                converging_groups[direction].append(
                    {
                        "condition_name": c["condition_name"],
                        "starting_event": st0,
                        "sample_size": c["sample_size_total"],
                        "oos_dir_prob": c["probability"]["oos_dir_prob"],
                        "oos_expectancy_usd": c["expectancy"]["oos_usd"],
                    }
                )
            if len(converging_groups[direction]) >= 5:
                break

    return {
        "sequences": all_seqs,
        "branching_patterns": branching_groups[:10],
        "converging_patterns": converging_groups,
    }


CURATED_MTF_3TF: Tuple[Tuple[str, str, str, str, str], ...] = (
    ("H1_TREND_BULL", "M15_PULLBACK_BULL", "SWEEP_LOW", "BUY", "H1 ขาขึ้น + M15 ย่อพักตัว + M1 Sweep Low"),
    ("H1_TREND_BULL", "M15_PULLBACK_BULL", "RECLAIM_LOW", "BUY", "H1 ขาขึ้น + M15 ย่อพักตัว + M1 Reclaim แนวรับ"),
    ("H1_TREND_BULL", "M15_PULLBACK_BULL", "DOM_ABSORPTION_BUY", "BUY", "H1 ขาขึ้น + M15 ย่อพักตัว + M1 Bid Absorption"),
    ("H1_TREND_BEAR", "M15_PULLBACK_BEAR", "SWEEP_HIGH", "SELL", "H1 ขาลง + M15 ดีดรีเทสต์ + M1 Sweep High"),
    ("H1_TREND_BEAR", "M15_PULLBACK_BEAR", "RECLAIM_HIGH", "SELL", "H1 ขาลง + M15 ดีดรีเทสต์ + M1 Reclaim แนวต้าน"),
    ("H1_TREND_BEAR", "M15_PULLBACK_BEAR", "DOM_ABSORPTION_SELL", "SELL", "H1 ขาลง + M15 ดีดรีเทสต์ + M1 Ask Absorption"),
    ("H4_NEAR_SUPPORT", "M15_SWEEP_LOW", "BOS_BULL", "BUY", "H4 แนวรับสำคัญ + M15 Sweep Low + M1 Bullish BOS"),
    ("H4_NEAR_SUPPORT", "M15_SWEEP_LOW", "DOM_ABSORPTION_BUY", "BUY", "H4 แนวรับสำคัญ + M15 Sweep Low + M1 DOM Bid Wall"),
    ("H4_NEAR_RESIST", "M15_SWEEP_HIGH", "BOS_BEAR", "SELL", "H4 แนวต้านสำคัญ + M15 Sweep High + M1 Bearish BOS"),
    ("H4_NEAR_RESIST", "M15_SWEEP_HIGH", "DOM_ABSORPTION_SELL", "SELL", "H4 แนวต้านสำคัญ + M15 Sweep High + M1 DOM Ask Wall"),
    ("H1_NEAR_RESIST", "M15_FAILED_RETEST_TOP", "DISPLACEMENT_BEAR", "SELL", "H1 แนวต้าน + M15 ทดสอบ High ไม่ผ่าน -> M1 ทุบแรง"),
    ("H1_NEAR_SUPPORT", "M15_FAILED_RETEST_BOT", "DISPLACEMENT_BULL", "BUY", "H1 แนวรับ + M15 ทดสอบ Low ไม่หลุด -> M1 พุ่งแรง"),
    ("H1_RANGE", "M5_FALSE_BREAK_UP", "REJECTION_BEAR", "SELL", "H1 กรอบ Range + M5 False Break บน + M1 ปฏิเสธราคา"),
    ("H1_RANGE", "M5_FALSE_BREAK_DOWN", "REJECTION_BULL", "BUY", "H1 กรอบ Range + M5 False Break ล่าง + M1 ปฏิเสธราคา"),
    ("H1_EXHAUSTION_TOP", "M15_CHOCH_BEAR", "DISPLACEMENT_BEAR", "SELL", "H1 แรงซื้อแผ่ว + M15 CHoCH ลง + M1 Bearish Displacement"),
    ("H1_EXHAUSTION_BOT", "M15_CHOCH_BULL", "DISPLACEMENT_BULL", "BUY", "H1 แรงขายแผ่ว + M15 CHoCH ขึ้น + M1 Bullish Displacement"),
    ("DEV_H1_REJECTION_BULL", "M15_SWEEP_LOW", "RECLAIM_LOW", "BUY", "แท่ง H1 ปัจจุบันทิ้งไส้ล่าง (Causal) + M15 Sweep + M1 Reclaim"),
    ("DEV_H1_REJECTION_BEAR", "M15_SWEEP_HIGH", "RECLAIM_HIGH", "SELL", "แท่ง H1 ปัจจุบันทิ้งไส้บน (Causal) + M15 Sweep + M1 Reclaim"),
)

CURATED_MTF_2TF: Tuple[Tuple[str, str, str, str], ...] = (
    ("H1_TREND_BULL", "SWEEP_LOW", "BUY", "H1 ขาขึ้น + M1 Sweep Low"),
    ("H1_TREND_BEAR", "SWEEP_HIGH", "SELL", "H1 ขาลง + M1 Sweep High"),
    ("H1_TREND_BULL", "DOM_ABSORPTION_BUY", "BUY", "H1 ขาขึ้น + M1 Bid Absorption"),
    ("H1_TREND_BEAR", "DOM_ABSORPTION_SELL", "SELL", "H1 ขาลง + M1 Ask Absorption"),
    ("M15_SWEEP_LOW", "RECLAIM_LOW", "BUY", "M15 Sweep Low + M1 Reclaim"),
    ("M15_SWEEP_HIGH", "RECLAIM_HIGH", "SELL", "M15 Sweep High + M1 Reclaim"),
    ("M5_FALSE_BREAK_UP", "REJECTION_BEAR", "SELL", "M5 False Break บน + M1 Rejection ลง"),
    ("M5_FALSE_BREAK_DOWN", "REJECTION_BULL", "BUY", "M5 False Break ล่าง + M1 Rejection ขึ้น"),
    ("DEV_H1_REJECTION_BULL", "DOM_ABSORPTION_BUY", "BUY", "แท่ง H1 กำลังทิ้งไส้ล่าง + M1 DOM Bid Absorption"),
    ("DEV_H1_REJECTION_BEAR", "DOM_ABSORPTION_SELL", "SELL", "แท่ง H1 กำลังทิ้งไส้บน + M1 DOM Ask Absorption"),
)


def mine_mtf_patterns(
    dataset: Dict[str, Any],
    events: Dict[str, Dict[str, Any]],
    htf_projected: Dict[str, Dict[str, Any]],
    single_results: List[Dict[str, Any]],
    baselines: Dict[Any, Any],
) -> Dict[str, Any]:
    """
    Round 3: Evaluates Dual-HTF Cross-Timeframe Conditions, checks temporal ordering
    (MTF before vs concurrent with LTF trigger), and builds the empirical
    `1 TF vs 2 TF vs 3+ TF` Confluence Proof table.
    """
    m1_ts = dataset["m1"]["ts_unix"]
    single_by_name = {r["condition_name"]: r for r in single_results}
    mtf_cache: Dict[str, Dict[str, Any]] = {}

    def _eval_combo(name: str, tfs: List[str], pre_cond: str, seq_tokens: List[str], fmt_seq: str, desc: str, mask: np.ndarray, pref_dir: str, req_micro: bool) -> Dict[str, Any]:
        if name in mtf_cache:
            return mtf_cache[name]
        idxs = np.flatnonzero(mask)
        prov = "MICROSTRUCTURE_LIVE" if req_micro else "HYBRID_LIVE_MTF_OHLCV"
        meta = {
            "condition_name": name,
            "condition_type": "Multi-TF",
            "timeframes": tfs,
            "pre_condition": pre_cond,
            "event_sequence": seq_tokens,
            "formatted_sequence": fmt_seq,
            "entry_criteria": desc,
            "requires_microstructure": req_micro,
            "data_tier_provenance": prov,
            "sequence_timing": {"avg_gap_bars": 0.0, "avg_atr_speed": 0.0, "pct_immediate": 1.0},
        }
        ev = evaluate_condition(dataset, baselines, idxs, pref_dir, meta, cooldown_bars=12)
        mtf_cache[name] = ev
        return ev

    # 1. Curated 3-TF & 2-TF patterns
    for htf_k, mtf_k, ltf_k, pdir, desc in CURATED_MTF_3TF:
        if htf_k in htf_projected and mtf_k in htf_projected and ltf_k in events:
            hk = htf_projected[htf_k]
            mk = htf_projected[mtf_k]
            lk = events[ltf_k]
            mask = hk["mask"] & mk["mask"] & lk["mask"]
            tfs = sorted({hk["tf"].upper(), mk["tf"].upper(), "M1"})
            cname = f"MTF: {htf_k} -> {mtf_k} -> M1_{ltf_k}"
            fmt = f"{htf_k} -> {mtf_k} -> M1 [{ltf_k}] -> Next-Bar Open Entry -> Expected Outcome"
            _eval_combo(cname, tfs, f"{hk['desc']} + {mk['desc']}", [htf_k, mtf_k, f"M1_{ltf_k}"], fmt, desc, mask, pdir, lk["requires_microstructure"])

    for mtf_k, ltf_k, pdir, desc in CURATED_MTF_2TF:
        if mtf_k in htf_projected and ltf_k in events:
            mk = htf_projected[mtf_k]
            lk = events[ltf_k]
            mask = mk["mask"] & lk["mask"]
            tfs = sorted({mk["tf"].upper(), "M1"})
            cname = f"MTF: {mtf_k} -> M1_{ltf_k}"
            fmt = f"{mtf_k} -> M1 [{ltf_k}] -> Next-Bar Open Entry -> Expected Outcome"
            _eval_combo(cname, tfs, mk["desc"], [mtf_k, f"M1_{ltf_k}"], fmt, desc, mask, pdir, lk["requires_microstructure"])

    # 2. Data-driven cross-TF pairing: top H1/M15 contexts x top M1 events
    top_htf_keys = [k for k in ("H1_TREND_BULL", "H1_TREND_BEAR", "H1_RANGE", "M15_SWEEP_LOW", "M15_SWEEP_HIGH", "M15_PULLBACK_BULL", "M15_PULLBACK_BEAR") if k in htf_projected]
    top_m1_cands = [r["condition_name"] for r in sorted(single_results, key=lambda x: x["expectancy"]["is_usd"], reverse=True)[:10]]
    for hk_name in top_htf_keys:
        hk = htf_projected[hk_name]
        h_dir = "BUY" if ("BULL" in hk_name or "LOW" in hk_name or "BOT" in hk_name) else ("SELL" if ("BEAR" in hk_name or "HIGH" in hk_name or "TOP" in hk_name) else "AUTO")
        for ltf_name in top_m1_cands:
            lk = events[ltf_name]
            if not _dirs_compatible(h_dir, lk["default_dir"]):
                continue
            pref = h_dir if h_dir in ("BUY", "SELL") else lk["default_dir"]
            mask = hk["mask"] & lk["mask"]
            if int(np.sum(mask)) >= 12:
                cname = f"MTF: {hk_name} -> M1_{ltf_name}"
                fmt = f"{hk_name} -> M1 [{ltf_name}] -> Next-Bar Open Entry -> Expected Outcome"
                _eval_combo(cname, [hk["tf"].upper(), "M1"], hk["desc"], [hk_name, f"M1_{ltf_name}"], fmt, f"Data-mined Cross-TF: {hk_name} + M1 {ltf_name}", mask, pref, lk["requires_microstructure"])

    # 3. Temporal Ordering Check on M15 Setup -> M1 Trigger pairs
    temporal_order_checks: List[Dict[str, Any]] = []
    for mtf_k, ltf_k in (("M15_SWEEP_LOW", "RECLAIM_LOW"), ("M15_SWEEP_HIGH", "RECLAIM_HIGH"), ("M5_SWEEP_LOW", "BOS_BULL"), ("M5_SWEEP_HIGH", "BOS_BEAR")):
        if mtf_k not in htf_projected or ltf_k not in events:
            continue
        mk = htf_projected[mtf_k]
        lk = events[ltf_k]
        both = mk["mask"] & lk["mask"]
        idxs = np.flatnonzero(both)
        if len(idxs) < 6:
            continue
        earlier_mtf = np.array([int(i) for i in idxs if (int(m1_ts[int(i)]) - int(mk["event_ts"][int(i)])) >= 900], dtype=np.int64)
        fresh_mtf = np.array([int(i) for i in idxs if (int(m1_ts[int(i)]) - int(mk["event_ts"][int(i)])) < 900], dtype=np.int64)
        pdir = "BUY" if ("LOW" in mtf_k or "BULL" in ltf_k) else "SELL"
        if len(fresh_mtf) >= 4 and len(earlier_mtf) >= 4:
            e_fresh = evaluate_condition(dataset, baselines, fresh_mtf, pdir, {"condition_name": "tmp_f"}, cooldown_bars=10)
            e_early = evaluate_condition(dataset, baselines, earlier_mtf, pdir, {"condition_name": "tmp_e"}, cooldown_bars=10)
            temporal_order_checks.append(
                {
                    "pair": f"{mtf_k} + M1_{ltf_k}",
                    "fresh_mtf_before_ltf": {"n": e_fresh["sample_size_total"], "oos_prob": e_fresh["probability"]["oos_dir_prob"], "oos_exp": e_fresh["expectancy"]["oos_usd"]},
                    "older_mtf_before_ltf": {"n": e_early["sample_size_total"], "oos_prob": e_early["probability"]["oos_dir_prob"], "oos_exp": e_early["expectancy"]["oos_usd"]},
                }
            )

    # 4. Empirical Timeframe Confluence Proof (`1_TF` vs `2_TF` vs `3_PLUS_TF`)
    confluence_specs = (
        ("SWEEP_LOW", ("M5_SWEEP_LOW", "M15_SWEEP_LOW", "M15_PULLBACK_BULL"), ("H1_TREND_BULL", "H1_NEAR_SUPPORT", "H4_NEAR_SUPPORT"), "BUY"),
        ("SWEEP_HIGH", ("M5_SWEEP_HIGH", "M15_SWEEP_HIGH", "M15_PULLBACK_BEAR"), ("H1_TREND_BEAR", "H1_NEAR_RESIST", "H4_NEAR_RESIST"), "SELL"),
        ("RECLAIM_LOW", ("M5_FALSE_BREAK_DOWN", "M15_SWEEP_LOW", "M15_PULLBACK_BULL"), ("H1_TREND_BULL", "H1_NEAR_SUPPORT"), "BUY"),
        ("RECLAIM_HIGH", ("M5_FALSE_BREAK_UP", "M15_SWEEP_HIGH", "M15_PULLBACK_BEAR"), ("H1_TREND_BEAR", "H1_NEAR_RESIST"), "SELL"),
        ("DOM_ABSORPTION_BUY", ("M5_SWEEP_LOW", "M15_PULLBACK_BULL", "M15_SWEEP_LOW"), ("H1_TREND_BULL", "H1_NEAR_SUPPORT"), "BUY"),
        ("DOM_ABSORPTION_SELL", ("M5_SWEEP_HIGH", "M15_PULLBACK_BEAR", "M15_SWEEP_HIGH"), ("H1_TREND_BEAR", "H1_NEAR_RESIST"), "SELL"),
        ("BOS_BULL", ("M5_BOS_BULL", "M15_PULLBACK_BULL"), ("H1_TREND_BULL", "H4_TREND_BULL"), "BUY"),
        ("BOS_BEAR", ("M5_BOS_BEAR", "M15_PULLBACK_BEAR"), ("H1_TREND_BEAR", "H4_TREND_BEAR"), "SELL"),
        ("REJECTION_BULL", ("M5_FALSE_BREAK_DOWN", "M15_SWEEP_LOW"), ("H1_NEAR_SUPPORT", "H1_REJECTION_BULL"), "BUY"),
        ("REJECTION_BEAR", ("M5_FALSE_BREAK_UP", "M15_SWEEP_HIGH"), ("H1_NEAR_RESIST", "H1_REJECTION_BEAR"), "SELL"),
    )

    tier_buckets: Dict[str, List[Dict[str, Any]]] = {"1_TF": [], "2_TF": [], "3_PLUS_TF": []}
    for ltf_k, mtf_list, htf_list, pdir in confluence_specs:
        if ltf_k not in events:
            continue
        base_m = events[ltf_k]["mask"]
        mtf_union = np.zeros_like(base_m)
        for mk in mtf_list:
            if mk in htf_projected:
                mtf_union |= htf_projected[mk]["mask"]
        htf_union = np.zeros_like(base_m)
        for hk in htf_list:
            if hk in htf_projected:
                htf_union |= htf_projected[hk]["mask"]

        r1 = single_by_name.get(ltf_k)
        if r1 and r1["sample_size_oos"] >= 3:
            tier_buckets["1_TF"].append(r1)

        m2 = base_m & mtf_union
        idx2 = np.flatnonzero(m2)
        if len(idx2) >= 5:
            r2 = evaluate_condition(dataset, baselines, idx2, pdir, {"condition_name": f"2TF_{ltf_k}"}, cooldown_bars=10)
            if r2["sample_size_oos"] >= 3:
                tier_buckets["2_TF"].append(r2)

        m3 = base_m & mtf_union & htf_union
        idx3 = np.flatnonzero(m3)
        if len(idx3) >= 5:
            r3 = evaluate_condition(dataset, baselines, idx3, pdir, {"condition_name": f"3TF_{ltf_k}"}, cooldown_bars=10)
            if r3["sample_size_oos"] >= 3:
                tier_buckets["3_PLUS_TF"].append(r3)

    confluence_summary: Dict[str, Any] = {}
    for tname, rows in tier_buckets.items():
        if not rows:
            confluence_summary[tname] = {"patterns_tested": 0, "avg_oos_sample": 0.0, "avg_oos_dir_prob": 0.0, "avg_oos_win_rate": 0.0, "avg_oos_expectancy_usd": 0.0, "avg_oos_pf": 0.0}
        else:
            confluence_summary[tname] = {
                "patterns_tested": len(rows),
                "avg_oos_sample": round(sum(r["sample_size_oos"] for r in rows) / len(rows), 1),
                "avg_oos_dir_prob": round(sum(r["probability"]["oos_dir_prob"] for r in rows) / len(rows), 4),
                "avg_oos_win_rate": round(sum(r["win_rate"]["oos"] for r in rows) / len(rows), 4),
                "avg_oos_expectancy_usd": round(sum(r["expectancy"]["oos_usd"] for r in rows) / len(rows), 4),
                "avg_oos_pf": round(sum(min(r["profit_factor"]["oos"], 5.0) for r in rows) / len(rows), 3),
            }

    e1 = confluence_summary["1_TF"]["avg_oos_expectancy_usd"]
    e2 = confluence_summary["2_TF"]["avg_oos_expectancy_usd"]
    e3 = confluence_summary["3_PLUS_TF"]["avg_oos_expectancy_usd"]
    p1 = confluence_summary["1_TF"]["avg_oos_dir_prob"]
    p3 = confluence_summary["3_PLUS_TF"]["avg_oos_dir_prob"]
    if confluence_summary["3_PLUS_TF"]["patterns_tested"] == 0:
        conf_verdict = "INSUFFICIENT_3TF_CONFLUENCE_SAMPLE"
    elif e3 > e1 and p3 > p1:
        conf_verdict = "CONFLUENCE_IMPROVES_PROB_AND_EXP"
    elif e2 > e1 or e3 > e1:
        conf_verdict = "CONFLUENCE_SELECTIVE_IMPROVEMENT"
    else:
        conf_verdict = "CONFLUENCE_NOT_MONOTONIC_OVER_SINGLE_TF"

    return {
        "mtf_conditions": list(mtf_cache.values()),
        "temporal_order_checks": temporal_order_checks,
        "confluence_proof": {
            "tiers": confluence_summary,
            "verdict": conf_verdict,
        },
    }
