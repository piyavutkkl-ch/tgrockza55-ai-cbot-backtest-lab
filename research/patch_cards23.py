html_path = r'd:\cbot-atgvt\docs\index.html'

with open(html_path, 'r', encoding='utf-8') as f:
    text = f.read()

old_c2 = """            <div class="text-xs font-bold text-blue-400 mb-1 flex items-center gap-1">
              <span>📊</span> 2. สภาพคล่อง Order Book & DOM จริง
            </div>"""

new_c2 = """            <div class="text-xs font-bold text-cyan-400 mb-1.5 flex items-center justify-between">
              <span class="flex items-center gap-1.5"><span>🧱</span> 2. สภาพคล่องสมุดคำสั่ง Level 2 (DOM Imbalance)</span>
              <span class="text-[10px] text-cyan-400/80 font-mono">Order Book</span>
            </div>"""

old_c3 = """            <div class="text-xs font-bold text-emerald-400 mb-1 flex items-center gap-1">
              <span>🔍</span> 3. ทำไมถึงได้กำไร/ขาดทุนตรงนี้
            </div>"""

new_c3 = """            <div class="text-xs font-bold text-emerald-400 mb-1.5 flex items-center justify-between">
              <span class="flex items-center gap-1.5"><span>🏁</span> 3. ทำไมถึงได้กำไร/ขาดทุนตรงนี้ (บทเรียน)</span>
              <span class="text-[10px] text-slate-500 font-mono">Outcome</span>
            </div>"""

if old_c2 in text:
    text = text.replace(old_c2, new_c2)
    print("Replaced card 2!")
else:
    print("Warning: old_c2 not matched")

if old_c3 in text:
    text = text.replace(old_c3, new_c3)
    print("Replaced card 3!")
else:
    print("Warning: old_c3 not matched")

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(text)
