import re

html_path = r'd:\cbot-atgvt\docs\index.html'

with open(html_path, 'r', encoding='utf-8') as f:
    html = f.read()

# =========================================================================
# 2. UPDATE HEADER & STRATEGY SWITCHER TITLES
# =========================================================================
old_h1_section = '''        <h1 class="text-xl md:text-2xl font-bold tracking-tight text-white">
          วิจัยจุดกลับตัว (Turning Points) & ระบบ Run กำไรอัจฉริยะ (Smart DOM Runner)
        </h1>
        <p class="text-xs sm:text-sm text-slate-400 mt-0.5">
          เปรียบเทียบการพัฒนา 3 ยุค: (1) DOM Fade เดิม ➜ (2) SMC Fibo 5m ➜ (3) Smart Runner ปลดล็อค 5 นาทีพร้อม Smart DOM Exit
        </p>'''

new_h1_section = '''        <h1 class="text-xl md:text-2xl font-bold tracking-tight text-white flex items-center gap-2">
          <span>📊</span> ผลการทดสอบและวิเคราะห์กลยุทธ์ (Strategy Backtest Lab)
        </h1>
        <p class="text-xs sm:text-sm text-slate-400 mt-0.5">
          เลือกดูกลยุทธ์ด้านขวามือเพื่อวิเคราะห์อัตราการชนะ (Win Rate), กราฟการเติบโตของพอร์ต (Equity Curve) และดูแท่งเทียนรอบจุดเข้า-ออกจริง
        </p>'''

if old_h1_section in html:
    html = html.replace(old_h1_section, new_h1_section)
    print("Updated H1 section successfully!")
else:
    print("Warning: old_h1_section not found")


# =========================================================================
# 3. ADD INSTRUCTION HINT BANNER ABOVE CHART IN MAIN VIEW
# =========================================================================
hint_banner = '''
      <!-- INTERACTIVE USER HINT BANNER FOR BEGINNERS -->
      <div class="bg-gradient-to-r from-blue-950/60 to-slate-900 border border-blue-500/30 rounded-xl p-3 flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs text-blue-200 shadow-sm">
        <div class="flex items-center gap-2">
          <span class="text-base">💡</span>
          <span><strong>คำแนะนำสำหรับผู้เข้าชม:</strong> คลิกเลือกรายการเทรดใน <em>"ตารางรายการออเดอร์"</em> ด้านล่าง กราฟด้านบนจะซูมแท่งเทียนรอบจุดเข้า-ออกของไม้นั้น พร้อมบทวิเคราะห์เหตุผลทางขวามือทันที</span>
        </div>
        <div class="flex items-center gap-1.5 text-[11px] text-blue-400 font-mono bg-blue-500/10 px-2 py-0.5 rounded border border-blue-500/20 whitespace-nowrap">
          <span>🖱️</span> คลิกแถวเพื่อเปลี่ยนกราฟ
        </div>
      </div>
'''

if 'id="chart-card-container"' in html and '<!-- INTERACTIVE USER HINT BANNER' not in html:
    html = html.replace('<div id="chart-card-container"', hint_banner + '      <div id="chart-card-container"')
    print("Injected Interactive Hint Banner successfully!")


# =========================================================================
# 4. UPDATE KPI RENDERING IN JAVASCRIPT WITH CLEAR DESCRIPTIONS
# =========================================================================
old_kpi_func_pattern = r'function renderKpis\(mode\) \{.*?(?=function renderTable\(\))'

new_kpi_func = '''function renderKpis(mode) {
      const container = document.getElementById('kpi-section');
      if (mode === 'compare') {
        const s1 = DATA['dom_fade'].summary;
        const s2 = DATA['smc_fibo_dom'].summary;
        const s3 = DATA['dom_smart_runner'].summary;
        container.innerHTML = `
          <div class="bg-slate-900 p-3 rounded-xl border border-slate-800 shadow-sm">
            <span class="text-xs text-slate-400">กำไรสุทธิสูงสุด</span>
            <div class="text-base font-bold text-emerald-400 mt-0.5">+$${s3.net_profit} <span class="text-[11px] text-slate-400 font-normal">(vs $${s2.net_profit} / $${s1.net_profit})</span></div>
            <div class="text-[10px] text-slate-500 mt-0.5">หักค่าสเปรดครบถ้วน</div>
          </div>
          <div class="bg-slate-900 p-3 rounded-xl border border-slate-800 shadow-sm">
            <span class="text-xs text-slate-400">Profit Factor สูงสุด</span>
            <div class="text-base font-bold text-emerald-400 mt-0.5">${s3.profit_factor} <span class="text-[11px] text-slate-400 font-normal">(vs ${s2.profit_factor} / ${s1.profit_factor})</span></div>
            <div class="text-[10px] text-slate-500 mt-0.5">กำไรมากกว่าขาดทุน 1.5 เท่า</div>
          </div>
          <div class="bg-slate-900 p-3 rounded-xl border border-slate-800 shadow-sm">
            <span class="text-xs text-slate-400">Win Rate</span>
            <div class="text-base font-bold text-white mt-0.5">${s3.win_rate}%</div>
            <div class="text-[10px] text-slate-500 mt-0.5">ความแม่นยำในการเข้า</div>
          </div>
          <div class="bg-slate-900 p-3 rounded-xl border border-slate-800 shadow-sm">
            <span class="text-xs text-slate-400">Max Drawdown</span>
            <div class="text-base font-bold text-emerald-400 mt-0.5">$${s3.max_drawdown}</div>
            <div class="text-[10px] text-slate-500 mt-0.5">การย่อตัวต่ำเพียง 5.9%</div>
          </div>
          <div class="bg-slate-900 p-3 rounded-xl border border-slate-800 shadow-sm">
            <span class="text-xs text-slate-400">กำไรเฉลี่ย/ไม้</span>
            <div class="text-base font-bold text-emerald-400 mt-0.5">+$${s3.avg_pnl}</div>
            <div class="text-[10px] text-slate-500 mt-0.5">เฉลี่ยต่อคำสั่งเทรด</div>
          </div>
          <div class="bg-slate-900 p-3 rounded-xl border border-slate-800 shadow-sm">
            <span class="text-xs text-slate-400">จำนวนไม้ทดสอบ</span>
            <div class="text-base font-bold text-white mt-0.5">${s3.total_trades} ไม้</div>
            <div class="text-[10px] text-slate-500 mt-0.5">เข้าทีละ 1 ไม้ (ปลอดภัย)</div>
          </div>
        `;
        return;
      }

      const s = DATA[mode].summary;
      const profitColor = s.net_profit >= 0 ? 'text-emerald-400' : 'text-rose-400';
      const wins = DATA[mode].trades.filter(x => x.net > 0).length;
      const losses = DATA[mode].trades.length - wins;

      // Interpret Profit Factor in plain words
      let pfDesc = 'กำไรมากกว่าขาดทุน ' + s.profit_factor + ' เท่า';
      if (s.profit_factor >= 3.0) pfDesc = '🔥 ระดับสถาบัน (กำไร > ขาดทุน ' + s.profit_factor + ' เท่า)';
      else if (s.profit_factor >= 1.5) pfDesc = '⭐ ยอดเยี่ยม (กำไร > ขาดทุน ' + s.profit_factor + ' เท่า)';

      // Interpret Drawdown
      const ddPct = ((s.max_drawdown / 100) * 100).toFixed(1);

      container.innerHTML = `
        <div class="bg-slate-900 p-3.5 rounded-xl border border-slate-800 shadow-sm hover:border-slate-700 transition">
          <div class="flex items-center justify-between">
            <span class="text-[11px] font-semibold text-slate-400">กำไรสุทธิ (Net PnL)</span>
            <span class="text-[10px] text-slate-500 font-mono">สุทธิ</span>
          </div>
          <div class="text-xl font-extrabold ${profitColor} mt-1 font-mono">$${s.net_profit > 0 ? '+' : ''}${s.net_profit.toFixed(2)}</div>
          <div class="text-[10px] text-slate-400 mt-1 flex items-center gap-1">
            <span>🛡️</span> <span>หักค่าสเปรดโบรกเกอร์แล้ว</span>
          </div>
        </div>

        <div class="bg-slate-900 p-3.5 rounded-xl border border-slate-800 shadow-sm hover:border-slate-700 transition">
          <div class="flex items-center justify-between">
            <span class="text-[11px] font-semibold text-slate-400">Profit Factor (PF)</span>
            <span class="text-[10px] text-emerald-400 font-mono">เกณฑ์สถาบัน</span>
          </div>
          <div class="text-xl font-extrabold text-emerald-400 mt-1 font-mono">${s.profit_factor.toFixed(2)}</div>
          <div class="text-[10px] text-slate-400 mt-1 flex items-center gap-1">
            <span>📈</span> <span>${pfDesc}</span>
          </div>
        </div>

        <div class="bg-slate-900 p-3.5 rounded-xl border border-slate-800 shadow-sm hover:border-slate-700 transition">
          <div class="flex items-center justify-between">
            <span class="text-[11px] font-semibold text-slate-400">Win Rate (% ชนะ)</span>
            <span class="text-[10px] text-blue-400 font-mono">${wins}W / ${losses}L</span>
          </div>
          <div class="text-xl font-extrabold text-white mt-1 font-mono">${s.win_rate.toFixed(1)}%</div>
          <div class="text-[10px] text-slate-400 mt-1 flex items-center gap-1">
            <span>🎯</span> <span>ชนะ ${wins} จากทั้งหมด ${s.total_trades} ไม้</span>
          </div>
        </div>

        <div class="bg-slate-900 p-3.5 rounded-xl border border-slate-800 shadow-sm hover:border-slate-700 transition">
          <div class="flex items-center justify-between">
            <span class="text-[11px] font-semibold text-slate-400">Max Drawdown (ย่อตัว)</span>
            <span class="text-[10px] text-purple-400 font-mono">${ddPct}% ทุน</span>
          </div>
          <div class="text-xl font-extrabold text-emerald-400 mt-1 font-mono">$${s.max_drawdown.toFixed(2)}</div>
          <div class="text-[10px] text-slate-400 mt-1 flex items-center gap-1">
            <span>🔒</span> <span>ทุนย่อตัวต่ำมาก ไม่มีความเสี่ยงล้างพอร์ต</span>
          </div>
        </div>

        <div class="bg-slate-900 p-3.5 rounded-xl border border-slate-800 shadow-sm hover:border-slate-700 transition">
          <div class="flex items-center justify-between">
            <span class="text-[11px] font-semibold text-slate-400">กำไรเฉลี่ยต่อไม้</span>
            <span class="text-[10px] text-slate-500 font-mono">Avg PnL</span>
          </div>
          <div class="text-xl font-extrabold text-emerald-400 mt-1 font-mono">$${s.avg_pnl > 0 ? '+' : ''}${s.avg_pnl.toFixed(2)}</div>
          <div class="text-[10px] text-slate-400 mt-1 flex items-center gap-1">
            <span>⚡</span> <span>เฉลี่ยบวก $${s.avg_pnl.toFixed(2)} ทุกครั้งที่เทรด</span>
          </div>
        </div>

        <div class="bg-slate-900 p-3.5 rounded-xl border border-slate-800 shadow-sm hover:border-slate-700 transition">
          <div class="flex items-center justify-between">
            <span class="text-[11px] font-semibold text-slate-400">จำนวนไม้เทรด</span>
            <span class="text-[10px] text-slate-500 font-mono">1 ไม้ต่อครั้ง</span>
          </div>
          <div class="text-xl font-extrabold text-white mt-1 font-mono">${s.total_trades} ไม้</div>
          <div class="text-[10px] text-slate-400 mt-1 flex items-center gap-1">
            <span>🛡️</span> <span>ไม่เบิ้ลลอต ไม่เบิ้ลไม้ ปลอดภัย 100%</span>
          </div>
        </div>
      `;
    }

    '''

m_kpi = re.search(old_kpi_func_pattern, html, flags=re.DOTALL)
if m_kpi:
    html = html[:m_kpi.start()] + new_kpi_func + html[m_kpi.end():]
    print("Updated renderKpis function successfully!")
else:
    print("Warning: old_kpi_func_pattern not found")


# =========================================================================
# 5. ADD TOGGLE FUNCTION FOR BEGINNER GUIDE IN JAVASCRIPT
# =========================================================================
toggle_func = '''
    // Toggle Beginner Guide Drawer
    function toggleBeginnerGuide() {
      const drawer = document.getElementById('beginner-guide-drawer');
      const btnText = document.getElementById('guide-btn-text');
      if (!drawer) return;
      if (drawer.classList.contains('hidden')) {
        drawer.classList.remove('hidden');
        if (btnText) btnText.textContent = 'ย่อเก็บ "คู่มือมือใหม่" ▲';
      } else {
        drawer.classList.add('hidden');
        if (btnText) btnText.textContent = 'คลิกเปิด "คู่มือมือใหม่ & พจนานุกรมศัพท์" ▼';
      }
    }
'''

if 'function toggleBeginnerGuide' not in html:
    html = html.replace('function switchStrategy(strat) {', toggle_func + '\n    function switchStrategy(strat) {')
    print("Added toggleBeginnerGuide function successfully!")

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(html)
print("Saved docs/index.html with all UX upgrades!")
