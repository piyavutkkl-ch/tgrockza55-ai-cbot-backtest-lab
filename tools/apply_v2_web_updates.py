import re

path = 'docs/index.html'
with open(path, 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Update Strategy Switcher Buttons
old_buttons = '''      <!-- Strategy Switcher Buttons -->
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
        <button id="tab-compare" onclick="switchStrategy('compare')" class="px-3 py-1.5 text-xs md:text-sm font-medium rounded-lg transition-all text-slate-400 hover:text-white flex items-center gap-1">
          <span>📊</span> เปรียบเทียบ 3 ยุค
        </button>
      </div>'''

new_buttons = '''      <!-- Strategy Switcher Buttons -->
      <div class="flex flex-wrap items-center bg-slate-900 p-1 rounded-xl border border-slate-800 shadow-sm gap-1">
        <button id="tab-dom-abs-btc" onclick="switchStrategy('dom_absorption_btc')" class="px-3 py-1.5 text-xs md:text-sm font-bold rounded-lg transition-all bg-amber-500 text-slate-950 shadow flex items-center gap-1.5">
          <span>🔥</span> DOM_ABSORPTION (BTC) <span class="bg-slate-950 text-amber-300 text-[10px] px-1.5 py-0.5 rounded-full font-mono">V2 +$5.34 (92.9%)</span>
        </button>
        <button id="tab-dom-abs-eth" onclick="switchStrategy('dom_absorption_eth')" class="px-3 py-1.5 text-xs md:text-sm font-medium rounded-lg transition-all text-slate-300 hover:text-white flex items-center gap-1.5">
          <span>⚡</span> DOM_ABSORPTION (ETH) <span class="bg-blue-500/20 text-blue-400 text-[10px] px-1.5 py-0.5 rounded-full font-mono">V2 +$0.10</span>
        </button>
        <button id="tab-dom-abs-xau" onclick="switchStrategy('dom_absorption_xau')" class="px-3 py-1.5 text-xs md:text-sm font-medium rounded-lg transition-all text-slate-300 hover:text-white flex items-center gap-1.5">
          <span>🏆</span> DOM_ABSORPTION (XAU) <span class="bg-amber-500/20 text-amber-300 text-[10px] px-1.5 py-0.5 rounded-full font-mono">V2 +$0.06</span>
        </button>
        <button id="tab-runner" onclick="switchStrategy('dom_smart_runner')" class="px-3 py-1.5 text-xs md:text-sm font-medium rounded-lg transition-all text-slate-400 hover:text-white">
          🚀 SMART_RUNNER (XAU M5)
        </button>
        <button id="tab-smc" onclick="switchStrategy('smc_fibo_dom')" class="px-3 py-1.5 text-xs md:text-sm font-medium rounded-lg transition-all text-slate-400 hover:text-white">
          ⚡ SMC_FIBO_5M
        </button>
        <button id="tab-fade" onclick="switchStrategy('dom_fade')" class="px-3 py-1.5 text-xs md:text-sm font-medium rounded-lg transition-all text-slate-400 hover:text-white">
          🛡️ DOM_FADE_5M
        </button>
        <button id="tab-compare" onclick="switchStrategy('compare')" class="px-3 py-1.5 text-xs md:text-sm font-medium rounded-lg transition-all text-slate-400 hover:text-white flex items-center gap-1">
          <span>📊</span> เปรียบเทียบ 3 ยุค
        </button>
      </div>'''

assert old_buttons in html, "Could not find old_buttons"
html = html.replace(old_buttons, new_buttons)

# 2. Add Visual Linkage Callout Banner
target_hint = '''      <!-- INTERACTIVE USER HINT BANNER FOR BEGINNERS -->'''
linkage_banner = '''      <!-- 🔗 VISUAL LINKAGE: ZONE 2 BACKTEST <-> ZONE 1 LIVE BOT FLEET -->
      <div class="bg-gradient-to-r from-amber-950/40 via-slate-900 to-slate-900 border border-amber-500/30 rounded-xl p-3.5 shadow-sm text-xs text-slate-300">
        <div class="flex items-center gap-2 font-bold text-amber-400 text-sm mb-1.5">
          <span>🔗</span> ความเชื่อมโยงระหว่าง "ห้องทดลองย้อนหลัง" (โซน 2) และ "บอทเทรดสด" (โซน 1 ด้านบน):
        </div>
        <p class="text-slate-400 text-xs mb-2 leading-relaxed">
          แท็บกลยุทธ์ 3 ตัวแรก (BTC, ETH, XAU) คือสูตรอัลกอริทึมสมุดคำสั่งซื้อขายสถาบัน (L2 Order Book V2) ที่ผ่านการจำลองย้อนหลังบนข้อมูลจริง 2,020 แท่ง (1-2 พ.ย. 2026) 
          เพื่อทำหน้าที่เป็น <strong>"สมองควบคุมคำสั่ง"</strong> ของบอทสดที่กำลังรันในโซน 1:
        </p>
        <div class="grid grid-cols-1 md:grid-cols-4 gap-2 text-[11px]">
          <div class="p-2.5 rounded-lg bg-slate-950/70 border border-amber-500/20">
            <div class="flex items-center justify-between text-amber-400 font-bold mb-1">
              <span>🔥 บอท 1: BTCUSD M1</span>
              <span class="text-[10px] bg-amber-500/20 px-1.5 py-0.2 rounded font-mono">ชนะ 92.9%</span>
            </div>
            <p class="text-slate-400">ควบคุมโดยแท็บ <strong>DOM_ABSORPTION (BTC)</strong> ป้องกันสเปรดถ่างกลางคืน &gt; $20</p>
          </div>
          <div class="p-2.5 rounded-lg bg-slate-950/70 border border-blue-500/20">
            <div class="flex items-center justify-between text-blue-400 font-bold mb-1">
              <span>⚡ บอท 2: ETHUSD M1</span>
              <span class="text-[10px] bg-blue-500/20 px-1.5 py-0.2 rounded font-mono">ชนะ 62.5%</span>
            </div>
            <p class="text-slate-400">ควบคุมโดยแท็บ <strong>DOM_ABSORPTION (ETH)</strong> ดักจับ Ask/Bid Wall ด้วยเพดานสเปรด $2.2</p>
          </div>
          <div class="p-2.5 rounded-lg bg-slate-950/70 border border-emerald-500/20">
            <div class="flex items-center justify-between text-emerald-400 font-bold mb-1">
              <span>🏆 บอท 3: XAUUSD M1</span>
              <span class="text-[10px] bg-emerald-500/20 px-1.5 py-0.2 rounded font-mono">PF 1.75</span>
            </div>
            <p class="text-slate-400">ควบคุมโดยแท็บ <strong>DOM_ABSORPTION (XAU)</strong> ดักจับสภาพคล่องทองคำ M1 เพดาน $0.20</p>
          </div>
          <div class="p-2.5 rounded-lg bg-slate-950/70 border border-purple-500/20">
            <div class="flex items-center justify-between text-purple-400 font-bold mb-1">
              <span>📡 การ์ด 4: GOLD-PERP</span>
              <span class="text-[10px] bg-purple-500/20 px-1.5 py-0.2 rounded font-mono">RECORDER</span>
            </div>
            <p class="text-slate-400">ตัวบันทึก Depth L2 สด 24 ชม. กำลังเก็บสะสมข้อมูลสร้างโมเดล จึงยังไม่มีแท็บย้อนหลัง</p>
          </div>
        </div>
      </div>\n\n''' + target_hint

assert target_hint in html, "Could not find target_hint"
html = html.replace(target_hint, linkage_banner)

# 3. Update switchStrategy in JS
old_js_start = '''      const tabBtc = document.getElementById('tab-dom-abs-btc');
      const tabEth = document.getElementById('tab-dom-abs-eth');
      const tabRunner = document.getElementById('tab-runner');
      const tabSmc = document.getElementById('tab-smc');
      const tabFade = document.getElementById('tab-fade');
      const tabCompare = document.getElementById('tab-compare');
      
      [tabBtc, tabEth, tabRunner, tabSmc, tabFade, tabCompare].forEach(t => {'''

new_js_start = '''      const tabBtc = document.getElementById('tab-dom-abs-btc');
      const tabEth = document.getElementById('tab-dom-abs-eth');
      const tabXau = document.getElementById('tab-dom-abs-xau');
      const tabRunner = document.getElementById('tab-runner');
      const tabSmc = document.getElementById('tab-smc');
      const tabFade = document.getElementById('tab-fade');
      const tabCompare = document.getElementById('tab-compare');
      
      [tabBtc, tabEth, tabXau, tabRunner, tabSmc, tabFade, tabCompare].forEach(t => {'''

assert old_js_start in html, "Could not find old_js_start"
html = html.replace(old_js_start, new_js_start)

old_badges_js = '''      if (strat === 'dom_absorption_btc') {
        if (bHighlight) bHighlight.innerHTML = '🔥 BTCUSD (M1): วางกรอบดักวอลุ่มสถาบัน กำไร +$14.16 USD';
        if (bDate) bDate.innerHTML = '📅 สมุดคำสั่งสด L2: 31 ต.ค. - 01 พ.ย. 2026';
        if (bMode) bMode.innerHTML = '🛡️ เข้าทีละ 1 ไม้ · TP $50 / SL $25';
      } else if (strat === 'dom_absorption_eth') {
        if (bHighlight) bHighlight.innerHTML = '⚡ ETHUSD (M1): ซับแรงขาย Ask/Bid Wall กำไร +$16.16 USD';
        if (bDate) bDate.innerHTML = '📅 สมุดคำสั่งสด L2: 31 ต.ค. - 01 พ.ย. 2026';
        if (bMode) bMode.innerHTML = '🛡️ เข้าทีละ 1 ไม้ · TP $3.5 / SL $1.0';
      } else if (strat === 'dom_smart_runner') {'''

new_badges_js = '''      if (strat === 'dom_absorption_btc') {
        if (bHighlight) bHighlight.innerHTML = '🔥 BTCUSD (M1): ซับแรงดูดสภาพคล่อง L2 V2 กำไร +$5.34 USD (Win Rate 92.9%)';
        if (bDate) bDate.innerHTML = '📅 ข้อมูล DOM จริง 01 - 02 พ.ย. 2026 (2,020 แท่ง M1)';
        if (bMode) bMode.innerHTML = '🛡️ เข้าทีละ 1 ไม้ · TP $105 / SL $70 · เพดานสเปรด $20';
      } else if (strat === 'dom_absorption_eth') {
        if (bHighlight) bHighlight.innerHTML = '⚡ ETHUSD (M1): ซับแรงขาย Ask/Bid Wall V2 กำไร +$0.10 USD (Win Rate 62.5%)';
        if (bDate) bDate.innerHTML = '📅 ข้อมูล DOM จริง 01 - 02 พ.ย. 2026 (2,022 แท่ง M1)';
        if (bMode) bMode.innerHTML = '🛡️ เข้าทีละ 1 ไม้ · TP $3.0 / SL $1.5 · เพดานสเปรด $2.20';
      } else if (strat === 'dom_absorption_xau') {
        if (bHighlight) bHighlight.innerHTML = '🏆 XAUUSD (M1): ซับสภาพคล่องทองคำ L2 V2 กำไร +$0.06 USD (PF 1.75)';
        if (bDate) bDate.innerHTML = '📅 ข้อมูล DOM จริง 01 - 02 พ.ย. 2026 (722 นาที)';
        if (bMode) bMode.innerHTML = '🛡️ เข้าทีละ 1 ไม้ · TP $7.0 / SL $3.5 · เพดานสเปรด $0.15';
      } else if (strat === 'dom_smart_runner') {'''

assert old_badges_js in html, "Could not find old_badges_js"
html = html.replace(old_badges_js, new_badges_js)

# 4. Update tab active highlight
old_active_tab = '''        if (strat === 'dom_absorption_btc' && tabBtc) {
          tabBtc.className = "px-3 py-1.5 text-xs md:text-sm font-bold rounded-lg transition-all bg-amber-500 text-slate-950 shadow flex items-center gap-1.5";
        } else if (strat === 'dom_absorption_eth' && tabEth) {
          tabEth.className = "px-3 py-1.5 text-xs md:text-sm font-bold rounded-lg transition-all bg-blue-500 text-white shadow flex items-center gap-1.5";
        } else if (strat === 'dom_smart_runner' && tabRunner) {'''

new_active_tab = '''        if (strat === 'dom_absorption_btc' && tabBtc) {
          tabBtc.className = "px-3 py-1.5 text-xs md:text-sm font-bold rounded-lg transition-all bg-amber-500 text-slate-950 shadow flex items-center gap-1.5";
        } else if (strat === 'dom_absorption_eth' && tabEth) {
          tabEth.className = "px-3 py-1.5 text-xs md:text-sm font-bold rounded-lg transition-all bg-blue-500 text-white shadow flex items-center gap-1.5";
        } else if (strat === 'dom_absorption_xau' && tabXau) {
          tabXau.className = "px-3 py-1.5 text-xs md:text-sm font-bold rounded-lg transition-all bg-amber-500 text-slate-950 shadow flex items-center gap-1.5";
        } else if (strat === 'dom_smart_runner' && tabRunner) {'''

assert old_active_tab in html, "Could not find old_active_tab"
html = html.replace(old_active_tab, new_active_tab)

with open(path, 'w', encoding='utf-8') as f:
    f.write(html)

print("Updated docs/index.html successfully!")
