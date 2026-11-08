import re
import os

def build_full_update():
    html_path = 'docs/index.html'
    with open(html_path, 'r', encoding='utf-8') as f:
        html = f.read()

    # 1. Update <html> tag to class="light"
    html = re.sub(r'<html lang="th"[^>]*>', '<html lang="th" class="light">', html)

    # 2. Add Light Theme CSS and Theme Toggle Script in <style>
    light_theme_css = """
    /* ========================================================================= */
    /* INSTITUTIONAL WHITE / LIGHT THEME STYLES (ธีมสีขาวมาตรฐานสถาบัน)          */
    /* ========================================================================= */
    html.light body {
      background-color: #f8fafc !important;
      color: #1e293b !important;
    }
    html.light .bg-grid {
      background-image: radial-gradient(rgba(148, 163, 184, 0.22) 1px, transparent 1px) !important;
      background-size: 20px 20px !important;
    }
    html.light header {
      background-color: rgba(255, 255, 255, 0.95) !important;
      border-color: #e2e8f0 !important;
      box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05) !important;
    }
    html.light .card {
      background: #ffffff !important;
      border: 1px solid #e2e8f0 !important;
      border-radius: 20px !important;
      box-shadow: 0 4px 20px -2px rgba(15, 23, 42, 0.05) !important;
      color: #1e293b !important;
    }
    html.light .card:hover {
      border-color: #cbd5e1 !important;
      box-shadow: 0 10px 25px -3px rgba(15, 23, 42, 0.08) !important;
    }
    html.light .bg-slate-950,
    html.light .bg-slate-950\\/80,
    html.light .bg-slate-950\\/90,
    html.light .bg-slate-900,
    html.light .bg-slate-900\\/80,
    html.light .bg-slate-900\\/90,
    html.light .bg-slate-900\\/70,
    html.light .bg-slate-900\\/60,
    html.light .bg-black\\/60 {
      background-color: #ffffff !important;
    }
    html.light .bg-slate-950\\/50,
    html.light .bg-slate-900\\/40,
    html.light .bg-slate-900\\/50 {
      background-color: #f8fafc !important;
    }
    html.light .border-slate-800,
    html.light .border-slate-800\\/80,
    html.light .border-slate-800\\/90,
    html.light .border-slate-700 {
      border-color: #e2e8f0 !important;
    }
    html.light .text-white {
      color: #0f172a !important;
    }
    html.light .text-slate-100,
    html.light .text-slate-200,
    html.light .text-slate-300 {
      color: #334155 !important;
    }
    html.light .text-slate-400 {
      color: #64748b !important;
    }
    html.light .text-slate-500 {
      color: #94a3b8 !important;
    }
    html.light .pillar-tab {
      background-color: #ffffff !important;
      border-color: #e2e8f0 !important;
      color: #475569 !important;
    }
    html.light .pillar-tab:hover {
      background-color: #f1f5f9 !important;
      color: #0f172a !important;
    }
    html.light .pillar-tab.active-tab {
      background: linear-gradient(135deg, rgba(6, 182, 212, 0.15), rgba(16, 185, 129, 0.15)) !important;
      border-color: #0284c7 !important;
      box-shadow: 0 0 16px rgba(2, 132, 199, 0.2) !important;
      color: #0369a1 !important;
      font-weight: 700 !important;
    }
    html.light #four-pillars-ensemble-card {
      background: linear-gradient(135deg, #ffffff, #f0fdf4) !important;
      border-color: #86efac !important;
    }
    html.light #strategy-foundry-card {
      background: linear-gradient(135deg, #ffffff, #fffbeb) !important;
      border-color: #fde68a !important;
    }
    html.light #flywheel-learnings-card {
      background: linear-gradient(135deg, #ffffff, #eef2ff) !important;
      border-color: #c7d2fe !important;
    }
    html.light #flywheel-summary-card {
      background: linear-gradient(135deg, #ffffff, #f0f9ff) !important;
      border-color: #bae6fd !important;
    }
    html.light #tradingview-studio-card {
      background: #ffffff !important;
      border-color: #e2e8f0 !important;
    }
    html.light table thead {
      background-color: #f1f5f9 !important;
      color: #475569 !important;
    }
    html.light table tbody tr:hover {
      background-color: #f8fafc !important;
    }
  </style>"""

    if "/* INSTITUTIONAL WHITE / LIGHT THEME STYLES" not in html:
        html = html.replace('</style>', light_theme_css)

    # 3. Add Theme Toggle Button in Header (near Emergency Kill Switch)
    theme_btn_html = """
        <!-- Theme Switcher Toggle (White / Dark) -->
        <button id="btn-theme-toggle" onclick="toggleTheme()" class="px-2.5 py-1.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold border border-slate-300 text-xs flex items-center gap-1.5 transition cursor-pointer shadow-sm" title="สลับระหว่างธีมสีขาว (White) และธีมมืด (Dark)">
          <span id="theme-icon">☀️</span> <span id="theme-label" class="hidden sm:inline">ธีมสีขาว</span>
        </button>
    """
    if 'id="btn-theme-toggle"' not in html:
        html = html.replace('<button id="btn-kill-switch"', theme_btn_html + '\n        <button id="btn-kill-switch"')

    # 4. Insert TradingView Live Studio Card right before flywheel-summary-card
    tradingview_studio_card = """
    <!-- ======================================================================= -->
    <!-- TRADINGVIEW LIVE CHART & MICROSTRUCTURE STUDIO (สตูดิโอกราฟสด TradingView)-->
    <!-- ======================================================================= -->
    <div id="tradingview-studio-card" class="card p-5 sm:p-6 space-y-4 border border-sky-300 shadow-xl bg-white rounded-2xl">
      <div class="flex flex-col lg:flex-row lg:items-center justify-between gap-3 border-b border-slate-200 pb-3">
        <div class="flex items-center gap-3">
          <div class="w-11 h-11 rounded-2xl bg-sky-100 border border-sky-300 flex items-center justify-center text-2xl shadow-sm">
            📈
          </div>
          <div>
            <div class="flex flex-wrap items-center gap-2">
              <h2 class="text-base sm:text-lg font-black text-slate-900">ห้องวิเคราะห์กราฟสดเชิงลึกสไตล์ TradingView (Live Microstructure Studio)</h2>
              <span class="px-2.5 py-0.5 rounded text-[10px] font-mono font-bold bg-sky-100 text-sky-800 border border-sky-300">TRADINGVIEW REAL-TIME · LIGHT THEME</span>
            </div>
            <p class="text-xs text-slate-600 mt-0.5">
              กราฟแท่งเทียนสดระดับสถาบัน: แสดงโครงสร้างราคาจริง, ระดับกำแพงสภาพคล่อง L2 DOM, กรอบ Breakout CHoCH, และเซสชันตลาดเพื่อยืนยันจุดเข้าออเดอร์
            </p>
          </div>
        </div>

        <!-- Symbol Switcher Tabs -->
        <div class="flex items-center gap-1.5 bg-slate-100 p-1.5 rounded-xl border border-slate-200 font-mono text-xs">
          <button onclick="changeTvSymbol('BINANCE:BTCUSDT', this)" class="tv-sym-btn px-3 py-1 rounded-lg bg-white text-sky-700 font-extrabold shadow-sm border border-slate-200 cursor-pointer">
            ₿ BTCUSD (Asia Champion)
          </button>
          <button onclick="changeTvSymbol('BINANCE:ETHUSDT', this)" class="tv-sym-btn px-3 py-1 rounded-lg text-slate-600 hover:text-slate-900 cursor-pointer">
            ⟠ ETHUSD (London Champion)
          </button>
          <button onclick="changeTvSymbol('CAPITALCOM:GOLD', this)" class="tv-sym-btn px-3 py-1 rounded-lg text-slate-600 hover:text-slate-900 cursor-pointer">
            🥇 XAUUSD (NY Fader)
          </button>
        </div>
      </div>

      <!-- TradingView Interactive Embed Widget -->
      <div class="rounded-xl overflow-hidden border border-slate-200 shadow-inner bg-white relative" style="height: 480px;">
        <div id="tv_chart_container" style="height: 100%; width: 100%;"></div>
      </div>

      <!-- Chart Technical Annotation Box (คำอธิบายกราฟประกอบเพื่อความเข้าใจง่าย) -->
      <div class="p-3.5 rounded-xl bg-sky-50 border border-sky-200 text-xs text-slate-700 space-y-1.5 leading-relaxed">
        <div class="font-bold text-sky-900 flex items-center gap-1.5 text-xs">
          <span>💡</span> <span>คำอธิบายโครงสร้างกราฟและตัวอย่างจุดเข้า (Why & How):</span>
        </div>
        <p class="text-[11px] text-slate-600">
          <strong>จุดสังเกตตาม 4 เสาหลัก:</strong> เมื่อราคาวิ่งลงมาชนกำแพงสภาพคล่อง <span class="text-emerald-700 font-bold">L2 DOM Bid Wall (&gt;1.4x)</span> และเกิดไส้เทียนดีดตัว (Absorption Wick) จากนั้นแท่ง M1/M5 ปิดเหนือแนวสวิงเดิมเป็น <span class="text-sky-700 font-bold">Displacement CHoCH</span> ให้รอราคาย่อตัวกลับมา Retest ที่กรอบ <span class="text-amber-700 font-bold">Fibo Golden Zone 50-65%</span> เพื่อเข้า Buy โดยวาง Stop Loss ใต้กำแพง 15 pips และตั้งเป้า Take Profit ที่จุดดูดซับสภาพคล่องฝั่งตรงข้าม (Smart DOM Exit)
        </p>
      </div>
    </div>
    """

    if 'id="tradingview-studio-card"' not in html:
        html = html.replace('<div id="flywheel-summary-card"', tradingview_studio_card + '\n\n    <div id="flywheel-summary-card"')

    # 5. Inject SVG Charts into Step 1, 2, 3, 4 of Flywheel Cards
    import sys
    sys.path.insert(0, '.')
    from tools.test_svg_definitions import get_svg_step1, get_svg_step2, get_svg_step3, get_svg_step4

    svg1 = get_svg_step1()
    svg2 = get_svg_step2()
    svg3 = get_svg_step3()
    svg4 = get_svg_step4()

    # Step 1
    old_step1_target = '<p id="fw-step1-desc"'
    if 'id="svg-step1-chart"' not in html:
        html = html.replace(old_step1_target, f'<div id="svg-step1-chart">{svg1}</div>\n          <p id="fw-step1-desc"')

    # Step 2
    old_step2_target = '<p id="fw-step2-desc"'
    if 'id="svg-step2-chart"' not in html:
        html = html.replace(old_step2_target, f'<div id="svg-step2-chart">{svg2}</div>\n          <p id="fw-step2-desc"')

    # Step 3
    old_step3_target = '<p id="fw-step3-desc"'
    if 'id="svg-step3-chart"' not in html:
        html = html.replace(old_step3_target, f'<div id="svg-step3-chart">{svg3}</div>\n          <p id="fw-step3-desc"')

    # Step 4
    old_step4_target = '<p id="fw-step4-desc"'
    if 'id="svg-step4-chart"' not in html:
        html = html.replace(old_step4_target, f'<div id="svg-step4-chart">{svg4}</div>\n          <p id="fw-step4-desc"')

    # 6. Add TradingView widget loader script & Theme Toggle Script at end of body
    tv_script = """
  <!-- TradingView tv.js script -->
  <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
  <script type="text/javascript">
    let tvWidget = null;
    let currentTvSymbol = 'BINANCE:BTCUSDT';

    function initTradingViewChart(symbol) {
      currentTvSymbol = symbol || currentTvSymbol;
      const isDark = document.documentElement.classList.contains('dark');
      const themeName = isDark ? 'dark' : 'light';
      const container = document.getElementById('tv_chart_container');
      if (!container) return;
      container.innerHTML = '';
      
      try {
        tvWidget = new TradingView.widget({
          "autosize": true,
          "symbol": currentTvSymbol,
          "interval": "15",
          "timezone": "Asia/Bangkok",
          "theme": themeName,
          "style": "1",
          "locale": "th_TH",
          "toolbar_bg": isDark ? "#0f172a" : "#ffffff",
          "enable_publishing": false,
          "hide_side_toolbar": false,
          "allow_symbol_change": true,
          "container_id": "tv_chart_container"
        });
      } catch(e) {
        console.error("TV widget error:", e);
      }
    }

    function changeTvSymbol(symbol, btn) {
      const btns = document.querySelectorAll('.tv-sym-btn');
      btns.forEach(b => {
        b.className = 'tv-sym-btn px-3 py-1 rounded-lg text-slate-600 hover:text-slate-900 cursor-pointer';
      });
      if (btn) {
        btn.className = 'tv-sym-btn px-3 py-1 rounded-lg bg-white text-sky-700 font-extrabold shadow-sm border border-slate-200 cursor-pointer';
      }
      initTradingViewChart(symbol);
    }

    function toggleTheme() {
      const htmlEl = document.documentElement;
      const isCurrentlyDark = htmlEl.classList.contains('dark');
      const newTheme = isCurrentlyDark ? 'light' : 'dark';
      htmlEl.classList.remove('dark', 'light');
      htmlEl.classList.add(newTheme);
      
      const icon = document.getElementById('theme-icon');
      const label = document.getElementById('theme-label');
      if (icon) icon.textContent = newTheme === 'light' ? '☀️' : '🌙';
      if (label) label.textContent = newTheme === 'light' ? 'ธีมสีขาว' : 'ธีมมืด';
      
      localStorage.setItem('antigravity_theme', newTheme);
      initTradingViewChart(currentTvSymbol);
    }

    // Auto load TV on init
    const origInit = window.onload;
    window.onload = function() {
      if (origInit) origInit();
      initTradingViewChart('BINANCE:BTCUSDT');
    };
  </script>
    """

    if 'initTradingViewChart' not in html:
        html = html.replace('</body>', tv_script + '\n</body>')

    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print("Successfully built White Theme and TradingView Chart integrations in docs/index.html!")

if __name__ == '__main__':
    build_full_update()
