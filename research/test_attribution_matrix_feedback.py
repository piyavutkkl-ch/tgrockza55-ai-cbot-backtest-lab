"""
Unit Tests for Pillar 3 & 4: Regime-Strategy Attribution Matrix & Dynamic Feedback Loop
======================================================================================
Tests:
1. Regime-Strategy Attribution Matrix persistence into SQLite
2. Dynamic Feedback Loop: Cutting losers (BANNED, weight 0.0)
3. Dynamic Feedback Loop: Promoting winners (PROMOTED, weight 1.35)
4. Conditional Strategy Router: Hysteresis stability and mandatory No-Trade (STR-009)
"""

import unittest
import sys, os, tempfile
from typing import Dict, Any

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'research'))

from market_intelligence_engine import MarketRegime
from strategy_library import StrategyRegistry
from risk_governor import RiskGovernor
from strategy_memory_recorder import StrategyMemoryRecorder
from adaptive_strategy_selector import AdaptiveStrategySelector

class TestAttributionMatrixFeedback(unittest.TestCase):

    def setUp(self):
        # Create isolated temporary database for test suite
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.sqlite', delete=False)
        self.temp_db.close()
        self.rec = StrategyMemoryRecorder(db_path=self.temp_db.name)
        self.registry = StrategyRegistry()
        self.risk_governor = RiskGovernor()
        self.selector = AdaptiveStrategySelector(self.registry, self.risk_governor, self.rec)

    def tearDown(self):
        if os.path.exists(self.temp_db.name):
            os.remove(self.temp_db.name)

    def _mock_fingerprint(self, regime: str, symbol: str = "XAUUSD", conf: float = 0.8) -> Dict[str, Any]:
        return {
            'symbol': symbol,
            'timestamp': '2026-11-14 10:00',
            'primary_market_regime': regime,
            'active_market_regimes': [regime],
            'time_context': {'hour_utc': 10, 'minute_utc': 0, 'primary_session': 'LONDON', 'is_daily_flat_triggered': False},
            'news_context': {'news_state': 'CLEAR', 'min_to_next': 999, 'next_impact': '', 'min_since_last': 999, 'last_impact': ''},
            'microstructure': {'spread': 0.12, 'is_spread_elevated': False, 'order_flow_delta': 12.0},
            'price_behavior': {'high_20': 3910.0, 'low_20': 3890.0},
            'confidence_score': conf
        }

    def test_01_attribution_matrix_persistence(self):
        trades = [
            {"strategy_id": "STR-001", "market_regime": MarketRegime.STRONG_UPTREND, "pnl": 10.0, "win": True},
            {"strategy_id": "STR-001", "market_regime": MarketRegime.STRONG_UPTREND, "pnl": 5.0, "win": True},
            {"strategy_id": "STR-001", "market_regime": MarketRegime.STRONG_UPTREND, "pnl": -3.0, "win": False},
        ]
        matrix = self.rec.update_regime_performance_matrix(trades)
        self.assertEqual(len(matrix), 1)
        row = matrix[0]
        self.assertEqual(row['strategy_code'], "STR-001")
        self.assertEqual(row['market_regime'], MarketRegime.STRONG_UPTREND)
        self.assertEqual(row['total_trades'], 3)
        self.assertAlmostEqual(row['win_rate_pct'], 66.7, places=1)
        self.assertAlmostEqual(row['net_pnl_usd'], 12.0, places=1)
        self.assertEqual(row['status'], "PROMOTED")
        self.assertEqual(row['weight_multiplier'], 1.35)

    def test_02_cut_losers_banned_feedback_loop(self):
        # Simulate Mean Reversion losing heavily in a Trend regime
        losing_trades = [
            {"strategy_id": "STR-002", "market_regime": MarketRegime.STRONG_UPTREND, "pnl": -5.0, "win": False},
            {"strategy_id": "STR-002", "market_regime": MarketRegime.STRONG_UPTREND, "pnl": -4.0, "win": False},
            {"strategy_id": "STR-002", "market_regime": MarketRegime.STRONG_UPTREND, "pnl": -6.0, "win": False},
            {"strategy_id": "STR-002", "market_regime": MarketRegime.STRONG_UPTREND, "pnl": -3.0, "win": False},
            {"strategy_id": "STR-002", "market_regime": MarketRegime.STRONG_UPTREND, "pnl": -4.5, "win": False},
        ]
        self.rec.update_regime_performance_matrix(losing_trades)
        perf = self.rec.get_regime_performance("STR-002", MarketRegime.STRONG_UPTREND)
        self.assertIsNotNone(perf)
        self.assertEqual(perf['status'], "BANNED")
        self.assertEqual(perf['weight_multiplier'], 0.0)

        # Verify router cuts its suitability score to 0.0 immediately
        fp = self._mock_fingerprint(MarketRegime.STRONG_UPTREND)
        s2 = self.registry.get_strategy("STR-002")
        score = self.selector._compute_suitability_score(s2, fp)
        self.assertEqual(score, 0.0, "BANNED strategy score must be strictly 0.0")

    def test_03_promote_winners_feedback_loop(self):
        winning_trades = [
            {"strategy_id": "STR-001", "market_regime": MarketRegime.STRONG_UPTREND, "pnl": 15.0, "win": True},
            {"strategy_id": "STR-001", "market_regime": MarketRegime.STRONG_UPTREND, "pnl": 12.0, "win": True},
            {"strategy_id": "STR-001", "market_regime": MarketRegime.STRONG_UPTREND, "pnl": 8.0, "win": True},
        ]
        self.rec.update_regime_performance_matrix(winning_trades)
        perf = self.rec.get_regime_performance("STR-001", MarketRegime.STRONG_UPTREND)
        self.assertEqual(perf['status'], "PROMOTED")
        self.assertGreater(perf['weight_multiplier'], 1.2)

        fp = self._mock_fingerprint(MarketRegime.STRONG_UPTREND)
        s1 = self.registry.get_strategy("STR-001")
        score = self.selector._compute_suitability_score(s1, fp)
        self.assertGreaterEqual(score, 90.0, "PROMOTED strategy should receive dominant suitability score")

    def test_04_hysteresis_and_no_trade_mode(self):
        # 1. Test Hysteresis: Prevent rapid flip within minimum bars
        self.selector.current_active_strategy_id = "STR-001"
        self.selector.bars_since_last_switch = 2 # Only 2 bars ago (below 15)

        fp_range = self._mock_fingerprint(MarketRegime.RANGE_BOUND)
        curr = {'close': 3900.0, 'low': 3890.0, 'high': 3910.0, 'vwap': 3900.0, 'sd': 3.5}

        # Should maintain STR-001 to prevent whipsaw
        dec = self.selector.evaluate_and_select(fp_range, curr)
        self.assertEqual(dec['selected_strategy_id'], "STR-001")

        # 2. Advance bars past hysteresis -> now free to switch
        self.selector.bars_since_last_switch = 25
        dec_switch = self.selector.evaluate_and_select(fp_range, curr)
        self.assertIn(dec_switch['selected_strategy_id'], ["STR-002", "STR-010"])

        # 3. Test Mandatory No-Trade mode during extreme spread / uncertainty
        fp_notrade = self._mock_fingerprint(MarketRegime.THIN_LIQUIDITY)
        fp_notrade['microstructure']['spread'] = 1.50 # Extreme spread widening
        dec_notrade = self.selector.evaluate_and_select(fp_notrade, curr)
        self.assertEqual(dec_notrade['selected_strategy_id'], "STR-009")
        self.assertEqual(dec_notrade['action'], "NO_TRADE")

if __name__ == '__main__':
    unittest.main()
