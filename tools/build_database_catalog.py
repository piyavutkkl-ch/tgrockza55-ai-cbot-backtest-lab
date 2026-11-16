#!/usr/bin/env python3
"""
Build unified metadata catalog (docs/assets/database_catalog.json) for Page 8 (Unified Database).
Scans all files in docs/data/, preserves the 33 canonical core JSON datasets under the 5 primary
folders ("Live Telemetry", "Backtest Runs", "Strategy Registries", "Research Papers", "Audit Logs"),
and indexes generated UI caches / Markdown reports as optional secondary scope.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "docs" / "data"
OUT_PATH = ROOT / "docs" / "assets" / "database_catalog.json"

FOLDER_SPECS = [
    {
        "id": "live_telemetry",
        "name": "Live Telemetry",
        "icon": "telemetry",
        "dot": "green",
        "description": "Real-time Pepperstone Demo #5258778 feed, M1 streams, Watchdog health, and calibrated costs",
    },
    {
        "id": "backtest_runs",
        "name": "Backtest Runs",
        "icon": "backtest",
        "dot": "green",
        "description": "Strategy backtest equity curves, trade logs, 13-engine benchmarks, and XAUUSD horizon studies",
    },
    {
        "id": "strategy_registries",
        "name": "Strategy Registries",
        "icon": "registry",
        "dot": "green",
        "description": "Institutional strategy catalog STR-001..010, Champion arena promotions, and rule tiers",
    },
    {
        "id": "research_papers",
        "name": "Research Papers",
        "icon": "papers",
        "dot": "green",
        "description": "193 ArXiv quantitative papers, symbolic alpha mining, and behavioral alpha models",
    },
    {
        "id": "audit_logs",
        "name": "Audit Logs",
        "icon": "audit",
        "dot": "green",
        "description": "Truth Guard empirical audits, validation gates, alerts, flywheel cycles, and Supabase snapshots",
    },
]

CORE_FOLDER_MAP: dict[str, tuple[str, str, str]] = {
    # Live Telemetry (6)
    "live_status.json": ("live_telemetry", "live_fleet_v4", "Pepperstone #5258778 live bots fleet, open trades, closed deals & flywheel snapshot"),
    "live_market_intelligence.json": ("live_telemetry", "market_intel_v4", "Real-time market regimes, order flow delta, DOM imbalance & active strategy selector"),
    "terminal_stream_data.json": ("live_telemetry", "m1_stream_v1", "Full M1 stream playback bars & executed trade markers (XAUUSD, BTCUSD, ETHUSD)"),
    "terminal_compact.json": ("live_telemetry", "m1_compact_v1", "Compact initial + streaming M1 terminal bars across live symbols"),
    "watchdog_status.json": ("live_telemetry", "watchdog_guard_v1", "24/7 LiveRecorder fleet supervisor health & stall alert diagnostics"),
    "calibrated_costs.json": ("live_telemetry", "cost_model_v1", "Empirical spread, slippage, swap & commission calibration per instrument"),

    # Backtest Runs (7)
    "backtest_data.json": ("backtest_runs", "backtest_suite_v4", "Verified Champion & Challenger backtest trades, equity curves & performance summary"),
    "benchmark_13_engines_results.json": ("backtest_runs", "engine_bench_13", "13 C# Strategy Engine benchmark metrics across BTCUSD, ETHUSD & GOLD-PERP"),
    "exhaustive_13_engines_optimization.json": ("backtest_runs", "engine_grid_13", "Exhaustive parameter grid optimization runs across 13 DOM engines"),
    "phase1-XAUUSD.json": ("backtest_runs", "phase1_study_v1", "Phase 1 XAUUSD multi-horizon feature predictability & news event study"),
    "daystudy-XAUUSD.json": ("backtest_runs", "daystudy_xau_v1", "XAUUSD 774-day intraday session & weekday statistical edge breakdown"),
    "ha-examples.json": ("backtest_runs", "ha_signals_v1", "Heikin-Ashi microstructure entry & exit signal examples"),
    "experiment_registry.json": ("backtest_runs", "exp_registry_v4", "Experiment run ledger with immutable config SHA hashes & hypotheses"),

    # Strategy Registries (7)
    "strategy_registry.json": ("strategy_registries", "strategy_lib_v4", "Institutional Strategy Library STR-001..010 definitions & regimes"),
    "champion_registry.json": ("strategy_registries", "champion_arena_v1", "Nightly Showdown Champion/Challenger promotion tournament results"),
    "autonomous_champions.json": ("strategy_registries", "auto_champions_v1", "Synthesized autonomous champion configurations & portfolio ensemble"),
    "live_evolution_champions.json": ("strategy_registries", "live_evo_champ_v1", "Live microstructure evolution top configurations evaluated across assets"),
    "strategy_foundry.json": ("strategy_registries", "foundry_bots_v1", "Strategy Foundry active micro-bots, decommissioned bots & failure graveyard"),
    "strategy_evolution.json": ("strategy_registries", "evo_vault_v1", "Strategy evolution generations, immune memory & adaptive evolution policy"),
    "rule_classification_matrix.json": ("strategy_registries", "rule_matrix_v4", "Tier 1 immutable hard risk limits, Tier 2 adaptive rules & Tier 3 hypotheses"),

    # Research Papers (4)
    "papers_database.json": ("research_papers", "arxiv_papers_v1", "Catalog of 193 quantitative microstructure & execution research papers"),
    "alpha_discovery.json": ("research_papers", "alpha_miner_v1", "Symbolic algebraic alpha mining formulas & screening pass metrics"),
    "behavioral_alphas.json": ("research_papers", "behavioral_v3", "Quantified behavioral finance biases & disposition-effect alpha models"),
    "external_alphas.json": ("research_papers", "external_scout_v1", "External arXiv q-fin / SSRN / GitHub cTrader quantitative alpha leads"),

    # Audit Logs (9)
    "web_alerts.json": ("audit_logs", "web_alerts_v1", "Gatekeeper PASS/VETO, HITL approval gates & system incident alerts"),
    "truth_guard.json": ("audit_logs", "truth_guard_v4", "Empirical trade file audit from %LOCALAPPDATA%\\BacktestLab\\live & statistical power"),
    "autonomous_validation.json": ("audit_logs", "stats_audit_v1", "Deflated Sharpe Ratio (DSR), Monte Carlo permutation, SPRT & CSCV PBO checks"),
    "quant_fund_status.json": ("audit_logs", "quant_fund_v1", "Multi-agent Quant Fund V1 CEO directive, worker result & risk audit"),
    "quant_fund_v2_status.json": ("audit_logs", "quant_fund_v2", "10-node LangGraph V2 data quality gate, CEO policy & checklist status"),
    "agent_handovers.json": ("audit_logs", "agent_handover_v1", "8-officer multi-agent handover ledger & deliverable artifacts"),
    "flywheel_cycles.json": ("audit_logs", "flywheel_live_v2", "Continuous 24/7 evolution flywheel cycles & accumulated learnings"),
    "archive_historical_cycles_v1.json": ("audit_logs", "flywheel_archive_v1", "Archived 122 historical flywheel cycles prior to pure-live reset"),
    "supabase_v2_backup_latest.json": ("audit_logs", "supabase_v2_snap", "Local PostgreSQL/Supabase V2 backup of recent runs, policies & audit logs"),
    "hybrid_data_audit.json": ("live_telemetry", "hybrid_merger_v5", "Merged cTrader historical OHLCV/sessions + sanitized live L2 DOM/Order Flow audit"),
}

SECONDARY_DESCRIPTIONS: dict[str, tuple[str, str]] = {
    "overview_summary.json": ("ui_cache_p1", "Pre-computed compact summary feed for Page 1 Overview"),
    "dc_meta.json": ("ui_cache_p2", "Data Center live symbol metadata & DOM feed summary"),
    "dc_BTCUSD.json": ("ui_cache_p2", "Pre-built BTCUSD M1 OHLCV + DOM stream slice for Page 2 Data Center"),
    "dc_ETHUSD.json": ("ui_cache_p2", "Pre-built ETHUSD M1 OHLCV + DOM stream slice for Page 2 Data Center"),
    "dc_GOLD-PERP.json": ("ui_cache_p2", "Pre-built GOLD-PERP M1 OHLCV + DOM stream slice for Page 2 Data Center"),
    "dc_XAUUSD.json": ("ui_cache_p2", "Pre-built XAUUSD M1 OHLCV + DOM stream slice for Page 2 Data Center"),
    "research_lab_summary.json": ("ui_cache_p3", "Unified research bundle for Page 3 Research Lab"),
    "intelligence_summary.json": ("ui_cache_p5", "Aggregated performance matrix & microstructure bundle for Page 5 Intelligence"),
    "audit_summary.json": ("ui_cache_p6", "Aggregated governance & audit payload for Page 6 Improvement & Audit"),
    "archive_system_summary.json": ("ui_cache_p7", "Archive transcript & legacy summary for Page 7 Archive / System"),
    "13_engine_benchmark_scorecard.md": ("markdown_report", "13-Engine C# DOM Strategy Benchmark Scorecard (Markdown)"),
    "13_engine_optimization_report.md": ("markdown_report", "13-Engine Exhaustive Parameter Optimization Report (Markdown)"),
    "all_modules_max_profit_backtest.md": ("markdown_report", "All Modules Max-Profit Backtest Analysis Report (Markdown)"),
}


def format_size(num_bytes: int) -> str:
    if num_bytes >= 1024 * 1024:
        return f"{num_bytes / (1024 * 1024):.2f} MB"
    if num_bytes >= 1024:
        return f"{num_bytes / 1024:.1f} KB"
    return f"{num_bytes} B"


def extract_timestamp(obj: Any, fallback_mtime: float) -> str:
    if isinstance(obj, dict):
        for key in (
            "updated_at_utc",
            "updated_at",
            "timestamp_utc",
            "audited_at_utc",
            "audit_timestamp",
            "generated_at_utc",
            "generatedAt",
            "backup_created_at_utc",
            "arena_run_utc",
            "synthesized_at_utc",
            "calibrated_at",
            "last_scouted",
        ):
            val = obj.get(key)
            if isinstance(val, str) and val.strip():
                return val.strip()
        fw = obj.get("flywheel")
        if isinstance(fw, dict) and isinstance(fw.get("last_updated_utc"), str):
            return fw["last_updated_utc"]
    return datetime.fromtimestamp(fallback_mtime, tz=timezone.utc).isoformat()


def infer_record_stats(filename: str, parsed: Any) -> tuple[int, str, list[str]]:
    if filename == "backtest_data.json" and isinstance(parsed, dict):
        trades = sum(len(v.get("trades", [])) for v in parsed.values() if isinstance(v, dict))
        return trades, f"{trades:,} trades", list(parsed.keys())[:10]

    if filename in ("terminal_stream_data.json", "terminal_compact.json") and isinstance(parsed, dict):
        bars = 0
        for sym_obj in parsed.values():
            if isinstance(sym_obj, dict):
                bars += len(sym_obj.get("bars", [])) + len(sym_obj.get("initial", [])) + len(sym_obj.get("stream", []))
        return bars, f"{bars:,} bars", list(parsed.keys())

    if filename.startswith("dc_") and filename != "dc_meta.json" and isinstance(parsed, dict):
        bars = len(parsed.get("bars", [])) or len(parsed.get("candles", []))
        if bars:
            return bars, f"{bars:,} bars", list(parsed.keys())[:10]

    if isinstance(parsed, list):
        n = len(parsed)
        sample_keys = list(parsed[0].keys())[:10] if n > 0 and isinstance(parsed[0], dict) else []
        unit = "papers" if filename == "papers_database.json" else "rows"
        return n, f"{n:,} {unit}", sample_keys

    if isinstance(parsed, dict):
        # Special composite dictionaries
        if filename == "supabase_v2_backup_latest.json":
            runs = len(parsed.get("supabase_recent_runs") or [])
            v2_tbl = parsed.get("v2_tables") or {}
            v2_rows = sum(len(v) for v in v2_tbl.values() if isinstance(v, list))
            total = runs + v2_rows
            return total, f"{total:,} rows", list(parsed.keys())

        if filename == "live_status.json":
            bots = len(parsed.get("bots_fleet") or [])
            deals = len(parsed.get("recent_closed_deals") or [])
            trades = len(parsed.get("recent_trades") or [])
            total = bots + deals + trades
            return total, f"{total:,} records", list(parsed.keys())[:12]

        if filename == "strategy_registry.json" and isinstance(parsed.get("strategies"), dict):
            n = len(parsed["strategies"])
            return n, f"{n:,} strategies", list(parsed.keys())

        if filename == "champion_registry.json" and isinstance(parsed.get("results"), dict):
            n = len(parsed["results"])
            return n, f"{n:,} symbols", list(parsed.keys())

        if filename == "autonomous_champions.json" and isinstance(parsed.get("champions"), dict):
            n = len(parsed["champions"])
            return n, f"{n:,} champions", list(parsed.keys())

        if filename == "watchdog_status.json" and isinstance(parsed.get("symbols"), dict):
            n = len(parsed["symbols"])
            return n, f"{n:,} feeds", list(parsed.keys())

        if filename == "calibrated_costs.json" and isinstance(parsed.get("symbols"), dict):
            n = len(parsed["symbols"])
            return n, f"{n:,} symbols", list(parsed.keys())

        if filename == "archive_historical_cycles_v1.json":
            orig = parsed.get("original_state") or {}
            n = len(orig.get("cycles") or [])
            return n, f"{n:,} cycles", list(parsed.keys())

        if filename == "exhaustive_13_engines_optimization.json":
            n = sum(len(v) for v in parsed.values() if isinstance(v, (list, dict)))
            return n, f"{n:,} configs", list(parsed.keys())

        if filename == "benchmark_13_engines_results.json":
            n = sum(len(v) for v in parsed.values() if isinstance(v, (list, dict)))
            return n, f"{n:,} rows", list(parsed.keys())

        if filename == "live_market_intelligence.json" and isinstance(parsed.get("assets"), dict):
            n = len(parsed["assets"])
            return n, f"{n:,} assets", list(parsed.keys())

        if filename == "live_evolution_champions.json" and isinstance(parsed.get("champions"), dict):
            n = len(parsed["champions"])
            return n, f"{n:,} champions", list(parsed.keys())

        if filename == "rule_classification_matrix.json":
            n = sum(
                len(parsed.get(k) or {})
                for k in ("tier_1_immutable_hard_constraints", "tier_2_adaptive_rules", "tier_3_open_research_hypotheses")
                if isinstance(parsed.get(k), (list, dict))
            )
            return n, f"{n:,} tiers", list(parsed.keys())

        if filename == "strategy_evolution.json":
            vault = parsed.get("vault") or {}
            gens = parsed.get("generations") or {}
            n = (len(vault) if isinstance(vault, (list, dict)) else 0) + (len(gens) if isinstance(gens, (list, dict)) else 0)
            return n, f"{n:,} items", list(parsed.keys())

        if filename == "autonomous_validation.json":
            tests = [k for k in parsed.keys() if k.startswith("real_")]
            return len(tests), f"{len(tests)} audits", list(parsed.keys())

        if filename == "truth_guard.json":
            metrics = parsed.get("metrics_empirical") or {}
            n = len(metrics) if isinstance(metrics, dict) else len(parsed)
            return n, f"{n} metrics", list(parsed.keys())

        if filename == "daystudy-XAUUSD.json" and isinstance(parsed.get("rows"), list):
            n = len(parsed["rows"])
            return n, f"{n:,} days", list(parsed.keys())[:10]

        # Generic dict: pick primary largest list if significant, else top key count
        best_list_len = 0
        for v in parsed.values():
            if isinstance(v, list) and len(v) > best_list_len:
                best_list_len = len(v)
        if best_list_len > 0:
            return best_list_len, f"{best_list_len:,} rows", list(parsed.keys())[:12]
        n = len(parsed)
        return n, f"{n:,} keys", list(parsed.keys())[:12]

    return 1, "1 value", []


def main() -> None:
    if not DATA_DIR.exists():
        raise SystemExit(f"Missing data directory: {DATA_DIR}")

    datasets: list[dict[str, Any]] = []
    files = sorted(DATA_DIR.iterdir(), key=lambda x: x.name.lower())

    for f in files:
        if not f.is_file():
            continue
        ext = f.suffix.lower()
        if ext not in (".json", ".md"):
            continue

        raw_bytes = f.read_bytes()
        size_bytes = len(raw_bytes)
        sha_short = hashlib.sha256(raw_bytes).hexdigest()[:12]
        mtime = f.stat().st_mtime

        if ext == ".json":
            try:
                parsed = json.loads(raw_bytes.decode("utf-8"))
                valid_json = True
            except Exception:
                parsed = None
                valid_json = False

            record_count, row_label, top_keys = infer_record_stats(f.name, parsed)
            updated_at = extract_timestamp(parsed, mtime)
            root_type = "array" if isinstance(parsed, list) else "object" if isinstance(parsed, dict) else type(parsed).__name__

            if f.name in CORE_FOLDER_MAP:
                folder_id, schema_name, desc = CORE_FOLDER_MAP[f.name]
                is_core = True
            else:
                folder_id = "generated_caches"
                schema_name, desc = SECONDARY_DESCRIPTIONS.get(
                    f.name, ("workspace_json_v1", f"Workspace JSON artifact ({f.name})")
                )
                is_core = False

            datasets.append({
                "id": f.name,
                "filename": f.name,
                "path": f"data/{f.name}",
                "format": "JSON",
                "folder_id": folder_id,
                "is_core": is_core,
                "schema_name": schema_name,
                "description": desc,
                "size_bytes": size_bytes,
                "size_label": format_size(size_bytes),
                "record_count": record_count,
                "row_label": row_label,
                "root_type": root_type,
                "top_keys": top_keys,
                "valid": valid_json,
                "sha256_short": sha_short,
                "updated_at": updated_at,
            })
        elif ext == ".md":
            text = raw_bytes.decode("utf-8", errors="ignore")
            lines = text.splitlines()
            schema_name, desc = SECONDARY_DESCRIPTIONS.get(
                f.name, ("markdown_report", f"Quant research report ({f.name})")
            )
            datasets.append({
                "id": f.name,
                "filename": f.name,
                "path": f"data/{f.name}",
                "format": "MD",
                "folder_id": "generated_caches",
                "is_core": False,
                "schema_name": schema_name,
                "description": desc,
                "size_bytes": size_bytes,
                "size_label": format_size(size_bytes),
                "record_count": len(lines),
                "row_label": f"{len(lines):,} lines",
                "root_type": "markdown",
                "top_keys": [],
                "valid": True,
                "sha256_short": sha_short,
                "updated_at": datetime.fromtimestamp(mtime, tz=timezone.utc).isoformat(),
            })

    # Order folders strictly as specified; put optional generated caches folder at the end
    all_folders = list(FOLDER_SPECS) + [
        {
            "id": "generated_caches",
            "name": "Generated Caches & Reports",
            "icon": "cache",
            "dot": "blue",
            "description": "Pre-compiled summary caches for Pages 1–7 and Markdown benchmark reports",
        }
    ]

    core_datasets = [d for d in datasets if d["is_core"]]
    core_bytes = sum(d["size_bytes"] for d in core_datasets)
    total_bytes = sum(d["size_bytes"] for d in datasets)

    payload = {
        "catalog_version": "V4.0-UNIFIED-DATABASE",
        "generated_at_utc": datetime.now(tz=timezone.utc).isoformat(),
        "default_file": "backtest_data.json",
        "counts": {
            "core_datasets": len(core_datasets),
            "total_files": len(datasets),
            "core_total_bytes": core_bytes,
            "core_total_label": format_size(core_bytes),
            "all_total_bytes": total_bytes,
            "all_total_label": format_size(total_bytes),
        },
        "folders": all_folders,
        "datasets": datasets,
    }

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {OUT_PATH} ({len(core_datasets)} core datasets, {len(datasets)} total files, {OUT_PATH.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
