# Script to generate rich TradingView-style SVG diagrams for Pillars, Sessions, and Foundry Funnel

def get_svg_pillar1():
    return '''
    <div class="w-full bg-slate-50 border border-slate-200 rounded-lg p-2 mb-2 overflow-hidden shadow-inner">
      <div class="text-[9px] font-mono font-bold text-sky-800 flex justify-between items-center mb-0.5">
        <span>BLUEPRINT 1: STRUCTURAL ANCHOR</span>
        <span class="text-emerald-700">L2 DOM > 1.4x</span>
      </div>
      <svg viewBox="0 0 240 75" class="w-full h-auto text-xs" xmlns="http://www.w3.org/2000/svg">
        <rect x="0" y="0" width="240" height="75" fill="#ffffff" rx="4" stroke="#e2e8f0"/>
        <!-- Value Area 70% Box -->
        <rect x="25" y="15" width="190" height="42" fill="#f0f9ff" stroke="#38bdf8" stroke-dasharray="2,2" stroke-width="1"/>
        <text x="30" y="24" font-size="6.5" font-family="monospace" fill="#0284c7" font-weight="bold">VAH (Value Area High)</text>
        <text x="30" y="52" font-size="6.5" font-family="monospace" fill="#0284c7" font-weight="bold">VAL (Value Area Low)</text>
        
        <!-- L2 DOM Wall Bar at VAL -->
        <rect x="60" y="55" width="140" height="6" fill="#10b981" rx="2"/>
        <text x="130" y="60" font-size="5.5" font-family="monospace" fill="#ffffff" font-weight="extrabold" text-anchor="middle">L2 DOM BID WALL 1.52x</text>
        
        <!-- Candlesticks bouncing off VAL wall -->
        <line x1="80" y1="20" x2="80" y2="38" stroke="#f43f5e" stroke-width="1"/>
        <rect x="77" y="24" width="6" height="10" fill="#f43f5e"/>
        
        <line x1="110" y1="32" x2="110" y2="56" stroke="#f43f5e" stroke-width="1"/>
        <rect x="107" y="38" width="6" height="14" fill="#f43f5e"/>
        
        <!-- Rejection Bounce Candle -->
        <line x1="140" y1="36" x2="140" y2="56" stroke="#059669" stroke-width="1.2"/>
        <rect x="137" y="38" width="6" height="12" fill="#10b981"/>
        
        <!-- Upward Bounce Candle -->
        <line x1="170" y1="22" x2="170" y2="44" stroke="#059669" stroke-width="1.2"/>
        <rect x="167" y="24" width="6" height="16" fill="#059669"/>
        
        <polygon points="140,68 136,73 144,73" fill="#059669"/>
        <text x="148" y="72" font-size="6.5" font-family="monospace" fill="#047857" font-weight="bold">Anchor Bounce</text>
      </svg>
    </div>
    '''

def get_svg_pillar2():
    return '''
    <div class="w-full bg-slate-50 border border-slate-200 rounded-lg p-2 mb-2 overflow-hidden shadow-inner">
      <div class="text-[9px] font-mono font-bold text-amber-800 flex justify-between items-center mb-0.5">
        <span>BLUEPRINT 2: CHOCH CONFIRMATION</span>
        <span class="text-amber-700">Fibo 50-65%</span>
      </div>
      <svg viewBox="0 0 240 75" class="w-full h-auto text-xs" xmlns="http://www.w3.org/2000/svg">
        <rect x="0" y="0" width="240" height="75" fill="#ffffff" rx="4" stroke="#e2e8f0"/>
        
        <!-- Swing High CHoCH Line -->
        <line x1="40" y1="30" x2="160" y2="30" stroke="#f59e0b" stroke-dasharray="2,2" stroke-width="1"/>
        <text x="45" y="26" font-size="6" font-family="monospace" fill="#d97706" font-weight="bold">Swing High Level</text>
        
        <!-- Displacement Candle Breakout -->
        <line x1="110" y1="18" x2="110" y2="52" stroke="#059669" stroke-width="1.2"/>
        <rect x="107" y="22" width="6" height="24" fill="#059669"/>
        <text x="117" y="24" font-size="6.5" font-family="monospace" fill="#047857" font-weight="bold">CHoCH ↑</text>
        
        <!-- Fibo Golden Zone Box (50-65%) -->
        <rect x="130" y="34" width="55" height="12" fill="#fef3c7" stroke="#fde68a" stroke-width="1"/>
        <text x="133" y="42" font-size="5.5" font-family="monospace" fill="#b45309" font-weight="bold">Fibo 50-65%</text>
        
        <!-- Pullback candle into Golden Zone -->
        <line x1="150" y1="32" x2="150" y2="44" stroke="#f59e0b" stroke-width="1"/>
        <rect x="147" y="35" width="6" height="6" fill="#f59e0b"/>
        
        <!-- Confirmed Entry Candle -->
        <line x1="175" y1="14" x2="175" y2="40" stroke="#059669" stroke-width="1.2"/>
        <rect x="172" y="16" width="6" height="20" fill="#059669"/>
        
        <circle cx="150" cy="46" r="3" fill="#059669"/>
        <text x="156" y="52" font-size="6.5" font-family="monospace" fill="#047857" font-weight="extrabold">BUY RETEST</text>
      </svg>
    </div>
    '''

def get_svg_pillar3():
    return '''
    <div class="w-full bg-slate-50 border border-slate-200 rounded-lg p-2 mb-2 overflow-hidden shadow-inner">
      <div class="text-[9px] font-mono font-bold text-rose-800 flex justify-between items-center mb-0.5">
        <span>BLUEPRINT 3: NEWS VOID GATE</span>
        <span class="text-rose-700">Drawdown -82%</span>
      </div>
      <svg viewBox="0 0 240 75" class="w-full h-auto text-xs" xmlns="http://www.w3.org/2000/svg">
        <rect x="0" y="0" width="240" height="75" fill="#ffffff" rx="4" stroke="#e2e8f0"/>
        
        <!-- Timeline track -->
        <line x1="15" y1="35" x2="225" y2="35" stroke="#cbd5e1" stroke-width="1.5"/>
        
        <!-- Normal trading green zone -->
        <rect x="15" y="25" width="55" height="20" fill="#dcfce7" rx="3"/>
        <text x="42" y="38" font-size="6" font-family="monospace" fill="#15803d" font-weight="bold" text-anchor="middle">ACTIVE</text>
        
        <!-- RED NEWS VOID GATE BOX -->
        <rect x="75" y="12" width="90" height="46" fill="#fee2e2" stroke="#ef4444" stroke-dasharray="3,2" rx="4"/>
        <text x="120" y="26" font-size="7" font-family="monospace" fill="#b91c1c" font-weight="extrabold" text-anchor="middle">⛔ NEWS VOID GATE</text>
        <text x="120" y="36" font-size="5.5" font-family="monospace" fill="#dc2626" text-anchor="middle">CPI / NFP / FOMC</text>
        <text x="120" y="46" font-size="5" font-family="monospace" fill="#7f1d1d" text-anchor="middle">-30m to +120m BLACKOUT</text>
        
        <!-- Post news green zone -->
        <rect x="170" y="25" width="55" height="20" fill="#dcfce7" rx="3"/>
        <text x="197" y="38" font-size="6" font-family="monospace" fill="#15803d" font-weight="bold" text-anchor="middle">RESUME</text>
        
        <!-- Spread Shield Meter -->
        <text x="15" y="68" font-size="6.5" font-family="monospace" fill="#475569" font-weight="bold">Spread Shield: <tspan fill="#059669">0.15p ≤ 1.5x (Safe)</tspan></text>
      </svg>
    </div>
    '''

def get_svg_pillar4():
    return '''
    <div class="w-full bg-slate-50 border border-slate-200 rounded-lg p-2 mb-2 overflow-hidden shadow-inner">
      <div class="text-[9px] font-mono font-bold text-emerald-800 flex justify-between items-center mb-0.5">
        <span>BLUEPRINT 4: EXIT & KELLY SIZING</span>
        <span class="text-emerald-700">R:R ≥ 1:2.5</span>
      </div>
      <svg viewBox="0 0 240 75" class="w-full h-auto text-xs" xmlns="http://www.w3.org/2000/svg">
        <rect x="0" y="0" width="240" height="75" fill="#ffffff" rx="4" stroke="#e2e8f0"/>
        
        <!-- Target Line TP (Top) -->
        <line x1="30" y1="18" x2="220" y2="18" stroke="#059669" stroke-width="1.5"/>
        <text x="35" y="14" font-size="6.5" font-family="monospace" fill="#047857" font-weight="bold">Smart DOM TP +$15.81 (R:R 2.5R)</text>
        
        <!-- Breakeven Line -->
        <line x1="80" y1="36" x2="220" y2="36" stroke="#0284c7" stroke-dasharray="2,2" stroke-width="1"/>
        <text x="85" y="32" font-size="6" font-family="monospace" fill="#0369a1" font-weight="bold">1.0R Lock: Move SL to Breakeven</text>
        
        <!-- Entry Line -->
        <line x1="30" y1="46" x2="220" y2="46" stroke="#64748b" stroke-width="1"/>
        <circle cx="50" cy="46" r="3" fill="#0284c7"/>
        <text x="56" y="49" font-size="6.5" font-family="monospace" fill="#334155" font-weight="bold">Entry Point (0.01 Lot)</text>
        
        <!-- Structural SL Line (Bottom) -->
        <line x1="30" y1="62" x2="220" y2="62" stroke="#e11d48" stroke-width="1.5"/>
        <text x="35" y="70" font-size="6.5" font-family="monospace" fill="#be123c" font-weight="bold">Structural SL: 15 pips (-$3.30 Max)</text>
      </svg>
    </div>
    '''

def get_svg_foundry_funnel():
    return '''
    <div class="w-full bg-slate-50 border border-slate-200 rounded-xl p-3 mb-2 overflow-hidden shadow-inner">
      <div class="flex items-center justify-between text-[11px] font-mono mb-1 text-slate-700">
        <span class="font-bold">🏭 แผนผังกระบวนการคัดกรอง 5 ชั้น (Quantitative Sieve Funnel)</span>
        <span class="px-2 py-0.5 rounded bg-rose-100 text-rose-800 font-bold border border-rose-300">Rejection Rate: 98.0%</span>
      </div>
      <svg viewBox="0 0 520 80" class="w-full h-auto text-xs" xmlns="http://www.w3.org/2000/svg">
        <rect x="0" y="0" width="520" height="80" fill="#ffffff" rx="6" stroke="#e2e8f0"/>
        
        <!-- Funnel Step 1 -->
        <polygon points="15,10 115,10 100,70 30,70" fill="#f0f9ff" stroke="#38bdf8" stroke-width="1"/>
        <text x="65" y="28" font-size="8" font-family="monospace" fill="#0369a1" font-weight="bold" text-anchor="middle">1. สร้างไอเดีย</text>
        <text x="65" y="44" font-size="11" font-family="monospace" fill="#0f172a" font-weight="black" text-anchor="middle">1,420 ชุด</text>
        <text x="65" y="60" font-size="6.5" font-family="monospace" fill="#64748b" text-anchor="middle">AI + Papers</text>
        
        <!-- Funnel Arrow 1 -->
        <polygon points="120,40 128,40 128,36 135,40 128,44 128,40" fill="#94a3b8"/>
        
        <!-- Funnel Step 2 -->
        <polygon points="140,10 230,10 215,70 155,70" fill="#fff1f2" stroke="#f43f5e" stroke-width="1"/>
        <text x="185" y="28" font-size="8" font-family="monospace" fill="#be123c" font-weight="bold" text-anchor="middle">2. สุสานคัดทิ้ง</text>
        <text x="185" y="44" font-size="11" font-family="monospace" fill="#e11d48" font-weight="black" text-anchor="middle">1,392 ชุด</text>
        <text x="185" y="60" font-size="6.5" font-family="monospace" fill="#9f1239" text-anchor="middle">98.0% Rejection</text>
        
        <!-- Funnel Arrow 2 -->
        <polygon points="235,40 243,40 243,36 250,40 243,44 243,40" fill="#94a3b8"/>
        
        <!-- Funnel Step 3 -->
        <polygon points="255,10 335,10 325,70 265,70" fill="#f0fdf4" stroke="#4ade80" stroke-width="1"/>
        <text x="295" y="28" font-size="8" font-family="monospace" fill="#15803d" font-weight="bold" text-anchor="middle">3. รอดสู่ Sandbox</text>
        <text x="295" y="44" font-size="11" font-family="monospace" fill="#059669" font-weight="black" text-anchor="middle">28 ชุด (2%)</text>
        <text x="295" y="60" font-size="6.5" font-family="monospace" fill="#166534" text-anchor="middle">ผ่าน 5 ด่านตรวจ</text>
        
        <!-- Funnel Arrow 3 -->
        <polygon points="340,40 348,40 348,36 355,40 348,44 348,40" fill="#94a3b8"/>
        
        <!-- Funnel Step 4 -->
        <polygon points="360,10 435,10 425,70 370,70" fill="#f0fdfa" stroke="#2dd4bf" stroke-width="1.5"/>
        <text x="397" y="28" font-size="8" font-family="monospace" fill="#0f766e" font-weight="bold" text-anchor="middle">4. เทรดสด 0.01L</text>
        <text x="397" y="44" font-size="11" font-family="monospace" fill="#0d9488" font-weight="black" text-anchor="middle">3 บอท</text>
        <text x="397" y="60" font-size="6.5" font-family="monospace" fill="#115e59" text-anchor="middle">BTC, ETH, XAU</text>
        
        <!-- Funnel Arrow 4 -->
        <polygon points="440,40 448,40 448,36 455,40 448,44 448,40" fill="#94a3b8"/>
        
        <!-- Funnel Step 5 -->
        <polygon points="460,10 510,10 500,70 470,70" fill="#faf5ff" stroke="#c084fc" stroke-width="1"/>
        <text x="485" y="28" font-size="7.5" font-family="monospace" fill="#7e22ce" font-weight="bold" text-anchor="middle">5. ปลดออก</text>
        <text x="485" y="44" font-size="10" font-family="monospace" fill="#9333ea" font-weight="black" text-anchor="middle">25 บอท</text>
        <text x="485" y="60" font-size="6" font-family="monospace" fill="#6b21a8" text-anchor="middle">Auto-Retire</text>
      </svg>
    </div>
    '''

def inject_all():
    html_path = 'docs/index.html'
    with open(html_path, 'r', encoding='utf-8') as f:
        html = f.read()

    # 1. Inject Funnel into Strategy Foundry
    foundry_target = '<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3 font-mono text-xs">'
    if 'id="svg-foundry-funnel"' not in html:
        html = html.replace(foundry_target, f'<div id="svg-foundry-funnel">{get_svg_foundry_funnel()}</div>\n      {foundry_target}')

    # 2. Inject Pillar Blueprints into Pillar 1, 2, 3, 4
    p1_target = '<div class="text-sm font-bold text-white">จุดได้เปรียบเชิงโครงสร้าง</div>'
    if 'id="svg-pillar1-blueprint"' not in html:
        html = html.replace(p1_target, f'<div id="svg-pillar1-blueprint">{get_svg_pillar1()}</div>\n            {p1_target}')

    p2_target = '<div class="text-sm font-bold text-white">ยืนยันด้วย CHoCH &amp; Flow</div>'
    if 'id="svg-pillar2-blueprint"' not in html:
        html = html.replace(p2_target, f'<div id="svg-pillar2-blueprint">{get_svg_pillar2()}</div>\n            {p2_target}')

    p3_target = '<div class="text-sm font-bold text-white">ปราการกั้นข่าว &amp; สเปรด</div>'
    if 'id="svg-pillar3-blueprint"' not in html:
        html = html.replace(p3_target, f'<div id="svg-pillar3-blueprint">{get_svg_pillar3()}</div>\n            {p3_target}')

    p4_target = '<div class="text-sm font-bold text-white">ออกตามสมดุล &amp; คุมเสี่ยง Kelly</div>'
    if 'id="svg-pillar4-blueprint"' not in html:
        html = html.replace(p4_target, f'<div id="svg-pillar4-blueprint">{get_svg_pillar4()}</div>\n            {p4_target}')

    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print("Successfully injected all visual blueprints into docs/index.html!")

if __name__ == '__main__':
    inject_all()
