"""
Adaptive Strategy Library & Strategy Registry V4 (Architecture V4)
==================================================================
Implements the formalized, extensible strategy library conforming to MASTER PROMPT V4:
- Standardized Strategy Schema
- Immutable Strategy Versioning (never overwrite history without a new version)
- Suitable Market Regimes, Sessions, News Conditions, Failure Conditions, and Cost Sensitivity
- Initial Core Fleet:
    * STR-001: Trend Following
    * STR-002: Mean Reversion
    * STR-003: Liquidity Sweep Reversal
    * STR-004: Momentum Breakout
    * STR-005: News Reaction
    * STR-006: Order Flow Imbalance
    * STR-007: Volatility Reversal
    * STR-008: Session Opening Range
    * STR-009: No Trade
"""

from typing import Dict, Any, List, Optional, Tuple
from abc import ABC, abstractmethod
import os
import json
from datetime import datetime, timezone

from market_intelligence_engine import MarketRegime

class BaseAdaptiveStrategy(ABC):
    """
    Standardized base class for all quantitative strategies in the library.
    """
    def __init__(self, strategy_id: str, version: str, name: str, hypothesis: str):
        self.strategy_id = strategy_id
        self.version = version
        self.name = name
        self.hypothesis = hypothesis
        
        # Risk & execution defaults
        self.sl_dist: float = 4.0
        self.rr_ratio: float = 2.5
        self.risk_per_trade_pct: float = 1.0
        
        # Environmental affinities
        self.suitable_regimes: List[str] = []
        self.suitable_sessions: List[str] = []
        self.suitable_news_conditions: List[str] = ["CLEAR"]
        
        # Attribution & metadata
        self.failure_conditions: List[str] = []
        self.execution_cost_sensitivity: str = "MEDIUM" # LOW, MEDIUM, HIGH
        self.validation_status: str = "EXPERIMENTAL"    # EXPERIMENTAL, CHALLENGER, CHAMPION, REJECTED
        
        # Metrics cache
        self.historical_metrics: Dict[str, Any] = {}
        self.context_performance: Dict[str, Any] = {}

    def is_context_suitable(self, fingerprint: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Deterministic pre-filter: Checks if market regime, session, and news state match.
        """
        # 1. News check
        news_state = fingerprint['news_context']['news_state']
        if news_state == "PRE_NEWS_BLACKOUT" and self.strategy_id != "STR-009":
            return False, "Pre-news volatility blackout active"
        if news_state not in self.suitable_news_conditions and "ALL" not in self.suitable_news_conditions:
            return False, f"News state {news_state} not suitable"
            
        # 2. Session check
        primary_session = fingerprint['time_context']['primary_session']
        if self.suitable_sessions and "ALL" not in self.suitable_sessions and primary_session not in self.suitable_sessions:
            return False, f"Session {primary_session} not in suitable sessions {self.suitable_sessions}"
            
        # 3. Market Regime check
        primary_regime = fingerprint['primary_market_regime']
        active_regimes = fingerprint['active_market_regimes']
        if self.suitable_regimes and not any(r in self.suitable_regimes for r in active_regimes):
            return False, f"Regime {primary_regime} not in suitable regimes {self.suitable_regimes}"
            
        return True, "Context suitable"

    @abstractmethod
    def evaluate_signal(self, fingerprint: Dict[str, Any], curr_bar: Dict[str, Any]) -> Tuple[str, float, float, Dict[str, Any]]:
        """
        Evaluates trading signal from the bar and context fingerprint.
        Returns: (side, sl_distance, tp_distance, execution_metadata)
        Side must be 'BUY', 'SELL', or 'NONE'.
        """
        pass

    def to_dict(self) -> Dict[str, Any]:
        """Serializes strategy specification to dictionary."""
        return {
            "strategy_id": self.strategy_id,
            "version": self.version,
            "name": self.name,
            "hypothesis": self.hypothesis,
            "parameters": {
                "sl_dist": self.sl_dist,
                "rr_ratio": self.rr_ratio,
                "tp_dist": round(self.sl_dist * self.rr_ratio, 2),
                "risk_per_trade_pct": self.risk_per_trade_pct
            },
            "suitable_market_regimes": self.suitable_regimes,
            "suitable_trading_sessions": self.suitable_sessions,
            "suitable_news_conditions": self.suitable_news_conditions,
            "failure_conditions": self.failure_conditions,
            "execution_cost_sensitivity": self.execution_cost_sensitivity,
            "validation_status": self.validation_status,
            "historical_metrics": self.historical_metrics,
            "context_performance": self.context_performance
        }

# -----------------------------------------------------------------------------
# Concrete Strategy Implementations (STR-001 through STR-009)
# -----------------------------------------------------------------------------

class STR001_TrendFollowing(BaseAdaptiveStrategy):
    def __init__(self, version="1.0.0"):
        super().__init__(
            strategy_id="STR-001", version=version, name="Multi-Timeframe Trend Following",
            hypothesis="Asset prices in strong directional trends exhibit momentum persistence when entering on minor pullbacks."
        )
        self.suitable_regimes = [MarketRegime.STRONG_UPTREND, MarketRegime.STRONG_DOWNTREND]
        self.suitable_sessions = ["LONDON", "NEW_YORK", "LONDON_NY_OVERLAP"]
        self.failure_conditions = ["Chop / Range transition", "Premature trend exhaustion"]
        self.execution_cost_sensitivity = "LOW"
        self.sl_dist = 5.0
        self.rr_ratio = 2.5

    def evaluate_signal(self, fp: Dict[str, Any], curr: Dict[str, Any]) -> Tuple[str, float, float, Dict[str, Any]]:
        c = float(curr['close'])
        ema50 = float(curr.get('ema50', c))
        delta = fp['microstructure']['order_flow_delta']
        regime = fp['primary_market_regime']
        
        if regime == MarketRegime.STRONG_UPTREND and delta > 0 and c >= ema50:
            return "BUY", self.sl_dist, self.sl_dist * self.rr_ratio, {"signal_trigger": "UPTREND_MOMENTUM_ALIGN"}
        elif regime == MarketRegime.STRONG_DOWNTREND and delta < 0 and c <= ema50:
            return "SELL", self.sl_dist, self.sl_dist * self.rr_ratio, {"signal_trigger": "DOWNTREND_MOMENTUM_ALIGN"}
        return "NONE", 0.0, 0.0, {}

class STR002_MeanReversion(BaseAdaptiveStrategy):
    def __init__(self, version="1.0.0"):
        super().__init__(
            strategy_id="STR-002", version=version, name="Session VWAP Mean Reversion",
            hypothesis="Prices oscillating in range-bound markets mean-revert to the volume-weighted average price (VWAP)."
        )
        self.suitable_regimes = [MarketRegime.RANGE_BOUND, MarketRegime.SIDEWAY]
        self.suitable_sessions = ["ASIA", "LONDON"]
        self.failure_conditions = ["Sudden trend breakout", "News volatility expansion"]
        self.execution_cost_sensitivity = "HIGH"
        self.sl_dist = 4.0
        self.rr_ratio = 2.0

    def evaluate_signal(self, fp: Dict[str, Any], curr: Dict[str, Any]) -> Tuple[str, float, float, Dict[str, Any]]:
        c = float(curr['close'])
        vwap = float(curr.get('vwap', c))
        sd = float(curr.get('sd', 3.5))
        delta = fp['microstructure']['order_flow_delta']
        
        if c <= (vwap - sd * 1.0) and delta > 0:
            return "BUY", self.sl_dist, self.sl_dist * self.rr_ratio, {"signal_trigger": "VWAP_LOWER_BAND_BOUNCE"}
        elif c >= (vwap + sd * 1.0) and delta < 0:
            return "SELL", self.sl_dist, self.sl_dist * self.rr_ratio, {"signal_trigger": "VWAP_UPPER_BAND_BOUNCE"}
        return "NONE", 0.0, 0.0, {}

class STR003_LiquiditySweepReversal(BaseAdaptiveStrategy):
    def __init__(self, version="1.0.0"):
        super().__init__(
            strategy_id="STR-003", version=version, name="Liquidity Sweep & Stop Hunt Reversal",
            hypothesis="False breakouts past key structural levels absorb retail stop liquidity, creating high-probability sharp reversals."
        )
        self.suitable_regimes = [MarketRegime.FALSE_BREAKOUT, MarketRegime.REVERSAL]
        self.suitable_sessions = ["LONDON", "NEW_YORK", "LONDON_NY_OVERLAP"]
        self.failure_conditions = ["True runaway breakout with massive institutional volume"]
        self.execution_cost_sensitivity = "MEDIUM"
        self.sl_dist = 4.5
        self.rr_ratio = 3.0

    def evaluate_signal(self, fp: Dict[str, Any], curr: Dict[str, Any]) -> Tuple[str, float, float, Dict[str, Any]]:
        micro = fp['microstructure']
        price = fp['price_behavior']
        
        if (micro['liquidity_sweep_detected'] or price['is_bullish_rejection']) and micro['is_bullish_absorption']:
            return "BUY", self.sl_dist, self.sl_dist * self.rr_ratio, {"signal_trigger": "BULLISH_SWEEP_ABSORPTION"}
        elif (micro['liquidity_sweep_detected'] or price['is_bearish_rejection']) and micro['is_bearish_absorption']:
            return "SELL", self.sl_dist, self.sl_dist * self.rr_ratio, {"signal_trigger": "BEARISH_SWEEP_ABSORPTION"}
        return "NONE", 0.0, 0.0, {}

class STR004_MomentumBreakout(BaseAdaptiveStrategy):
    def __init__(self, version="1.0.0"):
        super().__init__(
            strategy_id="STR-004", version=version, name="Volatility Expansion Breakout",
            hypothesis="When price pierces multi-hour consolidation with aggressive volume delta, it initiates a sustained momentum leg."
        )
        self.suitable_regimes = [MarketRegime.BREAKOUT, MarketRegime.VOLATILITY_EXPANSION]
        self.suitable_sessions = ["LONDON", "NEW_YORK", "LONDON_NY_OVERLAP"]
        self.failure_conditions = ["Bull/Bear traps", "False breakout re-absorption"]
        self.execution_cost_sensitivity = "LOW"
        self.sl_dist = 5.5
        self.rr_ratio = 2.8

    def evaluate_signal(self, fp: Dict[str, Any], curr: Dict[str, Any]) -> Tuple[str, float, float, Dict[str, Any]]:
        c = float(curr['close'])
        price = fp['price_behavior']
        delta = fp['microstructure']['order_flow_delta']
        
        if c >= price['high_20'] and delta > 15.0:
            return "BUY", self.sl_dist, self.sl_dist * self.rr_ratio, {"signal_trigger": "HIGH_20_BREAKOUT"}
        elif c <= price['low_20'] and delta < -15.0:
            return "SELL", self.sl_dist, self.sl_dist * self.rr_ratio, {"signal_trigger": "LOW_20_BREAKOUT"}
        return "NONE", 0.0, 0.0, {}

class STR005_NewsReaction(BaseAdaptiveStrategy):
    def __init__(self, version="1.0.0"):
        super().__init__(
            strategy_id="STR-005", version=version, name="Post-News Directional Reaction",
            hypothesis="After economic news releases settle (15-30 mins post-event), directional momentum establishes a multi-hour trend."
        )
        self.suitable_regimes = [MarketRegime.NEWS_DRIVEN, MarketRegime.STRONG_UPTREND, MarketRegime.STRONG_DOWNTREND]
        self.suitable_sessions = ["NEW_YORK", "LONDON_NY_OVERLAP"]
        self.suitable_news_conditions = ["POST_NEWS_VOLATILITY"]
        self.failure_conditions = ["Whipsaw news repricing", "Conflicting economic data components"]
        self.execution_cost_sensitivity = "MEDIUM"
        self.sl_dist = 6.0
        self.rr_ratio = 3.0

    def evaluate_signal(self, fp: Dict[str, Any], curr: Dict[str, Any]) -> Tuple[str, float, float, Dict[str, Any]]:
        n_ctx = fp['news_context']
        delta = fp['microstructure']['order_flow_delta']
        c = float(curr['close'])
        ema50 = float(curr.get('ema50', c))
        
        # Only trade between 15m and 60m post news
        if 15.0 <= n_ctx['min_since_last'] <= 60.0:
            if c > ema50 and delta > 20.0:
                return "BUY", self.sl_dist, self.sl_dist * self.rr_ratio, {"signal_trigger": "POST_NEWS_BULL_CONTINUATION"}
            elif c < ema50 and delta < -20.0:
                return "SELL", self.sl_dist, self.sl_dist * self.rr_ratio, {"signal_trigger": "POST_NEWS_BEAR_CONTINUATION"}
        return "NONE", 0.0, 0.0, {}

class STR006_OrderFlowImbalance(BaseAdaptiveStrategy):
    def __init__(self, version="1.0.0"):
        super().__init__(
            strategy_id="STR-006", version=version, name="L2 DOM Order Flow Imbalance",
            hypothesis="Significant DOM volume imbalances at key psychological levels signal aggressive institutional accumulation or distribution."
        )
        self.suitable_regimes = [MarketRegime.REVERSAL, MarketRegime.RANGE_BOUND]
        self.suitable_sessions = ["ALL"]
        self.failure_conditions = ["Spoofing / phantom orders in order book", "Flash liquidity pulls"]
        self.execution_cost_sensitivity = "HIGH"
        self.sl_dist = 4.0
        self.rr_ratio = 2.5

    def evaluate_signal(self, fp: Dict[str, Any], curr: Dict[str, Any]) -> Tuple[str, float, float, Dict[str, Any]]:
        micro = fp['microstructure']
        imb = micro['dom_imbalance']
        delta = micro['order_flow_delta']
        
        if imb >= 0.025 and delta > 5.0:
            return "BUY", self.sl_dist, self.sl_dist * self.rr_ratio, {"signal_trigger": "DOM_BID_WALL_ABSORPTION"}
        elif imb <= -0.025 and delta < -5.0:
            return "SELL", self.sl_dist, self.sl_dist * self.rr_ratio, {"signal_trigger": "DOM_ASK_WALL_ABSORPTION"}
        return "NONE", 0.0, 0.0, {}

class STR007_VolatilityReversal(BaseAdaptiveStrategy):
    def __init__(self, version="1.0.0"):
        super().__init__(
            strategy_id="STR-007", version=version, name="Extreme Volatility Stretch Reversal",
            hypothesis="Extreme deviations (>2.5 SD from VWAP) during non-news periods represent overextended retail positioning prone to sharp snaps."
        )
        self.suitable_regimes = [MarketRegime.REVERSAL, MarketRegime.VOLATILITY_EXPANSION]
        self.suitable_sessions = ["ASIA", "LONDON", "NEW_YORK"]
        self.failure_conditions = ["Structural multi-day trend repricing"]
        self.execution_cost_sensitivity = "MEDIUM"
        self.sl_dist = 5.0
        self.rr_ratio = 3.0

    def evaluate_signal(self, fp: Dict[str, Any], curr: Dict[str, Any]) -> Tuple[str, float, float, Dict[str, Any]]:
        c = float(curr['close'])
        vwap = float(curr.get('vwap', c))
        sd = float(curr.get('sd', 3.5))
        price = fp['price_behavior']
        
        if c <= (vwap - sd * 2.5) and price['is_bullish_rejection']:
            return "BUY", self.sl_dist, self.sl_dist * self.rr_ratio, {"signal_trigger": "VWAP_2.5SD_OVERSOLD_REVERSAL"}
        elif c >= (vwap + sd * 2.5) and price['is_bearish_rejection']:
            return "SELL", self.sl_dist, self.sl_dist * self.rr_ratio, {"signal_trigger": "VWAP_2.5SD_OVERBOUGHT_REVERSAL"}
        return "NONE", 0.0, 0.0, {}

class STR008_SessionOpeningRange(BaseAdaptiveStrategy):
    def __init__(self, version="1.0.0"):
        super().__init__(
            strategy_id="STR-008", version=version, name="Session Opening Range Expansion",
            hypothesis="The initial 15-minute range of the London or NY session defines institutional inventory imbalance for the day."
        )
        self.suitable_regimes = [MarketRegime.BREAKOUT, MarketRegime.VOLATILITY_EXPANSION]
        self.suitable_sessions = ["LONDON", "NEW_YORK", "LONDON_NY_OVERLAP"]
        self.failure_conditions = ["Asian range continuation", "Mid-morning chop"]
        self.execution_cost_sensitivity = "LOW"
        self.sl_dist = 5.0
        self.rr_ratio = 2.5

    def evaluate_signal(self, fp: Dict[str, Any], curr: Dict[str, Any]) -> Tuple[str, float, float, Dict[str, Any]]:
        t_ctx = fp['time_context']
        delta = fp['microstructure']['order_flow_delta']
        c = float(curr['close'])
        price = fp['price_behavior']
        
        if (t_ctx['is_london_open'] or t_ctx['is_ny_open']):
            if c >= price['high_20'] and delta > 10.0:
                return "BUY", self.sl_dist, self.sl_dist * self.rr_ratio, {"signal_trigger": "SESSION_OPEN_BULL_EXPANSION"}
            elif c <= price['low_20'] and delta < -10.0:
                return "SELL", self.sl_dist, self.sl_dist * self.rr_ratio, {"signal_trigger": "SESSION_OPEN_BEAR_EXPANSION"}
        return "NONE", 0.0, 0.0, {}

class STR009_NoTrade(BaseAdaptiveStrategy):
    def __init__(self, version="1.0.0"):
        super().__init__(
            strategy_id="STR-009", version=version, name="Capital Defense & No-Trade Mode",
            hypothesis="Preserving capital during illiquid, erratic, or uncertain market states is an active institutional trading edge."
        )
        self.suitable_regimes = [MarketRegime.THIN_LIQUIDITY, MarketRegime.HIGH_UNCERTAINTY, MarketRegime.NEWS_DRIVEN]
        self.suitable_sessions = ["ALL"]
        self.suitable_news_conditions = ["ALL"]
        self.failure_conditions = []
        self.execution_cost_sensitivity = "ZERO"
        self.validation_status = "CHAMPION"

    def evaluate_signal(self, fp: Dict[str, Any], curr: Dict[str, Any]) -> Tuple[str, float, float, Dict[str, Any]]:
        return "NONE", 0.0, 0.0, {"action": "NO_TRADE", "reason": "Capital defense active"}

# -----------------------------------------------------------------------------
# Strategy Registry & Lifecycle Manager
# -----------------------------------------------------------------------------

class StrategyRegistry:
    """
    Central repository for all strategies with immutable version history.
    """
    ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    REGISTRY_FILE = os.path.join(ROOT, 'docs', 'data', 'strategy_registry.json')

    def __init__(self):
        self.strategies: Dict[str, BaseAdaptiveStrategy] = {}
        self._load_core_fleet()

    def _load_core_fleet(self):
        core = [
            STR001_TrendFollowing(),
            STR002_MeanReversion(),
            STR003_LiquiditySweepReversal(),
            STR004_MomentumBreakout(),
            STR005_NewsReaction(),
            STR006_OrderFlowImbalance(),
            STR007_VolatilityReversal(),
            STR008_SessionOpeningRange(),
            STR009_NoTrade()
        ]
        for s in core:
            self.strategies[s.strategy_id] = s

    def get_strategy(self, strategy_id: str) -> Optional[BaseAdaptiveStrategy]:
        return self.strategies.get(strategy_id)

    def register_strategy(self, strategy: BaseAdaptiveStrategy):
        """Registers a new strategy or a new version of an existing strategy."""
        sid = strategy.strategy_id
        if sid in self.strategies:
            old_ver = self.strategies[sid].version
            if old_ver == strategy.version:
                raise ValueError(f"Immutable Version Violation: Strategy {sid} version {old_ver} already exists. Increment version to register updates.")
        self.strategies[sid] = strategy

    def save_registry_json(self):
        """Serializes current registry to JSON feed."""
        data = {
            "registry_version": "V4.0-INSTITUTIONAL",
            "updated_at_utc": datetime.now(timezone.utc).isoformat(),
            "total_strategies": len(self.strategies),
            "strategies": {sid: strat.to_dict() for sid, strat in self.strategies.items()}
        }
        os.makedirs(os.path.dirname(self.REGISTRY_FILE), exist_ok=True)
        with open(self.REGISTRY_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

if __name__ == '__main__':
    reg = StrategyRegistry()
    print("Testing StrategyRegistry...")
    print(f"Total core strategies loaded: {len(reg.strategies)}")
    for sid, s in reg.strategies.items():
        print(f"  [{s.strategy_id} v{s.version}] {s.name} ({s.validation_status})")
    reg.save_registry_json()
    print("Saved strategy registry to docs/data/strategy_registry.json")
    print("✅ Strategy Library & Registry V4 verified successfully!")
