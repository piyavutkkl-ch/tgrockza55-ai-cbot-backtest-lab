# Test and build visual SVG charts for index.html

def get_svg_step1():
    """Level 2 DOM Order Book Depth Chart (25 Layers)"""
    return '''
    <div class="w-full bg-slate-50 border border-slate-200 rounded-xl p-2.5 mb-2 overflow-hidden shadow-inner">
      <div class="flex items-center justify-between text-[10px] font-mono mb-1 text-slate-600">
        <span class="font-bold flex items-center gap-1">📊 <span class="text-slate-800">Order Book L2 Depth (25 Layers)</span></span>
        <span class="px-1.5 py-0.5 rounded bg-emerald-100 text-emerald-800 font-bold border border-emerald-300">Spread: 0.15 pips</span>
      </div>
      <svg viewBox="0 0 380 95" class="w-full h-auto text-xs" xmlns="http://www.w3.org/2000/svg">
        <!-- Background Grid -->
        <rect x="0" y="0" width="380" height="95" fill="#ffffff" rx="6" stroke="#e2e8f0"/>
        
        <!-- Center Spread Divider -->
        <line x1="190" y1="5" x2="190" y2="90" stroke="#cbd5e1" stroke-dasharray="3,3" stroke-width="1.5"/>
        <text x="190" y="16" font-size="8" font-family="monospace" fill="#64748b" text-anchor="middle" font-weight="bold">MID $68,420.50</text>
        
        <!-- BID DEPTH BARS (Left - Green) -->
        <text x="10" y="16" font-size="8" font-family="monospace" fill="#059669" font-weight="bold">← BIDS (Buyer Wall)</text>
        <rect x="70" y="22" width="115" height="8" fill="#10b981" rx="2" opacity="0.85"/>
        <rect x="95" y="33" width="90" height="8" fill="#10b981" rx="2" opacity="0.75"/>
        <rect x="50" y="44" width="135" height="8" fill="#059669" rx="2" opacity="0.95"/> <!-- Huge Wall 1.4x -->
        <rect x="110" y="55" width="75" height="8" fill="#10b981" rx="2" opacity="0.65"/>
        <rect x="80" y="66" width="105" height="8" fill="#10b981" rx="2" opacity="0.80"/>
        <rect x="60" y="77" width="125" height="8" fill="#059669" rx="2" opacity="0.90"/>
        
        <text x="45" y="50" font-size="7" font-family="monospace" fill="#047857" font-weight="extrabold">WALL 1.48x</text>
        
        <!-- ASK DEPTH BARS (Right - Red) -->
        <text x="370" y="16" font-size="8" font-family="monospace" fill="#e11d48" font-weight="bold" text-anchor="end">ASKS (Seller Wall) →</text>
        <rect x="195" y="22" width="90" height="8" fill="#f43f5e" rx="2" opacity="0.75"/>
        <rect x="195" y="33" width="120" height="8" fill="#e11d48" rx="2" opacity="0.85"/>
        <rect x="195" y="44" width="70" height="8" fill="#f43f5e" rx="2" opacity="0.65"/>
        <rect x="195" y="55" width="130" height="8" fill="#be123c" rx="2" opacity="0.95"/> <!-- Ask Wall -->
        <rect x="195" y="66" width="85" height="8" fill="#f43f5e" rx="2" opacity="0.70"/>
        <rect x="195" y="77" width="100" height="8" fill="#f43f5e" rx="2" opacity="0.80"/>
        
        <text x="330" y="61" font-size="7" font-family="monospace" fill="#9f1239" font-weight="extrabold">WALL 1.42x</text>
      </svg>
    </div>
    '''

def get_svg_step2():
    """TradingView-Style Candlestick DOM Absorption & CHoCH Entry Chart"""
    return '''
    <div class="w-full bg-slate-50 border border-slate-200 rounded-xl p-2.5 mb-2 overflow-hidden shadow-inner">
      <div class="flex items-center justify-between text-[10px] font-mono mb-1 text-slate-600">
        <span class="font-bold flex items-center gap-1">📈 <span class="text-slate-800">DOM Absorption & CHoCH Entry</span></span>
        <span class="px-1.5 py-0.5 rounded bg-blue-100 text-blue-800 font-bold border border-blue-300">Win Rate: 59.1%</span>
      </div>
      <svg viewBox="0 0 380 95" class="w-full h-auto text-xs" xmlns="http://www.w3.org/2000/svg">
        <rect x="0" y="0" width="380" height="95" fill="#ffffff" rx="6" stroke="#e2e8f0"/>
        
        <!-- Green Liquidity Absorption Zone -->
        <rect x="40" y="65" width="220" height="22" fill="#dcfce7" rx="3" stroke="#86efac" stroke-dasharray="2,2"/>
        <text x="45" y="80" font-size="7.5" font-family="monospace" fill="#15803d" font-weight="bold">L2 DOM Absorption Wall ($68,380)</text>
        
        <!-- Candlesticks Downward Sweep -->
        <!-- Candle 1 Red -->
        <line x1="60" y1="20" x2="60" y2="48" stroke="#f43f5e" stroke-width="1.2"/>
        <rect x="56" y="25" width="8" height="18" fill="#f43f5e" rx="1"/>
        
        <!-- Candle 2 Red -->
        <line x1="85" y1="35" x2="85" y2="62" stroke="#f43f5e" stroke-width="1.2"/>
        <rect x="81" y="40" width="8" height="18" fill="#f43f5e" rx="1"/>
        
        <!-- Candle 3 Absorption Wick Rejection -->
        <line x1="110" y1="48" x2="110" y2="78" stroke="#059669" stroke-width="1.2"/>
        <rect x="106" y="52" width="8" height="10" fill="#10b981" rx="1"/>
        <circle cx="110" cy="78" r="3" fill="#059669"/>
        <text x="117" y="86" font-size="7" font-family="monospace" fill="#047857" font-weight="bold">Absorption Wick</text>
        
        <!-- Candle 4 Strong Green Displacement CHoCH -->
        <line x1="140" y1="28" x2="140" y2="60" stroke="#059669" stroke-width="1.2"/>
        <rect x="136" y="32" width="8" height="24" fill="#059669" rx="1"/>
        
        <!-- CHoCH Breakout Line -->
        <line x1="75" y1="38" x2="180" y2="38" stroke="#3b82f6" stroke-dasharray="3,3" stroke-width="1.2"/>
        <text x="148" y="34" font-size="7.5" font-family="monospace" fill="#1d4ed8" font-weight="bold">CHoCH Breakout ↑</text>
        
        <!-- Candle 5 Retest Golden Zone -->
        <line x1="170" y1="40" x2="170" y2="56" stroke="#f59e0b" stroke-width="1.2"/>
        <rect x="166" y="43" width="8" height="8" fill="#f59e0b" rx="1"/>
        
        <!-- Candle 6 Rocket Long Entry -->
        <line x1="200" y1="12" x2="200" y2="48" stroke="#059669" stroke-width="1.2"/>
        <rect x="196" y="16" width="8" height="28" fill="#059669" rx="1"/>
        
        <!-- Entry Marker Arrow -->
        <polygon points="170,68 165,76 175,76" fill="#059669"/>
        <text x="180" y="74" font-size="8" font-family="monospace" fill="#047857" font-weight="extrabold">BUY ENTRY @ 50-65% Retest</text>
        
        <!-- SL & TP Target lines -->
        <line x1="195" y1="14" x2="360" y2="14" stroke="#10b981" stroke-width="1.5"/>
        <text x="360" y="12" font-size="7.5" font-family="monospace" fill="#059669" font-weight="bold" text-anchor="end">Smart DOM TP +$15.81</text>
        
        <line x1="160" y1="88" x2="360" y2="88" stroke="#e11d48" stroke-dasharray="2,2" stroke-width="1.2"/>
        <text x="360" y="86" font-size="7.5" font-family="monospace" fill="#be123c" font-weight="bold" text-anchor="end">Structural SL 15 pips</text>
      </svg>
    </div>
    '''

def get_svg_step3():
    """Cumulative Equity Curve Chart & Daily Win Rate Bar Chart"""
    return '''
    <div class="w-full bg-slate-50 border border-slate-200 rounded-xl p-2.5 mb-2 overflow-hidden shadow-inner">
      <div class="flex items-center justify-between text-[10px] font-mono mb-1 text-slate-600">
        <span class="font-bold flex items-center gap-1">💰 <span class="text-slate-800">7-Day Real Cumulative PnL</span></span>
        <span class="px-1.5 py-0.5 rounded bg-emerald-100 text-emerald-800 font-bold border border-emerald-300">PF 1.90 · 6/7 Days Green</span>
      </div>
      <svg viewBox="0 0 380 95" class="w-full h-auto text-xs" xmlns="http://www.w3.org/2000/svg">
        <rect x="0" y="0" width="380" height="95" fill="#ffffff" rx="6" stroke="#e2e8f0"/>
        
        <!-- Zero Line -->
        <line x1="30" y1="75" x2="370" y2="75" stroke="#cbd5e1" stroke-width="1"/>
        <text x="25" y="78" font-size="7" font-family="monospace" fill="#94a3b8" text-anchor="end">$0</text>
        <text x="25" y="22" font-size="7" font-family="monospace" fill="#059669" text-anchor="end font-weight="bold">+$15.20</text>
        
        <!-- Daily Profit Bars (Bottom) -->
        <!-- Day 1: 05 Oct -$0.18 -->
        <rect x="50" y="75" width="22" height="4" fill="#f43f5e" rx="1"/>
        <text x="61" y="90" font-size="6.5" font-family="monospace" fill="#64748b" text-anchor="middle">5 ต.ค.</text>
        
        <!-- Day 2: 01 Nov +$1.39 -->
        <rect x="90" y="67" width="22" height="8" fill="#10b981" rx="1"/>
        <text x="101" y="90" font-size="6.5" font-family="monospace" fill="#64748b" text-anchor="middle">1 พ.ย.</text>
        
        <!-- Day 3: 02 Nov +$5.47 -->
        <rect x="130" y="45" width="22" height="30" fill="#059669" rx="1"/>
        <text x="141" y="90" font-size="6.5" font-family="monospace" fill="#64748b" text-anchor="middle">2 พ.ย.</text>
        
        <!-- Day 4: 03 Nov +$2.76 -->
        <rect x="170" y="60" width="22" height="15" fill="#10b981" rx="1"/>
        <text x="181" y="90" font-size="6.5" font-family="monospace" fill="#64748b" text-anchor="middle">3 พ.ย.</text>
        
        <!-- Day 5: 05 Nov +$3.49 -->
        <rect x="210" y="56" width="22" height="19" fill="#059669" rx="1"/>
        <text x="221" y="90" font-size="6.5" font-family="monospace" fill="#64748b" text-anchor="middle">5 พ.ย.</text>
        
        <!-- Day 6: 06 Nov +$2.02 -->
        <rect x="250" y="64" width="22" height="11" fill="#10b981" rx="1"/>
        <text x="261" y="90" font-size="6.5" font-family="monospace" fill="#64748b" text-anchor="middle">6 พ.ย.</text>
        
        <!-- Day 7: 07 Nov +$0.26 -->
        <rect x="290" y="73" width="22" height="2" fill="#10b981" rx="1"/>
        <text x="301" y="90" font-size="6.5" font-family="monospace" fill="#64748b" text-anchor="middle">7 พ.ย.</text>
        
        <!-- Cumulative Equity Line (Top) -->
        <polyline points="40,75 61,77 101,70 141,43 181,30 221,18 261,15 301,14 360,14" 
                  fill="none" stroke="#0284c7" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
        
        <!-- Shaded area under equity curve -->
        <polygon points="40,75 61,77 101,70 141,43 181,30 221,18 261,15 301,14 360,14 360,75 40,75" 
                 fill="#38bdf8" opacity="0.12"/>
                 
        <circle cx="360" cy="14" r="3.5" fill="#0284c7" stroke="#ffffff" stroke-width="1.5"/>
        <text x="355" y="27" font-size="7.5" font-family="monospace" fill="#0369a1" font-weight="extrabold" text-anchor="end">+$15.20 USD (85.7% Win)</text>
      </svg>
    </div>
    '''

def get_svg_step4():
    """Flywheel Engine Cycle Progression Diagram"""
    return '''
    <div class="w-full bg-slate-50 border border-slate-200 rounded-xl p-2.5 mb-2 overflow-hidden shadow-inner">
      <div class="flex items-center justify-between text-[10px] font-mono mb-1 text-slate-600">
        <span class="font-bold flex items-center gap-1">🔄 <span class="text-slate-800">10-Stage Evolution Engine Loop</span></span>
        <span class="px-1.5 py-0.5 rounded bg-purple-100 text-purple-800 font-bold border border-purple-300">Cycle #1 ➔ Cycle #2</span>
      </div>
      <svg viewBox="0 0 380 95" class="w-full h-auto text-xs" xmlns="http://www.w3.org/2000/svg">
        <rect x="0" y="0" width="380" height="95" fill="#ffffff" rx="6" stroke="#e2e8f0"/>
        
        <!-- Loop Track -->
        <rect x="30" y="25" width="320" height="48" rx="24" fill="none" stroke="#e2e8f0" stroke-width="3"/>
        <rect x="30" y="25" width="220" height="48" rx="24" fill="none" stroke="#8b5cf6" stroke-width="3" stroke-dasharray="8,4"/>
        
        <!-- Node 1: Cycle #1 Complete -->
        <circle cx="54" cy="49" r="16" fill="#10b981" stroke="#ffffff" stroke-width="2"/>
        <text x="54" y="52" font-size="8" font-family="monospace" fill="#ffffff" font-weight="extrabold" text-anchor="middle">#1</text>
        <text x="54" y="80" font-size="7" font-family="monospace" fill="#059669" font-weight="bold" text-anchor="middle">PF 1.90 Done</text>
        
        <!-- Arrow 1 -->
        <polygon points="105,46 115,49 105,52" fill="#8b5cf6"/>
        
        <!-- Node 2: Archive 122 Legacy -->
        <circle cx="150" cy="49" r="14" fill="#f59e0b" stroke="#ffffff" stroke-width="2"/>
        <text x="150" y="52" font-size="7.5" font-family="monospace" fill="#ffffff" font-weight="bold" text-anchor="middle">ARCH</text>
        <text x="150" y="80" font-size="7" font-family="monospace" fill="#d97706" font-weight="bold" text-anchor="middle">122 Archived</text>
        
        <!-- Arrow 2 -->
        <polygon points="205,46 215,49 205,52" fill="#8b5cf6"/>
        
        <!-- Node 3: 24/7 Watchdog Active -->
        <circle cx="250" cy="49" r="15" fill="#0284c7" stroke="#ffffff" stroke-width="2"/>
        <text x="250" y="52" font-size="7" font-family="monospace" fill="#ffffff" font-weight="bold" text-anchor="middle">WD 24/7</text>
        <text x="250" y="80" font-size="7" font-family="monospace" fill="#0284c7" font-weight="bold" text-anchor="middle">Ingesting Ticks</text>
        
        <!-- Arrow 3 -->
        <polygon points="295,46 305,49 295,52" fill="#8b5cf6"/>
        
        <!-- Node 4: Cycle #2 Running -->
        <circle cx="330" cy="49" r="16" fill="#8b5cf6" stroke="#ffffff" stroke-width="2"/>
        <text x="330" y="52" font-size="8" font-family="monospace" fill="#ffffff" font-weight="extrabold" text-anchor="middle">#2</text>
        <text x="330" y="80" font-size="7" font-family="monospace" fill="#7c3aed" font-weight="bold" text-anchor="middle">RUNNING</text>
      </svg>
    </div>
    '''

print("SVG definitions prepared successfully!")
