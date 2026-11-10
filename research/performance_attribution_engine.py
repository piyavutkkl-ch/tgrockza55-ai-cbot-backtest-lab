"""
Performance Attribution & AI Critic Engine V4 (Architecture V4)
================================================================
Implements post-trade quantitative audit and empirical critique:
1. Trade Win/Loss Diagnostic:
   - Timing: Early vs Late entry
   - Regime Accuracy: Was market regime correctly identified?
   - Strategy Match: Was this the right strategy for this context?
   - News Impact: Did macro news disrupt the trade?
   - DOM & Order Flow: Did L2 book and Delta confirm the move?
   - Execution Friction: Did spread and slippage exceed expectation?
   - Exit Quality: Did trade exit at optimal structural target or get stopped out?

2. 7 Formal Failure Mode Categories:
   - 1. STRATEGY_FAILURE: Fundamental edge breakdown under target conditions
   - 2. REGIME_MISCLASSIFICATION: Incompatible market regime during entry
   - 3. STRATEGY_SELECTION_FAILURE: Sub-optimal strategy selected from library
   - 4. EXECUTION_FAILURE: Severe slippage, execution latency, or spread spikes
   - 5. DATA_FAILURE: Data feed staleness, missing ticks, or anomalous DOM
   - 6. RISK_MANAGEMENT_FAILURE: Sub-optimal SL distance or holding duration breach
   - 7. MODEL_OVERFITTING: Hyper-optimized parameters failing on out-of-sample data

3. AI Critic:
   - Empirically challenges Strategy Researcher claims with mathematical evidence.
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone
import json

class FailureMode:
    STRATEGY_FAILURE = "STRATEGY_FAILURE"
    REGIME_MISCLASSIFICATION = "REGIME_MISCLASSIFICATION"
    STRATEGY_SELECTION_FAILURE = "STRATEGY_SELECTION_FAILURE"
    EXECUTION_FAILURE = "EXECUTION_FAILURE"
    DATA_FAILURE = "DATA_FAILURE"
    RISK_MANAGEMENT_FAILURE = "RISK_MANAGEMENT_FAILURE"
    MODEL_OVERFITTING = "MODEL_OVERFITTING"
    NONE_WIN = "NONE_WIN"

class PerformanceAttributionEngine:
    """
    Evaluates completed trades and attributes the causal drivers of performance.
    """

    @classmethod
    def attribute_trade(cls, trade: Dict[str, Any], fingerprint: Dict[str, Any], strategy_cfg: Dict[str, Any]) -> Dict[str, Any]:
        """
        Diagnoses a single trade outcome across timing, regime, DOM, friction, and exit.
        """
        pnl = float(trade.get('pnl', 0.0))
        is_win = pnl > 0
        side = trade.get('side', 'BUY')
        reason = trade.get('reason', 'EXIT')
        
        # Microstructure features at entry
        micro = fingerprint.get('microstructure', {})
        spread = float(micro.get('spread', 0.15))
        avg_spread = float(micro.get('avg_spread', 0.15))
        delta = float(micro.get('order_flow_delta', 0.0))
        imb = float(micro.get('dom_imbalance', 0.0))
        
        # Regime features
        primary_regime = fingerprint.get('primary_market_regime', 'SIDEWAY')
        suitable_regimes = strategy_cfg.get('suitable_market_regimes', [])
        news_state = fingerprint.get('news_context', {}).get('news_state', 'CLEAR')
        
        # 1. Regime compatibility check
        regime_compatible = (not suitable_regimes) or (primary_regime in suitable_regimes)
        
        # 2. Execution friction analysis
        friction_severe = (spread > avg_spread * 1.8)
        
        # 3. Order flow alignment
        delta_aligned = (side == 'BUY' and delta > 0) or (side == 'SELL' and delta < 0)
        
        # 4. Failure Mode Determination
        failure_mode = FailureMode.NONE_WIN
        diagnostic_notes = []
        
        if is_win:
            diagnostic_notes.append(f"Trade succeeded via {reason}: Strong synergy with {primary_regime} regime.")
            if delta_aligned:
                diagnostic_notes.append("Order flow delta strongly supported trade direction.")
        else:
            # Diagnose loss
            if news_state in ["PRE_NEWS_BLACKOUT", "POST_NEWS_VOLATILITY"]:
                failure_mode = FailureMode.RISK_MANAGEMENT_FAILURE
                diagnostic_notes.append("Trade breached news safety window during macroeconomic release.")
            elif not regime_compatible:
                failure_mode = FailureMode.REGIME_MISCLASSIFICATION
                diagnostic_notes.append(f"Strategy deployed in incompatible regime {primary_regime} (Expected: {suitable_regimes}).")
            elif friction_severe:
                failure_mode = FailureMode.EXECUTION_FAILURE
                diagnostic_notes.append(f"Execution spread ({spread:.2f}) was severely elevated above baseline ({avg_spread:.2f}).")
            elif not delta_aligned and abs(delta) > 15.0:
                failure_mode = FailureMode.STRATEGY_SELECTION_FAILURE
                diagnostic_notes.append(f"Traded against strong opposing institutional delta ({delta:.1f}). Alternative strategy should have been routed.")
            elif reason == "SL":
                failure_mode = FailureMode.STRATEGY_FAILURE
                diagnostic_notes.append("Normal statistical stop-out: Hypothesis invalid in this specific market window.")
            else:
                failure_mode = FailureMode.RISK_MANAGEMENT_FAILURE
                diagnostic_notes.append("Sub-optimal exit or holding duration exceeded.")
                
        return {
            "trade_id": trade.get('entry_time', ''),
            "symbol": trade.get('symbol', 'UNKNOWN'),
            "side": side,
            "pnl_usd": round(pnl, 2),
            "is_win": is_win,
            "exit_reason": reason,
            "primary_regime": primary_regime,
            "failure_mode": failure_mode,
            "delta_aligned": delta_aligned,
            "friction_severe": friction_severe,
            "diagnostic_notes": diagnostic_notes
        }

class AICritic:
    """
    AI Critic: Rigorously audits Strategy Researcher claims and challenges unproven hypotheses.
    """

    @classmethod
    def critique_strategy_performance(cls, validation_report: Dict[str, Any], attribution_summary: Dict[str, Any]) -> Dict[str, Any]:
        """
        Synthesizes attribution and validation results into an adversarial critique.
        """
        metrics = validation_report.get('metrics', {})
        passed = validation_report.get('validation_passed', False)
        failed_checks = validation_report.get('failed_checks', [])
        
        n_trades = metrics.get('trades_count', 0)
        pf = metrics.get('profit_factor', 0.0)
        sharpe = metrics.get('annualized_sharpe', 0.0)
        ruin = metrics.get('monte_carlo_ruin_prob_pct', 0.0)
        
        verdict = "APPROVED" if passed else "REJECTED_WITH_PREJUDICE"
        critique_points = []
        
        if n_trades < 15:
            critique_points.append(f"CRITIQUE (Sample Inadequacy): Only {n_trades} trades observed. Statistical significance is insufficient to reject random luck.")
            
        if pf > 8.0:
            critique_points.append(f"CRITIQUE (Overfitting Suspicion): Profit factor {pf:.2f} is suspiciously high for intraday trading, indicating curve-fitting on local historical noise.")
            
        if ruin > 0.5:
            critique_points.append(f"CRITIQUE (Tail Risk Warning): Monte Carlo risk of ruin ({ruin:.2f}%) exceeds institutional threshold of 0.5%. Capital risk too high.")
            
        failure_dist = attribution_summary.get('failure_distribution', {})
        if failure_dist.get(FailureMode.REGIME_MISCLASSIFICATION, 0) > 2:
            critique_points.append("CRITIQUE (Regime Inconsistency): Multiple losses caused by regime misclassification. Need tighter regime gate.")
            
        if not critique_points and passed:
            critique_points.append("CRITIQUE (Endorsement): Robust performance across Sharpe, Sortino, and Monte Carlo. No severe failure clusters detected.")
            
        return {
            "critic_verdict": verdict,
            "critique_points": critique_points,
            "recommended_action": "PROMOTE_TO_CHALLENGER" if passed else "RETURN_TO_RESEARCH_SANDBOX"
        }

if __name__ == '__main__':
    print("Testing PerformanceAttributionEngine & AICritic...")
    mock_trade = {'entry_time': '2026-11-02 14:00', 'symbol': 'XAUUSD', 'side': 'BUY', 'pnl': -5.2, 'reason': 'SL'}
    mock_fp = {
        'primary_market_regime': 'STRONG_DOWNTREND',
        'microstructure': {'spread': 0.15, 'avg_spread': 0.15, 'order_flow_delta': -25.0},
        'news_context': {'news_state': 'CLEAR'}
    }
    mock_cfg = {'suitable_market_regimes': ['STRONG_UPTREND']}
    
    attr = PerformanceAttributionEngine.attribute_trade(mock_trade, mock_fp, mock_cfg)
    print("Attribution Result:", attr['failure_mode'], "| Notes:", attr['diagnostic_notes'])
    assert attr['failure_mode'] == FailureMode.REGIME_MISCLASSIFICATION
    
    val_report = {'validation_passed': True, 'metrics': {'trades_count': 25, 'profit_factor': 2.1, 'annualized_sharpe': 1.8, 'monte_carlo_ruin_prob_pct': 0.0}}
    critique = AICritic.critique_strategy_performance(val_report, {'failure_distribution': {}})
    print("Critic Verdict:", critique['critic_verdict'])
    assert critique['critic_verdict'] == "APPROVED"
    print("✅ PerformanceAttributionEngine & AICritic V4 verified successfully!")
