import os

p = r"d:\cbot-atgvt\docs\index.html"
with open(p, "r", encoding="utf-8") as f:
    text = f.read()

target = "แดชบอร์ด AI (ล่าสุด)"
idx = text.find(target)
if idx != -1:
    close_a = text.find("</a>", idx)
    if close_a != -1:
        insert_pos = close_a + 4
        nav_buttons = """
        <a href="research.html" class="px-3 py-1.5 rounded-lg text-slate-300 hover:text-white hover:bg-slate-800 transition border border-slate-700/80 bg-slate-900/90 shadow-sm flex items-center gap-1.5 cursor-pointer">
          <span>🔬</span> งานวิจัย (141 Papers)
        </a>
        <a href="chat_transcript.html" target="_blank" class="px-3 py-1.5 rounded-lg text-cyan-300 hover:text-white hover:bg-cyan-950/60 transition border border-cyan-800/60 bg-cyan-950/30 flex items-center gap-1.5 shadow-sm">
          <span>💬</span> บทสนทนาการวิจัย
        </a>"""
        new_text = text[:insert_pos] + nav_buttons + text[insert_pos:]
        with open(p, "w", encoding="utf-8") as f:
            f.write(new_text)
        print("Successfully inserted Research Tab into docs/index.html navbar!")
    else:
        print("Could not find </a> after target")
else:
    print("Could not find target text")
