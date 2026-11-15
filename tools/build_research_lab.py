"""
Build Page 3 / 8: docs/research-lab.html (+ docs/assets/research-lab.css, docs/assets/research-lab.js, docs/data/research_lab_summary.json)
Fits natively into the official Shared 8-Page Shell (docs/assets/shell.css & docs/assets/shell.js).
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = ROOT / "tools"
LAB_DIR = TOOLS_DIR / "research_lab"
DOCS_DIR = ROOT / "docs"
ASSETS_DIR = DOCS_DIR / "assets"
DATA_OUT_DIR = DOCS_DIR / "data"

OUT_HTML = DOCS_DIR / "research-lab.html"
OUT_CSS = ASSETS_DIR / "research-lab.css"
OUT_JS = ASSETS_DIR / "research-lab.js"
OUT_JSON = DATA_OUT_DIR / "research_lab_summary.json"

sys.path.insert(0, str(TOOLS_DIR))
from research_lab.data_prep import (
    prepare_papers_payload,
    prepare_engines_payload,
    prepare_candlestick_payload,
    prepare_foundry_payload,
)


def safe_json(obj: dict) -> str:
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")


def build_research_lab() -> None:
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    DATA_OUT_DIR.mkdir(parents=True, exist_ok=True)

    css_code = (LAB_DIR / "styles.css").read_text(encoding="utf-8")
    js_core = (LAB_DIR / "app_core.js").read_text(encoding="utf-8")
    js_papers = (LAB_DIR / "tab_papers.js").read_text(encoding="utf-8")
    js_engines = (LAB_DIR / "tab_engines.js").read_text(encoding="utf-8")
    js_candle = (LAB_DIR / "tab_candlestick.js").read_text(encoding="utf-8")
    js_foundry = (LAB_DIR / "tab_foundry.js").read_text(encoding="utf-8")

    payload = {
        "papers": prepare_papers_payload(),
        "engines": prepare_engines_payload(),
        "candlestick": prepare_candlestick_payload(),
        "foundry": prepare_foundry_payload(),
    }

    # 1. Write standalone CSS & JSON assets matching 8-page architecture
    OUT_CSS.write_text(css_code, encoding="utf-8")
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    # 2. Write ES module docs/assets/research-lab.js that mounts official shell.js + Page 3 workspace
    bundle_js = f'''// ANTIGRAVITY QUANT · Page 3 / 8: Research Lab ES Module
import {{ mountShell, loadShellTelemetryOnly }} from './shell.js';

{js_core}

{js_papers}

{js_engines}

{js_candle}

{js_foundry}

async function ensureLabData() {{
  if (window.LAB_DATA && window.LAB_DATA.papers) return window.LAB_DATA;
  try {{
    const res = await fetch(`data/research_lab_summary.json?t=${{Date.now()}}`, {{ cache: 'no-store' }});
    if (res.ok) {{
      window.LAB_DATA = await res.json();
      return window.LAB_DATA;
    }}
  }} catch (_) {{}}
  return window.LAB_DATA || {{}};
}}

async function initPage() {{
  mountShell({{ activePage: 'research-lab.html', onRetry: loadShellTelemetryOnly }});
  await Promise.all([loadShellTelemetryOnly(), ensureLabData()]);
  if (typeof window.initResearchLabApp === 'function') {{
    window.initResearchLabApp();
  }}
}}

if (document.readyState === 'loading') {{
  document.addEventListener('DOMContentLoaded', initPage);
}} else {{
  initPage();
}}
'''
    OUT_JS.write_text(bundle_js, encoding="utf-8")

    # 3. Write docs/research-lab.html cleanly using the official Shared 8-Page Shell markup
    payload_js = safe_json(payload)
    html = f'''<!DOCTYPE html>
<html lang="th" data-theme="dark">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>🧠 Research Lab (ห้องวิจัยสมมติฐานและพัฒนากลยุทธ์) — AI Quant Backtest Lab (Page 3/8)</title>
  <meta name="description" content="ห้องวิจัยสมมติฐานและพัฒนากลยุทธ์: Virtual List 193 Papers พร้อม Slide-over Drawer, 13 Quant Engines 6-Axis Radar, Pro Candlestick Split-View & Instant Dictionary และ Strategy Foundry STR-001..010" />
  <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'><rect width='24' height='24' rx='6' fill='%230d1424'/><path d='M4 17l5-5 4 3 7-8' stroke='%23a855f7' stroke-width='2.5' fill='none' stroke-linecap='round' stroke-linejoin='round'/></svg>" />
  <script>
    (function () {{
      try {{
        var t = localStorage.getItem('cbot_quant_theme_v1');
        if (t === 'light' || t === 'dark') document.documentElement.setAttribute('data-theme', t);
      }} catch (e) {{}}
    }})();
  </script>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700;800&family=Noto+Sans+Thai:wght@400;600;700;800&family=Plus+Jakarta+Sans:wght@400;600;700;800&display=swap" rel="stylesheet" />
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css" />
  <script src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.js"></script>
  <link rel="stylesheet" href="assets/shell.css" />
  <link rel="stylesheet" href="assets/research-lab.css" />
</head>
<body data-page="research-lab.html">
  <div id="app-shell"></div>

  <div id="page-main-template" hidden>
    <div class="rl-wrap">

      <!-- Page Header Strip matching Page 2 & Page 6 -->
      <div class="rl-header-row">
        <div class="rl-title-group">
          <span class="rl-page-badge mono">PAGE 3 / 8</span>
          <h1 class="rl-h1">🧠 Research Lab — ห้องวิจัยสมมติฐานและพัฒนากลยุทธ์</h1>
        </div>
        <div class="rl-header-meta">
          <span class="rl-pill-chip mono">193 Papers · 14 Quant Engines · STR-001..010</span>
          <a href="old-web/research.html" class="rl-pill-chip mono" title="ดูหน้า Research เวอร์ชันเดิม">Legacy Archive ↗</a>
        </div>
      </div>

      <!-- Sticky Search & Filter Control Header -->
      <div class="rl-sticky-controls">
        <div class="space-y-2.5">
          <div class="grid grid-cols-1 xl:grid-cols-[1fr_210px_190px_190px] gap-2.5 items-center">
            <div class="relative flex items-center">
              <span class="absolute left-3 text-slate-400 text-sm">🔍</span>
              <input id="global-search" type="text" oninput="window.onGlobalFilterChange()" class="lab-input w-full pl-9 pr-20 py-2 rounded-xl text-xs sm:text-sm" placeholder="Search 193 papers by title, author, ID, mechanism, or tag...">
              <div class="absolute right-2 flex items-center gap-1.5">
                <button type="button" onclick="window.clearGlobalSearch()" class="px-1.5 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-[10px] text-slate-300 font-semibold" title="Reset search &amp; filters">Reset</button>
                <span class="hidden sm:inline px-1.5 py-0.5 rounded bg-slate-800 border border-slate-700 mono text-[10px] text-slate-400">⌘K</span>
              </div>
            </div>

            <select id="filter-select-1" onchange="window.onGlobalFilterChange()" class="lab-input py-2 px-3 rounded-xl text-xs font-medium cursor-pointer"></select>
            <select id="filter-select-2" onchange="window.onGlobalFilterChange()" class="lab-input py-2 px-3 rounded-xl text-xs font-medium cursor-pointer"></select>
            <select id="filter-select-3" onchange="window.onGlobalFilterChange()" class="lab-input py-2 px-3 rounded-xl text-xs font-medium cursor-pointer"></select>
          </div>

          <!-- 4-Tab Workspace Strip -->
          <div class="flex items-center justify-between gap-2 overflow-x-auto border-t pt-1">
            <div class="flex items-center gap-1">
              <button type="button" data-tab="papers" onclick="window.switchTab('papers')" class="workspace-tab active">
                <span>📄</span> <span>193 Papers Database</span>
              </button>
              <button type="button" data-tab="engines" onclick="window.switchTab('engines')" class="workspace-tab">
                <span>⚗️</span> <span>13 Quant Engines</span>
              </button>
              <button type="button" data-tab="candlestick" onclick="window.switchTab('candlestick')" class="workspace-tab">
                <span>🕯️</span> <span>Pro Candlestick &amp; Dictionary</span>
              </button>
              <button type="button" data-tab="foundry" onclick="window.switchTab('foundry')" class="workspace-tab">
                <span>🏆</span> <span>Strategy Foundry (STR-001..010)</span>
              </button>
            </div>
            <div class="hidden 2xl:flex items-center gap-2 text-[11px] font-mono text-slate-400 pr-1">
              <span>Truth-Guard · Virtualized Viewport · Live Micro-Forward</span>
            </div>
          </div>
        </div>
      </div>

      <!-- TAB 1: 193 PAPERS DATABASE (VIRTUAL LIST + SLIDE-OVER DRAWER) -->
      <section id="pane-papers" class="tab-pane">
        <div id="papers-layout" class="papers-layout drawer-open">
          <div class="lab-panel overflow-hidden flex flex-col">
            <div class="paper-header-grid bg-slate-900/90 border-b text-[11px] font-bold text-slate-400 uppercase tracking-wider">
              <button type="button" onclick="window.sortPapersBy('idx')" class="text-left hover:text-white"># <span id="sort-ind-idx"></span></button>
              <div>Paper ID</div>
              <button type="button" onclick="window.sortPapersBy('title')" class="text-left hover:text-white">Title &amp; Category <span id="sort-ind-title"></span></button>
              <div class="paper-col-tags">Alpha Factor Tags</div>
              <button type="button" onclick="window.sortPapersBy('score')" class="text-right pr-2 text-cyan-300 hover:text-cyan-200" title="Rubric Alignment Index">Alignment <span id="sort-ind-score">▼</span></button>
              <button type="button" onclick="window.sortPapersBy('year')" class="paper-col-year text-center hover:text-white">Year <span id="sort-ind-year"></span></button>
              <div class="text-center">Inspect</div>
            </div>

            <div id="papers-viewport" tabindex="0">
              <div id="papers-spacer" style="height: 11580px; position: relative;">
                <div id="papers-slice-layer"></div>
              </div>
              <div id="papers-empty" class="hidden p-10 text-center text-xs text-slate-400">
                No papers matched your search / filters. Click <strong>Reset</strong> above to view all 193 studies.
              </div>
            </div>

            <div class="px-4 py-2.5 bg-slate-900/80 border-t flex flex-wrap items-center justify-between gap-2 text-xs font-mono text-slate-400">
              <span id="papers-count-readout">Showing 193 of 193 papers</span>
              <div class="flex items-center gap-3">
                <span id="papers-src-readout" class="text-cyan-300">arXiv: 141 · SSRN: 52</span>
                <span id="papers-dom-readout" class="text-emerald-300">DOM Rows: 16 / 193</span>
              </div>
            </div>
          </div>

          <div id="drawer-backdrop" onclick="window.closePaperDrawer()" class="hidden lg:hidden fixed inset-0 bg-black/60 z-50"></div>
          <aside id="paper-drawer" class="lab-panel p-4 drawer-panel is-open">
            <div id="paper-drawer-content"></div>
          </aside>
        </div>
      </section>

      <!-- TAB 2: 13 QUANT ENGINES RADAR COMPARISON -->
      <section id="pane-engines" class="tab-pane hidden space-y-4">
        <div class="lab-panel p-4 space-y-3">
          <div class="flex flex-wrap items-center justify-between gap-2">
            <div>
              <h2 class="text-sm font-extrabold text-white">⚗️ 13 Quant Engines (+ Unified Master Pipeline) · 6-Axis Radar Comparison</h2>
              <p class="text-xs text-slate-400">Compare mathematical model strength across Alpha Edge, Win Consistency, DD Control, Overfit Resistance, Cost Resilience &amp; Latency.</p>
            </div>
            <div class="flex flex-wrap items-center gap-1.5 text-xs">
              <button type="button" onclick="window.applyRadarPreset('TOP3')" class="px-2.5 py-1 rounded-lg bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 font-bold">Top 3 Champions</button>
              <button type="button" onclick="window.applyRadarPreset('TOP5')" class="px-2.5 py-1 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-300 border border-slate-700 font-semibold">Top 5 Opt</button>
              <button type="button" onclick="window.applyRadarPreset('EXEC')" class="px-2.5 py-1 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-300 border border-slate-700 font-semibold">Execution</button>
              <button type="button" onclick="window.applyRadarPreset('RISK')" class="px-2.5 py-1 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-300 border border-slate-700 font-semibold">Risk &amp; Regime</button>
            </div>
          </div>

          <div id="engine-overlay-chips" class="flex flex-wrap gap-1.5"></div>
        </div>

        <div class="grid grid-cols-1 xl:grid-cols-12 gap-4">
          <div class="xl:col-span-6 lab-panel p-4 flex flex-col justify-between gap-3">
            <div id="engines-radar-svg" class="flex items-center justify-center min-h-[370px]"></div>
            <div id="radar-legend-list" class="grid grid-cols-1 gap-1.5"></div>
          </div>

          <div class="xl:col-span-6 lab-panel p-4">
            <div id="engine-inspector-panel"></div>
          </div>
        </div>

        <div class="p-3 rounded-xl bg-amber-950/25 border border-amber-500/35 text-xs text-amber-200 flex items-center gap-2">
          <span>⚠️</span>
          <span id="engines-weekend-note"></span>
        </div>

        <div class="lab-panel overflow-hidden">
          <div class="px-4 py-2.5 bg-slate-900/90 border-b flex items-center justify-between">
            <span class="text-xs font-extrabold text-white">Full 14-Engine Empirical Scorecard (Click row to inspect · Checkbox to overlay on Radar)</span>
          </div>
          <div class="overflow-x-auto">
            <table class="w-full text-left border-collapse">
              <thead class="bg-slate-900/70 text-[11px] font-mono text-slate-400 border-b">
                <tr>
                  <th class="px-3 py-2 text-center">Radar</th>
                  <th class="px-3 py-2">Engine</th>
                  <th class="px-3 py-2 hidden md:table-cell">Mathematical Pillar</th>
                  <th class="px-3 py-2 text-right">Net PnL</th>
                  <th class="px-3 py-2 text-right">PF</th>
                  <th class="px-3 py-2 text-right">Win Rate</th>
                  <th class="px-3 py-2 text-right">Max DD</th>
                  <th class="px-3 py-2 text-right">Trades</th>
                </tr>
              </thead>
              <tbody id="engines-table-body"></tbody>
            </table>
          </div>
        </div>
      </section>

      <!-- TAB 3: PRO CANDLESTICK & TECHNICAL DICTIONARY -->
      <section id="pane-candlestick" class="tab-pane hidden space-y-4">
        <div class="lab-panel p-4 space-y-3">
          <div class="flex flex-wrap items-center justify-between gap-2">
            <div class="flex flex-wrap items-center gap-1.5 text-xs">
              <span class="font-bold text-slate-300 mr-1">Market / HA Study:</span>
              <button type="button" data-ds="XAUUSD" onclick="window.switchCandlestickDataset('XAUUSD')" class="cs-ds-btn px-2.5 py-1 rounded-lg bg-cyan-500/20 text-cyan-300 border border-cyan-500/50 font-mono font-bold">🥇 XAUUSD M1</button>
              <button type="button" data-ds="BTCUSD" onclick="window.switchCandlestickDataset('BTCUSD')" class="cs-ds-btn px-2.5 py-1 rounded-lg bg-slate-900 text-slate-300 border border-slate-700 font-mono font-bold">₿ BTCUSD M1</button>
              <button type="button" data-ds="ETHUSD" onclick="window.switchCandlestickDataset('ETHUSD')" class="cs-ds-btn px-2.5 py-1 rounded-lg bg-slate-900 text-slate-300 border border-slate-700 font-mono font-bold">⟠ ETHUSD M1</button>
              <button type="button" data-ds="HA_0" onclick="window.switchCandlestickDataset('HA_0')" class="cs-ds-btn px-2.5 py-1 rounded-lg bg-slate-900 text-emerald-300 border border-slate-700 font-mono font-semibold">HA Study #1 (Up ✓)</button>
              <button type="button" data-ds="HA_1" onclick="window.switchCandlestickDataset('HA_1')" class="cs-ds-btn px-2.5 py-1 rounded-lg bg-slate-900 text-rose-300 border border-slate-700 font-mono font-semibold">HA Study #2 (Down ✓)</button>
              <button type="button" data-ds="HA_2" onclick="window.switchCandlestickDataset('HA_2')" class="cs-ds-btn px-2.5 py-1 rounded-lg bg-slate-900 text-amber-300 border border-slate-700 font-mono font-semibold">HA Study #3 (Reversal ✗)</button>
            </div>
            <div class="flex items-center gap-1.5 text-xs font-mono">
              <button type="button" onclick="window.zoomCandlestick(1)" class="px-2.5 py-1 rounded bg-slate-900 border border-slate-700 hover:border-cyan-400">+ Zoom In</button>
              <button type="button" onclick="window.zoomCandlestick(-1)" class="px-2.5 py-1 rounded bg-slate-900 border border-slate-700 hover:border-cyan-400">- Zoom Out</button>
              <button type="button" onclick="window.zoomCandlestick(0)" class="px-2.5 py-1 rounded bg-slate-900 border border-slate-700 hover:border-cyan-400">Reset</button>
            </div>
          </div>

          <div id="ha-example-callout" class="hidden p-2.5 rounded-xl bg-slate-900/90 border border-cyan-500/35"></div>
          <div id="split-telemetry-strip" class="p-2.5 rounded-xl bg-slate-900/80 border"></div>

          <div class="grid grid-cols-1 lg:grid-cols-2 gap-3">
            <div class="space-y-1.5">
              <div class="flex items-center justify-between text-xs px-1">
                <span class="font-extrabold text-white">🕯️ Standard Candlestick (Raw OHLC + VWAP)</span>
                <span class="mono text-[10px] text-slate-400">Drag to pan · Wheel to zoom · Synced Crosshair</span>
              </div>
              <div class="split-canvas-wrap">
                <canvas id="canvas-ohlc"></canvas>
              </div>
            </div>

            <div class="space-y-1.5">
              <div class="flex items-center justify-between text-xs px-1">
                <span class="font-extrabold text-cyan-300">🌊 Heikin-Ashi Smoothed + VWAP ±1σ / ±2σ SD Bands</span>
                <span class="mono text-[10px] text-purple-300">Purple Shaded = ±2σ Equilibrium Channel</span>
              </div>
              <div class="split-canvas-wrap">
                <canvas id="canvas-ha"></canvas>
              </div>
            </div>
          </div>

          <div class="p-2.5 rounded-xl bg-slate-950/70 border flex flex-wrap items-center justify-between gap-2">
            <span class="text-xs font-bold text-slate-300">📐 Heikin-Ashi &amp; VWAP Band Equations:</span>
            <div id="ha-math-formula" class="text-xs overflow-x-auto"></div>
          </div>
        </div>

        <div class="lab-panel p-4 space-y-3">
          <div class="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h3 class="text-sm font-extrabold text-white">📚 Technical &amp; Microstructure Instant Dictionary</h3>
              <p class="text-xs text-slate-400">Type in top search bar or below to filter 32 candlestick, VWAP, DOM order flow, and statistical validation concepts instantly.</p>
            </div>
            <div class="flex items-center gap-2">
              <input id="dict-local-search" type="text" oninput="window.onLocalDictSearch()" placeholder="Filter dictionary term..." class="lab-input px-3 py-1.5 rounded-lg text-xs w-48 sm:w-64">
              <span id="dict-count" class="mono text-xs text-cyan-300 font-bold">32 / 32 terms</span>
            </div>
          </div>

          <div class="flex flex-wrap items-center gap-1.5 text-xs">
            <button type="button" data-cat="ALL" onclick="window.filterDictionaryQuick('ALL')" class="dict-cat-btn px-2.5 py-1 rounded-lg bg-cyan-500/20 text-cyan-300 border border-cyan-500/50 font-bold">All (32)</button>
            <button type="button" data-cat="Candlestick & HA" onclick="window.filterDictionaryQuick('Candlestick & HA')" class="dict-cat-btn px-2.5 py-1 rounded-lg bg-slate-900 text-slate-300 border border-slate-700 font-semibold">Candlestick &amp; HA</button>
            <button type="button" data-cat="VWAP & Execution" onclick="window.filterDictionaryQuick('VWAP & Execution')" class="dict-cat-btn px-2.5 py-1 rounded-lg bg-slate-900 text-slate-300 border border-slate-700 font-semibold">VWAP &amp; Execution</button>
            <button type="button" data-cat="DOM & Microstructure" onclick="window.filterDictionaryQuick('DOM & Microstructure')" class="dict-cat-btn px-2.5 py-1 rounded-lg bg-slate-900 text-slate-300 border border-slate-700 font-semibold">DOM &amp; Microstructure</button>
            <button type="button" data-cat="Quant Validation" onclick="window.filterDictionaryQuick('Quant Validation')" class="dict-cat-btn px-2.5 py-1 rounded-lg bg-slate-900 text-slate-300 border border-slate-700 font-semibold">Quant Validation</button>
          </div>

          <div id="dict-grid" class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3"></div>
        </div>
      </section>

      <!-- TAB 4: STRATEGY FOUNDRY (STR-001 TO STR-009 STATUS BOARD) -->
      <section id="pane-foundry" class="tab-pane hidden space-y-4">
        <div id="foundry-funnel-banner"></div>

        <div class="flex flex-wrap items-center justify-between gap-2">
          <div class="flex flex-wrap items-center gap-1.5 text-xs">
            <button type="button" data-st="ALL" onclick="window.filterFoundryQuick('ALL')" class="foundry-status-btn px-3 py-1.5 rounded-lg bg-cyan-500/20 text-cyan-300 border border-cyan-500/50 font-bold">All Strategies (<span class="cnt">9</span>)</button>
            <button type="button" data-st="PASSED" onclick="window.filterFoundryQuick('PASSED')" class="foundry-status-btn px-3 py-1.5 rounded-lg bg-slate-900 text-emerald-300 border border-slate-700 font-bold">✓ PASSED (<span class="cnt">3</span>)</button>
            <button type="button" data-st="INCUBATING" onclick="window.filterFoundryQuick('INCUBATING')" class="foundry-status-btn px-3 py-1.5 rounded-lg bg-slate-900 text-amber-300 border border-slate-700 font-bold">🧪 INCUBATING (<span class="cnt">5</span>)</button>
            <button type="button" data-st="REJECTED" onclick="window.filterFoundryQuick('REJECTED')" class="foundry-status-btn px-3 py-1.5 rounded-lg bg-slate-900 text-rose-300 border border-slate-700 font-bold">✕ REJECTED (<span class="cnt">1</span>)</button>
          </div>
          <span class="mono text-[11px] text-slate-400">Pepperstone Demo #5258778 · Empirical Truth-Guard Synchronized</span>
        </div>

        <div id="foundry-cards-grid" class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3.5"></div>

        <div class="grid grid-cols-1 xl:grid-cols-2 gap-4">
          <div id="foundry-bots-panel" class="lab-panel p-4"></div>
          <div id="foundry-graveyard-panel" class="lab-panel p-4"></div>
        </div>
      </section>

    </div>
  </div>

  <!-- Embedded Offline / Fast Boot Fallback Payload -->
  <script>
    window.LAB_DATA = {payload_js};
  </script>
  <script type="module" src="assets/research-lab.js"></script>
</body>
</html>
'''

    OUT_HTML.write_text(html, encoding="utf-8")
    print(f"Built {OUT_HTML} ({len(html):,} bytes), {OUT_CSS}, {OUT_JS}, {OUT_JSON}")


if __name__ == "__main__":
    build_research_lab()
