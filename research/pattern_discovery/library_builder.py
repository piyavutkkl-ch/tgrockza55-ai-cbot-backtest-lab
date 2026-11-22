"""
Trading Condition Library Builder, Statistical Ranker & Report Generator (Step 7)
================================================================================
Applies Benjamini-Hochberg FDR, +-15% Parameter Perturbation (Jitter Test),
Composite Evidence Ranking, 7-Category Classification, and emits:
- docs/data/trading_condition_library.json (20 required fields per entry)
- docs/data/pattern_discovery_state.json (iterative progress state tracker)
- TRADING_CONDITION_LIBRARY_REPORT.md (comprehensive research summary report)
"""

from __future__ import annotations

import json
import math
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from research.pattern_discovery.data_loader import load_scalping_mtf_dataset
from research.pattern_discovery.event_tokenizer import (
    project_htf_events_to_m1,
    tokenize_htf_events,
    tokenize_m1_events,
)
from research.pattern_discovery.level_memory import extract_level_structure
from research.pattern_discovery.round2_micro_session_miner import (
    mine_micro_mtf_fusion,
    mine_orderbook_sequences,
    mine_session_specific_patterns,
)
from research.pattern_discovery.sequence_mtf_miner import (
    match_anchored_sequence,
    mine_multi_step_sequences,
    mine_mtf_patterns,
    mine_single_conditions,
)
from research.pattern_discovery.statistical_validator import (
    benjamini_hochberg_fdr,
    compute_regime_baselines,
    evaluate_condition,
)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def _assign_categories(entry: Dict[str, Any], unit_exp_floor: float = 0.05) -> List[str]:
    cats: List[str] = []
    prob = entry["probability"]
    wr = entry["win_rate"]
    exp = entry["expectancy"]
    pf = entry["profit_factor"]
    n_tot = entry["sample_size_total"]
    freq_day = entry["frequency_per_day"]
    steps = entry["event_sequence"]
    tfs = entry["timeframes"]

    high_exp_th = min(0.15, max(0.015, unit_exp_floor * 3.0))
    rare_exp_th = min(0.10, max(0.010, unit_exp_floor * 2.0))

    if (prob["oos_dir_prob"] >= 0.45 and prob["oos_dir_lift"] >= 0.03) or (wr["oos"] >= 0.52 and n_tot >= 15):
        cats.append("High Probability")
    if n_tot >= 40 and freq_day >= 1.5:
        cats.append("High Frequency")
    if exp["oos_usd"] >= high_exp_th and pf["oos"] >= 1.25:
        cats.append("High Expectancy")
    if (len(tfs) >= 2 and len(steps) >= 2) or len(steps) >= 3 or any("+" in s for s in steps):
        cats.append("High Confluence")
    if entry["condition_type"] == "Sequential":
        cats.append("Sequential Patterns")
    if entry["condition_type"] == "Multi-TF":
        cats.append("Multi-Timeframe Patterns")
    if n_tot < 25 and (exp["oos_usd"] >= rare_exp_th or pf["oos"] >= 1.35 or prob["oos_dir_lift"] >= 0.08):
        cats.append("Rare but Powerful")
    return cats


def _evidence_score(entry: Dict[str, Any]) -> float:
    status_bonus = {
        "VALIDATED_OOS": 50.0,
        "REGIME_SPECIFIC_EDGE": 30.0,
        "RARE_HIGH_EDGE": 20.0,
        "IS_ONLY_OVERFIT": 5.0,
        "NO_EDGE": 0.0,
        "INSUFFICIENT_DATA": -10.0,
    }.get(entry["validation_status"], 0.0)

    n_oos = entry["sample_size_oos"]
    oos_exp = entry["expectancy"]["oos_usd"]
    oos_pf = min(entry["profit_factor"]["oos"], 4.0) if entry["sample_size_oos"] >= 5 else 1.0
    lift = entry["probability"]["oos_dir_lift"]
    wf_pos = entry["walk_forward"]["positive_folds"]

    exp_term = max(-15.0, min(35.0, oos_exp * 6.0 * math.sqrt(max(1, min(n_oos, 64)))))
    pf_term = max(-5.0, (oos_pf - 1.0) * 8.0)
    lift_term = max(-5.0, lift * 40.0)
    wf_term = wf_pos * 3.0
    return round(status_bonus + exp_term + pf_term + lift_term + wf_term, 3)


def _derive_regime_priority_tag(entry: Dict[str, Any]) -> str:
    sub = entry.get("best_sub_regime_oos")
    if sub:
        return sub
    oos_rb = entry.get("regime_breakdown_oos", {})
    if oos_rb:
        best_r = max(oos_rb.items(), key=lambda kv: kv[1].get("expectancy_usd", -999.0))
        if best_r[1].get("expectancy_usd", 0.0) > 0:
            return f"REGIME:{best_r[0]}"
    return "REGIME:ALL_LIVE"


def _format_entry_20_fields(
    raw: Dict[str, Any],
    rank: int,
    fdr_q: float,
    jitter_info: Dict[str, Any],
    unit_exp_floor: float = 0.05,
) -> Dict[str, Any]:
    h = raw["primary_horizon_bars"]
    prob = raw["probability"]
    oos_p = prob["oos_primary"]
    d = raw["direction"]
    expected_dir_prob = prob["oos_dir_prob"]
    avg_mv = oos_p.get("avg_move_atr", 0.0)
    mfe_mae = raw["mfe_mae"]

    expected_behavior = (
        f"{d} over next {h} M1 bars (~{h}m): OOS P({d})={expected_dir_prob*100:.1f}% "
        f"(vs baseline {prob['oos_base_prob']*100:.1f}%, lift {prob['oos_dir_lift']*100:+.1f}%), "
        f"avg move {avg_mv:+.3f} ATR, MFE before MAE {mfe_mae['pct_mfe_before_mae']*100:.1f}%"
    )

    cats = _assign_categories(raw, unit_exp_floor=unit_exp_floor)
    priority_tag = _derive_regime_priority_tag(raw)
    compact_prob = {
        "primary_horizon_bars": prob["primary_horizon_bars"],
        "oos_dir_prob": prob["oos_dir_prob"],
        "oos_base_prob": prob["oos_base_prob"],
        "oos_dir_lift": prob["oos_dir_lift"],
        "all_dir_prob": prob["all_dir_prob"],
        "all_dir_lift": prob["all_dir_lift"],
        "dir_p_value_oos": prob["dir_p_value_oos"],
        "oos_primary": {
            "n_valid": oos_p.get("n_valid", 0),
            "p_bull": oos_p.get("p_bull", 0.0),
            "p_bear": oos_p.get("p_bear", 0.0),
            "p_neutral": oos_p.get("p_neutral", 0.0),
            "avg_move_atr": avg_mv,
        },
        "horizons_oos": prob["horizons_oos"],
    }
    keep_full_bd = raw["validation_status"] in ("VALIDATED_OOS", "REGIME_SPECIFIC_EDGE", "RARE_HIGH_EDGE") or rank <= 35

    return {
        # Exact 20 Required Fields (Prompt Section 9)
        "rank": rank,
        "condition_name": raw["condition_name"],
        "condition_type": raw["condition_type"],
        "timeframes": raw["timeframes"],
        "pre_condition": raw["pre_condition"],
        "event_sequence": raw["event_sequence"],
        "entry_criteria": raw["entry_criteria"],
        "direction": raw["direction"],
        "expected_behavior": expected_behavior,
        "probability": compact_prob,
        "win_rate": raw["win_rate"],
        "expectancy": raw["expectancy"],
        "profit_factor": raw["profit_factor"],
        "mfe_mae": raw["mfe_mae"],
        "time_horizon": {
            "primary_bars": h,
            "label": f"M1 +{h} bars (~{h}m)",
            "horizons_evaluated": [5, 15, 30, 60],
        },
        "frequency": {
            "per_1000_bars": raw["frequency_per_1000_bars"],
            "per_day": raw["frequency_per_day"],
            "raw_triggers": raw["raw_trigger_count"],
            "declustered_episodes": raw["sample_size_total"],
        },
        "sample_size": {
            "total": raw["sample_size_total"],
            "in_sample": raw["sample_size_is"],
            "out_of_sample": raw["sample_size_oos"],
        },
        "sl_tp": {
            "sl_atr": raw["sl_atr"],
            "tp_atr": raw["tp_atr"],
            "rr_ratio": raw["rr_ratio"],
            "mode": "Adaptive ATR (Frozen on IS)",
        },
        "reliability": raw["reliability"],
        "validation": {
            "status": raw["validation_status"],
            "best_sub_regime_oos": raw["best_sub_regime_oos"],
            "walk_forward_positive_folds": raw["walk_forward"]["positive_folds"],
            "walk_forward_total_folds": raw["walk_forward"]["total_folds"],
            "walk_forward_avg_exp_usd": raw["walk_forward"]["avg_expectancy_usd"],
            "fdr_q_value": fdr_q,
            "jitter_stability": jitter_info,
        },
        # Structured Quant Metadata
        "symbol": raw["symbol"],
        "categories": cats,
        "evidence_score": _evidence_score(raw),
        "formatted_sequence": raw["formatted_sequence"],
        "requires_microstructure": raw.get("requires_microstructure", False),
        "data_tier_provenance": raw.get("data_tier_provenance", "HYBRID_LIVE_M1"),
        "discovery_round": int(raw.get("discovery_round", 1)),
        "session_scope": str(raw.get("session_scope", "ALL")),
        "base_condition_ref": raw.get("base_condition_ref"),
        "base_condition_type": raw.get("base_condition_type"),
        "session_lift_vs_allday": raw.get("session_lift_vs_allday"),
        "regime_priority_tag": priority_tag,
        "ablation_lift": raw.get("ablation_lift"),
        "sequence_timing": raw.get("sequence_timing"),
        "walk_forward": raw["walk_forward"] if keep_full_bd else {"positive_folds": raw["walk_forward"]["positive_folds"], "total_folds": raw["walk_forward"]["total_folds"]},
        "regime_breakdown_oos": raw["regime_breakdown_oos"] if keep_full_bd else {},
        "session_breakdown_oos": raw["session_breakdown_oos"] if keep_full_bd else {},
        "vol_breakdown": raw["vol_breakdown"] if keep_full_bd else {},
    }


def _extract_jitter_indices(
    entry: Dict[str, Any],
    m1: Dict[str, Any],
    ev_set: Dict[str, Dict[str, Any]],
    htf_projected: Dict[str, Dict[str, Any]],
) -> np.ndarray:
    ctype = entry["condition_type"]
    effective_type = entry.get("base_condition_type") or ctype if ctype in ("Session-Micro", "Session-Specific") else ctype
    steps = entry["event_sequence"]

    if effective_type == "Single":
        nm = steps[0]
        idxs = np.flatnonzero(ev_set[nm]["mask"]) if nm in ev_set else np.zeros(0, dtype=np.int64)
    elif effective_type == "Sequential":
        if all(all(p.strip() in ev_set for p in s.split("+") if p.strip()) for s in steps):
            matched = match_anchored_sequence(m1, steps, ev_set, max_gap=20)
            idxs = matched["indices"]
        else:
            idxs = np.zeros(0, dtype=np.int64)
    else:
        ltf_raw = steps[-1].replace("M1_", "")
        if ltf_raw not in ev_set:
            idxs = np.zeros(0, dtype=np.int64)
        else:
            mask = ev_set[ltf_raw]["mask"].copy()
            for htok in steps[:-1]:
                if htok in htf_projected:
                    mask &= htf_projected[htok]["mask"]
            idxs = np.flatnonzero(mask)

    zone = entry.get("session_scope")
    if ctype in ("Session-Micro", "Session-Specific") and zone and zone != "ALL" and len(idxs) > 0:
        sz_arr = m1["session_zone"]
        idxs = idxs[sz_arr[idxs] == zone]
    return idxs


def _run_jitter_check_for_symbol(
    dataset: Dict[str, Any],
    level_m1: Dict[str, np.ndarray],
    htf_projected: Dict[str, Dict[str, Any]],
    baselines: Dict[Any, Any],
    top_entries: List[Dict[str, Any]],
) -> Dict[str, Dict[str, Any]]:
    """Tests +-15% threshold stability (`jitter_scale = 0.85, 1.15`) on top patterns (session-aware)."""
    events_low = tokenize_m1_events(dataset, level_m1, jitter_scale=0.85)
    events_high = tokenize_m1_events(dataset, level_m1, jitter_scale=1.15)
    m1 = dataset["m1"]

    jitter_map: Dict[str, Dict[str, Any]] = {}
    for entry in top_entries:
        cname = entry["condition_name"]
        pdir = entry["direction"]
        base_exp = entry["expectancy"]["oos_usd"]

        exps = {}
        for lbl, ev_set in (("0.85", events_low), ("1.15", events_high)):
            idxs = _extract_jitter_indices(entry, m1, ev_set, htf_projected)
            sim_res = evaluate_condition(dataset, baselines, idxs, pdir, {"condition_name": f"jit_{lbl}_{cname}"}, cooldown_bars=10)
            exps[lbl] = sim_res["expectancy"]["oos_usd"]

        stable = (exps["0.85"] > 0 and exps["1.15"] > 0) if base_exp > 0 else (
            abs(exps["0.85"] - base_exp) <= 0.15 and abs(exps["1.15"] - base_exp) <= 0.15
        )
        jitter_map[cname] = {
            "tested": True,
            "oos_exp_085": exps["0.85"],
            "oos_exp_100": base_exp,
            "oos_exp_115": exps["1.15"],
            "stable": bool(stable),
        }
    return jitter_map


def analyze_symbol_patterns(
    symbol: str,
    fetch_ctrader: bool = True,
    preloaded_dataset: Optional[Dict[str, Any]] = None,
    include_round2: bool = True,
) -> Dict[str, Any]:
    """Executes Round 1 + Round 2 discovery, Benjamini-Hochberg FDR & +-15% Jitter test on one symbol."""
    dataset = preloaded_dataset if preloaded_dataset is not None else load_scalping_mtf_dataset(symbol, fetch_ctrader=fetch_ctrader)
    m1 = dataset["m1"]

    # 1. Extract Causal Level Memory on M1 and all HTFs
    level_m1 = extract_level_structure(m1, pivot_left=3, pivot_right=3, is_m1_live=True)
    m1_events = tokenize_m1_events(dataset, level_m1, jitter_scale=1.0)

    htf_tokens: Dict[str, Dict[str, np.ndarray]] = {}
    for tf, tf_data in dataset["htf"].items():
        if tf_data["n"] > 0:
            htf_lvl = extract_level_structure(tf_data, pivot_left=2, pivot_right=2, is_m1_live=False)
            htf_tokens[tf] = tokenize_htf_events(tf_data, htf_lvl)
        else:
            htf_tokens[tf] = {}
    htf_projected = project_htf_events_to_m1(dataset, htf_tokens)

    # 2. Compute Regime-Matched Empirical Baselines
    baselines = compute_regime_baselines(dataset)

    # 3. Round 1 Discovery (Single + Sequences + MTF Confluence)
    r1_singles = mine_single_conditions(dataset, m1_events, baselines)
    r2_out = mine_multi_step_sequences(dataset, m1_events, r1_singles, baselines, max_gap=20)
    r3_out = mine_mtf_patterns(dataset, m1_events, htf_projected, r1_singles, baselines)

    r1_all: List[Dict[str, Any]] = r1_singles + r2_out["sequences"] + r3_out["mtf_conditions"]
    for item in r1_all:
        item.setdefault("discovery_round", 1)
        item.setdefault("session_scope", "ALL")

    raw_all: List[Dict[str, Any]] = list(r1_all)
    r2_ob_branches: List[Dict[str, Any]] = []
    r2_session_playbook: Dict[str, Dict[str, Any]] = {}
    r2_count = 0

    # 4. Round 2 Discovery (Order Book Sequences + XAU/BTC Micro MTF + 7-Zone Session Mining)
    if include_round2:
        existing_names = {r["condition_name"] for r in r1_all}
        r2_ob = mine_orderbook_sequences(
            dataset, m1_events, r1_singles, baselines, existing_names=existing_names, max_gap=18
        )
        ob_seqs = r2_ob["orderbook_sequences"]
        r2_ob_branches = r2_ob["orderbook_branching_patterns"]
        existing_names.update(r["condition_name"] for r in ob_seqs)

        r2_micro_mtf: List[Dict[str, Any]] = []
        if symbol in ("XAUUSD", "BTCUSD"):
            r2_micro_mtf = mine_micro_mtf_fusion(
                dataset, m1_events, htf_projected, baselines, existing_names=existing_names
            )
            existing_names.update(r["condition_name"] for r in r2_micro_mtf)

        base_for_sessions = r1_all + ob_seqs + r2_micro_mtf
        r2_ses = mine_session_specific_patterns(
            dataset, m1_events, htf_projected, base_for_sessions, baselines, existing_names=existing_names
        )
        ses_conds = r2_ses["session_conditions"]
        r2_session_playbook = r2_ses["session_playbook"]

        r2_items = ob_seqs + r2_micro_mtf + ses_conds
        r2_count = len(r2_items)
        raw_all.extend(r2_items)

    # 5. Benjamini-Hochberg FDR across all tested Round 1 + Round 2 conditions
    raw_pvals = [float(r.get("raw_fdr_p_value", 1.0)) for r in raw_all]
    q_vals = benjamini_hochberg_fdr(raw_pvals)

    # Sort raw candidates by composite evidence score
    scored_pairs = sorted(zip(raw_all, q_vals), key=lambda x: _evidence_score(x[0]), reverse=True)

    # 6. +-15% Parameter Perturbation Stability check on top 35 candidates
    top_for_jitter = [pair[0] for pair in scored_pairs[:35]]
    jitter_map = _run_jitter_check_for_symbol(dataset, level_m1, htf_projected, baselines, top_for_jitter)

    # 7. Build exact 20-field library entries
    spec = dataset["spec"]
    unit_exp_floor = min(0.05, max(0.004, float(spec["min_atr"]) * float(spec["lot_scale"]) * 0.5))
    all_entries: List[Dict[str, Any]] = []
    for idx, (raw_item, qv) in enumerate(scored_pairs, start=1):
        j_info = jitter_map.get(raw_item["condition_name"], {"tested": False})
        all_entries.append(_format_entry_20_fields(raw_item, rank=idx, fdr_q=qv, jitter_info=j_info, unit_exp_floor=unit_exp_floor))

    # Compact JSON archive filter: keep ALL validated/regime/rare edges + all Single events + top 30 remaining
    archived_entries: List[Dict[str, Any]] = []
    extra_kept = 0
    for e in all_entries:
        st = e["validation"]["status"]
        if st in ("VALIDATED_OOS", "REGIME_SPECIFIC_EDGE", "RARE_HIGH_EDGE") or e["condition_type"] == "Single":
            archived_entries.append(e)
        elif extra_kept < 30:
            archived_entries.append(e)
            extra_kept += 1

    val_counts = Counter(e["validation"]["status"] for e in all_entries)
    r1_val_counts = Counter(e["validation"]["status"] for e in all_entries if e["discovery_round"] == 1)
    r2_val_counts = Counter(e["validation"]["status"] for e in all_entries if e["discovery_round"] == 2)
    cat_counts = Counter(cat for e in all_entries for cat in e["categories"])

    live_mask = m1["has_l2_dom"] & m1["has_real_spread"]
    flow_mask = live_mask & m1["has_order_flow"]

    return {
        "symbol": symbol,
        "data_audit": {
            "total_m1_bars": int(m1["n"]),
            "live_microstructure_bars": int(np.sum(live_mask)),
            "live_order_flow_bars": int(np.sum(flow_mask)),
            "start_time_utc": m1["time_strs"][0] if m1["n"] else None,
            "end_time_utc": m1["time_strs"][-1] if m1["n"] else None,
            "is_cutoff_utc": m1["time_strs"][dataset["is_cutoff_idx"]] if m1["n"] else None,
            "tf_sources": dataset["tf_sources"],
            "htf_bar_counts": {tf: int(d["n"]) for tf, d in dataset["htf"].items()},
        },
        "summary_counts": {
            "total_conditions_tested": len(all_entries),
            "conditions_archived_in_json": len(archived_entries),
            "round1_tested": len(r1_all),
            "round2_tested": r2_count,
            "single_count": len(r1_singles),
            "sequential_count": sum(1 for e in all_entries if e["condition_type"] == "Sequential"),
            "mtf_count": sum(1 for e in all_entries if e["condition_type"] == "Multi-TF"),
            "session_count": sum(1 for e in all_entries if e["condition_type"] in ("Session-Micro", "Session-Specific")),
            "validation_breakdown": dict(val_counts),
            "round1_validation_breakdown": dict(r1_val_counts),
            "round2_validation_breakdown": dict(r2_val_counts),
            "category_breakdown": dict(cat_counts),
        },
        "confluence_proof": r3_out["confluence_proof"],
        "temporal_order_checks": r3_out["temporal_order_checks"],
        "branching_patterns": r2_out["branching_patterns"],
        "converging_patterns": r2_out["converging_patterns"],
        "round2_highlights": {
            "orderbook_branching_patterns": r2_ob_branches,
            "session_playbook": r2_session_playbook,
            "round1_vs_round2_summary": {
                "round1_tested": len(r1_all),
                "round1_validated_or_regime": sum(r1_val_counts.get(k, 0) for k in ("VALIDATED_OOS", "REGIME_SPECIFIC_EDGE", "RARE_HIGH_EDGE")),
                "round2_tested": r2_count,
                "round2_validated_or_regime": sum(r2_val_counts.get(k, 0) for k in ("VALIDATED_OOS", "REGIME_SPECIFIC_EDGE", "RARE_HIGH_EDGE")),
            },
        },
        "conditions": archived_entries,
    }


def _write_json_atomic(path: Path, payload: Any, compact: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    text = (
        json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
        if compact
        else json.dumps(payload, indent=2, ensure_ascii=False)
    )
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def render_library_markdown(lib: Dict[str, Any]) -> str:
    """Renders structured TRADING_CONDITION_LIBRARY_REPORT.md covering all 20 fields and empirical proofs."""
    lines: List[str] = [
        "# 📚 TRADING CONDITION LIBRARY REPORT (V5 Scalping & Intraday Pattern Discovery)",
        "",
        f"> **Generated (UTC):** `{lib['generated_at_utc']}` · **Data Scope:** Tier 1 Pure Live L2 DOM/Order Flow/Real Spread + Tier 2 cTrader Real Multi-TF OHLCV (Strict Zero-Lookahead, Next-Bar Open + Friction, Chronological 60/40 IS/OOS + 3-Fold Walk-Forward)",
        "",
        "---",
        "",
        "## 1. Data Provenance & Portfolio Validation Summary",
        "",
        "| Symbol | M1 Total Bars | Live DOM+Spread Bars | Order Flow Bars | Range (UTC) | Tested | `VALIDATED_OOS` | `REGIME_SPECIFIC` | `RARE_HIGH_EDGE` | `IS_ONLY_OVERFIT` | `NO_EDGE` | `INSUFFICIENT` |",
        "| :--- | :---: | :---: | :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |",
    ]

    for sym, sdata in lib["symbols"].items():
        da = sdata["data_audit"]
        sc = sdata["summary_counts"]
        vb = sc["validation_breakdown"]
        lines.append(
            f"| **{sym}** | {da['total_m1_bars']:,} | {da['live_microstructure_bars']:,} | {da['live_order_flow_bars']:,} | "
            f"`{da['start_time_utc']} -> {da['end_time_utc']}` | {sc['total_conditions_tested']} | "
            f"**{vb.get('VALIDATED_OOS', 0)}** | {vb.get('REGIME_SPECIFIC_EDGE', 0)} | {vb.get('RARE_HIGH_EDGE', 0)} | "
            f"{vb.get('IS_ONLY_OVERFIT', 0)} | {vb.get('NO_EDGE', 0)} | {vb.get('INSUFFICIENT_DATA', 0)} |"
        )

    lines.extend([
        "",
        "## 1B. Iteration Round 1 vs Round 2 Yield Comparison",
        "",
        "| Symbol | Round | Tested | `VALIDATED_OOS` | `REGIME_SPECIFIC` | `RARE_HIGH_EDGE` | `IS_ONLY_OVERFIT` | `NO_EDGE` | Total Edge Rate |",
        "| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |",
    ])
    for sym, sdata in lib["symbols"].items():
        sc = sdata["summary_counts"]
        for rlbl, n_tst, vmap in (
            ("Round 1 (Base)", sc.get("round1_tested", 0), sc.get("round1_validation_breakdown", {})),
            ("Round 2 (OB + Session)", sc.get("round2_tested", 0), sc.get("round2_validation_breakdown", {})),
        ):
            edges = vmap.get("VALIDATED_OOS", 0) + vmap.get("REGIME_SPECIFIC_EDGE", 0) + vmap.get("RARE_HIGH_EDGE", 0)
            rate = (edges / n_tst * 100.0) if n_tst > 0 else 0.0
            lines.append(
                f"| **{sym}** | {rlbl} | {n_tst} | **{vmap.get('VALIDATED_OOS', 0)}** | {vmap.get('REGIME_SPECIFIC_EDGE', 0)} | "
                f"{vmap.get('RARE_HIGH_EDGE', 0)} | {vmap.get('IS_ONLY_OVERFIT', 0)} | {vmap.get('NO_EDGE', 0)} | `{rate:.1f}%` |"
            )

    lines.extend(["", "## 2. Empirical Multi-Timeframe Confluence Proof (`1 TF` vs `2 TF` vs `3+ TF`)", ""])
    lines.append("| Symbol | Tier | Patterns | Avg OOS N | Avg OOS P(Dir) | Avg OOS Win Rate | Avg OOS Expectancy (USD) | Avg OOS PF | Verdict |")
    lines.append("| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |")

    for sym, sdata in lib["symbols"].items():
        cp = sdata["confluence_proof"]
        verdict = cp["verdict"]
        for tkey in ("1_TF", "2_TF", "3_PLUS_TF"):
            tr = cp["tiers"][tkey]
            lines.append(
                f"| **{sym}** | `{tkey}` | {tr['patterns_tested']} | {tr['avg_oos_sample']} | "
                f"{tr['avg_oos_dir_prob']*100:.1f}% | {tr['avg_oos_win_rate']*100:.1f}% | "
                f"{tr['avg_oos_expectancy_usd']:+.4f} | {tr['avg_oos_pf']:.2f} | `{verdict if tkey == '3_PLUS_TF' else '-'}` |"
            )

    for sym, sdata in lib["symbols"].items():
        lines.extend([
            "",
            "---",
            "",
            f"## 3. {sym} — Top Discovered Conditions & 20-Field Trading Condition Library",
            "",
            "| Rank | Condition Name | Type | TFs | Dir | OOS P(Dir) / Lift | OOS WR (Wilson LB) | OOS Exp (USD) | OOS PF | MFE / MAE | Horizon | Freq/Day | N (IS/OOS) | SL/TP (ATR) | WF Folds | Jitter ±15% | Status / Reliability |",
            "| :---: | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |",
        ])

        top_rows = sdata["conditions"][:20]
        for c in top_rows:
            pb = c["probability"]
            wr = c["win_rate"]
            ex = c["expectancy"]
            pf = c["profit_factor"]
            mm = c["mfe_mae"]
            ss = c["sample_size"]
            st = c["sl_tp"]
            val = c["validation"]
            jit = val["jitter_stability"]
            jit_str = ("PASS" if jit.get("stable") else "FRAGILE") if jit.get("tested") else "-"
            lines.append(
                f"| #{c['rank']} | `{c['condition_name']}` | {c['condition_type']} | `{'+'.join(c['timeframes'])}` | "
                f"**{c['direction']}** | {pb['oos_dir_prob']*100:.1f}% ({pb['oos_dir_lift']*100:+.1f}%) | "
                f"{wr['oos']*100:.1f}% ({wr['oos_wilson_lb95']*100:.1f}%) | {ex['oos_usd']:+.4f} | {pf['oos']:.2f} | "
                f"{mm['avg_mfe_atr']:.2f} / {mm['avg_mae_atr']:.2f} | `+{c['time_horizon']['primary_bars']}b` | "
                f"{c['frequency']['per_day']:.1f}/d | {ss['total']} ({ss['in_sample']}/{ss['out_of_sample']}) | "
                f"{st['sl_atr']:.1f} / {st['tp_atr']:.1f} | {val['walk_forward_positive_folds']}/{val['walk_forward_total_folds']} | "
                f"{jit_str} | `{val['status']}` (`{c['reliability']}`) |"
            )

        # Formatted sequences for top 8 edges
        lines.extend(["", f"### {sym} — Structured Event Sequences (`HTF Context → MTF Setup → LTF Trigger → Entry → Outcome`)", ""])
        for c in top_rows[:8]:
            ab = c.get("ablation_lift")
            ab_str = ""
            if ab:
                ab_str = (
                    f" | Ablation Lift vs prev: ΔP=`{(ab['delta_oos_prob_vs_prev'] or 0)*100:+.1f}%`, "
                    f"ΔExp=`{ab['delta_oos_exp_vs_prev'] or 0:+.4f} USD`"
                )
            lines.append(
                f"- **#{c['rank']} `{c['condition_name']}`** ({c['validation']['status']}): "
                f"`{c['formatted_sequence']}` · {c['expected_behavior']}{ab_str}"
            )

        # Branching & Converging highlights
        bps = sdata.get("branching_patterns", [])
        if bps:
            lines.extend(["", f"### {sym} — Branching Patterns (Same Prefix Diverging by Next Step)", ""])
            for bp in bps[:4]:
                b_txt = " ; ".join(
                    f"`{b['next_step']}` ➔ **{b['direction']}** (N={b['sample_size']}, OOS P={b['oos_dir_prob']*100:.1f}%, Exp={b['oos_expectancy_usd']:+.3f})"
                    for b in bp["branches"]
                )
                lines.append(f"- Prefix `{bp['shared_prefix']}`: {b_txt}")

    # Section 4: Round 2 Order Book Imbalance, Liquidity Ladder & Microstructure Sequences (XAUUSD & BTCUSD)
    lines.extend([
        "",
        "---",
        "",
        "## 4. Round 2 Deep Dive — Order Book Imbalance, Liquidity Ladder & Microstructure Sequences (`XAUUSD` & `BTCUSD`)",
        "",
    ])
    for sym in ("XAUUSD", "BTCUSD"):
        sdata = lib["symbols"].get(sym)
        if not sdata:
            continue
        ob_rows = [
            c for c in sdata["conditions"]
            if c.get("discovery_round") == 2 and c.get("session_scope") == "ALL"
        ][:15]
        if not ob_rows:
            continue
        lines.extend([
            f"### {sym} — Top Order Book Imbalance & Microstructure Patterns (Round 2)",
            "",
            "| Rank | Condition Name | Type | Dir | OOS P(Dir) / Lift | OOS WR | OOS Exp (USD) | OOS PF | N (IS/OOS) | Ablation ΔP / ΔExp | WF Folds | Jitter ±15% | Status |",
            "| :---: | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |",
        ])
        for c in ob_rows:
            pb = c["probability"]
            wr = c["win_rate"]
            ex = c["expectancy"]
            pf = c["profit_factor"]
            ss = c["sample_size"]
            val = c["validation"]
            jit = val["jitter_stability"]
            jit_str = ("PASS" if jit.get("stable") else "FRAGILE") if jit.get("tested") else "-"
            ab = c.get("ablation_lift")
            ab_str = (
                f"`{(ab.get('delta_oos_prob_vs_prev') or 0)*100:+.1f}%` / `{ab.get('delta_oos_exp_vs_prev') or 0:+.3f}`"
                if ab
                else "-"
            )
            lines.append(
                f"| #{c['rank']} | `{c['condition_name']}` | {c['condition_type']} | **{c['direction']}** | "
                f"{pb['oos_dir_prob']*100:.1f}% ({pb['oos_dir_lift']*100:+.1f}%) | {wr['oos']*100:.1f}% | "
                f"{ex['oos_usd']:+.4f} | {pf['oos']:.2f} | {ss['total']} ({ss['in_sample']}/{ss['out_of_sample']}) | "
                f"{ab_str} | {val['walk_forward_positive_folds']}/{val['walk_forward_total_folds']} | {jit_str} | `{val['status']}` |"
            )

        ob_bps = sdata.get("round2_highlights", {}).get("orderbook_branching_patterns", [])
        if ob_bps:
            lines.extend(["", f"**{sym} Order Book Branching Divergences:**", ""])
            for bp in ob_bps[:3]:
                b_txt = " ; ".join(
                    f"`{b['next_step']}` ➔ **{b['direction']}** (N={b['sample_size']}, Exp={b['oos_expectancy_usd']:+.3f})"
                    for b in bp["branches"]
                )
                lines.append(f"- Prefix `{bp['shared_prefix']}`: {b_txt}")
        lines.append("")

    # Section 5: 7-Zone Session-Specific Scalping Playbooks (XAUUSD & BTCUSD)
    lines.extend([
        "---",
        "",
        "## 5. 7-Zone Session-Specific Scalping Playbooks (`XAUUSD` & `BTCUSD`)",
        "",
    ])
    for sym in ("XAUUSD", "BTCUSD"):
        sdata = lib["symbols"].get(sym)
        if not sdata:
            continue
        pb_map = sdata.get("round2_highlights", {}).get("session_playbook", {})
        if not pb_map:
            continue
        lines.extend([
            f"### {sym} — Winning Pattern & Session Lift per Session Zone",
            "",
            "| Session Zone | Winning Condition | Type | Dir | N (IS/OOS) | Session OOS WR | Session OOS Exp (USD) | Session OOS PF | All-Day Exp (USD) | Session Lift | SL/TP (ATR) | Status |",
            "| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |",
        ])
        for zone, zp in pb_map.items():
            lines.append(
                f"| **`{zone}`** | `{zp['best_condition']}` | {zp['condition_type']} | **{zp['direction']}** | "
                f"{zp['sample_size']} ({zp['sample_is_oos']}) | {zp['oos_win_rate']*100:.1f}% | "
                f"{zp['oos_expectancy_usd']:+.4f} | {zp['oos_profit_factor']:.2f} | "
                f"{zp['allday_oos_exp_usd']:+.4f} | **`{zp['delta_oos_exp_vs_allday']:+.4f}`** | "
                f"{zp['sl_atr']:.1f} / {zp['tp_atr']:.1f} | `{zp['validation_status']}` |"
            )
        lines.append("")

    return "\n".join(lines) + "\n"


def build_trading_condition_library(
    symbols: Tuple[str, ...] = ("XAUUSD", "BTCUSD", "ETHUSD"),
    fetch_ctrader: bool = True,
    output_json_path: Optional[Path] = None,
    output_state_path: Optional[Path] = None,
    output_report_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """Runs full 3-symbol Scalping/Intraday Pattern Discovery (Round 1 + Round 2) and writes Library, State, and Report."""
    sym_results: Dict[str, Any] = {}
    all_signatures: List[str] = []

    for sym in symbols:
        res = analyze_symbol_patterns(sym, fetch_ctrader=fetch_ctrader, include_round2=True)
        sym_results[sym] = res
        for c in res["conditions"]:
            all_signatures.append(f"{sym}:{c['condition_name']}")

    now_utc = datetime.now(timezone.utc).isoformat()
    library_payload = {
        "schema_version": "5.2.0-SCALPING-PATTERN-LIBRARY-R2",
        "generated_at_utc": now_utc,
        "scope": "Scalping & Intraday (M1/M5/M15 triggers + H1/H4 Dual-HTF context + Round 2 OrderBook & Session-Specific) fusing Tier 1 Live L2 DOM/Order Flow/Real Spread & Tier 2 cTrader MTF OHLCV",
        "methodology_safeguards": [
            "Zero Future Lookahead (closed HTF bar + causal developing HTF + pivot confirmation lag)",
            "Episode De-clustering (cooldown >= 10 M1 bars per independent episode)",
            "Session-Normalized Z-Scores across 7 UTC Session/Transition zones",
            "Next-Bar Open Entry + Real Spread + Slippage + Commission + Conservative SL-First Tie-Break",
            "Strict Chronological 60/40 IS/OOS + 3-Fold Rolling Walk-Forward + Benjamini-Hochberg FDR + Session-Aware +-15% Jitter Test",
        ],
        "symbols": sym_results,
    }

    total_tested = sum(sym_results[s]["summary_counts"]["total_conditions_tested"] for s in symbols)
    state_payload = {
        "schema_version": "5.2.0-DISCOVERY-STATE",
        "last_run_utc": now_utc,
        "iteration_round": 2,
        "rounds_completed": [
            "Round_1_Single_Conditions",
            "Round_2_Anchored_Sequences",
            "Round_3_Dual_HTF_MTF_Confluence",
            "Round_2_OrderBook_Imbalance_Sequences",
            "Round_2_Session_Specific_Mining",
            "Round_2_XAU_BTC_Microstructure_DeepDive",
        ],
        "symbols_covered": list(symbols),
        "total_conditions_archived": total_tested,
        "conditions_archived_in_json": len(all_signatures),
        "validated_summary": {
            sym: sym_results[sym]["summary_counts"]["validation_breakdown"]
            for sym in symbols
        },
        "round2_yield": {
            sym: sym_results[sym]["round2_highlights"]["round1_vs_round2_summary"]
            for sym in symbols
        },
        "scanned_signatures_count": total_tested,
    }

    json_path = output_json_path or (REPO_ROOT / "docs" / "data" / "trading_condition_library.json")
    state_path = output_state_path or (REPO_ROOT / "docs" / "data" / "pattern_discovery_state.json")
    report_path = output_report_path or (REPO_ROOT / "TRADING_CONDITION_LIBRARY_REPORT.md")

    _write_json_atomic(json_path, library_payload, compact=True)
    _write_json_atomic(state_path, state_payload, compact=False)
    report_md = render_library_markdown(library_payload)
    report_path.write_text(report_md, encoding="utf-8")

    return library_payload
