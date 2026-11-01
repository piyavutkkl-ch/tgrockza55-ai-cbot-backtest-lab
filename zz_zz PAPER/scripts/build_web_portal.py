import os
import sys
import json

sys.stdout.reconfigure(encoding='utf-8')

base_dir = "d:/cbot-atgvt/zz_zz PAPER"
db_path = os.path.join(base_dir, "strategies_database.json")
web_html_path = os.path.join(base_dir, "web", "index.html")

with open(db_path, encoding='utf-8') as f:
    strategies = json.load(f)

json_data_str = json.dumps(strategies, ensure_ascii=False)

html_template = f"""<!DOCTYPE html>
<html lang="th" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🏛️ Quant Research Portal - 141 Trading Bot Strategies</title>
    <!-- Tailwind CSS CDN -->
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
        ::-webkit-scrollbar {{ width: 8px; height: 8px; }}
        ::-webkit-scrollbar-track {{ background: #0b0f17; }}
        ::-webkit-scrollbar-thumb {{ background: #1f2937; border-radius: 4px; }}
        ::-webkit-scrollbar-thumb:hover {{ background: #374151; }}
    </style>
</head>
<body class="min-h-screen flex flex-col font-sans antialiased selection:bg-brand-500 selection:text-white">

    <!-- Navbar -->
    <header class="sticky top-0 z-40 bg-dark-bg/80 backdrop-blur-md border-b border-dark-border px-6 py-4 flex flex-wrap items-center justify-between gap-4">
        <div class="flex items-center gap-3">
            <span class="text-3xl">🏛️</span>
            <div>
                <h1 class="text-xl font-bold bg-gradient-to-r from-emerald-400 via-teal-300 to-cyan-400 bg-clip-text text-transparent">
                    Quant Research Portal
                </h1>
                <p class="text-xs text-gray-400">141 Quantitative Trading Strategies จาก arXiv q-fin</p>
            </div>
        </div>
        <div class="flex items-center gap-3">
            <button onclick="toggleEnsembleModal()" class="px-4 py-2 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white rounded-lg text-sm font-semibold shadow-lg shadow-emerald-900/30 transition-all flex items-center gap-2">
                <span>🧩 แผนผังรันพร้อมกัน (Ensemble Matrix)</span>
            </button>
            <span class="px-3 py-1.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-xs font-mono">
                5-Tier Pipeline
            </span>
        </div>
    </header>

    <!-- Main Container -->
    <main class="flex-1 max-w-7xl w-full mx-auto p-6 flex flex-col gap-6">

        <!-- Search & Stats Bar -->
        <div class="bg-dark-card border border-dark-border rounded-2xl p-6 shadow-xl flex flex-col md:flex-row items-center justify-between gap-4">
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
            <!-- Generated dynamically -->
        </div>

        <!-- Strategy Cards Grid -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5" id="strategyGrid">
            <!-- Cards populated by JS -->
        </div>

    </main>

    <!-- Strategy Detail Modal -->
    <div id="detailModal" class="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm hidden flex items-center justify-center p-4">
        <div class="bg-dark-card border border-dark-border rounded-2xl max-w-3xl w-full max-h-[90vh] flex flex-col overflow-hidden shadow-2xl animate-in fade-in zoom-in-95 duration-200">
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
                <!-- Action Links -->
                <div class="flex items-center gap-3">
                    <a id="modalHtmlLink" target="_blank" class="px-4 py-1.5 bg-brand-500 hover:bg-brand-600 text-white rounded-lg text-xs font-medium transition-colors flex items-center gap-1.5">
                        🌐 อ่าน HTML เต็มบนเว็บ
                    </a>
                    <a id="modalPdfLink" target="_blank" class="px-4 py-1.5 bg-dark-border hover:bg-gray-700 text-gray-300 rounded-lg text-xs font-medium transition-colors flex items-center gap-1.5">
                        📥 ดาวน์โหลด PDF
                    </a>
                </div>

                <!-- Strategy Type -->
                <div class="bg-dark-bg p-3.5 rounded-xl border border-dark-border">
                    <span class="text-xs text-gray-400 font-semibold block mb-1">ประเภทกลยุทธ์:</span>
                    <span id="modalType" class="text-emerald-400 font-medium"></span>
                </div>

                <!-- Profit Mechanism -->
                <div>
                    <h4 class="text-xs font-bold uppercase tracking-wider text-emerald-400 mb-1.5 flex items-center gap-1.5">
                        <span>💰</span> ทำไมถึงได้กำไร? (Alpha & Profit Mechanism)
                    </h4>
                    <p id="modalProfit" class="text-gray-300 bg-dark-bg/60 p-3.5 rounded-xl border border-dark-border/60 leading-relaxed"></p>
                </div>

                <!-- Entry Trigger -->
                <div>
                    <h4 class="text-xs font-bold uppercase tracking-wider text-green-400 mb-1.5 flex items-center gap-1.5">
                        <span>🟢</span> เงื่อนไขจุดเข้า (Entry Trigger)
                    </h4>
                    <p id="modalEntry" class="text-gray-200 bg-emerald-950/20 p-3.5 rounded-xl border border-emerald-500/20 leading-relaxed font-mono text-xs"></p>
                </div>

                <!-- Exit Trigger -->
                <div>
                    <h4 class="text-xs font-bold uppercase tracking-wider text-rose-400 mb-1.5 flex items-center gap-1.5">
                        <span>🔴</span> เงื่อนไขจุดออก (Exit Trigger / TP / SL)
                    </h4>
                    <p id="modalExit" class="text-gray-200 bg-rose-950/20 p-3.5 rounded-xl border border-rose-500/20 leading-relaxed font-mono text-xs"></p>
                </div>

                <!-- Strengths & Weaknesses -->
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div class="bg-dark-bg p-3.5 rounded-xl border border-dark-border">
                        <span class="text-xs text-emerald-400 font-bold block mb-1">💎 จุดเด่น (Strengths):</span>
                        <p id="modalStrengths" class="text-xs text-gray-300"></p>
                    </div>
                    <div class="bg-dark-bg p-3.5 rounded-xl border border-dark-border">
                        <span class="text-xs text-amber-400 font-bold block mb-1">⚠️ จุดอ่อน (Weaknesses):</span>
                        <p id="modalWeaknesses" class="text-xs text-gray-300"></p>
                    </div>
                </div>

                <!-- Risks -->
                <div class="bg-rose-950/10 p-3.5 rounded-xl border border-rose-500/20">
                    <span class="text-xs text-rose-400 font-bold block mb-1">🚨 สิ่งที่ต้องเฝ้าระวังอย่างยิ่ง:</span>
                    <p id="modalRisks" class="text-xs text-gray-300"></p>
                </div>

                <!-- Abstract -->
                <div>
                    <h4 class="text-xs font-bold uppercase tracking-wider text-gray-400 mb-1.5">📌 บทคัดย่อ (Abstract)</h4>
                    <p id="modalAbstract" class="text-xs text-gray-400 bg-dark-bg p-3.5 rounded-xl border border-dark-border leading-relaxed"></p>
                </div>
            </div>
        </div>
    </div>

    <!-- Ensemble Matrix Modal -->
    <div id="ensembleModal" class="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm hidden flex items-center justify-center p-4">
        <div class="bg-dark-card border border-dark-border rounded-2xl max-w-4xl w-full max-h-[90vh] flex flex-col overflow-hidden shadow-2xl">
            <div class="p-6 border-b border-dark-border flex items-center justify-between bg-dark-accent/40">
                <div class="flex items-center gap-3">
                    <span class="text-2xl">🧩</span>
                    <div>
                        <h3 class="text-lg font-bold text-white">5-Tier Hierarchical Multi-Engine Architecture</h3>
                        <p class="text-xs text-gray-400">สถาปัตยกรรมการรัน 141 กลยุทธ์พร้อมกันโดยไม่ชนกันเอง</p>
                    </div>
                </div>
                <button onclick="toggleEnsembleModal()" class="text-gray-400 hover:text-white p-1 rounded-lg hover:bg-dark-border">
                    ✕
                </button>
            </div>
            <div class="p-6 overflow-y-auto space-y-4 text-xs">
                <div class="p-4 rounded-xl border border-rose-500/20 bg-rose-950/10">
                    <div class="font-bold text-rose-400 text-sm mb-1">🛑 Tier 1: Macro & News Safety Gate</div>
                    <div class="text-gray-300">หมวด 11 (Financial LLMs) + หมวด 6 (Gold Fix) -> ทำหน้าที่เป็นผู้เฝ้าประตู ระงับการเทรดทุกระบบเมื่อมีข่าว FOMC / NFP ภายใน 15 นาที</div>
                </div>
                <div class="p-4 rounded-xl border border-amber-500/20 bg-amber-950/10">
                    <div class="font-bold text-amber-400 text-sm mb-1">🎛️ Tier 2: Market Regime Master Switch</div>
                    <div class="text-gray-300">หมวด 7 (HMM) + หมวด 10 (Diffusion Simulation) -> สลับโหมดอัตโนมัติ (Trending vs Range-Bound vs Turbulent) ไม่ให้บอทเทรนด์และบอทกริดชนกัน</div>
                </div>
                <div class="p-4 rounded-xl border border-emerald-500/20 bg-emerald-950/10">
                    <div class="font-bold text-emerald-400 text-sm mb-1">⚡ Tier 3: Alpha Signal Engines</div>
                    <div class="grid grid-cols-1 md:grid-cols-3 gap-3 mt-2 text-gray-300">
                        <div class="bg-dark-bg p-2.5 rounded-lg border border-dark-border">
                            <span class="text-brand-500 font-semibold block">Sniper Entry:</span> หมวด 1 (DeepLOB) + หมวด 2 (OFI) + หมวด 8 (Lead-Lag)
                        </div>
                        <div class="bg-dark-bg p-2.5 rounded-lg border border-dark-border">
                            <span class="text-cyan-400 font-semibold block">Trend Follow:</span> หมวด 5 (Hawkes Burst) + หมวด 9 (Kalman Velocity)
                        </div>
                        <div class="bg-dark-bg p-2.5 rounded-lg border border-dark-border">
                            <span class="text-indigo-400 font-semibold block">Liquidity Provider:</span> หมวด 3 (Avellaneda-Stoikov MM)
                        </div>
                    </div>
                </div>
                <div class="p-4 rounded-xl border border-cyan-500/20 bg-cyan-950/10">
                    <div class="font-bold text-cyan-400 text-sm mb-1">🎯 Tier 4: Optimal Execution & Routing</div>
                    <div class="text-gray-300">หมวด 4 (Almgren-Chriss, Guaranteed VWAP) -> เลือกว่าจะส่งแบบ Passive Limit (กินสเปรด) หรือ Aggressive Market ซอยย่อยตาม Volume Profile ลด Slippage</div>
                </div>
                <div class="p-4 rounded-xl border border-purple-500/20 bg-purple-950/10">
                    <div class="font-bold text-purple-400 text-sm mb-1">📐 Tier 5: Dynamic Position Sizing & Risk Guardian</div>
                    <div class="text-gray-300">หมวด 12 (Fractional Kelly & Volatility Targeting) + หมวด 13 (Rough Volatility Bounds) -> คุม Lot Size ตาม ATR และคุม Daily Max Drawdown 3.0% ตัดไฟอัตโนมัติ</div>
                </div>
            </div>
        </div>
    </div>

    <!-- Data Injection & JavaScript Engine -->
    <script>
        const rawStrategies = {json_data_str};
        let currentCategory = 'ALL';
        let searchQuery = '';

        // Extract Categories
        const categoriesMap = {{}};
        rawStrategies.forEach(s => {{
            if (!categoriesMap[s.category_folder]) {{
                categoriesMap[s.category_folder] = {{
                    id: s.category_folder,
                    title: s.category_title,
                    icon: s.category_icon || '📊',
                    count: 0
                }};
            }}
            categoriesMap[s.category_folder].count++;
        }});

        // Render Category Filter Pills
        const filterContainer = document.getElementById('categoryFilter');
        Object.values(categoriesMap).forEach(c => {{
            const btn = document.createElement('button');
            btn.className = 'cat-pill px-3.5 py-1.5 rounded-xl text-xs font-medium bg-dark-card hover:bg-dark-border text-gray-300 border border-dark-border transition-all whitespace-nowrap flex items-center gap-1.5';
            btn.innerHTML = `<span>${{c.icon}}</span> <span>${{c.title.split(':')[0]}} (${{c.count}})</span>`;
            btn.onclick = () => setCategory(c.id, btn);
            filterContainer.appendChild(btn);
        }});

        function setCategory(catId, btnEl) {{
            currentCategory = catId;
            document.querySelectorAll('.cat-pill').forEach(b => {{
                b.classList.remove('bg-emerald-500', 'text-white', 'border-emerald-400');
                b.classList.add('bg-dark-card', 'text-gray-300', 'border-dark-border');
            }});
            if (btnEl) {{
                btnEl.classList.remove('bg-dark-card', 'text-gray-300', 'border-dark-border');
                btnEl.classList.add('bg-emerald-500', 'text-white', 'border-emerald-400');
            }} else {{
                document.querySelector('.cat-pill').classList.add('bg-emerald-500', 'text-white', 'border-emerald-400');
            }}
            filterStrategies();
        }}

        function filterStrategies() {{
            searchQuery = document.getElementById('searchInput').value.toLowerCase();
            const grid = document.getElementById('strategyGrid');
            grid.innerHTML = '';

            let count = 0;
            rawStrategies.forEach(s => {{
                const matchCat = (currentCategory === 'ALL' || s.category_folder === currentCategory);
                const matchSearch = !searchQuery || 
                    s.title.toLowerCase().includes(searchQuery) ||
                    s.id.toLowerCase().includes(searchQuery) ||
                    s.paper_id.toLowerCase().includes(searchQuery) ||
                    s.entry_trigger.toLowerCase().includes(searchQuery) ||
                    s.strategy_type.toLowerCase().includes(searchQuery);

                if (matchCat && matchSearch) {{
                    count++;
                    const card = document.createElement('div');
                    card.className = 'bg-dark-card border border-dark-border hover:border-emerald-500/50 rounded-2xl p-5 shadow-lg transition-all hover:-translate-y-1 hover:shadow-emerald-950/20 cursor-pointer flex flex-col justify-between';
                    card.onclick = () => openDetailModal(s);
                    card.innerHTML = `
                        <div>
                            <div class="flex items-center justify-between text-xs mb-2">
                                <span class="px-2.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-medium">
                                    ${{s.category_icon}} ${{s.category_folder.split('_').slice(1,3).join(' ')}}
                                </span>
                                <span class="font-mono text-gray-500 text-[11px]">${{s.id}}</span>
                            </div>
                            <h4 class="font-bold text-sm text-gray-100 line-clamp-2 mb-2 group-hover:text-emerald-400 transition-colors">
                                ${{s.title}}
                            </h4>
                            <p class="text-xs text-gray-400 line-clamp-2 mb-3">
                                <strong class="text-emerald-400 font-semibold">เข้า:</strong> ${{s.entry_trigger}}
                            </p>
                        </div>
                        <div class="pt-3 border-t border-dark-border/60 flex items-center justify-between text-[11px] text-gray-500">
                            <span>arXiv:${{s.paper_id}}</span>
                            <span class="text-emerald-400 hover:underline font-semibold flex items-center gap-1">ดูรายละเอียด →</span>
                        </div>
                    `;
                    grid.appendChild(card);
                }}
            }});
            document.getElementById('visibleCount').innerText = count;
        }}

        function openDetailModal(s) {{
            document.getElementById('modalId').innerText = s.id;
            document.getElementById('modalIcon').innerText = s.category_icon || '📊';
            document.getElementById('modalCategory').innerText = s.category_title;
            document.getElementById('modalTitle').innerText = s.title;
            document.getElementById('modalAuthors').innerText = `${{s.authors.join(', ')}} (${{s.published}})`;
            document.getElementById('modalHtmlLink').href = s.html_url;
            document.getElementById('modalPdfLink').href = s.pdf_url;
            document.getElementById('modalType').innerText = s.strategy_type;
            document.getElementById('modalProfit').innerText = s.profit_mechanism;
            document.getElementById('modalEntry').innerText = s.entry_trigger;
            document.getElementById('modalExit').innerText = s.exit_trigger;
            document.getElementById('modalStrengths').innerText = s.strengths;
            document.getElementById('modalWeaknesses').innerText = s.weaknesses;
            document.getElementById('modalRisks').innerText = s.risks;
            document.getElementById('modalAbstract').innerText = s.abstract;

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

with open(web_html_path, "w", encoding="utf-8") as f:
    f.write(html_template)

print(f"Interactive Web Portal generated at: {web_html_path}")
