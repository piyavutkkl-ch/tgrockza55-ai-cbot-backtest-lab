"""
CLI Runner & Human-in-the-Loop (HITL) Controller for the Multi-Agent Quant Fund.
Usage:
  1. Run workflow up to HITL Approval Gate:
       python -m quant_fund.run_fund --symbol XAUUSD
  2. Approve and trigger production deployment (simulating HITL confirmation):
       python -m quant_fund.run_fund --symbol XAUUSD --approve
"""

import argparse
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

from . import MODEL_CEO, MODEL_RISK_MANAGER, MODEL_WORKER
from .graph import build_quant_fund_graph
from .tools import REPORTS_DIR


def main():
    parser = argparse.ArgumentParser(description="Multi-Agent Quant Fund Orchestrator (LangGraph)")
    parser.add_argument("--symbol", default="XAUUSD", help="Target trading symbol (default: XAUUSD)")
    parser.add_argument("--max-iterations", type=int, default=3, help="Max Worker/Risk Manager loop iterations")
    parser.add_argument("--thread-id", default="quant-fund-session-001", help="LangGraph checkpoint thread ID")
    parser.add_argument(
        "--approve",
        action="store_true",
        help="Approve the pending HITL gate and resume graph execution into deploy_to_cloud",
    )
    args = parser.parse_args()

    print("=" * 88)
    print(" 🏛️  ANTIGRAVITY MULTI-AGENT QUANT FUND (LangGraph + Google GenAI SDK)")
    print("=" * 88)
    print(f" • CEO Strategist Model  : {MODEL_CEO}")
    print(f" • Quant Worker Model    : {MODEL_WORKER}")
    print(f" • Risk Manager Model    : {MODEL_RISK_MANAGER}")
    print(f" • Target Instrument     : {args.symbol}")
    print(f" • HITL Safety Lock      : interrupt_before=['deploy_to_cloud']")
    print("=" * 88)

    graph = build_quant_fund_graph()
    config = {"configurable": {"thread_id": args.thread_id}}

    initial_state = {
        "symbol": args.symbol,
        "iteration": 0,
        "max_iterations": args.max_iterations,
        "pivot_count": 0,
        "audit_history": [],
        "human_approved": False,
    }

    # Execute graph until it hits the HITL interrupt before `deploy_to_cloud`
    for _ in graph.stream(initial_state, config=config, stream_mode="values"):
        pass

    snapshot = graph.get_state(config)
    next_nodes = snapshot.next

    print("\n" + "=" * 88)
    if "deploy_to_cloud" in next_nodes:
        print(" 🛑 HUMAN-IN-THE-LOOP (HITL) SAFETY GATE ENGAGED")
        print("=" * 88)
        print(" • Next Scheduled Node   : `deploy_to_cloud` (BLOCKED awaiting Human Approval)")
        print(f" • Executive Briefing    : {snapshot.values.get('briefing_markdown_path')}")
        print(f" • Dashboard JSON        : {snapshot.values.get('status_json_path')}")
        print("-" * 88)

        if args.approve:
            print(" ✅ `--approve` flag detected! Resuming LangGraph workflow past HITL gate...")
            for _ in graph.stream(None, config=config, stream_mode="values"):
                pass
            final_snap = graph.get_state(config)
            print(" 🚀 Deployment Result:", json.dumps(final_snap.values.get("deployment_result"), indent=2))
        else:
            print(" 💡 System is safely paused. Review the Executive Briefing before approving to production.")
    else:
        print(f" Workflow finished at state: {next_nodes}")
    print("=" * 88)


if __name__ == "__main__":
    main()
