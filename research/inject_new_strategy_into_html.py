import json
import re

html_path = r'd:\cbot-atgvt\docs\index.html'
json_path = r'd:\cbot-atgvt\docs\data\backtest_data.json'
live_status_path = r'd:\cbot-atgvt\docs\data\live_status.json'

with open(html_path, 'r', encoding='utf-8') as f:
    html = f.read()

with open(json_path, 'r', encoding='utf-8') as f:
    db = json.load(f)

with open(live_status_path, 'r', encoding='utf-8') as f:
    live_status = json.load(f)

print("Backtest keys:", list(db.keys()))

# 1. Update the Strategy Switcher Buttons in HTML
old_buttons = '''      <!-- Strategy Switcher Buttons -->
      <div class="flex flex-wrap items-center bg-slate-900 p-1 rounded-xl border border-slate-800 shadow-sm">
        <button id="tab-runner" onclick="switchStrategy('dom_smart_runner')" class="px-3 py-1.5 text-xs md:text-sm font-bold rounded-lg transition-all bg-emerald-500 text-slate-950 shadow">
          🚀 DOM_SMART_RUNNER (ปลดล็อค)
        </button>
        <button id="tab-smc" onclick="switchStrategy('smc_fibo_dom')" class="px-3 py-1.5 text-xs md:text-sm font-medium rounded-lg transition-all text-slate-400 hover:text-white">
          ⚡ SMC_FIBO_DOM_5M
        </button>
        <button id="tab-fade" onclick="switchStrategy('dom_fade')" class="px-3 py-1.5 text-xs md:text-sm font-medium rounded-lg transition-all text-slate-400 hover:text-white">
          🛡️ DOM_FADE_5M
        </button>
        <button id="tab-compare" onclick="switchStrategy('compare')" class="px-3 py-1.5 text-xs md:text-sm font-medium rounded-lg transition-all text-slate-400 hover:text-white">
          ⚖️ เปรียบเทียบ 3 ตัว
        </button>
      </div>'''

new_buttons = '''      <!-- Strategy Switcher Buttons -->
      <div class="flex flex-wrap items-center bg-slate-900 p-1 rounded-xl border border-slate-800 shadow-sm gap-1">
        <button id="tab-dom-abs-btc" onclick="switchStrategy('dom_absorption_btc')" class="px-3 py-1.5 text-xs md:text-sm font-bold rounded-lg transition-all bg-amber-500 text-slate-950 shadow flex items-center gap-1.5">
          <span>🔥</span> DOM_ABSORPTION (BTC) <span class="bg-slate-950 text-amber-400 text-[10px] px-1.5 py-0.5 rounded-full font-mono">NEW +$14.16</span>
        </button>
        <button id="tab-dom-abs-eth" onclick="switchStrategy('dom_absorption_eth')" class="px-3 py-1.5 text-xs md:text-sm font-medium rounded-lg transition-all text-slate-300 hover:text-white flex items-center gap-1.5">
          <span>⚡</span> DOM_ABSORPTION (ETH) <span class="bg-blue-500/20 text-blue-400 text-[10px] px-1.5 py-0.5 rounded-full font-mono">+$16.16</span>
        </button>
        <button id="tab-runner" onclick="switchStrategy('dom_smart_runner')" class="px-3 py-1.5 text-xs md:text-sm font-medium rounded-lg transition-all text-slate-400 hover:text-white">
          🚀 SMART_RUNNER (XAU)
        </button>
        <button id="tab-smc" onclick="switchStrategy('smc_fibo_dom')" class="px-3 py-1.5 text-xs md:text-sm font-medium rounded-lg transition-all text-slate-400 hover:text-white">
          ⚡ SMC_FIBO_5M
        </button>
        <button id="tab-fade" onclick="switchStrategy('dom_fade')" class="px-3 py-1.5 text-xs md:text-sm font-medium rounded-lg transition-all text-slate-400 hover:text-white">
          🛡️ DOM_FADE_5M
        </button>
      </div>'''

if old_buttons in html:
    html = html.replace(old_buttons, new_buttons)
    print("Replaced Strategy Switcher Buttons successfully!")
else:
    print("Warning: old_buttons pattern not exact match")

# 2. Update the Live Status Banner at the top
old_banner_time = '31 ต.ค. 2026, 16:55 น.'
new_banner_time = '1 พ.ย. 2026, 09:35 น.'
html = html.replace(old_banner_time, new_banner_time)

# 3. Add Real-time Live Forward Trading Monitor Widget directly above the KPIs
live_widget_html = f'''
    <!-- REAL-TIME FORWARD TRADING & DOM LIVE FEED (AUTO-REFRESHING) -->
    <div id="live-forward-card" class="bg-gradient-to-r from-amber-950/40 via-slate-900 to-slate-900 border-2 border-amber-500/40 rounded-2xl p-4 sm:p-5 shadow-xl">
      <div class="flex flex-col md:flex-row md:items-center justify-between gap-3 border-b border-slate-800 pb-3 mb-4">
        <div class="flex items-center gap-3">
          <span class="flex h-3.5 w-3.5 relative">
            <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-amber-400 opacity-75"></span>
            <span class="relative inline-flex rounded-full h-3.5 w-3.5 bg-amber-500"></span>
          </span>
          <div>
            <div class="flex items-center gap-2">
              <h2 class="text-base font-bold text-white tracking-wide">🔴 ระบบเทรดสดในตลาด (Real-Time Forward Execution)</h2>
              <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30">
                LIVE DEMO ACTIVE
              </span>
            </div>
            <p class="text-xs text-slate-400 mt-0.5">
              บอท <strong>BacktestLab (DOM_ABSORPTION)</strong> กำลังเฝ้าสมุดคำสั่ง Level 2 และส่งคำสั่งเทรดสดบนพอร์ต Pepperstone #5258778
            </p>
          </div>
        </div>
        <div class="flex items-center gap-3 text-xs">
          <div class="bg-slate-950/80 px-3 py-1.5 rounded-xl border border-slate-800 text-right">
            <div class="text-[10px] text-slate-400">อัปเดตสดล่าสุด:</div>
            <div id="live-clock" class="font-mono font-bold text-emerald-400">{live_status['timestamp_local']}</div>
          </div>
          <button onclick="fetchLiveStatus()" class="px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition flex items-center gap-1.5 text-xs">
            <span>🔄</span> รีเฟรช
          </button>
        </div>
      </div>

      <!-- Live Metric Grid -->
      <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        <div class="bg-slate-950/80 border border-slate-800 rounded-xl p-3">
          <div class="text-[11px] text-slate-400">สินทรัพย์ที่เทรดสด</div>
          <div id="live-symbol" class="text-base font-extrabold text-white mt-1 font-mono">BTCUSD (M1)</div>
          <div class="text-[10px] text-amber-400 mt-0.5">0.01 Lot / TP $50 / SL $25</div>
        </div>

        <div class="bg-slate-950/80 border border-slate-800 rounded-xl p-3">
          <div class="text-[11px] text-slate-400">ราคากลางสด (Mid Price)</div>
          <div id="live-price" class="text-base font-extrabold text-emerald-400 mt-1 font-mono">${live_status['dom_recorders'][0]['current_price']:.2f}</div>
          <div id="live-spread" class="text-[10px] text-slate-400 mt-0.5">Spread: ${live_status['dom_recorders'][0]['spread']:.2f}</div>
        </div>

        <div class="bg-slate-950/80 border border-slate-800 rounded-xl p-3">
          <div class="text-[11px] text-slate-400">DOM Imbalance (แรงซื้อ/ขาย)</div>
          <div id="live-imbalance" class="text-base font-extrabold mt-1 font-mono text-cyan-400">{live_status['dom_recorders'][0]['imbalance']:+.3f}</div>
          <div id="live-imbalance-desc" class="text-[10px] text-slate-400 mt-0.5">สมุดคำสั่งสมดุลปกติ</div>
        </div>

        <div class="bg-slate-950/80 border border-slate-800 rounded-xl p-3">
          <div class="text-[11px] text-slate-400">CVD (สะสม Volume Delta)</div>
          <div id="live-cvd" class="text-base font-extrabold text-blue-400 mt-1 font-mono">{live_status['dom_recorders'][0]['cvd']:+.0f}</div>
          <div class="text-[10px] text-slate-400 mt-0.5">Anchored Daily CVD</div>
        </div>

        <div class="bg-slate-950/80 border border-slate-800 rounded-xl p-3">
          <div class="text-[11px] text-slate-400">พอร์ตทดลอง (Demo Balance)</div>
          <div id="live-balance" class="text-base font-extrabold text-white mt-1 font-mono">${live_status['forward_trading']['balance']:.2f}</div>
          <div class="text-[10px] text-emerald-400 mt-0.5">Equity: ${live_status['forward_trading']['equity']:.2f} USD</div>
        </div>

        <div class="bg-slate-950/80 border border-slate-800 rounded-xl p-3">
          <div class="text-[11px] text-slate-400">บันทึก DOM Level 2 สด</div>
          <div class="text-base font-extrabold text-emerald-400 mt-1 font-mono">546+ นาที</div>
          <div class="text-[10px] text-emerald-400/80 mt-0.5">3 ตลาดขนานกัน 24 ชม.</div>
        </div>
      </div>
    </div>
'''

if 'id="kpi-section"' in html and 'id="live-forward-card"' not in html:
    html = html.replace('<div id="kpi-section"', live_widget_html + '\n    <div id="kpi-section"')
    print("Injected Live Forward Card Widget successfully!")

# 4. Inject Updated DATA JSON into HTML script
data_decl_idx = html.find('const DATA = ')
if data_decl_idx != -1:
    data_end_idx = html.find('let currentStrat = ', data_decl_idx)
    if data_end_idx != -1:
        new_data_str = f"const DATA = {json.dumps(db, ensure_ascii=False)};\n    "
        html = html[:data_decl_idx] + new_data_str + html[data_end_idx:]
        print("Updated inlined DATA JSON with DOM_ABSORPTION strategies!")

# 5. Add Live Polling Script to index.html
live_polling_js = '''
    // Real-Time Polling function to update live forward trading metrics every 3 seconds
    async function fetchLiveStatus() {
      try {
        const res = await fetch('data/live_status.json?t=' + Date.now());
        if (!res.ok) return;
        const data = await res.json();
        
        const elClock = document.getElementById('live-clock');
        const elPrice = document.getElementById('live-price');
        const elSpread = document.getElementById('live-spread');
        const elImb = document.getElementById('live-imbalance');
        const elCvd = document.getElementById('live-cvd');
        const elBal = document.getElementById('live-balance');
        
        if (elClock) elClock.textContent = data.timestamp_local;
        if (data.dom_recorders && data.dom_recorders.length > 0) {
          const btc = data.dom_recorders[0];
          if (elPrice) elPrice.textContent = '$' + btc.current_price.toFixed(2);
          if (elSpread) elSpread.textContent = 'Spread: $' + btc.spread.toFixed(2);
          if (elImb) {
            elImb.textContent = (btc.imbalance >= 0 ? '+' : '') + btc.imbalance.toFixed(3);
            if (btc.imbalance >= 0.03) {
              elImb.className = 'text-base font-extrabold mt-1 font-mono text-emerald-400';
              document.getElementById('live-imbalance-desc').textContent = '⚠️ Bid Wall หนุนรับ (จังหวะ Buy)';
            } else if (btc.imbalance <= -0.03) {
              elImb.className = 'text-base font-extrabold mt-1 font-mono text-rose-400';
              document.getElementById('live-imbalance-desc').textContent = '⚠️ Ask Wall ขวางต้าน (จังหวะ Sell)';
            } else {
              elImb.className = 'text-base font-extrabold mt-1 font-mono text-cyan-400';
              document.getElementById('live-imbalance-desc').textContent = 'สมุดคำสั่งสมดุลปกติ';
            }
          }
          if (elCvd) elCvd.textContent = (btc.cvd >= 0 ? '+' : '') + Math.round(btc.cvd);
        }
        if (data.forward_trading && elBal) {
          elBal.textContent = '$' + data.forward_trading.balance.toFixed(2);
        }
      } catch (err) {
        // Fallback gracefully
      }
    }
    // Auto-poll every 3 seconds
    setInterval(fetchLiveStatus, 3000);
'''

if 'setInterval(fetchLiveStatus, 3000);' not in html:
    # Inject before </script>
    last_script_close = html.rfind('</script>')
    if last_script_close != -1:
        html = html[:last_script_close] + live_polling_js + '\n  ' + html[last_script_close:]
        print("Injected live polling Javascript successfully!")

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(html)

print("Saved updated docs/index.html successfully!")
