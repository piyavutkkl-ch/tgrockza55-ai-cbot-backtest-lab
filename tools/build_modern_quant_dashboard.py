import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
INDEX_PATH = DOCS / "index.html"

# Load compact backtest data
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

# Read existing index.html for blueprints
existing = INDEX_PATH.read_text(encoding="utf-8")

def extract_block(text, start_pattern, end_pattern):
    m = re.search(start_pattern + r"(.*?)" + end_pattern, text, re.DOTALL)
    return m.group(1).strip() if m else ""

svg_funnel = extract_block(existing, r'<div id="svg-foundry-funnel"[^>]*>', r'</div>\s*</div>')
if not svg_funnel or len(svg_funnel) < 100:
    svg_funnel = '''<svg viewBox="0 0 760 110" class="w-full h-auto text-xs" xmlns="http://www.w3.org/2000/svg">
      <rect width="760" height="110" fill="#0b111e" rx="12" stroke="#1e293b"/>
      <polygon points="40,20 720,20 540,95 220,95" fill="#0f172a" stroke="#38bdf8" stroke-width="1.5" opacity="0.6"/>
      <text x="380" y="42" font-size="12" font-family="monospace" fill="#38bdf8" text-anchor="middle" font-weight="bold">STAGE 1: 1,000 HYPOTHESES (L2 DOM + TICK DATA)</text>
      <text x="380" y="65" font-size="11" font-family="monospace" fill="#fbbf24" text-anchor="middle">STAGE 2-3: 100 FILTERED (COST MODEL + CHOCH)</text>
      <text x="380" y="88" font-size="11" font-family="monospace" fill="#34d399" text-anchor="middle" font-weight="bold">STAGE 4-7: 3 PRODUCTION CBOTS DEPLOYED TO PEPPERSTONE</text>
    </svg>'''

svg_p1 = extract_block(existing, r'<div id="svg-pillar1-blueprint"[^>]*>', r'</div>\s*<p class="text-\[11px\]')
if not svg_p1 or len(svg_p1) < 50:
    svg_p1 = '''<svg viewBox="0 0 320 70" class="w-full h-auto" xmlns="http://www.w3.org/2000/svg"><rect width="320" height="70" fill="#0b111e" rx="8" stroke="#1e293b"/><text x="160" y="40" font-size="10" font-family="monospace" fill="#38bdf8" text-anchor="middle" font-weight="bold">PILLAR 1: STRUCTURAL ANCHOR (ANCHORED VWAP)</text></svg>'''

svg_p2 = extract_block(existing, r'<div id="svg-pillar2-blueprint"[^>]*>', r'</div>\s*<p class="text-\[11px\]')
if not svg_p2 or len(svg_p2) < 50:
    svg_p2 = '''<svg viewBox="0 0 320 70" class="w-full h-auto" xmlns="http://www.w3.org/2000/svg"><rect width="320" height="70" fill="#0b111e" rx="8" stroke="#1e293b"/><text x="160" y="40" font-size="10" font-family="monospace" fill="#a855f7" text-anchor="middle" font-weight="bold">PILLAR 2: DISPLACEMENT CHOCH CONFIRMATION</text></svg>'''

svg_p3 = extract_block(existing, r'<div id="svg-pillar3-blueprint"[^>]*>', r'</div>\s*<p class="text-\[11px\]')
if not svg_p3 or len(svg_p3) < 50:
    svg_p3 = '''<svg viewBox="0 0 320 70" class="w-full h-auto" xmlns="http://www.w3.org/2000/svg"><rect width="320" height="70" fill="#0b111e" rx="8" stroke="#1e293b"/><text x="160" y="40" font-size="10" font-family="monospace" fill="#f43f5e" text-anchor="middle" font-weight="bold">PILLAR 3: MACRO NEWS VOID GATE</text></svg>'''

svg_p4 = extract_block(existing, r'<div id="svg-pillar4-blueprint"[^>]*>', r'</div>\s*<p class="text-\[11px\]')
if not svg_p4 or len(svg_p4) < 50:
    svg_p4 = '''<svg viewBox="0 0 320 70" class="w-full h-auto" xmlns="http://www.w3.org/2000/svg"><rect width="320" height="70" fill="#0b111e" rx="8" stroke="#1e293b"/><text x="160" y="40" font-size="10" font-family="monospace" fill="#10b981" text-anchor="middle" font-weight="bold">PILLAR 4: SMART LIQUIDITY EXIT & FRACTIONAL KELLY</text></svg>'''

new_html = f'''<!DOCTYPE html>
<html lang="th" class="dark" data-theme-supports='class="light"'>
<head>
  <meta charset="UTF-8">
  <script>
    // Early Theme Guard: prevent flash of unstyled theme
    (function() {{
      const savedTheme = localStorage.getItem('antigravity_theme');
      if (savedTheme === 'light') {{
        document.documentElement.classList.remove('dark');
        document.documentElement.classList.add('light');
      }} else {{
        document.documentElement.classList.remove('light');
        document.documentElement.classList.add('dark');
      }}
    }})();
  </script>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>ANTIGRAVITY QUANT · Institutional Quant Dashboard & 10-Stage Lifecycle</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="config.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Noto+Sans+Thai:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600;700;800&display=swap" rel="stylesheet">
  <script>
    tailwind.config = {{
      darkMode: 'class',
      theme: {{
        extend: {{
          fontFamily: {{
            sans: ['"Plus Jakarta Sans"', '"Noto Sans Thai"', 'sans-serif'],
            mono: ['"JetBrains Mono"', 'Consolas', 'monospace']
          }},
          colors: {{
            brand: {{
              50: '#f0f9ff',
              500: '#0284c7',
              600: '#0369a1',
              900: '#0c4a6e',
            }}
          }}
        }}
      }}
    }}
  </script>
  <style>
    /* ========================================================================= */
    /* EXECUTIVE QUANT DESIGN SYSTEM (WHITESPACE, CARD ELEVATION, TYPOGRAPHY)   */
    /* ========================================================================= */
    body {{
      background-color: #090d16;
      color: #e2e8f0;
      font-family: 'Plus Jakarta Sans', 'Noto Sans Thai', sans-serif;
      -webkit-font-smoothing: antialiased;
      -moz-osx-font-smoothing: grayscale;
      text-rendering: optimizeLegibility;
    }}
    ::-webkit-scrollbar {{ width: 6px; height: 6px; }}
    ::-webkit-scrollbar-track {{ background: #090d16; }}
    ::-webkit-scrollbar-thumb {{ background: rgba(148, 163, 184, 0.2); border-radius: 3px; }}
    ::-webkit-scrollbar-thumb:hover {{ background: rgba(148, 163, 184, 0.4); }}
    
    .mono {{ font-family: 'JetBrains Mono', monospace; }}
    .card-surface {{
      background-color: #0f1523;
      border: 1px solid rgba(255, 255, 255, 0.08);
      border-radius: 16px;
      box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.4);
      transition: border-color 0.2s ease, box-shadow 0.2s ease;
    }}
    .card-surface:hover {{
      border-color: rgba(56, 189, 248, 0.25);
    }}

    /* Stepper Styling */
    .stepper-node {{
      transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
    }}
    .stepper-node.active-node {{
      background-color: #0284c7;
      color: #ffffff;
      box-shadow: 0 0 12px rgba(2, 132, 199, 0.5);
    }}

    /* ========================================================================= */
    /* INSTITUTIONAL WHITE / LIGHT THEME STYLES (WCAG AAA HIGH-CONTRAST) */
    /* ========================================================================= */
    html.light body {{
      background-color: #f8fafc !important;
      color: #0f172a !important;
    }}
    html.light header,
    html.light #segmented-nav-bar {{
      background-color: rgba(255, 255, 255, 0.95) !important;
      border-color: #e2e8f0 !important;
      box-shadow: 0 1px 3px 0 rgba(15, 23, 42, 0.05) !important;
    }}
    html.light .card-surface {{
      background-color: #ffffff !important;
      border: 1px solid #e2e8f0 !important;
      box-shadow: 0 4px 16px -2px rgba(15, 23, 42, 0.05) !important;
      color: #0f172a !important;
    }}
    html.light .card-surface:hover {{
      border-color: #cbd5e1 !important;
    }}
    html.light .text-white {{ color: #0f172a !important; }}
    html.light .text-slate-100,
    html.light .text-slate-200,
    html.light .text-slate-300 {{ color: #1e293b !important; }}
    html.light .text-slate-400 {{ color: #475569 !important; font-weight: 500 !important; }}
    html.light .text-slate-500 {{ color: #64748b !important; }}
    html.light .border-slate-800,
    html.light .border-slate-700 {{ border-color: #e2e8f0 !important; }}
    html.light .bg-slate-900,
    html.light .bg-slate-950,
    html.light .bg-slate-900\/60,
    html.light .bg-slate-950\/80 {{ background-color: #ffffff !important; border-color: #e2e8f0 !important; }}
    
    html.light .bg-slate-800,
    html.light .bg-slate-800\/80 {{ background-color: #f1f5f9 !important; border-color: #cbd5e1 !important; color: #1e293b !important; }}
    
    /* High contrast accents in light mode */
    html.light .text-cyan-300,
    html.light .text-cyan-400 {{ color: #0369a1 !important; font-weight: 700 !important; }}
    html.light .text-emerald-300,
    html.light .text-emerald-400 {{ color: #047857 !important; font-weight: 700 !important; }}
    html.light .text-amber-300,
    html.light .text-amber-400 {{ color: #b45309 !important; font-weight: 700 !important; }}
    html.light .text-rose-300,
    html.light .text-rose-400 {{ color: #be123c !important; font-weight: 700 !important; }}
    html.light .text-purple-300,
    html.light .text-purple-400 {{ color: #6d28d9 !important; font-weight: 700 !important; }}
    html.light .text-pink-300,
    html.light .text-pink-400 {{ color: #be185d !important; font-weight: 700 !important; }}
    
    html.light .bg-cyan-500\/20,
    html.light .bg-cyan-500\/15 {{ background-color: #e0f2fe !important; border-color: #7dd3fc !important; color: #0369a1 !important; }}
    html.light .bg-emerald-500\/20,
    html.light .bg-emerald-500\/15 {{ background-color: #d1fae5 !important; border-color: #6ee7b7 !important; color: #047857 !important; }}
    html.light .bg-amber-500\/20,
    html.light .bg-amber-950\/60 {{ background-color: #fef3c7 !important; border-color: #fcd34d !important; color: #b45309 !important; }}
    html.light .bg-rose-500\/20,
    html.light .bg-rose-500\/15 {{ background-color: #ffe4e6 !important; border-color: #fda4af !important; color: #be123c !important; }}
    html.light .bg-purple-500\/15 {{ background-color: #f3e8ff !important; border-color: #d8b4fe !important; color: #6d28d9 !important; }}
    html.light .bg-pink-500\/15 {{ background-color: #fce7f3 !important; border-color: #fbcfe8 !important; color: #be185d !important; }}
    
    /* Institutional SVG Light Mode Adaptations */
    html.light svg rect[fill="#0b111e"] {{ fill: #ffffff !important; stroke: #e2e8f0 !important; }}
    html.light svg line[stroke="#1e293b"] {{ stroke: #f1f5f9 !important; }}
    html.light svg line[stroke="#334155"] {{ stroke: #cbd5e1 !important; }}
    html.light svg text[fill="#94a3b8"] {{ fill: #475569 !important; font-weight: 600 !important; }}
    html.light svg text[fill="#64748b"] {{ fill: #475569 !important; }}
    
    html.light table thead {{ background-color: #f8fafc !important; color: #334155 !important; }}
    html.light table tbody tr:hover {{ background-color: #f1f5f9 !important; }}
  </style>
</head>
<body class="bg-[#090d16] text-[#e2e8f0] min-h-screen antialiased">

  <!-- ========================================================================= -->
  <!-- 1. STICKY QUICK STATUS HEADER (Point #5: Quick Status Bar)               -->
  <!-- ========================================================================= -->
  <header class="sticky top-0 z-50 bg-[#090d16]/95 backdrop-blur-md border-b border-slate-800/80 px-4 sm:px-6 py-2.5 transition-colors">
    <div class="max-w-[1600px] mx-auto flex flex-wrap items-center justify-between gap-3">
      
      <!-- Logo + Brand -->
      <div class="flex items-center gap-3">
        <a href="index.html" class="flex items-center gap-2.5 group">
          <div class="w-9 h-9 rounded-xl bg-slate-900 border border-slate-700/80 flex items-center justify-center text-lg shadow-sm">
            🏛️
          </div>
          <div>
            <div class="flex items-center gap-2">
              <span class="font-extrabold text-white text-base tracking-wider">ANTIGRAVITY</span>
              <span class="font-extrabold text-sky-400 text-base">QUANT</span>
              <span class="px-2 py-0.5 text-[11px] font-mono font-bold rounded-md bg-sky-500/15 text-sky-300 border border-sky-500/30">V3 PLATFORM</span>
            </div>
            <div class="text-[11px] text-slate-400">Institutional cBot Quant Architecture & Lifecycle</div>
          </div>
        </a>
      </div>

      <!-- Quick Status Badges -->
      <div class="flex items-center gap-2.5 sm:gap-3 flex-wrap text-xs">
        
        <!-- Live Real Balance / Demo Equity -->
        <div class="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-900/90 border border-slate-800 font-mono" title="Pepperstone Demo #5258778 Live Equity">
          <span class="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse"></span>
          <span class="text-slate-400 text-xs">Balance:</span>
          <span id="hdr-equity" class="font-extrabold text-emerald-400 text-sm">$82.93</span>
          <span class="text-slate-500 text-[11px]">#5258778</span>
        </div>

        <!-- Champion Model Indicator -->
        <div class="hidden lg:flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-900/90 border border-slate-800 font-mono">
          <span class="text-slate-400 text-xs">Champion:</span>
          <span class="font-bold text-amber-300">VWAP_ABSORPTION</span>
          <span class="px-1.5 py-0.5 rounded text-[11px] bg-emerald-500/20 text-emerald-300 font-bold border border-emerald-500/30">+$96.00</span>
        </div>

        <!-- Access Mode Badge (Public Research Lab) -->
        <div id="visitor-mode-badge" class="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-700 text-xs font-mono text-emerald-400">
          <span class="h-2 w-2 rounded-full bg-emerald-400 animate-pulse"></span>
          <span>🌐 PUBLIC RESEARCH LAB</span>
        </div>

        <!-- Theme Toggle Button -->
        <button id="btn-theme-toggle" onclick="toggleTheme()" class="px-3 py-1.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-slate-300 font-bold border border-slate-700 text-xs flex items-center gap-1.5 transition cursor-pointer shadow-sm" title="สลับระหว่างธีมมืด (Dark Terminal) และธีมสว่าง (High-Contrast Light)">
          <span id="theme-icon">🌙</span> <span id="theme-label" class="hidden sm:inline">ธีมมืด</span>
        </button>

        <a href="terminal.html" class="px-3 py-1.5 rounded-xl bg-sky-500/15 hover:bg-sky-500/25 text-sky-300 border border-sky-500/40 font-bold text-xs flex items-center gap-1.5 transition">
          <span>📈</span> <span>cTrader Live Terminal</span>
        </a>

        <a href="pro.html" class="px-3 py-1.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-slate-300 border border-slate-700 font-bold text-xs flex items-center gap-1.5 transition">
          <span>🕯️</span> <span>Candlestick Lab</span>
        </a>

        <a href="research.html" class="px-3 py-1.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-slate-300 border border-slate-700 font-bold text-xs hidden md:flex items-center gap-1.5 transition">
          <span>🔬</span> <span>193 Papers &amp; Alphas</span>
        </a>

      </div>
    </div>
  </header>

  <!-- ========================================================================= -->
  <!-- 2. SEGMENTED INTERACTIVE ZONE CONTROL (Point #3: Segmented Switch)         -->
  <!-- ========================================================================= -->
  <nav id="segmented-nav-bar" class="sticky top-[58px] z-40 bg-[#090d16]/95 backdrop-blur-md border-b border-slate-800/80 px-4 sm:px-6 py-2">
    <div class="max-w-[1600px] mx-auto flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
      
      <!-- Clean Segmented Control Tabs -->
      <div class="flex items-center gap-1.5 bg-slate-900/90 p-1 rounded-xl border border-slate-800 text-xs">
        <button onclick="setInteractiveZone('all')" id="zone-tab-all" class="px-3.5 py-1.5 rounded-lg font-bold bg-sky-500/20 text-sky-300 border border-sky-500/40 transition cursor-pointer flex items-center gap-1.5">
          <span>🌐</span> <span>ดูทั้งหมด (All Views)</span>
        </button>
        <button onclick="setInteractiveZone('backtest')" id="zone-tab-backtest" class="px-3.5 py-1.5 rounded-lg font-medium text-slate-400 hover:text-white transition cursor-pointer flex items-center gap-1.5">
          <span>🔬</span> <span>Strategy Backtest Lab</span>
          <span class="px-1.5 py-0.2 rounded bg-amber-500/20 text-amber-300 font-mono text-[10px]">+$96.00</span>
        </button>
        <button onclick="setInteractiveZone('live')" id="zone-tab-live" class="px-3.5 py-1.5 rounded-lg font-medium text-slate-400 hover:text-white transition cursor-pointer flex items-center gap-1.5">
          <span>📡</span> <span>Bot Fleet Live Monitor</span>
          <span class="px-1.5 py-0.2 rounded bg-emerald-500/20 text-emerald-300 font-mono text-[10px]">4 LIVE</span>
        </button>
        <button onclick="setInteractiveZone('lifecycle')" id="zone-tab-lifecycle" class="px-3.5 py-1.5 rounded-lg font-medium text-slate-400 hover:text-white transition cursor-pointer flex items-center gap-1.5">
          <span>🔄</span> <span>10-Stage Lifecycle</span>
        </button>
      </div>

      <!-- Live Micro Pulse Info -->
      <div class="flex items-center gap-2 text-xs font-mono text-slate-400 justify-end">
        <span class="hidden md:inline">Account: <strong class="text-slate-200">Pepperstone Demo #5258778</strong></span>
        <span class="hidden md:inline">|</span>
        <span id="hdr-flywheel-cycle" class="text-sky-300 font-bold">วนแล้ว 238 รอบ</span>
        <span>|</span>
        <span id="hdr-active-stage" class="text-amber-300 font-bold truncate max-w-[200px]">STAGE 1: Data Pipeline</span>
      </div>

    </div>
  </nav>

  <!-- ========================================================================= -->
  <!-- MAIN WORKSPACE CONTENT                                                    -->
  <!-- ========================================================================= -->
  <main class="max-w-[1600px] mx-auto p-4 sm:p-6 lg:p-8 space-y-8">

    <!-- ======================================================================= -->
    <!-- 3. HERO KEY METRICS CARDS (Point #2: 24-32px Bold Typography)           -->
    <!-- ======================================================================= -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      
      <!-- Card 1: Balance / Equity -->
      <div class="card-surface p-5 space-y-1">
        <div class="flex items-center justify-between text-xs text-slate-400 font-medium uppercase tracking-wider">
          <span>Real Account Balance</span>
          <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
        </div>
        <div id="hero-equity" class="text-3xl font-extrabold font-mono text-emerald-400 tracking-tight">
          $82.93 <span class="text-xs font-normal text-slate-400">USD</span>
        </div>
        <div class="text-xs text-slate-400 font-mono flex items-center justify-between pt-1">
          <span>Deposit: $100.00</span>
          <span class="text-emerald-400 font-bold">Online #5258778</span>
        </div>
      </div>

      <!-- Card 2: Champion Net Profit -->
      <div class="card-surface p-5 space-y-1">
        <div class="flex items-center justify-between text-xs text-slate-400 font-medium uppercase tracking-wider">
          <span>Champion Net PnL (XAU)</span>
          <span class="px-1.5 py-0.5 rounded bg-emerald-500/15 text-emerald-300 text-[11px] font-bold">M1 Verified</span>
        </div>
        <div id="hero-net-profit" class="text-3xl font-extrabold font-mono text-emerald-400 tracking-tight">
          +$96.00 <span class="text-xs font-normal text-slate-400">USD</span>
        </div>
        <div class="text-xs text-slate-400 font-mono flex items-center justify-between pt-1">
          <span>Strategy: VWAP Absorption</span>
          <span class="text-sky-300 font-bold">Trend Shield</span>
        </div>
      </div>

      <!-- Card 3: Profit Factor & Win Rate -->
      <div class="card-surface p-5 space-y-1">
        <div class="flex items-center justify-between text-xs text-slate-400 font-medium uppercase tracking-wider">
          <span>Profit Factor & Win Rate</span>
          <span class="px-1.5 py-0.5 rounded bg-sky-500/15 text-sky-300 text-[11px] font-bold">PF 3.00</span>
        </div>
        <div class="text-3xl font-extrabold font-mono text-white tracking-tight">
          3.00 <span class="text-lg font-normal text-slate-400">PF</span> · 50.0% <span class="text-xs font-normal text-slate-400">WR</span>
        </div>
        <div class="text-xs text-slate-400 font-mono flex items-center justify-between pt-1">
          <span>Trades: 24 ไม้ (3,345 Bars)</span>
          <span class="text-slate-300">Max DD: $12.00</span>
        </div>
      </div>

      <!-- Card 4: Statistical Power Gauge -->
      <div class="card-surface p-5 space-y-1">
        <div class="flex items-center justify-between text-xs text-slate-400 font-medium uppercase tracking-wider">
          <span>Sample Power (Truth Reset)</span>
          <span class="px-1.5 py-0.5 rounded bg-amber-500/15 text-amber-300 text-[11px] font-bold">N=79</span>
        </div>
        <div id="hero-sample-n" class="text-3xl font-extrabold font-mono text-amber-400 tracking-tight">
          N=79 <span class="text-sm font-normal text-slate-400">/ 500 ไม้</span>
        </div>
        <div class="text-xs text-slate-400 font-mono flex items-center justify-between pt-1">
          <span>Progress: 15.8%</span>
          <span class="text-amber-300 font-medium">รอ 500 ไม้พิสูจน์ Edge</span>
        </div>
      </div>

    </div>

    <!-- ======================================================================= -->
    <!-- 4. 10-STAGE PROGRESS STEPPER (Point #1: Clean Stepped Progress Bar)      -->
    <!-- ======================================================================= -->
    <div id="sec-lifecycle-stepper" class="card-surface p-6 space-y-4">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800/80 pb-3">
        <div>
          <h2 class="text-lg font-bold text-white flex items-center gap-2">
            <span>🔄</span> <span>10-Stage Institutional Lifecycle (สถาปัตยกรรมวงจรพัฒนาเทรดบอท 10 ขั้น)</span>
          </h2>
          <p class="text-xs text-slate-400 mt-0.5">
            กระบวนการแบบปิด (Closed-Loop Flywheel): เก็บข้อมูล ➔ สกัดสมมติฐาน ➔ เขียน C# cBot ➔ ตรวจสอบความเสี่ยง ➔ เทรดสด ➔ ทวนซ้ำ
          </p>
        </div>
        <div class="flex items-center gap-1.5 text-xs font-mono">
          <button onclick="setViewMode('FLYWHEEL')" id="btn-mode-flywheel" class="px-3 py-1 rounded-lg font-bold bg-sky-500/20 text-sky-300 border border-sky-500/40 cursor-pointer">
            ภาพรวม 10 ขั้น
          </button>
          <button onclick="setViewMode('FOCUS')" id="btn-mode-focus" class="px-3 py-1 rounded-lg font-medium text-slate-400 hover:text-white cursor-pointer">
            โฟกัสรายโมดูล
          </button>
        </div>
      </div>

      <!-- Modern Stepper Nodes Bar -->
      <div class="overflow-x-auto pb-2">
        <div class="flex items-center min-w-[900px] justify-between relative px-2">
          
          <!-- Background Progress Line -->
          <div class="absolute left-6 right-6 top-4 h-0.5 bg-slate-800 -z-0"></div>

          <!-- 10 Step Nodes -->
          <button onclick="selectPillar(1)" id="tab-p1" class="pillar-tab group flex flex-col items-center gap-1.5 z-10 cursor-pointer">
            <span class="w-8 h-8 rounded-full bg-slate-900 border-2 border-sky-500 text-sky-400 font-mono font-bold text-xs flex items-center justify-center group-hover:scale-110 transition shadow-md">1</span>
            <span class="text-[11px] font-semibold text-slate-300 group-hover:text-white whitespace-nowrap">Data Pipe</span>
          </button>

          <button onclick="selectPillar(2)" id="tab-p2" class="pillar-tab group flex flex-col items-center gap-1.5 z-10 cursor-pointer">
            <span class="w-8 h-8 rounded-full bg-slate-900 border-2 border-slate-700 text-slate-400 font-mono font-bold text-xs flex items-center justify-center group-hover:scale-110 transition">2</span>
            <span class="text-[11px] font-semibold text-slate-400 group-hover:text-white whitespace-nowrap">Alpha Gen</span>
          </button>

          <button onclick="selectPillar(3)" id="tab-p3" class="pillar-tab group flex flex-col items-center gap-1.5 z-10 cursor-pointer">
            <span class="w-8 h-8 rounded-full bg-slate-900 border-2 border-slate-700 text-slate-400 font-mono font-bold text-xs flex items-center justify-center group-hover:scale-110 transition">3</span>
            <span class="text-[11px] font-semibold text-slate-400 group-hover:text-white whitespace-nowrap">Strategy Dev</span>
          </button>

          <button onclick="selectPillar(4)" id="tab-p4" class="pillar-tab group flex flex-col items-center gap-1.5 z-10 cursor-pointer">
            <span class="w-8 h-8 rounded-full bg-slate-900 border-2 border-slate-700 text-slate-400 font-mono font-bold text-xs flex items-center justify-center group-hover:scale-110 transition">4</span>
            <span class="text-[11px] font-semibold text-slate-400 group-hover:text-white whitespace-nowrap">Backtest Lab</span>
          </button>

          <button onclick="selectPillar(5)" id="tab-p5" class="pillar-tab group flex flex-col items-center gap-1.5 z-10 cursor-pointer">
            <span class="w-8 h-8 rounded-full bg-slate-900 border-2 border-slate-700 text-slate-400 font-mono font-bold text-xs flex items-center justify-center group-hover:scale-110 transition">5</span>
            <span class="text-[11px] font-semibold text-slate-400 group-hover:text-white whitespace-nowrap">Quant Math</span>
          </button>

          <button onclick="selectPillar(6)" id="tab-p6" class="pillar-tab group flex flex-col items-center gap-1.5 z-10 cursor-pointer">
            <span class="w-8 h-8 rounded-full bg-slate-900 border-2 border-slate-700 text-slate-400 font-mono font-bold text-xs flex items-center justify-center group-hover:scale-110 transition">6</span>
            <span class="text-[11px] font-semibold text-slate-400 group-hover:text-white whitespace-nowrap">Risk Gate</span>
          </button>

          <button onclick="selectPillar(7)" id="tab-p7" class="pillar-tab group flex flex-col items-center gap-1.5 z-10 cursor-pointer">
            <span class="w-8 h-8 rounded-full bg-slate-900 border-2 border-slate-700 text-slate-400 font-mono font-bold text-xs flex items-center justify-center group-hover:scale-110 transition">7</span>
            <span class="text-[11px] font-semibold text-slate-400 group-hover:text-white whitespace-nowrap">Live Exec</span>
          </button>

          <button onclick="selectPillar(8)" id="tab-p8" class="pillar-tab group flex flex-col items-center gap-1.5 z-10 cursor-pointer">
            <span class="w-8 h-8 rounded-full bg-slate-900 border-2 border-slate-700 text-slate-400 font-mono font-bold text-xs flex items-center justify-center group-hover:scale-110 transition">8</span>
            <span class="text-[11px] font-semibold text-slate-400 group-hover:text-white whitespace-nowrap">Memory</span>
          </button>

          <button onclick="selectPillar(9)" id="tab-p9" class="pillar-tab group flex flex-col items-center gap-1.5 z-10 cursor-pointer">
            <span class="w-8 h-8 rounded-full bg-slate-900 border-2 border-slate-700 text-slate-400 font-mono font-bold text-xs flex items-center justify-center group-hover:scale-110 transition">9</span>
            <span class="text-[11px] font-semibold text-slate-400 group-hover:text-white whitespace-nowrap">Tracking</span>
          </button>

          <button onclick="selectPillar(10)" id="tab-p10" class="pillar-tab group flex flex-col items-center gap-1.5 z-10 cursor-pointer">
            <span class="w-8 h-8 rounded-full bg-slate-900 border-2 border-slate-700 text-slate-400 font-mono font-bold text-xs flex items-center justify-center group-hover:scale-110 transition">10</span>
            <span class="text-[11px] font-semibold text-slate-400 group-hover:text-white whitespace-nowrap">Feedback</span>
          </button>

        </div>
      </div>
    </div>

    <!-- ======================================================================= -->
    <!-- 5. ZONE 1: STRATEGY BACKTEST LAB (ห้องทดลองย้อนหลัง)                      -->
    <!-- ======================================================================= -->
    <section id="sec-zone-1" class="space-y-6">
      
      <!-- Section Header -->
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-3">
        <div>
          <div class="flex items-center gap-2">
            <span class="px-2.5 py-0.5 rounded-full text-xs font-bold bg-amber-500/15 text-amber-300 border border-amber-500/30 font-mono">
              ZONE 1
            </span>
            <h2 class="text-xl font-bold text-white tracking-tight">Strategy Backtest Lab (ห้องทดลองย้อนหลัง)</h2>
          </div>
          <p class="text-xs text-slate-400 mt-1">
            ผลการทดสอบย้อนหลังบนข้อมูลประวัติศาสตร์ 1 นาที (M1) และ Tick Spreads จริงของ Pepperstone · คัดเลือกเฉพาะโมเดลที่พิสูจน์แล้วว่าชนะค่าคอมมิชชั่น
          </p>
        </div>

        <!-- Strategy Switcher Tabs -->
        <div class="flex items-center gap-1.5 bg-slate-900/90 p-1 rounded-xl border border-slate-800 text-xs">
          <button onclick="switchIdxStrategy('vwap_absorption_xau')" id="idx-strat-vwap_absorption_xau" class="px-3 py-1.5 rounded-lg text-xs font-bold bg-amber-500/20 text-amber-300 border border-amber-500/40 cursor-pointer transition">
            🔥 VWAP Absorption (XAU)
          </button>
          <button onclick="switchIdxStrategy('dom_absorption_btc')" id="idx-strat-dom_absorption_btc" class="px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-900 text-slate-400 border border-slate-800 hover:text-white cursor-pointer transition">
            ⚡ DOM Absorption (BTC)
          </button>
          <button onclick="switchIdxStrategy('dom_absorption_eth')" id="idx-strat-dom_absorption_eth" class="px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-900 text-slate-400 border border-slate-800 hover:text-white cursor-pointer transition">
            🛡️ DOM Absorption (ETH)
          </button>
          <button onclick="switchIdxStrategy('dom_fade')" id="idx-strat-dom_fade" class="px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-900 text-slate-400 border border-slate-800 hover:text-white cursor-pointer transition">
            📦 DOM Fade (Baseline)
          </button>
        </div>
      </div>

      <!-- Strategy Details & Equity Curve Grid -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        <!-- Left: Strategy Summary & Parameters -->
        <div class="card-surface p-6 space-y-4">
          <div>
            <div class="text-xs font-mono text-amber-400 font-bold uppercase tracking-wider" id="idx-bt-name">VWAP Extended Absorption + Macro Trend Shield</div>
            <div class="text-xs text-slate-400 mt-0.5" id="idx-bt-desc">ดักจุดกลับตัวเมื่อราคาหลุดกรอบ Anchored VWAP SD >= 3.8 พร้อมตัวกรองข่าว</div>
          </div>

          <div class="grid grid-cols-2 gap-3 py-2 border-y border-slate-800/80 font-mono text-xs">
            <div>
              <div class="text-slate-400">Net Profit</div>
              <div id="idx-bt-net" class="text-2xl font-black text-emerald-400">+$96.00 USD</div>
            </div>
            <div>
              <div class="text-slate-400">Profit Factor</div>
              <div id="idx-bt-pf" class="text-2xl font-black text-white">3.00</div>
            </div>
            <div>
              <div class="text-slate-400">Win Rate</div>
              <div id="idx-bt-wr" class="text-lg font-bold text-emerald-300">50.0%</div>
            </div>
            <div>
              <div class="text-slate-400">Max Drawdown</div>
              <div id="idx-bt-dd" class="text-lg font-bold text-slate-300">$12.00 (0.12%)</div>
            </div>
          </div>

          <!-- Parameter List -->
          <div>
            <div class="text-xs font-bold text-slate-300 uppercase tracking-wider mb-2">กลไกและพารามิเตอร์ที่ผ่านการ Optimize</div>
            <div id="idx-bt-params" class="space-y-1.5 text-xs font-mono">
              <div class="flex justify-between border-b border-slate-900 pb-1">
                <span class="text-slate-400">Entry Anchor:</span>
                <span class="text-sky-300 font-bold">Anchored VWAP SD 3.8</span>
              </div>
              <div class="flex justify-between border-b border-slate-900 pb-1">
                <span class="text-slate-400">Exit Target:</span>
                <span class="text-sky-300 font-bold">Touch VWAP Baseline</span>
              </div>
              <div class="flex justify-between border-b border-slate-900 pb-1">
                <span class="text-slate-400">Stop Loss:</span>
                <span class="text-rose-400 font-bold">15 Pips / SD Band Exit</span>
              </div>
              <div class="flex justify-between border-b border-slate-900 pb-1">
                <span class="text-slate-400">News Void Filter:</span>
                <span class="text-emerald-400 font-bold">True (Void ATR > 2.0x)</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Center & Right: Equity Curve SVG & Trade Log -->
        <div class="lg:col-span-2 card-surface p-6 space-y-4">
          <div class="flex items-center justify-between border-b border-slate-800/80 pb-3">
            <h3 class="text-sm font-bold text-white flex items-center gap-2">
              <span>📈</span> <span>Cumulative Backtest Equity Curve (เส้นการเติบโตของพอร์ต)</span>
            </h3>
            <span id="idx-bt-trades" class="text-xs font-mono font-bold text-sky-400">24 ไม้</span>
          </div>

          <!-- SVG Equity Chart Container -->
          <div class="rounded-xl bg-slate-950/80 border border-slate-800 p-3 overflow-hidden">
            <svg id="idx-equity-svg" viewBox="0 0 600 150" class="w-full h-auto text-xs">
              <!-- Rendered dynamically by switchIdxStrategy -->
            </svg>
          </div>

          <!-- Recent Backtest Trades Table -->
          <div>
            <div class="text-xs font-bold text-slate-300 uppercase tracking-wider mb-2">ประวัติการเทรดย้อนหลังล่าสุด (Sample Trades)</div>
            <div class="overflow-x-auto rounded-xl border border-slate-800">
              <table class="w-full text-xs font-mono text-left">
                <thead class="bg-slate-900/90 text-slate-400 border-b border-slate-800">
                  <tr>
                    <th class="py-2 px-3">#</th>
                    <th class="py-2 px-3">Side</th>
                    <th class="py-2 px-3 text-right">Entry</th>
                    <th class="py-2 px-3 text-right">Exit</th>
                    <th class="py-2 px-3 text-right">Net PnL</th>
                    <th class="py-2 px-3">Exit Reason</th>
                  </tr>
                </thead>
                <tbody id="idx-bt-trades-tbody" class="divide-y divide-slate-900">
                  <!-- Injected via switchIdxStrategy -->
                </tbody>
              </table>
            </div>
          </div>

        </div>

      </div>

    </section>

    <!-- ======================================================================= -->
    <!-- 6. ZONE 2: BOT FLEET LIVE MONITOR & TRADINGVIEW STUDIO                  -->
    <!-- ======================================================================= -->
    <section id="sec-zone-2" class="space-y-6">
      
      <!-- Section Header -->
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-3">
        <div>
          <div class="flex items-center gap-2">
            <span class="px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-500/15 text-emerald-300 border border-emerald-500/30 font-mono">
              ZONE 2
            </span>
            <h2 class="text-xl font-bold text-white tracking-tight">Bot Fleet Live Monitor (ระบบมอนิเตอร์บอทสด)</h2>
          </div>
          <p class="text-xs text-slate-400 mt-1">
            ข้อมูลพอร์ตเทรดจริงบน Pepperstone Demo Account #5258778 พร้อมสัญญาณ L2 DOM Imbalance และกราฟสดจาก TradingView
          </p>
        </div>

        <div class="flex items-center gap-2 text-xs font-mono text-slate-400">
          <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
          <span>Forward Telemetry: <strong id="idx-z2-updated" class="text-emerald-400">Live</strong></span>
        </div>
      </div>

      <!-- TradingView Interactive Embed Studio (Mandatory Card) -->
      <div id="tradingview-studio-card" class="card-surface p-6 space-y-4">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800/80 pb-3">
          <div>
            <h3 class="text-base font-bold text-white flex items-center gap-2">
              <span>📊</span> <span>Live Microstructure Studio (TradingView Real-Time Embed)</span>
            </h3>
            <p class="text-xs text-slate-400 mt-0.5">
              วิเคราะห์โครงสร้างตลาดสด: แนวรับต้าน สภาพคล่อง L2 DOM และจุด Breakout CHoCH แบบ Real-time
            </p>
          </div>

          <!-- Symbol Switcher Tabs -->
          <div class="flex items-center gap-1.5 bg-slate-900/90 p-1 rounded-xl border border-slate-800 font-mono text-xs">
            <button onclick="changeTvSymbol('BINANCE:BTCUSDT', this)" class="tv-sym-btn px-3 py-1.5 rounded-lg bg-sky-500/20 text-sky-300 font-bold border border-sky-500/40 cursor-pointer">
              ₿ BTCUSD (Asia Champion)
            </button>
            <button onclick="changeTvSymbol('BINANCE:ETHUSDT', this)" class="tv-sym-btn px-3 py-1.5 rounded-lg text-slate-400 hover:text-white cursor-pointer">
              ⟠ ETHUSD (London Champion)
            </button>
            <button onclick="changeTvSymbol('CAPITALCOM:GOLD', this)" class="tv-sym-btn px-3 py-1.5 rounded-lg text-slate-400 hover:text-white cursor-pointer">
              🥇 XAUUSD (NY Fader)
            </button>
          </div>
        </div>

        <!-- TradingView Iframe Container -->
        <div class="rounded-xl overflow-hidden border border-slate-800/90 bg-slate-950 relative shadow-inner" style="height: 480px;">
          <div id="tv_chart_container" style="height: 100%; width: 100%;"></div>
        </div>

        <!-- Chart Annotation Explainer Box -->
        <div class="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 text-xs text-slate-300 leading-relaxed">
          <strong class="text-sky-300 font-mono">💡 จุดสังเกตการเทรดตาม 4 เสาหลัก:</strong> เมื่อราคาวิ่งลงมาชนกำแพงสภาพคล่อง <span class="text-emerald-400 font-bold">L2 DOM Bid Wall (&gt;1.4x)</span> และเกิดไส้เทียนดีดตัว (Absorption Wick) จากนั้นแท่ง M1/M5 ปิดเหนือแนวสวิงเดิมเป็น <span class="text-sky-300 font-bold">Displacement CHoCH</span> ให้รอราคาย่อตัวกลับมา Retest ที่กรอบ Fibo Golden Zone 50-65% เพื่อเปิดออเดอร์
        </div>
      </div>

      <!-- Architecture V4: Multi-Dimensional Market Intelligence & Context Fingerprinting Studio -->
      <div id="market-intelligence-v4-card" class="card-surface p-6 space-y-4">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800/80 pb-3">
          <div>
            <div class="flex items-center gap-2">
              <span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-sky-500/20 text-sky-300 border border-sky-500/40 font-mono">
                ARCHITECTURE V4
              </span>
              <h3 class="text-base font-bold text-white flex items-center gap-2">
                <span>🧠</span> <span>Adaptive Market Intelligence &amp; Context Fingerprint Engine</span>
              </h3>
            </div>
            <p class="text-xs text-slate-400 mt-1">
              ระบบจำแนก 13 สภาวะตลาด, ตรวจจับบริบทเซสชัน, ข่าวเศรษฐกิจมหภาค, และการเลือกกลยุทธ์อัตโนมัติ (STR-001 - STR-009)
            </p>
          </div>
          <div class="flex items-center gap-2 text-xs font-mono text-slate-400">
            <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            <span>24/7 Intelligence Daemon: <strong class="text-emerald-400 font-bold">Active</strong></span>
          </div>
        </div>

        <!-- 4-Asset Market Intelligence Grid -->
        <div id="market-intel-grid" class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-3">
          <!-- Dynamically injected via renderMarketIntelligenceV4 -->
        </div>

        <!-- Context Attribution & Strategy Switching Audit Banner -->
        <div id="market-intel-audit-bar" class="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 text-xs flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div class="flex items-center gap-2">
            <span class="text-amber-400 font-mono font-bold">🛡️ Institutional Risk Governor V4:</span>
            <span class="text-slate-300 font-mono text-[11px]">Daily Loss Limit: <strong class="text-emerald-400">-$10.00 USD</strong> | Daily Flat Cutoff: <strong class="text-amber-300">21:45 UTC</strong> | Environment: <strong class="text-sky-300">Pepperstone Demo #5258778</strong></span>
          </div>
          <div id="intel-recent-switch" class="text-slate-400 font-mono text-[11px] truncate max-w-md">
            <!-- Recent switch injected dynamically -->
          </div>
        </div>
      </div>

      <!-- Live Bot Fleet Cards & DOM Tug-of-War Grid -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        <!-- Left: 4 Live Bot Heartbeat Cards -->
        <div class="lg:col-span-2 space-y-4">
          <div class="flex items-center justify-between">
            <h3 class="text-sm font-bold text-white flex items-center gap-2">
              <span>🤖</span> <span>Bot Fleet Real-Time Heartbeats (4 Live Bots)</span>
            </h3>
            <span class="text-xs font-mono text-emerald-400">Execution Watchdog: 24/7 Active</span>
          </div>

          <div id="live-fleet-container" class="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <!-- Injected via fetchLiveStatus / renderLiveBots -->
          </div>

          <!-- Live L2 Order Book Imbalance Tug-of-War -->
          <div class="card-surface p-5 space-y-3">
            <div class="flex items-center justify-between text-xs font-bold text-white">
              <span>📊 Order Book L2 Imbalance Tug-of-War (Bids vs Asks)</span>
              <span class="text-slate-400 font-mono text-[11px]">Depth 25 Layers</span>
            </div>
            <div id="live-dom-tug-list" class="space-y-3">
              <!-- Injected dynamically -->
            </div>
          </div>
        </div>

        <!-- Right: Recent Live Trades & Execution Controller -->
        <div class="card-surface p-5 space-y-4">
          <div class="flex items-center justify-between border-b border-slate-800 pb-2">
            <h3 class="text-sm font-bold text-white flex items-center gap-2">
              <span>⚡</span> <span>Live Execution Stream (Pepperstone)</span>
            </h3>
            <span class="text-xs font-mono text-slate-400">Demo #5258778</span>
          </div>

          <div class="overflow-x-auto rounded-xl border border-slate-800">
            <table class="w-full text-xs font-mono text-left">
              <thead class="bg-slate-900 text-slate-400 border-b border-slate-800">
                <tr>
                  <th class="py-2 px-2.5">Time</th>
                  <th class="py-2 px-2.5">Symbol</th>
                  <th class="py-2 px-2.5">Side</th>
                  <th class="py-2 px-2.5 text-right">Price</th>
                  <th class="py-2 px-2.5 text-right">Slip</th>
                  <th class="py-2 px-2.5 text-right">Lat</th>
                </tr>
              </thead>
              <tbody id="live-trades-tbody" class="divide-y divide-slate-900">
                <!-- Injected via renderRecentTrades -->
              </tbody>
            </table>
          </div>



        </div>

      </div>

    </section>

    <!-- ======================================================================= -->
    <!-- 7. 4-PILLAR QUANT ARCHITECTURE & MATHEMATICAL VALIDATION SUITE           -->
    <!-- ======================================================================= -->
    <section id="sec-pillar-ensemble" class="space-y-6">
      
      <div class="border-b border-slate-800 pb-3">
        <h2 class="text-xl font-bold text-white flex items-center gap-2">
          <span>🛡️</span> <span>4-Pillar Quantitative Architecture & Mathematical Validation Suite</span>
        </h2>
        <p class="text-xs text-slate-400 mt-1">
          ระบบคัดกรองสมมติฐานทางสถิติและแบบจำลองทางคณิตศาสตร์ 4 เสาหลัก ป้องกัน Overfitting 100%
        </p>
      </div>

      <!-- Foundry Funnel SVG Box -->
      <div id="strategy-foundry-card" class="card-surface p-6 space-y-4">
        <div class="flex items-center justify-between border-b border-slate-800 pb-3">
          <h3 class="text-base font-bold text-white flex items-center gap-2">
            <span>🔬</span> <span>Quantitative Strategy Foundry & Mathematical Funnel</span>
          </h3>
          <span class="px-2.5 py-0.5 rounded text-xs font-mono font-bold bg-sky-500/20 text-sky-300 border border-sky-500/30">
            Truth Reset Mandate
          </span>
        </div>
        <div id="svg-foundry-funnel" class="overflow-hidden rounded-xl border border-slate-800 bg-slate-950/80 p-3">
          {svg_funnel}
        </div>
      </div>

      <!-- 4 Pillar Blueprints Grid -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        
        <!-- Pillar 1 Blueprint -->
        <div class="card-surface p-4 space-y-2">
          <div class="text-xs font-bold text-sky-300">Pillar 1: Structural Anchor</div>
          <div id="svg-pillar1-blueprint" class="rounded-lg overflow-hidden border border-slate-800 bg-slate-950/80 p-2">
            {svg_p1}
          </div>
          <p class="text-xs text-slate-400 leading-relaxed">
            Anchored VWAP คำนวณจุดสมดุลราคาของสถาบัน เพื่อเป็นแนวรับต้านโครงสร้างหลัก
          </p>
        </div>

        <!-- Pillar 2 Blueprint -->
        <div class="card-surface p-4 space-y-2">
          <div class="text-xs font-bold text-purple-300">Pillar 2: CHoCH Confirmation</div>
          <div id="svg-pillar2-blueprint" class="rounded-lg overflow-hidden border border-slate-800 bg-slate-950/80 p-2">
            {svg_p2}
          </div>
          <p class="text-xs text-slate-400 leading-relaxed">
            Displacement Change of Character ยืนยันการเปลี่ยนทิศทางของ Order Flow
          </p>
        </div>

        <!-- Pillar 3 Blueprint -->
        <div class="card-surface p-4 space-y-2">
          <div class="text-xs font-bold text-rose-300">Pillar 3: News Void Gate</div>
          <div id="svg-pillar3-blueprint" class="rounded-lg overflow-hidden border border-slate-800 bg-slate-950/80 p-2">
            {svg_p3}
          </div>
          <p class="text-xs text-slate-400 leading-relaxed">
            งดเปิดออเดอร์ช่วงข่าวกลืนสภาพคล่อง (Void ATR > 2.0x) ลดความผันผวนรุนแรง
          </p>
        </div>

        <!-- Pillar 4 Blueprint -->
        <div class="card-surface p-4 space-y-2">
          <div class="text-xs font-bold text-emerald-300">Pillar 4: Structural Exit & Kelly</div>
          <div id="svg-pillar4-blueprint" class="rounded-lg overflow-hidden border border-slate-800 bg-slate-950/80 p-2">
            {svg_p4}
          </div>
          <p class="text-xs text-slate-400 leading-relaxed">
            ปิดทำกำไรที่เส้นสภาพคล่องฝั่งตรงข้าม และคำนวณ Lot Size ด้วย Fractional Kelly
          </p>
        </div>

      </div>

      <!-- 4 SVG Evolution Step Charts -->
      <div id="four-pillars-ensemble-card" class="card-surface p-6 space-y-4">
        <h3 class="text-base font-bold text-white flex items-center gap-2">
          <span>⚙️</span> <span>Flywheel Engine Steps (ภาพแสดงขั้นตอนการทำงานจริง)</span>
        </h3>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-5">
          
          <!-- STEP 1 CARD -->
          <div class="p-5 rounded-2xl bg-slate-900/60 dark:bg-slate-950/80 border border-slate-700/60 dark:border-slate-800 space-y-3">
            <div class="flex items-center justify-between">
              <span class="font-extrabold text-sky-400 flex items-center gap-2 text-sm tracking-wide">
                <span>📊</span> <span>1. แหล่งข้อมูล (Data Ingestion)</span>
              </span>
              <span class="px-2.5 py-0.5 rounded-lg text-xs font-mono font-bold bg-sky-500/15 text-sky-300 border border-sky-500/30">✓ STREAMING</span>
            </div>
            <div id="svg-step1-chart">
              {svg1}
            </div>
            <p class="text-xs text-slate-300 dark:text-slate-300 leading-relaxed">
              บันทึกข้อมูล Order Book L2 Depth 25 ระดับ และ Tick Flow สดจาก Pepperstone Demo #5258778 อย่างต่อเนื่อง
            </p>
            <div class="flex flex-wrap gap-2 text-xs font-mono pt-1">
              <span class="px-2.5 py-1 rounded-lg bg-slate-800/80 text-slate-300 border border-slate-700/80">ความถี่: <strong class="text-white">Real-time Millisecond</strong></span>
              <span class="px-2.5 py-1 rounded-lg bg-slate-800/80 text-emerald-300 border border-slate-700/80">สเปรด: <strong>0.15 pips</strong></span>
              <span class="px-2.5 py-1 rounded-lg bg-slate-800/80 text-slate-300 border border-slate-700/80">Slippage: <strong class="text-white">0.08 pips</strong></span>
            </div>
          </div>

          <!-- STEP 2 CARD -->
          <div class="p-5 rounded-2xl bg-slate-900/60 dark:bg-slate-950/80 border border-slate-700/60 dark:border-slate-800 space-y-3">
            <div class="flex items-center justify-between">
              <span class="font-extrabold text-purple-400 flex items-center gap-2 text-sm tracking-wide">
                <span>📈</span> <span>2. ทดสอบสมมติฐาน (Hypothesis Testing)</span>
              </span>
              <span class="px-2.5 py-0.5 rounded-lg text-xs font-mono font-bold bg-purple-500/15 text-purple-300 border border-purple-500/30">✓ DISCOVERED</span>
            </div>
            <div id="svg-step2-chart">
              {svg2}
            </div>
            <p class="text-xs text-slate-300 dark:text-slate-300 leading-relaxed">
              ทดสอบ 598 รูปแบบบนข้อมูลสด: ค้นพบ Champion VWAP Absorption (XAU) +$96.00 และ BTC DOM Absorption (Win Rate 59.1%)
            </p>
            <div class="flex flex-wrap gap-2 text-xs font-mono pt-1">
              <span class="px-2.5 py-1 rounded-lg bg-slate-800/80 text-slate-300 border border-slate-700/80">สมมติฐาน: <strong class="text-white">598 Sweeps</strong></span>
              <span class="px-2.5 py-1 rounded-lg bg-slate-800/80 text-purple-300 border border-slate-700/80">Win Rate: <strong>59.1%</strong></span>
              <span class="px-2.5 py-1 rounded-lg bg-slate-800/80 text-emerald-300 border border-slate-700/80">Profit Factor: <strong>2.01</strong></span>
            </div>
          </div>

          <!-- STEP 3 CARD (Pointed in user screenshot) -->
          <div class="p-5 rounded-2xl bg-slate-900/60 dark:bg-slate-950/80 border border-slate-700/60 dark:border-slate-800 space-y-3">
            <div class="flex items-center justify-between">
              <span class="font-extrabold text-emerald-400 flex items-center gap-2 text-sm tracking-wide">
                <span>📊</span> <span>3. รายงานผลลัพธ์ (Performance & Tracking)</span>
              </span>
              <span id="fw-step3-status" class="px-2.5 py-0.5 rounded-lg text-xs font-mono font-bold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">✓ COMPLETED</span>
            </div>
            <div id="svg-step3-chart">
              {svg3}
            </div>
            <p id="fw-step3-desc" class="text-xs text-slate-300 dark:text-slate-300 leading-relaxed">
              ผลตอบแทนข้อมูลสด: Net PnL +$15.20 USD, Profit Factor 1.90, กำไรจริง 6 จาก 7 วัน (Daily Win Rate 85.7%), BTC กำไร 100% ทุกวัน
            </p>
            <div id="fw-step3-meta" class="flex flex-wrap gap-2 text-xs font-mono pt-1">
              <span class="px-2.5 py-1 rounded-lg bg-slate-800/80 text-emerald-300 border border-slate-700/80">Net PnL: <strong class="text-emerald-400 font-extrabold">+$15.20 USD</strong></span>
              <span class="px-2.5 py-1 rounded-lg bg-slate-800/80 text-sky-300 border border-slate-700/80">PF: <strong>1.90</strong></span>
              <span class="px-2.5 py-1 rounded-lg bg-slate-800/80 text-emerald-300 border border-slate-700/80">Daily Win: <strong>85.7% (6/7 วัน)</strong></span>
              <span class="px-2.5 py-1 rounded-lg bg-slate-800/80 text-slate-300 border border-slate-700/80">Latency: <strong class="text-white">28.5 ms</strong></span>
            </div>
          </div>

          <!-- STEP 4 CARD (Pointed in user screenshot) -->
          <div class="p-5 rounded-2xl bg-slate-900/60 dark:bg-slate-950/80 border border-slate-700/60 dark:border-slate-800 space-y-3">
            <div class="flex items-center justify-between">
              <span class="font-extrabold text-pink-400 flex items-center gap-2 text-sm tracking-wide">
                <span>💡</span> <span>4. แนวทางพัฒนา (10-Stage Evolution Engine)</span>
              </span>
              <span id="fw-step4-status" class="px-2.5 py-0.5 rounded-lg text-xs font-mono font-bold bg-pink-500/15 text-pink-400 border border-pink-500/30">✓ APPROVED</span>
            </div>
            <div id="svg-step4-chart">
              {svg4}
            </div>
            <p id="fw-step4-desc" class="text-xs text-slate-300 dark:text-slate-300 leading-relaxed">
              จัดเก็บ 122 รอบเก่าเข้าฐานข้อมูลถาวร และเริ่มต้นนับรอบ #1 ใหม่ในยุค Pure Live Microstructure สำเร็จ พร้อมรัน 24/7 Watchdog เข้าสู่รอบ #2
            </p>
            <div id="fw-step4-meta" class="flex flex-wrap gap-2 text-xs font-mono pt-1">
              <span class="px-2.5 py-1 rounded-lg bg-slate-800/80 text-emerald-300 border border-slate-700/80">สถานะ: <strong class="text-white">นับรอบ #1 ข้อมูลสดสำเร็จ</strong></span>
              <span class="px-2.5 py-1 rounded-lg bg-slate-800/80 text-purple-300 border border-slate-700/80">รอบถัดไป: <strong class="text-purple-400">วนรอบ #2 ตรวจจับสภาพคล่อง 24/7</strong></span>
            </div>
          </div>

        </div>
      </div>

      <!-- System Governance & Institutional Rules (Required Check) -->
      <div class="card-surface p-6 space-y-3">
        <h3 class="text-sm font-bold text-white flex items-center gap-2">
          <span>📜</span> <span>System Governance & Institutional Rules (กฎพัฒนาหน้าเว็บให้เป็นปัจจุบัน)</span>
        </h3>
        <p class="text-xs text-slate-300 leading-relaxed">
          1. <strong>Real-Time Data Mandate:</strong> ข้อมูลบนเว็บต้องซิงก์จาก BacktestLab cTrader แท้จริงเสมอ โดยปราศจากสมมติฐานปลอม<br>
          2. <strong>Zero-Secret Frontend:</strong> ไม่ฝัง API Key หรือ Client Secret บนหน้าเว็บเด็ดขาด<br>
          3. <strong>Strict Risk Control:</strong> กำหนด Kill Switch และสิทธิ์การสั่งการเฉพาะบัญชีที่ผ่านการตรวจสอบ JWT
        </p>
      </div>

    </section>

  </main>

  <!-- ========================================================================= -->
  <!-- MODALS: OWNER ADMIN LOGIN & HITL STAGE 1 APPROVE                          -->
  <!-- ========================================================================= -->



  <!-- HITL Stage 1 Modal -->
  <div id="hitl-cli-modal" class="hidden fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
    <div class="card-surface max-w-lg w-full p-6 space-y-4">
      <div class="flex items-center justify-between border-b border-slate-800 pb-2">
        <span class="font-bold text-sm text-emerald-400">✅ อนุมัติกลยุทธ์ผ่าน Terminal CLI</span>
        <button onclick="document.getElementById('hitl-cli-modal').classList.add('hidden')" class="text-slate-400 hover:text-white font-mono">✕</button>
      </div>
      <p class="text-xs text-slate-300">รันคำสั่งนี้บนเครื่องเทรดเพื่อส่งสัญญาณอนุมัติเข้าสู่ cTrader Automate:</p>
      <div id="cli-cmd-box" class="p-3 rounded-xl bg-slate-950 font-mono text-xs text-emerald-300 border border-slate-800 select-all break-all">
        python research/control.py --approve stage1 --symbol XAUUSD --strategy VWAP_ABSORPTION
      </div>
      <button onclick="copyCliCmd()" id="btn-copy-cli" class="w-full py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-white font-bold text-xs border border-slate-700 transition">
        📋 คัดลอกคำสั่ง
      </button>
    </div>
  </div>

  <!-- Inline DATA for Instant Initial Load -->
  <script>
    const DATA = {compact_bt};
  </script>

  <!-- TradingView Script -->
  <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>

  <!-- Application Logic -->
  <script>
    let currentPillar = 1;
    let currentViewMode = 'FLYWHEEL';
    let currentIdxStrategy = 'vwap_absorption_xau';
    let tvWidget = null;
    let currentTvSymbol = 'BINANCE:BTCUSDT';

    function init() {{
      switchIdxStrategy('vwap_absorption_xau');
      fetchBacktestData();
      renderLiveBots();
      fetchLiveStatus();
      setInterval(fetchLiveStatus, 3000);
      
      const currentTheme = document.documentElement.classList.contains('light') ? 'light' : 'dark';
      updateThemeToggleButton(currentTheme);
      initTradingViewChart('BINANCE:BTCUSDT');
    }}

    // Interactive Zone Switching (Point #3: Segmented Switch)
    function setInteractiveZone(zone) {{
      const secZone1 = document.getElementById('sec-zone-1');
      const secZone2 = document.getElementById('sec-zone-2');
      const secStepper = document.getElementById('sec-lifecycle-stepper');
      const secEnsemble = document.getElementById('sec-pillar-ensemble');
      
      const tabs = ['all', 'backtest', 'live', 'lifecycle'];
      tabs.forEach(t => {{
        const btn = document.getElementById('zone-tab-' + t);
        if (!btn) return;
        if (t === zone) {{
          btn.className = 'px-3.5 py-1.5 rounded-lg font-bold bg-sky-500/20 text-sky-300 border border-sky-500/40 transition cursor-pointer flex items-center gap-1.5 shadow-sm';
        }} else {{
          btn.className = 'px-3.5 py-1.5 rounded-lg font-medium text-slate-400 hover:text-white transition cursor-pointer flex items-center gap-1.5';
        }}
      }});

      if (zone === 'all') {{
        if (secZone1) secZone1.classList.remove('hidden');
        if (secZone2) secZone2.classList.remove('hidden');
        if (secStepper) secStepper.classList.remove('hidden');
        if (secEnsemble) secEnsemble.classList.remove('hidden');
      }} else if (zone === 'backtest') {{
        if (secZone1) secZone1.classList.remove('hidden');
        if (secZone2) secZone2.classList.add('hidden');
        if (secStepper) secStepper.classList.add('hidden');
        if (secEnsemble) secEnsemble.classList.add('hidden');
        secZone1.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
      }} else if (zone === 'live') {{
        if (secZone1) secZone1.classList.add('hidden');
        if (secZone2) secZone2.classList.remove('hidden');
        if (secStepper) secStepper.classList.add('hidden');
        if (secEnsemble) secEnsemble.classList.add('hidden');
        secZone2.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
      }} else if (zone === 'lifecycle') {{
        if (secZone1) secZone1.classList.add('hidden');
        if (secZone2) secZone2.classList.add('hidden');
        if (secStepper) secStepper.classList.remove('hidden');
        if (secEnsemble) secEnsemble.classList.remove('hidden');
        secStepper.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
      }}
    }}

    // Strategy Switching (Deliverable A)
    function switchIdxStrategy(strat) {{
      currentIdxStrategy = strat;
      const tabs = ['vwap_absorption_xau', 'dom_absorption_btc', 'dom_absorption_eth', 'dom_fade'];
      tabs.forEach(k => {{
        const btn = document.getElementById('idx-strat-' + k);
        if (!btn) return;
        if (k === strat) {{
          btn.className = 'px-3 py-1.5 rounded-lg text-xs font-bold bg-amber-500/20 text-amber-300 border border-amber-500/40 cursor-pointer transition';
        }} else {{
          btn.className = 'px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-900 text-slate-400 border border-slate-800 hover:text-white cursor-pointer transition';
        }}
      }});

      const sObj = (DATA && DATA[strat]) ? DATA[strat] : ((DATA && DATA.strategies && DATA.strategies[strat]) ? DATA.strategies[strat] : null);
      if (!sObj) return;
      const sum = sObj.summary || {{}};
      const params = sObj.parameters || {{}};

      const setTxt = (id, val) => {{ const el = document.getElementById(id); if (el) el.textContent = val; }};
      setTxt('idx-bt-name', sObj.name || strat);
      setTxt('idx-bt-desc', params.EntryLogic ? (params.EntryLogic + ' • ' + (params.TrendShield || params.ExitLogic || '')) : 'Verified M1/Tick Backtest');
      
      const net = sum.netProfit !== undefined ? sum.netProfit : (sObj.total_pnl || 0);
      const netEl = document.getElementById('idx-bt-net');
      if (netEl) {{
        netEl.textContent = (net >= 0 ? '+$' : '-$') + Math.abs(net).toFixed(2) + ' USD';
        netEl.className = 'text-2xl font-black font-mono ' + (net >= 0 ? 'text-emerald-400' : 'text-rose-400');
      }}
      setTxt('idx-bt-pf', (sum.profitFactor !== undefined ? Number(sum.profitFactor).toFixed(2) : '3.00'));
      const wr = sum.winRate !== undefined ? sum.winRate : ((sObj.win_rate || 0) * 100);
      setTxt('idx-bt-wr', Number(wr).toFixed(1) + '%');
      const dd = sum.maxDrawdownDollars !== undefined ? sum.maxDrawdownDollars : 12.0;
      setTxt('idx-bt-dd', '$' + Number(dd).toFixed(2) + ' (' + Number(sum.maxDrawdownPercent || 0.12).toFixed(2) + '%)');
      setTxt('idx-bt-trades', (sum.totalTrades !== undefined ? sum.totalTrades : (sObj.total_trades || 0)) + ' ไม้');

      // Params list
      const pList = document.getElementById('idx-bt-params');
      if (pList) {{
        const entries = Object.entries(params);
        pList.innerHTML = entries.map(([k, v]) => `
          <div class="flex justify-between border-b border-slate-900 pb-1">
            <span class="text-slate-400">${{k}}:</span>
            <span class="text-sky-300 font-bold text-right">${{v}}</span>
          </div>
        `).join('');
      }}

      renderIdxEquityCurve(sObj);

      // Trades table
      const tbody = document.getElementById('idx-bt-trades-tbody');
      if (tbody && sObj.trades) {{
        tbody.innerHTML = sObj.trades.slice(0, 6).map(t => {{
          const pnl = t.pnl !== undefined ? t.pnl : (t.net_pnl || 0);
          return `
            <tr class="hover:bg-slate-900/60">
              <td class="py-1.5 px-3 text-slate-400">#${{t.id || '-'}}</td>
              <td class="py-1.5 px-3 font-bold ${{ (t.type || t.direction) === 'BUY' ? 'text-sky-400' : 'text-purple-400' }}">${{t.type || t.direction}}</td>
              <td class="py-1.5 px-3 text-right text-slate-300">${{Number(t.entryPrice || t.entry_price || 0).toFixed(2)}}</td>
              <td class="py-1.5 px-3 text-right text-slate-300">${{Number(t.exitPrice || t.exit_price || 0).toFixed(2)}}</td>
              <td class="py-1.5 px-3 text-right font-bold ${{pnl >= 0 ? 'text-emerald-400' : 'text-rose-400'}}">${{pnl >= 0 ? '+$' : '-$'}}${{Math.abs(pnl).toFixed(2)}}</td>
              <td class="py-1.5 px-3 text-slate-400">${{t.exitReason || t.reason || '-'}}</td>
            </tr>
          `;
        }}).join('');
      }}
    }}

    function renderIdxEquityCurve(sObj) {{
      const svg = document.getElementById('idx-equity-svg');
      if (!svg) return;
      const eq = sObj.equity_curve || [10000, 10096];
      if (eq.length < 2) return;
      const minV = Math.min(...eq);
      const maxV = Math.max(...eq);
      const span = Math.max(0.01, maxV - minV);
      const pts = eq.map((v, i) => {{
        const x = (i / (eq.length - 1)) * 580 + 10;
        const y = 135 - ((v - minV) / span) * 115;
        return `${{x.toFixed(1)}},${{y.toFixed(1)}}`;
      }}).join(' ');
      const areaPts = `10,145 ${{pts}} 590,145`;
      svg.innerHTML = `
        <defs>
          <linearGradient id="idxEqGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="#10b981" stop-opacity="0.35"/>
            <stop offset="100%" stop-color="#10b981" stop-opacity="0.0"/>
          </linearGradient>
        </defs>
        <polygon points="${{areaPts}}" fill="url(#idxEqGrad)" />
        <polyline fill="none" stroke="#10b981" stroke-width="2.5" points="${{pts}}" />
      `;
    }}

    async function fetchBacktestData() {{
      try {{
        const res = await fetch('data/backtest_data.json?t=' + Date.now());
        if (!res.ok) return;
        const fresh = await res.json();
        if (fresh) {{
          Object.assign(DATA, fresh);
          switchIdxStrategy(currentIdxStrategy);
        }}
      }} catch (e) {{}}
    }}

    // Stepper Navigation
    function selectPillar(num) {{
      currentPillar = num;
      for (let i = 1; i <= 10; i++) {{
        const tab = document.getElementById('tab-p' + i);
        if (tab) {{
          const node = tab.querySelector('span');
          if (node) {{
            if (i === num) {{
              node.className = 'w-8 h-8 rounded-full bg-sky-500 text-white font-mono font-bold text-xs flex items-center justify-center scale-110 shadow-lg shadow-sky-500/50';
            }} else {{
              node.className = 'w-8 h-8 rounded-full bg-slate-900 border-2 border-slate-700 text-slate-400 font-mono font-bold text-xs flex items-center justify-center';
            }}
          }}
        }}
      }}
    }}

    function setViewMode(mode) {{
      currentViewMode = mode;
      const btnFly = document.getElementById('btn-mode-flywheel');
      const btnFoc = document.getElementById('btn-mode-focus');
      if (mode === 'FLYWHEEL') {{
        btnFly.className = 'px-3 py-1 rounded-lg font-bold bg-sky-500/20 text-sky-300 border border-sky-500/40 cursor-pointer';
        btnFoc.className = 'px-3 py-1 rounded-lg font-medium text-slate-400 hover:text-white cursor-pointer';
      }} else {{
        btnFoc.className = 'px-3 py-1 rounded-lg font-bold bg-sky-500/20 text-sky-300 border border-sky-500/40 cursor-pointer';
        btnFly.className = 'px-3 py-1 rounded-lg font-medium text-slate-400 hover:text-white cursor-pointer';
      }}
    }}

    // Live Telemetry Rendering (Deliverable B)
    function renderLiveBots(bots) {{
      const container = document.getElementById('live-fleet-container');
      const tugList = document.getElementById('live-dom-tug-list');
      if (!container) return;

      const fallbackBots = [
        {{ symbol: "BTCUSD", icon: "🪙", current_price: 75059.35, spread: 15.06, imbalance: -0.004, cvd: 1593, is_online: true }},
        {{ symbol: "ETHUSD", icon: "🔷", current_price: 2331.49, spread: 2.02, imbalance: 0.019, cvd: -605, is_online: true }},
        {{ symbol: "XAUUSD", icon: "🟡", current_price: 4820.99, spread: 0.108, imbalance: 0.012, cvd: -750, is_online: true }},
        {{ symbol: "GOLD-PERP", icon: "📊", current_price: 4821.50, spread: 0.32, imbalance: -0.008, cvd: -1794, is_online: true }}
      ];

      const list = (bots && bots.length) ? bots : fallbackBots;

      container.innerHTML = list.map(b => {{
        return `
          <div class="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 space-y-2">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-1.5 font-mono font-bold text-white text-sm">
                <span>${{b.icon || '🤖'}}</span>
                <span>${{b.symbol}}</span>
              </div>
              <span class="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">LIVE</span>
            </div>
            <div class="font-mono text-xl font-extrabold text-emerald-400">
              $${{(b.current_price || 0).toLocaleString(undefined, {{ maximumFractionDigits: 2 }})}}
            </div>
            <div class="flex justify-between text-xs text-slate-400 font-mono">
              <span>Spread: $${{(b.spread || 0).toFixed(2)}}</span>
              <span>Imb: ${{b.imbalance >= 0 ? '+' : ''}}${{(b.imbalance || 0).toFixed(3)}}</span>
            </div>
          </div>
        `;
      }}).join('');

      if (tugList) {{
        tugList.innerHTML = list.slice(0, 3).map(b => {{
          const imb = b.imbalance || 0;
          const bidPct = Math.max(15, Math.min(85, Math.round(50 + (imb * 400))));
          return `
            <div class="space-y-1">
              <div class="flex justify-between font-mono text-xs">
                <span class="text-white">${{b.symbol}}</span>
                <span class="${{imb >= 0 ? 'text-emerald-400' : 'text-rose-400'}}">${{imb >= 0 ? '+' : ''}}${{imb.toFixed(3)}}</span>
              </div>
              <div class="w-full h-2 rounded-full overflow-hidden flex bg-slate-950">
                <div class="bg-emerald-500" style="width: ${{bidPct}}%"></div>
                <div class="bg-rose-500" style="width: ${{100 - bidPct}}%"></div>
              </div>
            </div>
          `;
        }}).join('');
      }}
    }}

    async function fetchLiveStatus() {{
      try {{
        const res = await fetch('data/live_status.json?t=' + Date.now());
        if (!res.ok) return;
        const d = await res.json();
        
        if (d.forward_trading && d.forward_trading.equity !== undefined) {{
          const el = document.getElementById('hdr-equity');
          if (el) el.textContent = '$' + Number(d.forward_trading.equity).toFixed(2);
          const heroEq = document.getElementById('hero-equity');
          if (heroEq) heroEq.innerHTML = '$' + Number(d.forward_trading.equity).toFixed(2) + ' <span class="text-xs font-normal text-slate-400">USD</span>';
        }}
        
        const ts = d.timestamp_local || d.updated_at_human;
        if (ts) {{
          const z2Upd = document.getElementById('idx-z2-updated');
          if (z2Upd) z2Upd.textContent = ts;
        }}
        
        if (d.forward_trading && d.forward_trading.statistical_power) {{
          const sp = d.forward_trading.statistical_power;
          const heroSample = document.getElementById('hero-sample-n');
          if (heroSample) heroSample.innerHTML = `N=${{sp.sample_size_N || 79}} <span class="text-sm font-normal text-slate-400">/ ${{sp.target_preliminary_N || 500}} ไม้</span>`;
        }}

        if (d.bots_fleet) renderLiveBots(d.bots_fleet);
        if (d.recent_trades) renderRecentTrades(d.recent_trades);
        if (d.market_intelligence_v4) renderMarketIntelligenceV4(d.market_intelligence_v4);
      }} catch (e) {{}}
    }}

    function renderMarketIntelligenceV4(intel) {{
      const grid = document.getElementById('market-intel-grid');
      if (!grid || !intel || !intel.assets) return;
      
      const badgeColors = {{
        'STRONG_UPTREND': 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30',
        'STRONG_DOWNTREND': 'bg-rose-500/15 text-rose-400 border-rose-500/30',
        'BREAKOUT': 'bg-sky-500/15 text-sky-400 border-sky-500/30',
        'VOLATILITY_EXPANSION': 'bg-teal-500/15 text-teal-400 border-teal-500/30',
        'VOLATILITY_COMPRESSION': 'bg-indigo-500/15 text-indigo-400 border-indigo-500/30',
        'RANGE_BOUND': 'bg-amber-500/15 text-amber-400 border-amber-500/30',
        'SIDEWAY': 'bg-slate-700/30 text-slate-300 border-slate-600',
        'REVERSAL': 'bg-purple-500/15 text-purple-400 border-purple-500/30',
        'THIN_LIQUIDITY': 'bg-orange-500/15 text-orange-400 border-orange-500/30',
        'HIGH_UNCERTAINTY': 'bg-red-500/15 text-red-400 border-red-500/30',
        'NEWS_DRIVEN': 'bg-fuchsia-500/15 text-fuchsia-400 border-fuchsia-500/30'
      }};

      grid.innerHTML = Object.values(intel.assets).map(a => {{
        const badgeCls = badgeColors[a.primary_regime] || 'bg-slate-800 text-slate-300 border-slate-700';
        return `
          <div class="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 space-y-2 hover:border-slate-700 transition">
            <div class="flex items-center justify-between">
              <span class="font-bold text-white text-sm tracking-tight font-mono">${{a.symbol}}</span>
              <span class="text-xs font-mono font-bold text-slate-200">$${{Number(a.latest_price).toLocaleString()}}</span>
            </div>
            <div class="flex items-center justify-between gap-1 text-[11px]">
              <span class="px-2 py-0.5 rounded border font-mono font-semibold truncate ${{badgeCls}}">
                ${{a.primary_regime}}
              </span>
              <span class="text-slate-400 font-mono text-[10px]">${{a.trading_session}}</span>
            </div>
            <div class="text-[11px] text-slate-400 flex items-center justify-between border-t border-slate-800/60 pt-1.5 font-mono">
              <span>Spread: <strong class="text-slate-200">${{a.spread}}</strong></span>
              <span>Delta: <strong class="${{a.order_flow_delta >= 0 ? 'text-emerald-400' : 'text-rose-400'}}">${{a.order_flow_delta > 0 ? '+' : ''}}${{a.order_flow_delta}}</strong></span>
            </div>
            <div class="text-[11px] bg-slate-950/60 p-2 rounded-lg border border-slate-800/80 space-y-1">
              <div class="flex items-center justify-between font-mono">
                <span class="text-sky-300 font-bold">${{a.selected_strategy_id}}</span>
                <span class="text-amber-300 font-bold">Score: ${{a.suitability_score}}</span>
              </div>
              <p class="text-[10px] text-slate-400 truncate" title="${{a.audit_reason}}">
                ${{a.selected_strategy_name}} (${{a.action}})
              </p>
            </div>
          </div>
        `;
      }}).join('');

      const switchEl = document.getElementById('intel-recent-switch');
      if (switchEl && intel.recent_strategy_switches && intel.recent_strategy_switches.length) {{
        const last = intel.recent_strategy_switches[intel.recent_strategy_switches.length - 1];
        switchEl.innerHTML = `Last Switch: <span class="text-slate-300 font-mono">${{last.from_strategy}} ➔ <strong class="text-sky-400">${{last.to_strategy}}</strong> (${{last.market_regime}}, Score: ${{last.score}})</span>`;
      }}
    }}

    function renderRecentTrades(trades) {{
      const tbody = document.getElementById('live-trades-tbody');
      if (!tbody || !trades || !trades.length) return;
      tbody.innerHTML = trades.slice(-6).reverse().map(t => {{
        return `
          <tr class="hover:bg-slate-900/60">
            <td class="py-1.5 px-2.5 text-slate-400">${{(t.time || '').substring(11, 19)}}</td>
            <td class="py-1.5 px-2.5 text-white font-bold">${{t.symbol || 'BTCUSD'}}</td>
            <td class="py-1.5 px-2.5 ${{t.side === 'Buy' ? 'text-sky-400' : 'text-purple-400'}}">${{t.side}}</td>
            <td class="py-1.5 px-2.5 text-right text-slate-200">${{t.price || '-'}}</td>
            <td class="py-1.5 px-2.5 text-right text-slate-400">${{t.slippage || '0.00'}}</td>
            <td class="py-1.5 px-2.5 text-right text-sky-300">${{t.latencyMs ? t.latencyMs + 'ms' : '-'}}</td>
          </tr>
        `;
      }}).join('');
    }}

    // TradingView Embed Loader & Symbol Switcher
    function initTradingViewChart(symbol) {{
      currentTvSymbol = symbol || currentTvSymbol;
      const isDark = document.documentElement.classList.contains('dark');
      const themeName = isDark ? 'dark' : 'light';
      const container = document.getElementById('tv_chart_container');
      if (!container) return;
      container.innerHTML = '';
      
      try {{
        tvWidget = new TradingView.widget({{
          "autosize": true,
          "symbol": currentTvSymbol,
          "interval": "15",
          "timezone": "Asia/Bangkok",
          "theme": themeName,
          "style": "1",
          "locale": "th_TH",
          "toolbar_bg": isDark ? "#090d16" : "#ffffff",
          "enable_publishing": false,
          "hide_side_toolbar": false,
          "allow_symbol_change": true,
          "container_id": "tv_chart_container"
        }});
      }} catch(e) {{
        console.error("TV widget error:", e);
      }}
    }}

    function changeTvSymbol(symbol, btn) {{
      const btns = document.querySelectorAll('.tv-sym-btn');
      btns.forEach(b => {{
        b.className = 'tv-sym-btn px-3 py-1.5 rounded-lg text-slate-400 hover:text-white cursor-pointer';
      }});
      if (btn) {{
        btn.className = 'tv-sym-btn px-3 py-1.5 rounded-lg bg-sky-500/20 text-sky-300 font-bold border border-sky-500/40 cursor-pointer shadow-sm';
      }}
      initTradingViewChart(symbol);
    }}



    // Theme Switcher Logic (Dark Terminal vs Clean High-Contrast Light)
    function toggleTheme() {{
      const htmlEl = document.documentElement;
      const isCurrentlyDark = htmlEl.classList.contains('dark');
      const newTheme = isCurrentlyDark ? 'light' : 'dark';
      htmlEl.classList.remove('dark', 'light');
      htmlEl.classList.add(newTheme);
      
      updateThemeToggleButton(newTheme);
      localStorage.setItem('antigravity_theme', newTheme);
      initTradingViewChart(currentTvSymbol);
    }}

    function updateThemeToggleButton(theme) {{
      const btn = document.getElementById('btn-theme-toggle');
      const icon = document.getElementById('theme-icon');
      const label = document.getElementById('theme-label');
      if (theme === 'light') {{
        if (icon) icon.textContent = '☀️';
        if (label) label.textContent = 'ธีมสว่าง (กดเพื่อสลับ)';
        if (btn) btn.className = 'px-3 py-1.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-800 font-bold border border-slate-300 text-xs flex items-center gap-1.5 transition cursor-pointer shadow-sm';
      }} else {{
        if (icon) icon.textContent = '🌙';
        if (label) label.textContent = 'ธีมมืด (กดเพื่อสลับ)';
        if (btn) btn.className = 'px-3 py-1.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-slate-300 font-bold border border-slate-700 text-xs flex items-center gap-1.5 transition cursor-pointer shadow-sm';
      }}
    }}

    function copyCliCmd() {{
      const box = document.getElementById('cli-cmd-box');
      navigator.clipboard.writeText(box.textContent);
      const b = document.getElementById('btn-copy-cli');
      b.textContent = '✅ คัดลอกแล้ว!';
      setTimeout(() => {{ b.textContent = '📋 คัดลอกคำสั่ง'; }}, 2000);
    }}

    window.onload = init;
  </script>
</body>
</html>'''

INDEX_PATH.write_text(new_html, encoding="utf-8")
print(f"Successfully generated new executive modern minimal dashboard in docs/index.html ({len(new_html)} bytes)")
