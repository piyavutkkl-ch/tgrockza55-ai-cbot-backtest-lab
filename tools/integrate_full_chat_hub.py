import re
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

log_path = r"C:\Users\Strong Baesus PC1\.gemini\antigravity\brain\066c0b89-502c-4b32-b8ff-2f8201902c09\.system_generated\logs\transcript_full.jsonl"
research_path = r"docs\research.html"

def clean_user_text(raw):
    m = re.search(r'<USER_REQUEST>(.*?)</USER_REQUEST>', raw, re.DOTALL)
    text = m.group(1).strip() if m else raw.strip()
    text = re.sub(r'@\[conversation:[^\]]+\]\s*', '', text)
    text = re.sub(r'</?[A-Z_]+>', '', text)
    return text.strip()

thai_months = ['ม.ค.', 'ก.พ.', 'มี.ค.', 'เม.ย.', 'พ.ค.', 'มิ.ย.', 'ก.ค.', 'ส.ค.', 'ก.ย.', 'ต.ค.', 'พ.ย.', 'ธ.ค.']

def format_thai_timestamp(iso_str):
    if not iso_str: return ''
    try:
        dt_part = iso_str[:19]
        y, m, d = int(dt_part[:4]), int(dt_part[5:7]), int(dt_part[8:10])
        hour, minute, sec = int(dt_part[11:13]), int(dt_part[14:16]), int(dt_part[17:19])
        hour += 7
        if hour >= 24:
            hour -= 24
            d += 1
        m_thai = thai_months[m - 1]
        return f"{d:02d} {m_thai} {y}, {hour:02d}:{minute:02d}:{sec:02d} น."
    except Exception:
        return iso_str[:19].replace('T', ' ')

messages = []
with open(log_path, 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if not line: continue
        try:
            data = json.loads(line)
            step_type = data.get('type')
            content = data.get('content', '')
            created_at = data.get('created_at', '')
            
            if step_type == 'USER_INPUT':
                txt = clean_user_text(content)
                if txt:
                    messages.append({
                        'id': len(messages) + 1,
                        'role': 'user',
                        'time': format_thai_timestamp(created_at),
                        'text': txt
                    })
            elif step_type == 'PLANNER_RESPONSE' and content:
                messages.append({
                    'id': len(messages) + 1,
                    'role': 'assistant',
                    'time': format_thai_timestamp(created_at),
                    'text': content
                })
        except Exception:
            continue

print(f"Extracted {len(messages)} messages ({len([m for m in messages if m['role']=='user'])} user, {len([m for m in messages if m['role']=='assistant'])} assistant)")

chat_json_str = json.dumps(messages, ensure_ascii=False)

with open(research_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add CDNs to <head> if not already present
head_cdns = """  <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/atom-one-dark.min.css">
  <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/katex.min.css">
  <script src="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/katex.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/contrib/auto-render.min.js"></script>
"""
if "marked.min.js" not in content:
    content = content.replace("<head>\n", "<head>\n" + head_cdns)

# 2. Add prose styles
prose_styles = """
    /* Markdown Styles inside embedded chat bubbles */
    .prose-content { font-size: 0.9375rem; line-height: 1.75; color: #cbd5e1; }
    .prose-content p { margin-bottom: 1rem; }
    .prose-content p:last-child { margin-bottom: 0; }
    .prose-content h1, .prose-content h2, .prose-content h3, .prose-content h4 {
      color: #ffffff;
      font-weight: 700;
      margin-top: 1.5rem;
      margin-bottom: 0.75rem;
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }
    .prose-content h1 { font-size: 1.35rem; color: #34d399; border-bottom: 1px solid #1e293b; padding-bottom: 0.5rem; }
    .prose-content h2 { font-size: 1.2rem; color: #38bdf8; }
    .prose-content h3 { font-size: 1.05rem; color: #a7f3d0; }
    .prose-content ul, .prose-content ol { margin-left: 1.5rem; margin-bottom: 1rem; }
    .prose-content ul { list-style-type: disc; }
    .prose-content ol { list-style-type: decimal; }
    .prose-content li { margin-bottom: 0.35rem; }
    .prose-content strong { color: #ffffff; font-weight: 700; }
    .prose-content em { color: #94a3b8; }
    .prose-content blockquote {
      border-left: 4px solid #10b981;
      background: rgba(16, 185, 129, 0.08);
      padding: 0.75rem 1rem;
      border-radius: 0 0.5rem 0.5rem 0;
      margin: 1rem 0;
      color: #93c5fd;
    }
    .prose-content table {
      width: 100%;
      border-collapse: collapse;
      margin: 1.25rem 0;
      font-size: 0.8125rem;
      overflow-x: auto;
      display: block;
    }
    .prose-content th, .prose-content td {
      border: 1px solid #1e293b;
      padding: 0.55rem 0.8rem;
      text-align: left;
    }
    .prose-content th {
      background: #0f172a;
      color: #34d399;
      font-weight: 700;
      white-space: nowrap;
    }
    .prose-content tr:nth-child(even) {
      background: rgba(15, 23, 42, 0.5);
    }
    .prose-content code {
      background: #1e293b;
      color: #38bdf8;
      padding: 0.15rem 0.4rem;
      border-radius: 0.25rem;
      font-family: Consolas, monospace;
      font-size: 0.85em;
    }
    .prose-content pre {
      background: #070a10 !important;
      border: 1px solid #1e293b;
      border-radius: 0.75rem;
      padding: 1rem;
      margin: 1rem 0;
      overflow-x: auto;
    }
    .prose-content pre code {
      background: none !important;
      color: #e2e8f0;
      padding: 0;
      font-size: 0.8125rem;
    }
    .prose-content hr {
      border: 0;
      border-top: 1px solid #1e293b;
      margin: 1.5rem 0;
    }
    .prose-content a {
      color: #38bdf8;
      text-decoration: underline;
      text-underline-offset: 2px;
    }
    .prose-content a:hover {
      color: #7dd3fc;
    }
    .katex { font-size: 1.05em; color: #38bdf8; }
"""
if ".prose-content" not in content:
    content = content.replace("</style>", prose_styles + "\n  </style>")

# 3. Update Tab button label
content = content.replace(
    '<span>💬</span> 1. สรุปการสนทนา & ไทม์ไลน์การวิจัย',
    '<span>💬</span> 1. บทสนทนาการวิจัยฉบับเต็ม & ไทม์ไลน์'
)

# 4. Modify Tab 1 header & switcher
tab1_old_start = """    <!-- ========================================================================= -->
    <!-- TAB 1: CONVERSATION SUMMARY & RESEARCH TIMELINE -->
    <!-- ========================================================================= -->
    <div id="tab-content-timeline" class="space-y-6">
      
      <!-- Timeline Header Card -->
      <div class="bg-dark-card border border-dark-border rounded-2xl p-6 shadow-xl">
        <div class="flex flex-wrap items-center justify-between gap-4 mb-4">
          <div>
            <h3 class="text-lg font-bold text-white flex items-center gap-2">
              <span>📜</span> สรุปบันทึกการสนทนาและขั้นตอนการวิจัย (Research Journey Timeline)
            </h3>
            <p class="text-xs text-slate-400 mt-1">
              บทสรุปการพูดคุย คำถาม-คำตอบ และการส่งต่อผลงานระหว่างผู้ใช้กับ Antigravity ในโปรเจกต์ Financial Research Paper Scraping
            </p>
          </div>
          <a href="chat_transcript.html" target="_blank" class="px-3.5 py-1.5 rounded-lg bg-blue-500/10 text-blue-400 hover:bg-blue-500/20 border border-blue-500/30 text-xs font-semibold flex items-center gap-1.5 transition">
            <span>🌐</span> เปิดหน้าต่างแชทเต็ม (120+ KB)
          </a>
        </div>"""

tab1_new_start = """    <!-- ========================================================================= -->
    <!-- TAB 1: CONVERSATION SUMMARY & RESEARCH TIMELINE -->
    <!-- ========================================================================= -->
    <div id="tab-content-timeline" class="space-y-6">
      
      <!-- Timeline Header & View Mode Switcher -->
      <div class="bg-dark-card border border-dark-border rounded-2xl p-5 sm:p-6 shadow-xl">
        <div class="flex flex-wrap items-center justify-between gap-4 mb-4 border-b border-slate-800 pb-4">
          <div>
            <div class="flex items-center gap-2">
              <span class="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-cyan-500/15 text-cyan-400 border border-cyan-500/30">
                <span>💬</span> บทสนทนาการวิจัยฉบับเต็ม (Full Research Transcript)
              </span>
              <span class="text-xs font-mono text-slate-400">36 ข้อความจริง (ไม่มีตัดทอน)</span>
            </div>
            <h3 class="text-lg font-bold text-white flex items-center gap-2 mt-1">
              <span>📜</span> บทสนทนาการค้นคว้า 141 เปเปอร์ & พัฒนาระบบ 13-Engine Quant Benchmark
            </h3>
            <p class="text-xs text-slate-400 mt-0.5">
              บทสนทนา Pair Programming จริงระหว่างผู้ใช้กับ Antigravity ตั้งแต่การสกัดเปเปอร์วิชาการจนถึงรัน Backtest ครบ 14 โมดูล
            </p>
          </div>
          
          <div class="flex items-center gap-2">
            <a href="chat_transcript.html" target="_blank" class="px-3.5 py-2 rounded-xl bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-500 hover:to-cyan-500 text-white text-xs font-semibold shadow-md transition flex items-center gap-1.5">
              <span>↗️</span> เปิดหน้าต่างแชทเต็มจอ (Standalone)
            </a>
          </div>
        </div>

        <!-- Inner View Switcher: Live Chat Stream vs 6-Phase Timeline -->
        <div class="flex items-center justify-between flex-wrap gap-3">
          <div class="flex items-center bg-slate-950 p-1 rounded-xl border border-slate-800 shadow-inner">
            <button id="view-mode-chat" onclick="switchTimelineView('chat')" class="px-4 py-2 rounded-lg text-xs font-bold bg-cyan-500 text-slate-950 shadow transition cursor-pointer flex items-center gap-1.5">
              <span>💬</span> อ่านบทสนทนาตัวเต็ม (36 ข้อความ)
            </button>
            <button id="view-mode-timeline" onclick="switchTimelineView('timeline')" class="px-4 py-2 rounded-lg text-xs font-medium text-slate-400 hover:text-white transition cursor-pointer flex items-center gap-1.5">
              <span>📜</span> สรุปไทม์ไลน์ 6 เฟส
            </button>
          </div>

          <!-- Quick search for chat view -->
          <div id="chat-search-wrap" class="relative w-full sm:w-72">
            <span class="absolute inset-y-0 left-0 pl-2.5 flex items-center pointer-events-none text-slate-500 text-xs">🔍</span>
            <input 
              type="text" 
              id="chatSearchInput" 
              placeholder="ค้นหาในแชท (เช่น Hawkes, OFI, Kelly)..." 
              class="w-full pl-8 pr-3 py-1.5 bg-slate-950 border border-slate-800 rounded-xl text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500 transition"
              oninput="handleEmbeddedChatSearch()"
            />
          </div>
        </div>
      </div>

      <!-- VIEW A: EMBEDDED LIVE CHAT STREAM -->
      <div id="view-container-chat" class="space-y-5">
        <div id="embeddedChatStream" class="space-y-5">
          <!-- Populated by JavaScript -->
        </div>
      </div>

      <!-- VIEW B: 6 PHASES TIMELINE CONTAINER (Hidden by default, toggleable) -->
      <div id="view-container-timeline" class="hidden bg-dark-card border border-dark-border rounded-2xl p-6 shadow-xl">
        <div class="mb-5 pb-3 border-b border-slate-800">
          <h4 class="text-base font-bold text-white flex items-center gap-2">
            <span>📜</span> สรุปบันทึกขั้นตอนการวิจัย 6 เฟส (Research Journey Timeline)
          </h4>
          <p class="text-xs text-slate-400 mt-1">
            สรุปไทม์ไลน์สังเขปของโปรเจกต์ Financial Research Paper Scraping ตั้งแต่วิเคราะห์เปเปอร์ สกัดคณิตศาสตร์ ถึงสร้างบอท cTrader
          </p>
        </div>"""

assert tab1_old_start in content, "tab1_old_start not found in research.html"
content = content.replace(tab1_old_start, tab1_new_start, 1)

# 5. Inject Embedded Chat Data & Scripts at bottom
chat_script_injection = f"""
  <!-- EMBEDDED PRISTINE RESEARCH CHAT DATA SCRIPT -->
  <script id="embedded-chat-data" type="application/json">
{chat_json_str}
  </script>

  <script>
    function escapeHtml(str) {{
      if (!str) return '';
      return str
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
    }}

    // Configure marked with highlight.js
    if (typeof marked !== 'undefined') {{
      marked.setOptions({{
        breaks: true,
        gfm: true,
        highlight: function(code, lang) {{
          if (typeof hljs !== 'undefined') {{
            if (lang && hljs.getLanguage(lang)) {{
              try {{
                return hljs.highlight(code, {{ language: lang }}).value;
              }} catch (e) {{}}
            }}
            return hljs.highlightAuto(code).value;
          }}
          return code;
        }}
      }});
    }}

    const EMBEDDED_CHAT = JSON.parse(document.getElementById('embedded-chat-data').textContent);
    let embeddedChatSearch = '';
    let currentTimelineView = 'chat';

    function switchTimelineView(mode) {{
      currentTimelineView = mode;
      const bChat = document.getElementById('view-mode-chat');
      const bTimeline = document.getElementById('view-mode-timeline');
      const vChat = document.getElementById('view-container-chat');
      const vTimeline = document.getElementById('view-container-timeline');
      const sWrap = document.getElementById('chat-search-wrap');

      if (mode === 'chat') {{
        bChat.className = "px-4 py-2 rounded-lg text-xs font-bold bg-cyan-500 text-slate-950 shadow transition cursor-pointer flex items-center gap-1.5";
        bTimeline.className = "px-4 py-2 rounded-lg text-xs font-medium text-slate-400 hover:text-white transition cursor-pointer flex items-center gap-1.5";
        vChat.classList.remove('hidden');
        vTimeline.classList.add('hidden');
        if (sWrap) sWrap.classList.remove('hidden');
      }} else {{
        bTimeline.className = "px-4 py-2 rounded-lg text-xs font-bold bg-emerald-500 text-slate-950 shadow transition cursor-pointer flex items-center gap-1.5";
        bChat.className = "px-4 py-2 rounded-lg text-xs font-medium text-slate-400 hover:text-white transition cursor-pointer flex items-center gap-1.5";
        vTimeline.classList.remove('hidden');
        vChat.classList.add('hidden');
        if (sWrap) sWrap.classList.add('hidden');
      }}
    }}

    function renderEmbeddedChat() {{
      const stream = document.getElementById('embeddedChatStream');
      if (!stream) return;
      stream.innerHTML = '';

      const query = embeddedChatSearch.trim().toLowerCase();

      EMBEDDED_CHAT.forEach(msg => {{
        if (query && !msg.text.toLowerCase().includes(query)) return;

        const isUser = msg.role === 'user';
        const card = document.createElement('div');
        card.className = isUser ? 'flex justify-end' : 'flex justify-start w-full';
        card.id = 'embedded-msg-' + msg.id;

        if (isUser) {{
          card.innerHTML = `
            <div class="max-w-[85%] sm:max-w-[75%] bg-gradient-to-br from-blue-950/80 via-slate-900 to-slate-900 border border-blue-500/40 rounded-2xl rounded-tr-sm p-4 sm:p-5 shadow-lg">
              <div class="flex items-center justify-between gap-3 border-b border-blue-500/20 pb-2 mb-2.5">
                <span class="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-blue-600 text-white shadow-sm">
                  <span>👤</span> USER (ผู้ใช้งาน)
                </span>
                <span class="text-[11px] font-mono text-blue-300/80">${{msg.time}}</span>
              </div>
              <div class="text-sm sm:text-base text-slate-100 whitespace-pre-wrap leading-relaxed font-sans">
                ${{escapeHtml(msg.text)}}
              </div>
            </div>
          `;
        }} else {{
          let renderedMd = typeof marked !== 'undefined' ? marked.parse(msg.text) : msg.text;
          let artifactHtml = '';
          if (msg.id === 36) {{
            artifactHtml = `
              <div class="mt-5 p-4 rounded-xl bg-slate-950/90 border border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-md hover:border-slate-700 transition">
                <div class="flex items-start gap-3">
                  <div class="p-2.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xl">📄</div>
                  <div>
                    <div class="font-bold text-white text-sm">All Modules Max Profit Backtest</div>
                    <p class="text-xs text-slate-400 mt-0.5 leading-relaxed">
                      Comprehensive Backtest Report of All Discovered Max-Profit Methods across all 14 Quant Modules (56 methods tested), identifying the highest alpha winners and key microstructure mechanics.
                    </p>
                  </div>
                </div>
                <div class="flex items-center gap-2 self-end sm:self-center shrink-0">
                  <span class="text-[11px] font-mono text-emerald-400 bg-emerald-950/60 px-2 py-0.5 rounded border border-emerald-800/40 font-bold">+927 -0</span>
                  <a href="data/all_modules_max_profit_backtest.md" target="_blank" class="px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow transition flex items-center gap-1">
                    <span>📖</span> เปิดอ่านรีพอร์ต
                  </a>
                </div>
              </div>
            `;
          }}

          card.innerHTML = `
            <div class="w-full bg-[#111827]/90 border border-slate-800 rounded-2xl rounded-tl-sm p-5 sm:p-7 shadow-xl hover:border-slate-700/80 transition">
              <div class="flex items-center justify-between gap-3 border-b border-slate-800 pb-3 mb-4 flex-wrap">
                <div class="flex items-center gap-2">
                  <span class="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 shadow-sm">
                    <span>🤖</span> ANTIGRAVITY (AI QUANT)
                  </span>
                  <span class="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400">
                    #${{msg.id}}
                  </span>
                </div>
                <span class="text-xs font-mono text-slate-400">${{msg.time}}</span>
              </div>
              <div class="prose-content">
                ${{renderedMd}}
              </div>
              ${{artifactHtml}}
            </div>
          `;
        }}

        stream.appendChild(card);

        if (typeof renderMathInElement !== 'undefined') {{
          try {{
            renderMathInElement(card, {{
              delimiters: [
                {{left: '$$', right: '$$', display: true}},
                {{left: '$', right: '$', display: false}},
                {{left: '\\\\(', right: '\\\\)', display: false}},
                {{left: '\\\\[', right: '\\\\]', display: true}}
              ],
              throwOnError: false
            }});
          }} catch(e) {{}}
        }}
      }});
    }}

    function handleEmbeddedChatSearch() {{
      const inp = document.getElementById('chatSearchInput');
      embeddedChatSearch = inp ? inp.value : '';
      renderEmbeddedChat();
    }}
  </script>
"""

content = content.replace("</body>", chat_script_injection + "\n</body>")
content = content.replace("filterStrategies();", "filterStrategies();\n        renderEmbeddedChat();")

with open(research_path, "w", encoding="utf-8") as f:
    f.write(content)

print(f"Successfully integrated embedded full chat into Tab 1 of {research_path}!")
