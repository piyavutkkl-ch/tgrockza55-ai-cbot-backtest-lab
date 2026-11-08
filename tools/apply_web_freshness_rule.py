import os
import json
import re

REPO_ROOT = r'd:\cbot-atgvt'
DOCS_DATA = os.path.join(REPO_ROOT, 'docs', 'data')
FLYWHEEL_JSON = os.path.join(DOCS_DATA, 'flywheel_cycles.json')
INDEX_HTML = os.path.join(REPO_ROOT, 'docs', 'index.html')
FLYWHEEL_ENGINE = os.path.join(REPO_ROOT, 'research', 'flywheel_engine.py')
RULES_MD = os.path.join(REPO_ROOT, 'zz_zz PAPER', 'SYSTEM_RULES_AND_GOVERNANCE.md')

def update_flywheel_json():
    if os.path.exists(FLYWHEEL_JSON):
        with open(FLYWHEEL_JSON, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        takeaways = [
            "1. ข้อมูล L2 DOM 25 ชั้นและ Real Tick Spreads คือหัวใจสำคัญที่ไม่สามารถดึงย้อนหลังจากโบรคเกอร์ได้",
            "2. Fading จุดกลับตัวตามกำแพงสภาพคล่อง (DOM Absorption) ในช่วงตลาด Asia ชนะตลาดต่อเนื่อง 100% ทุกวัน (PF 2.01)",
            "3. การใช้ High Wall 0.05 ร่วมกับเซสชัน London ช่วยเอาชนะต้นทุน Spread Drag 79.5% บน ETHUSD ได้สำเร็จ",
            "4. 4 เสาหลัก (Structural Anchor + Displacement CHoCH + News Void Gate + Dynamic SL 10-20 pips) เป็นรากฐานของความเสี่ยงจำกัด",
            "5. กฎพัฒนาหน้าเว็บให้เป็นปัจจุบัน (Web Dashboard Freshness Mandate): ทุกการวิจัย รอบสวีป และสถานะบอทสด ต้องซิงค์ขึ้น Dashboard เสมอ",
            "6. กฎความยืดหยุ่นในหมวด 3 และ 4 (Adaptive Strategy Evolution): ปรับเปลี่ยนกฎเข้าออกและพารามิเตอร์ได้ตลอดเวลาเมื่อพบโมเดลที่ทำกำไรได้ดีกว่า"
        ]
        
        if "accumulated_learnings" in data:
            data["accumulated_learnings"]["core_takeaways"] = takeaways
            
        with open(FLYWHEEL_JSON, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print("Updated docs/data/flywheel_cycles.json")

def update_flywheel_engine():
    if os.path.exists(FLYWHEEL_ENGINE):
        with open(FLYWHEEL_ENGINE, 'r', encoding='utf-8') as f:
            code = f.read()

        old_core = """CORE_TAKEAWAYS = [
    "1. ข้อมูล L2 DOM 25 ชั้นและ Real Tick Spreads คือหัวใจสำคัญที่ไม่สามารถดึงย้อนหลังจากโบรคเกอร์ได้",
    "2. Fading จุดกลับตัวตามกำแพงสภาพคล่อง (DOM Absorption) ในช่วงตลาด Asia ชนะตลาดต่อเนื่อง 100% ทุกวัน (PF 2.01)",
    "3. การใช้ High Wall 0.05 ร่วมกับเซสชัน London ช่วยเอาชนะต้นทุน Spread Drag 79.5% บน ETHUSD ได้สำเร็จ",
    "4. 4 เสาหลัก (Structural Anchor + Displacement CHoCH + News Void Gate + Dynamic SL 10-20 pips) เป็นรากฐานของความเสี่ยงจำกัด"
]"""

        new_core = """CORE_TAKEAWAYS = [
    "1. ข้อมูล L2 DOM 25 ชั้นและ Real Tick Spreads คือหัวใจสำคัญที่ไม่สามารถดึงย้อนหลังจากโบรคเกอร์ได้",
    "2. Fading จุดกลับตัวตามกำแพงสภาพคล่อง (DOM Absorption) ในช่วงตลาด Asia ชนะตลาดต่อเนื่อง 100% ทุกวัน (PF 2.01)",
    "3. การใช้ High Wall 0.05 ร่วมกับเซสชัน London ช่วยเอาชนะต้นทุน Spread Drag 79.5% บน ETHUSD ได้สำเร็จ",
    "4. 4 เสาหลัก (Structural Anchor + Displacement CHoCH + News Void Gate + Dynamic SL 10-20 pips) เป็นรากฐานของความเสี่ยงจำกัด",
    "5. กฎพัฒนาหน้าเว็บให้เป็นปัจจุบัน (Web Dashboard Freshness Mandate): ทุกการวิจัย รอบสวีป และสถานะบอทสด ต้องซิงค์ขึ้น Dashboard เสมอ",
    "6. กฎความยืดหยุ่นในหมวด 3 และ 4 (Adaptive Strategy Evolution): ปรับเปลี่ยนกฎเข้าออกและพารามิเตอร์ได้ตลอดเวลาเมื่อพบโมเดลที่ทำกำไรได้ดีกว่า"
]"""

        if old_core in code:
            code = code.replace(old_core, new_core)
            with open(FLYWHEEL_ENGINE, 'w', encoding='utf-8') as f:
                f.write(code)
            print("Updated research/flywheel_engine.py")

def update_index_html():
    if os.path.exists(INDEX_HTML):
        with open(INDEX_HTML, 'r', encoding='utf-8') as f:
            html = f.read()

        old_section = """      <!-- Core Institutional Takeaways (4 กฎทองเชิงประจักษ์) -->
      <div class="p-3.5 rounded-xl bg-slate-950 border border-indigo-500/30 text-xs space-y-2">
        <div class="font-extrabold text-white flex items-center gap-2">
          <span>🏛️</span> <span>4 กฎทองเชิงประจักษ์ที่ค้นพบจากการรันจริง (Core Institutional Takeaways):</span>
        </div>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-2 text-slate-300 text-[11px] font-mono">
          <div class="flex items-start gap-1.5 p-2 rounded-lg bg-slate-900/60 border border-slate-800/80">
            <span class="text-emerald-400 font-bold">1.</span>
            <span>ห้ามเทรดช่วงข่าว Extreme (CPI, NFP, FOMC) เด็ดขาด — การหลบข่าวคือปัจจัยหลักที่ทำให้กลยุทธ์พลิกกลับมามีกำไร</span>
          </div>
          <div class="flex items-start gap-1.5 p-2 rounded-lg bg-slate-900/60 border border-slate-800/80">
            <span class="text-emerald-400 font-bold">2.</span>
            <span>อย่าถือครองสั้นเกินไปในสภาวะสเปรดถ่าง — ระยะถือครอง 15-60 นาทีให้ Expectancy เหนือต้นทุนค่าคอมมิชชันและสเปรด</span>
          </div>
          <div class="flex items-start gap-1.5 p-2 rounded-lg bg-slate-900/60 border border-slate-800/80">
            <span class="text-emerald-400 font-bold">3.</span>
            <span>ต้องใช้ข้อมูล Order Book DOM Level 2 (25 ชั้น) เพื่อดูการดูดซับสภาพคล่อง แทนการพึ่งพาแค่อินดิเคเตอร์แท่งเทียนย้อนหลัง</span>
          </div>
          <div class="flex items-start gap-1.5 p-2 rounded-lg bg-slate-900/60 border border-slate-800/80">
            <span class="text-emerald-400 font-bold">4.</span>
            <span>ใช้ Quantum Stealth RAM SL (&plusmn;5% Jitter) ซ่อนระดับตัดขาดทุนในหน่วยความจำ เพื่อป้องกันอัลกอริทึมล่าสภาพคล่อง (Stop Hunting)</span>
          </div>
        </div>
      </div>"""

        new_section = """      <!-- Core Institutional Governance & Rules (กฎเหล็กและระเบียบบริหารจัดการระบบ) -->
      <div class="p-4 rounded-xl bg-slate-950 border border-indigo-500/40 text-xs space-y-3 shadow-lg">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-2">
          <div class="font-extrabold text-white flex items-center gap-2 text-sm">
            <span>🏛️</span> <span>กฎเหล็กและระเบียบบริหารจัดการระบบเชิงสถาบัน (System Governance & Institutional Rules)</span>
          </div>
          <span class="px-2.5 py-0.5 rounded text-[9px] font-mono font-bold bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 w-fit">ENFORCED IN REAL-TIME</span>
        </div>
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2.5 text-slate-300 text-[11px] font-mono">
          <div class="flex items-start gap-2 p-2.5 rounded-lg bg-slate-900/70 border border-slate-800/80">
            <span class="text-emerald-400 font-bold shrink-0">1.</span>
            <span><strong>News Void Gate:</strong> ห้ามเทรดช่วงข่าว Extreme (CPI, NFP, FOMC) เด็ดขาด 30m ก่อน / 120m หลังข่าว</span>
          </div>
          <div class="flex items-start gap-2 p-2.5 rounded-lg bg-slate-900/70 border border-slate-800/80">
            <span class="text-emerald-400 font-bold shrink-0">2.</span>
            <span><strong>Spread Friction Defense:</strong> ถือครอง 15-60 นาที และเข้าเมื่อสเปรดต่ำ เพื่อให้กำไรครอบคลุมค่าคอมมิชชัน</span>
          </div>
          <div class="flex items-start gap-2 p-2.5 rounded-lg bg-slate-900/70 border border-slate-800/80">
            <span class="text-emerald-400 font-bold shrink-0">3.</span>
            <span><strong>Pure Live Microstructure:</strong> พัฒนาบนข้อมูลเก็บสด L2 DOM 25 ชั้น + Spreads จริง 100% เท่านั้น</span>
          </div>
          <div class="flex items-start gap-2 p-2.5 rounded-lg bg-slate-900/70 border border-slate-800/80">
            <span class="text-emerald-400 font-bold shrink-0">4.</span>
            <span><strong>Quantum Stealth RAM SL:</strong> ซ่อน Stop Loss ในหน่วยความจำ (±5% Jitter) ป้องกัน Stop Hunting</span>
          </div>
          <div class="flex items-start gap-2 p-2.5 rounded-lg bg-cyan-950/40 border border-cyan-500/50">
            <span class="text-cyan-400 font-bold shrink-0">5.</span>
            <span><strong class="text-cyan-300">กฎพัฒนาหน้าเว็บให้เป็นปัจจุบัน:</strong> ทุกความก้าวหน้า รอบ Flywheel และข้อมูลสด ต้องอัปเดตและซิงค์ขึ้นหน้าเว็บทันที</span>
          </div>
          <div class="flex items-start gap-2 p-2.5 rounded-lg bg-blue-950/40 border border-blue-500/50">
            <span class="text-blue-400 font-bold shrink-0">6.</span>
            <span><strong class="text-blue-300">กฎความยืดหยุ่นในหมวด 3 &amp; 4:</strong> ปรับเปลี่ยน Entry/Exit และพารามิเตอร์ได้ตลอดเวลาเมื่อพบโมเดลที่ทำกำไรได้ดีกว่า</span>
          </div>
        </div>
      </div>"""

        if old_section in html:
            html = html.replace(old_section, new_section)
            with open(INDEX_HTML, 'w', encoding='utf-8') as f:
                f.write(html)
            print("Updated docs/index.html")
        else:
            print("Target section in index.html not found, will check fallback.")

def create_system_rules_paper():
    content = """# ระเบียบและกฎเหล็กการบริหารจัดการระบบเชิงสถาบัน (System Governance & Operating Rules)
> **สถานะ**: มีผลบังคับใช้แบบ Real-Time (Enforced Automatically across Agents, Daemons & UI)  
> **วันที่มีผลบังคับใช้ล่าสุด**: 08 พฤศจิกายน 2026  
> **การกำกับดูแล**: Autonomous Flywheel Pipeline & 24/7 Watchdog Supervisor

---

## สารบัญหมวดกฎเกณฑ์ (Rule Categories)
1. [หมวดที่ 1: ระดับนโยบายสัจธรรมและความจริงแท้ (Truth & Governance Rules)](#หมวดที่-1-ระดับนโยบายสัจธรรมและความจริงแท้)
2. [หมวดที่ 2: ระบบความต่อเนื่องและการกู้คืนอัตโนมัติ (Watchdog & Continuous Ingestion)](#หมวดที่-2-ระบบความต่อเนื่องและการกู้คืนอัตโนมัติ)
3. [หมวดที่ 3: กฎเหล็กเทคนิคคณิตศาสตร์ 4 เสาหลัก (The 4 Quantitative Pillars)](#หมวดที่-3-กฎเหล็กเทคนิคคณิตศาสตร์-4-เสาหลัก)
4. [หมวดที่ 4: การกระจายรอบ 4 เซสชันตลอด 24 ชั่วโมง (24-Hour Multi-Session Matrix)](#หมวดที่-4-การกระจายรอบ-4-เซสชันตลอด-24-ชั่วโมง)
5. [หมวดที่ 5: กฎการพัฒนาหน้าเว็บให้เป็นปัจจุบันตลอดเวลา (Real-Time Web Freshness Mandate)](#หมวดที่-5-กฎการพัฒนาหน้าเว็บให้เป็นปัจจุบันตลอดเวลา)
6. [หมวดที่ 6: กฎความยืดหยุ่นในการพัฒนากลยุทธ์และการสวีปพารามิเตอร์ (Adaptive Evolution in Stage 3 & 4)](#หมวดที่-6-กฎความยืดหยุ่นในการพัฒนากลยุทธ์และการสวีปพารามิเตอร์)

---

### หมวดที่ 1: ระดับนโยบายสัจธรรมและความจริงแท้
1. **สัจธรรม 100% (Truth Reset & Zero Hallucination):**
   * ห้ามเดาหรือสมมติตัวเลขผลกำไรใดๆ ตัวเลขทั้งหมดบน Dashboard ต้องมาจากการตรวจสอบไฟล์ดิบจริง (`%LOCALAPPDATA%\\BacktestLab\\live`) และพอร์ตจริง Pepperstone #5258778 เท่านั้น
2. **โรงงานคัดกรองกลยุทธ์ (The Strategy Foundry):**
   * เปลี่ยนแนวคิดจาก *"บอทที่ฉลาดขึ้นเรื่อยๆ"* สู่ *"โรงงานคัดกรองกลยุทธ์"*: สร้างสมมติฐานจำนวนมาก โค้ดคณิตศาสตร์คัดทิ้ง 98% ตัวที่รอดอนุญาตให้ทดสอบสดด้วยเงินน้อยที่สุด (0.01 Lot)
3. **สุสานกลยุทธ์ (The Failure Graveyard):**
   * บันทึกทุกความล้มเหลวลงในสุสานกลยุทธ์ เพื่อป้องกันไม่ให้ระบบหรือ AI ย้อนกลับไปค้นหาหรือทำซ้ำข้อผิดพลาดเดิม (Negative Knowledge Repository)
4. **บัญญัติข้อมูลเก็บสดเท่านั้น (Pure Live Microstructure Data Mandate):**
   * การวิจัย การทดสอบ และการพัฒนาต่อยอด ต้องใช้เฉพาะข้อมูลที่บันทึกสดจริงที่มี Order Book Level 2 (25 ชั้น), Tick Spreads สด และ Order Flow Delta เท่านั้น ห้ามใช้ข้อมูลแท่งเทียนสังเคราะห์ย้อนหลังจากโบรกเกอร์

---

### หมวดที่ 2: ระบบความต่อเนื่องและการกู้คืนอัตโนมัติ
1. **บันทึกข้อมูลตลอดเวลา 24/7 (Continuous Ingestion):**
   * ระบบต้องรัน Background Daemon เก็บข้อมูล Tick และ DOM Snapshot ของคู่เงินที่ตลาดเปิดอยู่ (BTCUSD, ETHUSD) ตลอด 24 ชั่วโมง ไม่มีวันหยุด
2. **ตรวจจับการหยุดทำงานทุก 15 วินาที (Watchdog Heartbeat & Inactivity Recovery):**
   * มี Supervisor ตรวจสอบไฟล์ `.csv` หากไม่มีข้อมูลสดใหม่เกิน 180 วินาที ให้บันทึกเวลาที่หยุด สั่งปิดโปรเซสที่ค้าง และเปิดโปรเซสใหม่ขึ้นมาทำงานต่อทันที
3. **โหมดสแตนด์บายตลาดทองคำ (Weekend Standby for Gold):**
   * วันเสาร์-อาทิตย์ ตลาด XAUUSD ปิดทำการ ให้ระบบเข้าสู่สถานะ `WEEKEND_STANDBY` และตรวจจับเวลาเปิดตลาด (วันอาทิตย์ 22:00 UTC / จันทร์ 05:00 น. ไทย) เพื่อเริ่มบันทึกต่ออัตโนมัติ

---

### หมวดที่ 3: กฎเหล็กเทคนิคคณิตศาสตร์ 4 เสาหลัก
1. **Pillar 1: Structural Anchor (จุดอ้างอิงโครงสร้างจริง):**
   * ห้ามเทรดกลางอากาศ เข้าทำได้เฉพาะเมื่อมีกำแพงสภาพคล่อง L2 DOM Depth $> 1.4\\times$, กรอบ Auction Market Theory (AMT 70% Value Area) หรือ VWAP Bands $\\ge 4.2\\sigma$
2. **Pillar 2: Timing & Confirmation (จังหวะและการยืนยัน):**
   * ห้ามรับมีด ต้องรอการกลับตัวแบบ Displacement CHoCH บนกรอบ M1/M5 ร่วมกับ Retest Fibo Golden Zone (50–65%) หรือ Cumulative Volume Delta (CVD) Divergence
3. **Pillar 3: Event & Volatility Gate (เกราะป้องกันความผันผวน):**
   * **News Void Gate:** งดส่งคำสั่ง 30 นาทีก่อน และ 120 นาทีหลังข่าวรุนแรง (CPI, NFP, FOMC)
   * **Spread Shield:** ปฏิเสธการเข้าออเดอร์ทันทีเมื่อสเปรดถ่างเกิน 1.5 เท่าของค่าเฉลี่ยปกติ
4. **Pillar 4: Structural Exit & Dynamic Risk (จุดออกและบริหารความเสี่ยง):**
   * ใช้ Structural SL หลังกำแพงสภาพคล่อง (10–20 pips), ล็อค Breakeven ที่ 1.0R และใช้ Smart DOM Exit ปิดออเดอร์เมื่อสภาพคล่องฝั่งตรงข้ามเริ่มดูดซับ

---

### หมวดที่ 4: การกระจายรอบ 4 เซสชันตลอด 24 ชั่วโมง
* **เซสชัน 1: เอเชีย (07:00 – 14:00 น. ไทย):** เน้น BTCUSD กรอบแคบ สเปรดต่ำ ใช้ `DOM_ABSORPTION` Fading
* **เซสชัน 2: ลอนดอน (14:00 – 20:00 น. ไทย):** เน้น ETHUSD ใช้ High Wall 0.05 เพื่อเอาชนะ Spread Drag 79.5%
* **เซสชัน 3: นิวยอร์ก (20:00 – 03:00 น. ไทย):** เน้น XAUUSD ใช้ Value Area Fade ร่วมกับ News Void Gate
* **เซสชัน 4: คริปโต 24/7 (BTC/ETH ตลอดคืน):** อาศัย CVD Divergence และ Smart DOM Exit

---

### หมวดที่ 5: กฎการพัฒนาหน้าเว็บให้เป็นปัจจุบันตลอดเวลา (Real-Time Web Freshness Mandate)
> **กฎใหม่ตามคำสั่งผู้ใช้**:
1. **Immediate UI Sync:** ทุกครั้งที่มีการวิจัย, การทดสอบสวีปพารามิเตอร์, การขยับรอบวงจร Flywheel, หรือการปรับเปลี่ยนกฎ ต้องอัปเดตหน้าเว็บ `docs/index.html` และชุดข้อมูลใน `docs/data/` ทันที
2. **Zero Stale State:** ห้ามปล่อยให้หน้าเว็บแสดงผลค้างสถานะเดิม ข้อมูลสถานะบอท (Watchdog), Balance, PnL รายวัน, และ Badge รอบปัจจุบัน ต้องดึงจากสัจธรรมล่าสุดเสมอ
3. **Git Sync Pipeline:** ต้องมีกระบวนการคอมมิตและพุชขึ้นสู่ GitHub Pages อย่างสม่ำเสมอ เพื่อให้ผู้ใช้สามารถตรวจสอบความคืบหน้าผ่านมือถือหรือเบราว์เซอร์ภายนอกได้ทุกที่ทุกเวลา

---

### หมวดที่ 6: กฎความยืดหยุ่นในการพัฒนากลยุทธ์และการสวีปพารามิเตอร์ (Adaptive Evolution in Stage 3 & 4)
> **กฎใหม่ตามคำสั่งผู้ใช้**:
1. **Non-Rigid Rules in Stage 3 & 4:** กฎเกณฑ์ในหมวด 3 (Strategy Dev) และหมวด 4 (Backtest & Optimization) ไม่ใช่กฎตายตัว สามารถปรับปรุง แก้ไข หรือสร้างตรรกะใหม่ได้ตลอดเวลา
2. **Superior Strategy Replacement:** หากการจำลองบนข้อมูลสดพบกลยุทธ์ใหม่ที่ให้ Profit Factor สูงกว่า, Daily Win Rate สม่ำเสมอกว่า (เป้าหมายกำไรทุกวัน), หรือ Drawdown ต่ำกว่า ให้มีสิทธิ์ปรับเปลี่ยนกฎเดิมและเลื่อนระดับกลยุทธ์ใหม่ขึ้นมาเป็น Master Champion ประจำเซสชันได้ทันที
3. **Safety Boundaries:** คงไว้เฉพาะกฎความปลอดภัยขั้นวิกฤต (Zero Lookahead Bias และ Fail-Closed Stop Loss) นอกเหนือจากนั้นเปิดกว้างให้ระบบวิวัฒนาการเพื่อแสวงหากำไรสูงสุดอย่างต่อเนื่อง
"""
    os.makedirs(os.path.dirname(RULES_MD), exist_ok=True)
    with open(RULES_MD, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Created zz_zz PAPER/SYSTEM_RULES_AND_GOVERNANCE.md")

if __name__ == '__main__':
    update_flywheel_json()
    update_flywheel_engine()
    update_index_html()
    create_system_rules_paper()
