import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
COMPACT_DATA_PATH = DOCS / "data" / "terminal_compact.json"
TERMINAL_PATH = DOCS / "terminal.html"

compact_data = COMPACT_DATA_PATH.read_text(encoding="utf-8")

html_content = f'''<!DOCTYPE html>
<html lang="th" class="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>cTrader Automate Terminal · Live Microstructure Trading & Stream Playback</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700;800&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
  <style>
    body {{
      font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
      background-color: #0b0e14;
      color: #e2e8f0;
      user-select: none;
    }}
    .font-mono {{
      font-family: 'JetBrains Mono', monospace;
    }}
    /* cTrader Specific Scrollbars */
    ::-webkit-scrollbar {{
      width: 6px;
      height: 6px;
    }}
    ::-webkit-scrollbar-track {{
      background: #0f131c;
    }}
    ::-webkit-scrollbar-thumb {{
      background: #252c3d;
      border-radius: 3px;
    }}
    ::-webkit-scrollbar-thumb:hover {{
      background: #3b455d;
    }}
    .ctrader-panel {{
      background-color: #121622;
      border: 1px solid #1e2536;
    }}
    .ctrader-header-bg {{
      background-color: #0c0f17;
      border-bottom: 1px solid #1b2130;
    }}
    .ctrader-bid-btn {{
      background: linear-gradient(180deg, #dc2626 0%, #991b1b 100%);
    }}
    .ctrader-bid-btn:hover {{
      background: linear-gradient(180deg, #ef4444 0%, #b91c1c 100%);
    }}
    .ctrader-ask-btn {{
      background: linear-gradient(180deg, #16a34a 0%, #15803d 100%);
    }}
    .ctrader-ask-btn:hover {{
      background: linear-gradient(180deg, #22c55e 0%, #16a34a 100%);
    }}
    .dom-depth-ask {{
      background: linear-gradient(90deg, transparent, rgba(239, 68, 68, 0.18));
    }}
    .dom-depth-bid {{
      background: linear-gradient(90deg, transparent, rgba(34, 197, 94, 0.18));
    }}
  </style>
</head>
<body class="min-h-screen flex flex-col text-xs antialiased overflow-hidden">

  <!-- ========================================================================= -->
  <!-- 1. TOP CTRADER APP HEADER BAR                                            -->
  <!-- ========================================================================= -->
  <header class="ctrader-header-bg px-3 py-1.5 flex items-center justify-between gap-3 shrink-0 z-30">
    <div class="flex items-center gap-3">
      <!-- Back to Foundry Hub -->
      <a href="index.html" class="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-300 border border-slate-800 transition font-medium" title="กลับสู่หน้าแดชบอร์ดหลัก">
        <span>←</span> <span>Hub</span>
      </a>

      <!-- cTrader Branding -->
      <div class="flex items-center gap-2 border-r border-slate-800 pr-3">
        <div class="w-6 h-6 rounded bg-gradient-to-tr from-sky-600 to-indigo-500 flex items-center justify-center font-black text-white text-xs shadow-sm">
          cT
        </div>
        <div>
          <div class="font-extrabold text-white text-xs tracking-wider flex items-center gap-1.5">
            <span>cTrader</span>
            <span class="text-[10px] font-mono font-bold text-sky-400 bg-sky-950 px-1 rounded border border-sky-800">AUTOMATE</span>
          </div>
        </div>
      </div>

      <!-- Simulator Mode Notice -->
      <div class="hidden lg:flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-sky-950/80 border border-sky-500/40 font-mono text-[11px] text-sky-200">
        <span class="text-amber-400">🎮</span>
        <span class="font-bold">โหมดจำลองการเทรด (Interactive Paper Trading Simulator จากชุดข้อมูลบันทึกจริง)</span>
      </div>

      <!-- Asset Tabs -->
      <div class="flex items-center gap-1 bg-[#151a27] p-0.5 rounded-lg border border-slate-800 font-mono">
        <button onclick="switchSymbol('XAUUSD')" id="tab-sym-XAUUSD" class="px-2.5 py-1 rounded font-bold text-xs bg-amber-500/20 text-amber-300 border border-amber-500/40 transition flex items-center gap-1">
          <span>🥇</span> <span>XAUUSD</span>
        </button>
        <button onclick="switchSymbol('BTCUSD')" id="tab-sym-BTCUSD" class="px-2.5 py-1 rounded font-bold text-xs text-slate-400 hover:text-white transition flex items-center gap-1">
          <span>₿</span> <span>BTCUSD</span>
        </button>
        <button onclick="switchSymbol('ETHUSD')" id="tab-sym-ETHUSD" class="px-2.5 py-1 rounded font-bold text-xs text-slate-400 hover:text-white transition flex items-center gap-1">
          <span>⟠</span> <span>ETHUSD</span>
        </button>
      </div>

      <!-- Timeframe Tabs -->
      <div class="flex items-center gap-0.5 bg-[#151a27] p-0.5 rounded-lg border border-slate-800 font-mono">
        <button onclick="setTimeframe('1m')" id="tf-1m" class="px-2 py-0.5 rounded text-[11px] font-bold bg-sky-500/20 text-sky-300 border border-sky-500/40">1m</button>
        <button onclick="setTimeframe('5m')" id="tf-5m" class="px-2 py-0.5 rounded text-[11px] text-slate-400 hover:text-white">5m</button>
        <button onclick="setTimeframe('15m')" id="tf-15m" class="px-2 py-0.5 rounded text-[11px] text-slate-400 hover:text-white">15m</button>
      </div>

      <!-- Indicators Toggles -->
      <div class="hidden xl:flex items-center gap-1.5 font-mono text-[11px]">
        <button onclick="toggleIndicator('vwap')" id="btn-ind-vwap" class="px-2 py-0.5 rounded bg-sky-950 text-cyan-300 border border-cyan-800 font-bold">VWAP</button>
        <button onclick="toggleIndicator('sd')" id="btn-ind-sd" class="px-2 py-0.5 rounded bg-sky-950 text-purple-300 border border-purple-800 font-bold">±SD Bands</button>
        <button onclick="toggleIndicator('vol')" id="btn-ind-vol" class="px-2 py-0.5 rounded bg-slate-900 text-slate-300 border border-slate-700 font-bold">Volume</button>
        <button onclick="toggleIndicator('trades')" id="btn-ind-trades" class="px-2 py-0.5 rounded bg-amber-950 text-amber-300 border border-amber-800 font-bold">Trades</button>
      </div>
    </div>

    <!-- Playback & Stream Status Controls -->
    <div class="flex items-center gap-2 sm:gap-3">
      <!-- Live Recorder Stream Delay Badge -->
      <div class="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-emerald-950/70 border border-emerald-500/40 font-mono text-[11px] text-emerald-300">
        <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
        <span class="font-bold">REC STREAM · DELAY 00:01:00 (1M)</span>
      </div>

      <!-- Countdown to Next Minute Bar -->
      <div class="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-slate-900 border border-slate-800 font-mono text-[11px] text-slate-300">
        <span class="text-amber-400">⏱️</span>
        <span>Next M1:</span>
        <span id="countdown-readout" class="font-bold text-amber-300 tabular-nums">60s</span>
      </div>

      <!-- Speed Selector -->
      <div class="flex items-center gap-0.5 bg-[#151a27] p-0.5 rounded-lg border border-slate-800 font-mono text-[10px]">
        <button onclick="setSpeed(1)" id="spd-1" class="px-1.5 py-0.5 rounded font-bold bg-slate-800 text-white" title="ความเร็วเท่าของจริง (1 บาร์ ทุก 60 วินาที)">1x (60s)</button>
        <button onclick="setSpeed(5)" id="spd-5" class="px-1.5 py-0.5 rounded text-slate-400 hover:text-white" title="เร็ว 5 เท่า (1 บาร์ ทุก 12 วินาที)">5x (12s)</button>
        <button onclick="setSpeed(20)" id="spd-20" class="px-1.5 py-0.5 rounded text-slate-400 hover:text-white" title="เร็ว 20 เท่า (1 บาร์ ทุก 3 วินาที)">20x (3s)</button>
        <button onclick="setSpeed(60)" id="spd-60" class="px-1.5 py-0.5 rounded text-slate-400 hover:text-white" title="เร็ว 60 เท่า (1 บาร์ ทุก 1 วินาที)">60x (1s)</button>
      </div>

      <!-- Play/Pause Toggle -->
      <button onclick="togglePlayback()" id="btn-playback" class="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-white border border-slate-700 font-bold flex items-center gap-1">
        <span id="icon-playback">⏸️</span> <span id="label-playback" class="hidden sm:inline">Pause</span>
      </button>

      <!-- Account Balance -->
      <div class="hidden lg:flex items-center gap-2 px-2.5 py-1 rounded-lg bg-slate-900 border border-slate-800 font-mono">
        <span class="text-slate-400">Balance (Paper):</span>
        <span id="header-balance" class="font-bold text-emerald-400">$10,000.00</span>
      </div>
    </div>
  </header>

  <!-- ========================================================================= -->
  <!-- 2. MAIN TRADING TERMINAL WORKSPACE                                        -->
  <!-- ========================================================================= -->
  <div class="flex-1 flex overflow-hidden relative">

    <!-- Left / Center: Chart Viewport & QuickTrade Bar -->
    <div class="flex-1 flex flex-col overflow-hidden relative">

      <!-- cTrader QuickTrade Floating Ribbon Bar -->
      <div class="bg-[#10141f] border-b border-slate-800 px-3 py-1.5 flex items-center justify-between gap-3 shrink-0 z-20 font-mono text-xs">
        
        <!-- QuickTrade Sell / Buy Widget -->
        <div class="flex items-center gap-2">
          <!-- SELL BUTTON -->
          <button onclick="placeQuickOrder('SELL')" class="ctrader-bid-btn px-4 py-1.5 rounded-lg text-white font-extrabold flex items-center gap-2 shadow-sm active:scale-95 transition cursor-pointer">
            <div class="text-[10px] uppercase font-bold tracking-wider text-rose-200">SELL</div>
            <div id="quick-bid-price" class="text-sm font-black tabular-nums tracking-tight">3895.12</div>
          </button>

          <!-- Middle: Lot Size Input & Spread Display -->
          <div class="flex flex-col items-center justify-center px-2 py-0.5 rounded bg-slate-900 border border-slate-800">
            <div class="flex items-center gap-1">
              <span class="text-[10px] text-slate-400">Lot:</span>
              <input type="number" id="quick-lot-input" value="0.01" step="0.01" min="0.01" max="5.0" class="w-14 bg-transparent text-center font-bold text-white text-xs outline-none">
            </div>
            <div class="text-[9px] text-amber-300 font-bold flex items-center gap-1">
              <span>Spread:</span>
              <span id="quick-spread-pips">0.13</span>
            </div>
          </div>

          <!-- BUY BUTTON -->
          <button onclick="placeQuickOrder('BUY')" class="ctrader-ask-btn px-4 py-1.5 rounded-lg text-white font-extrabold flex items-center gap-2 shadow-sm active:scale-95 transition cursor-pointer">
            <div class="text-[10px] uppercase font-bold tracking-wider text-emerald-200">BUY</div>
            <div id="quick-ask-price" class="text-sm font-black tabular-nums tracking-tight">3895.25</div>
          </button>

          <span class="hidden 2xl:inline-block text-[10px] font-mono text-amber-300/90 px-2 py-0.5 rounded bg-amber-950/40 border border-amber-500/30">
            🎮 โหมดจำลองการเทรด (Interactive Paper Trading Simulator จากชุดข้อมูลบันทึกจริง)
          </span>
        </div>

        <!-- OHLC Tooltip & Metric Strip -->
        <div id="chart-ohlc-strip" class="hidden md:flex items-center gap-3 text-[11px] text-slate-400">
          <span>O: <strong id="val-o" class="text-slate-200">--</strong></span>
          <span>H: <strong id="val-h" class="text-slate-200">--</strong></span>
          <span>L: <strong id="val-l" class="text-slate-200">--</strong></span>
          <span>C: <strong id="val-c" class="text-slate-200">--</strong></span>
          <span>Vol: <strong id="val-vol" class="text-cyan-400">--</strong></span>
          <span>VWAP: <strong id="val-vwap" class="text-cyan-300">--</strong></span>
          <span>Imbalance: <strong id="val-imb" class="text-amber-300">--</strong></span>
        </div>

        <!-- Stream Buffer Indicator -->
        <div class="flex items-center gap-2 text-[11px]">
          <span class="text-slate-400">Stream Buffer:</span>
          <span id="buffer-badge" class="px-2 py-0.5 rounded bg-sky-950 text-sky-300 border border-sky-800 font-bold">200 bars</span>
        </div>
      </div>

      <!-- Canvas Chart Container -->
      <div id="chart-viewport" class="flex-1 relative w-full h-full bg-[#0a0d14] overflow-hidden cursor-crosshair">
        <canvas id="candle-canvas" class="w-full h-full block"></canvas>

        <!-- Floating Tooltip Card -->
        <div id="canvas-tooltip" class="pointer-events-none hidden absolute z-30 p-2.5 rounded-lg bg-slate-950/95 border border-slate-700 font-mono text-[11px] shadow-2xl backdrop-blur-md space-y-1">
          <div id="tt-time" class="font-bold text-sky-400 border-b border-slate-800 pb-1">--</div>
          <div class="grid grid-cols-2 gap-x-3 gap-y-0.5 text-[10px]">
            <span class="text-slate-400">Open:</span> <span id="tt-o" class="text-white text-right">--</span>
            <span class="text-slate-400">High:</span> <span id="tt-h" class="text-emerald-400 text-right">--</span>
            <span class="text-slate-400">Low:</span> <span id="tt-l" class="text-rose-400 text-right">--</span>
            <span class="text-slate-400">Close:</span> <span id="tt-c" class="text-white text-right">--</span>
            <span class="text-slate-400">Ticks:</span> <span id="tt-vol" class="text-cyan-300 text-right">--</span>
            <span class="text-slate-400">VWAP:</span> <span id="tt-vwap" class="text-cyan-400 text-right">--</span>
            <span class="text-slate-400">Imbalance:</span> <span id="tt-imb" class="text-amber-300 text-right">--</span>
          </div>
        </div>

        <!-- Floating Chart Controls (Bottom-Left) -->
        <div class="absolute bottom-3 left-3 z-20 flex items-center gap-1.5 bg-slate-900/90 backdrop-blur p-1 rounded-lg border border-slate-800 font-mono text-xs">
          <button onclick="adjustZoom(1.2)" class="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-white font-bold" title="Zoom In">🔍+</button>
          <button onclick="adjustZoom(0.8)" class="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-white font-bold" title="Zoom Out">🔍-</button>
          <button onclick="resetChartView()" class="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 font-bold" title="Reset Chart to Latest Candle">Auto</button>
        </div>
      </div>

    </div>

    <!-- Right Sidebar: cTrader Depth of Market (DoM) Ladder -->
    <div id="dom-sidebar" class="w-64 ctrader-panel flex flex-col border-l border-slate-800 shrink-0 font-mono text-xs">
      <!-- DoM Header -->
      <div class="p-2.5 border-b border-slate-800 bg-[#0f131d] flex items-center justify-between">
        <span class="font-extrabold text-white flex items-center gap-1.5">
          <span>📊</span> <span>Depth of Market (DoM)</span>
        </span>
        <span class="text-[10px] text-slate-400">L2 (25 Levels)</span>
      </div>

      <!-- Quick Imbalance Ratio Bar -->
      <div class="p-2.5 border-b border-slate-800 space-y-1.5">
        <div class="flex items-center justify-between text-[11px] font-bold">
          <span class="text-emerald-400" id="dom-bid-ratio">Bids 52.4%</span>
          <span class="text-rose-400" id="dom-ask-ratio">47.6% Asks</span>
        </div>
        <div class="w-full h-1.5 rounded-full bg-slate-800 flex overflow-hidden">
          <div id="dom-bar-bids" class="bg-emerald-500 h-full transition-all duration-300" style="width: 52.4%;"></div>
          <div id="dom-bar-asks" class="bg-rose-500 h-full transition-all duration-300" style="width: 47.6%;"></div>
        </div>
      </div>

      <!-- Asks Ladder (Red) -->
      <div class="flex-1 overflow-hidden flex flex-col justify-end p-2 space-y-0.5" id="dom-asks-list">
        <!-- Injected dynamically -->
      </div>

      <!-- Spread Separator -->
      <div class="py-1.5 px-3 bg-slate-900/90 border-y border-slate-800 flex items-center justify-between font-bold text-[11px] text-amber-300">
        <span>SPREAD</span>
        <span id="dom-spread-badge">0.13 USD</span>
      </div>

      <!-- Bids Ladder (Green) -->
      <div class="flex-1 overflow-hidden flex flex-col justify-start p-2 space-y-0.5" id="dom-bids-list">
        <!-- Injected dynamically -->
      </div>

      <!-- Microstructure Stats Footer -->
      <div class="p-2.5 border-t border-slate-800 bg-[#0c1018] text-[10px] space-y-1 text-slate-400">
        <div class="flex justify-between">
          <span>Tick Volume:</span>
          <strong id="dom-tick-vol" class="text-slate-200">346 ticks/m</strong>
        </div>
        <div class="flex justify-between">
          <span>Micro Flow Speed:</span>
          <strong class="text-emerald-400">Continuous 1m Feed</strong>
        </div>
        <div class="flex justify-between">
          <span>Slippage Estimate:</span>
          <strong class="text-sky-300">0.02 pips</strong>
        </div>
      </div>
    </div>

  </div>

  <!-- ========================================================================= -->
  <!-- 3. BOTTOM TERMINAL PANELS: POSITIONS & DEALS HISTORY                      -->
  <!-- ========================================================================= -->
  <div class="h-44 ctrader-panel flex flex-col border-t border-slate-800 shrink-0 font-mono text-xs">
    
    <!-- Tab Strip -->
    <div class="flex items-center justify-between border-b border-slate-800 bg-[#0c1017] px-3 py-1">
      <div class="flex items-center gap-2">
        <button onclick="setBottomTab('positions')" id="tab-btn-positions" class="px-2.5 py-1 rounded font-bold text-sky-400 bg-sky-950/60 border border-sky-800/60 flex items-center gap-1.5">
          <span>💼</span> <span>Positions</span>
          <span id="badge-open-count" class="px-1.5 py-0.2 rounded-full text-[10px] bg-emerald-500/20 text-emerald-300 font-bold">0</span>
        </button>
        <button onclick="setBottomTab('deals')" id="tab-btn-deals" class="px-2.5 py-1 rounded font-medium text-slate-400 hover:text-white flex items-center gap-1.5">
          <span>📜</span> <span>Deals History</span>
          <span id="badge-deals-count" class="px-1.5 py-0.2 rounded-full text-[10px] bg-slate-800 text-slate-300">0</span>
        </button>
        <button onclick="setBottomTab('telemetry')" id="tab-btn-telemetry" class="px-2.5 py-1 rounded font-medium text-slate-400 hover:text-white flex items-center gap-1.5">
          <span>📡</span> <span>Recorder Feed Telemetry</span>
        </button>
      </div>

      <!-- Account Summary Status -->
      <div class="flex items-center gap-4 text-[11px] text-slate-400">
        <span>Balance: <strong id="btm-balance" class="text-slate-200">$10,000.00</strong></span>
        <span>Equity: <strong id="btm-equity" class="text-emerald-400">$10,000.00</strong></span>
        <span>Margin: <strong id="btm-margin" class="text-slate-200">$0.00</strong></span>
        <span>Unrealized PnL: <strong id="btm-pnl" class="text-slate-200">$0.00</strong></span>
      </div>
    </div>

    <!-- Tab Viewport Container -->
    <div class="flex-1 overflow-y-auto">
      
      <!-- Tab 1: Positions Table -->
      <div id="tab-view-positions" class="w-full">
        <table class="w-full text-left text-[11px]">
          <thead class="bg-[#0f131e] text-slate-400 border-b border-slate-800">
            <tr>
              <th class="py-1 px-3">Ticket</th>
              <th class="py-1 px-3">Time</th>
              <th class="py-1 px-3">Symbol</th>
              <th class="py-1 px-3">Direction</th>
              <th class="py-1 px-3 text-right">Volume</th>
              <th class="py-1 px-3 text-right">Entry Price</th>
              <th class="py-1 px-3 text-right">Current Price</th>
              <th class="py-1 px-3 text-right">Net PnL ($)</th>
              <th class="py-1 px-3 text-center">Action</th>
            </tr>
          </thead>
          <tbody id="positions-tbody" class="divide-y divide-slate-800/50">
            <tr>
              <td colspan="9" class="py-6 text-center text-slate-500 font-sans italic">
                ไม่มีออเดอร์ที่เปิดอยู่ · กดปุ่ม SELL หรือ BUY ใน QuickTrade ด้านบนเพื่อเปิดออเดอร์ทดลอง
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Tab 2: Deals History Table -->
      <div id="tab-view-deals" class="hidden w-full">
        <table class="w-full text-left text-[11px]">
          <thead class="bg-[#0f131e] text-slate-400 border-b border-slate-800">
            <tr>
              <th class="py-1 px-3">Ticket</th>
              <th class="py-1 px-3">Timestamp</th>
              <th class="py-1 px-3">Symbol</th>
              <th class="py-1 px-3">Direction</th>
              <th class="py-1 px-3 text-right">Volume</th>
              <th class="py-1 px-3 text-right">Execution Price</th>
              <th class="py-1 px-3 text-right">Spread</th>
              <th class="py-1 px-3 text-right">Realized Net</th>
            </tr>
          </thead>
          <tbody id="deals-tbody" class="divide-y divide-slate-800/50">
            <!-- Injected via JS -->
          </tbody>
        </table>
      </div>

      <!-- Tab 3: Telemetry Stream Details -->
      <div id="tab-view-telemetry" class="hidden p-3 text-slate-300 space-y-2 text-[11px]">
        <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div class="p-2 rounded bg-slate-900 border border-slate-800">
            <div class="text-slate-400 text-[10px]">Dataset Source</div>
            <div class="font-bold text-white mt-0.5">Pepperstone Continuous M1/DOM</div>
          </div>
          <div class="p-2 rounded bg-slate-900 border border-slate-800">
            <div class="text-slate-400 text-[10px]">Playback Delay Policy</div>
            <div class="font-bold text-emerald-400 mt-0.5">Fixed 1-Minute Buffered Stream</div>
          </div>
          <div class="p-2 rounded bg-slate-900 border border-slate-800">
            <div class="text-slate-400 text-[10px]">Tick Fluctuation Engine</div>
            <div class="font-bold text-sky-400 mt-0.5">Sub-Second Bid/Ask Micro-Simulator</div>
          </div>
          <div class="p-2 rounded bg-slate-900 border border-slate-800">
            <div class="text-slate-400 text-[10px]">Streamed Ingested Bars</div>
            <div id="telem-stream-count" class="font-bold text-amber-300 mt-0.5">0 bars</div>
          </div>
        </div>
      </div>

    </div>
  </div>

  <!-- ========================================================================= -->
  <!-- 4. EMBEDDED REAL DATASET & CLIENT SIMULATION ENGINE                       -->
  <!-- ========================================================================= -->
  <script>
    // Embedded Recorded Data
    const RECORDED_DATA = {compact_data};

    // State Variables
    let currentSymbol = 'XAUUSD';
    let currentTimeframe = '1m'; // 1m, 5m, 15m
    let visibleBars = [];
    let streamBuffer = [];
    let executedDeals = [];
    let openPositions = [];
    let accountBalance = 10000.00;
    
    // Playback Engine State
    let isPlaying = true;
    let playbackSpeed = 5; // 1 = 60s, 5 = 12s, 20 = 3s, 60 = 1s
    let countdownSeconds = 60;
    let countdownTimer = null;
    let tickTimer = null;
    let streamedBarsCount = 0;

    // Active Candle Micro-Ticks
    let activeCandle = null;
    let currentBid = 0;
    let currentAsk = 0;
    let currentSpread = 0.12;

    // Indicators Visibility
    const indicators = {{
      vwap: true,
      sd: true,
      vol: true,
      trades: true
    }};

    // Chart Canvas Coordinates & Scaling
    let canvas, ctx;
    let candleWidth = 7;
    let zoomLevel = 1.0;
    let panOffset = 0; // bars shifted from right
    let isDragging = false;
    let dragStartX = 0;
    let hoverMouseX = -1;
    let hoverMouseY = -1;

    // Initialize Terminal
    window.onload = function() {{
      canvas = document.getElementById('candle-canvas');
      ctx = canvas.getContext('2d');

      setupResizeListener();
      setupMouseEvents();
      loadSymbolData(currentSymbol);
      startPlaybackEngine();
    }};

    function setupResizeListener() {{
      const resizeObserver = new ResizeObserver(() => {{
        resizeCanvas();
        drawChart();
      }});
      resizeObserver.observe(document.getElementById('chart-viewport'));
    }}

    function resizeCanvas() {{
      const dpr = window.devicePixelRatio || 1;
      const rect = canvas.getBoundingClientRect();
      canvas.width = rect.width * dpr;
      canvas.height = rect.height * dpr;
      ctx.scale(dpr, dpr);
    }}

    function loadSymbolData(sym) {{
      currentSymbol = sym;
      const data = RECORDED_DATA[sym];
      if (!data) return;

      // Copy initial bars and stream queue
      visibleBars = JSON.parse(JSON.stringify(data.initial));
      streamBuffer = JSON.parse(JSON.stringify(data.stream));
      executedDeals = JSON.parse(JSON.stringify(data.trades || []));

      // Prime active forming candle from stream buffer
      if (streamBuffer.length > 0) {{
        const nextBar = streamBuffer.shift();
        activeCandle = {{
          time: nextBar.time,
          o: nextBar.o,
          h: nextBar.o,
          l: nextBar.o,
          c: nextBar.o,
          targetH: nextBar.h,
          targetL: nextBar.l,
          targetC: nextBar.c,
          v: Math.max(10, Math.floor(nextBar.v * 0.1)),
          targetV: nextBar.v,
          sp: nextBar.sp,
          imb: nextBar.imb,
          vwap: nextBar.vwap,
          sd: nextBar.sd
        }};
        currentBid = activeCandle.c;
        currentSpread = activeCandle.sp;
        currentAsk = parseFloat((currentBid + currentSpread).toFixed(2));
      }}

      countdownSeconds = getBarIntervalSeconds();
      updateHeaderAndDoM();
      renderDealsTable();
      drawChart();
    }}

    function getBarIntervalSeconds() {{
      if (currentTimeframe === '1m') return 60;
      if (currentTimeframe === '5m') return 300;
      if (currentTimeframe === '15m') return 900;
      return 60;
    }}

    // Switch Symbol
    function switchSymbol(sym) {{
      ['XAUUSD', 'BTCUSD', 'ETHUSD'].forEach(s => {{
        const b = document.getElementById('tab-sym-' + s);
        if (s === sym) {{
          b.className = 'px-2.5 py-1 rounded font-bold text-xs bg-amber-500/20 text-amber-300 border border-amber-500/40 transition flex items-center gap-1';
        }} else {{
          b.className = 'px-2.5 py-1 rounded font-bold text-xs text-slate-400 hover:text-white transition flex items-center gap-1';
        }}
      }});
      loadSymbolData(sym);
    }}

    // Switch Timeframe
    function setTimeframe(tf) {{
      currentTimeframe = tf;
      ['1m', '5m', '15m'].forEach(t => {{
        const b = document.getElementById('tf-' + t);
        if (t === tf) {{
          b.className = 'px-2 py-0.5 rounded text-[11px] font-bold bg-sky-500/20 text-sky-300 border border-sky-500/40';
        }} else {{
          b.className = 'px-2 py-0.5 rounded text-[11px] text-slate-400 hover:text-white';
        }}
      }});
      drawChart();
    }}

    // Toggle Indicator
    function toggleIndicator(ind) {{
      indicators[ind] = !indicators[ind];
      const btn = document.getElementById('btn-ind-' + ind);
      if (btn) {{
        if (indicators[ind]) {{
          btn.classList.add('bg-sky-950', 'text-cyan-300', 'border-cyan-800');
          btn.classList.remove('bg-slate-900', 'text-slate-500', 'border-slate-800');
        }} else {{
          btn.classList.remove('bg-sky-950', 'text-cyan-300', 'border-cyan-800');
          btn.classList.add('bg-slate-900', 'text-slate-500', 'border-slate-800');
        }}
      }}
      drawChart();
    }}

    // Playback Engine: Countdown & Continuous Ticking
    function startPlaybackEngine() {{
      if (countdownTimer) clearInterval(countdownTimer);
      if (tickTimer) clearInterval(tickTimer);

      // Countdown ticker (100ms precision)
      countdownTimer = setInterval(() => {{
        if (!isPlaying || !activeCandle) return;

        // Decrease countdown based on speed multiplier
        const step = (0.1 * playbackSpeed);
        countdownSeconds -= step;

        if (countdownSeconds <= 0) {{
          closeActiveCandleAndAdvance();
          countdownSeconds = getBarIntervalSeconds();
        }}

        const rounded = Math.max(0, Math.ceil(countdownSeconds));
        document.getElementById('countdown-readout').textContent = rounded + 's';
      }}, 100);

      // Sub-Second Micro Tick Simulator
      tickTimer = setInterval(() => {{
        if (!isPlaying || !activeCandle) return;
        simulateMicroTick();
      }}, 250);
    }}

    function simulateMicroTick() {{
      if (!activeCandle) return;

      // Realistic random walk pulling towards targetC with volatility
      const dist = (activeCandle.targetC - activeCandle.c);
      const noise = (Math.random() - 0.5) * (currentSpread * 0.8);
      const delta = (dist * 0.08) + noise;

      activeCandle.c = parseFloat((activeCandle.c + delta).toFixed(2));
      if (activeCandle.c > activeCandle.h) activeCandle.h = activeCandle.c;
      if (activeCandle.c < activeCandle.l) activeCandle.l = activeCandle.c;

      activeCandle.v = Math.min(activeCandle.targetV, activeCandle.v + Math.floor(Math.random() * 3 + 1));
      currentBid = activeCandle.c;
      currentAsk = parseFloat((currentBid + currentSpread).toFixed(2));

      updateHeaderAndDoM();
      updateOpenPositionsPnL();
      drawChart();
    }}

    function closeActiveCandleAndAdvance() {{
      if (!activeCandle) return;

      // Finalize active candle to its exact recorded values
      activeCandle.h = Math.max(activeCandle.h, activeCandle.targetH);
      activeCandle.l = Math.min(activeCandle.l, activeCandle.targetL);
      activeCandle.c = activeCandle.targetC;
      activeCandle.v = activeCandle.targetV;

      visibleBars.push({{
        time: activeCandle.time,
        o: activeCandle.o,
        h: activeCandle.h,
        l: activeCandle.l,
        c: activeCandle.c,
        v: activeCandle.v,
        sp: activeCandle.sp,
        imb: activeCandle.imb,
        vwap: activeCandle.vwap,
        sd: activeCandle.sd
      }});

      streamedBarsCount++;
      document.getElementById('telem-stream-count').textContent = streamedBarsCount + ' bars';

      // Load next bar from stream queue
      if (streamBuffer.length > 0) {{
        const nextBar = streamBuffer.shift();
        activeCandle = {{
          time: nextBar.time,
          o: nextBar.o,
          h: nextBar.o,
          l: nextBar.o,
          c: nextBar.o,
          targetH: nextBar.h,
          targetL: nextBar.l,
          targetC: nextBar.c,
          v: Math.max(10, Math.floor(nextBar.v * 0.1)),
          targetV: nextBar.v,
          sp: nextBar.sp,
          imb: nextBar.imb,
          vwap: nextBar.vwap,
          sd: nextBar.sd
        }};
      }} else {{
        // Buffer exhausted: loop back seamlessly from initial dataset
        const data = RECORDED_DATA[currentSymbol];
        streamBuffer = JSON.parse(JSON.stringify(data.stream));
      }}

      document.getElementById('buffer-badge').textContent = streamBuffer.length + ' bars';
      drawChart();
    }}

    function setSpeed(spd) {{
      playbackSpeed = spd;
      [1, 5, 20, 60].forEach(s => {{
        const b = document.getElementById('spd-' + s);
        if (s === spd) {{
          b.className = 'px-1.5 py-0.5 rounded font-bold bg-slate-800 text-white';
        }} else {{
          b.className = 'px-1.5 py-0.5 rounded text-slate-400 hover:text-white';
        }}
      }});
    }}

    function togglePlayback() {{
      isPlaying = !isPlaying;
      document.getElementById('icon-playback').textContent = isPlaying ? '⏸️' : '▶️';
      document.getElementById('label-playback').textContent = isPlaying ? 'Pause' : 'Resume';
    }}

    // QuickTrade Order Placement
    function placeQuickOrder(side) {{
      const lot = parseFloat(document.getElementById('quick-lot-input').value) || 0.01;
      const price = (side === 'BUY') ? currentAsk : currentBid;
      const ticket = Math.floor(Math.random() * 90000000 + 10000000);
      const time = activeCandle ? activeCandle.time : new Date().toLocaleTimeString();

      const pos = {{
        ticket: ticket,
        time: time,
        symbol: currentSymbol,
        side: side,
        lot: lot,
        entryPrice: price,
        currentPrice: price,
        pnl: 0.00
      }};

      openPositions.push(pos);
      updatePositionsTable();
      drawChart();
    }}

    function closePosition(ticket) {{
      const idx = openPositions.findIndex(p => p.ticket === ticket);
      if (idx === -1) return;
      const p = openPositions[idx];
      accountBalance += p.pnl;

      // Add to deals history
      executedDeals.unshift({{
        time: activeCandle ? activeCandle.time : new Date().toLocaleTimeString(),
        id: p.ticket,
        side: p.side,
        units: p.lot,
        price: p.currentPrice,
        spread: currentSpread,
        net: p.pnl
      }});

      openPositions.splice(idx, 1);
      updatePositionsTable();
      renderDealsTable();
      drawChart();
    }}

    function updateOpenPositionsPnL() {{
      let totalPnL = 0;
      openPositions.forEach(p => {{
        const mktPrice = (p.side === 'BUY') ? currentBid : currentAsk;
        p.currentPrice = mktPrice;
        const diff = (p.side === 'BUY') ? (mktPrice - p.entryPrice) : (p.entryPrice - mktPrice);
        
        let multiplier = 100;
        if (currentSymbol === 'BTCUSD') multiplier = 1;
        if (currentSymbol === 'ETHUSD') multiplier = 10;
        
        p.pnl = parseFloat((diff * p.lot * multiplier).toFixed(2));
        totalPnL += p.pnl;
      }});

      const equity = accountBalance + totalPnL;
      document.getElementById('header-balance').textContent = '$' + equity.toFixed(2);
      document.getElementById('btm-equity').textContent = '$' + equity.toFixed(2);
      document.getElementById('btm-pnl').textContent = (totalPnL >= 0 ? '+' : '') + '$' + totalPnL.toFixed(2);
      document.getElementById('btm-pnl').className = totalPnL >= 0 ? 'text-emerald-400 font-bold' : 'text-rose-400 font-bold';

      updatePositionsTable();
    }}

    function updatePositionsTable() {{
      const tbody = document.getElementById('positions-tbody');
      document.getElementById('badge-open-count').textContent = openPositions.length;

      if (openPositions.length === 0) {{
        tbody.innerHTML = `<tr><td colspan="9" class="py-6 text-center text-slate-500 font-sans italic">ไม่มีออเดอร์ที่เปิดอยู่ · กดปุ่ม SELL หรือ BUY ใน QuickTrade ด้านบนเพื่อเปิดออเดอร์ทดลอง</td></tr>`;
        return;
      }}

      tbody.innerHTML = openPositions.map(p => `
        <tr class="hover:bg-slate-900/60 transition">
          <td class="py-1 px-3 text-slate-400">#${{p.ticket}}</td>
          <td class="py-1 px-3 text-slate-300">${{p.time}}</td>
          <td class="py-1 px-3 font-bold text-white">${{p.symbol}}</td>
          <td class="py-1 px-3 font-bold ${{p.side === 'BUY' ? 'text-emerald-400' : 'text-rose-400'}}">${{p.side}}</td>
          <td class="py-1 px-3 text-right">${{p.lot.toFixed(2)}}</td>
          <td class="py-1 px-3 text-right">${{p.entryPrice.toFixed(2)}}</td>
          <td class="py-1 px-3 text-right text-slate-200">${{p.currentPrice.toFixed(2)}}</td>
          <td class="py-1 px-3 text-right font-bold ${{p.pnl >= 0 ? 'text-emerald-400' : 'text-rose-400'}}">${{p.pnl >= 0 ? '+' : ''}}${{p.pnl.toFixed(2)}}</td>
          <td class="py-1 px-3 text-center">
            <button onclick="closePosition(${{p.ticket}})" class="px-2 py-0.5 rounded bg-rose-950/80 hover:bg-rose-900 text-rose-300 border border-rose-700 font-bold transition">Close ✕</button>
          </td>
        </tr>
      `).join('');
    }}

    function renderDealsTable() {{
      const tbody = document.getElementById('deals-tbody');
      document.getElementById('badge-deals-count').textContent = executedDeals.length;

      if (!executedDeals.length) {{
        tbody.innerHTML = `<tr><td colspan="8" class="py-6 text-center text-slate-500 font-sans italic">ยังไม่มีประวัติ Deals</td></tr>`;
        return;
      }}

      tbody.innerHTML = executedDeals.slice(0, 30).map(d => `
        <tr class="hover:bg-slate-900/60 transition">
          <td class="py-1 px-3 text-slate-400">#${{d.id || '--'}}</td>
          <td class="py-1 px-3 text-slate-300">${{d.time}}</td>
          <td class="py-1 px-3 font-bold text-white">${{currentSymbol}}</td>
          <td class="py-1 px-3 font-bold ${{d.side === 'Buy' ? 'text-emerald-400' : 'text-rose-400'}}">${{d.side}}</td>
          <td class="py-1 px-3 text-right">${{parseFloat(d.units || 1).toFixed(2)}}</td>
          <td class="py-1 px-3 text-right text-slate-200">${{parseFloat(d.price).toFixed(2)}}</td>
          <td class="py-1 px-3 text-right text-amber-300">${{parseFloat(d.spread || 0.12).toFixed(2)}}</td>
          <td class="py-1 px-3 text-right font-bold ${{parseFloat(d.net || 0) >= 0 ? 'text-emerald-400' : 'text-rose-400'}}">${{parseFloat(d.net || 0) >= 0 ? '+' : ''}}${{parseFloat(d.net || 0).toFixed(2)}}</td>
        </tr>
      `).join('');
    }}

    function updateHeaderAndDoM() {{
      document.getElementById('quick-bid-price').textContent = currentBid.toFixed(2);
      document.getElementById('quick-ask-price').textContent = currentAsk.toFixed(2);
      document.getElementById('quick-spread-pips').textContent = currentSpread.toFixed(2);
      document.getElementById('dom-spread-badge').textContent = currentSpread.toFixed(2) + ' USD';

      // Update DoM Ladder
      renderDoMLadder();
    }}

    function renderDoMLadder() {{
      const asksContainer = document.getElementById('dom-asks-list');
      const bidsContainer = document.getElementById('dom-bids-list');

      const step = (currentSymbol === 'BTCUSD') ? 5.0 : (currentSymbol === 'ETHUSD' ? 0.5 : 0.25);
      const askRows = [];
      const bidRows = [];

      let totalAskVol = 0;
      let totalBidVol = 0;

      for (let i = 5; i >= 1; i--) {{
        const price = (currentAsk + i * step).toFixed(2);
        const vol = Math.floor(20 + Math.sin(i * 1.5 + currentBid) * 15 + Math.random() * 10);
        totalAskVol += vol;
        askRows.push({{ price, vol }});
      }}

      for (let i = 1; i <= 5; i--) {{
        const price = (currentBid - (5 - i + 1) * step).toFixed(2);
        const vol = Math.floor(22 + Math.cos(i * 1.5 + currentAsk) * 16 + Math.random() * 10);
        totalBidVol += vol;
        bidRows.push({{ price, vol }});
      }}

      const maxVol = Math.max(totalAskVol, totalBidVol, 1);
      const bidPct = ((totalBidVol / (totalBidVol + totalAskVol)) * 100).toFixed(1);
      const askPct = (100 - bidPct).toFixed(1);

      document.getElementById('dom-bid-ratio').textContent = `Bids ${{bidPct}}%`;
      document.getElementById('dom-ask-ratio').textContent = `${{askPct}}% Asks`;
      document.getElementById('dom-bar-bids').style.width = bidPct + '%';
      document.getElementById('dom-bar-asks').style.width = askPct + '%';

      asksContainer.innerHTML = askRows.map(r => `
        <div class="dom-depth-ask flex items-center justify-between px-2 py-0.5 rounded text-[11px] text-rose-300">
          <span class="text-rose-400 font-bold">${{r.price}}</span>
          <span class="text-slate-400 font-mono text-[10px]">${{r.vol}}</span>
        </div>
      `).join('');

      bidsContainer.innerHTML = bidRows.map(r => `
        <div class="dom-depth-bid flex items-center justify-between px-2 py-0.5 rounded text-[11px] text-emerald-300">
          <span class="text-emerald-400 font-bold">${{r.price}}</span>
          <span class="text-slate-400 font-mono text-[10px]">${{r.vol}}</span>
        </div>
      `).join('');
    }}

    // =========================================================================
    // CANVAS CHART RENDERING ENGINE
    // =========================================================================
    function getResampledData() {{
      const allBars = [...visibleBars];
      if (activeCandle) allBars.push(activeCandle);

      if (currentTimeframe === '1m') return allBars;

      const factor = (currentTimeframe === '5m') ? 5 : 15;
      const resampled = [];

      for (let i = 0; i < allBars.length; i += factor) {{
        const chunk = allBars.slice(i, i + factor);
        if (!chunk.length) continue;
        const o = chunk[0].o;
        let h = -Infinity;
        let l = Infinity;
        let v = 0;
        let vwapSum = 0;
        chunk.forEach(b => {{
          if (b.h > h) h = b.h;
          if (b.l < l) l = b.l;
          v += b.v;
          vwapSum += b.vwap;
        }});
        const c = chunk[chunk.length - 1].c;
        resampled.push({{
          time: chunk[chunk.length - 1].time,
          o: o, h: h, l: l, c: c,
          v: v,
          vwap: parseFloat((vwapSum / chunk.length).toFixed(2)),
          sd: chunk[chunk.length - 1].sd,
          imb: chunk[chunk.length - 1].imb,
          sp: chunk[chunk.length - 1].sp
        }});
      }}
      return resampled;
    }}

    function drawChart() {{
      if (!canvas || !ctx) return;

      const rect = canvas.getBoundingClientRect();
      const W = rect.width;
      const H = rect.height;
      ctx.clearRect(0, 0, W, H);

      const priceScaleWidth = 65;
      const timeScaleHeight = 24;
      const chartW = W - priceScaleWidth;
      const chartH = H - timeScaleHeight;

      const data = getResampledData();
      if (!data.length) return;

      // Calculate Visible Window
      const effectiveCandleW = candleWidth * zoomLevel;
      const maxBarsOnScreen = Math.floor(chartW / effectiveCandleW);
      const rightIndex = Math.max(0, data.length - 1 - panOffset);
      const leftIndex = Math.max(0, rightIndex - maxBarsOnScreen + 1);
      const visible = data.slice(leftIndex, rightIndex + 1);

      if (!visible.length) return;

      // Price Extrema
      let minP = Infinity;
      let maxP = -Infinity;
      let maxVol = 0;

      visible.forEach(b => {{
        if (b.l < minP) minP = b.l;
        if (b.h > maxP) maxP = b.h;
        if (b.v > maxVol) maxVol = b.v;
        if (indicators.sd && b.vwap && b.sd) {{
          const highBand = b.vwap + 3.8 * b.sd;
          const lowBand = b.vwap - 3.8 * b.sd;
          if (highBand > maxP) maxP = highBand;
          if (lowBand < minP) minP = lowBand;
        }}
      }});

      // Add 8% vertical padding
      const pad = (maxP - minP) * 0.08 || 1.0;
      maxP += pad;
      minP -= pad;

      const y = (price) => {{
        return chartH - ((price - minP) / (maxP - minP)) * chartH;
      }};

      const x = (i) => {{
        return chartW - (visible.length - 1 - i) * effectiveCandleW - effectiveCandleW / 2;
      }};

      // 1. Draw Grid Lines & Price Labels
      ctx.strokeStyle = '#181f2f';
      ctx.lineWidth = 1;
      const priceSteps = 6;
      for (let s = 0; s <= priceSteps; s++) {{
        const p = minP + (maxP - minP) * (s / priceSteps);
        const yPos = y(p);

        ctx.beginPath();
        ctx.moveTo(0, yPos);
        ctx.lineTo(chartW, yPos);
        ctx.stroke();

        // Label on Right Axis
        ctx.fillStyle = '#64748b';
        ctx.font = '10px JetBrains Mono';
        ctx.textAlign = 'left';
        ctx.fillText(p.toFixed(2), chartW + 8, yPos + 3);
      }}

      // 2. Draw Volume Histogram
      if (indicators.vol && maxVol > 0) {{
        const volMaxH = chartH * 0.18;
        visible.forEach((b, i) => {{
          const bx = x(i);
          const vh = (b.v / maxVol) * volMaxH;
          ctx.fillStyle = b.c >= b.o ? 'rgba(0, 192, 118, 0.22)' : 'rgba(242, 54, 69, 0.22)';
          ctx.fillRect(bx - effectiveCandleW * 0.35, chartH - vh, effectiveCandleW * 0.7, vh);
        }});
      }}

      // 3. Draw Indicators: VWAP & SD Bands
      if (indicators.vwap) {{
        ctx.beginPath();
        ctx.strokeStyle = '#00e5ff';
        ctx.lineWidth = 1.5;
        let started = false;
        visible.forEach((b, i) => {{
          if (b.vwap) {{
            const vx = x(i);
            const vy = y(b.vwap);
            if (!started) {{ ctx.moveTo(vx, vy); started = true; }}
            else {{ ctx.lineTo(vx, vy); }}
          }}
        }});
        ctx.stroke();

        // SD Extreme Reversal Bands
        if (indicators.sd) {{
          ctx.beginPath();
          ctx.strokeStyle = 'rgba(168, 85, 247, 0.75)';
          ctx.setLineDash([4, 4]);
          ctx.lineWidth = 1;
          started = false;
          visible.forEach((b, i) => {{
            if (b.vwap && b.sd) {{
              const vx = x(i);
              const vy = y(b.vwap + 2.0 * b.sd);
              if (!started) {{ ctx.moveTo(vx, vy); started = true; }}
              else {{ ctx.lineTo(vx, vy); }}
            }}
          }});
          ctx.stroke();

          ctx.beginPath();
          started = false;
          visible.forEach((b, i) => {{
            if (b.vwap && b.sd) {{
              const vx = x(i);
              const vy = y(b.vwap - 2.0 * b.sd);
              if (!started) {{ ctx.moveTo(vx, vy); started = true; }}
              else {{ ctx.lineTo(vx, vy); }}
            }}
          }});
          ctx.stroke();
          ctx.setLineDash([]);
        }}
      }}

      // 4. Draw Candlesticks (Wicks + Bodies)
      visible.forEach((b, i) => {{
        const cx = x(i);
        const cyO = y(b.o);
        const cyC = y(b.c);
        const cyH = y(b.h);
        const cyL = y(b.l);
        const isBull = b.c >= b.o;
        const color = isBull ? '#00c076' : '#f23645';

        // Wick
        ctx.beginPath();
        ctx.strokeStyle = color;
        ctx.lineWidth = 1;
        ctx.moveTo(cx, cyH);
        ctx.lineTo(cx, cyL);
        ctx.stroke();

        // Body
        ctx.fillStyle = color;
        const topY = Math.min(cyO, cyC);
        const bodyH = Math.max(1.5, Math.abs(cyO - cyC));
        ctx.fillRect(cx - effectiveCandleW * 0.38, topY, effectiveCandleW * 0.76, bodyH);
      }});

      // 5. Draw Active Current Price Dashed Line & Price Pill
      if (activeCandle) {{
        const curY = y(activeCandle.c);
        ctx.beginPath();
        ctx.strokeStyle = (activeCandle.c >= activeCandle.o) ? '#00c076' : '#f23645';
        ctx.setLineDash([3, 3]);
        ctx.moveTo(0, curY);
        ctx.lineTo(chartW, curY);
        ctx.stroke();
        ctx.setLineDash([]);

        // Right Price Axis Pill
        const pillColor = (activeCandle.c >= activeCandle.o) ? '#00c076' : '#f23645';
        ctx.fillStyle = pillColor;
        ctx.fillRect(chartW + 2, curY - 9, priceScaleWidth - 4, 18);
        ctx.fillStyle = '#ffffff';
        ctx.font = 'bold 10px JetBrains Mono';
        ctx.textAlign = 'center';
        ctx.fillText(activeCandle.c.toFixed(2), chartW + priceScaleWidth / 2, curY + 3.5);
      }}

      // 6. Draw Open Position Lines on Chart
      openPositions.forEach(p => {{
        const py = y(p.entryPrice);
        const color = (p.side === 'BUY') ? '#22c55e' : '#ef4444';
        ctx.beginPath();
        ctx.strokeStyle = color;
        ctx.lineWidth = 1.2;
        ctx.setLineDash([5, 3]);
        ctx.moveTo(0, py);
        ctx.lineTo(chartW, py);
        ctx.stroke();
        ctx.setLineDash([]);

        ctx.fillStyle = color;
        ctx.fillRect(chartW - 140, py - 9, 130, 18);
        ctx.fillStyle = '#ffffff';
        ctx.font = 'bold 10px JetBrains Mono';
        ctx.textAlign = 'left';
        ctx.fillText(`${{p.side}} ${{p.lot}} @ ${{p.entryPrice.toFixed(2)}}`, chartW - 135, py + 3.5);
      }});

      // 7. Crosshair Tracking & Time Axis
      if (hoverMouseX >= 0 && hoverMouseX <= chartW && hoverMouseY >= 0 && hoverMouseY <= chartH) {{
        ctx.beginPath();
        ctx.strokeStyle = '#475569';
        ctx.setLineDash([3, 3]);
        ctx.moveTo(hoverMouseX, 0);
        ctx.lineTo(hoverMouseX, chartH);
        ctx.moveTo(0, hoverMouseY);
        ctx.lineTo(chartW, hoverMouseY);
        ctx.stroke();
        ctx.setLineDash([]);

        // Hover Price Box on Right Scale
        const hoverPrice = minP + (maxP - minP) * ((chartH - hoverMouseY) / chartH);
        ctx.fillStyle = '#334155';
        ctx.fillRect(chartW + 2, hoverMouseY - 8, priceScaleWidth - 4, 16);
        ctx.fillStyle = '#f8fafc';
        ctx.font = '10px JetBrains Mono';
        ctx.textAlign = 'center';
        ctx.fillText(hoverPrice.toFixed(2), chartW + priceScaleWidth / 2, hoverMouseY + 3.5);
      }}

      // Right Scale Separator Line
      ctx.strokeStyle = '#1e2536';
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(chartW, 0);
      ctx.lineTo(chartW, H);
      ctx.moveTo(0, chartH);
      ctx.lineTo(W, chartH);
      ctx.stroke();
    }}

    // Mouse Navigation: Pan & Zoom
    function setupMouseEvents() {{
      const vp = document.getElementById('chart-viewport');

      vp.addEventListener('mousedown', (e) => {{
        isDragging = true;
        dragStartX = e.clientX;
      }});

      window.addEventListener('mouseup', () => {{
        isDragging = false;
      }});

      vp.addEventListener('mousemove', (e) => {{
        const rect = canvas.getBoundingClientRect();
        hoverMouseX = e.clientX - rect.left;
        hoverMouseY = e.clientY - rect.top;

        if (isDragging) {{
          const dx = e.clientX - dragStartX;
          const barsShifted = Math.round(dx / (candleWidth * zoomLevel));
          if (barsShifted !== 0) {{
            panOffset = Math.max(0, panOffset - barsShifted);
            dragStartX = e.clientX;
            drawChart();
          }}
        }} else {{
          updateTooltip(hoverMouseX, hoverMouseY);
          drawChart();
        }}
      }});

      vp.addEventListener('mouseleave', () => {{
        hoverMouseX = -1;
        hoverMouseY = -1;
        document.getElementById('canvas-tooltip').classList.add('hidden');
        drawChart();
      }});

      vp.addEventListener('wheel', (e) => {{
        e.preventDefault();
        const factor = e.deltaY < 0 ? 1.15 : 0.85;
        adjustZoom(factor);
      }}, {{ passive: false }});
    }}

    function adjustZoom(factor) {{
      zoomLevel = Math.max(0.4, Math.min(3.5, zoomLevel * factor));
      drawChart();
    }}

    function resetChartView() {{
      panOffset = 0;
      zoomLevel = 1.0;
      drawChart();
    }}

    function updateTooltip(mx, my) {{
      const rect = canvas.getBoundingClientRect();
      const chartW = rect.width - 65;
      if (mx > chartW) {{
        document.getElementById('canvas-tooltip').classList.add('hidden');
        return;
      }}

      const data = getResampledData();
      const effectiveCandleW = candleWidth * zoomLevel;
      const maxBars = Math.floor(chartW / effectiveCandleW);
      const rightIndex = Math.max(0, data.length - 1 - panOffset);
      const leftIndex = Math.max(0, rightIndex - maxBars + 1);
      const visible = data.slice(leftIndex, rightIndex + 1);

      const barIndexFromRight = Math.floor((chartW - mx) / effectiveCandleW);
      const barIdx = visible.length - 1 - barIndexFromRight;

      if (barIdx >= 0 && barIdx < visible.length) {{
        const b = visible[barIdx];
        const tt = document.getElementById('canvas-tooltip');
        tt.classList.remove('hidden');
        tt.style.left = Math.min(rect.width - 200, Math.max(10, mx + 15)) + 'px';
        tt.style.top = Math.max(10, Math.min(rect.height - 150, my + 15)) + 'px';

        document.getElementById('tt-time').textContent = b.time;
        document.getElementById('tt-o').textContent = b.o.toFixed(2);
        document.getElementById('tt-h').textContent = b.h.toFixed(2);
        document.getElementById('tt-l').textContent = b.l.toFixed(2);
        document.getElementById('tt-c').textContent = b.c.toFixed(2);
        document.getElementById('tt-vol').textContent = b.v + ' ticks';
        document.getElementById('tt-vwap').textContent = b.vwap ? b.vwap.toFixed(2) : '--';
        document.getElementById('tt-imb').textContent = b.imb ? (b.imb > 0 ? '+' : '') + b.imb : '0.00';

        // Update strip
        document.getElementById('val-o').textContent = b.o.toFixed(2);
        document.getElementById('val-h').textContent = b.h.toFixed(2);
        document.getElementById('val-l').textContent = b.l.toFixed(2);
        document.getElementById('val-c').textContent = b.c.toFixed(2);
        document.getElementById('val-vol').textContent = b.v;
        document.getElementById('val-vwap').textContent = b.vwap ? b.vwap.toFixed(2) : '--';
        document.getElementById('val-imb').textContent = b.imb || '0';
      }}
    }}

    // Bottom Tabs
    function setBottomTab(tab) {{
      ['positions', 'deals', 'telemetry'].forEach(t => {{
        const btn = document.getElementById('tab-btn-' + t);
        const view = document.getElementById('tab-view-' + t);
        if (t === tab) {{
          btn.className = 'px-2.5 py-1 rounded font-bold text-sky-400 bg-sky-950/60 border border-sky-800/60 flex items-center gap-1.5';
          view.classList.remove('hidden');
        }} else {{
          btn.className = 'px-2.5 py-1 rounded font-medium text-slate-400 hover:text-white flex items-center gap-1.5';
          view.classList.add('hidden');
        }}
      }});
    }}
  </script>
</body>
</html>'''

TERMINAL_PATH.write_text(html_content, encoding="utf-8")
print(f"Successfully generated docs/terminal.html ({len(html_content):,} bytes)")
