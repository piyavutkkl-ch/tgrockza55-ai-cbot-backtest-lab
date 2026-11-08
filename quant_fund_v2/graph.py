"""
LangGraph V2 10-Node StateGraph Orchestrator.
Enforces:
  1. Fail-Closed Data Quality Gate (Node 1)
  2. Token/Cost Circuit Breaker checks
  3. Max 3 Worker Iterations per Hypothesis (if exceeded -> Drop Hypothesis & route to CEO)
  4. Boolean Checklist Validation (Node 6 — zero LLM math)
  5. Dual-Stage Human-in-the-Loop Interrupts:
     - Stage 1 Interrupt before `node_09a_deploy_paper_trading` (Paper Trading / Headless Cloud VM ONLY)
     - Stage 2 Interrupt before `node_09b_deploy_live_trading` (Requires healthy Paper Forward Test + 2nd Human Approval)
  6. Strategy Memory Persistence (Node 10)
"""

from typing import Literal
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from .nodes import (
    node_01_data_quality_gate,
    node_02_market_research_team,
    node_03_ceo_strategist,
    node_04_quant_worker,
    node_05_backtest_math_engine,
    node_06_validation_and_gatekeeper,
    node_07_ceo_final_review,
    node_09a_deploy_paper_trading,
    node_09b_deploy_live_trading,
    node_10_strategy_memory_db,
)
from .state import FundStateV2


def route_after_node_01(
    state: FundStateV2,
) -> Literal["node_02_market_research_team", "__end__"]:
    if not state.get("data_quality_report", {}).get("passed", False):
        return "__end__"
    return "node_02_market_research_team"


def route_after_circuit_breaker(
    next_node_name: str,
):
    def _router(state: FundStateV2):
        if state.get("circuit_breaker_tripped", False):
            return "__end__"
        return next_node_name

    return _router


def route_after_node_06_gatekeeper(
    state: FundStateV2,
) -> Literal[
    "node_07_ceo_final_review",
    "node_04_quant_worker",
    "node_03_ceo_strategist",
    "node_10_strategy_memory_db",
]:
    if state.get("circuit_breaker_tripped", False):
        return "node_10_strategy_memory_db"

    chk = state.get("validation_checklist", {})
    if chk.get("overall_passed", False):
        return "node_07_ceo_final_review"

    max_iters = int(state.get("admin_risk_policy", {}).get("max_worker_iterations", 3))
    iteration = int(state.get("iteration", 1))

    if iteration < max_iters:
        return "node_04_quant_worker"
    else:
        # Exceeded 3 iterations -> Hypothesis was added to `dropped_hypotheses`; pivot back to CEO!
        return "node_03_ceo_strategist"


def route_after_paper_deployment(
    state: FundStateV2,
) -> Literal["node_09b_deploy_live_trading", "node_10_strategy_memory_db"]:
    paper_rep = state.get("paper_deployment_report", {})
    health = paper_rep.get("forward_monitoring_health", {})
    if not health.get("healthy", False):
        return "node_10_strategy_memory_db"
    return "node_09b_deploy_live_trading"


def build_quant_fund_v2_graph(checkpointer=None, enable_interrupts: bool = True):
    builder = StateGraph(FundStateV2)

    builder.add_node("node_01_data_quality_gate", node_01_data_quality_gate)
    builder.add_node("node_02_market_research_team", node_02_market_research_team)
    builder.add_node("node_03_ceo_strategist", node_03_ceo_strategist)
    builder.add_node("node_04_quant_worker", node_04_quant_worker)
    builder.add_node("node_05_backtest_math_engine", node_05_backtest_math_engine)
    builder.add_node("node_06_validation_and_gatekeeper", node_06_validation_and_gatekeeper)
    builder.add_node("node_07_ceo_final_review", node_07_ceo_final_review)
    builder.add_node("node_09a_deploy_paper_trading", node_09a_deploy_paper_trading)
    builder.add_node("node_09b_deploy_live_trading", node_09b_deploy_live_trading)
    builder.add_node("node_10_strategy_memory_db", node_10_strategy_memory_db)

    builder.add_edge(START, "node_01_data_quality_gate")
    builder.add_conditional_edges(
        "node_01_data_quality_gate",
        route_after_node_01,
        {
            "node_02_market_research_team": "node_02_market_research_team",
            "__end__": END,
        },
    )

    builder.add_conditional_edges(
        "node_02_market_research_team",
        route_after_circuit_breaker("node_03_ceo_strategist"),
        {
            "node_03_ceo_strategist": "node_03_ceo_strategist",
            "__end__": END,
        },
    )

    builder.add_conditional_edges(
        "node_03_ceo_strategist",
        route_after_circuit_breaker("node_04_quant_worker"),
        {
            "node_04_quant_worker": "node_04_quant_worker",
            "__end__": END,
        },
    )

    builder.add_conditional_edges(
        "node_04_quant_worker",
        route_after_circuit_breaker("node_05_backtest_math_engine"),
        {
            "node_05_backtest_math_engine": "node_05_backtest_math_engine",
            "__end__": END,
        },
    )

    builder.add_edge("node_05_backtest_math_engine", "node_06_validation_and_gatekeeper")

    builder.add_conditional_edges(
        "node_06_validation_and_gatekeeper",
        route_after_node_06_gatekeeper,
        {
            "node_07_ceo_final_review": "node_07_ceo_final_review",
            "node_04_quant_worker": "node_04_quant_worker",
            "node_03_ceo_strategist": "node_03_ceo_strategist",
            "node_10_strategy_memory_db": "node_10_strategy_memory_db",
        },
    )

    builder.add_edge("node_07_ceo_final_review", "node_09a_deploy_paper_trading")

    builder.add_conditional_edges(
        "node_09a_deploy_paper_trading",
        route_after_paper_deployment,
        {
            "node_09b_deploy_live_trading": "node_09b_deploy_live_trading",
            "node_10_strategy_memory_db": "node_10_strategy_memory_db",
        },
    )

    builder.add_edge("node_09b_deploy_live_trading", "node_10_strategy_memory_db")
    builder.add_edge("node_10_strategy_memory_db", END)

    if checkpointer is None:
        checkpointer = MemorySaver()

    interrupt_nodes = (
        ["node_09a_deploy_paper_trading", "node_09b_deploy_live_trading"]
        if enable_interrupts
        else []
    )
    return builder.compile(
        checkpointer=checkpointer,
        interrupt_before=interrupt_nodes,
    )
