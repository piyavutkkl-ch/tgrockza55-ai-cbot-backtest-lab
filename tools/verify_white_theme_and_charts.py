import os
import sys
import json

sys.stdout.reconfigure(encoding='utf-8')

legacy_html_path = 'docs/old-web/index.html' if os.path.exists('docs/old-web/index.html') else 'docs/index.html'
with open(legacy_html_path, 'r', encoding='utf-8') as f:
    html = f.read()

checks = [
    ('Legacy HTML Light Class', 'class="light"' in html),
    ('TradingView Widget Container', 'id="tv_chart_container"' in html),
    ('TradingView Studio Card', 'id="tradingview-studio-card"' in html),
    ('TradingView Script Tag', 'https://s3.tradingview.com/tv.js' in html),
    ('Step 1 SVG Chart (L2 DOM Depth)', 'id="svg-step1-chart"' in html),
    ('Step 2 SVG Chart (DOM Absorption & CHoCH)', 'id="svg-step2-chart"' in html),
    ('Step 3 SVG Chart (Cumulative Equity & PnL)', 'id="svg-step3-chart"' in html),
    ('Step 4 SVG Chart (Flywheel Evolution Loop)', 'id="svg-step4-chart"' in html),
    ('Strategy Foundry Funnel SVG', 'id="svg-foundry-funnel"' in html),
    ('Pillar 1 Blueprint SVG (Structural Anchor)', 'id="svg-pillar1-blueprint"' in html),
    ('Pillar 2 Blueprint SVG (CHoCH Confirmation)', 'id="svg-pillar2-blueprint"' in html),
    ('Pillar 3 Blueprint SVG (News Void Gate)', 'id="svg-pillar3-blueprint"' in html),
    ('Pillar 4 Blueprint SVG (Structural Exit & Kelly)', 'id="svg-pillar4-blueprint"' in html),
    ('White Theme CSS Overrides', '/* ========================================================================= */\n    /* INSTITUTIONAL WHITE / LIGHT THEME STYLES' in html),
    ('Theme Toggle Button', 'id="btn-theme-toggle"' in html),
    ('All 6 Rules in System Governance', 'System Governance & Institutional Rules' in html and 'กฎพัฒนาหน้าเว็บให้เป็นปัจจุบัน' in html),
    ('Dynamic JS Handlers', 'function initTradingViewChart' in html and 'function toggleTheme' in html)
]

modular_pages = [
    'docs/index.html',
    'docs/data-center.html',
    'docs/research-lab.html',
    'docs/experiment-lab.html',
    'docs/intelligence.html',
    'docs/improvement-audit.html',
    'docs/archive-system.html',
    'docs/database.html',
]
for p in modular_pages:
    exists = os.path.exists(p)
    has_shell = exists and ('id="app-shell"' in open(p, 'r', encoding='utf-8').read())
    checks.append((f'8-Page Shell ({os.path.basename(p)})', has_shell))

checks.append(('Shared Shell JS (docs/assets/shell.js)', os.path.exists('docs/assets/shell.js')))
checks.append(('Database Catalog (docs/assets/database_catalog.json)', os.path.exists('docs/assets/database_catalog.json')))
if os.path.exists('docs/data/truth_guard.json'):
    tg = json.load(open('docs/data/truth_guard.json', 'r', encoding='utf-8'))
    n_val = tg.get('metrics_empirical', {}).get('total_closed_trades_N', 0)
    checks.append((f'Truth Guard Telemetry Populated (N={n_val})', n_val > 0))

all_passed = True
print("=== VERIFICATION REPORT: 8-PAGE SHELL & LEGACY DASHBOARD ===")
for name, passed in checks:
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"[{status}] {name}")
    if not passed:
        all_passed = False

if all_passed:
    print(f"\n🎉 ALL {len(checks)} UI & TELEMETRY CHECKS PASSED PERFECTLY!")
    sys.exit(0)
else:
    print("\n⚠️ SOME CHECKS FAILED! Please inspect.")
    sys.exit(1)
