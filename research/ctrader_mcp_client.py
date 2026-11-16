"""
cTrader Desktop MCP HTTP JSON-RPC Client
=========================================
Connects directly to the local cTrader Desktop MCP server (default http://127.0.0.1:9876/mcp/)
using Python standard library only. Caches historical M1 OHLCV trendbars and broker session
schedules locally under %LOCALAPPDATA%\\BacktestLab\\ctrader_cache\\ so backtests and
evolution engines never re-record data that cTrader already stores retroactively.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


DEFAULT_MCP_URL = "http://127.0.0.1:9876/mcp/"


def _default_cache_dir() -> Path:
    local_app = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    cache = Path(local_app) / "BacktestLab" / "ctrader_cache"
    cache.mkdir(parents=True, exist_ok=True)
    return cache


class CTraderMCPClient:
    """Lightweight JSON-RPC 2.0 client over Streamable HTTP for cTrader Desktop MCP."""

    def __init__(self, url: str = DEFAULT_MCP_URL, timeout: float = 15.0) -> None:
        self.url = url
        self.timeout = timeout
        self.session_id: Optional[str] = None
        self._req_id = 0
        self.cache_dir = _default_cache_dir()

    def _next_id(self) -> int:
        self._req_id += 1
        return self._req_id

    @staticmethod
    def _parse_response_body(raw_text: str) -> Optional[Dict[str, Any]]:
        txt = raw_text.strip()
        if not txt:
            return None
        if txt.startswith("{"):
            return json.loads(txt)
        # Parse Server-Sent Events (SSE) payloads if returned by streamable HTTP
        last_obj = None
        for line in txt.splitlines():
            if line.startswith("data:"):
                payload = line[5:].strip()
                if payload and payload != "[DONE]":
                    try:
                        last_obj = json.loads(payload)
                    except json.JSONDecodeError:
                        continue
        return last_obj

    def _post(self, method: str, params: Optional[Dict[str, Any]] = None, is_notification: bool = False) -> Optional[Dict[str, Any]]:
        body_obj: Dict[str, Any] = {"jsonrpc": "2.0", "method": method}
        if not is_notification:
            body_obj["id"] = self._next_id()
        if params is not None:
            body_obj["params"] = params

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }
        if self.session_id:
            headers["Mcp-Session-Id"] = self.session_id

        req = urllib.request.Request(
            self.url,
            data=json.dumps(body_obj).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            sid = resp.headers.get("Mcp-Session-Id") or resp.headers.get("mcp-session-id")
            if sid:
                self.session_id = sid
            raw = resp.read().decode("utf-8", errors="replace")
            return self._parse_response_body(raw)

    def ensure_initialized(self) -> bool:
        """Initializes an MCP session if not already active. Returns False if offline."""
        if self.session_id:
            return True
        try:
            res = self._post(
                "initialize",
                {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "cbot-atgvt-hybrid-merger", "version": "1.0.0"},
                },
            )
            if not res or "error" in res:
                return False
            try:
                self._post("notifications/initialized", {}, is_notification=True)
            except Exception:
                pass
            return True
        except Exception:
            return False

    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Invokes a cTrader MCP tool and returns its parsed JSON content, or None on failure."""
        if not self.ensure_initialized():
            return None
        try:
            res = self._post("tools/call", {"name": tool_name, "arguments": arguments})
            if not res or "error" in res:
                return None
            result = res.get("result") or {}
            if result.get("structuredContent") and isinstance(result["structuredContent"], dict):
                return result["structuredContent"]
            for item in result.get("content") or []:
                if item.get("type") == "text" and item.get("text"):
                    return json.loads(item["text"])
        except Exception:
            return None
        return None

    def get_symbol_sessions(self, symbol: str, force_refresh: bool = False) -> Optional[Dict[str, Any]]:
        """Loads trading session schedule for symbol from MCP or local cache."""
        cache_file = self.cache_dir / f"{symbol}_sessions.json"
        if not force_refresh:
            live = self.call_tool("get_symbol_sessions", {"symbolName": symbol})
            if live and live.get("sessions"):
                live["cached_at_utc"] = datetime.now(timezone.utc).isoformat()
                cache_file.write_text(json.dumps(live, indent=2), encoding="utf-8")
                return live
        else:
            live = self.call_tool("get_symbol_sessions", {"symbolName": symbol})
            if live and live.get("sessions"):
                live["cached_at_utc"] = datetime.now(timezone.utc).isoformat()
                cache_file.write_text(json.dumps(live, indent=2), encoding="utf-8")
                return live

        if cache_file.exists():
            try:
                return json.loads(cache_file.read_text(encoding="utf-8"))
            except Exception:
                return None
        return None

    def fetch_and_cache_m1_bars(
        self,
        symbol: str,
        start_utc: datetime,
        end_utc: datetime,
    ) -> List[Dict[str, Any]]:
        """
        Incrementally fetches M1 OHLCV bars from cTrader MCP in 950-bar slices (under 1000 cap)
        and persists to %LOCALAPPDATA%\\BacktestLab\\ctrader_cache\\<symbol>_m1.json.
        """
        cache_file = self.cache_dir / f"{symbol}_m1.json"
        cached: Dict[str, Dict[str, Any]] = {}
        if cache_file.exists():
            try:
                rows = json.loads(cache_file.read_text(encoding="utf-8"))
                for r in rows:
                    if isinstance(r, dict) and r.get("time"):
                        cached[r["time"]] = r
            except Exception:
                cached = {}

        if not self.ensure_initialized():
            return sorted(cached.values(), key=lambda x: x["time"])

        # Walk backward from end_utc in 14-hour slices (<= 840 M1 bars per request < 1000 cap)
        cur_end = end_utc.astimezone(timezone.utc)
        target_start = start_utc.astimezone(timezone.utc)
        added = 0

        # Avoid refetching ranges completely covered if start..end already well populated,
        # unless tail minutes are recent (always refresh last 24h cleanly).
        cached_times = sorted(cached.keys())
        earliest_cached = cached_times[0] if cached_times else None
        latest_cached = cached_times[-1] if cached_times else None
        recent_cutoff = (end_utc.astimezone(timezone.utc) - timedelta(hours=24)).strftime("%Y-%m-%d %H:%M")

        while cur_end > target_start:
            cur_start = max(target_start, cur_end - timedelta(hours=14))
            s_key = cur_start.strftime("%Y-%m-%d %H:%M")
            e_key = cur_end.strftime("%Y-%m-%d %H:%M")

            # Skip strictly interior ranges already fetched and older than the 24h refresh window
            if earliest_cached and latest_cached and s_key >= earliest_cached and e_key <= min(latest_cached, recent_cutoff):
                count_in_slice = sum(1 for k in cached_times if s_key <= k <= e_key)
                is_weekend_gap = (symbol == "XAUUSD" and cur_start.weekday() == 5 and cur_end.weekday() == 5)
                if count_in_slice >= 60 or is_weekend_gap:
                    cur_end = cur_start
                    continue

            payload = self.call_tool(
                "get_trendbars",
                {
                    "symbolName": symbol,
                    "timeframe": "m1",
                    "from": cur_start.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "to": cur_end.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "limit": 1000,
                },
            )
            if payload and isinstance(payload.get("bars"), list):
                for b in payload["bars"]:
                    ts_iso = b.get("timestamp", "")
                    if len(ts_iso) < 16:
                        continue
                    t_key = ts_iso[:16].replace("T", " ")
                    row = {
                        "time": t_key,
                        "open": float(b["open"]),
                        "high": float(b["high"]),
                        "low": float(b["low"]),
                        "close": float(b["close"]),
                        "tickVolume": float(b.get("volume", 0) or 0),
                    }
                    if t_key not in cached:
                        added += 1
                    cached[t_key] = row

            cur_end = cur_start

        sorted_bars = sorted(cached.values(), key=lambda x: x["time"])
        if added > 0 or not cache_file.exists():
            tmp = cache_file.with_suffix(".tmp")
            tmp.write_text(json.dumps(sorted_bars), encoding="utf-8")
            tmp.replace(cache_file)
        return sorted_bars
