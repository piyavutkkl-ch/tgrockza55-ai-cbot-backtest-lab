import os
import sys
import json
import re

sys.stdout.reconfigure(encoding='utf-8')

def safe_filename(name):
    clean = re.sub(r'[^\w\-_\. ]', '_', name)
    clean = re.sub(r'_+', '_', clean)
    return clean[:45].strip(' _')

base_dir = "d:/cbot-atgvt/zz_zz PAPER"
db_path = os.path.join(base_dir, "papers_database.json")

with open(db_path, encoding='utf-8') as f:
    papers = json.load(f)

print(f"Total papers in database to index: {len(papers)}")

all_categories_meta = {
    "01_lob_and_deep_learning": {
        "title_th": "หมวดที่ 1: โครงสร้าง Limit Order Book (LOB/DOM) และโมเดล Deep Learning",
        "title_en": "Limit Order Book Structure & Deep Learning Architectures",
        "desc_th": "การนำข้อมูล Level 2 (Bid/Ask Price & Depth) มาสร้างฟีเจอร์เชิงพื้นที่และลำดับเวลา ป้อนเข้าโมเดล CNN/LSTM/Transformers/T-KAN เพื่อพยากรณ์การเคลื่อนที่ของราคา Mid-Price",
        "bot_relevance": "แกนหลักในการสกัดฟีเจอร์จาก DOM scraping เพื่อเทรน Machine Learning Robot ทำนายทิศทางราคาระยะสั้น (Scalping M1/M5) และตรวจจับคำสั่งหลอก (Spoofing Triaging)",
        "icon": "🧠"
    },
    "02_order_flow_imbalance": {
        "title_th": "หมวดที่ 2: แรงกดดันคำสั่งซื้อขาย (Order Flow Imbalance - OFI) และ Price Impact",
        "title_en": "Order Flow Imbalance (OFI) & Price Impact Dynamics",
        "desc_th": "ทฤษฎีการคำนวณแรงซื้อขายสุทธิ (Order Flow Imbalance) จากการเปลี่ยนแปลงของ Best Bid/Ask, Limit Orders, Market Orders และ Cancellations รวมถึง Multi-Level OFI และ Cross-Asset Impact",
        "bot_relevance": "ดัชนีตรวจจับแรงซื้อขายสถาบันที่เกิดขึ้นจริง แม่นยำกว่าแท่งเทียน ช่วยจับจังหวะการถูกดูดซับสภาพคล่อง (Absorption) หรือการหมดแรงของฝั่งตรงข้ามก่อนสไนเปอร์เข้าออเดอร์",
        "icon": "⚡"
    },
    "03_market_making_and_spread": {
        "title_th": "หมวดที่ 3: กลยุทธ์ Market Making, Bid/Ask Spreads และการคุม Inventory Risk",
        "title_en": "Market Making Algorithms, Spread Dynamics & Inventory Control",
        "desc_th": "แบบจำลองคณิตศาสตร์สำหรับการวางคำสั่ง Bid/Ask แบบ Passive (Avellaneda-Stoikov & Guéant models), การคำนวณ Reservation Price และการคุมความเสี่ยงเมื่อพอร์ตถือสถานะไม่สมดุล",
        "bot_relevance": "ใช้กำหนดระยะกางของสเปรดและจุดตั้ง Limit Order / Take Profit ตามความผันผวน และใช้เอียงราคาเสนอซื้อขาย (Quote Skewing) ตามทิศทางโมเมนตัม",
        "icon": "⚖️"
    },
    "04_optimal_execution_and_vwap": {
        "title_th": "หมวดที่ 4: การส่งคำสั่งอย่างคุ้มค่า (Optimal Execution) และกลยุทธ์ VWAP/TWAP",
        "title_en": "Optimal Execution, Market Impact Minimization & VWAP Strategies",
        "desc_th": "อัลกอริทึมการซอยคำสั่ง (Order Slicing / TWAP / VWAP) เพื่อลดค่า Slippage และ Market Impact รวมถึงการใช้ Reinforcement Learning ในการเลือกส่ง Market Order เทียบกับ Limit Order",
        "bot_relevance": "แก้ปัญหาบอทกำไรใน Backtest แต่ขาดทุนในตลาดจริงเพราะโดนกินสเปรดและ Slippage โดยช่วยคำนวณเส้นทางการแบ่งไม้เข้า-ออกที่ดีที่สุด",
        "icon": "🎯"
    },
    "05_hawkes_and_event_clustering": {
        "title_th": "หมวดที่ 5: แบบจำลอง Hawkes Processes และการจับกลุ่มคำสั่งผิดปกติ (Event Clustering)",
        "title_en": "Hawkes Processes & High-Frequency Trade Clustering",
        "desc_th": "แบบจำลอง Self-Exciting Point Process ที่อธิบายว่าการเกิดออเดอร์หนึ่งจะกระตุ้นให้ออเดอร์อื่นตามมาเป็นลูกโซ่ ช่วยในการวัดความตื่นตัวของตลาดและตรวจจับ Flash Crash / News Spikes",
        "bot_relevance": "ตรวจจับว่าตลาดกำลังอยู่ในภาวะเงียบสงบหรือกำลังเกิดพายุคำสั่ง (Trade Clustering) เพื่อสั่งให้บอทเปิดโหมด Scalping ทำรอบเร็ว หรือปิดระบบเพื่อหลบช่วงข่าวกระชาก",
        "icon": "🌊"
    },
    "06_gold_commodity_and_macro": {
        "title_th": "หมวดที่ 6: จุลภาคตลาดทองคำ (Gold/XAU) และสินทรัพย์ความผันผวนสูง",
        "title_en": "Gold (XAU) Microstructure, Alpha & Multi-Asset Allocation",
        "desc_th": "พฤติกรรมโครงสร้างสภาพคล่องของทองคำ (XAUUSD / Gold Futures), สัญญาณ Benchmark-Neutral Alpha, ช่วงเวลา London / NY Session Open, และการจัดสรรพอร์ตตาม Regime",
        "bot_relevance": "คู่มือเชิงลึกสำหรับสินทรัพย์หลักของโปรเจกต์ (XAUUSD) ในการหาจังหวะ Forecast-to-Fill และคุม Drawdown ในช่วงตลาดผันผวนสูง",
        "icon": "🥇"
    },
    "07_regime_detection_and_hmm": {
        "title_th": "หมวดที่ 7: การจำแนกสภาวะตลาด (Market Regime Detection) และแบบจำลอง HMM",
        "title_en": "Market Regime Detection & Hidden Markov Models (HMM)",
        "desc_th": "การระบุสภาวะตลาดแบบไม่อิงคนมอง (Unsupervised Regime Clustering) เช่น สภาวะ Low-Vol Trend, High-Vol Trend, Choppy Range และ Liquidity Squeeze",
        "bot_relevance": "ทำหน้าที่เป็น 'สวิตช์หลักของระบบ' (Master Strategy Router) เพื่อเลือกเปิดบอทที่เหมาะสมกับสภาพตลาดขณะนั้น และปิดบอทที่ไม่ควรทำงาน",
        "icon": "🎛️"
    },
    "08_lead_lag_and_latency": {
        "title_th": "หมวดที่ 8: ความสัมพันธ์ตัวนำ-ตัวตาม (Lead-Lag Microstructure) และ Latency Arbitrage",
        "title_en": "Lead-Lag Relationships & Cross-Market Latency Dynamics",
        "desc_th": "การวัดความหน่วงของข้อมูลและกระแสคำสั่งระหว่างตลาด เพื่อหาว่าสินทรัพย์หรือ Exchange ใดขยับก่อน และตัวใดขยับตาม",
        "bot_relevance": "ใช้ยิงดักหน้า (Preemptive Order) เช่น ดูว่า Binance นำ cTrader อยู่กี่ร้อย ms หรือดูว่า Bond Yield/DXY ส่งผลนำ XAUUSD ล่วงหน้ากี่วินาที",
        "icon": "🏎️"
    },
    "09_signal_processing_and_kalman": {
        "title_th": "หมวดที่ 9: การประมวลผลสัญญาณดิจิทัล (Digital Signal Processing) และ Kalman Filtering",
        "title_en": "Signal Processing, Kalman Filtering & Zero-Lag Noise Reduction",
        "desc_th": "การสกัด 'สัญญาณแท้จริง (Underlying State)' ออกจาก 'สัญญาณรบกวน (Market Noise)' โดยไม่เกิดปัญหาความหน่วงช้า (No Lagging Whipsaw)",
        "bot_relevance": "ใช้แทน Moving Average ทั่วไป ทำให้จับจุดกลับตัวและทิศทางได้ทันทีโดยไม่ถูกกราฟหลอกตัดขึ้นตัดลงบ่อยๆ",
        "icon": "🎯"
    },
    "10_synthetic_data_and_simulation": {
        "title_th": "หมวดที่ 10: ข้อมูลตลาดสังเคราะห์ (Synthetic Market Data) และ Diffusion Models",
        "title_en": "Synthetic LOB, Diffusion Models & Market Simulation",
        "desc_th": "การสร้างข้อมูลจำลอง Order Book และ Tick Data นับล้านฉากทัศน์ที่มีความสมจริงทางสถิติ เพื่อแก้ปัญหา Overfitting และทดสอบภาวะวิกฤติ",
        "bot_relevance": "ใช้ Stress-test บอทก่อนลงเงินจริง เพื่อทดสอบว่าบอทจะรอดหรือไม่หากเกิดเหตุการณ์ Black Swan ที่ไม่เคยเกิดขึ้นในประวัติศาสตร์ 5 ปีหลัง",
        "icon": "🧪"
    },
    "11_financial_llm_and_sentiment": {
        "title_th": "หมวดที่ 11: ปัญญาประดิษฐ์ประมวลผลภาษา (Financial LLMs) และการเทรดข่าว (Sentiment Trading)",
        "title_en": "Financial LLMs, NLP & News Event Sentiment Trading",
        "desc_th": "การแปลงพาดหัวข่าว คำแถลงของธนาคารกลาง และรายงานเศรษฐกิจเป็นคะแนนทิศทางตลาด (Sentiment Score) ภายในเวลาเสี้ยววินาที",
        "bot_relevance": "ช่วยให้บอทรู้ข่าวและปรับสถานะพอร์ตก่อนที่นักลงทุนรายย่อยจะอ่านข่าวจบ ป้องกันการติดดอยช่วงประกาศตัวเลขสำคัญ (FOMC/CPI/NFP)",
        "icon": "🤖"
    },
    "12_position_sizing_and_risk": {
        "title_th": "หมวดที่ 12: การคำนวณขนาดไม้ (Position Sizing), Kelly Criterion และการคุม Drawdown",
        "title_en": "Mathematical Position Sizing, Kelly Criterion & Drawdown Control",
        "desc_th": "แบบจำลองคณิตศาสตร์สำหรับการจัดสรรเงินทุน (Money Management) และการปรับ Lot Size แบบ Dynamic ตามระดับความผันผวน",
        "bot_relevance": "หัวใจที่ตัดสินความอยู่รอดในระยะยาว ปรับลด Lot อัตโนมัติเมื่อความผันผวนสูง เพื่อให้ความเสี่ยงต่อดอลลาร์คงที่ ป้องกันพอร์ตแตก",
        "icon": "📐"
    },
    "13_rough_volatility_and_jumps": {
        "title_th": "หมวดที่ 13: ฟิสิกส์ความขรุขระของราคา (Rough Volatility) และการกระโดดของราคา (Jumps)",
        "title_en": "Rough Volatility, Fractional Dynamics & Price Jumps",
        "desc_th": "ทฤษฎีความขรุขระของตลาดการเงิน (Hurst Parameter H < 0.5) ที่อธิบายว่าทำไมความผันผวนในกราฟสั้นจึงคมและกระชากกว่า Brownian Motion ปกติ",
        "bot_relevance": "ใช้คำนวณระยะ Stop Loss และ Take Profit เชิงฟิสิกส์ที่แท้จริง ไม่ให้ถูกสวิงสะบัดกิน SL ในช่วงที่ตลาดขรุขระผิดปกติ",
        "icon": "🌊"
    }
}

categorized = {}
for p in papers:
    cat = p.get('category_folder', '01_lob_and_deep_learning')
    categorized.setdefault(cat, []).append(p)

all_papers_flat = []

# Process each category
for cat_id, cat_meta in all_categories_meta.items():
    cat_dir = os.path.join(base_dir, cat_id)
    os.makedirs(cat_dir, exist_ok=True)
    cat_papers = categorized.get(cat_id, [])
    
    cat_readme = [
        f"# {cat_meta['icon']} {cat_meta['title_th']}",
        f"### {cat_meta['title_en']}",
        "",
        f"**ภาพรวมเนื้อหา:** {cat_meta['desc_th']}",
        "",
        f"**ความสำคัญต่อการพัฒนา Bot Trade:** {cat_meta['bot_relevance']}",
        "",
        "---",
        "",
        "## 📚 รายการงานวิจัยในหมวดนี้ (Curated Research Papers)",
        "",
        "| ลำดับ | รหัส arXiv | ชื่องานวิจัย | ผู้แต่ง | ปี | ลิงก์อ่าน |",
        "| :---: | :---: | :--- | :--- | :---: | :---: |"
    ]
    
    for idx, p in enumerate(cat_papers, 1):
        clean_t = p['title'].replace('|', '-')
        authors_short = ", ".join(p['authors'][:2]) + (" et al." if len(p['authors']) > 2 else "")
        pub_year = str(p['published'])[:4] if str(p['published'])[:4].isdigit() else "2026"
        aid = p['base_id']
        slug = safe_filename(clean_t)
        filename = f"{aid}_{slug}.md"
        doc_rel_path = f"{filename}"
        html_link = f"[HTML](https://arxiv.org/html/{p['arxiv_id']})"
        pdf_link = f"[PDF]({p['pdf_url']})"
        
        cat_readme.append(f"| {idx} | [`{aid}`]({doc_rel_path}) | {clean_t} | {authors_short} | {pub_year} | {html_link} / {pdf_link} |")
        
        all_papers_flat.append({
            "idx": len(all_papers_flat) + 1,
            "category_id": cat_id,
            "category_name": cat_meta['title_th'],
            "category_icon": cat_meta['icon'],
            "aid": aid,
            "arxiv_id": p['arxiv_id'],
            "title": clean_t,
            "authors": authors_short,
            "year": pub_year,
            "rel_path": f"{cat_id}/{filename}",
            "html_url": f"https://arxiv.org/html/{p['arxiv_id']}",
            "pdf_url": p['pdf_url'],
            "abstract": p.get('abstract', '')
        })
        
        # Write individual paper dossier
        doc_full_path = os.path.join(cat_dir, filename)
        if not os.path.exists(doc_full_path):
            doc = [
                f"# {clean_t}",
                f"**รหัส arXiv:** [`{p['arxiv_id']}`](https://arxiv.org/abs/{p['arxiv_id']}) | **หมวดหมู่:** `{p.get('primary_cat', 'q-fin')}`",
                f"**ผู้แต่ง:** {', '.join(p['authors'])}",
                f"**วันที่เผยแพร่:** {p['published']}",
                "",
                "## 🔗 ลิงก์เอกสารต้นฉบับ (Original Links)",
                f"- 🌐 **อ่านเวอร์ชัน HTML เต็ม:** [https://arxiv.org/html/{p['arxiv_id']}](https://arxiv.org/html/{p['arxiv_id']}) *(แนะนำ: ไม่ต้องดาวน์โหลดไฟล์)*",
                f"- 📄 **หน้า Abstract:** [https://arxiv.org/abs/{p['arxiv_id']}](https://arxiv.org/abs/{p['arxiv_id']})",
                f"- 📥 **ดาวน์โหลด PDF:** [https://arxiv.org/pdf/{p['arxiv_id']}.pdf](https://arxiv.org/pdf/{p['arxiv_id']}.pdf)",
                "",
                "---",
                "",
                "## 📌 บทคัดย่อ (Abstract)",
                f"> {p['abstract']}",
                "",
                "---",
                "",
                "## 💡 ความเชื่อมโยงและการนำไปใช้ใน Bot Trade (Trading Bot Implementation)",
                f"- **หมวดหมู่:** {cat_meta['title_th']}",
                f"- **แนวทางการประยุกต์ใช้:** {cat_meta['bot_relevance']}",
                "- **ข้อพิจารณาในการเขียนโค้ด (Implementation Notes):**",
                f"  1. **สกัด Feature ที่จำเป็น:** แปลงทฤษฎีในเปเปอร์เป็นฟีเจอร์คำนวณสด (เช่น ความแปรปรวน, สถิติถดถอย, หรือตัวแปรสภาวะ)",
                f"  2. **Latency & Execution:** การคำนวณต้องทำได้แบบ Tick-by-tick หรือ Bar-by-bar โดยไม่กิน CPU ของระบบเทรดจนเกิดความล่าช้า",
                f"  3. **Spread & Slippage Reality:** ผลตอบแทนที่คำนวณได้ต้องหักลบต้นทุนสเปรดและค่าธรรมเนียมจริงของโบรกเกอร์เสมอ",
                "",
                "---",
                "*จัดทำขึ้นสำหรับการวิจัยและพัฒนา Quantitative Trading Robot ในโปรเจกต์ cbot-atgvt*"
            ]
            with open(doc_full_path, "w", encoding="utf-8") as f:
                f.write("\n".join(doc))

    cat_readme.append("\n---\n*สารบัญนี้จัดทำขึ้นสำหรับการค้นคว้าวิจัยเชิงลึกของโปรเจกต์ cbot-atgvt*")
    with open(os.path.join(cat_dir, "README.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(cat_readme))

# Build Master PAPERS_INDEX.md
index_lines = [
    "# 📑 สารบัญงานวิจัยทางการเงินฉบับสมบูรณ์ (Master Quant Papers Index)",
    f"รวบรวมงานวิจัยจาก **arXiv (q-fin: Quantitative Finance)** ทั้งหมด **{len(all_papers_flat)} รายการ** ครอบคลุม **13 มิติสำคัญ** สำหรับพัฒนา Trading Bot, Market Microstructure และ Money Management",
    "",
    "> 💡 **คำแนะนำ:** คลิกอ่านผ่านลิงก์ **HTML** เพื่อเปิดอ่านในเบราว์เซอร์ได้ทันที สะดวก ไม่เปลืองเนื้อที่ และไม่ติดปัญหา Rate Limit",
    "",
    "---",
    "",
    "| ลำดับ | หมวดหมู่ | รหัส arXiv | ชื่องานวิจัย | ผู้แต่ง | ปี | อ่านเอกสาร | สรุปในโปรเจกต์ |",
    "| :---: | :---: | :---: | :--- | :--- | :---: | :---: | :---: |"
]

for p in all_papers_flat:
    index_lines.append(
        f"| {p['idx']} | {p['category_icon']} | `{p['aid']}` | {p['title'][:65]}... | {p['authors']} | {p['year']} | [HTML]({p['html_url']}) / [PDF]({p['pdf_url']}) | [สรุป]({p['rel_path']}) |"
    )

index_lines.append("\n---\n*ฐานข้อมูลนี้อัปเดตอัตโนมัติ พร้อมใช้งานร่วมกับ cTrader และ Python BacktestLab*")
with open(os.path.join(base_dir, "PAPERS_INDEX.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(index_lines))

print(f"Master index generated with {len(all_papers_flat)} papers!")

# Build Master README.md
readme_content = f"""# 🏛️ คู่มือและคลังงานวิจัยทางการเงินฉบับสมบูรณ์สำหรับพัฒนา Trading Bot
## (Quantitative Finance & Microstructure Master Research Repository)

> **เป้าหมายโครงการ:** สกัดทฤษฎีทางคณิตศาสตร์ โครงสร้างตลาดจุลภาค (Market Microstructure), สัญญาณดิจิทัล, และโมเดล Machine Learning/Deep Learning จากงานวิจัยระดับโลก **รวม 141 งานวิจัย ครอบคลุม 13 เสาหลัก** เพื่อนำมาแปลงเป็นอัลกอริทึมเทรดอัตโนมัติ (cTrader C# Robot & Python BacktestLab) สำหรับสินทรัพย์ **XAUUSD (Gold), BTCUSD และ ETHUSD**

---

## ⚡ สรุปแนวทางการเข้าถึงเอกสาร (HTML Full-Text Standard)

เพื่อความรวดเร็วและป้องกันปัญหา **Rate Limit (HTTP 429)**:
1. **อ่านผ่าน HTML ทันที:** arXiv มีหน้าเว็บ HTML เต็มรูปแบบที่ [https://arxiv.org/html/<id>](https://arxiv.org/html/1808.03668) แสดงสูตรคณิตศาสตร์ (LaTeX) และแผนผังโมเดลครบถ้วน
2. **คลังบทสรุปในโฟลเดอร์:** มีเอกสารสรุป (`.md`) ในแต่ละหมวดหมู่พร้อมลิงก์ตรงและข้อพิจารณาในการเขียนโค้ด
3. **ไฟล์ฐานข้อมูล:** จัดเก็บ Metadata ครบ 141 งานวิจัยไว้ใน [`papers_database.json`](file:///d:/cbot-atgvt/zz_zz%20PAPER/papers_database.json)

---

## 🗺️ แผนผัง 13 เสาหลักของงานวิจัย (The 13 Pillars for Quantitative Bot Trading)

| หมวดหมู่ | โฟลเดอร์ | ประโยชน์ต่อ Bot Trade | งานวิจัยเด่น |
| :--- | :--- | :--- | :--- |
| **1. LOB & Deep Learning** 🧠 | [`01_lob_and_deep_learning/`](file:///d:/cbot-atgvt/zz_zz%20PAPER/01_lob_and_deep_learning/) | นำข้อมูล DOM Level 2 (Bid/Ask Depth) ป้อน CNN/LSTM เพื่อทำนายทิศทาง 5 แท่ง M1 | `1808.03668` (DeepLOB)<br>`2403.13429` (Spoofing TCN) |
| **2. Order Flow Imbalance** ⚡ | [`02_order_flow_imbalance/`](file:///d:/cbot-atgvt/zz_zz%20PAPER/02_order_flow_imbalance/) | คำนวณแรงซื้อขายสุทธิ (OFI) จับจังหวะ Absorption และวัด Price Impact | `1011.6402` (Cont & Stoikov)<br>`2112.02947` (Multi-level OFI) |
| **3. Market Making & Spread** ⚖️ | [`03_market_making_and_spread/`](file:///d:/cbot-atgvt/zz_zz%20PAPER/03_market_making_and_spread/) | วางคำสั่ง Bid/Ask แบบ Passive, ปรับสเปรดตาม Volatility และคุม Inventory | `1605.01862` (Guéant Master MM)<br>`1105.3115` (Inventory Risk) |
| **4. Optimal Execution & VWAP** 🎯 | [`04_optimal_execution_and_vwap/`](file:///d:/cbot-atgvt/zz_zz%20PAPER/04_optimal_execution_and_vwap/) | ซอยคำสั่ง (Slicing) ลด Slippage และยิงตามเส้น VWAP สถาบัน | `1409.2618` (Dynamic OFI Slicing)<br>`1306.2832` (Guaranteed VWAP) |
| **5. Hawkes Event Clustering** 🌊 | [`05_hawkes_and_event_clustering/`](file:///d:/cbot-atgvt/zz_zz%20PAPER/05_hawkes_and_event_clustering/) | ตรวจจับการกระชากของคำสั่งที่เป็นลูกโซ่ (Point Process) หลบข่าวหรือ Scalp ด่วน | `1301.1135` (Bacry Hawkes Model)<br>`1809.08060` (State-dependent LOB) |
| **6. Gold Microstructure & Alpha** 🥇 | [`06_gold_commodity_and_macro/`](file:///d:/cbot-atgvt/zz_zz%20PAPER/06_gold_commodity_and_macro/) | จุลภาคสภาพคล่องของทองคำ (XAUUSD), จังหวะ Forecast-to-Fill และ Regime Alpha | `2511.08571` (Forecast-to-Fill Alpha)<br>`2609.07946` (Stock/Bond/Gold) |
| **7. Market Regime Detection** 🎛️ | [`07_regime_detection_and_hmm/`](file:///d:/cbot-atgvt/zz_zz%20PAPER/07_regime_detection_and_hmm/) | ใช้ Hidden Markov Models (HMM) จำแนกสภาวะตลาดอัตโนมัติ เพื่อเป็นสวิตช์เปิด/ปิดบอท | `2605.27848` (HMM + RL Regime)<br>`2606.23492` (Continuous HMM) |
| **8. Lead-Lag & Latency** 🏎️ | [`08_lead_lag_and_latency/`](file:///d:/cbot-atgvt/zz_zz%20PAPER/08_lead_lag_and_latency/) | ตรวจจับความหน่วงระหว่างตลาด (เช่น Binance นำ cTrader, หรือ Bond Yield นำ Gold) เพื่อยิงดักหน้า | `1906.10388` (Lead-lag in FX)<br>`2608.24703` (Lead-lag Estimators) |
| **9. Signal Processing & Kalman** 🎯 | [`09_signal_processing_and_kalman/`](file:///d:/cbot-atgvt/zz_zz%20PAPER/09_signal_processing_and_kalman/) | กรอง Noise ตลาดแบบ Zero-Lag แทน Moving Average ดั้งเดิม ตัดปัญหาความหน่วงและสัญญาณหลอก | `1808.03297` (Trend without Hiccups)<br>`2609.14205` (CAST State-Space) |
| **10. Synthetic Data & Simulation** 🧪 | [`10_synthetic_data_and_simulation/`](file:///d:/cbot-atgvt/zz_zz%20PAPER/10_synthetic_data_and_simulation/) | ใช้ Diffusion Models / GANs สร้างข้อมูล LOB สังเคราะห์นับล้านฉากทัศน์สำหรับ Stress-test บอท | `2602.03776` (DiffLOB Diffusion)<br>`2510.22685` (TABL-ABM Synthetic) |
| **11. Financial LLMs & Sentiment** 🤖 | [`11_financial_llm_and_sentiment/`](file:///d:/cbot-atgvt/zz_zz%20PAPER/11_financial_llm_and_sentiment/) | สกัด Sentiment ข่าว Macro (FOMC, CPI, NFP) แปลงเป็นคะแนนทิศทางตลาดภายในเสี้ยววินาที | `2412.19245` (LLM Sentiment Trading)<br>`2607.28127` (FinSMART NLP) |
| **12. Position Sizing & Risk** 📐 | [`12_position_sizing_and_risk/`](file:///d:/cbot-atgvt/zz_zz%20PAPER/12_position_sizing_and_risk/) | บริหารขนาดไม้ด้วย Kelly Criterion และ Volatility Targeting ปรับลด Lot อัตโนมัติเมื่อผันผวนสูง | `2508.16598` (Kelly & VIX Hybrid)<br>`2609.13825` (ViperQ Auction Theory) |
| **13. Rough Volatility & Jumps** 🌊 | [`13_rough_volatility_and_jumps/`](file:///d:/cbot-atgvt/zz_zz%20PAPER/13_rough_volatility_and_jumps/) | แบบจำลองความขรุขระของราคา (Hurst < 0.5) สำหรับคำนวณระยะ SL/TP เชิงฟิสิกส์แท้จริง | `2609.31570` (Deep Rough Volatility)<br>`2606.27932` (Inefficient States) |

---

## 📊 การเข้าถึงสารบัญฉบับเต็ม

- 👉 **เปิดสารบัญงานวิจัยทั้ง 141 เรื่อง พร้อมลิงก์ HTML / PDF / สรุป:** [`PAPERS_INDEX.md`](file:///d:/cbot-atgvt/zz_zz%20PAPER/PAPERS_INDEX.md)
- 👉 **ไฟล์ฐานข้อมูล JSON:** [`papers_database.json`](file:///d:/cbot-atgvt/zz_zz%20PAPER/papers_database.json)

---

## 🚀 แผนการดำเนินการขั้นถัดไป (Next Steps)

เมื่อคลังความรู้เชิงทฤษฎีจาก **arXiv (`q-fin`)** สมบูรณ์ครบถ้วนทั้ง 13 มิติแล้ว แหล่งข้อมูลถัดไปคือ:
1. **SSRN (https://www.ssrn.com/ssrn/):** Working Papers ของกองทุนและสถาบัน (AQR, Two Sigma, Man AHL) เน้นเรื่อง Practitioner Backtesting, Real-world Execution และ Factor Alpha
2. **World Gold Council (https://www.gold.org/):** รายงานความต้องการทองคำจริงของธนาคารกลาง, โครงสร้างสภาพคล่อง OTC และ LBMA Fixing สำหรับ XAUUSD โดยตรง
"""

with open(os.path.join(base_dir, "README.md"), "w", encoding="utf-8") as f:
    f.write(readme_content)

print("Master README.md successfully created!")
