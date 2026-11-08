"""
LangGraph StateGraph Workflow for the Multi-Agent Quant Fund.
Enforces strict directed graph routing:
  START ➔ CEO Strategist ➔ Quant Worker ➔ Risk Manager
    ├─ (VETO & iteration < max_iterations) ➔ Quant Worker (Fix Code/Params)
    ├─ (VETO & iteration >= max_iterations) ➔ CEO Strategist (Pivot Hypothesis)
    └─ (PASS) ➔ CEO Final Review ➔ [HITL Interrupt Gate] ➔ Deploy to Cloud ➔ END
"""

from typing import Literal
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from .agents import (
    ceo_final_review_node,
    ceo_strategist_node,
    deploy_to_cloud_node,
    quant_worker_node,
    risk_manager_node,
)
from .schemas import FundState


def route_after_risk_manager(
    state: FundState,
) -> Literal["quant_worker", "ceo_strategist", "ceo_final_review"]:
    audit = state.get("risk_audit", {})
    verdict = audit.get("verdict", "VETO")
    iteration = state.get("iteration", 1)
    max_iterations = state.get("max_iterations", 3)

    if verdict == "PASS":
        return "ceo_final_review"
    elif iteration < max_iterations:
        return "quant_worker"
    else:
        return "ceo_strategist"


def route_after_ceo_review(
    state: FundState,
) -> Literal["deploy_to_cloud", "ceo_strategist"]:
    briefing = state.get("ceo_briefing", {})
    if briefing.get("final_decision") == "APPROVE_FOR_HITL":
        return "deploy_to_cloud"
    return "ceo_strategist"


def build_quant_fund_graph(checkpointer=None):
    """
    Compiles the Multi-Agent Quant Fund StateGraph with a Human-in-the-Loop (HITL)
    interrupt gate immediately before `deploy_to_cloud`.
    """
    builder = StateGraph(FundState)

    builder.add_node("ceo_strategist", ceo_strategist_node)
    builder.add_node("quant_worker", quant_worker_node)
    builder.add_node("risk_manager", risk_manager_node)
    builder.add_node("ceo_final_review", ceo_final_review_node)
    builder.add_node("deploy_to_cloud", deploy_to_cloud_node)

    builder.add_edge(START, "ceo_strategist")
    builder.add_edge("ceo_strategist", "quant_worker")
    builder.add_edge("quant_worker", "risk_manager")

    builder.add_conditional_edges(
        "risk_manager",
        route_after_risk_manager,
        {
            "quant_worker": "quant_worker",
            "ceo_strategist": "ceo_strategist",
            "ceo_final_review": "ceo_final_review",
        },
    )

    builder.add_conditional_edges(
        "ceo_final_review",
        route_after_ceo_review,
        {
            "deploy_to_cloud": "deploy_to_cloud",
            "ceo_strategist": "ceo_strategist",
        },
    )

    builder.add_edge("deploy_to_cloud", END)

    if checkpointer is None:
        checkpointer = MemorySaver()

    return builder.compile(
        checkpointer=checkpointer,
        interrupt_before=["deploy_to_cloud"],
    )
