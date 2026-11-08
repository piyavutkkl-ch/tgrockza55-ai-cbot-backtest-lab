"""
Node 6B: Deterministic Python Risk Engine (Fail-Closed Boolean Checklist).
Replaces legacy AI 0-100 scoring with strict mathematical and rule-based validation.
"""

import math
from typing import Any, Dict, List
from ..state import AdminRiskPolicy, ValidationChecklistResult


def _is_valid_number(val: Any) -> bool:
    if val is None or isinstance(val, bool):
        return False
    try:
        f = float(val)
        return not (math.isnan(f) or math.isinf(f))
    except Exception:
        return False


def evaluate_deterministic_risk_checklist(
    admin_policy: AdminRiskPolicy,
    worker_build: Dict[str, Any],
    math_backtest_report: Dict[str, Any],
    validation_stats_report: Dict[str, Any],
    ai_security_audit: Dict[str, Any],
) -> ValidationChecklistResult:
    """
    Evaluates the 9 mandatory Boolean Checklist Gates (`CHK-01` through `CHK-09`).
    Fail-Closed Guarantee: If any required metric is missing, NaN, or raises an exception,
    the checklist immediately returns `overall_passed = False` (VETO).
    """
    veto_reasons: List[str] = []
    remediation: List[str] = []

    try:
        static_audit = worker_build.get("static_code_audit", {})
        compile_ok = bool(worker_build.get("compile_success", False))
        full_m = math_backtest_report.get("full_period_metrics", {})
        oos_m = math_backtest_report.get("out_of_sample_metrics", {})
        wf = validation_stats_report.get("walk_forward", {})
        mc = validation_stats_report.get("monte_carlo", {})

        # Verify numeric integrity (Fail-Closed on NaN/None)
        required_nums = [
            full_m.get("profit_factor"),
            full_m.get("max_dd_pct"),
            full_m.get("max_single_trade_risk_pct"),
            oos_m.get("profit_factor"),
            oos_m.get("net_pnl_usd"),
            wf.get("wf_efficiency_pct"),
            mc.get("mc_95th_max_dd_pct"),
            mc.get("ruin_probability_pct"),
        ]
        if not all(_is_valid_number(x) for x in required_nums):
            return ValidationChecklistResult(
                overall_passed=False,
                veto_reasons=["FAIL-CLOSED: Missing, None, or NaN metric in Backtest/Validation report."],
                remediation_directives=["Ensure Backtest & Validation Engine outputs valid finite numeric metrics."],
            )

        # CHK-01: Hard Stop Loss in C# & Compilation Passed
        chk_01 = compile_ok and bool(static_audit.get("has_stop_distance_override", False))
        if not chk_01:
            veto_reasons.append("CHK-01 FAILED: C# strategy missing `override double? StopDistance` or failed compilation.")
            remediation.append("Implement `public override double? StopDistance(TradeType side)` returning clamped ATR stop.")

        # CHK-02: Risk per Trade within Admin Hard Limit
        max_trade_risk = float(full_m["max_single_trade_risk_pct"])
        chk_02 = (0.0 < max_trade_risk <= admin_policy.hard_max_risk_per_trade_pct) and int(full_m.get("trades", 0)) > 0
        if not chk_02:
            veto_reasons.append(
                f"CHK-02 FAILED: Max risk per trade is {max_trade_risk:.2f}%, exceeding hard limit {admin_policy.hard_max_risk_per_trade_pct:.2f}%."
            )
            remediation.append(f"Enable Volatility-Targeted Risk Capping (`max_risk_usd <= {admin_policy.hard_max_risk_per_trade_pct * 0.5:.2f}`).")

        # CHK-03: Max Drawdown within Admin Hard Limit
        max_dd = float(full_m["max_dd_pct"])
        chk_03 = max_dd <= admin_policy.hard_max_dd_pct and int(full_m.get("trades", 0)) > 0
        if not chk_03:
            veto_reasons.append(
                f"CHK-03 FAILED: Max Drawdown is {max_dd:.2f}%, exceeding Admin hard limit {admin_policy.hard_max_dd_pct:.2f}%."
            )
            remediation.append("Reduce position risk scaling and filter low-probability entries to bring Max DD under 18%.")

        # CHK-04: Full-Period Profit Factor >= Admin Minimum
        pf = float(full_m["profit_factor"])
        chk_04 = pf >= admin_policy.hard_min_profit_factor
        if not chk_04:
            veto_reasons.append(
                f"CHK-04 FAILED: Net Profit Factor is {pf:.2f}, below Admin minimum {admin_policy.hard_min_profit_factor:.2f}."
            )
            remediation.append("Increase SD stretch threshold to >= 4.2 and exit at Session VWAP touch (`VWAP_TOUCH`).")

        # CHK-05: Out-of-Sample (OOS) Profitable
        oos_pf = float(oos_m["profit_factor"])
        oos_pnl = float(oos_m["net_pnl_usd"])
        chk_05 = (oos_pf >= admin_policy.hard_min_oos_pf) and (oos_pnl > 0.0)
        if not chk_05:
            veto_reasons.append(
                f"CHK-05 FAILED: Out-of-Sample PF={oos_pf:.2f} (min {admin_policy.hard_min_oos_pf:.2f}), OOS Net PnL=${oos_pnl:+.2f}."
            )
            remediation.append("Enable News & Volatility Void Gate (`max_atr_bar = 2.0`) to protect OOS performance.")

        # CHK-06: Walk-Forward Efficiency
        wf_eff = float(wf["wf_efficiency_pct"])
        chk_06 = wf_eff >= admin_policy.hard_min_wf_efficiency_pct
        if not chk_06:
            veto_reasons.append(
                f"CHK-06 FAILED: Walk-Forward Efficiency is {wf_eff:.1f}% (< {admin_policy.hard_min_wf_efficiency_pct:.1f}% required)."
            )
            remediation.append("Restrict entries to high-liquidity NY session (13:00-17:00 UTC) for multi-year consistency.")

        # CHK-07: Monte Carlo 1,000-Run Stress Test
        mc_dd = float(mc["mc_95th_max_dd_pct"])
        mc_ruin = float(mc["ruin_probability_pct"])
        chk_07 = (mc_dd <= admin_policy.hard_max_mc_95_dd_pct) and (mc_ruin <= admin_policy.hard_max_mc_ruin_prob_pct)
        if not chk_07:
            veto_reasons.append(
                f"CHK-07 FAILED: Monte Carlo 95% DD={mc_dd:.2f}% (limit {admin_policy.hard_max_mc_95_dd_pct:.2f}%), Ruin Prob={mc_ruin:.2f}%."
            )

        # CHK-08: Zero Look-Ahead Bias Verified
        chk_08 = bool(static_audit.get("uses_closed_bars", False)) and not bool(static_audit.get("has_lookahead_leak", True))
        if not chk_08:
            veto_reasons.append("CHK-08 FAILED: Look-ahead bias detected in C# bar indexing (`.Last(0)` used instead of `.Last(1)`).")

        # CHK-09: AI Argon Code Security Audit
        chk_09 = bool(ai_security_audit.get("security_passed", False))
        if not chk_09:
            veto_reasons.append(f"CHK-09 FAILED: AI Security Audit rejected code: {ai_security_audit.get('audit_notes')}")

        overall = all([chk_01, chk_02, chk_03, chk_04, chk_05, chk_06, chk_07, chk_08, chk_09])

        return ValidationChecklistResult(
            has_hard_stop_loss=chk_01,
            risk_per_trade_within_limit=chk_02,
            max_dd_within_limit=chk_03,
            pf_above_minimum=chk_04,
            oos_profitable=chk_05,
            walk_forward_passed=chk_06,
            monte_carlo_passed=chk_07,
            no_lookahead_bias_verified=chk_08,
            ai_security_audit_passed=chk_09,
            overall_passed=overall,
            veto_reasons=veto_reasons,
            remediation_directives=remediation,
        )
    except Exception as ex:
        return ValidationChecklistResult(
            overall_passed=False,
            veto_reasons=[f"FAIL-CLOSED EXCEPTION in Deterministic Risk Engine: {ex}"],
            remediation_directives=["Fix exception in risk evaluation inputs."],
        )
