"""
Unit & Integration Tests for Phase 2 Session Regime Engine & Blowup Forensics
=============================================================================
Verifies:
1. Strict zero-lookahead invariants (future bars cannot mutate bar k features/regime).
2. Entry signals require real L2 DOM & Tick Spread provenance (never fake DOM gaps).
3. Zero-SL Blowup Forensics records exact worst regime/session transition & diagnosis
   without permanently banning strategies under V5 Regime-Matched Memory.
4. MarketIntelligenceEngine exposes V5 7-zone session/transition classification while
   preserving full V4 compatibility.
"""

import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "research"))

from research.hybrid_data_merger import HybridDataMerger, SESSION_ZONES
from research.market_intelligence_engine import MarketIntelligenceEngine
from research.session_regime_forensics import (
    PARAMETER_PROFILES,
    analyze_symbol,
    enrich_merged_bars,
    evaluate_all_strategy_signals,
    simulate_profile_chronological,
)


def _make_bar(
    dt: datetime,
    price: float,
    high_off: float = 0.8,
    low_off: float = 0.8,
    delta: float = 12.0,
    imb: float = 0.03,
    vwap: float = 3900.0,
    sd: float = 2.0,
    has_live: bool = True,
) -> Dict[str, Any]:
    from research.hybrid_data_merger import classify_session_zone

    zone, is_trans = classify_session_zone(dt)
    return {
        "time": dt.strftime("%Y-%m-%d %H:%M"),
        "ts_unix": int(dt.timestamp()),
        "open": price,
        "high": price + high_off,
        "low": price - low_off,
        "close": price,
        "tickVolume": 120.0,
        "ticks": 90 if has_live else 0,
        "spreadAvg": 0.14 if has_live else None,
        "imbalance": imb if has_live else None,
        "delta": delta if has_live else None,
        "vwapDay": vwap if has_live else None,
        "sdDay": sd if has_live else None,
        "sweep": "",
        "nextImpact": "",
        "minToNext": 999.0,
        "lastImpact": "",
        "minSinceLast": 999.0,
        "has_l2_dom": has_live,
        "has_real_spread": has_live,
        "has_order_flow": has_live,
        "session_zone": zone,
        "is_session_transition": is_trans,
    }


class TestSessionRegimeForensics(unittest.TestCase):
    def test_01_zero_lookahead_invariance(self):
        base_dt = datetime(2026, 11, 2, 6, 0, tzinfo=timezone.utc)
        bars: List[Dict[str, Any]] = []
        for i in range(90):
            bars.append(_make_bar(base_dt + timedelta(minutes=i), 3900.0 + (i % 5) * 0.4))

        prefix_only = enrich_merged_bars(bars[:70], "XAUUSD")
        mutated_future = bars[:70] + [
            _make_bar(base_dt + timedelta(minutes=70 + j), 4500.0 + j * 50.0, delta=-500.0)
            for j in range(20)
        ]
        with_future = enrich_merged_bars(mutated_future, "XAUUSD")

        for key in ("ema20", "ema50", "atr14", "adx14", "macro_regime", "session_zone", "vwap"):
            self.assertEqual(prefix_only[69][key], with_future[69][key])

    def test_02_live_provenance_required_for_signal(self):
        base_dt = datetime(2026, 11, 2, 8, 15, tzinfo=timezone.utc)
        bars = [
            _make_bar(base_dt + timedelta(minutes=i), 3895.0, vwap=3900.0, sd=2.0, delta=25.0, has_live=(i >= 60))
            for i in range(65)
        ]
        enriched = enrich_merged_bars(bars, "XAUUSD")

        gap_sigs = evaluate_all_strategy_signals(enriched[55], "XAUUSD")
        self.assertTrue(all(v == "NONE" for v in gap_sigs.values()))

        live_sigs = evaluate_all_strategy_signals(enriched[62], "XAUUSD")
        self.assertEqual(live_sigs["STR-002"], "BUY")

    def test_03_zero_sl_blowup_forensics_and_no_permanent_ban(self):
        # Build sequence: ASIA calm range (STR-002 BUY triggers), then sharp crash in ASIA_TO_LONDON
        start = datetime(2026, 11, 2, 5, 30, tzinfo=timezone.utc)
        bars: List[Dict[str, Any]] = []
        for i in range(110):
            dt = start + timedelta(minutes=i)
            if i < 65:
                # Stable around 3900, slight dip below vwap at i=60..63 so STR-002 enters BUY
                price = 3897.0 if 60 <= i <= 63 else 3900.0
                bars.append(_make_bar(dt, price, high_off=0.5, low_off=0.5, delta=15.0, imb=0.02, vwap=3900.0, sd=2.0))
            else:
                # Transition after 07:00 UTC (ASIA_TO_LONDON): violent crash downwards -20 USD
                drop = (i - 64) * 1.2
                bars.append(
                    _make_bar(
                        dt,
                        3900.0 - drop,
                        high_off=0.3,
                        low_off=1.5,
                        delta=-35.0,
                        imb=-0.04,
                        vwap=3900.0 - drop * 0.3,
                        sd=2.5,
                    )
                )

        enriched = enrich_merged_bars(bars, "XAUUSD")
        sig_rows = [evaluate_all_strategy_signals(b, "XAUUSD") for b in enriched]
        zero_sl_prof = [p for p in PARAMETER_PROFILES if p["name"] == "FORENSIC_ZERO_SL"][0]

        trades, forensics = simulate_profile_chronological(enriched, sig_rows, "XAUUSD", "STR-002", zero_sl_prof, split_idx=80)
        self.assertGreaterEqual(len(trades), 1)
        self.assertGreaterEqual(len(forensics), 1)
        ev = forensics[0]
        self.assertEqual(ev["sl_mode"], "ZERO_SL")
        self.assertGreaterEqual(ev["mae_atr"], 5.5)
        self.assertTrue(ev["diagnosis"])
        self.assertTrue(ev["recommended_countermeasure"])

        # Now feed minimal temp live dataset into analyze_symbol to ensure non-banning status
        with tempfile.TemporaryDirectory() as tmp:
            sym_dir = Path(tmp) / "XAUUSD"
            sym_dir.mkdir(parents=True, exist_ok=True)
            lines = ["time,open,high,low,close,tickVolume,ticks,spreadAvg,spreadMax,books,bidVol,askVol,imbalance,depthUpdates,nextNews,nextImpact,minToNext,lastNews,lastImpact,minSinceLast"]
            flow_lines = ["time,delta,cvd,vwapDay,sdDay,vwapSession,poc,vah,val,sweep,ladderBid,ladderAsk"]
            for b in bars:
                lines.append(f"{b['time']},{b['open']},{b['high']},{b['low']},{b['close']},120,80,0.14,0.18,25,500,500,{b['imbalance']},10,,,999,,,999")
                flow_lines.append(f"{b['time']},{b['delta']},0,{b['vwapDay']},{b['sdDay']},{b['vwapDay']},0,0,0,,0,0")
            (sym_dir / "min-2026-11.csv").write_text("\n".join(lines), encoding="utf-8")
            (sym_dir / "flow-2026-11.csv").write_text("\n".join(flow_lines), encoding="utf-8")

            merger = HybridDataMerger(live_base=Path(tmp))
            res = analyze_symbol("XAUUSD", merger=merger, fetch_ctrader=False)
            self.assertEqual(res["status"], "COMPLETED")
            # Every strategy stays active in Regime-Matched Memory (no permanent ban)
            self.assertEqual(res["strategy_memory"]["STR-002"]["status"], "REGIME_MATCHED_ACTIVE")

    def test_04_market_intelligence_7_zone_classification(self):
        engine = MarketIntelligenceEngine("XAUUSD")
        checks = [
            (datetime(2026, 11, 2, 3, 15, tzinfo=timezone.utc), "ASIA", False),
            (datetime(2026, 11, 2, 7, 25, tzinfo=timezone.utc), "ASIA_TO_LONDON", True),
            (datetime(2026, 11, 2, 10, 0, tzinfo=timezone.utc), "LONDON", False),
            (datetime(2026, 11, 2, 13, 10, tzinfo=timezone.utc), "LONDON_TO_NY", True),
            (datetime(2026, 11, 2, 16, 45, tzinfo=timezone.utc), "NY", False),
            (datetime(2026, 11, 2, 21, 15, tzinfo=timezone.utc), "NY_TO_CLOSE", True),
            (datetime(2026, 11, 2, 23, 30, tzinfo=timezone.utc), "OVERNIGHT", False),
        ]
        seen = set()
        for dt, exp_zone, exp_trans in checks:
            ctx = engine.analyze_time_context(dt)
            self.assertEqual(ctx["session_zone"], exp_zone)
            self.assertEqual(ctx["is_session_transition"], exp_trans)
            seen.add(ctx["session_zone"])
        self.assertEqual(seen, set(SESSION_ZONES))


if __name__ == "__main__":
    unittest.main()
