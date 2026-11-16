#!/usr/bin/env python3
"""
Build compact, real-data JSON feeds for Page 2: Data Center (docs/data-center.html).
Reads real recorded Pepperstone M1, Order Flow, and Trade Execution telemetry from data/live/.
Generates:
  - docs/data/dc_meta.json
  - docs/data/dc_XAUUSD.json
  - docs/data/dc_BTCUSD.json
  - docs/data/dc_ETHUSD.json
  - docs/data/dc_GOLD-PERP.json
"""

from __future__ import annotations

import csv
import json
import os
import shutil
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research.hybrid_data_merger import sanitize_live_minute_files
REPO_LIVE_DIR = ROOT / "data" / "live"
DOCS_DATA_DIR = ROOT / "docs" / "data"

_local_appdata = os.environ.get("LOCALAPPDATA", "")
PC_LIVE_DIR = Path(_local_appdata) / "BacktestLab" / "live" if _local_appdata else None

SYMBOL_CONFIG: Dict[str, Dict[str, Any]] = {
    "XAUUSD": {
        "displayName": "XAU/USD",
        "label": "Gold Spot",
        "digits": 2,
        "pipSize": 0.10,
        "contractSize": 100,
        "domStep": 0.10,
        "defaultLot": 0.01,
    },
    "BTCUSD": {
        "displayName": "BTC/USD",
        "label": "Bitcoin CFD",
        "digits": 2,
        "pipSize": 1.00,
        "contractSize": 1,
        "domStep": 5.00,
        "defaultLot": 0.01,
    },
    "ETHUSD": {
        "displayName": "ETH/USD",
        "label": "Ethereum CFD",
        "digits": 2,
        "pipSize": 0.10,
        "contractSize": 10,
        "domStep": 0.50,
        "defaultLot": 0.01,
    },
    "GOLD-PERP": {
        "displayName": "GOLD-PERP",
        "label": "Gold Perpetual",
        "digits": 2,
        "pipSize": 0.10,
        "contractSize": 100,
        "domStep": 0.10,
        "defaultLot": 0.01,
    },
}

SCHEMA = [
    "t",    # 0: Unix timestamp (seconds, UTC)
    "o",    # 1: Open
    "h",    # 2: High
    "l",    # 3: Low
    "c",    # 4: Close
    "v",    # 5: Tick volume
    "tk",   # 6: Raw ticks in minute
    "d",    # 7: Order flow delta (buyTicks - sellTicks)
    "cvd",  # 8: Cumulative volume delta
    "sp",   # 9: Average spread (quote currency)
    "bv",   # 10: Bid depth volume (sum 25 levels avg)
    "av",   # 11: Ask depth volume (sum 25 levels avg)
    "imb",  # 12: Order book imbalance [-1, 1]
    "du",   # 13: Depth updates per minute
    "vw",   # 14: Day Anchored VWAP
    "sd",   # 15: Day VWAP Std Dev
    "poc",  # 16: Point of Control
    "vah",  # 17: Value Area High
    "val",  # 18: Value Area Low
    "lb",   # 19: Ladder span Bid (level 1 to 25)
    "la",   # 20: Ladder span Ask (level 1 to 25)
    "gap",  # 21: Missing M1 bars immediately prior to this bar
]


def _f(val: Any, default: float = 0.0, ndigits: int = 4) -> float:
    if val is None or val == "":
        return default
    try:
        num = float(val)
        return round(num, ndigits)
    except (ValueError, TypeError):
        return default


def _i(val: Any, default: int = 0) -> int:
    if val is None or val == "":
        return default
    try:
        return int(round(float(val)))
    except (ValueError, TypeError):
        return default


def parse_utc_minute(ts_str: str) -> int:
    dt = datetime.strptime(ts_str.strip(), "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
    return int(dt.timestamp())


def parse_trades(sym_dir: Path) -> List[Dict[str, Any]]:
    tpath = sym_dir / "trades.csv"
    if not tpath.exists():
        return []
    out: List[Dict[str, Any]] = []
    with tpath.open("r", encoding="utf-8", errors="replace") as f:
        for row in csv.DictReader(f):
            ts_raw = (row.get("time") or "").strip()
            if not ts_raw:
                continue
            try:
                dt = datetime.strptime(ts_raw[:19], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
                ts_sec = int(dt.timestamp())
            except ValueError:
                continue
            lat = _f(row.get("latencyMs"), -1.0, 1)
            out.append({
                "t": ts_sec,
                "time": ts_raw[:19],
                "event": (row.get("event") or "").strip(),
                "id": (row.get("id") or "").strip(),
                "side": (row.get("side") or "").strip(),
                "units": _f(row.get("units"), 0.0, 2),
                "price": _f(row.get("price"), 0.0, 2),
                "slippage": _f(row.get("slippage"), 0.0, 4),
                "latencyMs": lat if lat >= 0 else None,
                "spread": _f(row.get("spread"), 0.0, 3),
                "net": _f(row.get("net"), 0.0, 2) if row.get("net") else None,
            })
    return out


def build_symbol(sym: str, cfg: Dict[str, Any]) -> Dict[str, Any]:
    repo_sym_dir = REPO_LIVE_DIR / sym
    pc_sym_dir = (PC_LIVE_DIR / sym) if PC_LIVE_DIR else None

    # Sync trades from PC to repo if available
    if pc_sym_dir and pc_sym_dir.exists():
        pc_trades = pc_sym_dir / "trades.csv"
        repo_trades = repo_sym_dir / "trades.csv"
        if pc_trades.exists():
            repo_sym_dir.mkdir(parents=True, exist_ok=True)
            if not repo_trades.exists() or pc_trades.stat().st_size > repo_trades.stat().st_size:
                try:
                    shutil.copy2(pc_trades, repo_trades)
                except Exception:
                    pass

    # Pick directory with min-*.csv files (prefer PC if present and non-empty)
    if pc_sym_dir and pc_sym_dir.exists() and list(pc_sym_dir.glob("min-*.csv")):
        sym_dir = pc_sym_dir
    else:
        sym_dir = repo_sym_dir

    min_files = sorted(sym_dir.glob("min-*.csv"))
    flow_files = sorted(sym_dir.glob("flow-*.csv"))

    min_clean, flow_clean, _ = sanitize_live_minute_files(min_files, flow_files)

    bars: List[List[Any]] = []
    gaps: List[Dict[str, Any]] = []
    prev_ts: int | None = None
    prev_time_str: str = ""
    last_vw = 0.0
    last_sd = 0.0
    last_poc = 0.0
    last_vah = 0.0
    last_val = 0.0
    last_cvd = 0

    spreads_all: List[float] = []
    tick_freqs: List[float] = []
    cadences_ms: List[float] = []

    for tstr in sorted(min_clean.keys()):
        row = min_clean[tstr]
        t_sec = int(row["ts_unix"])
        missing_before = 0
        if prev_ts is not None:
            diff_min = int((t_sec - prev_ts) // 60)
            if diff_min > 1:
                missing_before = diff_min - 1
                gaps.append({
                    "afterIndex": len(bars) - 1,
                    "from": prev_time_str,
                    "to": tstr,
                    "missingBars": missing_before,
                })

        fl = flow_clean.get(tstr)
        o = round(float(row["open"]), 2)
        h = round(float(row["high"]), 2)
        l = round(float(row["low"]), 2)
        c = round(float(row["close"]), 2)
        v = int(round(float(row["tickVolume"])))
        tk = int(row["ticks"])
        sp = round(float(row["spreadAvg"]), 4)
        bv = round(float(row["bidVol"]), 2)
        av = round(float(row["askVol"]), 2)
        imb = round(float(row["imbalance"]), 4)
        du = int(row["depthUpdates"])

        if fl:
            d = int(round(float(fl["delta"])))
            cvd = int(round(float(fl["cvd"])))
            vw = round(float(fl["vwapDay"]) if fl["vwapDay"] is not None else c, 2)
            sd = round(float(fl["sdDay"]) if fl["sdDay"] is not None else 0.0, 2)
            poc = round(float(fl["poc"]) if fl["poc"] is not None else c, 2)
            vah = round(float(fl["vah"]) if fl["vah"] is not None else c, 2)
            val = round(float(fl["val"]) if fl["val"] is not None else c, 2)
            lb = round(float(fl["ladderBid"]) if fl["ladderBid"] is not None else cfg["domStep"] * 10, 3)
            la = round(float(fl["ladderAsk"]) if fl["ladderAsk"] is not None else cfg["domStep"] * 10, 3)
            last_cvd, last_vw, last_sd, last_poc, last_vah, last_val = cvd, vw, sd, poc, vah, val
        else:
            d = 0
            cvd = last_cvd
            vw = last_vw or c
            sd = last_sd
            poc = last_poc or c
            vah = last_vah or c
            val = last_val or c
            lb = round(cfg["domStep"] * 10, 3)
            la = round(cfg["domStep"] * 10, 3)

        bars.append([
            t_sec, o, h, l, c, v, tk, d, cvd, sp, bv, av, imb, du,
            vw, sd, poc, vah, val, lb, la, missing_before
        ])

        if sp > 0:
            spreads_all.append(sp)
        tick_freqs.append(round(tk / 60.0, 2))
        if du > 0:
            cadences_ms.append(round(60000.0 / du, 1))

        prev_ts = t_sec
        prev_time_str = tstr

    trades = parse_trades(pc_sym_dir) if (pc_sym_dir and (pc_sym_dir / "trades.csv").exists()) else parse_trades(sym_dir)
    exec_latencies = [t["latencyMs"] for t in trades if t.get("latencyMs") is not None]

    # Pick a sensible default replay start index (last ~200 bars remaining to replay)
    total_bars = len(bars)
    default_replay_idx = max(120, total_bars - 150) if total_bars > 160 else max(0, total_bars - 1)

    payload = {
        "symbol": sym,
        "displayName": cfg["displayName"],
        "label": cfg["label"],
        "digits": cfg["digits"],
        "pipSize": cfg["pipSize"],
        "contractSize": cfg["contractSize"],
        "domStep": cfg["domStep"],
        "defaultLot": cfg["defaultLot"],
        "defaultReplayIndex": default_replay_idx,
        "schema": SCHEMA,
        "stats": {
            "totalBars": total_bars,
            "startTimeUtc": datetime.fromtimestamp(bars[0][0], tz=timezone.utc).strftime("%Y-%m-%d %H:%M") if bars else None,
            "endTimeUtc": datetime.fromtimestamp(bars[-1][0], tz=timezone.utc).strftime("%Y-%m-%d %H:%M") if bars else None,
            "lastClose": bars[-1][4] if bars else 0.0,
            "medianSpread": round(statistics.median(spreads_all), 4) if spreads_all else 0.0,
            "medianTickFreq": round(statistics.median(tick_freqs), 2) if tick_freqs else 0.0,
            "medianCadenceMs": round(statistics.median(cadences_ms), 1) if cadences_ms else 250.0,
            "medianExecLatencyMs": round(statistics.median(exec_latencies), 1) if exec_latencies else None,
            "latestExecLatencyMs": exec_latencies[-1] if exec_latencies else None,
            "gapEvents": len(gaps),
            "totalMissingBars": sum(g["missingBars"] for g in gaps),
        },
        "gaps": gaps,
        "trades": trades,
        "bars": bars,
    }
    return payload


def main() -> None:
    DOCS_DATA_DIR.mkdir(parents=True, exist_ok=True)
    generated_at = datetime.now(timezone.utc).isoformat()
    meta: Dict[str, Any] = {
        "generated_at_utc": generated_at,
        "source": "data/live/ (Pepperstone Demo #5258778 Continuous M1 + Order Flow + Execution Logs)",
        "symbols": {},
    }

    for sym, cfg in SYMBOL_CONFIG.items():
        payload = build_symbol(sym, cfg)
        out_path = DOCS_DATA_DIR / f"dc_{sym}.json"
        out_path.write_text(json.dumps(payload, separators=(",", ":"), ensure_ascii=False), encoding="utf-8")
        size_kb = out_path.stat().st_size / 1024.0
        print(f"Wrote {out_path.name}: {payload['stats']['totalBars']} bars, {payload['stats']['gapEvents']} gaps, {size_kb:.1f} KB")
        meta["symbols"][sym] = {
            "displayName": cfg["displayName"],
            "label": cfg["label"],
            "digits": cfg["digits"],
            "pipSize": cfg["pipSize"],
            "contractSize": cfg["contractSize"],
            "file": f"data/dc_{sym}.json",
            "stats": payload["stats"],
        }

    meta_path = DOCS_DATA_DIR / "dc_meta.json"
    meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {meta_path.name} ({meta_path.stat().st_size / 1024.0:.1f} KB)")


if __name__ == "__main__":
    main()
