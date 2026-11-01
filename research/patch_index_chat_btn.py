import sys
sys.stdout.reconfigure(encoding='utf-8')

file_path = r"d:\cbot-atgvt\zz_zz PAPER\web\index.html"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

target = '<button onclick="toggleEnsembleModal()"'
replacement = """<a href="chat_transcript.html" target="_blank" class="px-4 py-2 bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-500 hover:to-cyan-500 text-white rounded-lg text-sm font-semibold shadow-lg shadow-blue-900/30 transition-all flex items-center gap-2">
                <span>💬 ดูบทสนทนาการวิจัย (Full Chat)</span>
            </a>
            <button onclick="toggleEnsembleModal()" """

if target in content and 'chat_transcript.html' not in content:
    content = content.replace(target, replacement, 1)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("Updated index.html successfully with Chat link button.")
else:
    print("Target already updated or not found.")
