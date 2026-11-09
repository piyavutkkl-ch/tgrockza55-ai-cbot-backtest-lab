# Test and build visual SVG charts for index.html

def get_svg_step1():
    """Level 2 DOM Order Book Depth Chart (25 Layers)"""
    return '''
    <div class="w-full bg-slate-900/60 dark:bg-slate-950/80 border border-slate-700/60 dark:border-slate-800 rounded-xl p-3 mb-2 overflow-hidden shadow-sm">
      <div class="flex items-center justify-between text-xs font-mono mb-2 text-slate-300 dark:text-slate-400">
        <span class="font-bold flex items-center gap-1.5 text-slate-100">📊 <span>Order Book L2 Depth (25 Layers)</span></span>
        <span class="px-2 py-0.5 rounded bg-emerald-500/15 text-emerald-400 font-bold border border-emerald-500/30">Spread: 0.15 pips</span>
      </div>
      <svg viewBox="0 0 460 125" class="w-full h-auto" xmlns="http://www.w3.org/2000/svg">
        <rect width="460" height="125" fill="#0b111e" rx="8" stroke="#1e293b"/>
        
        <!-- Center Spread Divider -->
        <line x1="230" y1="10" x2="230" y2="115" stroke="#334155" stroke-dasharray="3,3" stroke-width="1.5"/>
        <text x="230" y="22" font-size="10" font-family="monospace" fill="#94a3b8" text-anchor="middle" font-weight="bold">MID $68,420.50</text>
        
        <!-- BID DEPTH BARS (Left - Green) -->
        <text x="16" y="22" font-size="10" font-family="monospace" fill="#34d399" font-weight="bold">← BIDS (Buyer Wall)</text>
        <rect x="70" y="32" width="150" height="10" fill="#10b981" rx="2" opacity="0.85"/>
        <rect x="110" y="46" width="110" height="10" fill="#10b981" rx="2" opacity="0.75"/>
        <rect x="40" y="60" width="180" height="10" fill="#059669" rx="2" opacity="0.95"/> <!-- Huge Wall 1.48x -->
        <rect x="130" y="74" width="90" height="10" fill="#10b981" rx="2" opacity="0.65"/>
        <rect x="90" y="88" width="130" height="10" fill="#10b981" rx="2" opacity="0.80"/>
        <rect x="60" y="102" width="160" height="10" fill="#059669" rx="2" opacity="0.90"/>
        
        <text x="35" y="68" font-size="9" font-family="monospace" fill="#34d399" font-weight="bold" text-anchor="end">WALL 1.48x</text>
        
        <!-- ASK DEPTH BARS (Right - Red) -->
        <text x="444" y="22" font-size="10" font-family="monospace" fill="#f87171" font-weight="bold" text-anchor="end">ASKS (Seller Wall) →</text>
        <rect x="240" y="32" width="120" height="10" fill="#f43f5e" rx="2" opacity="0.75"/>
        <rect x="240" y="46" width="160" height="10" fill="#e11d48" rx="2" opacity="0.85"/>
        <rect x="240" y="60" width="90" height="10" fill="#f43f5e" rx="2" opacity="0.65"/>
        <rect x="240" y="74" width="175" height="10" fill="#be123c" rx="2" opacity="0.95"/> <!-- Ask Wall 1.42x -->
        <rect x="240" y="88" width="115" height="10" fill="#f43f5e" rx="2" opacity="0.70"/>
        <rect x="240" y="102" width="135" height="10" fill="#f43f5e" rx="2" opacity="0.80"/>
        
        <text x="425" y="82" font-size="9" font-family="monospace" fill="#f87171" font-weight="bold">WALL 1.42x</text>
      </svg>
    </div>
    '''

def get_svg_step2():
    """TradingView-Style Candlestick DOM Absorption & CHoCH Entry Chart"""
    return '''
    <div class="w-full bg-slate-900/60 dark:bg-slate-950/80 border border-slate-700/60 dark:border-slate-800 rounded-xl p-3 mb-2 overflow-hidden shadow-sm">
      <div class="flex items-center justify-between text-xs font-mono mb-2 text-slate-300 dark:text-slate-400">
        <span class="font-bold flex items-center gap-1.5 text-slate-100">📈 <span>DOM Absorption & CHoCH Entry</span></span>
        <span class="px-2 py-0.5 rounded bg-sky-500/15 text-sky-300 font-bold border border-sky-500/30">Win Rate: 59.1%</span>
      </div>
      <svg viewBox="0 0 460 125" class="w-full h-auto" xmlns="http://www.w3.org/2000/svg">
        <rect width="460" height="125" fill="#0b111e" rx="8" stroke="#1e293b"/>
        
        <!-- Liquidity Absorption Zone -->
        <rect x="40" y="85" width="280" height="28" fill="#064e3b" rx="4" stroke="#059669" stroke-dasharray="3,3" opacity="0.6"/>
        <text x="50" y="103" font-size="10" font-family="monospace" fill="#34d399" font-weight="bold">L2 DOM Absorption Wall ($68,380)</text>
        
        <!-- Candlesticks Downward Sweep -->
        <!-- Candle 1 Red -->
        <line x1="75" y1="28" x2="75" y2="65" stroke="#f43f5e" stroke-width="1.5"/>
        <rect x="70" y="34" width="10" height="24" fill="#f43f5e" rx="1"/>
        
        <!-- Candle 2 Red -->
        <line x1="110" y1="46" x2="110" y2="82" stroke="#f43f5e" stroke-width="1.5"/>
        <rect x="105" y="52" width="10" height="24" fill="#f43f5e" rx="1"/>
        
        <!-- Candle 3 Absorption Wick Rejection -->
        <line x1="145" y1="62" x2="145" y2="102" stroke="#10b981" stroke-width="1.5"/>
        <rect x="140" y="68" width="10" height="14" fill="#10b981" rx="1"/>
        <circle cx="145" cy="102" r="3.5" fill="#34d399"/>
        <text x="155" y="112" font-size="9" font-family="monospace" fill="#34d399" font-weight="bold">Absorption Wick</text>
        
        <!-- Candle 4 Strong Green Displacement CHoCH -->
        <line x1="185" y1="36" x2="185" y2="78" stroke="#34d399" stroke-width="1.5"/>
        <rect x="180" y="42" width="10" height="30" fill="#059669" rx="1"/>
        
        <!-- CHoCH Breakout Line -->
        <line x1="95" y1="50" x2="240" y2="50" stroke="#38bdf8" stroke-dasharray="3,3" stroke-width="1.5"/>
        <text x="195" y="44" font-size="9.5" font-family="monospace" fill="#38bdf8" font-weight="bold">CHoCH Breakout ↑</text>
        
        <!-- Candle 5 Retest Golden Zone -->
        <line x1="225" y1="52" x2="225" y2="74" stroke="#fbbf24" stroke-width="1.5"/>
        <rect x="220" y="56" width="10" height="12" fill="#f59e0b" rx="1"/>
        
        <!-- Candle 6 Rocket Long Entry -->
        <line x1="265" y1="18" x2="265" y2="65" stroke="#34d399" stroke-width="1.5"/>
        <rect x="260" y="24" width="10" height="35" fill="#10b981" rx="1"/>
        
        <!-- Entry Marker Arrow -->
        <polygon points="225,90 219,100 231,100" fill="#34d399"/>
        <text x="238" y="98" font-size="10" font-family="monospace" fill="#34d399" font-weight="extrabold">BUY RETEST (50-65%)</text>
        
        <!-- SL & TP Target lines -->
        <line x1="260" y1="20" x2="445" y2="20" stroke="#34d399" stroke-width="1.5"/>
        <text x="445" y="16" font-size="9.5" font-family="monospace" fill="#34d399" font-weight="bold" text-anchor="end">Smart DOM TP +$15.81</text>
        
        <line x1="220" y1="112" x2="445" y2="112" stroke="#f43f5e" stroke-dasharray="3,3" stroke-width="1.5"/>
        <text x="445" y="108" font-size="9.5" font-family="monospace" fill="#f87171" font-weight="bold" text-anchor="end">Structural SL 15 pips</text>
      </svg>
    </div>
    '''

def get_svg_step3():
    """Cumulative Equity Curve Chart & Daily Win Rate Bar Chart"""
    return '''
    <div class="w-full bg-slate-900/60 dark:bg-slate-950/80 border border-slate-700/60 dark:border-slate-800 rounded-xl p-3 mb-2 overflow-hidden shadow-sm">
      <div class="flex items-center justify-between text-xs font-mono mb-2 text-slate-300 dark:text-slate-400">
        <span class="font-bold flex items-center gap-1.5 text-slate-100">💰 <span>7-Day Real Cumulative PnL</span></span>
        <span class="px-2 py-0.5 rounded bg-emerald-500/15 text-emerald-300 font-bold border border-emerald-500/30">PF 1.90 · 6/7 Days Green</span>
      </div>
      <svg viewBox="0 0 460 145" class="w-full h-auto" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <linearGradient id="step3-eq-grad" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stop-color="#0284c7" stop-opacity="0.35"/>
            <stop offset="100%" stop-color="#0284c7" stop-opacity="0.02"/>
          </linearGradient>
        </defs>
        <rect width="460" height="145" fill="#0b111e" rx="8" stroke="#1e293b"/>
        
        <!-- Y Axis Gridlines & Labels -->
        <line x1="45" y1="25" x2="445" y2="25" stroke="#1e293b" stroke-width="1"/>
        <text x="40" y="28" font-size="9" font-family="monospace" fill="#64748b" text-anchor="end">+$15</text>
        
        <line x1="45" y1="58" x2="445" y2="58" stroke="#1e293b" stroke-width="1"/>
        <text x="40" y="61" font-size="9" font-family="monospace" fill="#64748b" text-anchor="end">+$10</text>
        
        <!-- Zero Baseline -->
        <line x1="45" y1="92" x2="445" y2="92" stroke="#334155" stroke-width="1.5"/>
        <text x="40" y="95" font-size="9.5" font-family="monospace" fill="#94a3b8" font-weight="bold" text-anchor="end">$0</text>
        
        <!-- 7 Daily Bars (Baseline y=92) -->
        <!-- Day 1: 05 Oct -$0.18 -->
        <rect x="62" y="92" width="26" height="5" fill="#f43f5e" rx="1.5"/>
        <text x="75" y="108" font-size="8.5" font-family="monospace" fill="#f87171" font-weight="bold" text-anchor="middle">-$0.18</text>
        <text x="75" y="128" font-size="9.5" font-family="monospace" fill="#94a3b8" text-anchor="middle">5 ต.ค.</text>
        
        <!-- Day 2: 01 Nov +$1.39 -->
        <rect x="115" y="80" width="26" height="12" fill="#10b981" rx="2"/>
        <text x="128" y="74" font-size="8.5" font-family="monospace" fill="#34d399" font-weight="bold" text-anchor="middle">+$1.39</text>
        <text x="128" y="128" font-size="9.5" font-family="monospace" fill="#94a3b8" text-anchor="middle">1 พ.ย.</text>
        
        <!-- Day 3: 02 Nov +$5.47 -->
        <rect x="168" y="47" width="26" height="45" fill="#059669" rx="2"/>
        <text x="181" y="41" font-size="8.5" font-family="monospace" fill="#34d399" font-weight="bold" text-anchor="middle">+$5.47</text>
        <text x="181" y="128" font-size="9.5" font-family="monospace" fill="#94a3b8" text-anchor="middle">2 พ.ย.</text>
        
        <!-- Day 4: 03 Nov +$2.76 -->
        <rect x="221" y="68" width="26" height="24" fill="#10b981" rx="2"/>
        <text x="234" y="62" font-size="8.5" font-family="monospace" fill="#34d399" font-weight="bold" text-anchor="middle">+$2.76</text>
        <text x="234" y="128" font-size="9.5" font-family="monospace" fill="#94a3b8" text-anchor="middle">3 พ.ย.</text>
        
        <!-- Day 5: 05 Nov +$3.49 -->
        <rect x="274" y="62" width="26" height="30" fill="#059669" rx="2"/>
        <text x="287" y="56" font-size="8.5" font-family="monospace" fill="#34d399" font-weight="bold" text-anchor="middle">+$3.49</text>
        <text x="287" y="128" font-size="9.5" font-family="monospace" fill="#94a3b8" text-anchor="middle">5 พ.ย.</text>
        
        <!-- Day 6: 06 Nov +$2.02 -->
        <rect x="327" y="74" width="26" height="18" fill="#10b981" rx="2"/>
        <text x="340" y="68" font-size="8.5" font-family="monospace" fill="#34d399" font-weight="bold" text-anchor="middle">+$2.02</text>
        <text x="340" y="128" font-size="9.5" font-family="monospace" fill="#94a3b8" text-anchor="middle">6 พ.ย.</text>
        
        <!-- Day 7: 07 Nov +$0.26 -->
        <rect x="380" y="89" width="26" height="3" fill="#10b981" rx="1.5"/>
        <text x="393" y="84" font-size="8.5" font-family="monospace" fill="#34d399" font-weight="bold" text-anchor="middle">+$0.26</text>
        <text x="393" y="128" font-size="9.5" font-family="monospace" fill="#94a3b8" text-anchor="middle">7 พ.ย.</text>
        
        <!-- Cumulative Equity Line -->
        <polyline points="45,92 75,93 128,84 181,49 234,35 287,23 340,19 393,17 440,17" 
                  fill="none" stroke="#0284c7" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
        
        <!-- Shaded Area Under Equity Curve -->
        <polygon points="45,92 75,93 128,84 181,49 234,35 287,23 340,19 393,17 440,17 440,92 45,92" 
                 fill="url(#step3-eq-grad)"/>
        
        <!-- Endpoint Dot & Badge -->
        <circle cx="393" cy="17" r="4.5" fill="#38bdf8" stroke="#ffffff" stroke-width="2"/>
        <rect x="315" y="4" width="130" height="22" rx="6" fill="#0284c7" opacity="0.95"/>
        <text x="380" y="19" font-size="10.5" font-family="monospace" fill="#ffffff" font-weight="extrabold" text-anchor="middle">+$15.20 USD (85.7%)</text>
      </svg>
    </div>
    '''

def get_svg_step4():
    """Flywheel Engine Cycle Progression Diagram"""
    return '''
    <div class="w-full bg-slate-900/60 dark:bg-slate-950/80 border border-slate-700/60 dark:border-slate-800 rounded-xl p-3 mb-2 overflow-hidden shadow-sm">
      <div class="flex items-center justify-between text-xs font-mono mb-2 text-slate-300 dark:text-slate-400">
        <span class="font-bold flex items-center gap-1.5 text-slate-100">🔄 <span>10-Stage Evolution Engine Loop</span></span>
        <span class="px-2 py-0.5 rounded bg-purple-500/15 text-purple-300 font-bold border border-purple-500/30">Cycle #1 ➔ Cycle #2</span>
      </div>
      <svg viewBox="0 0 460 130" class="w-full h-auto" xmlns="http://www.w3.org/2000/svg">
        <rect width="460" height="130" fill="#0b111e" rx="8" stroke="#1e293b"/>
        
        <!-- Connecting Pipeline Rails (Background) -->
        <line x1="55" y1="58" x2="405" y2="58" stroke="#334155" stroke-width="4" stroke-linecap="round"/>
        <line x1="55" y1="58" x2="290" y2="58" stroke="#10b981" stroke-width="4" stroke-linecap="round"/>
        <line x1="290" y1="58" x2="405" y2="58" stroke="#8b5cf6" stroke-width="4" stroke-dasharray="6,4" stroke-linecap="round"/>
        
        <!-- Directional Flow Chevrons (Centered between nodes) -->
        <polygon points="112,54 120,58 112,62" fill="#10b981"/>
        <polygon points="228,54 236,58 228,62" fill="#10b981"/>
        <polygon points="344,54 352,58 344,62" fill="#8b5cf6"/>
        
        <!-- Top Category Labels (y=20) -->
        <text x="55" y="22" font-size="9.5" font-family="monospace" fill="#34d399" font-weight="bold" text-anchor="middle">CYCLE #1</text>
        <text x="172" y="22" font-size="9.5" font-family="monospace" fill="#fbbf24" font-weight="bold" text-anchor="middle">ARCHIVE</text>
        <text x="290" y="22" font-size="9.5" font-family="monospace" fill="#38bdf8" font-weight="bold" text-anchor="middle">WATCHDOG</text>
        <text x="405" y="22" font-size="9.5" font-family="monospace" fill="#c084fc" font-weight="bold" text-anchor="middle">CYCLE #2</text>
        
        <!-- Node 1: Cycle #1 Complete -->
        <circle cx="55" cy="58" r="21" fill="#10b981" stroke="#ffffff" stroke-width="2.5"/>
        <text x="55" y="63" font-size="13" font-family="monospace" fill="#ffffff" font-weight="900" text-anchor="middle">#1</text>
        <text x="55" y="98" font-size="9.5" font-family="monospace" fill="#34d399" font-weight="bold" text-anchor="middle">PF 1.90 Done</text>
        <text x="55" y="112" font-size="8.5" font-family="system-ui, sans-serif" fill="#94a3b8" text-anchor="middle">78 Trades Validated</text>
        
        <!-- Node 2: Archive 122 Legacy -->
        <circle cx="172" cy="58" r="21" fill="#f59e0b" stroke="#ffffff" stroke-width="2.5"/>
        <text x="172" y="62" font-size="10" font-family="monospace" fill="#ffffff" font-weight="bold" text-anchor="middle">ARCH</text>
        <text x="172" y="98" font-size="9.5" font-family="monospace" fill="#fbbf24" font-weight="bold" text-anchor="middle">122 Archived</text>
        <text x="172" y="112" font-size="8.5" font-family="system-ui, sans-serif" fill="#94a3b8" text-anchor="middle">Clean Reset State</text>
        
        <!-- Node 3: 24/7 Watchdog Active -->
        <circle cx="290" cy="58" r="21" fill="#0284c7" stroke="#ffffff" stroke-width="2.5"/>
        <text x="290" y="62" font-size="10.5" font-family="monospace" fill="#ffffff" font-weight="extrabold" text-anchor="middle">24/7</text>
        <text x="290" y="98" font-size="9.5" font-family="monospace" fill="#38bdf8" font-weight="bold" text-anchor="middle">Live Ingestion</text>
        <text x="290" y="112" font-size="8.5" font-family="system-ui, sans-serif" fill="#94a3b8" text-anchor="middle">Tick &amp; DOM Feeds</text>
        
        <!-- Node 4: Cycle #2 Running -->
        <circle cx="405" cy="58" r="21" fill="#8b5cf6" stroke="#ffffff" stroke-width="2.5"/>
        <text x="405" y="63" font-size="13" font-family="monospace" fill="#ffffff" font-weight="900" text-anchor="middle">#2</text>
        <text x="405" y="98" font-size="9.5" font-family="monospace" fill="#c084fc" font-weight="extrabold" text-anchor="middle">RUNNING</text>
        <text x="405" y="112" font-size="8.5" font-family="system-ui, sans-serif" fill="#94a3b8" text-anchor="middle">Pure Live Flow</text>
      </svg>
    </div>
    '''

print("SVG definitions prepared successfully!")
