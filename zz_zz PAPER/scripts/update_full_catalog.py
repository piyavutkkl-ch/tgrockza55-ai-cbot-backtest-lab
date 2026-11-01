import os
import sys
import json
import re
import urllib.request
import urllib.error
from html.parser import HTMLParser

sys.stdout.reconfigure(encoding='utf-8')

class HTMLTextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text = []
        self.ignore = False

    def handle_starttag(self, tag, attrs):
        if tag in ['script', 'style', 'nav', 'header', 'footer']:
            self.ignore = True

    def handle_endtag(self, tag):
        if tag in ['script', 'style', 'nav', 'header', 'footer']:
            self.ignore = False

    def handle_data(self, data):
        if not self.ignore:
            self.text.append(data)

    def get_text(self):
        return ' '.join(self.text)

def clean_html_text(html_fragment):
    parser = HTMLTextExtractor()
    parser.feed(html_fragment)
    raw = parser.get_text()
    return re.sub(r'\s+', ' ', raw).strip()

def safe_filename(name):
    clean = re.sub(r'[^\w\-_\. ]', '_', name)
    clean = re.sub(r'_+', '_', clean)
    return clean[:45].strip(' _')

def fetch_html_sections(arxiv_id):
    url = f"https://arxiv.org/html/{arxiv_id}"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
    try:
        with urllib.request.urlopen(req, timeout=6) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
        
        sections = re.findall(r'<section\s+id="([^"]+)"\s+class="ltx_section"[^>]*>(.*?)</section>', html, re.DOTALL)
        extracted = {}
        for sec_id, sec_content in sections:
            title_m = re.search(r'<h2[^>]*>(.*?)</h2>', sec_content, re.DOTALL)
            title = clean_html_text(title_m.group(1)) if title_m else sec_id
            
            p_tags = re.findall(r'<p\s+[^>]*class="ltx_p"[^>]*>(.*?)</p>', sec_content, re.DOTALL)
            p_texts = [clean_html_text(p) for p in p_tags if len(clean_html_text(p)) > 40]
            
            if p_texts:
                extracted[title] = p_texts[:3]
        return {"status": "ok", "sections": extracted}
    except Exception as e:
        return {"status": "no_html", "error": str(e)}

# Load existing papers
json_path = "d:/cbot-atgvt/zz_zz PAPER/scripts/curated_arxiv_papers.json"
with open(json_path, encoding='utf-8') as f:
    papers = json.load(f)

# Load gold papers
gold_json_path = "d:/cbot-atgvt/zz_zz PAPER/scripts/scraped_gold_papers.json"
if os.path.exists(gold_json_path):
    with open(gold_json_path, encoding='utf-8') as f:
        gold_papers = json.load(f)
    existing_ids = {p['base_id'] for p in papers}
    for gp in gold_papers:
        if gp['base_id'] not in existing_ids:
            papers.append(gp)
            existing_ids.add(gp['base_id'])

# Save unified database
db_path = "d:/cbot-atgvt/zz_zz PAPER/papers_database.json"
with open(db_path, "w", encoding="utf-8") as f:
    json.dump(papers, f, ensure_ascii=False, indent=2)

base_dir = "d:/cbot-atgvt/zz_zz PAPER"

categories_meta = {
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
    }
}

categorized = {}
for p in papers:
    cat = p.get('category_folder', '01_lob_and_deep_learning')
    categorized.setdefault(cat, []).append(p)

all_papers_flat = []

# Process categories
for cat_id, cat_meta in categories_meta.items():
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
        pub_year = str(p['published'])[:4]
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
        
        # Write individual dossier
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
                f"  1. **สกัด Feature ที่จำเป็น:** สอดคล้องกับข้อมูล Level 2 / DOM Depth ที่ดึงได้จาก cTrader หรือ DOM Scraper หรือไม่",
                f"  2. **Latency & Execution:** การคำนวณต้องทำได้แบบ Tick-by-tick ภายในหลักมิลลิวินาที โดยไม่มี overhead ที่ทำให้บอทหน่วง",
                f"  3. **Spread & Slippage Reality:** ผลตอบแทนที่คำนวณได้ต้องหักลบต้นทุนสเปรดจริงของโบรกเกอร์เสมอ",
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
    f"รวบรวมงานวิจัยจาก **arXiv (q-fin: Quantitative Finance)** ทั้งหมด **{len(all_papers_flat)} รายการ** จัดหมวดหมู่เฉพาะสำหรับพัฒนา Trading Bot และกลยุทธ์ Market Microstructure",
    "",
    "> 💡 **คำแนะนำ:** สามารถคลิกอ่านผ่านลิงก์ **HTML** ได้ทันทีในเบราว์เซอร์ ซึ่งสะดวก รวดเร็ว และไม่ต้องดาวน์โหลดไฟล์ PDF ขนาดใหญ่ให้เปลืองพื้นที่หรือติด Rate Limit",
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
