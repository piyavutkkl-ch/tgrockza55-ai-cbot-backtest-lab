p = r"d:\cbot-atgvt\docs\chat_transcript.html"
with open(p, "r", encoding="utf-8") as f:
    text = f.read()

target = "<header>"
nav_bar = """<header>
    <div style="display: flex; gap: 12px; margin-bottom: 16px; flex-wrap: wrap;">
      <a href="index.html" style="padding: 8px 16px; border-radius: 8px; background: rgba(16, 185, 129, 0.15); color: #34d399; text-decoration: none; font-size: 13px; font-weight: bold; border: 1px solid rgba(16, 185, 129, 0.3);">🚀 กลับหน้าแดชบอร์ด AI</a>
      <a href="research.html" style="padding: 8px 16px; border-radius: 8px; background: rgba(56, 189, 248, 0.15); color: #38bdf8; text-decoration: none; font-size: 13px; font-weight: bold; border: 1px solid rgba(56, 189, 248, 0.3);">🔬 คลังวิจัย 141 เปเปอร์</a>
    </div>"""

if target in text:
    new_text = text.replace(target, nav_bar, 1)
    with open(p, "w", encoding="utf-8") as f:
        f.write(new_text)
    print("Successfully added navigation bar to chat_transcript.html!")
else:
    print("Target not found!")
