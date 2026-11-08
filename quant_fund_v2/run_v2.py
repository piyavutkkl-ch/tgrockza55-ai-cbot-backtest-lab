"""
CLI Orchestrator for Antigravity Quant Fund V2 (10-Node Pipeline).

Usage:
  1. Run Research -> Backtest -> Gatekeeper -> CEO Briefing (pauses before Paper Trading):
     python -m quant_fund_v2.run_v2 --symbol XAUUSD

  2. Human Stage 1 Approval -> Deploy ONLY to Paper Trading / Forward Test:
     python -m quant_fund_v2.run_v2 --symbol XAUUSD --approve-paper

  3. Human Stage 2 Approval -> Promote Paper Strategy to Live Trading & Persist Strategy Memory:
     python -m quant_fund_v2.run_v2 --symbol XAUUSD --approve-paper --approve-live
"""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from quant_fund_v2 import MODEL_ARGON_PRO, MODEL_FLASH_WORKER, POLICY_VERSION
from quant_fund_v2.db.memory_store import StrategyMemoryStore
from quant_fund_v2.graph import build_quant_fund_v2_graph
from quant_fund_v2.state import AdminRiskPolicy, FundStateV2


def build_initial_state(symbol: str = "XAUUSD") -> FundStateV2:
    """Create initial deterministic state for the 10-node Quant Fund V2 workflow."""
    admin_policy = AdminRiskPolicy()
    return {
        "symbol": symbol,
        "admin_risk_policy": admin_policy.model_dump(),
        "circuit_breaker_tripped": False,
        "circuit_breaker_reason": "",
        "tokens_used_today": 0,
        "estimated_cost_usd_today": 0.0,
        "iteration": 0,
        "dropped_hypotheses": [],
        "active_hypothesis_id": "",
        "data_quality_report": {},
        "market_research_proposals": [],
        "ceo_policy": {},
        "worker_build": {},
        "math_backtest_report": {},
        "validation_stats_report": {},
        "validation_checklist": {},
        "validation_history": [],
        "executive_briefing": {},
        "briefing_md_path": "",
        "paper_trading_approved": False,
        "paper_deployment_report": {},
        "live_trading_approved": False,
        "live_deployment_report": {},
        "strategy_memory_record": {},
    }


def export_dashboard_telemetry(final_state: Dict[str, Any]) -> Path:
    """Export V2 workflow state to JSON for dashboard inspection."""
    out_path = Path(r"d:\cbot-atgvt\docs\data\quant_fund_v2_status.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    bt = final_state.get("math_backtest_report") or {}
    payload = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "symbol": final_state.get("symbol"),
        "policy_version": POLICY_VERSION,
        "models": {
            "ceo_and_auditor": MODEL_ARGON_PRO,
            "research_and_worker": MODEL_FLASH_WORKER,
        },
        "data_quality_report": final_state.get("data_quality_report"),
        "ceo_policy": final_state.get("ceo_policy"),
        "iteration": final_state.get("iteration"),
        "dropped_hypotheses": final_state.get("dropped_hypotheses"),
        "worker_build": {
            k: v
            for k, v in (final_state.get("worker_build") or {}).items()
            if k != "compile_output"
        },
        "full_period_metrics": bt.get("full_period_metrics"),
        "in_sample_metrics": bt.get("in_sample_metrics"),
        "validation_metrics": bt.get("validation_metrics"),
        "out_of_sample_metrics": bt.get("out_of_sample_metrics"),
        "validation_stats_report": final_state.get("validation_stats_report"),
        "validation_checklist": final_state.get("validation_checklist"),
        "validation_history": final_state.get("validation_history"),
        "executive_briefing": final_state.get("executive_briefing"),
        "paper_trading_approved": final_state.get("paper_trading_approved"),
        "paper_deployment_report": final_state.get("paper_deployment_report"),
        "live_trading_approved": final_state.get("live_trading_approved"),
        "live_deployment_report": final_state.get("live_deployment_report"),
        "strategy_memory_record": final_state.get("strategy_memory_record"),
        "tokens_used_today": final_state.get("tokens_used_today"),
        "estimated_cost_usd_today": final_state.get("estimated_cost_usd_today"),
    }
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Antigravity Quant Fund V2 Orchestrator")
    parser.add_argument("--symbol", default="XAUUSD", help="Target trading symbol")
    parser.add_argument(
        "--approve-paper",
        action="store_true",
        help="Human Stage 1 Approval: Deploy strategy ONLY to Paper Trading / Forward Test VM",
    )
    parser.add_argument(
        "--approve-live",
        action="store_true",
        help="Human Stage 2 Approval: Promote Paper Trading strategy to Live cTrader execution",
    )
    parser.add_argument(
        "--thread-id",
        default="quant-fund-v2-main",
        help="LangGraph thread ID for checkpoint persistence",
    )
    parser.add_argument(
        "--backup-local",
        action="store_true",
        help="Export an on-demand local backup (.json.gz) of Supabase PostgreSQL & V2 Strategy Memory",
    )
    args = parser.parse_args()

    store = StrategyMemoryStore()
    if args.backup_local:
        bkp = store.export_local_backup()
        print("=" * 84)
        print("[LOCAL BACKUP COMPLETED] Supabase PostgreSQL + V2 Strategy Memory Snapshot:")
        print(f"  -> Compressed Archive : {bkp['backup_file_gz']}")
        print(f"  -> Web Download Mirror: {bkp['web_download_json']}")
        print(f"  -> Supabase Runs      : {bkp['supabase_runs_included']} | V2 Versions: {bkp['v2_versions_included']}")
        print("=" * 84)
        return

    print("=" * 84)
    print("ANTIGRAVITY QUANT FUND V2 — BUILD (AI) -> PROVE (MATH) -> PROTECT (RULES)")
    print(f"Models: CEO/Audit={MODEL_ARGON_PRO} | Research/Worker={MODEL_FLASH_WORKER}")
    print(f"Symbol: {args.symbol} | Policy: {POLICY_VERSION}")
    print("=" * 84)

    app = build_quant_fund_v2_graph(enable_interrupts=True)
    config = {"configurable": {"thread_id": args.thread_id}}

    init_state = build_initial_state(symbol=args.symbol)

    for _ in app.stream(init_state, config=config):
        pass

    snapshot = app.get_state(config)
    current_state = snapshot.values

    if snapshot.next and "node_09a_deploy_paper_trading" in snapshot.next:
        print("\n" + "!" * 84)
        print("[STAGE 8A: HUMAN-IN-THE-LOOP GATE — PAPER TRADING APPROVAL REQUIRED]")
        print("Pipeline is PAUSED before `node_09a_deploy_paper_trading`.")
        print("Stage 1 approval deploys ONLY to Headless Cloud VM Paper Trading (DEMO).")
        print(f"Executive Briefing: {current_state.get('briefing_md_path')}")
        print("!" * 84)

        if args.approve_paper:
            print("\n>>> [HUMAN STAGE 1] Operator granted `--approve-paper`. Resuming to Paper Trading Deployment...")
            app.update_state(config, {"paper_trading_approved": True})
            for _ in app.stream(None, config=config):
                pass

            snapshot = app.get_state(config)
            current_state = snapshot.values

            if snapshot.next and "node_09b_deploy_live_trading" in snapshot.next:
                print("\n" + "!" * 84)
                print("[STAGE 8B: HUMAN-IN-THE-LOOP GATE — LIVE PRODUCTION APPROVAL REQUIRED]")
                print("Paper Trading & Forward Execution Watchdog are HEALTHY.")
                print("Pipeline is PAUSED before `node_09b_deploy_live_trading`.")
                print("!" * 84)

                if args.approve_live:
                    print("\n>>> [HUMAN STAGE 2] Operator granted `--approve-live`. Resuming to Live Production & Strategy Memory...")
                    app.update_state(config, {"live_trading_approved": True})
                    for _ in app.stream(None, config=config):
                        pass
                    snapshot = app.get_state(config)
                    current_state = snapshot.values
                else:
                    print("\nTo promote Paper Trading strategy to Live Production, run:")
                    print(f"  python -m quant_fund_v2.run_v2 --symbol {args.symbol} --approve-paper --approve-live")
        else:
            print("\nTo approve Stage 1 Paper Trading deployment, run:")
            print(f"  python -m quant_fund_v2.run_v2 --symbol {args.symbol} --approve-paper")

    telemetry_path = export_dashboard_telemetry(current_state)
    bkp_info = store.export_local_backup()
    print(f"\n[TELEMETRY] Saved V2 status JSON -> {telemetry_path}")
    print(f"[BACKUP SNAPSHOT] Updated Web & Local Backup -> {bkp_info['backup_file_gz']}")


if __name__ == "__main__":
    main()
