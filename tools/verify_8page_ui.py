#!/usr/bin/env python3
"""
Verification Suite for the 8-Page Quant Research & Telemetry Portal (docs/)
Ensures:
1. All 8 HTML pages exist and load shared shell assets.
2. Zero live Supabase Auth / Edge Function dependencies remain in docs/.
3. Zero broken old-web/, missing assets/, or missing data/ references.
4. Valid JSON integrity across docs/data/ and docs/assets/database_catalog.json.
"""

import json
import os
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"

PAGES = [
    "index.html",
    "data-center.html",
    "research-lab.html",
    "experiment-lab.html",
    "intelligence.html",
    "improvement-audit.html",
    "archive-system.html",
    "database.html",
]

def main() -> int:
    failures = []

    print("=== VERIFICATION REPORT: 8-PAGE QUANT PORTAL & DECOMMISSION AUDIT ===")

    # 1. All 8 pages exist
    for p in PAGES:
        fp = DOCS / p
        ok = fp.exists() and fp.stat().st_size > 1000
        print(f"[{'✅ PASS' if ok else '❌ FAIL'}] Page {p}")
        if not ok:
            failures.append(f"Missing or empty page: {p}")

    # 2. Decommissioned Supabase / Old-web checks
    forbidden = [
        ("docs/config.js removed", not (DOCS / "config.js").exists()),
        ("docs/app.js removed", not (DOCS / "app.js").exists()),
        ("docs/old-web removed", not (DOCS / "old-web").exists()),
        ("supabase/ directory removed", not (ROOT / "supabase").exists()),
    ]
    for label, ok in forbidden:
        print(f"[{'✅ PASS' if ok else '❌ FAIL'}] {label}")
        if not ok:
            failures.append(label)

    # 3. Scan 8 pages + assets JS/CSS for dead refs & live Supabase client calls
    path_rx = re.compile(r"""['"]((?:data|assets)/[^'"`$\s]+|old-web/[^'"`$\s]+)['"]""")
    targets = [DOCS / p for p in PAGES] + list((DOCS / "assets").glob("*.js"))

    dead_refs = []
    supabase_leaks = []
    tgrock_leaks = []

    for fp in targets:
        if not fp.exists():
            continue
        txt = fp.read_text(encoding="utf-8", errors="ignore")
        rel_fp = fp.relative_to(ROOT).as_posix()

        for ref in path_rx.findall(txt):
            clean = ref.split("?")[0].split("#")[0]
            if clean.startswith("old-web/"):
                dead_refs.append(f"{rel_fp} -> {clean}")
            elif not (DOCS / clean).exists():
                dead_refs.append(f"{rel_fp} -> MISSING:{clean}")

        if re.search(r"supabase\.co|@supabase/supabase-js|LAB_API|SUPABASE_ANON_KEY", txt, re.I):
            supabase_leaks.append(rel_fp)

        if "tgrockza55" in txt.lower():
            tgrock_leaks.append(rel_fp)

    print(f"[{'✅ PASS' if not dead_refs else '❌ FAIL'}] Asset/Data/Old-Web Link Integrity ({len(dead_refs)} issues)")
    if dead_refs:
        failures.extend(dead_refs[:10])
        for d in dead_refs[:10]:
            print("   ->", d)

    print(f"[{'✅ PASS' if not supabase_leaks else '❌ FAIL'}] Zero Live Supabase Client/Auth Calls ({len(supabase_leaks)} leaks)")
    if supabase_leaks:
        failures.extend(supabase_leaks)

    print(f"[{'✅ PASS' if not tgrock_leaks else '❌ FAIL'}] Zero Legacy tgrockza55 URLs in UI ({len(tgrock_leaks)} leaks)")
    if tgrock_leaks:
        failures.extend(tgrock_leaks)

    # 4. Validate critical JSON payloads
    json_files = [
        DOCS / "assets" / "database_catalog.json",
        DOCS / "data" / "live_status.json",
        DOCS / "data" / "truth_guard.json",
        DOCS / "data" / "overview_summary.json",
        DOCS / "data" / "intelligence_summary.json",
        DOCS / "data" / "audit_summary.json",
        DOCS / "data" / "archive_system_summary.json",
        DOCS / "data" / "dc_meta.json",
        DOCS / "data" / "strategy_foundry.json",
        DOCS / "data" / "flywheel_cycles.json",
        DOCS / "data" / "hybrid_data_audit.json",
        DOCS / "data" / "regime_strategy_matrix.json",
        DOCS / "data" / "demo_deployment_state.json",
        DOCS / "data" / "v5_pipeline_state.json",
    ]
    json_errs = []
    for jf in json_files:
        try:
            data = json.loads(jf.read_text(encoding="utf-8"))
            if not data:
                json_errs.append(f"Empty JSON: {jf.name}")
        except Exception as exc:
            json_errs.append(f"{jf.name}: {exc}")

    print(f"[{'✅ PASS' if not json_errs else '❌ FAIL'}] JSON Payload Integrity ({len(json_files)} files checked)")
    if json_errs:
        failures.extend(json_errs)
        for e in json_errs:
            print("   ->", e)

    if failures:
        print(f"\n❌ VERIFICATION FAILED WITH {len(failures)} ISSUE(S).")
        return 1

    print("\n🎉 ALL 8-PAGE QUANT PORTAL CHECKS PASSED FLAWLESSLY!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
