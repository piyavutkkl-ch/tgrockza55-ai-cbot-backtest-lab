"""
Pydantic Schemas & LangGraph State Definitions for the Multi-Agent Quant Fund.
"""

from typing import Any, Dict, List, Literal, Optional, TypedDict
from pydantic import BaseModel, Field


class CEOStrategyDirective(BaseModel):
    hypothesis_id: str = Field(description="ID of the selected research paper/strategy from strategies_database.json")
    paper_title: str = Field(description="Title and arXiv ID of the research paper")
    strategy_code: str = Field(description="Unique uppercase strategy code for StrategyBase.Code, e.g. QUANT_FUND_ALPHA")
    strategy_class_name: str = Field(description="Valid C# class name for the strategy, e.g. QuantFundAlpha")
    target_symbol: str = Field(description="Target trading instrument, e.g. XAUUSD, BTCUSD, ETHUSD")
    market_regime_analysis: str = Field(description="Synthesis of current live DOM/Order Flow and macro volatility regime")
    entry_logic_spec: str = Field(description="Exact mathematical entry conditions for the Worker to implement")
    exit_logic_spec: str = Field(description="Exact exit rules including structural Stop Loss, Take Profit, and time limit")
    recommended_params: Dict[str, float] = Field(description="Initial parameter dictionary (sd_thresh, sl_atr_mult, rr_ratio, max_hold, use_trend_filter)")
    max_drawdown_limit_pct: float = Field(description="Maximum allowed drawdown percentage on a $100 base portfolio")
    min_profit_factor: float = Field(description="Minimum required Profit Factor net of spread and commission")
    rationale: str = Field(description="Why this hypothesis fits the current microstructure regime")


class WorkerBuildResult(BaseModel):
    iteration: int = Field(description="Current worker iteration number")
    strategy_code: str = Field(description="Strategy code implemented")
    csharp_file_path: str = Field(description="Absolute path to the generated C# strategy file")
    compile_success: bool = Field(description="Whether dotnet build succeeded with 0 errors")
    compile_output: str = Field(description="Compiler output log from dotnet build")
    backtest_metrics: Dict[str, Any] = Field(description="Full backtest metrics dictionary from run_local_backtest")
    worker_log_summary: str = Field(description="Worker summary of implementation, parameter tuning, and backtest results")
    changes_made: List[str] = Field(description="List of specific code and parameter changes made in this iteration")


class RiskAuditDecision(BaseModel):
    verdict: Literal["PASS", "VETO"] = Field(description="PASS if all risk & code gates succeed, VETO to reject back to Worker")
    risk_score: int = Field(description="Risk safety score from 0 to 100 (100 = safest, >= 75 required to PASS)")
    passed_hard_sl_check: bool = Field(description="True if C# code enforces an explicit StopDistance / Stop Loss and no martingale")
    passed_no_lookahead_check: bool = Field(description="True if C# code uses closed bars (.Last(1)) without future data leakage")
    passed_drawdown_check: bool = Field(description="True if Max Drawdown is within the CEO limit")
    passed_profit_factor_check: bool = Field(description="True if Net Profit Factor >= min_profit_factor after commission & spread")
    passed_multi_regime_check: bool = Field(description="True if strategy is profitable across multiple years/regimes, not a single lucky window")
    veto_reasons: List[str] = Field(description="Reasons for VETO if rejected (empty if PASS)")
    remediation_instructions: str = Field(description="Specific technical instructions for the Worker to fix the strategy on the next loop")


class CEOExecutiveBriefing(BaseModel):
    final_decision: Literal["APPROVE_FOR_HITL", "PIVOT_STRATEGY"] = Field(description="CEO final decision after Risk Manager PASS")
    headline: str = Field(description="One-line executive headline")
    executive_summary: str = Field(description="Comprehensive executive summary for the human portfolio manager")
    key_strengths: List[str] = Field(description="Key quantitative and microstructural strengths verified")
    residual_risks: List[str] = Field(description="Residual live execution risks the human operator should monitor")
    recommended_lot_size: float = Field(description="Recommended initial lot size for live/demo deployment (e.g. 0.01)")
    deployment_target: str = Field(description="Target environment after human approval")


class FundState(TypedDict, total=False):
    symbol: str
    iteration: int
    max_iterations: int
    pivot_count: int
    market_context: Dict[str, Any]
    research_candidates: List[Dict[str, Any]]
    ceo_directive: Dict[str, Any]
    worker_result: Dict[str, Any]
    risk_audit: Dict[str, Any]
    ceo_briefing: Dict[str, Any]
    audit_history: List[Dict[str, Any]]
    briefing_markdown_path: str
    status_json_path: str
    human_approved: bool
    deployment_result: Dict[str, Any]
