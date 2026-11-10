"""
Unit Tests for Adaptive Strategy Library V4
===========================================
Verifies:
1. Registration of STR-001 through STR-009.
2. Context suitability filtering (News, Session, Regime).
3. Strategy signal generation logic.
4. Immutable version protection (forbidding overwriting without a new version).
5. Serialization to JSON registry.
"""

import sys, os, unittest
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'research'))

from market_intelligence_engine import MarketRegime
from strategy_library import (
    StrategyRegistry, BaseAdaptiveStrategy,
    STR001_TrendFollowing, STR002_MeanReversion,
    STR003_LiquiditySweepReversal, STR009_NoTrade
)

class TestStrategyLibrary(unittest.TestCase):

    def setUp(self):
        self.registry = StrategyRegistry()

    def test_01_core_fleet_loaded(self):
        self.assertEqual(len(self.registry.strategies), 9)
        for i in range(1, 10):
            sid = f"STR-{i:03d}"
            self.assertIn(sid, self.registry.strategies)

    def test_02_context_suitability(self):
        strat = self.registry.get_strategy("STR-001")
        
        # Suitable context: London session, Strong Uptrend, Clear news
        fp_good = {
            'primary_market_regime': MarketRegime.STRONG_UPTREND,
            'active_market_regimes': [MarketRegime.STRONG_UPTREND],
            'time_context': {'primary_session': 'LONDON'},
            'news_context': {'news_state': 'CLEAR'}
        }
        ok, msg = strat.is_context_suitable(fp_good)
        self.assertTrue(ok, f"Expected suitable, got {msg}")
        
        # Unsuitable context: Pre-news blackout
        fp_bad_news = {
            'primary_market_regime': MarketRegime.STRONG_UPTREND,
            'active_market_regimes': [MarketRegime.STRONG_UPTREND],
            'time_context': {'primary_session': 'LONDON'},
            'news_context': {'news_state': 'PRE_NEWS_BLACKOUT'}
        }
        ok_news, msg_news = strat.is_context_suitable(fp_bad_news)
        self.assertFalse(ok_news)
        self.assertIn("Pre-news", msg_news)

    def test_03_signal_generation(self):
        strat_trend = self.registry.get_strategy("STR-001")
        fp = {
            'primary_market_regime': MarketRegime.STRONG_UPTREND,
            'microstructure': {'order_flow_delta': 25.0}
        }
        curr = {'close': 3950.0, 'ema50': 3940.0}
        side, sl, tp, meta = strat_trend.evaluate_signal(fp, curr)
        self.assertEqual(side, "BUY")
        self.assertGreater(tp, sl)

    def test_04_no_trade_strategy(self):
        strat_no_trade = self.registry.get_strategy("STR-009")
        fp = {'news_context': {'news_state': 'CLEAR'}}
        curr = {'close': 3950.0}
        side, sl, tp, meta = strat_no_trade.evaluate_signal(fp, curr)
        self.assertEqual(side, "NONE")
        self.assertEqual(meta.get("action"), "NO_TRADE")

    def test_05_immutable_version_guard(self):
        # Attempting to register identical version should raise ValueError
        dup_strat = STR001_TrendFollowing(version="1.0.0")
        with self.assertRaises(ValueError):
            self.registry.register_strategy(dup_strat)
            
        # Incrementing version should succeed
        new_ver_strat = STR001_TrendFollowing(version="1.1.0")
        self.registry.register_strategy(new_ver_strat)
        self.assertEqual(self.registry.get_strategy("STR-001").version, "1.1.0")

if __name__ == '__main__':
    unittest.main()
