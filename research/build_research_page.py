"""
Builder script to generate docs/research.html
Integrates:
1. Unified Backtest Lab Navigation
2. Executive Research & Conversation Summary (Financial Research Paper Scraping, 066c0b89-502c-4b32-b8ff-2f8201902c09)
3. Tab 1: Conversation Summary & Timeline
4. Tab 2: 13-Engine Benchmark Scorecard
5. Tab 3: Exhaustive Optimization Report & cTrader Parameters Mapping
6. Tab 4: 141 Research Paper Strategies Explorer (with search, category pills, detail modal)
7. 5-Tier Unified Pipeline Ensemble Architecture
"""

import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Read zz_zz PAPER/web/index.html to extract the rawStrategies data and helper JS
paper_web_path = r"d:\cbot-atgvt\zz_zz PAPER\web\index.html"
with open(paper_web_path, 'r', encoding='utf-8') as f:
    paper_html = f.read()

# Extract rawStrategies
strat_marker = "const rawStrategies = "
strat_idx = paper_html.find(strat_marker)
if strat_idx == -1:
    raise ValueError("Could not find rawStrategies in paper web index.html")

# Find the end of rawStrategies array definition
strat_end_marker = ";\n\n        // Category mapping and colors"
strat_end_idx = paper_html.find(strat_end_marker, strat_idx)
if strat_end_idx == -1:
    strat_end_marker = ";\n        // Category mapping and colors"
    strat_end_idx = paper_html.find(strat_end_marker, strat_idx)

raw_strat_js = paper_html[strat_idx:strat_end_idx]

# Construct docs/research.html
research_html = f"""<!DOCTYPE html>
<html lang="th" class="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Backtest Lab · งานวิจัย 141 เปเปอร์ & 13 Quant Engines</title>
  <link rel="stylesheet" href="style.css">
  <script src="https://cdn.tailwindcss.com"></script>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=Noto+Sans+Thai:wght@300;400;500;600;700&display=swap" rel="stylesheet">
  <script>
    tailwind.config = {{
      darkMode: 'class',
      theme: {{
        extend: {{
          fontFamily: {{
            sans: ['"Plus Jakarta Sans"', '"Noto Sans Thai"', 'sans-serif'],
          }},
          colors: {{
            brand: {{
              50: '#f0fdf4',
              500: '#10b981',
              600: '#059669',
              900: '#064e3b',
            }},
            dark: {{
              bg: '#0b0f17',
              card: '#111827',
              border: '#1f2937',
              accent: '#1e293b'
            }}
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
    .active-nav-tab {{
      background: rgba(16, 185, 129, 0.15);
      color: #34d399;
      border-color: rgba(16, 185, 129, 0.3);
      font-weight: 700;
    }}
    .subtab-btn.active {{
      background: #10b981;
      color: #ffffff;
      box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
    }}
  </style>
</head>
<body class="min-h-screen flex flex-col font-sans antialiased selection:bg-brand-500 selection:text-white">

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

        <!-- Active Research Tab -->
        <a href="research.html" class="px-3 py-1.5 rounded-lg active-nav-tab border flex items-center gap-1.5 shadow-sm">
          <span>🔬</span> งานวิจัย (141 Papers)
        </a>

        <a href="chat_transcript.html" target="_blank" class="px-3 py-1.5 rounded-lg text-cyan-300 hover:text-white hover:bg-cyan-950/60 transition border border-cyan-800/60 bg-cyan-950/30 flex items-center gap-1.5 shadow-sm">
          <span>💬</span> บทสนทนาการวิจัย (Full Chat)
        </a>
        
        <!-- Dropdown for Legacy Claude Results -->
        <div class="relative inline-block text-left" id="claude-dropdown-wrap">
          <button type="button" onclick="toggleClaudeDropdown(event)" class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-slate-300 hover:text-white hover:bg-slate-800 transition border border-slate-700/80 bg-slate-900/90 shadow-sm cursor-pointer">
            <span>📁</span>
            <span class="font-medium">ผลทดสอบเก่า CLAUDE</span>
            <svg class="w-3.5 h-3.5 transition-transform duration-200 text-slate-400" id="claude-dropdown-arrow" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
            </svg>
          </button>
          <div id="claude-dropdown-menu" class="hidden absolute left-0 mt-2 w-64 rounded-xl shadow-2xl bg-slate-900 border border-slate-700 divide-y divide-slate-800 z-50 py-1 ring-1 ring-black ring-opacity-5">
            <div class="px-3.5 py-2 text-[11px] font-semibold text-slate-400 border-b border-slate-800">
              คลังผลการวิจัยและทฤษฎีเดิม (CLAUDE)
            </div>
            <div class="py-1">
              <a href="legacy.html" class="flex items-center gap-2.5 px-3.5 py-2 text-xs text-slate-300 hover:bg-slate-800 hover:text-emerald-400 transition">
                <span class="text-base">📋</span>
                <div>
                  <div class="font-medium text-white">ผลทดสอบเดิม (Supabase)</div>
                  <div class="text-[10px] text-slate-400">ประวัติ Backtest กว่า 2,000 รอบ</div>
                </div>
              </a>
              <a href="summary.html" class="flex items-center gap-2.5 px-3.5 py-2 text-xs text-slate-300 hover:bg-slate-800 hover:text-emerald-400 transition">
                <span class="text-base">📊</span>
                <div>
                  <div class="font-medium text-white">สรุปผลการวิจัย</div>
                  <div class="text-[10px] text-slate-400">เปรียบเทียบช่วง Explore / Validate</div>
                </div>
              </a>
              <a href="strategies.html" class="flex items-center gap-2.5 px-3.5 py-2 text-xs text-slate-300 hover:bg-slate-800 hover:text-emerald-400 transition">
                <span class="text-base">💡</span>
                <div>
                  <div class="font-medium text-white">คลังทฤษฎี</div>
                  <div class="text-[10px] text-slate-400">คำอธิบายกลยุทธ์และพารามิเตอร์</div>
                </div>
              </a>
              <a href="chart.html" class="flex items-center gap-2.5 px-3.5 py-2 text-xs text-slate-300 hover:bg-slate-800 hover:text-emerald-400 transition">
                <span class="text-base">🕯️</span>
                <div>
                  <div class="font-medium text-white">ทฤษฎีกราฟ</div>
                  <div class="text-[10px] text-slate-400">ทฤษฎีที่ใช้ราคาอย่างเดียว (CH_)</div>
                </div>
              </a>
              <a href="daystudy.html" class="flex items-center gap-2.5 px-3.5 py-2 text-xs text-slate-300 hover:bg-slate-800 hover:text-emerald-400 transition">
                <span class="text-base">📅</span>
                <div>
                  <div class="font-medium text-white">สถิติรายวัน (Day Study)</div>
                  <div class="text-[10px] text-slate-400">พฤติกรรมแยกตามช่วงเวลาตลาด</div>
                </div>
              </a>
              <a href="phase1.html" class="flex items-center gap-2.5 px-3.5 py-2 text-xs text-slate-300 hover:bg-slate-800 hover:text-emerald-400 transition">
                <span class="text-base">🤖</span>
                <div>
                  <div class="font-medium text-white">ทำนายรายนาที (ML Model)</div>
                  <div class="text-[10px] text-slate-400">การพยากรณ์แท่งเทียนด้วย Machine Learning</div>
                </div>
              </a>
            </div>
          </div>
        </div>
      </nav>
    </div>
    <div class="flex items-center gap-2 text-xs">
      <span class="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-slate-700">
        <span class="w-1.5 h-1.5 rounded-full bg-blue-400"></span>
        GitHub Pages
      </span>
      <a href="https://github.com/tgrockza55-ai/tgrockza55-ai-cbot-backtest-lab" target="_blank" class="text-slate-400 hover:text-white transition font-mono">
        tgrockza55-ai
      </a>
    </div>
  </header>

  <!-- MAIN CONTAINER -->
  <main class="flex-1 max-w-[1380px] w-full mx-auto p-4 sm:p-6 flex flex-col gap-6">

    <!-- 1. HERO EXECUTIVE SUMMARY: FINANCIAL RESEARCH PAPER SCRAPING PROJECT -->
    <div class="bg-gradient-to-br from-slate-900 via-slate-900 to-slate-950 border border-slate-800 rounded-3xl p-6 sm:p-8 shadow-2xl relative overflow-hidden">
      <!-- Glow ambient lighting -->
      <div class="absolute -top-32 -right-32 w-[30rem] h-[30rem] bg-emerald-500/10 rounded-full blur-3xl pointer-events-none"></div>
      <div class="absolute -bottom-32 -left-32 w-[30rem] h-[30rem] bg-cyan-500/10 rounded-full blur-3xl pointer-events-none"></div>

      <div class="relative z-10 space-y-6">
        <!-- Top Metadata & Action Badges -->
        <div class="flex flex-wrap items-center justify-between gap-3">
          <div class="flex flex-wrap items-center gap-2 text-xs">
            <span class="px-3 py-1 rounded-full bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 font-semibold flex items-center gap-1.5">
              <span>🏛️</span> Financial Research Paper Scraping
            </span>
            <span class="px-2.5 py-1 rounded-full bg-slate-800/80 text-slate-400 border border-slate-700 font-mono">
              Conv ID: 066c0b89-502c-4b32-b8ff-2f8201902c09
            </span>
            <span class="px-2.5 py-1 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20">
              141 arXiv Papers
            </span>
            <span class="px-2.5 py-1 rounded-full bg-purple-500/10 text-purple-400 border border-purple-500/20">
              13 Quant Engines
            </span>
          </div>

          <div class="flex items-center gap-2">
            <a href="chat_transcript.html" target="_blank" class="px-4 py-2 bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-500 hover:to-cyan-500 text-white rounded-xl text-xs sm:text-sm font-semibold shadow-lg shadow-blue-900/30 transition-all flex items-center gap-2">
              <span>💬</span> อ่านบทสนทนาการวิจัยฉบับเต็ม (Full Chat)
            </a>
            <button onclick="toggleEnsembleModal()" class="px-4 py-2 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white rounded-xl text-xs sm:text-sm font-semibold shadow-lg shadow-emerald-900/30 transition-all flex items-center gap-2">
              <span>🧩</span> ผัง 5-Tier Pipeline
            </button>
          </div>
        </div>

        <!-- Main Title & Description -->
        <div>
          <h1 class="text-2xl sm:text-3xl font-extrabold bg-gradient-to-r from-emerald-400 via-teal-300 to-cyan-400 bg-clip-text text-transparent mb-2">
            โครงการสกัด 141 เปเปอร์การเงินชั้นนำ สู่ 13 เสาหลักอัลกอริทึมเทรด (Quant Research Hub)
          </h1>
          <p class="text-slate-300 text-sm sm:text-base max-w-4xl leading-relaxed">
            สรุปผลลัพธ์การค้นคว้า วิจัย และพัฒนาจากการสนทนาในโปรเจกต์ 
            <span class="text-emerald-400 font-semibold font-mono">"Financial Research Paper Scraping"</span> 
            ที่ได้ดึงเปเปอร์วิชาการระดับสถาบันจาก <span class="text-white font-medium">arXiv q-fin</span>, <span class="text-white font-medium">SSRN</span>, และ <span class="text-white font-medium">World Gold Council</span> 
            นำมาสกัดเป็นสูตรคณิตศาสตร์และตรรกะการเทรดจริง 141 กลยุทธ์ จัดหมวดหมู่เป็น 13 Quant Strategy Engines และทดสอบอย่างเข้มงวดด้วยชุดข้อมูล Order Book Level 2 จริง
          </p>
        </div>

        <!-- 4 Pillars Grid -->
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 pt-2">
          <div class="bg-slate-900/80 border border-slate-800 rounded-2xl p-4 shadow-sm hover:border-emerald-500/40 transition">
            <div class="text-2xl mb-2">📑</div>
            <div class="font-bold text-white text-sm mb-1">141 Research Papers</div>
            <div class="text-xs text-slate-400 leading-relaxed">คัดกรองเปเปอร์การเงินระดับสถาบัน 141 ฉบับ แบ่งเป็น 13 หมวดหมู่ พร้อมลิงก์ดาวน์โหลด PDF และอ่าน HTML เต็ม</div>
          </div>
          <div class="bg-slate-900/80 border border-slate-800 rounded-2xl p-4 shadow-sm hover:border-emerald-500/40 transition">
            <div class="text-2xl mb-2">⚙️</div>
            <div class="font-bold text-white text-sm mb-1">13 Quant Strategy Engines</div>
            <div class="text-xs text-slate-400 leading-relaxed">แปลงทฤษฎีเชิงปริมาณสู่ C# Robots ใน cTrader Automate: DeepLOB, OFI, Hawkes, HMM, Kelly Risk, Rough Volatility</div>
          </div>
          <div class="bg-slate-900/80 border border-slate-800 rounded-2xl p-4 shadow-sm hover:border-emerald-500/40 transition">
            <div class="text-2xl mb-2">📊</div>
            <div class="font-bold text-white text-sm mb-1">Real DOM Microstructure Test</div>
            <div class="text-xs text-slate-400 leading-relaxed">รัน Benchmark ทดสอบความทนทานบนข้อมูล Order Book จริงระดับ High-Frequency ข้าม BTCUSD, ETHUSD, และ GOLD-PERP</div>
          </div>
          <div class="bg-slate-900/80 border border-slate-800 rounded-2xl p-4 shadow-sm hover:border-emerald-500/40 transition">
            <div class="text-2xl mb-2">🏆</div>
            <div class="font-bold text-white text-sm mb-1">Exhaustive Optimization</div>
            <div class="text-xs text-slate-400 leading-relaxed">จูนพารามิเตอร์แบบ Coordinate Descent จนพบอัลฟ่ากำไรสูงสุด เช่น Dynamic Kelly (PF 3.37, WR 66.7%), Rough Vol (PF 2.34)</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 2. SECTION SUB-TABS NAVIGATION -->
    <div class="flex items-center gap-2 overflow-x-auto pb-1 border-b border-slate-800 text-xs sm:text-sm font-medium">
      <button onclick="switchTab('timeline')" id="subtab-timeline" class="subtab-btn active px-4 py-2.5 rounded-xl border border-transparent transition-all flex items-center gap-2 whitespace-nowrap">
        <span>💬</span> 1. สรุปการสนทนา & ไทม์ไลน์การวิจัย
      </button>
      <button onclick="switchTab('benchmark')" id="subtab-benchmark" class="subtab-btn px-4 py-2.5 rounded-xl border border-transparent text-slate-400 hover:text-white hover:bg-slate-800/60 transition-all flex items-center gap-2 whitespace-nowrap">
        <span>📊</span> 2. ตารางคะแนน 13-Engine Benchmark
      </button>
      <button onclick="switchTab('optimization')" id="subtab-optimization" class="subtab-btn px-4 py-2.5 rounded-xl border border-transparent text-slate-400 hover:text-white hover:bg-slate-800/60 transition-all flex items-center gap-2 whitespace-nowrap">
        <span>🚀</span> 3. ผลการ Optimize สูงสุด & ค่า cTrader
      </button>
      <button onclick="switchTab('strategies')" id="subtab-strategies" class="subtab-btn px-4 py-2.5 rounded-xl border border-transparent text-slate-400 hover:text-white hover:bg-slate-800/60 transition-all flex items-center gap-2 whitespace-nowrap">
        <span>📚</span> 4. คลังสืบค้น 141 เปเปอร์ (Strategy Explorer)
      </button>
    </div>

    <!-- ========================================================================= -->
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
        </div>

        <!-- 6 Phases Vertical Timeline -->
        <div class="relative border-l-2 border-emerald-500/30 ml-4 pl-6 space-y-8 my-6">
          
          <!-- Phase 1 -->
          <div class="relative group">
            <span class="absolute -left-[33px] top-1.5 w-4 h-4 rounded-full bg-emerald-500 ring-4 ring-slate-900"></span>
            <div class="bg-slate-900/90 border border-slate-800 rounded-xl p-4 hover:border-emerald-500/40 transition">
              <div class="flex flex-wrap items-center justify-between gap-2 mb-1">
                <span class="text-xs font-bold text-emerald-400 uppercase tracking-wider">ระยะที่ 1: การค้นหาและคัดกรองเปเปอร์การเงิน</span>
                <span class="text-[11px] text-slate-500 font-mono">15:30 - 16:10 น.</span>
              </div>
              <h4 class="text-sm font-bold text-white mb-2">เป้าหมาย: ดึงงานวิจัยจาก arXiv q-fin, SSRN และ Gold.org เพื่อมาเป็นสมองให้บอท</h4>
              <p class="text-xs text-slate-300 leading-relaxed mb-3">
                ผู้ใช้เริ่มการสนทนาโดยตั้งเป้าหมายว่าต้องการดาวน์โหลดเปเปอร์การเงินระดับสถาบันมาวิเคราะห์เพื่อพัฒนาบอทเทรด 
                ระบบได้เชื่อมต่อดึงงานวิจัยกว่า 141 ฉบับ ครอบคลุมคณิตศาสตร์การเงินชั้นสูง ทฤษฎีสภาพคล่อง และพฤติกรรม Order Book
              </p>
              <div class="flex flex-wrap gap-1.5 text-[11px]">
                <span class="px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">141 เปเปอร์</span>
                <span class="px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">arXiv q-fin</span>
                <span class="px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">HTML & PDF Parsing</span>
              </div>
            </div>
          </div>

          <!-- Phase 2 -->
          <div class="relative group">
            <span class="absolute -left-[33px] top-1.5 w-4 h-4 rounded-full bg-emerald-500 ring-4 ring-slate-900"></span>
            <div class="bg-slate-900/90 border border-slate-800 rounded-xl p-4 hover:border-emerald-500/40 transition">
              <div class="flex flex-wrap items-center justify-between gap-2 mb-1">
                <span class="text-xs font-bold text-emerald-400 uppercase tracking-wider">ระยะที่ 2: สกัดตรรกะและสูตรคณิตศาสตร์สู่ 13 Quant Engines</span>
                <span class="text-[11px] text-slate-500 font-mono">16:10 - 17:15 น.</span>
              </div>
              <h4 class="text-sm font-bold text-white mb-2">สกัดทฤษฎีจาก 141 เปเปอร์ออกมาเป็น 13 เสาหลักอัลกอริทึม และ 1 Master Pipeline</h4>
              <p class="text-xs text-slate-300 leading-relaxed mb-3">
                ผู้ใช้สั่งให้จำแนกและเขียน cBot ใน cTrader สำหรับทุกกลยุทธ์ ระบบจึงได้สังเคราะห์ออกมาเป็น 13 Engines สำคัญ: 
                DeepLOB (L2 Wall Absorption), OFI (Cont-Stoikov Flow), Avellaneda Market Making, VWAP Execution Slicer, 
                Hawkes Point Process, HMM Regime Switcher, Kalman Velocity, Dynamic Kelly Sizing, และ Rough Volatility Kernel
              </p>
              <div class="flex flex-wrap gap-1.5 text-[11px]">
                <span class="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">13 C# Robots</span>
                <span class="px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">5-Tier Orchestrator</span>
                <span class="px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">cAlgo Automate</span>
              </div>
            </div>
          </div>

          <!-- Phase 3 -->
          <div class="relative group">
            <span class="absolute -left-[33px] top-1.5 w-4 h-4 rounded-full bg-emerald-500 ring-4 ring-slate-900"></span>
            <div class="bg-slate-900/90 border border-slate-800 rounded-xl p-4 hover:border-emerald-500/40 transition">
              <div class="flex flex-wrap items-center justify-between gap-2 mb-1">
                <span class="text-xs font-bold text-emerald-400 uppercase tracking-wider">ระยะที่ 3: การรัน Benchmark บนข้อมูล Live DOM Scraping</span>
                <span class="text-[11px] text-slate-500 font-mono">17:15 - 18:15 น.</span>
              </div>
              <h4 class="text-sm font-bold text-white mb-2">สร้างสคริปต์ 13-Engine Testbench และทดสอบบนข้อมูลจริง 1,027 นาที</h4>
              <p class="text-xs text-slate-300 leading-relaxed mb-3">
                นำข้อมูล Order Book Level 2 และ Flow ที่บันทึกสดจากตลาดจริง (BTCUSD, ETHUSD, GOLD-PERP) มาทดสอบกับทั้ง 13 Engines 
                ผลลัพธ์พบว่า <span class="text-emerald-400 font-semibold">Engine 12 (Dynamic Kelly Risk)</span> ทำกำไรได้โดดเด่นที่สุดบน BTC (+$2.85 USD, WR 57.9%, PF 1.54) 
                และ <span class="text-emerald-400 font-semibold">Engine 11 (News Gate)</span> ให้ความแม่นยำสูงถึง 82.4% บน ETH
              </p>
              <div class="flex flex-wrap gap-1.5 text-[11px]">
                <span class="px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">1,027 M1 Bars</span>
                <span class="px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">L2 DOM Imbalance</span>
                <span class="px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">Quant Scorecard</span>
              </div>
            </div>
          </div>

          <!-- Phase 4 -->
          <div class="relative group">
            <span class="absolute -left-[33px] top-1.5 w-4 h-4 rounded-full bg-emerald-500 ring-4 ring-slate-900"></span>
            <div class="bg-slate-900/90 border border-slate-800 rounded-xl p-4 hover:border-emerald-500/40 transition">
              <div class="flex flex-wrap items-center justify-between gap-2 mb-1">
                <span class="text-xs font-bold text-emerald-400 uppercase tracking-wider">ระยะที่ 4: การค้นพบเรื่องค่าสเปรดและข้อจำกัดของทองคำวันหยุด</span>
                <span class="text-[11px] text-slate-500 font-mono">18:15 - 18:22 น.</span>
              </div>
              <h4 class="text-sm font-bold text-white mb-2">การเปิดเผยความจริง: ทำไมทองคำวันหยุดถึงเทรดสั้นไม่ได้?</h4>
              <p class="text-xs text-slate-300 leading-relaxed mb-3">
                ข้อมูลการทดสอบชี้ชัดว่าในวันหยุดเสาร์-อาทิตย์ สเปรดทองคำ ($1.41) กว้างกว่าการเคลื่อนที่ 1 นาที ($0.11) ถึง 12.3 เท่า 
                ทำให้การสเกลปปิ้งขาดทุนสเปรด แต่ในทางกลับกัน ในช่วงตลาดเปิดจริง (2023-2026 Active Hours) ทฤษฎี Session Window กลับทำกำไรได้ถึง +$212.25 USD (PF 1.22)
              </p>
              <div class="flex flex-wrap gap-1.5 text-[11px]">
                <span class="px-2 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20">The Spread Anomaly</span>
                <span class="px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">Session Window</span>
              </div>
            </div>
          </div>

          <!-- Phase 5 -->
          <div class="relative group">
            <span class="absolute -left-[33px] top-1.5 w-4 h-4 rounded-full bg-emerald-500 ring-4 ring-slate-900"></span>
            <div class="bg-slate-900/90 border border-slate-800 rounded-xl p-4 hover:border-emerald-500/40 transition">
              <div class="flex flex-wrap items-center justify-between gap-2 mb-1">
                <span class="text-xs font-bold text-emerald-400 uppercase tracking-wider">ระยะที่ 5: การ Optimize แบบ Exhaustive Coordinate Descent</span>
                <span class="text-[11px] text-slate-500 font-mono">18:22 - 18:28 น.</span>
              </div>
              <h4 class="text-sm font-bold text-white mb-2">ผู้ใช้สั่ง Optimize ทีละค่า จนได้กำไรสูงสุดในทุก Engine</h4>
              <p class="text-xs text-slate-300 leading-relaxed mb-3">
                ทำการ Sweep พารามิเตอร์แบบ Coordinate Descent เพื่อค้นหาชุดค่าที่ทำกำไรสูงสุดในแต่ละ Engine ส่งผลให้:
                <br>• <span class="text-emerald-400 font-semibold">Dynamic Kelly Risk:</span> กำไรพุ่งขึ้นเป็น <b>+$5.82 USD</b> (Profit Factor <b>3.37</b>, Win Rate <b>66.7%</b>)
                <br>• <span class="text-emerald-400 font-semibold">Rough Volatility:</span> กำไรพุ่งขึ้นเป็น <b>+$4.38 USD</b> (Profit Factor <b>2.34</b>, Win Rate <b>57.1%</b>)
                <br>• <span class="text-emerald-400 font-semibold">Multi-Level DeepLOB:</span> พลิกจากติดลบเป็น <b>+$3.38 USD</b> (Profit Factor <b>1.62</b>)
              </p>
              <div class="flex flex-wrap gap-1.5 text-[11px]">
                <span class="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">Top 5 Champions</span>
                <span class="px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">PF 3.37 Kelly</span>
                <span class="px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">Coordinate Sweep</span>
              </div>
            </div>
          </div>

          <!-- Phase 6 -->
          <div class="relative group">
            <span class="absolute -left-[33px] top-1.5 w-4 h-4 rounded-full bg-emerald-500 ring-4 ring-slate-900"></span>
            <div class="bg-slate-900/90 border border-slate-800 rounded-xl p-4 hover:border-emerald-500/40 transition">
              <div class="flex flex-wrap items-center justify-between gap-2 mb-1">
                <span class="text-xs font-bold text-emerald-400 uppercase tracking-wider">ระยะที่ 6: แมปพารามิเตอร์ขึ้น cTrader GUI & ส่งขึ้นหน้าเว็บ</span>
                <span class="text-[11px] text-slate-500 font-mono">18:28 - 18:32 น.</span>
              </div>
              <h4 class="text-sm font-bold text-white mb-2">สร้างคู่มือการตั้งค่า P1..P4 ใน cTrader และเผยแพร่ขึ้น Web Portal</h4>
              <p class="text-xs text-slate-300 leading-relaxed mb-3">
                จัดทำตาราง Parameter Mapping สำหรับนำไปใช้ในแท็บ Optimization ของ cTrader Automate พร้อมนำโครงการทั้งหมดมาสร้างเป็นแท็บงานวิจัย (Research Tab) บน GitHub Pages ให้ผู้สนใจสามารถสืบค้นเปเปอร์ทั้ง 141 ฉบับได้อย่างสมบูรณ์
              </p>
              <div class="flex flex-wrap gap-1.5 text-[11px]">
                <span class="px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20">cTrader Optimization Guide</span>
                <span class="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">Web Portal Published</span>
              </div>
            </div>
          </div>

        </div>
      </div>

    </div>

    <!-- ========================================================================= -->
    <!-- TAB 2: 13-ENGINE BENCHMARK SCORECARD -->
    <!-- ========================================================================= -->
    <div id="tab-content-benchmark" class="hidden space-y-6">
      
      <!-- Key Insights Banner -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div class="bg-slate-900/90 border border-emerald-500/30 rounded-2xl p-5 shadow-lg relative overflow-hidden">
          <div class="text-xs font-bold text-emerald-400 uppercase tracking-wider mb-1">🥇 Top Alpha Engine on BTC</div>
          <div class="text-xl font-extrabold text-white mb-1">Dynamic ATR Kelly Sizing</div>
          <div class="text-xs text-slate-300">
            Net Profit: <b class="text-emerald-400">+$2.85 USD</b> | Win Rate: <b class="text-white">57.9%</b> | Profit Factor: <b class="text-white">1.54</b>
          </div>
          <div class="text-[11px] text-slate-400 mt-2">ปรับขนาด SL / TP ไดนามิกตามความผันผวน ATR (1.5x SL, 3.0x TP)</div>
        </div>

        <div class="bg-slate-900/90 border border-blue-500/30 rounded-2xl p-5 shadow-lg relative overflow-hidden">
          <div class="text-xs font-bold text-blue-400 uppercase tracking-wider mb-1">🛡️ Win Rate Champion on ETH</div>
          <div class="text-xl font-extrabold text-white mb-1">Volatility Void News Gate</div>
          <div class="text-xs text-slate-300">
            Win Rate: <b class="text-blue-400">82.4%</b> | ชนะ 14 / แพ้ 3 | Max Drawdown: <b class="text-white">$0.70</b>
          </div>
          <div class="text-[11px] text-slate-400 mt-2">กรองสภาพคล่องและตัดช่วงความผันผวนผิดปกติ ป้องกันการขาดทุนช่วงหลุดสเปรด</div>
        </div>

        <div class="bg-slate-900/90 border border-purple-500/30 rounded-2xl p-5 shadow-lg relative overflow-hidden">
          <div class="text-xs font-bold text-purple-400 uppercase tracking-wider mb-1">🧱 Order Book Absorption</div>
          <div class="text-xl font-extrabold text-white mb-1">Multi-Level DeepLOB Wall</div>
          <div class="text-xs text-slate-300">
            Win Rate: <b class="text-purple-400">60.0% (BTC)</b> / <b class="text-purple-400">71.0% (ETH)</b>
          </div>
          <div class="text-[11px] text-slate-400 mt-2">ดักจับกำแพง Bid/Ask ในสมุดคำสั่งซื้อขายจริง ช่วยรักษาเงินทุนในสภาวะแกว่งตัว</div>
        </div>
      </div>

      <!-- BTCUSD Table -->
      <div class="bg-dark-card border border-dark-border rounded-2xl p-6 shadow-xl overflow-hidden">
        <div class="flex items-center justify-between mb-4">
          <div>
            <h3 class="text-base font-bold text-white flex items-center gap-2">
              <span class="text-amber-400">🪙</span> ตารางคะแนน BTCUSD (1,027 แท่ง M1 | ค่าสเปรดเฉลี่ย $0.16)
            </h3>
            <p class="text-xs text-slate-400">ทดสอบทั้ง 13 Engines บนข้อมูล Live DOM Scraping จริง</p>
          </div>
          <span class="px-2.5 py-1 rounded bg-slate-800 text-slate-300 text-xs font-mono">Continuous Feed</span>
        </div>

        <div class="overflow-x-auto">
          <table class="w-full text-left text-xs border-collapse">
            <thead>
              <tr class="border-b border-dark-border text-slate-400 bg-dark-bg/60">
                <th class="py-3 px-3">อันดับ</th>
                <th class="py-3 px-3">รหัส Engine</th>
                <th class="py-3 px-3">ทฤษฎีหลัก (Quant Pillar)</th>
                <th class="py-3 px-3 text-center">ไม้ทั้งหมด</th>
                <th class="py-3 px-3 text-center">ชนะ / แพ้</th>
                <th class="py-3 px-3 text-center">Win Rate</th>
                <th class="py-3 px-3 text-right">Net PnL</th>
                <th class="py-3 px-3 text-center">Profit Factor</th>
                <th class="py-3 px-3 text-right">Max DD</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-dark-border text-slate-300">
              <tr class="bg-emerald-500/5 font-semibold text-white">
                <td class="py-3 px-3 text-emerald-400">🥇 1</td>
                <td class="py-3 px-3 font-mono text-emerald-400">ENGINE_12_KELLY_SIZING</td>
                <td class="py-3 px-3">Dynamic ATR Kelly Risk Sizing</td>
                <td class="py-3 px-3 text-center">19</td>
                <td class="py-3 px-3 text-center">11 / 8</td>
                <td class="py-3 px-3 text-center text-emerald-400 font-bold">57.9%</td>
                <td class="py-3 px-3 text-right text-emerald-400 font-bold">+$2.85</td>
                <td class="py-3 px-3 text-center text-emerald-400 font-bold">1.54</td>
                <td class="py-3 px-3 text-right text-slate-300">$2.11</td>
              </tr>
              <tr>
                <td class="py-3 px-3 text-slate-400">🥈 2</td>
                <td class="py-3 px-3 font-mono text-white">ENGINE_01_DEEPLOB</td>
                <td class="py-3 px-3">Multi-Level L2 Depth Wall Absorption</td>
                <td class="py-3 px-3 text-center">25</td>
                <td class="py-3 px-3 text-center">15 / 10</td>
                <td class="py-3 px-3 text-center text-emerald-400 font-bold">60.0%</td>
                <td class="py-3 px-3 text-right text-slate-300">+$0.00</td>
                <td class="py-3 px-3 text-center">1.00</td>
                <td class="py-3 px-3 text-right text-slate-300">$1.53</td>
              </tr>
              <tr>
                <td class="py-3 px-3 text-slate-400">🥉 3</td>
                <td class="py-3 px-3 font-mono text-white">ENGINE_11_NEWS_GATE</td>
                <td class="py-3 px-3">Volatility Void Gate & Spread Shock Filter</td>
                <td class="py-3 px-3 text-center">9</td>
                <td class="py-3 px-3 text-center">5 / 4</td>
                <td class="py-3 px-3 text-center text-emerald-400 font-bold">55.6%</td>
                <td class="py-3 px-3 text-right text-slate-400">-$0.34</td>
                <td class="py-3 px-3 text-center">0.83</td>
                <td class="py-3 px-3 text-right text-slate-300">$1.02</td>
              </tr>
              <tr>
                <td class="py-3 px-3 text-slate-500">4</td>
                <td class="py-3 px-3 font-mono text-slate-300">ENGINE_13_ROUGH_VOL</td>
                <td class="py-3 px-3">Rough Heston Microstructure Kernel</td>
                <td class="py-3 px-3 text-center">18</td>
                <td class="py-3 px-3 text-center">7 / 11</td>
                <td class="py-3 px-3 text-center">38.9%</td>
                <td class="py-3 px-3 text-right text-slate-400">-$0.34</td>
                <td class="py-3 px-3 text-center">0.95</td>
                <td class="py-3 px-3 text-right text-slate-300">$3.06</td>
              </tr>
              <tr>
                <td class="py-3 px-3 text-slate-500">5</td>
                <td class="py-3 px-3 font-mono text-slate-300">ENGINE_06_GOLD_INTRADAY</td>
                <td class="py-3 px-3">Session Liquidity Window</td>
                <td class="py-3 px-3 text-center">8</td>
                <td class="py-3 px-3 text-center">2 / 6</td>
                <td class="py-3 px-3 text-center">25.0%</td>
                <td class="py-3 px-3 text-right text-red-400">-$2.38</td>
                <td class="py-3 px-3 text-center">0.22</td>
                <td class="py-3 px-3 text-right text-slate-300">$2.72</td>
              </tr>
              <tr>
                <td class="py-3 px-3 text-slate-500">6</td>
                <td class="py-3 px-3 font-mono text-slate-300">ENGINE_08_LEAD_LAG</td>
                <td class="py-3 px-3">CVD Delta Exhaustion</td>
                <td class="py-3 px-3 text-center">18</td>
                <td class="py-3 px-3 text-center">8 / 10</td>
                <td class="py-3 px-3 text-center">44.4%</td>
                <td class="py-3 px-3 text-right text-red-400">-$2.38</td>
                <td class="py-3 px-3 text-center">0.53</td>
                <td class="py-3 px-3 text-right text-slate-300">$2.38</td>
              </tr>
              <tr>
                <td class="py-3 px-3 text-slate-500">7</td>
                <td class="py-3 px-3 font-mono text-slate-300">ENGINE_04_VWAP_SLICER</td>
                <td class="py-3 px-3">Anchored VWAP 1.2 SD Band</td>
                <td class="py-3 px-3 text-center">21</td>
                <td class="py-3 px-3 text-center">9 / 12</td>
                <td class="py-3 px-3 text-center">42.9%</td>
                <td class="py-3 px-3 text-right text-red-400">-$2.72</td>
                <td class="py-3 px-3 text-center">0.65</td>
                <td class="py-3 px-3 text-right text-slate-300">$4.16</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- ETHUSD Table -->
      <div class="bg-dark-card border border-dark-border rounded-2xl p-6 shadow-xl overflow-hidden">
        <div class="flex items-center justify-between mb-4">
          <div>
            <h3 class="text-base font-bold text-white flex items-center gap-2">
              <span class="text-blue-400">💎</span> ตารางคะแนน ETHUSD (1,027 แท่ง M1 | ค่าสเปรดเฉลี่ย $0.20)
            </h3>
            <p class="text-xs text-slate-400">ทดสอบทั้ง 13 Engines บนข้อมูล Live DOM Scraping จริง</p>
          </div>
          <span class="px-2.5 py-1 rounded bg-slate-800 text-slate-300 text-xs font-mono">Continuous Feed</span>
        </div>

        <div class="overflow-x-auto">
          <table class="w-full text-left text-xs border-collapse">
            <thead>
              <tr class="border-b border-dark-border text-slate-400 bg-dark-bg/60">
                <th class="py-3 px-3">อันดับ</th>
                <th class="py-3 px-3">รหัส Engine</th>
                <th class="py-3 px-3">ทฤษฎีหลัก (Quant Pillar)</th>
                <th class="py-3 px-3 text-center">ไม้ทั้งหมด</th>
                <th class="py-3 px-3 text-center">ชนะ / แพ้</th>
                <th class="py-3 px-3 text-center">Win Rate</th>
                <th class="py-3 px-3 text-right">Net PnL</th>
                <th class="py-3 px-3 text-center">Profit Factor</th>
                <th class="py-3 px-3 text-right">Max DD</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-dark-border text-slate-300">
              <tr class="bg-blue-500/5 font-semibold text-white">
                <td class="py-3 px-3 text-blue-400">🥇 1</td>
                <td class="py-3 px-3 font-mono text-blue-400">ENGINE_11_NEWS_GATE</td>
                <td class="py-3 px-3">Volatility Void Gate & Spread Shock Filter</td>
                <td class="py-3 px-3 text-center">17</td>
                <td class="py-3 px-3 text-center">14 / 3</td>
                <td class="py-3 px-3 text-center text-blue-400 font-bold">82.4%</td>
                <td class="py-3 px-3 text-right text-slate-300">-$0.35</td>
                <td class="py-3 px-3 text-center text-blue-400 font-bold">0.67</td>
                <td class="py-3 px-3 text-right text-slate-300">$0.70</td>
              </tr>
              <tr>
                <td class="py-3 px-3 text-slate-400">🥈 2</td>
                <td class="py-3 px-3 font-mono text-white">ENGINE_08_LEAD_LAG</td>
                <td class="py-3 px-3">CVD Delta Exhaustion</td>
                <td class="py-3 px-3 text-center">6</td>
                <td class="py-3 px-3 text-center">4 / 2</td>
                <td class="py-3 px-3 text-center text-emerald-400 font-bold">66.7%</td>
                <td class="py-3 px-3 text-right text-slate-300">-$0.50</td>
                <td class="py-3 px-3 text-center">0.29</td>
                <td class="py-3 px-3 text-right text-slate-300">$0.55</td>
              </tr>
              <tr>
                <td class="py-3 px-3 text-slate-400">🥉 3</td>
                <td class="py-3 px-3 font-mono text-white">ENGINE_01_DEEPLOB</td>
                <td class="py-3 px-3">Multi-Level L2 Depth Wall Absorption</td>
                <td class="py-3 px-3 text-center">31</td>
                <td class="py-3 px-3 text-center">22 / 9</td>
                <td class="py-3 px-3 text-center text-emerald-400 font-bold">71.0%</td>
                <td class="py-3 px-3 text-right text-slate-300">-$2.05</td>
                <td class="py-3 px-3 text-center">0.35</td>
                <td class="py-3 px-3 text-right text-slate-300">$2.05</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

    </div>

    <!-- ========================================================================= -->
    <!-- TAB 3: EXHAUSTIVE OPTIMIZATION REPORT & CTRADER MAPPING -->
    <!-- ========================================================================= -->
    <div id="tab-content-optimization" class="hidden space-y-6">
      
      <!-- Top Champions Grid -->
      <div class="bg-dark-card border border-dark-border rounded-2xl p-6 shadow-xl">
        <h3 class="text-base font-bold text-white flex items-center gap-2 mb-2">
          <span>🏆</span> 5 สุดยอดกลยุทธ์อัลฟ่าหลังการ Optimize ละเอียด (Top 5 Champions)
        </h3>
        <p class="text-xs text-slate-400 mb-6">
          ผลลัพธ์จากการปรับแต่งแบบ Coordinate-Wise Descent บนข้อมูล Order Book ระดับ High-Frequency ดึงศักยภาพสูงสุดออกมาได้สมบูรณ์
        </p>

        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          <!-- Champ 1 -->
          <div class="bg-slate-900 border border-emerald-500/40 rounded-xl p-4 shadow-md relative">
            <div class="flex items-center justify-between mb-2">
              <span class="text-xs font-bold text-emerald-400">🥇 อันดับ 1: QUANT_KELLY</span>
              <span class="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 text-[10px] font-mono">Gain +$3.39</span>
            </div>
            <div class="text-2xl font-black text-white mb-1">+$5.82 <span class="text-xs font-normal text-slate-400">USD</span></div>
            <div class="text-xs text-slate-300 mb-2">Profit Factor: <b class="text-emerald-400">3.37</b> | Win Rate: <b class="text-emerald-400">66.7%</b></div>
            <div class="text-[11px] font-mono text-slate-400 bg-dark-bg p-2 rounded-lg border border-slate-800">
              atr_mult: 2.0, rr: 2.8, imb: 0.03
            </div>
          </div>

          <!-- Champ 2 -->
          <div class="bg-slate-900 border border-teal-500/40 rounded-xl p-4 shadow-md relative">
            <div class="flex items-center justify-between mb-2">
              <span class="text-xs font-bold text-teal-400">🥈 อันดับ 2: QUANT_ROUGH_VOL</span>
              <span class="px-2 py-0.5 rounded bg-teal-500/10 text-teal-400 text-[10px] font-mono">Gain +$3.35</span>
            </div>
            <div class="text-2xl font-black text-white mb-1">+$4.38 <span class="text-xs font-normal text-slate-400">USD</span></div>
            <div class="text-xs text-slate-300 mb-2">Profit Factor: <b class="text-teal-400">2.34</b> | Win Rate: <b class="text-teal-400">57.1%</b></div>
            <div class="text-[11px] font-mono text-slate-400 bg-dark-bg p-2 rounded-lg border border-slate-800">
              hurst: 0.35, env_mult: 0.55, rr: 2.5
            </div>
          </div>

          <!-- Champ 3 -->
          <div class="bg-slate-900 border border-cyan-500/40 rounded-xl p-4 shadow-md relative">
            <div class="flex items-center justify-between mb-2">
              <span class="text-xs font-bold text-cyan-400">🥉 อันดับ 3: DOM_ABSORPTION</span>
              <span class="px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-400 text-[10px] font-mono">Gain +$4.01</span>
            </div>
            <div class="text-2xl font-black text-white mb-1">+$3.38 <span class="text-xs font-normal text-slate-400">USD</span></div>
            <div class="text-xs text-slate-300 mb-2">Profit Factor: <b class="text-cyan-400">1.62</b> | Win Rate: <b class="text-cyan-400">55.0%</b></div>
            <div class="text-[11px] font-mono text-slate-400 bg-dark-bg p-2 rounded-lg border border-slate-800">
              lookback: 15, imb: 0.02, sl: 45, rr: 2.6
            </div>
          </div>
        </div>
      </div>

      <!-- cTrader Parameters Mapping Table -->
      <div class="bg-dark-card border border-dark-border rounded-2xl p-6 shadow-xl overflow-hidden">
        <div class="flex items-center justify-between mb-4">
          <div>
            <h3 class="text-base font-bold text-white flex items-center gap-2">
              <span>🎛️</span> ตารางตั้งค่าใน cTrader Automate Optimization (Parameters Mapping)
            </h3>
            <p class="text-xs text-slate-400">นำค่าช่วง Min, Max, Step ไปใส่ในหน้าต่าง Optimization ของ cTrader เพื่อรันได้ทันที</p>
          </div>
        </div>

        <div class="overflow-x-auto">
          <table class="w-full text-left text-xs border-collapse">
            <thead>
              <tr class="border-b border-dark-border text-slate-400 bg-dark-bg/60">
                <th class="py-3 px-3">Strategy Code</th>
                <th class="py-3 px-3">P1 (Parameter 1)</th>
                <th class="py-3 px-3">P2 (Parameter 2)</th>
                <th class="py-3 px-3">P3 (Parameter 3)</th>
                <th class="py-3 px-3">P4 (Parameter 4)</th>
                <th class="py-3 px-3">SL / TP แนะนำ</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-dark-border text-slate-300 font-mono">
              <tr class="bg-emerald-500/5">
                <td class="py-3 px-3 font-bold text-emerald-400">QUANT_KELLY</td>
                <td class="py-3 px-3"><b>AtrSlMultiplier</b><br><span class="text-slate-400">Def: 2.0 (Min: 1.0, Max: 2.5, Step: 0.2)</span></td>
                <td class="py-3 px-3"><b>RewardRiskRatio</b><br><span class="text-slate-400">Def: 2.8 (Min: 1.8, Max: 3.5, Step: 0.2)</span></td>
                <td class="py-3 px-3"><b>ImbalanceThresh</b><br><span class="text-slate-400">Def: 0.03 (Min: 0.015, Max: 0.04, Step: 0.005)</span></td>
                <td class="py-3 px-3"><b>RangeBoundaryPct</b><br><span class="text-slate-400">Def: 0.15 (Min: 0.10, Max: 0.20, Step: 0.02)</span></td>
                <td class="py-3 px-3 text-emerald-400">Dynamic ตาม ATR</td>
              </tr>
              <tr>
                <td class="py-3 px-3 font-bold text-teal-400">QUANT_ROUGH_VOL</td>
                <td class="py-3 px-3"><b>HurstH</b><br><span class="text-slate-400">Def: 0.35 (Min: 0.15, Max: 0.45, Step: 0.05)</span></td>
                <td class="py-3 px-3"><b>EnvelopeMult</b><br><span class="text-slate-400">Def: 0.55 (Min: 0.35, Max: 0.65, Step: 0.05)</span></td>
                <td class="py-3 px-3"><b>RewardRisk</b><br><span class="text-slate-400">Def: 2.5 (Min: 1.5, Max: 3.0, Step: 0.2)</span></td>
                <td class="py-3 px-3"><b>ImbalanceScale</b><br><span class="text-slate-400">Def: 1.0 (Min: 0.6, Max: 1.2, Step: 0.2)</span></td>
                <td class="py-3 px-3 text-teal-400">Dynamic ตาม Envelope</td>
              </tr>
              <tr>
                <td class="py-3 px-3 font-bold text-cyan-400">DOM_ABSORPTION</td>
                <td class="py-3 px-3"><b>LookbackMin</b><br><span class="text-slate-400">Def: 15 (Min: 10, Max: 30, Step: 5)</span></td>
                <td class="py-3 px-3"><b>ImbalanceThresh</b><br><span class="text-slate-400">Def: 0.02 (Min: 0.015, Max: 0.04, Step: 0.005)</span></td>
                <td class="py-3 px-3"><b>StopLossUsd</b><br><span class="text-slate-400">Def: 45.0 (Min: 20.0, Max: 50.0, Step: 5.0)</span></td>
                <td class="py-3 px-3"><b>RewardRisk</b><br><span class="text-slate-400">Def: 2.6 (Min: 1.5, Max: 3.0, Step: 0.2)</span></td>
                <td class="py-3 px-3 text-cyan-400">SL 45, TP 117</td>
              </tr>
              <tr>
                <td class="py-3 px-3 font-bold text-purple-400">QUANT_MASTER</td>
                <td class="py-3 px-3"><b>NewsGateRatio</b><br><span class="text-slate-400">Def: 1.6 (Min: 1.2, Max: 2.4, Step: 0.2)</span></td>
                <td class="py-3 px-3"><b>TrendVolRatio</b><br><span class="text-slate-400">Def: 1.5 (Min: 1.2, Max: 1.8, Step: 0.1)</span></td>
                <td class="py-3 px-3"><b>ChopStopLoss</b><br><span class="text-slate-400">Def: 25.0 (Min: 20.0, Max: 45.0, Step: 5.0)</span></td>
                <td class="py-3 px-3"><b>ChopTakeProfit</b><br><span class="text-slate-400">Def: 75.0 (Min: 50.0, Max: 100.0, Step: 10.0)</span></td>
                <td class="py-3 px-3 text-purple-400">SL 25, TP 75 (RR 3:1)</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

    </div>

    <!-- ========================================================================= -->
    <!-- TAB 4: 141 RESEARCH PAPERS STRATEGY EXPLORER -->
    <!-- ========================================================================= -->
    <div id="tab-content-strategies" class="hidden space-y-6">

      <!-- Search & Stats Bar -->
      <div class="bg-dark-card border border-dark-border rounded-2xl p-5 shadow-xl flex flex-col md:flex-row items-center justify-between gap-4">
        <div class="w-full md:w-96 relative">
          <span class="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-gray-400">🔍</span>
          <input type="text" id="searchInput" oninput="filterStrategies()" placeholder="ค้นหากลยุทธ์, ทริกเกอร์, สูตร, รหัสเปเปอร์..."
                 class="w-full pl-10 pr-4 py-2.5 bg-dark-bg border border-dark-border rounded-xl text-sm focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500 transition-colors text-white placeholder-gray-500">
        </div>
        <div class="flex items-center gap-4 text-xs text-gray-400">
          <div>ทั้งหมด: <span id="totalCount" class="font-bold text-white text-sm">141</span> กลยุทธ์</div>
          <div class="h-4 w-px bg-dark-border"></div>
          <div>กำลังแสดง: <span id="visibleCount" class="font-bold text-brand-500 text-sm">141</span> รายการ</div>
        </div>
      </div>

      <!-- Category Filter Pills -->
      <div class="flex items-center gap-2 overflow-x-auto pb-2 scrollbar-none" id="categoryFilter">
        <button onclick="setCategory('ALL')" class="cat-pill active px-4 py-2 rounded-xl text-xs font-medium bg-emerald-500 text-white border border-emerald-400 shadow-sm transition-all whitespace-nowrap">
          ทั้งหมด (141)
        </button>
      </div>

      <!-- Strategy Cards Grid -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5" id="strategyGrid">
        <!-- Cards populated by JS -->
      </div>

    </div>

  </main>

  <!-- STRATEGY DETAIL MODAL -->
  <div id="detailModal" class="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm hidden flex items-center justify-center p-4">
    <div class="bg-dark-card border border-dark-border rounded-2xl max-w-3xl w-full max-h-[90vh] flex flex-col overflow-hidden shadow-2xl">
      <div class="p-6 border-b border-dark-border flex items-start justify-between gap-4 bg-dark-accent/40">
        <div>
          <div class="flex items-center gap-2 mb-2">
            <span id="modalIcon" class="text-xl">📊</span>
            <span id="modalCategory" class="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"></span>
            <span id="modalId" class="text-xs font-mono text-gray-400"></span>
          </div>
          <h3 id="modalTitle" class="text-lg font-bold text-white"></h3>
          <p id="modalAuthors" class="text-xs text-gray-400 mt-1"></p>
        </div>
        <button onclick="closeDetailModal()" class="text-gray-400 hover:text-white p-1 rounded-lg hover:bg-dark-border transition-colors">
          ✕
        </button>
      </div>
      <div class="p-6 overflow-y-auto space-y-5 text-sm">
        <div class="flex items-center gap-3">
          <a id="modalHtmlLink" target="_blank" class="px-4 py-1.5 bg-brand-500 hover:bg-brand-600 text-white rounded-lg text-xs font-medium transition-colors flex items-center gap-1.5">
            🌐 อ่าน HTML เต็มบนเว็บ
          </a>
          <a id="modalPdfLink" target="_blank" class="px-4 py-1.5 bg-dark-border hover:bg-gray-700 text-gray-300 rounded-lg text-xs font-medium transition-colors flex items-center gap-1.5">
            📥 ดาวน์โหลด PDF
          </a>
        </div>

        <div class="bg-dark-bg p-3.5 rounded-xl border border-dark-border">
          <span class="text-xs text-gray-400 font-semibold block mb-1">ประเภทกลยุทธ์:</span>
          <span id="modalType" class="text-emerald-400 font-medium"></span>
        </div>

        <div>
          <h4 class="text-xs font-bold uppercase tracking-wider text-emerald-400 mb-1.5 flex items-center gap-1.5">
            <span>💰</span> ทำไมถึงได้กำไร? (Alpha & Profit Mechanism)
          </h4>
          <p id="modalWhyProfitable" class="text-gray-300 leading-relaxed bg-dark-bg p-4 rounded-xl border border-dark-border"></p>
        </div>

        <div>
          <h4 class="text-xs font-bold uppercase tracking-wider text-emerald-400 mb-1.5 flex items-center gap-1.5">
            <span>🎯</span> จุดเข้าออเดอร์ (Entry Trigger)
          </h4>
          <p id="modalEntry" class="text-gray-300 leading-relaxed bg-dark-bg p-4 rounded-xl border border-dark-border"></p>
        </div>

        <div>
          <h4 class="text-xs font-bold uppercase tracking-wider text-emerald-400 mb-1.5 flex items-center gap-1.5">
            <span>🚪</span> จุดออกและตัดขาดทุน (Exit & Stop Loss)
          </h4>
          <p id="modalExit" class="text-gray-300 leading-relaxed bg-dark-bg p-4 rounded-xl border border-dark-border"></p>
        </div>

        <div>
          <h4 class="text-xs font-bold uppercase tracking-wider text-emerald-400 mb-1.5 flex items-center gap-1.5">
            <span>📐</span> สูตรคณิตศาสตร์หลัก (Mathematical Formula)
          </h4>
          <code id="modalMath" class="block font-mono text-xs text-brand-500 bg-black/40 p-4 rounded-xl border border-dark-border overflow-x-auto"></code>
        </div>

        <div>
          <h4 class="text-xs font-bold uppercase tracking-wider text-emerald-400 mb-1.5 flex items-center gap-1.5">
            <span>🛡️</span> การคุมความเสี่ยง (Risk Management)
          </h4>
          <p id="modalRisk" class="text-gray-300 leading-relaxed bg-dark-bg p-4 rounded-xl border border-dark-border"></p>
        </div>
      </div>
    </div>
  </div>

  <!-- ENSEMBLE MODAL -->
  <div id="ensembleModal" class="fixed inset-0 z-50 bg-black/80 backdrop-blur-md hidden flex items-center justify-center p-4">
    <div class="bg-dark-card border border-dark-border rounded-2xl max-w-4xl w-full max-h-[90vh] flex flex-col overflow-hidden shadow-2xl">
      <div class="p-6 border-b border-dark-border flex items-center justify-between bg-dark-accent/40">
        <div>
          <h3 class="text-lg font-bold text-white flex items-center gap-2">
            <span>🧩</span> แผนผังการทำงานร่วมกัน 5 ลำดับชั้น (5-Tier Unified Pipeline)
          </h3>
          <p class="text-xs text-gray-400">สถาปัตยกรรมรวมมิตร 141 เปเปอร์เป็นระบบเทรดเดียว ไร้การชนกัน</p>
        </div>
        <button onclick="toggleEnsembleModal()" class="text-gray-400 hover:text-white p-1 rounded-lg hover:bg-dark-border transition-colors">
          ✕
        </button>
      </div>
      <div class="p-6 overflow-y-auto space-y-4 text-xs sm:text-sm">
        <div class="p-4 rounded-xl bg-dark-bg border border-dark-border">
          <span class="text-xs font-bold text-amber-400 block mb-1">Tier 1: Spread & News Gate (ตัวกรองความเสี่ยงชั้นแรก)</span>
          <p class="text-gray-300">หยุดระบบทันทีเมื่อสเปรดกว้างเกิน 0.35x ATR หรือเกิด Flash Shock จากข่าว ป้องกันการขาดทุนฟรี</p>
        </div>
        <div class="p-4 rounded-xl bg-dark-bg border border-dark-border">
          <span class="text-xs font-bold text-cyan-400 block mb-1">Tier 2: HMM Regime Switch (ตัวสลับโหมดตลาด)</span>
          <p class="text-gray-300">ใช้ Hidden Markov Model ตรวจจับว่าตลาดกำลังเป็น Sideway แคบ (Chop) หรือเป็นเทรนด์กระชาก (Expansion)</p>
        </div>
        <div class="p-4 rounded-xl bg-dark-bg border border-dark-border">
          <span class="text-xs font-bold text-emerald-400 block mb-1">Tier 3: Alpha Signal Generation (สร้างสัญญาณเข้าเทรด)</span>
          <p class="text-gray-300">
            • ถ้าเป็น Chop: ใช้ <b>DOM Absorption (DeepLOB)</b> สวนขอบสวิงกลับหาค่ากลาง
            <br>• ถ้าเป็น Trend: ใช้ <b>Hawkes Process + Kalman Velocity</b> ขี่ตามโมเมนตัม
          </p>
        </div>
        <div class="p-4 rounded-xl bg-dark-bg border border-dark-border">
          <span class="text-xs font-bold text-blue-400 block mb-1">Tier 4: Optimal Execution (การซอยออเดอร์)</span>
          <p class="text-gray-300">ใช้ Anchored VWAP คอยซอยส่งคำสั่งแบบไม่สร้าง Market Impact ต่อตลาด</p>
        </div>
        <div class="p-4 rounded-xl bg-dark-bg border border-dark-border">
          <span class="text-xs font-bold text-purple-400 block mb-1">Tier 5: Kelly Volatility-Targeted Dynamic Sizing (คำนวณขนาดไม้)</span>
          <p class="text-gray-300">คำนวณขนาดล็อตตาม Kelly Criterion และขยาย SL / TP ตามความผันผวน ATR แบบ Real-time</p>
        </div>
      </div>
    </div>
  </div>

  <!-- SCRIPT SECTION -->
  <script>
    // Tab switching logic
    function switchTab(tabId) {{
      const tabs = ['timeline', 'benchmark', 'optimization', 'strategies'];
      tabs.forEach(t => {{
        const btn = document.getElementById('subtab-' + t);
        const content = document.getElementById('tab-content-' + t);
        if (t === tabId) {{
          btn.classList.add('active');
          btn.classList.remove('text-slate-400');
          btn.classList.add('text-white');
          content.classList.remove('hidden');
        }} else {{
          btn.classList.remove('active');
          btn.classList.add('text-slate-400');
          btn.classList.remove('text-white');
          content.classList.add('hidden');
        }}
      }});
    }}

    // Claude Dropdown toggle
    function toggleClaudeDropdown(event) {{
      event.stopPropagation();
      const menu = document.getElementById('claude-dropdown-menu');
      const arrow = document.getElementById('claude-dropdown-arrow');
      menu.classList.toggle('hidden');
      arrow.classList.toggle('rotate-180');
    }}
    document.addEventListener('click', (e) => {{
      const wrap = document.getElementById('claude-dropdown-wrap');
      if (wrap && !wrap.contains(e.target)) {{
        const menu = document.getElementById('claude-dropdown-menu');
        const arrow = document.getElementById('claude-dropdown-arrow');
        if (menu && !menu.classList.contains('hidden')) {{
          menu.classList.add('hidden');
          arrow.classList.remove('rotate-180');
        }}
      }}
    }});

    // DATA & MODALS
    {raw_strat_js}

    // Category mapping and colors
    const categoryMeta = {{
      "01_deep_learning_lob": {{ label: "Deep Learning & LOB", icon: "🧠", color: "text-purple-400 bg-purple-500/10 border-purple-500/20" }},
      "02_order_flow_imbalance": {{ label: "Order Flow Imbalance", icon: "📊", color: "text-blue-400 bg-blue-500/10 border-blue-500/20" }},
      "03_high_freq_market_making": {{ label: "High-Freq Market Making", icon: "⚡", color: "text-yellow-400 bg-yellow-500/10 border-yellow-500/20" }},
      "04_optimal_execution_and_vwap": {{ label: "Optimal Execution & VWAP", icon: "🎯", color: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20" }},
      "05_point_processes_and_hawkes": {{ label: "Point Processes & Hawkes", icon: "📈", color: "text-red-400 bg-red-500/10 border-red-500/20" }},
      "06_gold_microstructure_and_intraday": {{ label: "Gold Microstructure", icon: "🪙", color: "text-amber-400 bg-amber-500/10 border-amber-500/20" }},
      "07_regime_switching_and_hmm": {{ label: "Regime Switching & HMM", icon: "🔄", color: "text-indigo-400 bg-indigo-500/10 border-indigo-500/20" }},
      "08_lead_lag_and_arbitrage": {{ label: "Lead-Lag & Arbitrage", icon: "🔗", color: "text-cyan-400 bg-cyan-500/10 border-cyan-500/20" }},
      "09_filtering_and_kalman": {{ label: "Filtering & Kalman", icon: "📡", color: "text-teal-400 bg-teal-500/10 border-teal-500/20" }},
      "10_synthetic_data_and_simulation": {{ label: "Synthetic Simulation", icon: "🎲", color: "text-pink-400 bg-pink-500/10 border-pink-500/20" }},
      "11_financial_llm_and_sentiment": {{ label: "Financial LLM & News", icon: "📰", color: "text-rose-400 bg-rose-500/10 border-rose-500/20" }},
      "12_position_sizing_and_risk": {{ label: "Position Sizing & Kelly", icon: "⚖️", color: "text-green-400 bg-green-500/10 border-green-500/20" }},
      "13_rough_volatility_and_jumps": {{ label: "Rough Volatility & Jumps", icon: "📉", color: "text-orange-400 bg-orange-500/10 border-orange-500/20" }}
    }};

    let currentCategory = 'ALL';
    let currentSearch = '';

    // Initialize Category Filters
    const filterContainer = document.getElementById('categoryFilter');
    Object.keys(categoryMeta).forEach(key => {{
      const meta = categoryMeta[key];
      const count = rawStrategies.filter(s => s.category === key).length;
      const btn = document.createElement('button');
      btn.onclick = () => setCategory(key);
      btn.className = `cat-pill px-4 py-2 rounded-xl text-xs font-medium bg-dark-bg text-gray-400 border border-dark-border hover:border-gray-600 transition-all whitespace-nowrap`;
      btn.id = `cat-${{key}}`;
      btn.innerHTML = `${{meta.icon}} ${{meta.label}} (${{count}})`;
      filterContainer.appendChild(btn);
    }});

    function setCategory(cat) {{
      currentCategory = cat;
      document.querySelectorAll('.cat-pill').forEach(btn => {{
        btn.classList.remove('bg-emerald-500', 'text-white', 'border-emerald-400');
        btn.classList.add('bg-dark-bg', 'text-gray-400', 'border-dark-border');
      }});
      const activeBtn = cat === 'ALL' 
        ? document.querySelector('.cat-pill') 
        : document.getElementById(`cat-${{cat}}`);
      if (activeBtn) {{
        activeBtn.classList.remove('bg-dark-bg', 'text-gray-400', 'border-dark-border');
        activeBtn.classList.add('bg-emerald-500', 'text-white', 'border-emerald-400');
      }}
      filterStrategies();
    }}

    function filterStrategies() {{
      const query = document.getElementById('searchInput').value.toLowerCase().trim();
      currentSearch = query;

      const filtered = rawStrategies.filter(s => {{
        const matchCat = currentCategory === 'ALL' || s.category === currentCategory;
        const matchQuery = !query || 
          s.title.toLowerCase().includes(query) ||
          s.strategy_type.toLowerCase().includes(query) ||
          s.why_profitable.toLowerCase().includes(query) ||
          s.entry_trigger.toLowerCase().includes(query) ||
          s.id.toLowerCase().includes(query) ||
          s.paper_id.toLowerCase().includes(query);
        return matchCat && matchQuery;
      }});

      renderStrategies(filtered);
      document.getElementById('visibleCount').innerText = filtered.length;
    }}

    function renderStrategies(list) {{
      const grid = document.getElementById('strategyGrid');
      grid.innerHTML = '';

      if (list.length === 0) {{
        grid.innerHTML = `<div class="col-span-full py-12 text-center text-gray-500 text-sm">ไม่พบกลยุทธ์ที่ตรงกับเงื่อนไขการค้นหา</div>`;
        return;
      }}

      list.forEach(s => {{
        const meta = categoryMeta[s.category] || {{ label: s.category, icon: "📄", color: "text-gray-400 bg-gray-500/10 border-gray-500/20" }};
        const card = document.createElement('div');
        card.className = "bg-dark-card border border-dark-border hover:border-brand-500/50 rounded-2xl p-5 shadow-lg flex flex-col justify-between transition-all hover:-translate-y-1 hover:shadow-brand-500/10 cursor-pointer group";
        card.onclick = () => openDetailModal(s);

        card.innerHTML = `
          <div>
            <div class="flex items-center justify-between gap-2 mb-3">
              <span class="text-xs font-semibold px-2.5 py-0.5 rounded-full border ${{meta.color}} flex items-center gap-1">
                <span>${{meta.icon}}</span> ${{meta.label}}
              </span>
              <span class="text-[11px] font-mono text-gray-500">${{s.id}}</span>
            </div>
            <h3 class="text-sm font-bold text-white group-hover:text-brand-500 transition-colors line-clamp-2 mb-2">
              ${{s.title}}
            </h3>
            <p class="text-xs text-gray-400 line-clamp-3 mb-4 leading-relaxed">
              ${{s.why_profitable}}
            </p>
          </div>
          <div class="pt-3 border-t border-dark-border/60 flex items-center justify-between text-xs">
            <span class="text-brand-500 font-medium">${{s.strategy_type}}</span>
            <span class="text-gray-400 group-hover:text-white flex items-center gap-1 transition-colors">
              อ่านรายละเอียด →
            </span>
          </div>
        `;
        grid.appendChild(card);
      }});
    }}

    function openDetailModal(s) {{
      const meta = categoryMeta[s.category] || {{ label: s.category, icon: "📄" }};
      document.getElementById('modalIcon').innerText = meta.icon;
      document.getElementById('modalCategory').innerText = meta.label;
      document.getElementById('modalId').innerText = `${{s.id}} • arXiv:${{s.paper_id}}`;
      document.getElementById('modalTitle').innerText = s.title;
      document.getElementById('modalAuthors').innerText = s.authors ? `ผู้แต่ง: ${{s.authors}}` : '';
      document.getElementById('modalHtmlLink').href = s.html_url || `https://arxiv.org/html/${{s.base_id}}`;
      document.getElementById('modalPdfLink').href = s.pdf_url || `https://arxiv.org/pdf/${{s.base_id}}`;
      document.getElementById('modalType').innerText = s.strategy_type;
      document.getElementById('modalWhyProfitable').innerText = s.why_profitable;
      document.getElementById('modalEntry').innerText = s.entry_trigger;
      document.getElementById('modalExit').innerText = s.exit_rules;
      document.getElementById('modalMath').innerText = s.math_formula;
      document.getElementById('modalRisk').innerText = s.risk_management;

      document.getElementById('detailModal').classList.remove('hidden');
    }}

    function closeDetailModal() {{
      document.getElementById('detailModal').classList.add('hidden');
    }}

    function toggleEnsembleModal() {{
      const m = document.getElementById('ensembleModal');
      m.classList.toggle('hidden');
    }}

    // Initial render
    filterStrategies();
  </script>
</body>
</html>
"""

out_path = r"d:\cbot-atgvt\docs\research.html"
with open(out_path, 'w', encoding='utf-8') as f:
    f.write(research_html)

print(f"Successfully generated {out_path} ({len(research_html)} bytes)!")
