import re

html_path = r'd:\cbot-atgvt\docs\index.html'

with open(html_path, 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Update reasonBadge in renderTable
old_badge = """        let reasonBadge = '';
        if (t.reason === 'TP') reasonBadge = '<span class="px-1.5 py-0.5 rounded text-[10px] font-semibold bg-emerald-500/10 text-emerald-400">TP (เป้า $3.50)</span>';
        else if (t.reason === 'DOM_EXIT') reasonBadge = '<span class="px-1.5 py-0.5 rounded text-[10px] font-semibold bg-emerald-500/10 text-emerald-400">⚡ Smart DOM</span>';
        else if (t.reason === 'SL') reasonBadge = '<span class="px-1.5 py-0.5 rounded text-[10px] font-semibold bg-rose-500/10 text-rose-400">SL (ตัดขาดทุน)</span>';
        else reasonBadge = '<span class="px-1.5 py-0.5 rounded text-[10px] font-semibold bg-amber-500/10 text-amber-400">Time / Flat</span>';"""

new_badge = """        let reasonBadge = '';
        if (t.reason === 'TP') reasonBadge = '<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">🎯 TP (ชนเป้ากำไร)</span>';
        else if (t.reason === 'DOM_EXIT') reasonBadge = '<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-cyan-500/15 text-cyan-400 border border-cyan-500/30">⚡ Smart DOM ออก</span>';
        else if (t.reason === 'SL') reasonBadge = '<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-500/15 text-rose-400 border border-rose-500/30">🛑 SL (ตัดขาดทุน)</span>';
        else reasonBadge = '<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/15 text-amber-400 border border-amber-500/30">⏱️ Time Exit</span>';"""

if old_badge in html:
    html = html.replace(old_badge, new_badge)
    print("Updated reasonBadge in renderTable!")
else:
    print("Warning: old_badge not found")

# 2. Update banner reason in selectTrade
old_banner_reason = "${t.reason === 'TP' ? '🎯 Take Profit ($3.50)' : t.reason === 'DOM_EXIT' ? '⚡ Smart DOM Exit ปิดล็อกกำไร' : t.reason === 'SL' ? '🛑 Stop Loss ($1.80)' : '⏱️ ปิดตามเวลาฉุกเฉิน'}"
new_banner_reason = "${t.reason === 'TP' ? '🎯 Take Profit (ชนเป้ากำไร)' : t.reason === 'DOM_EXIT' ? '⚡ Smart DOM Exit ปิดล็อกกำไร' : t.reason === 'SL' ? '🛑 Stop Loss (ตัดขาดทุนตามระบบ)' : '⏱️ ปิดตามเวลาฉุกเฉิน'}"

if old_banner_reason in html:
    html = html.replace(old_banner_reason, new_banner_reason)
    print("Updated banner reason text!")
else:
    print("Warning: old_banner_reason not found")

# 3. Update 3 inspector cards headings in selectTrade
old_card1 = """            <div class="text-xs font-bold text-amber-400 mb-1 flex items-center gap-1">
              <span>📍</span> 1. โครงสร้างราคา & Fibonacci Golden Zone
            </div>"""

new_card1 = """            <div class="text-xs font-bold text-amber-400 mb-1.5 flex items-center justify-between">
              <span class="flex items-center gap-1.5"><span>🎯</span> 1. ทำไมบอทถึงเปิดออเดอร์นี้ (จุดเลี้ยวราคา)</span>
              <span class="text-[10px] text-slate-500 font-mono">Entry Trigger</span>
            </div>"""

old_card2 = """            <div class="text-xs font-bold text-blue-400 mb-1 flex items-center gap-1">
              <span>📊</span> 2. สภาพคล่อง & สมุดคำสั่ง (DOM)
            </div>"""

new_card2 = """            <div class="text-xs font-bold text-cyan-400 mb-1.5 flex items-center justify-between">
              <span class="flex items-center gap-1.5"><span>🧱</span> 2. สภาพคล่องสมุดคำสั่ง Level 2 (DOM Imbalance)</span>
              <span class="text-[10px] text-cyan-400/80 font-mono">Order Book</span>
            </div>"""

old_card3 = """            <div class="text-xs font-bold text-emerald-400 mb-1 flex items-center gap-1">
              <span>🏁</span> 3. ผลลัพธ์และบทเรียน (Analysis)
            </div>"""

new_card3 = """            <div class="text-xs font-bold text-emerald-400 mb-1.5 flex items-center justify-between">
              <span class="flex items-center gap-1.5"><span>🏁</span> 3. สรุปผลลัพธ์และบทเรียน (Trade Outcome)</span>
              <span class="text-[10px] text-slate-500 font-mono">Analysis</span>
            </div>"""

for old_c, new_c, name in [(old_card1, new_card1, "card 1"), (old_card2, new_card2, "card 2"), (old_card3, new_card3, "card 3")]:
    if old_c in html:
        html = html.replace(old_c, new_c)
        print(f"Updated {name} successfully!")
    else:
        print(f"Warning: {name} not found")

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(html)
print("Saved docs/index.html with inspector and table improvements!")
