"""
Autonomous Demo Deployment, A/B Evaluator & Auto-Rollback Manager (Phase 3 — V5)
================================================================================
Enforces System Rules V5 (Pre-Edit Authority & Category 5):
1. Demo Quarantine (#5258778): Strictly prohibits deployment to any live or unknown
   account; only Pepperstone Demo #5258778 is permitted.
2. Preserves exact Baseline Rollback Config (DOM_ABSORPTION V2) before deploying V3
   (REGIME_ADAPTIVE_V5) into live.json.
3. Reads real closed Demo trades from %LOCALAPPDATA%\\BacktestLab\\live\\*\\trades.csv
   and performs empirical A/B comparison (REGIME_ADAPTIVE_V5 vs DOM_ABSORPTION).
4. Triggers deterministic Auto-Rollback back to DOM_ABSORPTION V2 whenever the
   challenger underperforms the baseline after forward sampling or hits emergency DD.
"""

from __future__ import annotations

import csv
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

ALLOWED_DEMO_ACCOUNT = "5258778"
SYMBOLS = ("BTCUSD", "ETHUSD", "XAUUSD")


def resolve_live_json_path() -> Path:
    one_drive = Path.home() / "OneDrive" / "เอกสาร" / "BacktestLab" / "live.json"
    if one_drive.exists():
        return one_drive
    docs_fallback = Path.home() / "Documents" / "BacktestLab" / "live.json"
    return one_drive if one_drive.parent.exists() else docs_fallback


def resolve_cli_account() -> Optional[str]:
    for base in (
        Path.home() / "OneDrive" / "เอกสาร" / "BacktestLab" / "cli.json",
        Path.home() / "Documents" / "BacktestLab" / "cli.json",
    ):
        if base.exists():
            try:
                cfg = json.loads(base.read_text(encoding="utf-8-sig"))
                return str(cfg.get("account", "")).strip()
            except Exception:
                return None
    return None


def assert_demo_quarantine(account_id: Optional[str]) -> None:
    """Rejects any deployment if target account is not verified Demo #5258778."""
    if str(account_id or "").strip() != ALLOWED_DEMO_ACCOUNT:
        raise PermissionError(
            f"Demo Quarantine Violation: expected account #{ALLOWED_DEMO_ACCOUNT}, got {account_id!r}"
        )


def _safe_float(val: Any, default: float = 0.0) -> float:
    try:
        return float(val) if val not in (None, "") else default
    except (ValueError, TypeError):
        return default


def load_closed_trades_by_strategy(live_base: Optional[Path] = None) -> Dict[str, Any]:
    """
    Parses all CLOSE events from %LOCALAPPDATA%\\BacktestLab\\live\\*\\trades.csv,
    deduplicates parallel desktop/CLI echoes by (symbol, position_id), and handles
    both 20-column headers and legacy 18-column files with appended extra columns.
    """
    base = live_base or (Path.home() / "AppData" / "Local" / "BacktestLab" / "live")
    by_strat: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

    for sym in SYMBOLS:
        tf = base / sym / "trades.csv"
        if not tf.exists():
            continue
        seen_ids = set()
        with tf.open("r", encoding="utf-8", errors="replace") as f:
            for row in csv.DictReader(f):
                if str(row.get("event", "")).upper() != "CLOSE":
                    continue
                pos_id = str(row.get("id", "") or "").strip()
                if pos_id:
                    if pos_id in seen_ids:
                        continue
                    seen_ids.add(pos_id)

                extra = row.get(None) or []
                raw_strat = row.get("strategy") or (extra[0] if len(extra) >= 1 else "")
                raw_reg = row.get("regime") or (extra[1] if len(extra) >= 2 else "")
                strat = str(raw_strat or "DOM_ABSORPTION").strip()
                net = _safe_float(row.get("net"), 0.0)
                by_strat[strat].append(
                    {
                        "symbol": sym,
                        "time": str(row.get("time", "")),
                        "net": net,
                        "regime": str(raw_reg or ""),
                        "reason": str(row.get("reason", "")),
                    }
                )

    summaries: Dict[str, Dict[str, Any]] = {}
    for strat, trades in by_strat.items():
        trades.sort(key=lambda t: t["time"])
        n = len(trades)
        wins = [t for t in trades if t["net"] > 0]
        losses = [t for t in trades if t["net"] <= 0]
        gw = sum(t["net"] for t in wins)
        gl = abs(sum(t["net"] for t in losses))
        net = gw - gl
        pf = (gw / gl) if gl > 0 else (9.99 if gw > 0 else 0.0)

        eq = 0.0
        peak = 0.0
        max_dd = 0.0
        for t in trades:
            eq += t["net"]
            if eq > peak:
                peak = eq
            max_dd = max(max_dd, peak - eq)

        by_sym: Dict[str, Dict[str, Any]] = {}
        for sym in SYMBOLS:
            st = [t for t in trades if t["symbol"] == sym]
            if st:
                by_sym[sym] = {
                    "trades": len(st),
                    "wins": sum(1 for t in st if t["net"] > 0),
                    "net_pnl_usd": round(sum(t["net"] for t in st), 2),
                }

        summaries[strat] = {
            "trades": n,
            "wins": len(wins),
            "losses": len(losses),
            "win_rate_pct": round(100.0 * len(wins) / n, 1) if n else 0.0,
            "gross_win_usd": round(gw, 2),
            "gross_loss_usd": round(gl, 2),
            "net_pnl_usd": round(net, 2),
            "profit_factor": round(pf, 2),
            "expectancy_usd": round(net / n, 4) if n else 0.0,
            "max_dd_usd": round(max_dd, 2),
            "first_trade_utc": trades[0]["time"] if trades else None,
            "last_trade_utc": trades[-1]["time"] if trades else None,
            "by_symbol": by_sym,
        }

    return summaries


def build_v3_live_config(baseline_cfg: Dict[str, Any]) -> Dict[str, Any]:
    """
    Constructs V3 live.json config deploying REGIME_ADAPTIVE_V5 across BTCUSD, ETHUSD, XAUUSD
    while preserving GOLD-PERP record-only baseline and Stealth RAM SL protections.
    """
    v3_symbols = {
        "BTCUSD": {
            "strategy": "REGIME_ADAPTIVE_V5",
            "p1": 1.0,    # SlAtrScale (adaptive 1.5x–2.5x ATR)
            "p2": 1.0,    # RrScale
            "p3": 0.020,  # ImbThresh
            "p4": 12.0,   # DeltaThresh
            "lots": 0.01,
            "placeOrders": True,
            "stealthStops": True,
            "jitterNoisePct": 5.0,
            "emergencySlMult": 3.5,
        },
        "ETHUSD": {
            "strategy": "REGIME_ADAPTIVE_V5",
            "p1": 1.0,
            "p2": 1.0,
            "p3": 0.015,
            "p4": 5.0,
            "lots": 0.01,
            "placeOrders": True,
            "stealthStops": True,
            "jitterNoisePct": 5.0,
            "emergencySlMult": 3.5,
        },
        "XAUUSD": {
            "strategy": "REGIME_ADAPTIVE_V5",
            "p1": 1.0,
            "p2": 1.0,
            "p3": 0.018,
            "p4": 6.0,
            "lots": 0.01,
            "placeOrders": True,
            "stealthStops": True,
            "jitterNoisePct": 5.0,
            "emergencySlMult": 3.5,
        },
        "GOLD-PERP": baseline_cfg.get("symbols", {}).get(
            "GOLD-PERP",
            {
                "strategy": "DOM_ABSORPTION",
                "p1": 15,
                "p2": 0.03,
                "p3": 2.5,
                "p4": 2.4,
                "lots": 0.01,
                "placeOrders": False,
                "stealthStops": True,
                "jitterNoisePct": 5.0,
                "emergencySlMult": 3.5,
            },
        ),
    }
    return {
        "strategy": "REGIME_ADAPTIVE_V5",
        "version": 3,
        "placeOrders": True,
        "lots": 0.01,
        "stealthStops": True,
        "jitterNoisePct": 5.0,
        "emergencySlMult": 3.5,
        "symbols": v3_symbols,
    }


def evaluate_ab_decision(
    ab_stats: Dict[str, Dict[str, Any]],
    challenger_code: str = "REGIME_ADAPTIVE_V5",
    baseline_code: str = "DOM_ABSORPTION",
    min_ab_trades: int = 8,
) -> Dict[str, Any]:
    """
    Pure decision function comparing Challenger V3 vs Baseline V2 real Demo performance.
    Returns verdict (`COLLECTING_PARALLEL_AB`, `AUTO_ROLLBACK`, `OUTPERFORMING_RETAIN_V3`, `PARITY_MONITOR_V3`).
    """
    base = ab_stats.get(
        baseline_code,
        {"trades": 0, "win_rate_pct": 0.0, "profit_factor": 0.0, "net_pnl_usd": 0.0, "expectancy_usd": 0.0, "max_dd_usd": 0.0},
    )
    chal = ab_stats.get(
        challenger_code,
        {"trades": 0, "win_rate_pct": 0.0, "profit_factor": 0.0, "net_pnl_usd": 0.0, "expectancy_usd": 0.0, "max_dd_usd": 0.0},
    )

    c_n = chal["trades"]
    if c_n >= 5 and chal["net_pnl_usd"] <= -12.0:
        return {
            "verdict": "AUTO_ROLLBACK",
            "should_rollback": True,
            "reason": f"Emergency bleed guard triggered: {challenger_code} lost {chal['net_pnl_usd']:.2f} USD over {c_n} trades.",
            "baseline": base,
            "challenger": chal,
        }

    if c_n < min_ab_trades:
        return {
            "verdict": "COLLECTING_PARALLEL_AB",
            "should_rollback": False,
            "reason": f"Forward Demo verification in progress ({c_n}/{min_ab_trades} closed trades on {challenger_code}). Baseline ({baseline_code}) N={base['trades']}, Net={base['net_pnl_usd']:+.2f} USD.",
            "baseline": base,
            "challenger": chal,
        }

    # Full comparison once >= min_ab_trades collected on Challenger
    worse_exp = chal["expectancy_usd"] < (base["expectancy_usd"] - 0.02)
    worse_pf = chal["profit_factor"] < max(0.85, base["profit_factor"] * 0.85)
    if (worse_exp and chal["net_pnl_usd"] < 0) or (worse_pf and chal["net_pnl_usd"] < base["net_pnl_usd"]):
        return {
            "verdict": "AUTO_ROLLBACK",
            "should_rollback": True,
            "reason": (
                f"{challenger_code} underperformed {baseline_code} over {c_n} Demo trades "
                f"(Exp {chal['expectancy_usd']:+.3f} vs {base['expectancy_usd']:+.3f}, "
                f"PF {chal['profit_factor']:.2f} vs {base['profit_factor']:.2f}) -> Auto-Rollback to V2."
            ),
            "baseline": base,
            "challenger": chal,
        }

    if chal["expectancy_usd"] >= base["expectancy_usd"] and chal["net_pnl_usd"] >= 0:
        return {
            "verdict": "OUTPERFORMING_RETAIN_V3",
            "should_rollback": False,
            "reason": (
                f"{challenger_code} outperformed {baseline_code} across {c_n} forward Demo trades "
                f"(Exp {chal['expectancy_usd']:+.3f} vs {base['expectancy_usd']:+.3f}, Net {chal['net_pnl_usd']:+.2f} USD)."
            ),
            "baseline": base,
            "challenger": chal,
        }

    return {
        "verdict": "PARITY_MONITOR_V3",
        "should_rollback": False,
        "reason": f"{challenger_code} performing within parity tolerance ({c_n} trades, Net {chal['net_pnl_usd']:+.2f} USD).",
        "baseline": base,
        "challenger": chal,
    }


def _load_or_init_state(state_path: Path, baseline_cfg: Dict[str, Any]) -> Dict[str, Any]:
    if state_path.exists():
        try:
            data = json.loads(state_path.read_text(encoding="utf-8"))
            if isinstance(data, dict) and "baseline_live_json" in data:
                return data
        except Exception:
            pass
    return {
        "schema_version": "5.0.0-DEMO-DEPLOYMENT",
        "account_quarantine": f"Pepperstone Demo #{ALLOWED_DEMO_ACCOUNT}",
        "active_strategy_code": baseline_cfg.get("strategy", "DOM_ABSORPTION"),
        "active_version": int(baseline_cfg.get("version", 2) or 2),
        "baseline_strategy_code": "DOM_ABSORPTION",
        "baseline_version": 2,
        "baseline_live_json": baseline_cfg,
        "deployment_history": [],
        "ab_evaluation": {},
    }


def _save_state(state_path: Path, state: Dict[str, Any]) -> None:
    state_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = state_path.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(state_path)


def sync_demo_deployment_and_ab(
    deploy_v3_if_baseline: bool = True,
    auto_rollback: bool = True,
    apply_live_json: bool = True,
    hypothesis: str = "Phase 2 OOS Matrix proved 7-zone Regime/ATR/Zone-End adaptation reduces rollover & transition losses vs static DOM_ABSORPTION V2.",
    build_verified: bool = False,
    live_base: Optional[Path] = None,
    live_json_path: Optional[Path] = None,
    state_path: Optional[Path] = None,
    account_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Executes Agent 4 Demo Governance:
    1) Verifies Pepperstone Demo #5258778 quarantine.
    2) Captures intact V2 Baseline rollback snapshot before updating live.json.
    3) Deploys V3 REGIME_ADAPTIVE_V5 if starting from V2 baseline (when deploy_v3_if_baseline=True).
    4) Runs live A/B comparison on real Demo trades.csv and auto-rolls back if triggered.
    """
    acct = account_id if account_id is not None else resolve_cli_account()
    assert_demo_quarantine(acct)

    ljson = live_json_path or resolve_live_json_path()
    spath = state_path or (REPO_ROOT / "docs" / "data" / "demo_deployment_state.json")

    current_live: Dict[str, Any] = {}
    if ljson.exists():
        current_live = json.loads(ljson.read_text(encoding="utf-8-sig"))

    state = _load_or_init_state(spath, current_live)
    now_iso = datetime.now(timezone.utc).isoformat()
    state["updated_at_utc"] = now_iso
    state["build_verified"] = bool(build_verified) or bool(state.get("build_verified", False))

    ab_stats = load_closed_trades_by_strategy(live_base=live_base)
    ab_eval = evaluate_ab_decision(ab_stats)
    state["ab_evaluation"] = ab_eval

    action_taken = "NONE"

    # Deploy V3 over baseline V2 autonomously under V5 Demo rule
    if deploy_v3_if_baseline and state.get("active_strategy_code") == "DOM_ABSORPTION" and not ab_eval["should_rollback"]:
        v3_cfg = build_v3_live_config(state["baseline_live_json"])
        if apply_live_json:
            ljson.parent.mkdir(parents=True, exist_ok=True)
            ljson.write_text(json.dumps(v3_cfg, indent=2, ensure_ascii=False), encoding="utf-8")
        state["active_strategy_code"] = "REGIME_ADAPTIVE_V5"
        state["active_version"] = 3
        state["deployment_history"].append(
            {
                "timestamp_utc": now_iso,
                "action": "DEPLOY_V3_ON_DEMO",
                "from": "DOM_ABSORPTION v2",
                "to": "REGIME_ADAPTIVE_V5 v3",
                "hypothesis": hypothesis,
                "baseline_trades_at_switch": ab_eval["baseline"].get("trades", 0),
                "baseline_net_usd_at_switch": ab_eval["baseline"].get("net_pnl_usd", 0.0),
                "live_json_written": bool(apply_live_json),
            }
        )
        action_taken = "DEPLOYED_V3_REGIME_ADAPTIVE_V5"

    # Auto-rollback if V3 underperformed V2 baseline
    elif auto_rollback and state.get("active_strategy_code") == "REGIME_ADAPTIVE_V5" and ab_eval["should_rollback"]:
        if apply_live_json and state.get("baseline_live_json"):
            ljson.parent.mkdir(parents=True, exist_ok=True)
            ljson.write_text(json.dumps(state["baseline_live_json"], indent=2, ensure_ascii=False), encoding="utf-8")
        state["active_strategy_code"] = "DOM_ABSORPTION"
        state["active_version"] = 2
        state["deployment_history"].append(
            {
                "timestamp_utc": now_iso,
                "action": "AUTO_ROLLBACK_TO_V2",
                "from": "REGIME_ADAPTIVE_V5 v3",
                "to": "DOM_ABSORPTION v2",
                "hypothesis": ab_eval["reason"],
                "live_json_written": bool(apply_live_json),
            }
        )
        action_taken = "AUTO_ROLLED_BACK_TO_V2_DOM_ABSORPTION"

    state["last_action"] = action_taken
    _save_state(spath, state)
    return state


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    res = sync_demo_deployment_and_ab(deploy_v3_if_baseline=False, apply_live_json=False)
    print(f"Account: {res['account_quarantine']} | Active: {res['active_strategy_code']} v{res['active_version']}")
    print("AB Decision:", res["ab_evaluation"]["verdict"], "-", res["ab_evaluation"]["reason"])
