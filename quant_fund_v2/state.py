"""
State & Node Schemas for Antigravity Trading Platform (V2).
"""

from typing import Any, Dict, List, Literal, Optional, TypedDict
from pydantic import BaseModel, Field


class AdminRiskPolicy(BaseModel):
    """Immutable Hard Risk Limits set by System Admin. AI cannot override these."""
    policy_version: str = "RISK-POL-V2.0"
    hard_max_dd_pct: float = 18.0
    hard_max_risk_per_trade_pct: float = 2.0
    hard_min_profit_factor: float = 1.15
    hard_min_oos_pf: float = 1.03
    hard_min_wf_efficiency_pct: float = 60.0
    hard_max_mc_ruin_prob_pct: float = 1.0
    hard_max_mc_95_dd_pct: float = 22.0
    max_worker_iterations: int = 3
    daily_token_limit: int = 500000
    daily_cost_limit_usd: float = 5.00


class CandidateHypothesis(BaseModel):
    hypothesis_id: str
    paper_id: str
    title: str
    strategy_code: str
    csharp_class_name: str
    entry_logic: str
    exit_logic: str
    recommended_params: Dict[str, Any]
    microstructure_thesis: str


class CEOPolicyDecision(BaseModel):
    selected_hypothesis_id: str
    strategy_code: str
    csharp_class_name: str
    symbol: str
    policy_rationale: str
    proposed_risk_per_trade_pct: float = Field(description="Must be <= Admin hard_max_risk_per_trade_pct")
    proposed_max_dd_pct: float = Field(description="Must be <= Admin hard_max_dd_pct")
    proposed_min_pf: float = Field(description="Must be >= Admin hard_min_profit_factor")
    strategy_params: Dict[str, Any]


class ValidationChecklistResult(BaseModel):
    """Boolean Checklist Validation (Replaces legacy 100/100 score). Fail-Closed."""
    has_hard_stop_loss: bool = False
    risk_per_trade_within_limit: bool = False
    max_dd_within_limit: bool = False
    pf_above_minimum: bool = False
    oos_profitable: bool = False
    walk_forward_passed: bool = False
    monte_carlo_passed: bool = False
    no_lookahead_bias_verified: bool = False
    ai_security_audit_passed: bool = False
    overall_passed: bool = False
    veto_reasons: List[str] = Field(default_factory=list)
    remediation_directives: List[str] = Field(default_factory=list)


class FundStateV2(TypedDict, total=False):
    # Global Metadata & Governance
    symbol: str
    admin_risk_policy: Dict[str, Any]
    circuit_breaker_tripped: bool
    circuit_breaker_reason: str
    tokens_used_today: int
    estimated_cost_usd_today: float

    # Iteration & Hypothesis Control
    iteration: int
    dropped_hypotheses: List[str]
    active_hypothesis_id: str

    # Node 1: Data Quality Gate
    data_quality_report: Dict[str, Any]

    # Node 2: Market Research Team (Flash)
    market_research_proposals: List[Dict[str, Any]]

    # Node 3: CEO Strategist (Argon)
    ceo_policy: Dict[str, Any]

    # Node 4: Quant Worker (Flash)
    worker_build: Dict[str, Any]

    # Node 5: Backtest & Performance Engine (Python Math)
    math_backtest_report: Dict[str, Any]

    # Node 6: Strategy Validation & Gatekeeper (Python Stats + Hard Rules + AI Security Audit)
    validation_stats_report: Dict[str, Any]
    validation_checklist: Dict[str, Any]
    validation_history: List[Dict[str, Any]]

    # Node 7: CEO Final Review (Argon)
    executive_briefing: Dict[str, Any]
    briefing_md_path: str

    # Node 8 & 9: Dual-Stage HITL & Deployment
    paper_trading_approved: bool
    paper_deployment_report: Dict[str, Any]
    live_trading_approved: bool
    live_deployment_report: Dict[str, Any]

    # Node 10: Version & Strategy Memory (PostgreSQL / SQLite Mirror)
    strategy_memory_record: Dict[str, Any]
