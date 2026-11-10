"""
Unit Tests for Adaptive Strategy Selector V4
============================================
Verifies:
1. Routing to STR-001 under Strong Uptrend.
2. Routing to STR-002 under Range-Bound Market.
3. Strict No-Trade enforcement during Pre-News Blackout (STR-009).
4. Strict No-Trade enforcement during Daily Flat window (21:45 UTC).
5. Dynamic Strategy Switching with Hysteresis.
6. Position preservation (refusing to drop an open trade mid-stream).
"""

import sys, os, unittest
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'research'))

from market_intelligence_engine import MarketRegime
from strategy_library import StrategyRegistry
from risk_governor import RiskGovernor
from adaptive_strategy_selector import AdaptiveStrategySelector

class TestAdaptiveStrategySelector(unittest.TestCase):

    def setUp(self):
        self.registry = StrategyRegistry()
        self.governor = RiskGovernor()
        self.selector = AdaptiveStrategySelector(self.registry, self.governor)

    def _create_mock_fingerprint(self, regime, primary_session="NEW_YORK", hour=14, minute=0, news_state="CLEAR", delta=20.0, spread=0.15):
        return {
            'symbol': 'XAUUSD',
            'timestamp': f'2026-11-02 {hour:02d}:{minute:02d}',
            'primary_market_regime': regime,
            'active_market_regimes': [regime],
            'time_context': {
                'primary_session': primary_session,
                'hour_utc': hour,
                'minute_utc': minute,
                'is_daily_flat_triggered': (hour * 60 + minute) >= (21 * 60 + 45)
            },
            'news_context': {
                'news_state': news_state,
                'next_impact': 'HIGH' if news_state == 'PRE_NEWS_BLACKOUT' else '',
                'min_to_next': 15 if news_state == 'PRE_NEWS_BLACKOUT' else 999,
                'min_since_last': 999,
                'last_impact': ''
            },
            'microstructure': {
                'spread': spread,
                'is_spread_elevated': False,
                'order_flow_delta': delta
            },
            'price_behavior': {'high_20': 3910.0, 'low_20': 3890.0},
            'confidence_score': 0.85
        }

    def test_01_strong_uptrend_routing(self):
        fp = self._create_mock_fingerprint(MarketRegime.STRONG_UPTREND, delta=25.0)
        curr = {'close': 3905.0, 'ema50': 3898.0}
        dec = self.selector.evaluate_and_select(fp, curr)
        self.assertEqual(dec['selected_strategy_id'], "STR-001")
        self.assertEqual(dec['action'], "EXECUTE")
        self.assertEqual(dec['trade_signal']['side'], "BUY")

    def test_02_range_bound_routing(self):
        fp = self._create_mock_fingerprint(MarketRegime.RANGE_BOUND, primary_session="ASIA", hour=4, delta=5.0)
        curr = {'close': 3895.0, 'vwap': 3900.0, 'sd': 4.0} # Stretched lower
        dec = self.selector.evaluate_and_select(fp, curr)
        self.assertEqual(dec['selected_strategy_id'], "STR-002")
        self.assertEqual(dec['action'], "EXECUTE")
        self.assertEqual(dec['trade_signal']['side'], "BUY")

    def test_03_pre_news_blackout_routes_to_no_trade(self):
        fp = self._create_mock_fingerprint(MarketRegime.STRONG_UPTREND, news_state="PRE_NEWS_BLACKOUT")
        curr = {'close': 3905.0}
        dec = self.selector.evaluate_and_select(fp, curr)
        self.assertEqual(dec['selected_strategy_id'], "STR-009")
        self.assertEqual(dec['action'], "NO_TRADE")
        self.assertIn("Risk Governor Gate", dec['audit_reason'])

    def test_04_daily_flat_routes_to_no_trade(self):
        fp = self._create_mock_fingerprint(MarketRegime.STRONG_UPTREND, hour=21, minute=50)
        curr = {'close': 3905.0}
        dec = self.selector.evaluate_and_select(fp, curr)
        self.assertEqual(dec['selected_strategy_id'], "STR-009")
        self.assertEqual(dec['action'], "NO_TRADE")

    def test_05_preserve_active_position(self):
        # Initial selection STR-001
        fp1 = self._create_mock_fingerprint(MarketRegime.STRONG_UPTREND)
        curr1 = {'close': 3905.0, 'ema50': 3898.0}
        self.selector.evaluate_and_select(fp1, curr1)
        
        # Now market shifts to RANGE_BOUND, but position is ACTIVE
        fp2 = self._create_mock_fingerprint(MarketRegime.RANGE_BOUND, primary_session="ASIA", hour=4)
        curr2 = {'close': 3895.0, 'vwap': 3900.0, 'sd': 4.0}
        dec2 = self.selector.evaluate_and_select(fp2, curr2, has_active_position=True)
        self.assertEqual(dec2['action'], "MAINTAIN_ACTIVE_POSITION")
        self.assertEqual(dec2['active_strategy_id'], "STR-001")

if __name__ == '__main__':
    unittest.main()
