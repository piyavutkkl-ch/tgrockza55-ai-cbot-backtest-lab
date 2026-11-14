#!/usr/bin/env python3
"""
Build compact summary JSON (docs/data/overview_summary.json) for Page 1 (Overview)
so Overview stays fast (< ~400 KB total payload) without fetching huge 550KB+ JSON blobs.
"""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "docs" / "data"
LIVE_DIR = ROOT / "data" / "live"
OUT_PATH = DATA_DIR / "overview_summary.json"


def read_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def downsample(items: list[Any], max_points: int) -> list[Any]:
    if len(items) <= max_points:
        return items
    if max_points <= 2:
        return [items[0], items[-1]]
    step = (len(items) - 1) / (max_points - 1)
    idxs = sorted({round(i * step) for i in range(max_points)})
    return [items[i] for i in idxs]


def build_live_equity_history(live_status: dict[str, Any]) -> dict[str, Any]:
    ft = live_status.get("forward_trading") or {}
    initial_deposit = float(ft.get("initial_deposit") or 100.0)
    points_by_key: dict[str, dict[str, Any]] = {}
    csv_close_count = 0

    for sym_dir in sorted(LIVE_DIR.glob("*")):
        csv_path = sym_dir / "trades.csv"
        if not csv_path.exists():
            continue
        sym_name = sym_dir.name
        with csv_path.open("r", encoding="utf-8", errors="ignore") as f:
            reader = csv.DictReader(f)
            for row in reader:
                ev = (row.get("event") or row.get("Event") or "").strip().upper()
                if ev != "CLOSE":
                    continue
                csv_close_count += 1
                bal_raw = row.get("balance")
                t_raw = (row.get("time") or "").strip()
                if not bal_raw or not t_raw:
                    continue
                try:
                    bal = float(bal_raw)
                except ValueError:
                    continue
                tid = (row.get("id") or f"{t_raw}-{sym_name}").strip()
                points_by_key[tid] = {
                    "id": tid,
                    "time": t_raw,
                    "symbol": sym_name,
                    "balance": round(bal, 2),
                    "net": round(float(row.get("net") or 0.0), 2),
                    "source": "csv",
                }

    for deal in live_status.get("recent_closed_deals") or []:
        t_raw = str(deal.get("close_time") or "").strip()
        bal = deal.get("balance")
        if not t_raw or bal is None:
            continue
        tid = str(deal.get("id") or t_raw)
        points_by_key[tid] = {
            "id": tid,
            "time": t_raw,
            "symbol": deal.get("symbol") or "",
            "balance": round(float(bal), 2),
            "net": round(float(deal.get("net") or 0.0), 2),
            "source": "recent",
        }

    ordered = sorted(points_by_key.values(), key=lambda x: x["time"])
    # Prepend initial deposit point for historical curve clarity
    curve = [{"time": "Start", "balance": round(initial_deposit, 2), "net": 0.0, "source": "deposit"}]
    curve.extend(ordered)
    if ft.get("balance") is not None:
        end_bal = round(float(ft["balance"]), 2)
        if not curve or abs(curve[-1]["balance"] - end_bal) > 1e-6:
            curve.append({
                "time": str(live_status.get("timestamp_utc") or "Latest")[:19].replace("T", " "),
                "balance": end_bal,
                "net": round(float(ft.get("net_pnl") or 0.0), 2),
                "source": "snapshot",
            })

    sampled_curve = downsample(curve, 44)
    # Compute latest trade execution latency from recent_trades OPEN events
    latest_latency = None
    latest_latency_time = None
    for t in live_status.get("recent_trades") or []:
        lat_raw = str(t.get("latencyMs") or "").strip()
        if lat_raw:
            try:
                lat_val = int(round(float(lat_raw)))
                t_str = str(t.get("time") or "")
                if latest_latency_time is None or t_str >= latest_latency_time:
                    latest_latency_time = t_str
                    latest_latency = lat_val
            except ValueError:
                pass

    return {
        "initial_deposit": round(initial_deposit, 2),
        "csv_closed_trades_count": csv_close_count,
        "merged_points_count": len(ordered),
        "equity_curve": sampled_curve,
        "latest_trade_latency_ms": latest_latency,
        "latest_trade_latency_time": latest_latency_time,
    }


def build_symbol_sparklines(terminal_compact: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    if not isinstance(terminal_compact, dict):
        return out

    for sym, payload in terminal_compact.items():
        if not isinstance(payload, dict):
            continue
        bars = list(payload.get("initial") or []) + list(payload.get("stream") or [])
        if not bars:
            continue
        closes_full = [
            {"t": str(b.get("time") or ""), "c": float(b["c"])}
            for b in bars
            if b.get("c") is not None
        ]
        if not closes_full:
            continue
        sampled = downsample(closes_full, 32)
        first_c = closes_full[0]["c"]
        last_c = closes_full[-1]["c"]
        chg_usd = last_c - first_c
        chg_pct = (chg_usd / first_c * 100.0) if first_c else 0.0
        out[sym] = {
            "bars_total": len(closes_full),
            "first_bar_time": closes_full[0]["t"],
            "last_bar_time": closes_full[-1]["t"],
            "session_open": round(first_c, 4),
            "session_close": round(last_c, 4),
            "session_change_usd": round(chg_usd, 4),
            "session_change_pct": round(chg_pct, 3),
            "points": [round(p["c"], 4) for p in sampled],
            "times": [p["t"] for p in sampled],
        }
    return out


def build_backtest_fallback(backtest_data: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(backtest_data, dict):
        return {}
    out: dict[str, Any] = {}
    for key, model in backtest_data.items():
        if not isinstance(model, dict):
            continue
        summary = model.get("summary") or {}
        daily = model.get("daily_pnl") or {}
        curve: list[dict[str, Any]] = []
        if isinstance(daily, dict) and daily:
            cum = 0.0
            curve.append({"label": "Start", "pnl": 0.0})
            for day in sorted(daily.keys()):
                cum += float(daily[day])
                curve.append({"label": day, "pnl": round(cum, 2)})
        elif isinstance(model.get("equity_curve"), list) and model["equity_curve"]:
            raw_eq = model["equity_curve"]
            for idx, pt in enumerate(downsample(raw_eq, 32)):
                if isinstance(pt, dict):
                    val = pt.get("equity") or pt.get("pnl") or pt.get("balance") or 0.0
                    curve.append({"label": str(pt.get("time") or idx), "pnl": round(float(val), 2)})
                else:
                    curve.append({"label": str(idx), "pnl": round(float(pt), 2)})
        out[key] = {
            "name": model.get("name") or key,
            "symbol": model.get("symbol") or "",
            "timeframe": model.get("timeframe") or "",
            "period": model.get("period") or "",
            "summary": summary,
            "equity_curve": curve,
        }
    return out


def main() -> None:
    live_status = read_json(DATA_DIR / "live_status.json", {})
    papers_db = read_json(DATA_DIR / "papers_database.json", [])
    strategy_reg = read_json(DATA_DIR / "strategy_registry.json", {})
    strategy_foundry = read_json(DATA_DIR / "strategy_foundry.json", {})
    terminal_compact = read_json(DATA_DIR / "terminal_compact.json", {})
    backtest_data = read_json(DATA_DIR / "backtest_data.json", {})
    calibrated_costs = read_json(DATA_DIR / "calibrated_costs.json", {})

    papers_count = len(papers_db) if isinstance(papers_db, list) else int(papers_db.get("total", 0) or 0)
    strategies_obj = strategy_reg.get("strategies") if isinstance(strategy_reg, dict) else None
    strategies_count = (
        int(strategy_reg.get("total_strategies"))
        if isinstance(strategy_reg, dict) and strategy_reg.get("total_strategies") is not None
        else (len(strategies_obj) if isinstance(strategies_obj, (dict, list)) else 0)
    )
    foundry_stats = strategy_foundry.get("stats") or {}

    summary_payload = {
        "schema_version": "1.0.0",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "alpha_funnel": {
            "ideas_count": int(foundry_stats.get("total_hypotheses_generated") or 0),
            "papers_count": papers_count,
            "strategies_count": strategies_count,
            "survived_screening_count": int(foundry_stats.get("survived_screening") or 0),
            "survivors_count": int(foundry_stats.get("active_micro_forward") or 0),
        },
        "live_history": build_live_equity_history(live_status),
        "symbols": build_symbol_sparklines(terminal_compact),
        "backtest_fallback": build_backtest_fallback(backtest_data),
        "calibrated_latency": {
            sym: (obj.get("latency_ms") or {}).get("median")
            for sym, obj in (calibrated_costs.get("symbols") or {}).items()
            if isinstance(obj, dict)
        },
    }

    OUT_PATH.write_text(json.dumps(summary_payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    size_kb = OUT_PATH.stat().st_size / 1024.0
    print(f"Wrote {OUT_PATH.relative_to(ROOT)} ({size_kb:.2f} KB)")
    print("alpha_funnel:", summary_payload["alpha_funnel"])
    print("live_history points:", len(summary_payload["live_history"]["equity_curve"]),
          "latest latency ms:", summary_payload["live_history"]["latest_trade_latency_ms"])
    print("symbols sparklines:", {k: len(v["points"]) for k, v in summary_payload["symbols"].items()})


if __name__ == "__main__":
    main()
