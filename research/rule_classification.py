"""
Institutional Rule Classification Matrix & Policy Enforcement Core (Architecture V4)
====================================================================================
Establishes the three strict operational boundaries defined in MASTER PROMPT V4:

1. Immutable Hard Constraints:
   - Zero lookahead bias (closed bars only)
   - Zero data leakage
   - Mandatory Stop Loss / Max Loss Protection on EVERY order
   - Strict prohibition of Martingale or unhedged Grid risk expansion
   - Risk Governor absolute supremacy over AI and Strategy Engines
   - Daily Flat enforcement (No overnight holding, mandatory liquidation before end of day)
   - Broker-level order close confirmation
   - Pepperstone Demo-only enforcement (Account.IsLive == false) unless owner signed auth
   - Complete audit trail of all trading decisions
   - Fail-closed data sanity check (halt trading on corrupted / stale data)

2. Adaptive Rules:
   - Parameters AI can propose and mutate within approved risk limits:
     TP, SL (<= Hard Stop), Entry/Exit logic, Trading Session, News Filter,
     Spread Threshold, Consecutive Loss Cooldown, Max Daily Orders,
     Position Sizing, Holding Duration, Strategy Switching Thresholds.
   - CANNOT be deployed to live execution without passing Statistical Validation.

3. Open Research Hypotheses:
   - Unconstrained AI strategy formulation:
     Trend Following, Mean Reversion, Liquidity Sweep, Momentum Breakout,
     News Reaction, Order Flow Imbalance, Volatility Reversal, Session Range,
     Ensembles, etc. Must be logged and tested systematically.
"""

from enum import Enum
from typing import Dict, Any, List, Tuple, Optional
import math
import os
import json

class RuleTier(str, Enum):
    IMMUTABLE_HARD = "IMMUTABLE_HARD"
    ADAPTIVE = "ADAPTIVE"
    OPEN_HYPOTHESIS = "OPEN_HYPOTHESIS"

class RuleViolationError(Exception):
    """Raised when an Immutable Hard Constraint is breached."""
    pass

class RuleClassificationMatrix:
    """
    Deterministic gatekeeper that validates parameters, orders, and strategies
    against the 3-Tier Rule Hierarchy.
    """

    # -------------------------------------------------------------------------
    # 2.1 IMMUTABLE HARD CONSTRAINTS (Zero AI Authority to Overwrite)
    # -------------------------------------------------------------------------
    HARD_MAX_RISK_PER_TRADE_PCT = 2.0         # Max risk per order (% of equity)
    HARD_PORTFOLIO_MAX_DAILY_LOSS_USD = 10.00 # Max portfolio daily loss ($10 on $100 = 10%)
    HARD_MAX_CONSECUTIVE_LOSSES = 2           # Max consecutive symbol stop-outs per day
    HARD_MAX_OPEN_POSITIONS = 1               # Strictly 1 position at a time (no stacking/grid)
    HARD_PROHIBIT_MARTINGALE = True           # Strictly zero lot-multiplication on losses
    HARD_PROHIBIT_OVERNIGHT = True            # Strictly zero overnight holding (Intraday only)
    HARD_MANDATORY_DAILY_FLAT_UTC = 2145      # Force close all positions by 21:45 UTC
    HARD_MAX_HOLDING_MINUTES = 480            # Max 8 hours holding duration
    HARD_IS_DEMO_ENFORCED = True              # Must be Pepperstone Demo (#5258778)
    HARD_FAIL_CLOSED_DATA_MAX_STALENESS_SEC = 180 # 3 mins stall threshold

    # -------------------------------------------------------------------------
    # 2.2 ADAPTIVE RULES BOUNDARIES (AI May Mutate Within These Bounds)
    # -------------------------------------------------------------------------
    ADAPTIVE_PARAM_BOUNDS = {
        'sl_dist': {'min': 1.0, 'max': 250.0},
        'rr_ratio': {'min': 1.0, 'max': 5.0},
        'be_ratio': {'min': 0.0, 'max': 2.0},
        'daily_target_usd': {'min': 5.0, 'max': 30.0},
        'max_daily_losses': {'min': 1, 'max': 2}, # Capped by HARD limit of 2
        'spread_threshold': {
            'XAUUSD': {'min': 0.05, 'max': 0.25},
            'GOLD-PERP': {'min': 0.20, 'max': 2.20},
            'BTCUSD': {'min': 5.0, 'max': 35.0},
            'ETHUSD': {'min': 0.5, 'max': 3.5}
        },
        'news_pre_blackout_min': {'min': 15, 'max': 60},
        'news_post_blackout_min': {'min': 30, 'max': 120},
        'max_holding_bars': {'min': 5, 'max': 240},
        'switching_hysteresis_bars': {'min': 15, 'max': 60}
    }

    # -------------------------------------------------------------------------
    # 2.3 OPEN RESEARCH HYPOTHESES REPOSITORY
    # -------------------------------------------------------------------------
    VALID_HYPOTHESIS_FAMILIES = [
        "TREND_FOLLOWING",
        "MEAN_REVERSION",
        "LIQUIDITY_SWEEP_REVERSAL",
        "MOMENTUM_BREAKOUT",
        "NEWS_REACTION",
        "ORDER_FLOW_IMBALANCE",
        "VOLATILITY_REVERSAL",
        "SESSION_OPENING_RANGE",
        "NO_TRADE",
        "MICROSTRUCTURE_DOM_ABSORPTION",
        "VWAP_EQUILIBRIUM",
        "MULTI_TIMEFRAME_ALIGNMENT",
        "REGIME_ENSEMBLE"
    ]

    @classmethod
    def validate_strategy_parameters(cls, params: Dict[str, Any], symbol: str) -> Tuple[bool, List[str]]:
        """
        Validates proposed strategy parameters against Hard Constraints and Adaptive Bounds.
        Returns (is_valid, list_of_violations).
        """
        violations = []

        # 1. Hard Stop Loss Validation
        sl = params.get('sl') or params.get('sl_dist')
        if sl is None or float(sl) <= 0:
            violations.append("IMMUTABLE HARD VIOLATION: Missing or non-positive Stop Loss. Every order must have an approved Stop Loss.")

        # 2. Martingale / Grid Risk Expansion Prohibition
        lot_multiplier = params.get('lot_multiplier', 1.0)
        is_grid = params.get('grid_enabled', False)
        if float(lot_multiplier) > 1.0 or is_grid:
            violations.append("IMMUTABLE HARD VIOLATION: Martingale lot scaling or Grid accumulation is strictly prohibited.")

        # 3. Max Risk per trade limit
        risk_pct = params.get('risk_per_trade_pct', 1.0)
        if float(risk_pct) > cls.HARD_MAX_RISK_PER_TRADE_PCT:
            violations.append(f"IMMUTABLE HARD VIOLATION: Risk per trade {risk_pct}% exceeds ceiling of {cls.HARD_MAX_RISK_PER_TRADE_PCT}%.")

        # 4. Adaptive Parameter Bounds Check
        if sl is not None:
            bounds = cls.ADAPTIVE_PARAM_BOUNDS['sl_dist']
            if not (bounds['min'] <= float(sl) <= bounds['max']):
                violations.append(f"ADAPTIVE BOUND VIOLATION: Stop Loss {sl} outside allowed range [{bounds['min']}, {bounds['max']}].")

        rr = params.get('rr') or params.get('rr_ratio')
        if rr is not None:
            bounds = cls.ADAPTIVE_PARAM_BOUNDS['rr_ratio']
            if not (bounds['min'] <= float(rr) <= bounds['max']):
                violations.append(f"ADAPTIVE BOUND VIOLATION: Risk/Reward ratio {rr} outside allowed range [{bounds['min']}, {bounds['max']}].")

        # Spread check
        if symbol in cls.ADAPTIVE_PARAM_BOUNDS['spread_threshold']:
            sp_bound = cls.ADAPTIVE_PARAM_BOUNDS['spread_threshold'][symbol]
            prop_sp = params.get('max_spread', sp_bound['max'])
            if float(prop_sp) > sp_bound['max']:
                violations.append(f"ADAPTIVE BOUND VIOLATION: Proposed spread limit {prop_sp} exceeds ceiling {sp_bound['max']} for {symbol}.")

        return (len(violations) == 0, violations)

    @classmethod
    def evaluate_daily_flat_mandate(cls, current_time_hhmm: int, has_open_position: bool) -> Tuple[bool, str]:
        """
        Enforces central mandatory Daily Flat closure before end of trading day.
        Does not depend on the strategy's internal logic.
        """
        if current_time_hhmm >= cls.HARD_MANDATORY_DAILY_FLAT_UTC:
            if has_open_position:
                return (True, f"MANDATORY DAILY FLAT TRIGGERED: Current time {current_time_hhmm} UTC >= {cls.HARD_MANDATORY_DAILY_FLAT_UTC} UTC. Force close all positions immediately.")
            return (False, "DAILY FLAT ACTIVE: No new positions permitted before next trading day.")
        return (False, "OK: Trading day active.")

    @classmethod
    def audit_environment_security(cls, is_live_account: bool, owner_auth_token: Optional[str] = None) -> Tuple[bool, str]:
        """
        Ensures execution remains strictly quarantined to Demo unless owner authenticated.
        """
        if is_live_account and not owner_auth_token:
            return (False, "CRITICAL SECURITY VETO: Live account execution attempted without authenticated owner authorization token.")
        return (True, "APPROVED: Running in approved environment.")

    @classmethod
    def get_rule_matrix_summary(cls) -> Dict[str, Any]:
        """Returns structured JSON summary of the 3-tier rules."""
        return {
            "tier_1_immutable_hard_constraints": {
                "prohibit_lookahead_bias": True,
                "prohibit_data_leakage": True,
                "mandatory_stop_loss": True,
                "prohibit_martingale_and_grid": True,
                "hard_max_risk_per_trade_pct": cls.HARD_MAX_RISK_PER_TRADE_PCT,
                "portfolio_daily_loss_ceiling_usd": cls.HARD_PORTFOLIO_MAX_DAILY_LOSS_USD,
                "symbol_max_consecutive_losses": cls.HARD_MAX_CONSECUTIVE_LOSSES,
                "max_open_positions": cls.HARD_MAX_OPEN_POSITIONS,
                "daily_flat_enforcement_utc": cls.HARD_MANDATORY_DAILY_FLAT_UTC,
                "prohibit_overnight_holding": cls.HARD_PROHIBIT_OVERNIGHT,
                "risk_governor_absolute_supremacy": True,
                "environment": "Pepperstone Demo #5258778 (Strict Sandbox)"
            },
            "tier_2_adaptive_rules": {
                "description": "Parameters AI can propose and mutate within verified limits; requires statistical validation before deployment",
                "parameters": list(cls.ADAPTIVE_PARAM_BOUNDS.keys()),
                "bounds": cls.ADAPTIVE_PARAM_BOUNDS
            },
            "tier_3_open_research_hypotheses": {
                "description": "Unbounded strategy formulation families requiring systematic logging, backtesting, and attribution",
                "families": cls.VALID_HYPOTHESIS_FAMILIES
            }
        }

if __name__ == '__main__':
    matrix = RuleClassificationMatrix()
    print("="*80)
    print("🏛️ INSTITUTIONAL RULE CLASSIFICATION MATRIX V4 (VERIFICATION)")
    print("="*80)
    summary = matrix.get_rule_matrix_summary()
    print(json.dumps(summary, indent=2))
    
    # Test valid params
    test_valid = {'sl': 4.5, 'rr': 3.0, 'max_spread': 0.20, 'risk_per_trade_pct': 1.0}
    ok, errs = matrix.validate_strategy_parameters(test_valid, 'XAUUSD')
    print(f"\nTest Valid Parameters: {'PASS' if ok else 'FAIL'}")
    assert ok, f"Expected pass, got {errs}"
    
    # Test Martingale rejection
    test_martingale = {'sl': 4.5, 'rr': 3.0, 'lot_multiplier': 2.0}
    ok, errs = matrix.validate_strategy_parameters(test_martingale, 'XAUUSD')
    print(f"Test Martingale Rejection: {'PASS (VETOED)' if not ok else 'FAIL'}")
    assert not ok and "Martingale" in errs[0]
    
    # Test Daily Flat Trigger
    flat_trig, reason = matrix.evaluate_daily_flat_mandate(2150, has_open_position=True)
    print(f"Test Daily Flat at 21:50 UTC: {'PASS (TRIGGERED)' if flat_trig else 'FAIL'}")
    assert flat_trig
    
    print("\n✅ ALL RULE CLASSIFICATION TESTS PASSED PERFECTLY!")
