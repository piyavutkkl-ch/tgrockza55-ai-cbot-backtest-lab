"""
CLI Runner: Scalping & Intraday Chart Condition Discovery Engine (All 3 Symbols)
================================================================================
Runs zero-lookahead 3-round discovery simultaneously across XAUUSD, BTCUSD, and ETHUSD,
fusing Tier 1 Live Microstructure + Tier 2 cTrader Real MTF OHLCV.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from research.pattern_discovery.library_builder import build_trading_condition_library


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    t0 = time.perf_counter()
    print("=" * 84)
    print("V5 SCALPING & INTRADAY PATTERN DISCOVERY ENGINE (TIER 1 LIVE + TIER 2 CTRADER MTF)")
    print("=" * 84)

    lib = build_trading_condition_library(
        symbols=("XAUUSD", "BTCUSD", "ETHUSD"),
        fetch_ctrader=True,
    )

    elapsed = time.perf_counter() - t0
    json_path = REPO_ROOT / "docs" / "data" / "trading_condition_library.json"
    state_path = REPO_ROOT / "docs" / "data" / "pattern_discovery_state.json"
    report_path = REPO_ROOT / "TRADING_CONDITION_LIBRARY_REPORT.md"

    for sym, sdata in lib["symbols"].items():
        da = sdata["data_audit"]
        sc = sdata["summary_counts"]
        vb = sc["validation_breakdown"]
        cp = sdata["confluence_proof"]
        r2_sum = sdata.get("round2_highlights", {}).get("round1_vs_round2_summary", {})
        print(
            f"\n[{sym}] M1={da['total_m1_bars']:,} | LiveDOM={da['live_microstructure_bars']:,} "
            f"| Flow={da['live_order_flow_bars']:,} | TF={da['tf_sources']}"
        )
        print(
            f"  Tested={sc['total_conditions_tested']} (Single={sc['single_count']}, "
            f"Seq={sc['sequential_count']}, MTF={sc['mtf_count']}, Session={sc.get('session_count', 0)}) "
            f"| Archived JSON={sc.get('conditions_archived_in_json', len(sdata['conditions']))}"
        )
        print(
            f"  Yield R1={r2_sum.get('round1_validated_or_regime', 0)}/{r2_sum.get('round1_tested', 0)} "
            f"| R2={r2_sum.get('round2_validated_or_regime', 0)}/{r2_sum.get('round2_tested', 0)}"
        )
        print(
            f"  Validation: VALIDATED_OOS={vb.get('VALIDATED_OOS', 0)}, "
            f"REGIME_SPECIFIC={vb.get('REGIME_SPECIFIC_EDGE', 0)}, "
            f"RARE_HIGH_EDGE={vb.get('RARE_HIGH_EDGE', 0)}, "
            f"IS_ONLY_OVERFIT={vb.get('IS_ONLY_OVERFIT', 0)}, "
            f"NO_EDGE={vb.get('NO_EDGE', 0)}, INSUFFICIENT={vb.get('INSUFFICIENT_DATA', 0)}"
        )
        print(f"  Confluence Verdict: {cp['verdict']} -> Tiers={cp['tiers']}")
        for top in sdata["conditions"][:5]:
            print(
                f"    #{top['rank']} [R{top.get('discovery_round', 1)}/{top.get('session_scope', 'ALL')}] "
                f"{top['condition_name']} [{top['direction']}] "
                f"N={top['sample_size']['total']} ({top['sample_size']['in_sample']}/{top['sample_size']['out_of_sample']}) "
                f"| OOS P={top['probability']['oos_dir_prob']*100:.1f}% "
                f"| WR={top['win_rate']['oos']*100:.1f}% "
                f"| Exp={top['expectancy']['oos_usd']:+.4f} USD "
                f"| PF={top['profit_factor']['oos']:.2f} "
                f"| {top['validation']['status']}"
            )
        if sym in ("XAUUSD", "BTCUSD"):
            ob_tops = [c for c in sdata["conditions"] if c.get("discovery_round") == 2 and c.get("session_scope") == "ALL"][:3]
            if ob_tops:
                print(f"  Top Round 2 OrderBook/Micro ({sym}):")
                for obc in ob_tops:
                    print(
                        f"    * #{obc['rank']} {obc['condition_name']} [{obc['direction']}] "
                        f"N={obc['sample_size']['total']} | Exp={obc['expectancy']['oos_usd']:+.4f} USD "
                        f"| PF={obc['profit_factor']['oos']:.2f} | {obc['validation']['status']}"
                    )
            pb_map = sdata.get("round2_highlights", {}).get("session_playbook", {})
            if pb_map:
                print(f"  Session Playbook ({sym}):")
                for zn, zp in pb_map.items():
                    print(
                        f"    * {zn}: {zp['best_condition']} [{zp['direction']}] N={zp['sample_size']} "
                        f"| SesExp={zp['oos_expectancy_usd']:+.4f} (Lift {zp['delta_oos_exp_vs_allday']:+.4f}) "
                        f"| PF={zp['oos_profit_factor']:.2f} | {zp['validation_status']}"
                    )

    print(
        f"\nCompleted in {elapsed:.2f}s | Outputs:\n"
        f"  - {json_path} ({json_path.stat().st_size / 1024:.1f} KB)\n"
        f"  - {state_path} ({state_path.stat().st_size / 1024:.1f} KB)\n"
        f"  - {report_path} ({report_path.stat().st_size / 1024:.1f} KB)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
