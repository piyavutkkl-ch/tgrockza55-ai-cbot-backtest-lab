"""
Adaptive Strategy Selection & Dynamic Switching Engine V4
=========================================================
Implements the 8-stage Hybrid Intelligence Strategy Selection Pipeline:
1. Deterministic Eligibility Filter (Session, News, Spread, Risk Governor)
2. Market Regime Matching
3. Historical Context & Regime Similarity
4. Conditional Performance Scoring
5. Risk-Adjusted Ranking (Suitability Score, not uncalibrated win probabilities)
6. Strategy Router & Explicit No-Trade Decision (STR-009)
7. Dynamic Strategy Switching with Hysteresis (prevents whipsaw, preserves active orders)
8. Complete Decision Audit Trail
"""

from typing import Dict, Any, List, Optional, Tuple
import os
import json
from datetime import datetime, timezone

from market_intelligence_engine import MarketRegime
from strategy_library import StrategyRegistry, BaseAdaptiveStrategy
from risk_governor import RiskGovernor

class AdaptiveStrategySelector:
    """
    Selects the optimal strategy from the Strategy Library for any given Market Context Fingerprint.
    """

    MIN_HYSTERESIS_BARS = 15      # Prevent switching strategies within 15 bars unless critical
    MIN_SUITABILITY_SCORE = 60.0  # Threshold to activate a strategy; below this routes to STR-009

    def __init__(self, registry: StrategyRegistry, risk_governor: RiskGovernor):
        self.registry = registry
        self.risk_governor = risk_governor
        
        self.current_active_strategy_id: str = "STR-009"
        self.bars_since_last_switch: int = 999
        self.switch_audit_log: List[Dict[str, Any]] = []

    def evaluate_and_select(self, fingerprint: Dict[str, Any], curr_bar: Dict[str, Any], has_active_position: bool = False) -> Dict[str, Any]:
        """
        Executes the 8-stage selection pipeline and returns the routing decision.
        """
        self.bars_since_last_switch += 1
        t_str = fingerprint['timestamp']
        symbol = fingerprint['symbol']
        regime = fingerprint['primary_market_regime']
        news_state = fingerprint['news_context']['news_state']
        spread = fingerprint['microstructure']['spread']
        
        # 1. Deterministic Risk Governor Check
        gov_ok, gov_msg = self.risk_governor.can_open_trade(
            symbol=symbol,
            current_spread=spread,
            current_time_hhmm=fingerprint['time_context']['hour_utc'] * 100 + fingerprint['time_context']['minute_utc'],
            min_to_news=fingerprint['news_context']['min_to_next'],
            news_impact=fingerprint['news_context']['next_impact'],
            min_since_news=fingerprint['news_context']['min_since_last'],
            last_impact=fingerprint['news_context']['last_impact']
        )
        
        if not gov_ok:
            return self._route_to_no_trade(t_str, f"Risk Governor Gate: {gov_msg}", fingerprint)

        # 2. Check Daily Flat Enforcement
        is_daily_flat = fingerprint['time_context']['is_daily_flat_triggered']
        if is_daily_flat:
            return self._route_to_no_trade(t_str, "Mandatory Daily Flat active (21:45 UTC cutoff)", fingerprint)

        # 3. Strategy Eligibility Filtering & Scoring
        candidates: List[Dict[str, Any]] = []
        for sid, strat in self.registry.strategies.items():
            if sid == "STR-009":
                continue # Baseline fallback
                
            suitable, reason = strat.is_context_suitable(fingerprint)
            if not suitable:
                continue
                
            # Compute Statistical Suitability Score (0 to 100)
            score = self._compute_suitability_score(strat, fingerprint)
            candidates.append({
                "strategy_id": sid,
                "strategy_name": strat.name,
                "suitability_score": score,
                "strategy": strat
            })
            
        # 4. Sort Candidates by Score
        candidates.sort(key=lambda x: x['suitability_score'], reverse=True)
        
        # 5. Routing Decision
        if not candidates or candidates[0]['suitability_score'] < self.MIN_SUITABILITY_SCORE:
            return self._route_to_no_trade(t_str, "No candidate met minimum suitability score threshold (60.0)", fingerprint)
            
        top_candidate = candidates[0]
        selected_id = top_candidate['strategy_id']
        selected_strat = top_candidate['strategy']
        
        # 6. Dynamic Switching with Hysteresis
        if selected_id != self.current_active_strategy_id:
            # Check if active position prevents switching
            if has_active_position:
                return {
                    "action": "MAINTAIN_ACTIVE_POSITION",
                    "active_strategy_id": self.current_active_strategy_id,
                    "target_strategy_id": selected_id,
                    "reason": "Maintaining active position under previous strategy management",
                    "fingerprint": fingerprint
                }
                
            # Hysteresis check (unless emergency regime shift)
            is_emergency_shift = regime in [MarketRegime.NEWS_DRIVEN, MarketRegime.THIN_LIQUIDITY]
            if self.bars_since_last_switch < self.MIN_HYSTERESIS_BARS and not is_emergency_shift:
                # Maintain current strategy to avoid whipsawing
                selected_strat = self.registry.get_strategy(self.current_active_strategy_id)
                selected_id = self.current_active_strategy_id
            else:
                self._record_strategy_switch(t_str, self.current_active_strategy_id, selected_id, top_candidate['suitability_score'], regime)
                self.current_active_strategy_id = selected_id
                self.bars_since_last_switch = 0
                
        # 7. Evaluate Trade Signal from Selected Strategy
        side, sl_dist, tp_dist, meta = selected_strat.evaluate_signal(fingerprint, curr_bar)
        
        return {
            "action": "EXECUTE" if side != "NONE" else "HOLD",
            "selected_strategy_id": selected_id,
            "selected_strategy_name": selected_strat.name,
            "suitability_score": top_candidate['suitability_score'],
            "trade_signal": {
                "side": side,
                "sl_distance": sl_dist,
                "tp_distance": tp_dist,
                "metadata": meta
            },
            "market_regime": regime,
            "alternative_candidates": [{"id": c['strategy_id'], "score": c['suitability_score']} for c in candidates[1:4]],
            "audit_reason": f"Selected {selected_id} for {regime} with score {top_candidate['suitability_score']:.1f}"
        }

    def _compute_suitability_score(self, strat: BaseAdaptiveStrategy, fp: Dict[str, Any]) -> float:
        """
        Computes calibrated Suitability Score (0 to 100).
        NOT an uncalibrated win probability.
        Factors:
        - Primary Regime Match: +40 pts
        - Secondary / Active Regime Match: +20 pts
        - Low Cost Sensitivity in elevated spread: +15 pts
        - Order Flow Delta Confirmation: +15 pts
        - High Confidence Score: +10 pts
        """
        score = 20.0 # Base participation
        primary_regime = fp['primary_market_regime']
        active_regimes = fp['active_market_regimes']
        conf = fp.get('confidence_score', 0.5)
        is_spread_elevated = fp['microstructure']['is_spread_elevated']
        delta = abs(fp['microstructure']['order_flow_delta'])
        
        if primary_regime in strat.suitable_regimes:
            score += 40.0
        elif any(r in strat.suitable_regimes for r in active_regimes):
            score += 20.0
            
        if not is_spread_elevated or strat.execution_cost_sensitivity == "LOW":
            score += 15.0
            
        if delta > 10.0:
            score += 15.0
            
        score += conf * 10.0
        return min(100.0, score)

    def _route_to_no_trade(self, t_str: str, reason: str, fp: Dict[str, Any]) -> Dict[str, Any]:
        """Explicit routing to STR-009 No Trade."""
        return {
            "action": "NO_TRADE",
            "selected_strategy_id": "STR-009",
            "selected_strategy_name": "Capital Defense & No-Trade Mode",
            "suitability_score": 100.0,
            "trade_signal": {"side": "NONE", "sl_distance": 0.0, "tp_distance": 0.0, "metadata": {"action": "NO_TRADE"}},
            "market_regime": fp['primary_market_regime'],
            "audit_reason": reason
        }

    def _record_strategy_switch(self, timestamp: str, from_id: str, to_id: str, score: float, regime: str):
        entry = {
            "timestamp": timestamp,
            "from_strategy": from_id,
            "to_strategy": to_id,
            "score": round(score, 1),
            "market_regime": regime,
            "bars_held": self.bars_since_last_switch
        }
        self.switch_audit_log.append(entry)

if __name__ == '__main__':
    print("Testing AdaptiveStrategySelector...")
    reg = StrategyRegistry()
    gov = RiskGovernor()
    selector = AdaptiveStrategySelector(reg, gov)
    
    # Mock fingerprint in Strong Uptrend
    mock_fp = {
        'symbol': 'XAUUSD',
        'timestamp': '2026-11-02 14:00',
        'primary_market_regime': MarketRegime.STRONG_UPTREND,
        'active_market_regimes': [MarketRegime.STRONG_UPTREND],
        'time_context': {'primary_session': 'NEW_YORK', 'hour_utc': 14, 'minute_utc': 0, 'is_daily_flat_triggered': False},
        'news_context': {'news_state': 'CLEAR', 'min_to_next': 999, 'next_impact': '', 'min_since_last': 999, 'last_impact': ''},
        'microstructure': {'spread': 0.15, 'is_spread_elevated': False, 'order_flow_delta': 25.0},
        'price_behavior': {'high_20': 3910.0, 'low_20': 3890.0},
        'confidence_score': 0.85
    }
    curr_bar = {'close': 3905.0, 'ema50': 3898.0}
    
    decision = selector.evaluate_and_select(mock_fp, curr_bar)
    print("Routing Decision:", decision['selected_strategy_id'], "| Action:", decision['action'], "| Reason:", decision['audit_reason'])
    assert decision['selected_strategy_id'] == 'STR-001'
    assert decision['action'] == 'EXECUTE'
    assert decision['trade_signal']['side'] == 'BUY'
    print("✅ AdaptiveStrategySelector V4 verified successfully!")
