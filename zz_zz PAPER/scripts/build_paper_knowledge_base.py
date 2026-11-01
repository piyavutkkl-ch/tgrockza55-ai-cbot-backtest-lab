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
    return clean[:50].strip().replace(' ', '_')

def fetch_html_sections(arxiv_id):
    url = f"https://arxiv.org/html/{arxiv_id}"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
        
        # Extract sections
        sections = re.findall(r'<section\s+id="([^"]+)"\s+class="ltx_section"[^>]*>(.*?)</section>', html, re.DOTALL)
        extracted = {}
        for sec_id, sec_content in sections:
            title_m = re.search(r'<h2[^>]*>(.*?)</h2>', sec_content, re.DOTALL)
            title = clean_html_text(title_m.group(1)) if title_m else sec_id
            
            p_tags = re.findall(r'<p\s+[^>]*class="ltx_p"[^>]*>(.*?)</p>', sec_content, re.DOTALL)
            p_texts = [clean_html_text(p) for p in p_tags if len(clean_html_text(p)) > 40]
            
            if p_texts:
                extracted[title] = p_texts[:4] # take first 4 paragraphs
        return {"status": "ok", "sections": extracted}
    except Exception as e:
        return {"status": "no_html", "error": str(e)}

# Load curated papers
json_path = "d:/cbot-atgvt/zz_zz PAPER/scripts/curated_arxiv_papers.json"
with open(json_path, encoding='utf-8') as f:
    papers = json.load(f)

base_dir = "d:/cbot-atgvt/zz_zz PAPER"

categories_meta = {
    "01_lob_and_deep_learning": {
        "title_th": "หมวดที่ 1: Limit Order Book (LOB/DOM) และโมเดล Deep Learning",
        "title_en": "Limit Order Book Structure & Deep Learning Architectures",
        "desc_th": "การวิเคราะห์โครงสร้างข้อมูล Level 2 (Bid/Ask Depth), การจับจังหวะการเปลี่ยนแปลงของ Queue, และการใช้โมเดล Deep Learning (CNN, LSTM, Transformers, T-KAN) ในการพยากรณ์การขยับของราคา Mid-Price",
        "bot_relevance": "หัวใจสำคัญในการสร้าง Feature จาก DOM scraping (Level 2) เพื่อป้อนเข้า ML Bot เช่น ทำนายทิศทาง 5 แท่ง M1 ข้างหน้า และการตรวจจับคำสั่งหลอก (Spoofing Triaging)"
    },
    "02_order_flow_imbalance": {
        "title_th": "หมวดที่ 2: แรงกดดันคำสั่งซื้อขาย (Order Flow Imbalance - OFI) และ Price Impact",
        "title_en": "Order Flow Imbalance (OFI) & Price Impact Dynamics",
        "desc_th": "ทฤษฎีการวัดแรงซื้อขายสุทธิจาก Event ของ Order Book (Limit Order, Market Order, Cancellations) และการขยายผลสู่ Multi-Level OFI รวมถึงผลกระทบข้ามสินทรัพย์ (Cross-Impact)",
        "bot_relevance": "เป็นดัชนีชี้วัดแรงซื้อขายจริง (Real-time Pressure) ที่แม่นยำกว่าสัญญาณจากแท่งเทียน สามารถใช้ยืนยันการเกิด Absorption หรือ Liquidity Exhaustion ก่อนเปิดออเดอร์"
    },
    "03_market_making_and_spread": {
        "title_th": "หมวดที่ 3: กลยุทธ์ Market Making, Bid/Ask Spreads และการคุม Inventory Risk",
        "title_en": "Market Making Algorithms, Spread Dynamics & Inventory Control",
        "desc_th": "แบบจำลองคณิตศาสตร์สำหรับการวางคำสั่ง Bid/Ask แบบ Passive (Avellaneda-Stoikov & Guéant models), การคำนวณ Reservation Price และการคุมความเสี่ยงเมื่อพอร์ตถือสถานะไม่สมดุล",
        "bot_relevance": "นำไปใช้ปรับสเปรดและจุดตั้ง Limit Order / Take Profit ให้สอดคล้องกับความผันผวน และใช้คำนวณการเบี่ยงราคา (Quote Skewing) ตามสัญญาณทิศทางของตลาด (Directional Alpha)"
    },
    "04_optimal_execution_and_vwap": {
        "title_th": "หมวดที่ 4: การส่งคำสั่งอย่างคุ้มค่า (Optimal Execution) และกลยุทธ์ VWAP/TWAP",
        "title_en": "Optimal Execution, Market Impact Minimization & VWAP Strategies",
        "desc_th": "อัลกอริทึมการซอยคำสั่ง (Order Slicing / TWAP / VWAP) เพื่อลดค่า Slippage และ Market Impact รวมถึงการใช้ Reinforcement Learning ในการเลือกส่ง Market Order เทียบกับ Limit Order",
        "bot_relevance": "ป้องกันปัญหาบอทกำไรใน Backtest แต่เจ๊งในตลาดจริงเพราะโดนกินสเปรดและ Slippage โดยช่วยคำนวณเส้นทางกระจายไม้เข้า-ออกที่ดีที่สุด"
    },
    "05_hawkes_and_event_clustering": {
        "title_th": "หมวดที่ 5: แบบจำลอง Hawkes Processes และการจับกลุ่มคำสั่งผิดปกติ (Event Clustering)",
        "title_en": "Hawkes Processes & High-Frequency Trade Clustering",
        "desc_th": "แบบจำลอง Self-Exciting Point Process ที่อธิบายว่าการเกิดออเดอร์หนึ่งจะกระตุ้นให้เกิดออเดอร์ตามมาเป็นลูกโซ่ ช่วยในการวัดระดับความตื่นตัวของตลาดและตรวจจับ Flash Moves",
        "bot_relevance": "ช่วยให้บอทรู้ว่าตลาดกำลังอยู่ในสภาวะ 'น้ำนิ่ง' หรือ 'พายุโหมกระหน่ำ' (Trade Clustering) เพื่อเปิดระบบ Scalping ด่วน หรือปิดสวิตช์ชั่วคราวเพื่อหลบข่าวแรง"
    },
    "06_gold_commodity_and_macro": {
        "title_th": "หมวดที่ 6: จุลภาคตลาดทองคำ (Gold/XAU) และสินทรัพย์ความผันผวนสูง",
        "title_en": "Gold (XAU) & Volatility Dynamics",
        "desc_th": "พฤติกรรมโครงสร้างสภาพคล่องของทองคำ (XAUUSD), ช่วงเวลา London / NY Session Open, ผลกระทบจากตัวเลข Macroeconomics, และการจัดพอร์ต Multi-Asset",
        "bot_relevance": "เป็นคู่มือวิเคราะห์สินทรัพย์หลักของโปรเจกต์ (XAUUSD) ในการกำหนดกรอบเวลาเทรด (Trading Windows) และการป้องกัน Drawdown"
    }
}

# Categorize papers
categorized = {}
for p in papers:
    cat = p.get('category_folder', '01_lob_and_deep_learning')
    categorized.setdefault(cat, []).append(p)

print(f"Total papers to process: {len(papers)}")

# Create directories and files
for cat_id, cat_meta in categories_meta.items():
    cat_dir = os.path.join(base_dir, cat_id)
    os.makedirs(cat_dir, exist_ok=True)
    cat_papers = categorized.get(cat_id, [])
    
    print(f"\nProcessing category [{cat_id}] ({len(cat_papers)} papers)...")
    
    # Generate Category README.md
    cat_readme = [
        f"# {cat_meta['title_th']}",
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
        year = p['published'][:4]
        aid = p['base_id']
        slug = safe_filename(clean_t)
        doc_link = f"[{aid}]({aid}_{slug}.md)"
        html_link = f"[HTML](https://arxiv.org/html/{p['arxiv_id']})"
        pdf_link = f"[PDF]({p['pdf_url']})"
        cat_readme.append(f"| {idx} | {doc_link} | {clean_t} | {authors_short} | {year} | {html_link} / {pdf_link} |")
    
    cat_readme.append("\n---\n*สารบัญนี้สร้างขึ้นอัตโนมัติจากการดึงข้อมูลเชิงลึกผ่าน arXiv q-fin*")
    with open(os.path.join(cat_dir, "README.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(cat_readme))

    # Generate individual paper Markdown dossiers
    # We fetch HTML for key highlight papers (first 3-4 in each category to avoid high traffic)
    for p_idx, p in enumerate(cat_papers):
        aid = p['base_id']
        clean_t = p['title']
        slug = safe_filename(clean_t)
        doc_path = os.path.join(cat_dir, f"{aid}_{slug}.md")
        
        # Determine if we should attempt HTML scrape
        html_content = None
        if p_idx < 3: # scrape HTML for top papers
            print(f"  Fetching HTML for [{aid}] {clean_t[:40]}...")
            html_content = fetch_html_sections(p['arxiv_id'])
        
        # Build Markdown content
        doc = [
            f"# {clean_t}",
            f"**รหัส arXiv:** [`{p['arxiv_id']}`](https://arxiv.org/abs/{p['arxiv_id']}) | **หมวดหลัก:** `{p.get('primary_cat', 'q-fin.TR')}`",
            f"**ผู้แต่ง:** {', '.join(p['authors'])}",
            f"**วันที่เผยแพร่:** {p['published']} (อัปเดตล่าสุด: {p.get('updated', p['published'])})",
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
            f"  1. ตรวจสอบ Feature ที่ใช้: สอดคล้องกับข้อมูล Level 2 (Bid/Ask Price & Depth) ที่ดึงได้จาก cTrader หรือ DOM Scraper หรือไม่",
            f"  2. การคำนวณแบบ Real-time: ต้องคำนวณได้ภายในเวลาหลัก Millisecond หรือ Tick-by-tick โดยไม่เกิด Latency ค้างสะสม",
            f"  3. ค่าสเปรดและคอมมิชชัน: ผลกำไรที่รายงานในงานวิจัยต้องถูกหักลบด้วยต้นทุนการเทรดจริงของโบรกเกอร์เสมอ",
            ""
        ]
        
        # If HTML sections were successfully retrieved
        if html_content and html_content.get("status") == "ok" and html_content.get("sections"):
            doc.append("---")
            doc.append("\n## 📖 สรุปเนื้อหาสำคัญจากเอกสารฉบับเต็ม (Key Text Sections from HTML)\n")
            for sec_name, paragraphs in html_content["sections"].items():
                # filter out non-essential sections
                if any(k in sec_name.lower() for k in ['reference', 'acknowledgement', 'appendix']):
                    continue
                doc.append(f"### {sec_name}")
                for para in paragraphs:
                    doc.append(f"{para}\n")
        
        doc.append("\n---\n*จัดทำขึ้นสำหรับการวิจัยและพัฒนา Quantitative Trading Robot ในโปรเจกต์ cbot-atgvt*")
        
        with open(doc_path, "w", encoding="utf-8") as f:
            f.write("\n".join(doc))

print("\nAll category folders and paper dossiers successfully created!")
