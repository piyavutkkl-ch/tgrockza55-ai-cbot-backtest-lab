import os
import sys
import json
import re
import time
import hashlib
import shutil
import subprocess
from datetime import datetime, timezone

sys.stdout.reconfigure(encoding='utf-8')

LOG_PATH = r"C:\Users\Strong Baesus PC1\.gemini\antigravity\brain\066c0b89-502c-4b32-b8ff-2f8201902c09\.system_generated\logs\transcript_full.jsonl"
OUT_CHAT_PATH = r"docs\chat_transcript.html"
OUT_RESEARCH_PATH = r"docs\research.html"
OUT_LOCAL_PATH = r"zz_zz PAPER\web\chat_transcript.html"
STATE_FILE = r"data\research_chat_sync_state.json"
REPO_ROOT = r"d:\cbot-atgvt"
MEDIA_SRC_DIR = r"C:\Users\Strong Baesus PC1\.gemini\antigravity\brain\066c0b89-502c-4b32-b8ff-2f8201902c09\.user_uploaded"
MEDIA_DST_DIR = r"docs\media"
LOCAL_MEDIA_DST_DIR = r"zz_zz PAPER\web\media"

THAI_MONTHS = ['ม.ค.', 'ก.พ.', 'มี.ค.', 'เม.ย.', 'พ.ค.', 'มิ.ย.', 'ก.ค.', 'ส.ค.', 'ก.ย.', 'ต.ค.', 'พ.ย.', 'ธ.ค.']

def format_thai_timestamp(iso_str):
    if not iso_str:
        return ''
    try:
        dt_part = iso_str[:19]
        y, m, d = int(dt_part[:4]), int(dt_part[5:7]), int(dt_part[8:10])
        hour, minute, sec = int(dt_part[11:13]), int(dt_part[14:16]), int(dt_part[17:19])
        hour += 7
        if hour >= 24:
            hour -= 24
            d += 1
        m_thai = THAI_MONTHS[m - 1]
        return f"{d:02d} {m_thai} {y}, {hour:02d}:{minute:02d}:{sec:02d} น."
    except Exception:
        return iso_str[:19].replace('T', ' ')

def clean_user_text(raw):
    m = re.search(r'<USER_REQUEST>(.*?)</USER_REQUEST>', raw, re.DOTALL)
    text = m.group(1).strip() if m else raw.strip()
    text = re.sub(r'@\[conversation:[^\]]+\]\s*', '', text)
    text = re.sub(r'</?[A-Z_]+>', '', text)
    return text.strip()

def extract_messages():
    if not os.path.exists(LOG_PATH):
        return []

    # Sync uploaded media files
    os.makedirs(MEDIA_DST_DIR, exist_ok=True)
    os.makedirs(LOCAL_MEDIA_DST_DIR, exist_ok=True)
    if os.path.exists(MEDIA_SRC_DIR):
        for fname in os.listdir(MEDIA_SRC_DIR):
            s_file = os.path.join(MEDIA_SRC_DIR, fname)
            if os.path.isfile(s_file):
                shutil.copy2(s_file, os.path.join(MEDIA_DST_DIR, fname))
                shutil.copy2(s_file, os.path.join(LOCAL_MEDIA_DST_DIR, fname))

    raw_turns = []
    current_user = None
    current_ai_list = []

    with open(LOG_PATH, 'r', encoding='utf-8') as f:
        for idx, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                stype = data.get('type')
                content = data.get('content', '')
                created_at = data.get('created_at', '')
                media = data.get('media', [])

                if stype == 'USER_INPUT':
                    if current_user is not None:
                        raw_turns.append((current_user, current_ai_list))
                    current_user = {
                        'line': idx,
                        'time': created_at,
                        'content': content,
                        'media': media
                    }
                    current_ai_list = []
                elif stype == 'PLANNER_RESPONSE' and content:
                    current_ai_list.append({
                        'line': idx,
                        'time': created_at,
                        'content': content
                    })
            except Exception:
                continue

    if current_user is not None:
        raw_turns.append((current_user, current_ai_list))

    messages = []
    
    for turn_idx, (user_step, ai_steps) in enumerate(raw_turns):
        user_txt = clean_user_text(user_step['content'])
        user_media_url = None
        if user_step.get('media'):
            med = user_step['media'][0]
            uri = med.get('uri', '')
            fname = os.path.basename(uri)
            user_media_url = f"media/{fname}"
            if not user_txt:
                user_txt = "📷 (ภาพหน้าจอแนบ: เมนู Antigravity สอบถามวิธีแชร์ลิงก์บทสนทนาออกสู่ภายนอก)"

        # Append User Message
        if user_txt or user_media_url:
            messages.append({
                'id': len(messages) + 1,
                'turn': turn_idx + 1,
                'role': 'user',
                'time': format_thai_timestamp(user_step['time']),
                'text': user_txt,
                'media': user_media_url
            })

        # Process AI Steps in this turn
        if not ai_steps:
            continue

        if len(ai_steps) > 1 and max(len(a['content']) for a in ai_steps) < 500:
            combined_txt = "\n\n".join(a['content'] for a in ai_steps)
            messages.append({
                'id': len(messages) + 1,
                'turn': turn_idx + 1,
                'role': 'assistant',
                'time': format_thai_timestamp(ai_steps[-1]['time']),
                'text': combined_txt,
                'steps': [a['content'] for a in ai_steps],
                'artifact': None
            })
        else:
            final_step = ai_steps[-1]
            inter_steps = [a['content'] for a in ai_steps[:-1]]

            artifact = None
            line_no = final_step['line']
            if line_no in [416, 420]:
                artifact = {
                    'icon': '📊',
                    'title': '13-Engine Quant Benchmark Scorecard',
                    'summary': 'Detailed 13-Engine Quant Benchmark Scorecard on real Level 2 DOM Scraping datasets (BTCUSD, ETHUSD, GOLD-PERP), highlighting win rates, profit factors, net profits, and market microstructure findings.',
                    'badge': '141 papers tested • +1,240 -0',
                    'url': 'data/13_engine_benchmark_scorecard.md'
                }
            elif line_no in [472, 476]:
                artifact = {
                    'icon': '⚙️',
                    'title': '13-Engine Optimization Report & cTrader Guide',
                    'summary': 'Complete 13-Engine Step-by-Step Optimization Report and cTrader Automate Optimization Parameter Guide.',
                    'badge': '13 engines • +630 -0',
                    'url': 'data/13_engine_optimization_report.md'
                }
            elif line_no in [516, 522]:
                artifact = {
                    'icon': '📄',
                    'title': 'All Modules Max Profit Backtest',
                    'summary': 'Comprehensive Backtest Report of All Discovered Max-Profit Methods across all 14 Quant Modules (56 methods tested), identifying the highest alpha winners and key microstructure mechanics.',
                    'badge': '2 files changed • +927 -0',
                    'url': 'data/all_modules_max_profit_backtest.md'
                }

            messages.append({
                'id': len(messages) + 1,
                'turn': turn_idx + 1,
                'role': 'assistant',
                'time': format_thai_timestamp(final_step['time']),
                'text': final_step['content'],
                'steps': inter_steps,
                'artifact': artifact
            })

    return messages

def build_chat_transcript_html(messages):
    user_count = len([m for m in messages if m['role'] == 'user'])
    ai_count = len([m for m in messages if m['role'] == 'assistant'])
    time_span = "01 พ.ย. 2026 - ปัจจุบัน"
    if messages:
        first_t = messages[0]['time'].split(',')[0] if ',' in messages[0]['time'] else messages[0]['time']
        last_t = messages[-1]['time'].split(',')[0] if ',' in messages[-1]['time'] else messages[-1]['time']
        time_span = f"{first_t} - {last_t}"

    chat_json_str = json.dumps(messages, ensure_ascii=False)

    html = f"""<!DOCTYPE html>
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

  <!-- TOP NAVBAR -->
  <header class="h-14 border-b border-slate-800 bg-slate-900/80 backdrop-blur sticky top-0 z-40 px-4 sm:px-6 flex items-center justify-between">
    <div class="flex items-center gap-3">
      <div class="flex items-center gap-2">
        <span class="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse"></span>
        <span class="font-extrabold tracking-tight text-white text-base">Backtest Lab</span>
      </div>
      <span class="text-slate-600 hidden sm:inline">|</span>
      <nav class="hidden md:flex items-center gap-2 text-xs">
        <a href="index.html" class="px-2.5 py-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition flex items-center gap-1.5">
          <span>🚀</span> แดชบอร์ด AI (ล่าสุด)
        </a>
        <a href="research.html" class="px-2.5 py-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition flex items-center gap-1.5">
          <span>🔬</span> งานวิจัย (141 Papers & สรุปบทสนทนา)
        </a>
        <a href="chat_transcript.html" class="px-2.5 py-1 rounded-lg text-cyan-400 bg-cyan-950/60 border border-cyan-800/60 font-semibold flex items-center gap-1.5 shadow-sm">
          <span>💬</span> บทสนทนาการวิจัยฉบับเต็ม
        </a>
      </nav>
    </div>
    <div class="flex items-center gap-2 text-xs">
      <a href="research.html" class="px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-medium shadow transition flex items-center gap-1.5">
        <span>🔬</span> ไปหน้ารวมงานวิจัย 141 เปเปอร์
      </a>
      <a href="index.html" class="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 font-medium transition flex items-center gap-1.5">
        <span>🏠</span> หน้าหลัก
      </a>
    </div>
  </header>

  <!-- MAIN CONTAINER -->
  <main class="flex-1 max-w-[1200px] w-full mx-auto p-4 sm:p-6 lg:p-8 flex flex-col gap-6">

    <!-- HERO HEADER -->
    <div class="bg-gradient-to-br from-slate-900 via-slate-900 to-slate-950 border border-slate-800 rounded-3xl p-6 sm:p-8 shadow-2xl relative overflow-hidden">
      <div class="absolute -top-24 -right-24 w-80 h-80 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none"></div>
      <div class="absolute -bottom-24 -left-24 w-80 h-80 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none"></div>

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

        <h1 class="text-xl sm:text-2xl lg:text-3xl font-extrabold text-white tracking-tight leading-snug">
          บทสนทนาการค้นคว้า 141 เปเปอร์ & พัฒนาระบบ 13-Engine Quant Benchmark
        </h1>
        <p class="text-xs sm:text-sm text-slate-400 mt-2 max-w-3xl leading-relaxed">
          บันทึกการทำงานร่วมกันแบบ Pair Programming ระหว่างผู้ใช้กับ Antigravity AI ตั้งแต่การดึงเปเปอร์วิชาการระดับสถาบันจาก arXiv q-fin, การสกัดทฤษฎีคณิตศาสตร์การเงินสู่ 13 Quant Engines, การรัน Benchmark บนข้อมูล Order Book Level 2 สด, การ Optimize จนถึงการดึงข้อมูลประวัติศาสตร์ย้อนหลัง
        </p>

        <!-- STATS BADGES -->
        <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-6 pt-6 border-t border-slate-800/80 text-xs">
          <div class="bg-slate-950/50 p-3 rounded-xl border border-slate-800/80">
            <span class="text-slate-400 text-[11px] block">จำนวนข้อความทั้งหมด</span>
            <span class="text-white font-bold text-sm sm:text-base mt-0.5 block">{len(messages)} ข้อความ</span>
          </div>
          <div class="bg-slate-950/50 p-3 rounded-xl border border-slate-800/80">
            <span class="text-slate-400 text-[11px] block">คำถาม / คำสั่งของผู้ใช้</span>
            <span class="text-blue-400 font-bold text-sm sm:text-base mt-0.5 block">{user_count} คำสั่ง</span>
          </div>
          <div class="bg-slate-950/50 p-3 rounded-xl border border-slate-800/80">
            <span class="text-slate-400 text-[11px] block">คำตอบวิเคราะห์เชิงลึก AI</span>
            <span class="text-emerald-400 font-bold text-sm sm:text-base mt-0.5 block">{ai_count} บทวิเคราะห์</span>
          </div>
          <div class="bg-slate-950/50 p-3 rounded-xl border border-slate-800/80">
            <span class="text-slate-400 text-[11px] block">ช่วงเวลาสนทนาจริง</span>
            <span class="text-slate-200 font-medium text-xs mt-0.5 block">{time_span}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- CONTROLS & FILTER BAR -->
    <div class="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 bg-slate-900/60 p-3.5 rounded-2xl border border-slate-800">
      <!-- Search Input -->
      <div class="relative flex-1">
        <span class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-500 text-xs">
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

      <!-- Role Filters -->
      <div class="flex items-center gap-1.5 self-end sm:self-center">
        <button id="filter-all" onclick="setFilter('all')" class="px-3 py-1.5 rounded-lg text-xs font-bold text-slate-950 bg-cyan-400 shadow-sm transition cursor-pointer">
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

  <!-- EMBEDDED PRISTINE JSON DATA SCRIPT -->
  <script id="chat-data" type="application/json">
{chat_json_str}
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

    function escapeHtml(str) {{
      if (!str) return '';
      return str
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
    }}

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
          let mediaHtml = '';
          if (msg.media) {{
            mediaHtml = `
              <div class="mb-3 rounded-xl overflow-hidden border border-blue-500/30 max-w-md bg-slate-950 shadow-md">
                <a href="${{msg.media}}" target="_blank" title="คลิกเพื่อดูรูปขนาดเต็ม">
                  <img src="${{msg.media}}" alt="ภาพแนบจากผู้ใช้" class="w-full h-auto object-cover hover:opacity-90 transition cursor-zoom-in" />
                </a>
              </div>
            `;
          }}

          card.innerHTML = `
            <div class="max-w-[85%] sm:max-w-[75%] bg-gradient-to-br from-blue-950/80 via-slate-900 to-slate-900 border border-blue-500/40 rounded-2xl rounded-tr-sm p-4 sm:p-5 shadow-lg">
              <div class="flex items-center justify-between gap-3 border-b border-blue-500/20 pb-2 mb-2.5">
                <span class="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-blue-600 text-white shadow-sm">
                  <span>👤</span> USER (ผู้ใช้งาน)
                </span>
                <span class="text-[11px] font-mono text-blue-300/80">${{msg.time}}</span>
              </div>
              ${{mediaHtml}}
              <div class="text-sm sm:text-base text-slate-100 whitespace-pre-wrap leading-relaxed font-sans">
                ${{escapeHtml(msg.text)}}
              </div>
            </div>
          `;
        }} else {{
          let stepsHtml = '';
          if (msg.steps && msg.steps.length > 0) {{
            stepsHtml = `
              <details class="mb-4 text-xs bg-slate-950/70 rounded-xl border border-slate-800/80 p-3 group">
                <summary class="cursor-pointer text-slate-400 hover:text-cyan-400 font-medium flex items-center justify-between select-none">
                  <span class="flex items-center gap-2">
                    <span>⚡</span> ขั้นตอนการประมวลผลเบื้องหลัง (${{msg.steps.length}} ขั้นตอน)
                  </span>
                  <span class="text-[10px] text-slate-500 group-open:rotate-180 transition-transform">▼</span>
                </summary>
                <ul class="mt-2.5 pt-2 border-t border-slate-800/60 space-y-1.5 text-slate-300 list-disc list-inside">
                  ${{msg.steps.map(s => `<li>${{escapeHtml(s)}}</li>`).join('')}}
                </ul>
              </details>
            `;
          }}

          let renderedMd = marked.parse(msg.text);

          let artifactHtml = '';
          if (msg.artifact) {{
            artifactHtml = `
              <div class="mt-5 p-4 rounded-xl bg-slate-950/90 border border-slate-800 hover:border-emerald-500/40 transition flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-lg">
                <div class="flex items-start gap-3.5">
                  <div class="p-2.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xl shrink-0">
                    ${{msg.artifact.icon || '📄'}}
                  </div>
                  <div>
                    <div class="font-bold text-white text-sm">${{msg.artifact.title}}</div>
                    <p class="text-xs text-slate-400 mt-0.5 leading-relaxed">${{msg.artifact.summary}}</p>
                  </div>
                </div>
                <div class="flex items-center gap-2.5 self-end sm:self-center shrink-0">
                  <span class="text-[11px] font-mono text-emerald-400 bg-emerald-950/80 px-2.5 py-1 rounded border border-emerald-800/50 font-bold">${{msg.artifact.badge}}</span>
                  <a href="${{msg.artifact.url}}" target="_blank" class="px-3.5 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow transition flex items-center gap-1.5">
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
              ${{stepsHtml}}
              <div class="prose-content">
                ${{renderedMd}}
              </div>
              ${{artifactHtml}}
            </div>
          `;
        }}

        stream.appendChild(card);

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

    function setFilter(role) {{
      currentFilter = role;
      const bAll = document.getElementById('filter-all');
      const bUser = document.getElementById('filter-user');
      const bAi = document.getElementById('filter-ai');

      const activeClass = "px-3 py-1.5 rounded-lg text-xs font-bold text-slate-950 bg-cyan-400 shadow-sm transition cursor-pointer";
      const inactiveClass = "px-3 py-1.5 rounded-lg text-xs font-medium text-slate-400 hover:text-white bg-slate-800/60 hover:bg-slate-800 transition cursor-pointer";

      bAll.className = role === 'all' ? activeClass : inactiveClass;
      bUser.className = role === 'user' ? activeClass : inactiveClass;
      bAi.className = role === 'assistant' ? activeClass : inactiveClass;

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
          if (target) target.scrollIntoView({{ block: 'start' }});
        }}, 300);
      }}
    }};
  </script>
</body>
</html>"""
    return html

def update_research_html(messages):
    if not os.path.exists(OUT_RESEARCH_PATH):
        return False

    with open(OUT_RESEARCH_PATH, 'r', encoding='utf-8') as f:
        content = f.read()

    chat_json_str = json.dumps(messages, ensure_ascii=False)

    # 1. Update embedded chat JSON data script using lambda replacement
    pattern_data = r'<script id="embedded-chat-data" type="application/json">.*?</script>'
    replacement_data = f'<script id="embedded-chat-data" type="application/json">\n{chat_json_str}\n  </script>'
    content = re.sub(pattern_data, lambda m: replacement_data, content, flags=re.DOTALL)

    # 2. Update message count badge in header
    pattern_badge = r'<span class="text-xs font-mono text-slate-400">\d+ ข้อความจริง \(ไม่มีตัดทอน\)</span>'
    replacement_badge = f'<span class="text-xs font-mono text-slate-400">{len(messages)} ข้อความจริง (ไม่มีตัดทอน)</span>'
    content = re.sub(pattern_badge, lambda m: replacement_badge, content)

    # 3. Update view-mode button count
    pattern_btn = r'<span>💬</span> อ่านบทสนทนาตัวเต็ม \(\d+ ข้อความ\)'
    replacement_btn = f'<span>💬</span> อ่านบทสนทนาตัวเต็ม ({len(messages)} ข้อความ)'
    content = re.sub(pattern_btn, lambda m: replacement_btn, content)

    # 4. Ensure renderEmbeddedChat handles media and artifacts dynamically
    old_render_function_pattern = r'function renderEmbeddedChat\(\) \{.*?stream\.appendChild\(card\);'
    new_render_function = """function renderEmbeddedChat() {
      const stream = document.getElementById('embeddedChatStream');
      if (!stream) return;
      stream.innerHTML = '';

      const query = embeddedChatSearch.trim().toLowerCase();

      EMBEDDED_CHAT.forEach(msg => {
        if (query && !msg.text.toLowerCase().includes(query)) return;

        const isUser = msg.role === 'user';
        const card = document.createElement('div');
        card.className = isUser ? 'flex justify-end' : 'flex justify-start w-full';
        card.id = 'embedded-msg-' + msg.id;

        if (isUser) {
          let mediaHtml = '';
          if (msg.media) {
            mediaHtml = `
              <div class="mb-3 rounded-xl overflow-hidden border border-blue-500/30 max-w-md bg-slate-950 shadow-md">
                <a href="${msg.media}" target="_blank" title="คลิกเพื่อดูรูปขนาดเต็ม">
                  <img src="${msg.media}" alt="ภาพแนบจากผู้ใช้" class="w-full h-auto object-cover hover:opacity-90 transition cursor-zoom-in" />
                </a>
              </div>
            `;
          }

          card.innerHTML = `
            <div class="max-w-[85%] sm:max-w-[75%] bg-gradient-to-br from-blue-950/80 via-slate-900 to-slate-900 border border-blue-500/40 rounded-2xl rounded-tr-sm p-4 sm:p-5 shadow-lg">
              <div class="flex items-center justify-between gap-3 border-b border-blue-500/20 pb-2 mb-2.5">
                <span class="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-blue-600 text-white shadow-sm">
                  <span>👤</span> USER (ผู้ใช้งาน)
                </span>
                <span class="text-[11px] font-mono text-blue-300/80">${msg.time}</span>
              </div>
              ${mediaHtml}
              <div class="text-sm sm:text-base text-slate-100 whitespace-pre-wrap leading-relaxed font-sans">
                ${escapeHtml(msg.text)}
              </div>
            </div>
          `;
        } else {
          let stepsHtml = '';
          if (msg.steps && msg.steps.length > 0) {
            stepsHtml = `
              <details class="mb-4 text-xs bg-slate-950/70 rounded-xl border border-slate-800/80 p-3 group">
                <summary class="cursor-pointer text-slate-400 hover:text-cyan-400 font-medium flex items-center justify-between select-none">
                  <span class="flex items-center gap-2">
                    <span>⚡</span> ขั้นตอนการประมวลผลเบื้องหลัง (${msg.steps.length} ขั้นตอน)
                  </span>
                  <span class="text-[10px] text-slate-500 group-open:rotate-180 transition-transform">▼</span>
                </summary>
                <ul class="mt-2.5 pt-2 border-t border-slate-800/60 space-y-1.5 text-slate-300 list-disc list-inside">
                  ${msg.steps.map(s => `<li>${escapeHtml(s)}</li>`).join('')}
                </ul>
              </details>
            `;
          }

          let renderedMd = typeof marked !== 'undefined' ? marked.parse(msg.text) : msg.text;

          let artifactHtml = '';
          if (msg.artifact) {
            artifactHtml = `
              <div class="mt-5 p-4 rounded-xl bg-slate-950/90 border border-slate-800 hover:border-emerald-500/40 transition flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-lg">
                <div class="flex items-start gap-3.5">
                  <div class="p-2.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xl shrink-0">
                    ${msg.artifact.icon || '📄'}
                  </div>
                  <div>
                    <div class="font-bold text-white text-sm">${msg.artifact.title}</div>
                    <p class="text-xs text-slate-400 mt-0.5 leading-relaxed">${msg.artifact.summary}</p>
                  </div>
                </div>
                <div class="flex items-center gap-2.5 self-end sm:self-center shrink-0">
                  <span class="text-[11px] font-mono text-emerald-400 bg-emerald-950/80 px-2.5 py-1 rounded border border-emerald-800/50 font-bold">${msg.artifact.badge}</span>
                  <a href="${msg.artifact.url}" target="_blank" class="px-3.5 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow transition flex items-center gap-1.5">
                    <span>📖</span> เปิดอ่านรีพอร์ต
                  </a>
                </div>
              </div>
            `;
          }

          card.innerHTML = `
            <div class="w-full bg-[#111827]/90 border border-slate-800 rounded-2xl rounded-tl-sm p-5 sm:p-7 shadow-xl hover:border-slate-700/80 transition">
              <div class="flex items-center justify-between gap-3 border-b border-slate-800 pb-3 mb-4 flex-wrap">
                <div class="flex items-center gap-2">
                  <span class="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 shadow-sm">
                    <span>🤖</span> ANTIGRAVITY (AI QUANT)
                  </span>
                  <span class="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400">
                    #${msg.id}
                  </span>
                </div>
                <span class="text-xs font-mono text-slate-400">${msg.time}</span>
              </div>
              ${stepsHtml}
              <div class="prose-content">
                ${renderedMd}
              </div>
              ${artifactHtml}
            </div>
          `;
        }

        stream.appendChild(card);"""

    content = re.sub(old_render_function_pattern, lambda m: new_render_function, content, flags=re.DOTALL)

    with open(OUT_RESEARCH_PATH, 'w', encoding='utf-8') as f:
        f.write(content)

    return True

def sync_chat_now(force=False):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    
    state = {}
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r', encoding='utf-8') as f:
                state = json.load(f)
        except Exception:
            state = {}

    messages = extract_messages()
    if not messages:
        return False

    chat_str = json.dumps(messages, ensure_ascii=False)
    current_hash = hashlib.md5(chat_str.encode('utf-8')).hexdigest()
    last_hash = state.get('last_hash', '')

    if not force and current_hash == last_hash:
        return False

    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Detected chat update! ({len(messages)} messages, old was {state.get('message_count', 0)})")

    # 1. Write docs/chat_transcript.html
    html_content = build_chat_transcript_html(messages)
    with open(OUT_CHAT_PATH, 'w', encoding='utf-8') as f:
        f.write(html_content)

    # 2. Write zz_zz PAPER/web/chat_transcript.html
    os.makedirs(os.path.dirname(OUT_LOCAL_PATH), exist_ok=True)
    with open(OUT_LOCAL_PATH, 'w', encoding='utf-8') as f:
        f.write(html_content)

    # 3. Update docs/research.html
    update_research_html(messages)

    # 4. Save state
    state['last_hash'] = current_hash
    state['message_count'] = len(messages)
    state['user_count'] = len([m for m in messages if m['role'] == 'user'])
    state['ai_count'] = len([m for m in messages if m['role'] == 'assistant'])
    state['last_sync_utc'] = datetime.now(timezone.utc).isoformat()
    state['last_sync_local'] = datetime.now().strftime("%d %b %Y, %H:%M:%S น.")

    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2, ensure_ascii=False)

    # 5. Git Commit & Push
    try:
        subprocess.run(['git', 'add', OUT_CHAT_PATH, OUT_RESEARCH_PATH, OUT_LOCAL_PATH, MEDIA_DST_DIR, LOCAL_MEDIA_DST_DIR, STATE_FILE], cwd=REPO_ROOT, check=True)
        commit_msg = f"chore(chat): high-fidelity sync research conversation ({len(messages)} messages with artifacts & media)"
        subprocess.run(['git', 'commit', '-m', commit_msg], cwd=REPO_ROOT, check=True)
        subprocess.run(['git', 'push', 'origin', 'main'], cwd=REPO_ROOT, check=True)
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Git commit and push succeeded ({len(messages)} messages)!")
    except Exception as e:
        print(f"Git push warning: {e}")

    return True

def run_daemon():
    print(f"Starting High-Fidelity Auto-Sync Daemon for Research Conversation...")
    print(f"Target log: {LOG_PATH}")
    print(f"Polling interval: 15s (forced check every 30 minutes)\n")

    # Initial sync
    sync_chat_now(force=True)

    last_periodic_check = time.time()
    
    while True:
        try:
            # Check for changes immediately
            synced = sync_chat_now(force=False)
            
            # 30-minute forced check
            if time.time() - last_periodic_check >= 1800:
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Running scheduled 30-minute periodic check...")
                sync_chat_now(force=False)
                last_periodic_check = time.time()
                
        except Exception as e:
            print(f"Error in sync loop: {e}")
            
        time.sleep(15)

if __name__ == '__main__':
    if '--daemon' in sys.argv:
        run_daemon()
    else:
        sync_chat_now(force=True)
