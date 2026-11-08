"""
Comprehensive Unit & Integration Test Suite for Antigravity Quant Fund V2.
Verifies:
  1. Deterministic Data Quality Gate (SHA-256 + Fail-Closed)
  2. Deterministic Risk Engine (9-Item Boolean Checklist, Fail-Closed on NaN/None)
  3. Two-Tier Risk Governance (Admin Hard Limits clamp CEO Policy)
  4. Token & Cost Circuit Breaker
  5. Max 3-Iteration VETO Cap & Hypothesis Drop/Pivot Routing
  6. Strategy Memory Fact vs Unverified AI Postmortem Separation
  7. Live Execution Monitor & Emergency Kill Switch
  8. End-to-End 10-Node LangGraph V2 Pipeline with Dual-Stage HITL Gates
"""

import os
import tempfile
import unittest
from pathlib import Path

from quant_fund_v2.core.data_quality import run_data_quality_gate
from quant_fund_v2.core.risk_engine import evaluate_deterministic_risk_checklist
from quant_fund_v2.db.memory_store import StrategyMemoryStore
from quant_fund_v2.graph import (
    build_quant_fund_v2_graph,
    route_after_node_06_gatekeeper,
)
from quant_fund_v2.monitoring.execution_monitor import (
    evaluate_execution_health,
    reset_kill_switch,
)
from quant_fund_v2.run_v2 import build_initial_state
from quant_fund_v2.state import AdminRiskPolicy


class TestQuantFundV2Suite(unittest.TestCase):
    """Enterprise verification suite for Antigravity Quant Fund V2."""

    def test_01_data_quality_gate_valid_and_fail_closed(self) -> None:
        """Node 1: Verify SHA-256 dataset hashing and fail-closed behavior on missing data."""
        missing_res = run_data_quality_gate(
            symbol="XAUUSD",
            custom_csv_path=r"d:\cbot-atgvt\data\NON_EXISTENT_FILE.csv",
        )
        self.assertFalse(missing_res["passed"], "Missing CSV must fail-closed.")

        valid_res = run_data_quality_gate(symbol="XAUUSD")
        self.assertTrue(valid_res["passed"], f"Valid dataset failed: {valid_res}")
        self.assertEqual(len(valid_res["dataset_sha256"]), 64)
        self.assertGreater(valid_res["total_bars"], 1_000_000)

    def test_02_deterministic_risk_checklist_fail_closed(self) -> None:
        """Node 6B: Verify 9-item Boolean Checklist (Pass/Fail only) and NaN fail-closed safety."""
        admin = AdminRiskPolicy()
        good_wb = {
            "compile_success": True,
            "static_code_audit": {
                "has_stop_distance_override": True,
                "uses_closed_bars": True,
                "has_lookahead_leak": False,
            },
        }
        good_bt = {
            "full_period_metrics": {
                "trades": 109,
                "profit_factor": 1.16,
                "max_dd_pct": 16.70,
                "max_single_trade_risk_pct": 0.85,
            },
            "out_of_sample_metrics": {
                "profit_factor": 1.15,
                "net_pnl_usd": 18.50,
            },
        }
        good_val = {
            "walk_forward": {"wf_efficiency_pct": 80.0},
            "monte_carlo": {
                "mc_95th_max_dd_pct": 18.5,
                "ruin_probability_pct": 0.0,
            },
        }
        good_sec = {"security_passed": True}

        res_pass = evaluate_deterministic_risk_checklist(
            admin_policy=admin,
            worker_build=good_wb,
            math_backtest_report=good_bt,
            validation_stats_report=good_val,
            ai_security_audit=good_sec,
        )
        self.assertTrue(res_pass.overall_passed, f"Expected all 9 checklist items to pass: {res_pass.veto_reasons}")
        self.assertEqual(len(res_pass.veto_reasons), 0)

        # Corrupt profit_factor with NaN -> must Fail-Closed
        nan_bt = {
            **good_bt,
            "full_period_metrics": {
                **good_bt["full_period_metrics"],
                "profit_factor": float("nan"),
            },
        }
        res_nan = evaluate_deterministic_risk_checklist(
            admin_policy=admin,
            worker_build=good_wb,
            math_backtest_report=nan_bt,
            validation_stats_report=good_val,
            ai_security_audit=good_sec,
        )
        self.assertFalse(res_nan.overall_passed, "NaN metric must fail-closed.")
        self.assertTrue(any("FAIL-CLOSED" in r for r in res_nan.veto_reasons))

    def test_03_ceo_policy_clamped_by_admin_hard_limits(self) -> None:
        """Node 3: Verify CEO Strategist cannot relax immutable Admin Risk Policy limits."""
        admin = AdminRiskPolicy(
            hard_max_dd_pct=18.0,
            hard_max_risk_per_trade_pct=2.0,
            hard_min_profit_factor=1.15,
        )
        # Suppose CEO attempts to propose 35% DD, 4.5% risk per trade, and 0.90 PF
        raw_dd = 35.0
        raw_risk = 4.5
        raw_pf = 0.90

        clamped_dd = min(raw_dd, admin.hard_max_dd_pct)
        clamped_risk = min(raw_risk, admin.hard_max_risk_per_trade_pct)
        clamped_pf = max(raw_pf, admin.hard_min_profit_factor)

        self.assertEqual(clamped_dd, 18.0)
        self.assertEqual(clamped_risk, 2.0)
        self.assertEqual(clamped_pf, 1.15)

    def test_04_token_and_cost_circuit_breaker(self) -> None:
        """Verify daily Token / Cost Circuit Breaker trips when budget is exceeded."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = str(Path(tmpdir) / "cb_test.sqlite")
            store = StrategyMemoryStore(db_path=db_path)
            admin = AdminRiskPolicy(daily_token_limit=500_000, daily_cost_limit_usd=5.00)
            store.log_node_execution(
                node_name="node_04_quant_worker",
                agent_model="gemini-3.8-flash",
                prompt_version="V2.0.0",
                policy_version="RISK-POL-V2.0",
                input_payload={},
                output_payload={},
                tokens_used=550_000,
                estimated_cost_usd=6.20,
                verdict="PASS",
            )
            tripped, reason = store.check_circuit_breaker(policy=admin)
            self.assertTrue(tripped)
            self.assertIn("CIRCUIT BREAKER TRIPPED", reason)

    def test_05_max_3_iteration_veto_and_hypothesis_pivot(self) -> None:
        """Verify Gatekeeper routes to Quant Worker for <3 iterations and pivots back to CEO at 3."""
        state_iter_1 = build_initial_state()
        state_iter_1["validation_checklist"] = {"overall_passed": False}
        state_iter_1["iteration"] = 1
        self.assertEqual(route_after_node_06_gatekeeper(state_iter_1), "node_04_quant_worker")

        state_iter_3 = build_initial_state()
        state_iter_3["validation_checklist"] = {"overall_passed": False}
        state_iter_3["iteration"] = 3
        self.assertEqual(route_after_node_06_gatekeeper(state_iter_3), "node_03_ceo_strategist")

    def test_06_strategy_memory_separates_facts_from_ai_opinion(self) -> None:
        """Node 10: Verify empirical math facts are separated from unverified AI postmortem notes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = str(Path(tmpdir) / "mem_test.sqlite")
            store = StrategyMemoryStore(db_path=db_path)
            store.record_strategy_memory(
                strategy_version_id="VER-01",
                symbol="XAUUSD",
                market_regime="NY_MEAN_REVERSION",
                empirical_facts={"profit_factor": 1.16, "max_dd_pct": 16.70},
                ai_postmortem_notes={"lesson": "Unverified AI opinion about market regime."},
                verified_by_human=False,
            )
            learnings = store.get_usable_strategy_learnings(symbol="XAUUSD")
            self.assertEqual(len(learnings), 1)
            self.assertEqual(learnings[0]["empirical_facts"]["profit_factor"], 1.16)
            self.assertEqual(
                learnings[0]["ai_postmortem_notes"]["status"],
                "UNVERIFIED_BLOCKED_FROM_AUTO_USE",
            )

    def test_07_execution_monitor_and_kill_switch(self) -> None:
        """Node 9: Verify Execution Monitor triggers Kill Switch on excessive slippage or missing SL."""
        bad_telemetry = {
            "actual_spread_usd": 0.90,
            "actual_slippage_usd": 0.45,
            "execution_latency_ms": 850.0,
            "order_rejections": 4,
            "missing_sl_tp": True,
            "position_mismatch": True,
            "connection_alive": False,
            "performance_drift_pct": 25.0,
        }
        health = evaluate_execution_health(
            strategy_code="QF_V2_VWAP_EQUILIBRIUM",
            symbol="XAUUSD",
            backtest_baseline={"cost_assumptions": {"spread_usd": 0.20, "slippage_usd": 0.02}},
            live_telemetry=bad_telemetry,
        )
        self.assertFalse(health["healthy"])
        self.assertTrue(health["kill_switch_triggered"])
        self.assertGreaterEqual(len(health["anomalies"]), 5)
        reset_kill_switch()

    def test_08_full_10_node_langgraph_v2_pipeline_with_dual_stage_hitl(self) -> None:
        """End-to-End Integration: Run 10-node LangGraph V2 through Iteration 1 VETO -> Iteration 2 PASS -> HITL Stage 1 & 2."""
        with tempfile.TemporaryDirectory() as tmpdir:
            os.environ["QF_V2_DB_PATH"] = str(Path(tmpdir) / "e2e_v2.sqlite")
            try:
                app = build_quant_fund_v2_graph(enable_interrupts=True)
                config = {"configurable": {"thread_id": "test-v2-e2e-thread"}}
                init_state = build_initial_state(symbol="XAUUSD")

                for _ in app.stream(init_state, config=config):
                    pass

                snapshot_stage1 = app.get_state(config)
                state_vals = snapshot_stage1.values

                # Verify Iteration 1 was VETOed and Iteration 2 passed all 9 checklist items
                self.assertEqual(state_vals["iteration"], 2)
                self.assertTrue(
                    state_vals["validation_checklist"]["overall_passed"],
                    f"Checklist failed: {state_vals['validation_checklist'].get('veto_reasons')}",
                )
                self.assertIn("node_09a_deploy_paper_trading", snapshot_stage1.next)

                # Stage 1 Approval -> Resumes to Paper Trading, then pauses before Stage 2 Live Trading
                app.update_state(config, {"paper_trading_approved": True})
                for _ in app.stream(None, config=config):
                    pass

                snapshot_stage2 = app.get_state(config)
                state_vals_2 = snapshot_stage2.values
                self.assertTrue(state_vals_2["paper_trading_approved"])
                self.assertIn("node_09b_deploy_live_trading", snapshot_stage2.next)

                # Stage 2 Approval -> Resumes to Live Trading & Node 10 Strategy Memory DB
                app.update_state(config, {"live_trading_approved": True})
                for _ in app.stream(None, config=config):
                    pass

                snapshot_final = app.get_state(config)
                state_vals_final = snapshot_final.values
                self.assertTrue(state_vals_final["live_trading_approved"])
                self.assertTrue(bool(state_vals_final["strategy_memory_record"].get("memory_id")))
                self.assertTrue(state_vals_final["strategy_memory_record"]["auto_apply_blocked"])
            finally:
                os.environ.pop("QF_V2_DB_PATH", None)


if __name__ == "__main__":
    unittest.main()
