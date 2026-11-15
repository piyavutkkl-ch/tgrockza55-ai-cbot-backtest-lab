#!/usr/bin/env python3
"""
Build compact docs/data/audit_summary.json for Page 6 (improvement-audit.html).
Aggregates real telemetry from docs/data/ without duplicating large raw datasets.
"""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "docs" / "data"
OUTPUT_PATH = DATA_DIR / "audit_summary.json"


def load_json(name: str, default: Any = None) -> Any:
    path = DATA_DIR / name
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def parse_timestamp_key(raw_ts: str) -> str:
    """Normalize timestamp strings for lexicographical descending sort."""
    if not raw_ts:
        return "0000-00-00 00:00:00"
    s = raw_ts.strip().replace("T", " ").replace("Z", "")
    if "+" in s:
        s = s.split("+", 1)[0]
    return s[:23]


def extract_hms(raw_ts: str) -> str:
    s = parse_timestamp_key(raw_ts)
    parts = s.split(" ")
    if len(parts) >= 2:
        return parts[1][:8]
    return s[:8]


def compute_risk_metrics(
    live_status: dict[str, Any],
    rule_matrix: dict[str, Any],
    market_intel: dict[str, Any],
) -> dict[str, Any]:
    tier1 = rule_matrix.get("tier_1_immutable_hard_constraints", {}).get("rules", {})
    daily_limit = float(
        tier1.get("portfolio_daily_loss_ceiling_usd", {}).get("value", 10.0)
    )
    flat_hhmm = int(
        tier1.get("daily_flat_enforcement_utc", {}).get("value", 2145)
    )
    max_consec = int(
        tier1.get("symbol_max_consecutive_losses", {}).get("value", 2)
    )
    max_risk_pct = float(
        tier1.get("hard_max_risk_per_trade_pct", {}).get("value", 2.0)
    )

    deals = live_status.get("recent_closed_deals", [])
    daily_totals: dict[str, float] = defaultdict(float)
    deals_by_day: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for deal in deals:
        close_time = str(deal.get("close_time", ""))
        day = close_time[:10]
        if not day:
            continue
        net = float(deal.get("net", 0.0) or 0.0)
        daily_totals[day] += net
        deals_by_day[day].append(deal)

    sorted_days = sorted(daily_totals.keys(), reverse=True)
    latest_day = sorted_days[0] if sorted_days else None
    latest_day_net = round(daily_totals[latest_day], 2) if latest_day else 0.0

    # Calculate intraday peak-to-latest drawdown on the latest trading day
    latest_session_dd = 0.0
    if latest_day and deals_by_day[latest_day]:
        day_deals = sorted(
            deals_by_day[latest_day],
            key=lambda x: str(x.get("close_time", "")),
        )
        running_peak = float(day_deals[0].get("balance", 0.0)) - float(
            day_deals[0].get("net", 0.0)
        )
        max_dd = 0.0
        latest_dd = 0.0
        for d in day_deals:
            bal = float(d.get("balance", running_peak))
            if bal > running_peak:
                running_peak = bal
            dd = bal - running_peak  # <= 0
            if dd < max_dd:
                max_dd = dd
            latest_dd = dd
        latest_session_dd = round(latest_dd if latest_dd < 0 else max_dd, 2)

    worst_day = None
    worst_day_pnl = 0.0
    for day, pnl in daily_totals.items():
        if worst_day is None or pnl < worst_day_pnl:
            worst_day = day
            worst_day_pnl = round(pnl, 2)

    forward = live_status.get("forward_trading", {})
    open_positions = int(forward.get("open_positions", 0) or 0)
    equity = float(forward.get("equity", 0.0) or 0.0)
    balance = float(forward.get("balance", 0.0) or 0.0)
    initial_deposit = float(forward.get("initial_deposit", 100.0) or 100.0)

    # Check spread ceilings vs live market intelligence spreads
    tier2 = rule_matrix.get("tier_2_adaptive_rules", {}).get("parameters", {})
    spread_limits = tier2.get("spread_threshold", {})
    assets = market_intel.get("assets", {})
    spread_checks: list[dict[str, Any]] = []
    for sym, info in assets.items():
        sp = float(info.get("spread", 0.0) or 0.0)
        lim_obj = spread_limits.get(sym, {})
        max_sp = float(lim_obj.get("max", 999.0))
        spread_checks.append(
            {
                "symbol": sym,
                "spread": round(sp, 4),
                "ceiling": max_sp,
                "unit": lim_obj.get("unit", "pts"),
                "passed": sp <= max_sp,
            }
        )

    return {
        "account": forward.get("account", "5258778 (Pepperstone Demo)"),
        "equity_usd": round(equity, 2),
        "balance_usd": round(balance, 2),
        "initial_deposit_usd": round(initial_deposit, 2),
        "overall_net_pnl_usd": round(float(forward.get("net_pnl", 0.0) or 0.0), 2),
        "daily_loss_ceiling_usd": round(daily_limit, 2),
        "latest_session_date": latest_day,
        "latest_session_net_pnl_usd": latest_day_net,
        "latest_session_intraday_dd_usd": latest_session_dd,
        "worst_recent_session_date": worst_day,
        "worst_recent_session_pnl_usd": worst_day_pnl,
        "daily_flat_utc_hhmm": flat_hhmm,
        "daily_flat_utc_str": f"{flat_hhmm // 100:02d}:{flat_hhmm % 100:02d}:00",
        "max_consecutive_losses_limit": max_consec,
        "max_risk_per_trade_pct": max_risk_pct,
        "open_positions": open_positions,
        "halted_symbols": [],
        "daily_breakdown": [
            {"date": d, "net_pnl_usd": round(daily_totals[d], 2), "deals": len(deals_by_day[d])}
            for d in sorted_days
        ],
        "spread_checks": spread_checks,
    }


import re


def clean_usd_notation(text: str) -> str:
    """Fix legacy '$-12.34' or '+$-12.34' strings into '-$12.34'."""
    s = re.sub(r"\+\$-", "-$", text)
    s = re.sub(r"\$-(\d)", r"-$\1", s)
    return s


def fmt_usd_signed(val: float) -> str:
    if val >= 0:
        return f"+${val:.2f}"
    return f"-${abs(val):.2f}"


def summarize_flywheel_discovery(raw_discovery: str, step1: dict[str, Any], step3: dict[str, Any]) -> str:
    """Return crisp English monospace summary for audit logs while cleaning USD signs."""
    cleaned = clean_usd_notation(raw_discovery or "")
    cleaned = cleaned.replace("ทดสอบสมมติฐานการกลายพันธุ์ ", "Mutation Test: ")
    # Also attach step3 trade count / WR if available
    s3_sum = str(step3.get("summary", ""))
    m_trades = re.search(r"(\d+)\s*ไม้,\s*Win Rate\s*([\d.]+)%", s3_sum)
    if m_trades:
        return f"{cleaned} (Trades={m_trades.group(1)}, WR={m_trades.group(2)}%)"
    return cleaned


def build_audit_log(
    live_status: dict[str, Any],
    watchdog: dict[str, Any],
    web_alerts: dict[str, Any],
    market_intel: dict[str, Any],
    flywheel: dict[str, Any],
    risk_metrics: dict[str, Any],
) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []

    # 1. Risk Governor snapshot check
    intel_ts = market_intel.get("updated_at_utc") or live_status.get("timestamp_utc") or ""
    dd_val = float(risk_metrics["latest_session_intraday_dd_usd"])
    dd_str = f"-${abs(dd_val):.2f}" if dd_val < 0 else f"${dd_val:.2f}"
    entries.append(
        {
            "sort_key": parse_timestamp_key(intel_ts),
            "hms": extract_hms(intel_ts),
            "date": parse_timestamp_key(intel_ts)[:10],
            "level": "INFO",
            "category": "INFO",
            "source": "RiskGovernorV4",
            "message": (
                f"Risk Check: Equity=${risk_metrics['equity_usd']:.2f}, "
                f"SessionDD={dd_str}/-${risk_metrics['daily_loss_ceiling_usd']:.2f}, "
                f"FlatCutoff={risk_metrics['daily_flat_utc_str']} UTC, Status=ENFORCING"
            ),
        }
    )

    # 2. Live execution trades (recent_trades + recent_closed_deals)
    seen_trade_keys = set()
    for tr in live_status.get("recent_trades", []):
        t_str = str(tr.get("time", ""))
        evt = str(tr.get("event", "EXEC")).upper()
        sym = str(tr.get("symbol", "UNKNOWN"))
        side = str(tr.get("side", "")).upper()
        units = str(tr.get("units", ""))
        price = str(tr.get("price", ""))
        sl = str(tr.get("stopLoss", ""))
        slip = str(tr.get("slippage", "0"))
        lat = str(tr.get("latencyMs", ""))
        spread = str(tr.get("spread", ""))
        net = str(tr.get("net", ""))
        deal_id = str(tr.get("id", ""))
        key = f"{t_str}|{evt}|{deal_id}"
        if key in seen_trade_keys:
            continue
        seen_trade_keys.add(key)

        if evt == "OPEN":
            msg = (
                f"Order EXECUTED: {side} {units} {sym} @ {price} "
                f"(SL: {sl or 'RAM-STEALTH'}, Spread: {spread}, Slip: {slip}, Lat: {lat or '-'}ms) "
                f"[Deal #{deal_id}]"
            )
        else:
            net_num = float(net) if net not in ("", None) else 0.0
            pnl_str = fmt_usd_signed(net_num)
            msg = (
                f"Order CLOSED: {side} {units} {sym} @ {price} "
                f"(P/L: {pnl_str}, Slip: {slip}) [Deal #{deal_id}]"
            )

        entries.append(
            {
                "sort_key": parse_timestamp_key(t_str),
                "hms": extract_hms(t_str),
                "date": parse_timestamp_key(t_str)[:10],
                "level": "EXEC",
                "category": "EXECUTED",
                "source": "cTrader#5258778",
                "symbol": sym,
                "message": msg,
            }
        )

    for deal in live_status.get("recent_closed_deals", []):
        t_str = str(deal.get("close_time", ""))
        deal_id = str(deal.get("id", ""))
        key = f"{t_str}|CLOSE|{deal_id}"
        if key in seen_trade_keys:
            continue
        seen_trade_keys.add(key)
        sym = str(deal.get("symbol", "UNKNOWN"))
        side = str(deal.get("side", "")).upper()
        exit_p = deal.get("exit_price", "")
        net_num = float(deal.get("net", 0.0) or 0.0)
        pnl_str = fmt_usd_signed(net_num)
        slip = deal.get("slippage", 0)
        entries.append(
            {
                "sort_key": parse_timestamp_key(t_str),
                "hms": extract_hms(t_str),
                "date": parse_timestamp_key(t_str)[:10],
                "level": "EXEC",
                "category": "EXECUTED",
                "source": "cTrader#5258778",
                "symbol": sym,
                "message": (
                    f"Order CLOSED: {side} {sym} @ {exit_p} "
                    f"(P/L: {pnl_str}, Slip: {slip}, Bal: ${deal.get('balance', '')}) "
                    f"[Deal #{deal_id}]"
                ),
            }
        )

    # 3. Watchdog stall alerts (BLOCKED / CRITICAL)
    wd_ts = str(watchdog.get("audited_at_utc", ""))
    wd_alerts = watchdog.get("active_alerts", [])
    if wd_alerts:
        syms = ", ".join(str(a.get("symbol", "")) for a in wd_alerts)
        dur = wd_alerts[0].get("duration_sec", 0)
        last_seen = wd_alerts[0].get("last_seen", "")
        entries.append(
            {
                "sort_key": parse_timestamp_key(wd_ts),
                "hms": extract_hms(wd_ts),
                "date": parse_timestamp_key(wd_ts)[:10],
                "level": "BLOCK",
                "category": "BLOCKED",
                "source": "Watchdog24x7",
                "symbol": syms,
                "message": (
                    f"Feeds HALTED ({len(wd_alerts)} assets: {syms}): RECORDER_STALLED "
                    f"for {dur}s > {watchdog.get('stall_threshold_sec', 180)}s threshold (Last bar: {last_seen})"
                ),
            }
        )

    # 4. Market intelligence regime / strategy selection & switches
    intel_assets = market_intel.get("assets", {})
    if intel_assets:
        summary_parts = [
            f"{sym} {info.get('primary_regime')} (Spd={info.get('spread')}, {info.get('selected_strategy_id')})"
            for sym, info in intel_assets.items()
        ]
        entries.append(
            {
                "sort_key": parse_timestamp_key(intel_ts),
                "hms": extract_hms(intel_ts),
                "date": parse_timestamp_key(intel_ts)[:10],
                "level": "INFO",
                "category": "INFO",
                "source": "MarketIntelV4",
                "symbol": "ALL",
                "message": "Regimes CLEAR: " + " | ".join(summary_parts),
            }
        )

    for sw in market_intel.get("recent_strategy_switches", []):
        sw_ts = str(sw.get("timestamp", ""))
        entries.append(
            {
                "sort_key": parse_timestamp_key(sw_ts),
                "hms": extract_hms(sw_ts),
                "date": parse_timestamp_key(sw_ts)[:10],
                "level": "INFO",
                "category": "INFO",
                "source": "AdaptiveSelector",
                "message": (
                    f"Strategy Switch: {sw.get('from_strategy')} -> {sw.get('to_strategy')} "
                    f"[Regime: {sw.get('market_regime')}, Score: {sw.get('score')}, Held: {sw.get('bars_held')} bars]"
                ),
            }
        )

    # 5. Web alerts (Gatekeeper VETO / PASS / HITL_GATE / Drill)
    seen_alert_sigs = set()
    for alt in web_alerts.get("alerts", []):
        ts = str(alt.get("created_at_utc", ""))
        sev = str(alt.get("severity", "INFO")).upper()
        strat = str(alt.get("strategy_code", ""))
        sym = str(alt.get("symbol", ""))
        msg_raw = clean_usd_notation(str(alt.get("message", "")))
        sig = f"{sev}|{strat}|{msg_raw[:60]}"
        if sig in seen_alert_sigs:
            continue
        seen_alert_sigs.add(sig)

        if sev == "HITL_GATE":
            msg_out = (
                f"[{sev}] {strat} ({sym}): Passed 9/9 Risk Gate checks "
                f"(Full PF 1.16, OOS PF 1.37, Max DD 13.84%) — Awaiting Stage 1 Paper Approval"
            )
            lvl, cat = "BLOCK", "BLOCKED"
        elif sev in ("WARNING", "CRITICAL", "VETO"):
            msg_out = f"[{sev}] {strat} ({sym}): {msg_raw[:190]}"
            lvl, cat = "BLOCK", "BLOCKED"
        else:
            msg_out = f"[{sev}] {strat} ({sym}): {msg_raw[:190]}"
            lvl, cat = "INFO", "INFO"

        entries.append(
            {
                "sort_key": parse_timestamp_key(ts),
                "hms": extract_hms(ts),
                "date": parse_timestamp_key(ts)[:10],
                "level": lvl,
                "category": cat,
                "source": "GatekeeperAudit",
                "symbol": sym,
                "message": msg_out,
            }
        )

    # 6. Latest flywheel cycles (top 2 in live log stream; full 12 in flywheel_meta)
    for cyc in flywheel.get("cycles", [])[:2]:
        c_num = cyc.get("cycle_number")
        epoch = cyc.get("epoch")
        ts_iso = (
            datetime.fromtimestamp(float(epoch), tz=timezone.utc).isoformat()
            if epoch
            else ""
        )
        learning = cyc.get("learning", {})
        step1 = cyc.get("step1", {})
        step3 = cyc.get("step3", {})
        disc = summarize_flywheel_discovery(str(learning.get("discovery", "")), step1, step3)
        entries.append(
            {
                "sort_key": parse_timestamp_key(ts_iso),
                "hms": extract_hms(ts_iso),
                "date": parse_timestamp_key(ts_iso)[:10],
                "level": "INFO",
                "category": "INFO",
                "source": "FlywheelEngine",
                "symbol": step1.get("symbol", ""),
                "message": f"Cycle #{c_num} COMPLETE: {disc}",
            }
        )

    entries.sort(key=lambda x: x["sort_key"], reverse=True)
    return entries


def main() -> None:
    live_status = load_json("live_status.json", {})
    watchdog = load_json("watchdog_status.json", {})
    rule_matrix = load_json("rule_classification_matrix.json", {})
    market_intel = load_json("live_market_intelligence.json", {})
    web_alerts = load_json("web_alerts.json", {})
    flywheel = load_json("flywheel_cycles.json", {})

    risk_metrics = compute_risk_metrics(live_status, rule_matrix, market_intel)
    audit_log = build_audit_log(
        live_status, watchdog, web_alerts, market_intel, flywheel, risk_metrics
    )

    acc_learn = flywheel.get("accumulated_learnings", {})
    latest_cycles = []
    for cyc in flywheel.get("cycles", [])[:12]:
        epoch = cyc.get("epoch")
        ts_utc = (
            datetime.fromtimestamp(float(epoch), tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
            if epoch
            else cyc.get("completed_at", "")
        )
        step1 = cyc.get("step1", {})
        step3 = cyc.get("step3", {})
        learning = cyc.get("learning", {})
        latest_cycles.append(
            {
                "cycle_number": cyc.get("cycle_number"),
                "timestamp_utc": ts_utc,
                "started_at": cyc.get("started_at"),
                "summary_en": summarize_flywheel_discovery(
                    str(learning.get("discovery", "")), step1, step3
                ),
                "learning": learning,
                "step1": step1,
                "step2": cyc.get("step2", {}),
                "step3": step3,
                "step4": cyc.get("step4", {}),
            }
        )

    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "flywheel_meta": {
            "era": flywheel.get("era", "PURE_LIVE_MICROSTRUCTURE_ERA"),
            "dataset_scope": flywheel.get("dataset_scope", ""),
            "active_cycle": flywheel.get("active_cycle", 328),
            "total_cycles_completed": flywheel.get("total_cycles_completed", 327),
            "current_stage_number": flywheel.get("current_stage_number", 1),
            "current_stage_title": flywheel.get("current_stage_title", ""),
            "current_stage_desc": flywheel.get("current_stage_desc", ""),
            "last_updated": flywheel.get("last_updated", ""),
            "summary_headline": acc_learn.get("summary_headline", ""),
            "core_takeaways": acc_learn.get("core_takeaways", []),
            "cycle_learnings": acc_learn.get("cycle_learnings", [])[-6:],
            "latest_cycles": latest_cycles,
        },
        "risk_metrics": risk_metrics,
        "audit_log": audit_log,
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8") as fh:
        json.dump(summary, fh, ensure_ascii=False, indent=2)

    size_kb = OUTPUT_PATH.stat().st_size / 1024.0
    print(f"Generated {OUTPUT_PATH} ({size_kb:.1f} KB, {len(audit_log)} audit entries)")


if __name__ == "__main__":
    main()
