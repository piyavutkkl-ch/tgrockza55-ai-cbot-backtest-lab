"""
Unit Tests for Phase 1: HybridDataMerger & V5 Demo Data Sanitizer
"""

import csv
import math
import os
import shutil
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from research.hybrid_data_merger import (
    classify_session_zone,
    sanitize_live_minute_files,
    HybridDataMerger,
)


class MockMCPClient:
    """Offline deterministic MCP stub returning cTrader trendbars and sessions."""

    url = "mock://ctrader-mcp"

    def ensure_initialized(self) -> bool:
        return True

    def get_symbol_sessions(self, symbol: str):
        return {
            "symbolName": symbol,
            "timeZone": "Eastern Standard Time",
            "sessions": [{"startDayOfWeek": "Sunday", "endDayOfWeek": "Monday"}],
        }

    def fetch_and_cache_m1_bars(self, symbol: str, start_utc: datetime, end_utc: datetime):
        return [
            {"time": "2026-11-16 06:58", "open": 3850.0, "high": 3851.0, "low": 3849.5, "close": 3850.5, "tickVolume": 120.0},
            {"time": "2026-11-16 06:59", "open": 3850.5, "high": 3852.0, "low": 3850.0, "close": 3851.5, "tickVolume": 150.0},  # Gap bar!
            {"time": "2026-11-16 07:00", "open": 3851.5, "high": 3853.0, "low": 3851.0, "close": 3852.0, "tickVolume": 180.0},
        ]


class TestHybridDataMerger(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = Path(tempfile.mkdtemp(prefix="test_hybrid_v5_"))
        self.sym_dir = self.tmp_dir / "XAUUSD"
        self.sym_dir.mkdir(parents=True)

    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_01_session_and_transition_zones(self):
        cases = [
            (datetime(2026, 11, 16, 3, 15, tzinfo=timezone.utc), ("ASIA", False)),
            (datetime(2026, 11, 16, 7, 30, tzinfo=timezone.utc), ("ASIA_TO_LONDON", True)),
            (datetime(2026, 11, 16, 10, 0, tzinfo=timezone.utc), ("LONDON", False)),
            (datetime(2026, 11, 16, 13, 15, tzinfo=timezone.utc), ("LONDON_TO_NY", True)),
            (datetime(2026, 11, 16, 16, 0, tzinfo=timezone.utc), ("NY", False)),
            (datetime(2026, 11, 16, 21, 10, tzinfo=timezone.utc), ("NY_TO_CLOSE", True)),
            (datetime(2026, 11, 16, 22, 30, tzinfo=timezone.utc), ("OVERNIGHT", False)),
        ]
        for dt, expected in cases:
            self.assertEqual(classify_session_zone(dt), expected)

    def test_02_sanitize_corrupt_and_duplicate_ghost_rows(self):
        min_fp = self.sym_dir / "min-2026-11.csv"
        flow_fp = self.sym_dir / "flow-2026-11.csv"

        min_header = [
            "time", "open", "high", "low", "close", "tickVolume", "ticks",
            "spreadAvg", "spreadMax", "books", "bidVol", "askVol", "imbalance", "depthUpdates",
        ]
        min_rows = [
            # Valid bar
            ["2026-11-16 06:58", "3850.0", "3851.0", "3849.5", "3850.5", "120", "65", "0.12", "0.15", "28", "2000", "2100", "-0.024", "70"],
            # Ghost duplicate at same minute (ticks=0, spreadAvg='') AFTER valid row
            ["2026-11-16 06:58", "3850.1", "3851.0", "3849.5", "3850.6", "120", "0", "", "", "0", "", "", "", "70"],
            # Corrupt NaN close -> must be dropped
            ["2026-11-16 06:59", "3850.5", "3852.0", "3850.0", "NaN", "150", "80", "0.11", "0.14", "29", "2100", "1900", "0.05", "85"],
            # Ghost row BEFORE valid row at 07:00
            ["2026-11-16 07:00", "3851.2", "3853.0", "3851.0", "3852.1", "180", "0", "", "", "0", "", "", "", "95"],
            ["2026-11-16 07:00", "3851.5", "3853.0", "3851.0", "3852.0", "180", "90", "0.13", "0.16", "30", "2300", "2000", "0.07", "95"],
        ]
        with min_fp.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(min_header)
            w.writerows(min_rows)

        flow_header = ["time", "ticks", "delta", "cvd", "vwapDay", "sdDay", "vwapSession", "poc", "vah", "val", "sweep", "ladderBid", "ladderAsk"]
        flow_rows = [
            ["2026-11-16 06:58", "65", "12", "110", "3848.0", "1.5", "3849.0", "3850.0", "3851.0", "3847.0", "", "1.2", "1.3"],
            ["2026-11-16 07:00", "90", "-8", "102", "3848.5", "1.6", "3849.2", "3850.5", "3851.5", "3847.5", "PL", "1.1", "1.2"],
        ]
        with flow_fp.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(flow_header)
            w.writerows(flow_rows)

        min_clean, flow_clean, stats = sanitize_live_minute_files([min_fp], [flow_fp])
        self.assertEqual(stats["clean_live_min_rows"], 2)
        self.assertEqual(stats["dropped_corrupt_ohlc"], 1)
        self.assertEqual(stats["dropped_incomplete_ghost"], 2)
        self.assertAlmostEqual(min_clean["2026-11-16 07:00"]["spreadAvg"], 0.13)
        self.assertEqual(min_clean["2026-11-16 06:58"]["ticks"], 65)

        merger = HybridDataMerger(live_base=self.tmp_dir, mcp_client=MockMCPClient())
        dataset = merger.load_merged_dataset("XAUUSD", fetch_ctrader=True)
        bars = dataset["bars"]
        self.assertEqual(len(bars), 3)

        # Bar 0: 06:58 HYBRID_FULL in ASIA
        self.assertEqual(bars[0]["provenance"], "HYBRID_FULL")
        self.assertTrue(bars[0]["has_l2_dom"])
        self.assertEqual(bars[0]["session_zone"], "ASIA")

        # Bar 1: 06:59 dropped NaN live row, cleanly gap-filled by cTrader OHLCV ONLY
        self.assertEqual(bars[1]["provenance"], "CTRADER_OHLCV_ONLY")
        self.assertFalse(bars[1]["has_l2_dom"])
        self.assertIsNone(bars[1]["spreadAvg"])

        # Bar 2: 07:00 HYBRID_FULL in ASIA_TO_LONDON transition
        self.assertEqual(bars[2]["provenance"], "HYBRID_FULL")
        self.assertEqual(bars[2]["session_zone"], "ASIA_TO_LONDON")
        self.assertTrue(bars[2]["is_session_transition"])


if __name__ == "__main__":
    unittest.main()
