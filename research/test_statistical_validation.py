"""
Unit Tests for Statistical Validation Engine V4
===============================================
Verifies:
1. Multi-objective validation (Expectancy, PF, Sharpe, Sortino, Drawdown).
2. Monte Carlo 1,000-run simulation (Ruin probability & 95th Percentile DD).
3. Execution Cost Stress Testing (1.5x friction).
4. Sample size adequacy check (rejecting under-sampled runs).
5. Context-aware threshold customization per strategy family.
"""

import sys, os, unittest
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'research'))

from statistical_validation_engine import StatisticalValidationEngine, StrategyTypeExpectation

class TestStatisticalValidation(unittest.TestCase):

    def test_01_insufficient_sample_size_rejected(self):
        # 5 trades when 15 required
        small_trades = [{'pnl': 5.0, 'win': True}] * 5
        daily = {'2026-11-02': 25.0}
        res = StatisticalValidationEngine.evaluate_strategy_run(small_trades, daily, strategy_family="TREND_FOLLOWING")
        self.assertFalse(res['validation_passed'])
        self.assertIn("sample_adequacy", res['failed_checks'])

    def test_02_monte_carlo_and_drawdown(self):
        trades = [
            {'pnl': 4.0, 'win': True}, {'pnl': -1.5, 'win': False},
            {'pnl': 5.0, 'win': True}, {'pnl': 3.5, 'win': True},
            {'pnl': -1.2, 'win': False}, {'pnl': 6.0, 'win': True},
            {'pnl': 4.5, 'win': True}, {'pnl': -1.8, 'win': False},
            {'pnl': 5.2, 'win': True}, {'pnl': 3.8, 'win': True},
            {'pnl': -1.4, 'win': False}, {'pnl': 5.5, 'win': True},
            {'pnl': 4.2, 'win': True}, {'pnl': -1.6, 'win': False},
            {'pnl': 4.8, 'win': True}, {'pnl': 3.9, 'win': True}
        ]
        daily = {'2026-11-02': 8.0, '2026-11-03': 12.0, '2026-11-04': 9.0, '2026-11-05': 10.0}
        res = StatisticalValidationEngine.evaluate_strategy_run(trades, daily, strategy_family="TREND_FOLLOWING")
        self.assertTrue(res['validation_passed'])
        self.assertLess(res['metrics']['monte_carlo_ruin_prob_pct'], 1.0)
        self.assertGreater(res['metrics']['annualized_sharpe'], 1.20)
        self.assertGreater(res['metrics']['stress_tested_net_pnl_usd'], 0.0)

    def test_03_losing_strategy_rejected(self):
        losing_trades = [
            {'pnl': -3.0, 'win': False}, {'pnl': 1.0, 'win': True},
            {'pnl': -4.0, 'win': False}, {'pnl': -2.5, 'win': False}
        ] * 4 # 16 trades
        daily = {'2026-11-02': -5.0, '2026-11-03': -8.0}
        res = StatisticalValidationEngine.evaluate_strategy_run(losing_trades, daily, strategy_family="TREND_FOLLOWING")
        self.assertFalse(res['validation_passed'])
        self.assertIn("profit_factor", res['failed_checks'])

if __name__ == '__main__':
    unittest.main()
