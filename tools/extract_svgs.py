import json
import re
from pathlib import Path

ROOT = Path("/home/antigravity")
DOCS = ROOT / "docs"
INDEX_PATH = DOCS / "index.html"

# Load existing DATA for inline injection
bt_data = json.loads((DOCS / "data" / "backtest_data.json").read_text(encoding="utf-8"))
compact_bt = json.dumps(bt_data, ensure_ascii=False, separators=(",", ":"))

# Extract SVGs from test_svg_definitions
import sys
sys.path.insert(0, str(ROOT / "tools"))
from test_svg_definitions import get_svg_step1, get_svg_step2, get_svg_step3, get_svg_step4

svg1 = get_svg_step1()
svg2 = get_svg_step2()
svg3 = get_svg_step3()
svg4 = get_svg_step4()

# Read the existing blueprints from index.html if present
existing_html = INDEX_PATH.read_text(encoding="utf-8")

def extract_between(text, start_tag, end_tag):
    m = re.search(re.escape(start_tag) + r"(.*?)" + re.escape(end_tag), text, re.DOTALL)
    return m.group(1) if m else ""

svg_funnel = extract_between(existing_html, '<div id="svg-foundry-funnel">', '</div>\n      </div>')
if not svg_funnel:
    svg_funnel = '<svg viewBox="0 0 760 120" class="w-full h-auto" xmlns="http://www.w3.org/2000/svg"><rect width="760" height="120" fill="#0f1523" rx="12"/><text x="380" y="65" fill="#38bdf8" font-family="monospace" font-size="14" text-anchor="middle" font-weight="bold">QUANT STRATEGY FOUNDRY & MATHEMATICAL VALIDATION SUITE</text></svg>'

svg_p1 = extract_between(existing_html, '<div id="svg-pillar1-blueprint">', '</div>\n            <p class="text-[11px]')
if not svg_p1:
    svg_p1 = '<svg viewBox="0 0 320 80" class="w-full h-auto" xmlns="http://www.w3.org/2000/svg"><rect width="320" height="80" fill="#0f1523" rx="8"/><text x="160" y="45" fill="#38bdf8" font-family="monospace" font-size="11" text-anchor="middle">PILLAR 1: STRUCTURAL ANCHOR</text></svg>'

svg_p2 = extract_between(existing_html, '<div id="svg-pillar2-blueprint">', '</div>\n            <p class="text-[11px]')
if not svg_p2:
    svg_p2 = '<svg viewBox="0 0 320 80" class="w-full h-auto" xmlns="http://www.w3.org/2000/svg"><rect width="320" height="80" fill="#0f1523" rx="8"/><text x="160" y="45" fill="#a855f7" font-family="monospace" font-size="11" text-anchor="middle">PILLAR 2: CHOCH CONFIRMATION</text></svg>'

svg_p3 = extract_between(existing_html, '<div id="svg-pillar3-blueprint">', '</div>\n            <p class="text-[11px]')
if not svg_p3:
    svg_p3 = '<svg viewBox="0 0 320 80" class="w-full h-auto" xmlns="http://www.w3.org/2000/svg"><rect width="320" height="80" fill="#0f1523" rx="8"/><text x="160" y="45" fill="#f43f5e" font-family="monospace" font-size="11" text-anchor="middle">PILLAR 3: NEWS VOID GATE</text></svg>'

svg_p4 = extract_between(existing_html, '<div id="svg-pillar4-blueprint">', '</div>\n            <p class="text-[11px]')
if not svg_p4:
    svg_p4 = '<svg viewBox="0 0 320 80" class="w-full h-auto" xmlns="http://www.w3.org/2000/svg"><rect width="320" height="80" fill="#0f1523" rx="8"/><text x="160" y="45" fill="#10b981" font-family="monospace" font-size="11" text-anchor="middle">PILLAR 4: STRUCTURAL EXIT & KELLY</text></svg>'

print("Extracted SVGs successfully.")
