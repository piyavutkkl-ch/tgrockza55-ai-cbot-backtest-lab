"""
Unit & Integration Tests for Phase 3 V5 4-Agent Pipeline & Demo Deployment/Rollback
===================================================================================
Verifies:
1. Permanent Demo #5258778 quarantine guard (rejects live/other accounts).
2. Baseline V2 preservation, V3 REGIME_ADAPTIVE_V5 deployment into live.json, and
   deterministic Auto-Rollback back to V2 when V3 underperforms on forward Demo trades.
3. End-to-end 4-Agent orchestration producing v5_pipeline_state.json, agent_handovers.json,
   and DECISION_LOG.md without touching production state during unit tests.
"""

import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "research"))

from research.demo_deployment_manager import (
    ALLOWED_DEMO_ACCOUNT,
    assert_demo_quarantine,
    load_closed_trades_by_strategy,
    sync_demo_deployment_and_ab,
)
from research.v5_multi_agent_pipeline import run_v5_pipeline


class TestV5MultiAgentAndDeployment(unittest.TestCase):
    def test_01_demo_quarantine_blocks_non_demo(self):
        assert_demo_quarantine(ALLOWED_DEMO_ACCOUNT)
        with self.assertRaises(PermissionError):
            assert_demo_quarantine("9999999")
        with self.assertRaises(PermissionError):
            assert_demo_quarantine("")
        with self.assertRaises(PermissionError):
            assert_demo_quarantine(None)

    def test_02_deploy_v3_and_auto_rollback_to_v2(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_p = Path(tmp)
            live_base = tmp_p / "live"
            xau_dir = live_base / "XAUUSD"
            xau_dir.mkdir(parents=True, exist_ok=True)
            trades_csv = xau_dir / "trades.csv"

            baseline_cfg = {
                "strategy": "DOM_ABSORPTION",
                "placeOrders": True,
                "lots": 0.01,
                "symbols": {"XAUUSD": {"strategy": "DOM_ABSORPTION", "p1": 15, "p2": 0.03, "p3": 2.5, "p4": 2.4}},
            }
            live_json = tmp_p / "live.json"
            live_json.write_text(json.dumps(baseline_cfg), encoding="utf-8")
            state_json = tmp_p / "demo_deployment_state.json"

            # Seed baseline profitable DOM_ABSORPTION trades
            rows = [
                "time,event,id,side,units,price,expected,slippage,latencyMs,spread,stopLoss,pUp,reason,gross,commission,swap,net,balance,strategy,regime",
                "2026-11-10 10:00:00,CLOSE,1,Buy,1,3900,3900,0,,0.12,,,TakeProfit,3.00,-0.08,0,2.92,102.92,DOM_ABSORPTION,RANGE",
                "2026-11-10 12:00:00,CLOSE,2,Sell,1,3910,3910,0,,0.12,,,TakeProfit,2.50,-0.08,0,2.42,105.34,DOM_ABSORPTION,RANGE",
                "2026-11-10 14:00:00,CLOSE,3,Buy,1,3905,3905,0,,0.12,,,StopLoss,-1.00,-0.08,0,-1.08,104.26,DOM_ABSORPTION,RANGE",
            ]
            trades_csv.write_text("\n".join(rows) + "\n", encoding="utf-8")

            # Step 1: Deploy V3 REGIME_ADAPTIVE_V5
            st1 = sync_demo_deployment_and_ab(
                deploy_v3_if_baseline=True,
                apply_live_json=True,
                build_verified=True,
                live_base=live_base,
                live_json_path=live_json,
                state_path=state_json,
                account_id=ALLOWED_DEMO_ACCOUNT,
            )
            self.assertEqual(st1["active_strategy_code"], "REGIME_ADAPTIVE_V5")
            self.assertEqual(st1["active_version"], 3)
            self.assertEqual(st1["ab_evaluation"]["verdict"], "COLLECTING_PARALLEL_AB")
            written = json.loads(live_json.read_text(encoding="utf-8"))
            self.assertEqual(written["strategy"], "REGIME_ADAPTIVE_V5")

            # Step 2: Simulate 8 losing trades on REGIME_ADAPTIVE_V5 -> verify Auto-Rollback to V2!
            bad_rows = [
                f"2026-11-17 10:0{k}:00,CLOSE,{10+k},Buy,1,3900,3900,0,,0.12,,,StopLoss,-1.80,-0.08,0,-1.88,100.00,REGIME_ADAPTIVE_V5,LONDON|RANGE"
                for k in range(8)
            ]
            trades_csv.write_text("\n".join(rows + bad_rows) + "\n", encoding="utf-8")

            st2 = sync_demo_deployment_and_ab(
                deploy_v3_if_baseline=False,
                auto_rollback=True,
                apply_live_json=True,
                live_base=live_base,
                live_json_path=live_json,
                state_path=state_json,
                account_id=ALLOWED_DEMO_ACCOUNT,
            )
            self.assertEqual(st2["ab_evaluation"]["verdict"], "AUTO_ROLLBACK")
            self.assertEqual(st2["active_strategy_code"], "DOM_ABSORPTION")
            self.assertEqual(st2["active_version"], 2)
            rolled_back = json.loads(live_json.read_text(encoding="utf-8"))
            self.assertEqual(rolled_back, baseline_cfg)

    def test_03_end_to_end_4agent_pipeline(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_p = Path(tmp)
            docs_data = tmp_p / "docs_data"
            docs_data.mkdir(parents=True, exist_ok=True)
            live_base = tmp_p / "live"
            (live_base / "XAUUSD").mkdir(parents=True, exist_ok=True)
            (live_base / "XAUUSD" / "trades.csv").write_text(
                "time,event,id,side,units,price,expected,slippage,latencyMs,spread,stopLoss,pUp,reason,gross,commission,swap,net,balance,strategy,regime\n",
                encoding="utf-8",
            )
            live_json = tmp_p / "live.json"
            live_json.write_text(json.dumps({"strategy": "DOM_ABSORPTION", "symbols": {}}), encoding="utf-8")
            dec_log = tmp_p / "DECISION_LOG.md"

            (docs_data / "hybrid_data_audit.json").write_text(
                json.dumps({"symbols": {"XAUUSD": {"total_merged_bars": 42000, "ctrader_mcp_online": True, "sanitization_report": {"clean_live_min_rows": 10000, "dropped_incomplete_ghost": 1028}}}}),
                encoding="utf-8",
            )
            (docs_data / "watchdog_status.json").write_text(json.dumps({"symbols": {"XAUUSD": {"status": "LIVE"}}}), encoding="utf-8")
            (docs_data / "papers_database.json").write_text(json.dumps({"papers": [{"id": "P1"}]}), encoding="utf-8")
            (docs_data / "external_alphas.json").write_text(json.dumps({"leads": []}), encoding="utf-8")
            (docs_data / "truth_guard.json").write_text(
                json.dumps({"metrics_empirical": {"current_balance": 120.76, "total_closed_trades_N": 125, "net_pnl_usd": 20.76, "profit_factor": 1.17}}),
                encoding="utf-8",
            )
            (docs_data / "regime_strategy_matrix.json").write_text(
                json.dumps(
                    {
                        "symbols": {
                            "XAUUSD": {
                                "status": "COMPLETED",
                                "data_window": {"live_rich_bars": 10000},
                                "regime_strategy_matrix": [
                                    {"session_zone": "LONDON", "macro_regime": "RANGE", "recommended_action": "DEPLOY_ADAPTIVE", "verdict_th": "LONDON · RANGE OK"}
                                ],
                                "blowup_forensics": {"total_severe_events": 3, "zero_sl_events": 2, "top_cases": [{"strategy_id": "STR-003", "entry_zone": "LONDON_TO_NY", "worst_zone": "LONDON_TO_NY", "mae_atr": 19.2, "diagnosis": "ROLLOVER_SPREAD_OR_THIN_LIQUIDITY"}]},
                            }
                        }
                    }
                ),
                encoding="utf-8",
            )

            out = run_v5_pipeline(
                deploy_v3=True,
                apply_live_json=True,
                build_verified=True,
                docs_data_dir=docs_data,
                decision_log_path=dec_log,
                live_base=live_base,
                live_json_path=live_json,
                account_id=ALLOWED_DEMO_ACCOUNT,
            )

            self.assertEqual(out["stages"]["agent_1_collector_merger"]["total_merged_bars"], 42000)
            self.assertEqual(out["stages"]["agent_2_research_hunter"]["zero_sl_forensic_cases"], 2)
            self.assertEqual(out["stages"]["agent_3_evolver_validator"]["oos_passed_cells"], 1)
            self.assertEqual(out["stages"]["agent_4_audit_demo_deploy"]["active_strategy_code"], "REGIME_ADAPTIVE_V5")
            self.assertTrue(dec_log.exists())
            self.assertIn("DEC-V5-002", dec_log.read_text(encoding="utf-8"))
            self.assertTrue((docs_data / "agent_handovers.json").exists())
            self.assertTrue((docs_data / "v5_pipeline_state.json").exists())

    def test_04_dedup_echoed_close_and_overflow_cols(self):
        with tempfile.TemporaryDirectory() as tmp:
            live_base = Path(tmp) / "live"
            xau_dir = live_base / "XAUUSD"
            xau_dir.mkdir(parents=True, exist_ok=True)
            # Legacy 18-column header + duplicate position ID + 20-col appended V3 row
            csv_rows = [
                "time,event,id,side,units,price,expected,slippage,latencyMs,spread,stopLoss,pUp,reason,gross,commission,swap,net,balance",
                "2026-11-16 15:58:10,CLOSE,263218950,Buy,1,3858.97,3858.80,-0.17,,0.13,,,Closed,-2.10,-0.08,0.00,-2.18,116.15",
                "2026-11-16 15:58:10,CLOSE,263218950,Buy,1,3858.97,,,,0.12,,,Closed,-2.10,-0.08,0.00,-2.18,116.15",
                "2026-11-16 16:40:00,CLOSE,263999001,Buy,1,3865.00,3865.00,0,,0.11,,,TakeProfit,4.50,-0.08,0.00,4.42,120.57,REGIME_ADAPTIVE_V5,LONDON|RANGE",
            ]
            (xau_dir / "trades.csv").write_text("\n".join(csv_rows) + "\n", encoding="utf-8")

            summary = load_closed_trades_by_strategy(live_base=live_base)
            self.assertEqual(summary["DOM_ABSORPTION"]["trades"], 1)
            self.assertAlmostEqual(summary["DOM_ABSORPTION"]["net_pnl_usd"], -2.18)
            self.assertEqual(summary["REGIME_ADAPTIVE_V5"]["trades"], 1)
            self.assertAlmostEqual(summary["REGIME_ADAPTIVE_V5"]["net_pnl_usd"], 4.42)


if __name__ == "__main__":
    unittest.main()
