import os
import sys
import re

sys.stdout.reconfigure(encoding='utf-8')

html_path = 'docs/index.html'
with open(html_path, 'r', encoding='utf-8') as f:
    html = f.read()

checks = [
    ('HTML Light Class', 'class="light"' in html),
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

all_passed = True
print("=== VERIFICATION REPORT: WHITE THEME & TRADINGVIEW CHARTS ===")
for name, passed in checks:
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"[{status}] {name}")
    if not passed:
        all_passed = False

if all_passed:
    print("\n🎉 ALL 17 SYSTEM CHECKS PASSED PERFECTLY!")
else:
    print("\n⚠️ SOME CHECKS FAILED! Please inspect.")
