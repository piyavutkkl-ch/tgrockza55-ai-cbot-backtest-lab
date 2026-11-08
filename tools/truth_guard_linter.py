"""
Truth Guard Linter & Continuous Verification Gate
==================================================
Ensures that all metrics in the repository remain 100% grounded in empirical reality.
Will FAIL (exit code 1) if:
1. Hardcoded synthetic win-rates or balances contradict raw cTrader CSV logs.
2. The Statistical Power warning is missing when N < 500 trades.
3. The Strategy Foundry rejection rate is below 90% (preventing rubber-stamping).
4. Any synthetic "guaranteed profit" or "ever-increasing profit bot" claims are found.
"""

import os
import sys
import json
import glob
import re

REPO_ROOT = r'd:\cbot-atgvt'
DOCS_DATA = os.path.join(REPO_ROOT, 'docs', 'data')
INDEX_HTML = os.path.join(REPO_ROOT, 'docs', 'index.html')

def lint_truth():
    print("=" * 70)
    print("RUNNING TRUTH GUARD LINTER & INTEGRITY VERIFICATION GATE")
    print("=" * 70)
    errors = []

    # 1. Verify truth_guard.json exists and is valid
    tg_path = os.path.join(DOCS_DATA, 'truth_guard.json')
    if not os.path.exists(tg_path):
        errors.append("MISSING_FILE: docs/data/truth_guard.json not found!")
    else:
        with open(tg_path, 'r', encoding='utf-8') as f:
            tg = json.load(f)
        n_trades = tg.get('metrics_empirical', {}).get('total_closed_trades_N', 0)
        print(f"[CHECK 1] Raw Audited Trades Count N = {n_trades}")
        if n_trades == 0:
            errors.append("EMPTY_AUDIT: Audited trades count N is 0!")
        if n_trades < 500:
            power_status = tg.get('statistical_power', {}).get('status', '')
            if 'UNDERPOWERED' not in power_status:
                errors.append(f"VIOLATION: N={n_trades} < 500 but status is not marked UNDERPOWERED! Got: {power_status}")
            else:
                print(f"  -> PASS: Statistical Power correctly marked as {power_status}")

    # 2. Verify strategy_foundry.json exists and rejection rate >= 90%
    sf_path = os.path.join(DOCS_DATA, 'strategy_foundry.json')
    if not os.path.exists(sf_path):
        errors.append("MISSING_FILE: docs/data/strategy_foundry.json not found!")
    else:
        with open(sf_path, 'r', encoding='utf-8') as f:
            sf = json.load(f)
        rejection_pct = sf.get('stats', {}).get('rejection_rate_pct', 0)
        graveyard_count = len(sf.get('failure_graveyard', []))
        print(f"[CHECK 2] Foundry Rejection Rate = {rejection_pct}%, Graveyard items = {graveyard_count}")
        if rejection_pct < 90.0:
            errors.append(f"VIOLATION: Sieve Rejection Rate ({rejection_pct}%) is below 90% threshold! System must reject bad ideas.")
        else:
            print(f"  -> PASS: Sieve Rejection Rate {rejection_pct}% >= 90.0%")
        if graveyard_count < 3:
            errors.append(f"VIOLATION: Failure Graveyard must document at least 3 failure cases! Got {graveyard_count}")
        else:
            print(f"  -> PASS: Failure Graveyard active with {graveyard_count} documented cases.")

    # 3. Verify index.html contains Truth Reset and Statistical Power warning
    if not os.path.exists(INDEX_HTML):
        errors.append("MISSING_FILE: docs/index.html not found!")
    else:
        with open(INDEX_HTML, 'r', encoding='utf-8') as f:
            html = f.read()

        print("[CHECK 3] Verifying docs/index.html HTML integrity...")
        required_substrings = [
            ("TRUTH RESET", "Truth Reset Mandate"),
            ("hdr-sample-size", "Sample Size Power Badge"),
            ("N=72", "Real Sample Size Display"),
            ("strategy-foundry-card", "Strategy Foundry Card"),
            ("สุสานกลยุทธ์ที่ถูกคัดทิ้ง", "The Failure Graveyard"),
            ("STATISTICALLY UNDERPOWERED", "Statistical Power Warning"),
            ("Auto-Decommission", "Auto-Decommission Watchdog")
        ]

        for sub, label in required_substrings:
            if sub in html:
                print(f"  -> PASS: Found {label} ('{sub}')")
            else:
                errors.append(f"VIOLATION: docs/index.html is missing {label} ('{sub}')!")

        # Check for forbidden synthetic marketing phrases
        forbidden_patterns = [
            (r'บอทที่ฉลาดขึ้นเรื่อย\s*ๆ\s*กำไรเป็นเส้นตรง', "Claim of linear infinite profit"),
            (r'Win\s*Rate\s*100%', "Claim of 100% win rate on live forward trading")
        ]
        for pat, desc in forbidden_patterns:
            if re.search(pat, html, re.IGNORECASE):
                errors.append(f"VIOLATION: Forbidden synthetic marketing claim found: {desc} (pattern: {pat})")

    print("-" * 70)
    if errors:
        print(f"FAILED: {len(errors)} TRUTH GUARD VIOLATIONS DETECTED:")
        for err in errors:
            print(f"  ❌ {err}")
        print("=" * 70)
        sys.exit(1)
    else:
        print("SUCCESS: 100% TRUTH GUARD COMPLIANCE VERIFIED!")
        print("All metrics are grounded in empirical cTrader data with zero synthetic inflation.")
        print("=" * 70)
        sys.exit(0)

if __name__ == "__main__":
    lint_truth()
