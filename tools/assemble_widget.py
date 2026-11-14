import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
WIDGET_DATA_PATH = DOCS / "data" / "terminal_compact.json"
ARTIFACT_DIR = Path("/home/antigravity/.gemini/jetski/brain/v1/default/jetski_remote_agents_3p/c16d8f07-3746-43cb-bcbf-0a7d6b6ac8e9")
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
OUT_PATH = ARTIFACT_DIR / "ctrader_stream_chart.html"

data_json = WIDGET_DATA_PATH.read_text(encoding="utf-8")

# Template parts
html_head = """<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <script src="https://www.gstatic.com/antigravity/web/dev/tailwindcss.min.js"></script>
  <style>
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      user-select: none;
    }
    .ctrader-btn-sell {
      background: linear-gradient(180deg, #dc2626 0%, #991b1b 100%);
    }
    .ctrader-btn-sell:hover {
      background: linear-gradient(180deg, #ef4444 0%, #b91c1c 100%);
    }
    .ctrader-btn-buy {
      background: linear-gradient(180deg, #16a34a 0%, #15803d 100%);
    }
    .ctrader-btn-buy:hover {
      background: linear-gradient(180deg, #22c55e 0%, #16a34a 100%);
    }
  </style>
</head>
<body class="bg-transparent text-[var(--foreground)] antialiased p-0 m-0">
  <div class="rounded-xl border border-[var(--card-border)] bg-[var(--card)] p-3 space-y-2.5 shadow-lg max-w-full">
    
    <!-- Header: Symbol Switcher, Status & Speed -->
    <div class="flex items-center justify-between gap-2 border-b border-[var(--card-border)] pb-2 text-xs flex-wrap">
      <div class="flex items-center gap-1.5">
        <span class="font-black text-sky-400 font-mono tracking-wider flex items-center gap-1">
          <span class="w-5 h-5 rounded bg-sky-600 text-white flex items-center justify-center text-[10px]">cT</span>
          <span>cTrader</span>
        </span>
        <div class="flex items-center gap-0.5 bg-[var(--background)] p-0.5 rounded-lg border border-[var(--border)] font-mono text-[11px]">
          <button onclick="switchSym('XAUUSD')" id="w-sym-XAUUSD" class="px-2 py-0.5 rounded font-bold bg-amber-500/20 text-amber-300 border border-amber-500/40">🥇 XAU</button>
          <button onclick="switchSym('BTCUSD')" id="w-sym-BTCUSD" class="px-2 py-0.5 rounded text-[var(--muted-foreground)] hover:text-[var(--foreground)]">₿ BTC</button>
          <button onclick="switchSym('ETHUSD')" id="w-sym-ETHUSD" class="px-2 py-0.5 rounded text-[var(--muted-foreground)] hover:text-[var(--foreground)]">⟠ ETH</button>
        </div>
      </div>

      <!-- Live Stream Delay Status -->
      <div class="flex items-center gap-2 font-mono text-[10px]">
        <div class="flex items-center gap-1 px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
          <span class="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
          <span class="font-bold">REC STREAM (1M DELAY)</span>
        </div>
        <div class="flex items-center gap-1 px-1.5 py-0.5 rounded bg-[var(--background)] border border-[var(--border)] text-[var(--muted-foreground)]">
          <span>⏱️</span>
          <span id="w-countdown" class="font-bold text-amber-400 tabular-nums">60s</span>
        </div>
        <!-- Speed Buttons -->
        <div class="flex items-center gap-0.5 bg-[var(--background)] p-0.5 rounded border border-[var(--border)]">
          <button onclick="setSpd(1)" id="w-spd-1" class="px-1.5 py-0.5 rounded font-bold bg-[var(--accent)] text-white text-[9px]">1x</button>
          <button onclick="setSpd(5)" id="w-spd-5" class="px-1.5 py-0.5 rounded text-[var(--muted-foreground)] text-[9px]">5x</button>
          <button onclick="setSpd(20)" id="w-spd-20" class="px-1.5 py-0.5 rounded text-[var(--muted-foreground)] text-[9px]">20x</button>
          <button onclick="togglePlay()" id="w-btn-play" class="px-1.5 py-0.5 rounded font-bold text-sky-400 text-[9px]">⏸️</button>
        </div>
      </div>
    </div>

    <!-- Paper Trading Simulator Mode Banner -->
    <div class="px-2 py-1 rounded-md bg-sky-500/10 border border-sky-500/25 text-[10px] font-mono text-sky-300 flex items-center justify-between">
      <div class="flex items-center gap-1.5">
        <span>🎮</span>
        <span class="font-bold">โหมดจำลองการเทรด (Interactive Paper Trading Simulator จากชุดข้อมูลบันทึกจริง)</span>
      </div>
      <span class="text-[9px] text-[var(--muted-foreground)]">Delay 1m</span>
    </div>

    <!-- QuickTrade Bar -->
    <div class="flex items-center justify-between gap-2 px-1 font-mono">
      <div class="flex items-center gap-2">
        <button onclick="trade('SELL')" class="ctrader-btn-sell px-3 py-1 rounded text-white font-bold text-xs flex items-center gap-1.5 shadow-sm active:scale-95 transition cursor-pointer">
          <span class="text-[9px] uppercase tracking-wider text-rose-200">SELL</span>
          <span id="w-bid-val" class="text-xs font-black tabular-nums">3895.12</span>
        </button>
        <div class="px-2 py-0.5 rounded bg-[var(--background)] border border-[var(--border)] text-[10px] text-center">
          <span class="text-[var(--muted-foreground)]">Spread:</span>
          <strong id="w-spread-val" class="text-amber-400 font-bold ml-1">0.13</strong>
        </div>
        <button onclick="trade('BUY')" class="ctrader-btn-buy px-3 py-1 rounded text-white font-bold text-xs flex items-center gap-1.5 shadow-sm active:scale-95 transition cursor-pointer">
          <span class="text-[9px] uppercase tracking-wider text-emerald-200">BUY</span>
          <span id="w-ask-val" class="text-xs font-black tabular-nums">3895.25</span>
        </button>
      </div>

      <!-- OHLC Tooltip summary -->
      <div id="w-metric-summary" class="hidden sm:flex items-center gap-2 text-[10px] text-[var(--muted-foreground)]">
        <span>Vol: <strong id="w-strip-vol" class="text-cyan-400">--</strong></span>
        <span>VWAP: <strong id="w-strip-vwap" class="text-cyan-300">--</strong></span>
        <span>Imb: <strong id="w-strip-imb" class="text-amber-300">--</strong></span>
      </div>
    </div>

    <!-- Canvas Chart Box -->
    <div id="w-chart-container" class="relative w-full h-[230px] rounded-lg border border-[var(--border)] bg-[#0a0d14] overflow-hidden">
      <canvas id="w-canvas" class="w-full h-full block cursor-crosshair"></canvas>

      <!-- Hover Tooltip -->
      <div id="w-tooltip" class="pointer-events-none hidden absolute z-20 p-2 rounded bg-slate-950/95 border border-slate-700 font-mono text-[10px] shadow-xl text-white space-y-0.5">
        <div id="w-tt-time" class="text-sky-400 font-bold border-b border-slate-800 pb-0.5">--</div>
        <div class="grid grid-cols-2 gap-x-2 text-[9px]">
          <span class="text-slate-400">O:</span><span id="w-tt-o" class="text-right">--</span>
          <span class="text-slate-400">H:</span><span id="w-tt-h" class="text-emerald-400 text-right">--</span>
          <span class="text-slate-400">L:</span><span id="w-tt-l" class="text-rose-400 text-right">--</span>
          <span class="text-slate-400">C:</span><span id="w-tt-c" class="text-right">--</span>
          <span class="text-slate-400">VWAP:</span><span id="w-tt-vwap" class="text-cyan-400 text-right">--</span>
        </div>
      </div>
    </div>

    <!-- Active Positions / Status Bar Footer -->
    <div class="flex items-center justify-between text-[10px] font-mono border-t border-[var(--card-border)] pt-2 text-[var(--muted-foreground)]">
      <div id="w-pos-status" class="flex items-center gap-1.5">
        <span>Positions:</span>
        <strong id="w-pos-count" class="text-[var(--foreground)]">0</strong>
        <span id="w-pos-detail" class="text-emerald-400 font-bold ml-1 hidden"></span>
      </div>
      <div class="flex items-center gap-2">
        <span>Stream Buffer: <strong id="w-buf-count" class="text-sky-400">100 bars</strong></span>
        <span>·</span>
        <span class="text-emerald-400">● Live Ticking</span>
      </div>
    </div>

  </div>

  <script>
"""

js_code = f"""
    const DATA = {data_json};

    let sym = 'XAUUSD';
    let visible = [];
    let queue = [];
    let active = null;
    let bid = 0, ask = 0, sp = 0.12;
    let isPlaying = true;
    let speed = 5;
    let countdown = 60;
    let cdTimer = null, tickTimer = null;
    let openPositions = [];

    let canvas, ctx;
    let hoverX = -1, hoverY = -1;

    function init() {{
      canvas = document.getElementById('w-canvas');
      ctx = canvas.getContext('2d');
      setupCanvas();
      loadSym(sym);
      startEngine();

      window.addEventListener('resize', () => {{ setupCanvas(); draw(); }});
      canvas.addEventListener('mousemove', (e) => {{
        const r = canvas.getBoundingClientRect();
        hoverX = e.clientX - r.left;
        hoverY = e.clientY - r.top;
        draw();
      }});
      canvas.addEventListener('mouseleave', () => {{
        hoverX = -1; hoverY = -1;
        document.getElementById('w-tooltip').classList.add('hidden');
        draw();
      }});
    }}

    function setupCanvas() {{
      const dpr = window.devicePixelRatio || 1;
      const r = canvas.getBoundingClientRect();
      canvas.width = r.width * dpr;
      canvas.height = r.height * dpr;
      ctx.scale(dpr, dpr);
    }}

    function loadSym(s) {{
      sym = s;
      const item = DATA[s];
      visible = JSON.parse(JSON.stringify(item.initial));
      queue = JSON.parse(JSON.stringify(item.stream));

      if (queue.length > 0) {{
        const nxt = queue.shift();
        active = {{
          time: nxt.time, o: nxt.o, h: nxt.o, l: nxt.o, c: nxt.o,
          targetH: nxt.h, targetL: nxt.l, targetC: nxt.c,
          v: Math.floor(nxt.v * 0.1), targetV: nxt.v,
          sp: nxt.sp, imb: nxt.imb, vwap: nxt.vwap, sd: nxt.sd
        }};
        bid = active.c; sp = active.sp;
        ask = parseFloat((bid + sp).toFixed(2));
      }}
      countdown = 60;
      updateUI();
      draw();
    }}

    function switchSym(s) {{
      ['XAUUSD', 'BTCUSD', 'ETHUSD'].forEach(k => {{
        const b = document.getElementById('w-sym-' + k);
        if (k === s) {{
          b.className = 'px-2 py-0.5 rounded font-bold bg-amber-500/20 text-amber-300 border border-amber-500/40';
        }} else {{
          b.className = 'px-2 py-0.5 rounded text-[var(--muted-foreground)] hover:text-[var(--foreground)]';
        }}
      }});
      loadSym(s);
    }}

    function startEngine() {{
      if (cdTimer) clearInterval(cdTimer);
      if (tickTimer) clearInterval(tickTimer);

      cdTimer = setInterval(() => {{
        if (!isPlaying || !active) return;
        countdown -= (0.1 * speed);
        if (countdown <= 0) {{
          advanceBar();
          countdown = 60;
        }}
        document.getElementById('w-countdown').textContent = Math.max(0, Math.ceil(countdown)) + 's';
      }}, 100);

      tickTimer = setInterval(() => {{
        if (!isPlaying || !active) return;
        const dist = active.targetC - active.c;
        const delta = (dist * 0.08) + ((Math.random() - 0.5) * sp * 0.8);
        active.c = parseFloat((active.c + delta).toFixed(2));
        if (active.c > active.h) active.h = active.c;
        if (active.c < active.l) active.l = active.c;
        active.v = Math.min(active.targetV, active.v + Math.floor(Math.random() * 2 + 1));
        bid = active.c;
        ask = parseFloat((bid + sp).toFixed(2));

        updateUI();
        updatePositions();
        draw();
      }}, 300);
    }}

    function advanceBar() {{
      if (!active) return;
      active.h = Math.max(active.h, active.targetH);
      active.l = Math.min(active.l, active.targetL);
      active.c = active.targetC;
      active.v = active.targetV;

      visible.push({{
        time: active.time, o: active.o, h: active.h, l: active.l, c: active.c,
        v: active.v, sp: active.sp, imb: active.imb, vwap: active.vwap, sd: active.sd
      }});

      if (visible.length > 90) visible.shift();

      if (queue.length > 0) {{
        const nxt = queue.shift();
        active = {{
          time: nxt.time, o: nxt.o, h: nxt.o, l: nxt.o, c: nxt.o,
          targetH: nxt.h, targetL: nxt.l, targetC: nxt.c,
          v: Math.floor(nxt.v * 0.1), targetV: nxt.v,
          sp: nxt.sp, imb: nxt.imb, vwap: nxt.vwap, sd: nxt.sd
        }};
      }} else {{
        queue = JSON.parse(JSON.stringify(DATA[sym].stream));
      }}
      document.getElementById('w-buf-count').textContent = queue.length + ' bars';
      draw();
    }}

    function setSpd(s) {{
      speed = s;
      [1, 5, 20].forEach(k => {{
        const b = document.getElementById('w-spd-' + k);
        b.className = k === s ? 'px-1.5 py-0.5 rounded font-bold bg-[var(--accent)] text-white text-[9px]' : 'px-1.5 py-0.5 rounded text-[var(--muted-foreground)] text-[9px]';
      }});
    }}

    function togglePlay() {{
      isPlaying = !isPlaying;
      document.getElementById('w-btn-play').textContent = isPlaying ? '⏸️' : '▶️';
    }}

    function trade(side) {{
      const p = (side === 'BUY') ? ask : bid;
      openPositions.push({{
        id: Math.floor(Math.random() * 90000 + 10000),
        side: side,
        entry: p,
        pnl: 0.00
      }});
      updatePositions();
      draw();
    }}

    function updatePositions() {{
      let tot = 0;
      openPositions.forEach(p => {{
        const cur = (p.side === 'BUY') ? bid : ask;
        const diff = (p.side === 'BUY') ? (cur - p.entry) : (p.entry - cur);
        let m = (sym === 'BTCUSD') ? 1 : (sym === 'ETHUSD' ? 10 : 100);
        p.pnl = parseFloat((diff * 0.01 * m).toFixed(2));
        tot += p.pnl;
      }});

      document.getElementById('w-pos-count').textContent = openPositions.length;
      const det = document.getElementById('w-pos-detail');
      if (openPositions.length > 0) {{
        det.classList.remove('hidden');
        det.textContent = '(PnL: ' + (tot >= 0 ? '+' : '') + '$' + tot.toFixed(2) + ')';
        det.className = tot >= 0 ? 'text-emerald-400 font-bold ml-1' : 'text-rose-400 font-bold ml-1';
      }} else {{
        det.classList.add('hidden');
      }}
    }}

    function updateUI() {{
      document.getElementById('w-bid-val').textContent = bid.toFixed(2);
      document.getElementById('w-ask-val').textContent = ask.toFixed(2);
      document.getElementById('w-spread-val').textContent = sp.toFixed(2);
      if (active) {{
        document.getElementById('w-strip-vol').textContent = active.v;
        document.getElementById('w-strip-vwap').textContent = active.vwap ? active.vwap.toFixed(2) : '--';
        document.getElementById('w-strip-imb').textContent = active.imb ? (active.imb > 0 ? '+' : '') + active.imb : '0';
      }}
    }}

    function draw() {{
      if (!canvas || !ctx) return;
      const rect = canvas.getBoundingClientRect();
      const W = rect.width, H = rect.height;
      ctx.clearRect(0, 0, W, H);

      const priceScaleW = 55;
      const chartW = W - priceScaleW;
      const chartH = H - 20;

      const bars = [...visible];
      if (active) bars.push(active);
      if (!bars.length) return;

      const cW = 5;
      const maxBars = Math.floor(chartW / cW);
      const displayBars = bars.slice(-maxBars);

      let minP = Infinity, maxP = -Infinity, maxV = 0;
      displayBars.forEach(b => {{
        if (b.l < minP) minP = b.l;
        if (b.h > maxP) maxP = b.h;
        if (b.v > maxV) maxV = b.v;
      }});
      const pad = (maxP - minP) * 0.08 || 1;
      maxP += pad; minP -= pad;

      const y = (p) => chartH - ((p - minP) / (maxP - minP)) * chartH;
      const x = (i) => chartW - (displayBars.length - 1 - i) * cW - cW / 2;

      // Grid
      ctx.strokeStyle = '#181f2f';
      ctx.lineWidth = 1;
      for (let s = 0; s <= 4; s++) {{
        const p = minP + (maxP - minP) * (s / 4);
        const yP = y(p);
        ctx.beginPath(); ctx.moveTo(0, yP); ctx.lineTo(chartW, yP); ctx.stroke();
        ctx.fillStyle = '#64748b';
        ctx.font = '9px monospace';
        ctx.fillText(p.toFixed(2), chartW + 5, yP + 3);
      }}

      // Volume
      if (maxV > 0) {{
        displayBars.forEach((b, i) => {{
          const bx = x(i);
          const vh = (b.v / maxV) * (chartH * 0.2);
          ctx.fillStyle = b.c >= b.o ? 'rgba(0, 192, 118, 0.2)' : 'rgba(242, 54, 69, 0.2)';
          ctx.fillRect(bx - cW * 0.35, chartH - vh, cW * 0.7, vh);
        }});
      }}

      // VWAP line
      ctx.beginPath();
      ctx.strokeStyle = '#00e5ff';
      ctx.lineWidth = 1.2;
      let started = false;
      displayBars.forEach((b, i) => {{
        if (b.vwap) {{
          const vx = x(i), vy = y(b.vwap);
          if (!started) {{ ctx.moveTo(vx, vy); started = true; }} else {{ ctx.lineTo(vx, vy); }}
        }}
      }});
      ctx.stroke();

      // Candlesticks
      displayBars.forEach((b, i) => {{
        const cx = x(i);
        const cyO = y(b.o), cyC = y(b.c);
        const cyH = y(b.h), cyL = y(b.l);
        const color = b.c >= b.o ? '#00c076' : '#f23645';

        ctx.beginPath();
        ctx.strokeStyle = color;
        ctx.lineWidth = 1;
        ctx.moveTo(cx, cyH); ctx.lineTo(cx, cyL); ctx.stroke();

        ctx.fillStyle = color;
        const top = Math.min(cyO, cyC);
        const hgt = Math.max(1.5, Math.abs(cyO - cyC));
        ctx.fillRect(cx - cW * 0.35, top, cW * 0.7, hgt);
      }});

      // Current Price line & pill
      if (active) {{
        const cy = y(active.c);
        ctx.beginPath();
        ctx.strokeStyle = active.c >= active.o ? '#00c076' : '#f23645';
        ctx.setLineDash([2, 2]);
        ctx.moveTo(0, cy); ctx.lineTo(chartW, cy); ctx.stroke();
        ctx.setLineDash([]);

        ctx.fillStyle = active.c >= active.o ? '#00c076' : '#f23645';
        ctx.fillRect(chartW + 2, cy - 7, priceScaleW - 4, 14);
        ctx.fillStyle = '#ffffff';
        ctx.font = 'bold 9px monospace';
        ctx.textAlign = 'center';
        ctx.fillText(active.c.toFixed(2), chartW + priceScaleW / 2, cy + 3);
      }}

      // Open Positions lines
      openPositions.forEach(p => {{
        const py = y(p.entry);
        ctx.beginPath();
        ctx.strokeStyle = p.side === 'BUY' ? '#22c55e' : '#ef4444';
        ctx.setLineDash([4, 2]);
        ctx.moveTo(0, py); ctx.lineTo(chartW, py); ctx.stroke();
        ctx.setLineDash([]);
      }});

      // Tooltip
      if (hoverX >= 0 && hoverX <= chartW && hoverY >= 0 && hoverY <= chartH) {{
        const barIdxFromRight = Math.floor((chartW - hoverX) / cW);
        const idx = displayBars.length - 1 - barIdxFromRight;
        if (idx >= 0 && idx < displayBars.length) {{
          const b = displayBars[idx];
          const tt = document.getElementById('w-tooltip');
          tt.classList.remove('hidden');
          tt.style.left = Math.min(chartW - 140, Math.max(10, hoverX + 10)) + 'px';
          tt.style.top = Math.max(10, Math.min(chartH - 90, hoverY + 10)) + 'px';
          document.getElementById('w-tt-time').textContent = b.time;
          document.getElementById('w-tt-o').textContent = b.o.toFixed(2);
          document.getElementById('w-tt-h').textContent = b.h.toFixed(2);
          document.getElementById('w-tt-l').textContent = b.l.toFixed(2);
          document.getElementById('w-tt-c').textContent = b.c.toFixed(2);
          document.getElementById('w-tt-vwap').textContent = b.vwap ? b.vwap.toFixed(2) : '--';
        }}
      }}
    }}

    window.onload = init;
"""

full_html = html_head + js_code + "\n  </script>\n</body>\n</html>"
OUT_PATH.write_text(full_html, encoding="utf-8")
print(f"Assembled successfully to {OUT_PATH} ({len(full_html)} bytes)")
