import os
import sys
import json
import re

log_path = r"C:\Users\Strong Baesus PC1\.gemini\antigravity\brain\066c0b89-502c-4b32-b8ff-2f8201902c09\.system_generated\logs\transcript_full.jsonl"
out_html_path = r"docs\chat_transcript.html"

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

user_count = len([m for m in messages if m['role'] == 'user'])
ai_count = len([m for m in messages if m['role'] == 'assistant'])

json_data_escaped = json.dumps(messages, ensure_ascii=False)

html_page = f"""<!DOCTYPE html>
<html lang="th" class="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Backtest Lab · บทสนทนาการวิจัยฉบับเต็ม (Full Research Chat Transcript)</title>
  <link rel="stylesheet" href="style.css">
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/atom-one-dark.min.css">
  <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/katex.min.css">
  <script src="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/katex.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/contrib/auto-render.min.js"></script>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=Noto+Sans+Thai:wght@300;400;500;600;700&display=swap" rel="stylesheet">
  <script>
    tailwind.config = {{
      darkMode: 'class',
      theme: {{
        extend: {{
          fontFamily: {{
            sans: ['"Plus Jakarta Sans"', '"Noto Sans Thai"', 'sans-serif'],
            mono: ['Consolas', 'Monaco', 'monospace']
          }}
        }}
      }}
    }}
  </script>
  <style>
    body {{ background-color: #0b0f17; color: #f3f4f6; }}
    ::-webkit-scrollbar {{ width: 6px; height: 6px; }}
    ::-webkit-scrollbar-track {{ background: #0b0f17; }}
    ::-webkit-scrollbar-thumb {{ background: #1f2937; border-radius: 3px; }}
    ::-webkit-scrollbar-thumb:hover {{ background: #374151; }}
    
    /* Markdown Styles inside assistant bubbles */
    .prose-content {{ font-size: 0.9375rem; line-height: 1.75; color: #cbd5e1; }}
    .prose-content p {{ margin-bottom: 1rem; }}
    .prose-content p:last-child {{ margin-bottom: 0; }}
    .prose-content h1, .prose-content h2, .prose-content h3, .prose-content h4 {{
      color: #ffffff;
      font-weight: 700;
      margin-top: 1.5rem;
      margin-bottom: 0.75rem;
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }}
    .prose-content h1 {{ font-size: 1.35rem; color: #34d399; border-bottom: 1px solid #1e293b; padding-bottom: 0.5rem; }}
    .prose-content h2 {{ font-size: 1.2rem; color: #38bdf8; }}
    .prose-content h3 {{ font-size: 1.05rem; color: #a7f3d0; }}
    .prose-content ul, .prose-content ol {{ margin-left: 1.5rem; margin-bottom: 1rem; }}
    .prose-content ul {{ list-style-type: disc; }}
    .prose-content ol {{ list-style-type: decimal; }}
    .prose-content li {{ margin-bottom: 0.35rem; }}
    .prose-content strong {{ color: #ffffff; font-weight: 700; }}
    .prose-content em {{ color: #94a3b8; }}
    .prose-content blockquote {{
      border-left: 4px solid #10b981;
      background: rgba(16, 185, 129, 0.08);
      padding: 0.75rem 1rem;
      border-radius: 0 0.5rem 0.5rem 0;
      margin: 1rem 0;
      color: #93c5fd;
    }}
    .prose-content table {{
      width: 100%;
      border-collapse: collapse;
      margin: 1.25rem 0;
      font-size: 0.8125rem;
      overflow-x: auto;
      display: block;
    }}
    .prose-content th, .prose-content td {{
      border: 1px solid #1e293b;
      padding: 0.55rem 0.8rem;
      text-align: left;
    }}
    .prose-content th {{
      background: #0f172a;
      color: #34d399;
      font-weight: 700;
      white-space: nowrap;
    }}
    .prose-content tr:nth-child(even) {{
      background: rgba(15, 23, 42, 0.5);
    }}
    .prose-content code {{
      background: #1e293b;
      color: #38bdf8;
      padding: 0.15rem 0.4rem;
      border-radius: 0.25rem;
      font-family: Consolas, monospace;
      font-size: 0.85em;
    }}
    .prose-content pre {{
      background: #070a10 !important;
      border: 1px solid #1e293b;
      border-radius: 0.75rem;
      padding: 1rem;
      margin: 1rem 0;
      overflow-x: auto;
    }}
    .prose-content pre code {{
      background: none !important;
      color: #e2e8f0;
      padding: 0;
      font-size: 0.8125rem;
    }}
    .prose-content hr {{
      border: 0;
      border-top: 1px solid #1e293b;
      margin: 1.5rem 0;
    }}
    .prose-content a {{
      color: #38bdf8;
      text-decoration: underline;
      text-underline-offset: 2px;
    }}
    .prose-content a:hover {{
      color: #7dd3fc;
    }}
    .katex {{ font-size: 1.05em; color: #38bdf8; }}
  </style>
</head>
<body class="min-h-screen flex flex-col font-sans antialiased">

  <!-- TOP GLOBAL NAVIGATION -->
  <header class="sticky top-0 z-50 bg-[#111827]/90 backdrop-blur-md border-b border-slate-800/80 px-4 py-2.5 flex flex-wrap items-center justify-between gap-3">
    <div class="flex items-center gap-4 flex-wrap">
      <a class="brand font-bold text-white text-base tracking-wide flex items-center gap-2" href="index.html">
        <span class="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse"></span>
        Backtest Lab
      </a>
      <nav class="flex items-center gap-2 flex-wrap text-xs md:text-sm">
        <a href="index.html" class="px-3 py-1.5 rounded-lg text-slate-300 hover:text-white hover:bg-slate-800 transition border border-slate-700/80 bg-slate-900/90 shadow-sm flex items-center gap-1.5 cursor-pointer">
          <span>🚀</span> แดชบอร์ด AI (ล่าสุด)
        </a>
        <a href="research.html" class="px-3 py-1.5 rounded-lg text-slate-300 hover:text-white hover:bg-slate-800 transition border border-slate-700/80 bg-slate-900/90 shadow-sm flex items-center gap-1.5 cursor-pointer">
          <span>🔬</span> งานวิจัย (141 Papers & สรุปบทสนทนา)
        </a>
        <a href="chat_transcript.html" class="px-3 py-1.5 rounded-lg bg-cyan-500/15 text-cyan-400 border border-cyan-500/30 font-bold flex items-center gap-1.5 shadow-sm">
          <span>💬</span> บทสนทนาการวิจัยฉบับเต็ม
        </a>
      </nav>
    </div>
    <div class="flex items-center gap-2 text-xs">
      <span class="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-slate-700">
        <span class="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
        GitHub Pages
      </span>
      <a href="https://github.com/tgrockza55-ai/tgrockza55-ai-cbot-backtest-lab" target="_blank" class="text-slate-400 hover:text-white transition font-mono">
        tgrockza55-ai
      </a>
    </div>
  </header>

  <!-- MAIN CONTAINER -->
  <main class="flex-1 max-w-[1100px] w-full mx-auto px-3 sm:px-6 py-6 space-y-6">

    <!-- HERO HEADER CARD -->
    <div class="bg-gradient-to-br from-slate-900 via-slate-900 to-slate-950 border border-slate-800 rounded-2xl p-5 sm:p-7 shadow-xl relative overflow-hidden">
      <div class="absolute -top-24 -right-24 w-96 h-96 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none"></div>
      <div class="absolute -bottom-24 -left-24 w-96 h-96 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none"></div>

      <div class="relative z-10">
        <div class="flex flex-wrap items-center gap-2 mb-3">
          <span class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-cyan-500/15 text-cyan-400 border border-cyan-500/30 shadow-sm">
            <span>💬</span> บันทึกบทสนทนาการวิจัยฉบับเต็ม (Full Research Transcript)
          </span>
          <span class="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold bg-slate-800 text-slate-300 border border-slate-700">
            โปรเจกต์: Financial Research Paper Scraping
          </span>
          <span class="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-mono text-cyan-300 bg-cyan-950/60 border border-cyan-800/60">
            Conv ID: 066c0b89-502c-4b32-b8ff-2f8201902c09
          </span>
        </div>

        <h1 class="text-xl sm:text-2xl md:text-3xl font-extrabold text-white tracking-tight">
          บทสนทนาการค้นคว้า 141 เปเปอร์ & พัฒนาระบบ 13-Engine Quant Benchmark
        </h1>
        <p class="text-xs sm:text-sm text-slate-300 mt-2 max-w-4xl leading-relaxed">
          บันทึกการทำงานร่วมกันแบบ Pair Programming ระหว่างผู้ใช้กับ Antigravity AI ตั้งแต่การดึงเปเปอร์วิชาการระดับสถาบันจาก <strong>arXiv q-fin</strong>, การสกัดทฤษฎีคณิตศาสตร์การเงินสู่ <strong>13 Quant Engines</strong>, การรัน Benchmark บนข้อมูล Level 2 Order Book สด, จนถึงการ Optimize จูนหาพารามิเตอร์ทำกำไรสูงสุด
        </p>

        <!-- Stats Bar -->
        <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-4 pt-4 border-t border-slate-800">
          <div class="bg-slate-950/60 border border-slate-800/80 rounded-xl p-3">
            <span class="text-[11px] text-slate-400">จำนวนข้อความทั้งหมด</span>
            <div class="text-base sm:text-lg font-bold text-white mt-0.5">{len(messages)} ข้อความ</div>
          </div>
          <div class="bg-slate-950/60 border border-slate-800/80 rounded-xl p-3">
            <span class="text-[11px] text-slate-400">คำถาม / คำสั่งของผู้ใช้</span>
            <div class="text-base sm:text-lg font-bold text-blue-400 mt-0.5">{user_count} คำสั่ง</div>
          </div>
          <div class="bg-slate-950/60 border border-slate-800/80 rounded-xl p-3">
            <span class="text-[11px] text-slate-400">คำตอบวิเคราะห์เชิงลึก AI</span>
            <div class="text-base sm:text-lg font-bold text-emerald-400 mt-0.5">{ai_count} บทวิเคราะห์</div>
          </div>
          <div class="bg-slate-950/60 border border-slate-800/80 rounded-xl p-3">
            <span class="text-[11px] text-slate-400">ช่วงเวลาสนทนาจริง</span>
            <div class="text-xs sm:text-sm font-bold text-amber-300 mt-1">01 พ.ย. 2026 (15:45 - 18:31 น.)</div>
          </div>
        </div>
      </div>
    </div>

    <!-- CONTROLS & SEARCH BAR -->
    <div class="bg-slate-900 border border-slate-800 rounded-2xl p-4 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-3 sticky top-14 z-40 backdrop-blur-md bg-opacity-95">
      <!-- Search Input -->
      <div class="relative flex-1 max-w-lg">
        <span class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
          🔍
        </span>
        <input 
          type="text" 
          id="search-input" 
          placeholder="ค้นหาข้อความ (เช่น DeepLOB, OFI, Hawkes, Kelly, Benchmark, สเปรด)..." 
          class="w-full pl-9 pr-8 py-2 bg-slate-950 border border-slate-700/80 rounded-xl text-xs sm:text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 transition"
          oninput="handleSearch()"
        />
        <button id="clear-search-btn" onclick="clearSearch()" class="hidden absolute inset-y-0 right-0 pr-3 flex items-center text-slate-500 hover:text-slate-300 text-xs cursor-pointer">
          ✕
        </button>
      </div>

      <!-- Filter Buttons & Jump Actions -->
      <div class="flex flex-wrap items-center gap-2">
        <button id="filter-all" onclick="setFilter('all')" class="px-3 py-1.5 rounded-lg text-xs font-bold bg-cyan-500 text-slate-950 shadow transition cursor-pointer">
          ทั้งหมด ({len(messages)})
        </button>
        <button id="filter-user" onclick="setFilter('user')" class="px-3 py-1.5 rounded-lg text-xs font-medium text-slate-400 hover:text-white bg-slate-800/60 hover:bg-slate-800 transition cursor-pointer">
          👤 ผู้ใช้ ({user_count})
        </button>
        <button id="filter-ai" onclick="setFilter('assistant')" class="px-3 py-1.5 rounded-lg text-xs font-medium text-slate-400 hover:text-white bg-slate-800/60 hover:bg-slate-800 transition cursor-pointer">
          🤖 AI วิเคราะห์ ({ai_count})
        </button>
        <div class="h-4 w-px bg-slate-800 mx-1 hidden sm:block"></div>
        <button onclick="scrollToBottom()" class="px-2.5 py-1.5 rounded-lg text-xs font-medium text-slate-300 bg-slate-800 hover:bg-slate-700 transition flex items-center gap-1 cursor-pointer" title="เลื่อนลงล่างสุด">
          <span>⬇</span> ล่างสุด
        </button>
      </div>
    </div>

    <!-- CHAT MESSAGES STREAM CONTAINER -->
    <div id="chat-stream" class="space-y-6">
      <!-- Populated dynamically by JavaScript from pristine JSON script -->
    </div>

    <!-- Empty search result alert -->
    <div id="no-results" class="hidden text-center py-16 bg-slate-900/50 rounded-2xl border border-slate-800">
      <span class="text-4xl">🔍</span>
      <h3 class="text-base font-bold text-white mt-2">ไม่พบข้อความที่ตรงกับการค้นหา</h3>
      <p class="text-xs text-slate-400 mt-1">ลองใช้คำค้นอื่น เช่น Hawkes, OFI, Kelly, DeepLOB หรือกดล้างการค้นหา</p>
      <button onclick="clearSearch()" class="mt-4 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-xs text-slate-200 rounded-xl transition cursor-pointer">
        ล้างการค้นหา
      </button>
    </div>

  </main>

  <!-- FLOATING QUICK JUMP -->
  <div class="fixed bottom-6 right-6 flex flex-col gap-2 z-50">
    <button onclick="scrollToTop()" class="p-2.5 rounded-full bg-slate-800/90 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700 shadow-xl backdrop-blur transition cursor-pointer" title="ขึ้นบนสุด">
      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 15l7-7 7 7"></path></svg>
    </button>
    <button onclick="scrollToBottom()" class="p-2.5 rounded-full bg-slate-800/90 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700 shadow-xl backdrop-blur transition cursor-pointer" title="ลงล่างสุด">
      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path></svg>
    </button>
  </div>

  <!-- EMBEDDED PRISTINE JSON DATA SCRIPT (ZERO QUOTE COLLISION, ZERO ATTRIBUTE ESCAPING BUGS) -->
  <script id="chat-data" type="application/json">
{json_data_escaped}
  </script>

  <!-- APP SCRIPT -->
  <script>
    marked.setOptions({{
      gfm: true,
      breaks: true,
      highlight: function(code, lang) {{
        const language = hljs.getLanguage(lang) ? lang : 'plaintext';
        return hljs.highlight(code, {{ language }}).value;
      }}
    }});

    const CHAT_DATA = JSON.parse(document.getElementById('chat-data').textContent);
    let currentFilter = 'all';
    let searchQuery = '';

    function renderChat() {{
      const stream = document.getElementById('chat-stream');
      const noRes = document.getElementById('no-results');
      stream.innerHTML = '';

      const query = searchQuery.trim().toLowerCase();
      let visibleCount = 0;

      CHAT_DATA.forEach(msg => {{
        if (currentFilter !== 'all' && msg.role !== currentFilter) return;

        const matchesSearch = !query || msg.text.toLowerCase().includes(query);
        if (!matchesSearch) return;

        visibleCount++;
        const isUser = msg.role === 'user';
        const card = document.createElement('div');
        card.className = isUser ? 'flex justify-end' : 'flex justify-start w-full';
        card.id = 'msg-' + msg.id;

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
          // Assistant message rendered through marked
          let renderedMd = marked.parse(msg.text);

          // Add interactive Artifact Card for Message 36 (Step 521)
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

        // Render KaTeX for mathematical equations
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
      }});

      if (visibleCount === 0) {{
        noRes.classList.remove('hidden');
      }} else {{
        noRes.classList.add('hidden');
      }}
    }}

    function escapeHtml(text) {{
      const div = document.createElement('div');
      div.textContent = text;
      return div.innerHTML;
    }}

    function setFilter(filter) {{
      currentFilter = filter;
      const bAll = document.getElementById('filter-all');
      const bUser = document.getElementById('filter-user');
      const bAi = document.getElementById('filter-ai');

      [bAll, bUser, bAi].forEach(b => {{
        b.className = "px-3 py-1.5 rounded-lg text-xs font-medium text-slate-400 hover:text-white bg-slate-800/60 hover:bg-slate-800 transition cursor-pointer";
      }});

      if (filter === 'all') {{
        bAll.className = "px-3 py-1.5 rounded-lg text-xs font-bold bg-cyan-500 text-slate-950 shadow transition cursor-pointer";
      }} else if (filter === 'user') {{
        bUser.className = "px-3 py-1.5 rounded-lg text-xs font-bold bg-blue-600 text-white shadow transition cursor-pointer";
      }} else {{
        bAi.className = "px-3 py-1.5 rounded-lg text-xs font-bold bg-emerald-500 text-slate-950 shadow transition cursor-pointer";
      }}

      renderChat();
    }}

    function handleSearch() {{
      const input = document.getElementById('search-input');
      const clearBtn = document.getElementById('clear-search-btn');
      searchQuery = input.value;
      if (searchQuery.length > 0) {{
        clearBtn.classList.remove('hidden');
      }} else {{
        clearBtn.classList.add('hidden');
      }}
      renderChat();
    }}

    function clearSearch() {{
      const input = document.getElementById('search-input');
      const clearBtn = document.getElementById('clear-search-btn');
      input.value = '';
      searchQuery = '';
      clearBtn.classList.add('hidden');
      renderChat();
    }}

    function scrollToTop() {{
      window.scrollTo({{ top: 0, behavior: 'smooth' }});
    }}

    function scrollToBottom() {{
      window.scrollTo({{ top: document.body.scrollHeight, behavior: 'smooth' }});
    }}

    window.onload = () => {{
      renderChat();
      if (window.location.hash) {{
        setTimeout(() => {{
          const target = document.querySelector(window.location.hash);
          if (target) target.scrollIntoView({{ behavior: 'smooth' }});
        }}, 200);
      }}
    }};
  </script>
</body>
</html>
"""

with open(out_html_path, "w", encoding="utf-8") as f:
    f.write(html_page)

copy_path = r"zz_zz PAPER\web\chat_transcript.html"
if os.path.exists(os.path.dirname(copy_path)):
    with open(copy_path, "w", encoding="utf-8") as f:
        f.write(html_page)

print(f"Generated {out_html_path} ({len(html_page)} bytes) with KaTeX and Artifact card!")
