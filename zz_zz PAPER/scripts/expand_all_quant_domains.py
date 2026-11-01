import os
import sys
import json
import re
import time
import urllib.request
import urllib.parse
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

def scrape_arxiv_web(query_term, max_items=8):
    url = f"https://arxiv.org/search/q-fin?query={urllib.parse.quote(query_term)}&searchtype=all&source=header"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
        
        blocks = re.findall(r'<li class="arxiv-result">(.*?)</li>', html, re.DOTALL)
        results = []
        for b in blocks[:max_items]:
            aid_m = re.search(r'<a href="https://arxiv.org/abs/([^"]+)">arXiv:\1</a>', b)
            if not aid_m:
                continue
            aid = aid_m.group(1)
            base_id = aid.split('v')[0]
            
            title_m = re.search(r'<p class="title is-5 mathjax">\s*(.*?)\s*</p>', b, re.DOTALL)
            title = re.sub(r'<[^>]+>', '', title_m.group(1)).strip() if title_m else aid
            title = re.sub(r'\s+', ' ', title)
            
            authors_m = re.findall(r'<a href="https://arxiv.org/search/q-fin\?searchtype=author[^"]*">(.*?)</a>', b)
            authors = [a.strip() for a in authors_m]
            
            date_m = re.search(r'<p class="is-size-7">.*?Submitted.*?(\d{1,2}\s+[A-Za-z]+,\s+\d{4})', b, re.DOTALL)
            pub_date = date_m.group(1) if date_m else "Recent"
            
            abs_m = re.search(r'<span class="abstract-full[^"]*">(.*?)<a class="is-size-7', b, re.DOTALL)
            if not abs_m:
                abs_m = re.search(r'<span class="abstract-short[^"]*">(.*?)</span>', b, re.DOTALL)
            abstract = re.sub(r'<[^>]+>', '', abs_m.group(1)).strip() if abs_m else ""
            abstract = re.sub(r'\s+', ' ', abstract).replace('▽ More', '').strip()
            
            results.append({
                "arxiv_id": aid,
                "base_id": base_id,
                "title": title,
                "authors": authors,
                "published": pub_date,
                "pdf_url": f"https://arxiv.org/pdf/{aid}.pdf",
                "html_url": f"https://arxiv.org/html/{aid}",
                "abstract": abstract
            })
        return results
    except Exception as e:
        print(f"Error scraping query '{query_term}': {e}")
        return []

# New domain definitions
new_domains = {
    "07_regime_detection_and_hmm": {
        "title_th": "หมวดที่ 7: การจำแนกสภาวะตลาด (Market Regime Detection) และแบบจำลอง HMM",
        "title_en": "Market Regime Detection & Hidden Markov Models (HMM)",
        "desc_th": "การระบุสภาวะตลาดแบบไม่อิงคนมอง (Unsupervised Regime Clustering) เช่น สภาวะ Low-Vol Trend, High-Vol Trend, Choppy Range และ Liquidity Squeeze",
        "bot_relevance": "ทำหน้าที่เป็น 'สวิตช์หลักของระบบ' (Master Strategy Router) เพื่อเลือกเปิดบอทที่เหมาะสมกับสภาพตลาดขณะนั้น และปิดบอทที่ไม่ควรทำงาน",
        "icon": "🎛️",
        "queries": ["hidden markov market regime", "regime switching trading", "market regime clustering"]
    },
    "08_lead_lag_and_latency": {
        "title_th": "หมวดที่ 8: ความสัมพันธ์ตัวนำ-ตัวตาม (Lead-Lag Microstructure) และ Latency Arbitrage",
        "title_en": "Lead-Lag Relationships & Cross-Market Latency Dynamics",
        "desc_th": "การวัดความหน่วงของข้อมูลและกระแสคำสั่งระหว่างตลาด เพื่อหาว่าสินทรัพย์หรือ Exchange ใดขยับก่อน และตัวใดขยับตาม",
        "bot_relevance": "ใช้ยิงดักหน้า (Preemptive Order) เช่น ดูว่า Binance นำ cTrader อยู่กี่ร้อย ms หรือดูว่า Bond Yield/DXY ส่งผลนำ XAUUSD ล่วงหน้ากี่วินาที",
        "icon": "🏎️",
        "queries": ["lead-lag financial markets", "lead-lag foreign exchange", "cross-market high frequency latency"]
    },
    "09_signal_processing_and_kalman": {
        "title_th": "หมวดที่ 9: การประมวลผลสัญญาณดิจิทัล (Digital Signal Processing) และ Kalman Filtering",
        "title_en": "Signal Processing, Kalman Filtering & Zero-Lag Noise Reduction",
        "desc_th": "การสกัด 'สัญญาณแท้จริง (Underlying State)' ออกจาก 'สัญญาณรบกวน (Market Noise)' โดยไม่เกิดปัญหาความหน่วงช้า (No Lagging Whipsaw)",
        "bot_relevance": "ใช้แทน Moving Average ทั่วไป ทำให้จับจุดกลับตัวและทิศทางได้ทันทีโดยไม่ถูกกราฟหลอกตัดขึ้นตัดลงบ่อยๆ",
        "icon": "🎯",
        "queries": ["kalman filter trading", "kalman filter trend", "state-space financial trading"]
    },
    "10_synthetic_data_and_simulation": {
        "title_th": "หมวดที่ 10: ข้อมูลตลาดสังเคราะห์ (Synthetic Market Data) และ Diffusion Models",
        "title_en": "Synthetic LOB, Diffusion Models & Market Simulation",
        "desc_th": "การสร้างข้อมูลจำลอง Order Book และ Tick Data นับล้านฉากทัศน์ที่มีความสมจริงทางสถิติ เพื่อแก้ปัญหา Overfitting และทดสอบภาวะวิกฤติ",
        "bot_relevance": "ใช้ Stress-test บอทก่อนลงเงินจริง เพื่อทดสอบว่าบอทจะรอดหรือไม่หากเกิดเหตุการณ์ Black Swan ที่ไม่เคยเกิดขึ้นในประวัติศาสตร์ 5 ปีหลัง",
        "icon": "🧪",
        "queries": ["synthetic limit order book", "diffusion models finance", "generative trading simulation"]
    },
    "11_financial_llm_and_sentiment": {
        "title_th": "หมวดที่ 11: ปัญญาประดิษฐ์ประมวลผลภาษา (Financial LLMs) และการเทรดข่าว (Sentiment Trading)",
        "title_en": "Financial LLMs, NLP & News Event Sentiment Trading",
        "desc_th": "การแปลงพาดหัวข่าว คำแถลงของธนาคารกลาง และรายงานเศรษฐกิจเป็นคะแนนทิศทางตลาด (Sentiment Score) ภายในเวลาเสี้ยววินาที",
        "bot_relevance": "ช่วยให้บอทรู้ข่าวและปรับสถานะพอร์ตก่อนที่นักลงทุนรายย่อยจะอ่านข่าวจบ ป้องกันการติดดอยช่วงประกาศตัวเลขสำคัญ (FOMC/CPI/NFP)",
        "icon": "🤖",
        "queries": ["LLM financial trading", "sentiment trading large language models", "financial news sentiment returns"]
    },
    "12_position_sizing_and_risk": {
        "title_th": "หมวดที่ 12: การคำนวณขนาดไม้ (Position Sizing), Kelly Criterion และการคุม Drawdown",
        "title_en": "Mathematical Position Sizing, Kelly Criterion & Drawdown Control",
        "desc_th": "แบบจำลองคณิตศาสตร์สำหรับการจัดสรรเงินทุน (Money Management) และการปรับ Lot Size แบบ Dynamic ตามระดับความผันผวน",
        "bot_relevance": "หัวใจที่ตัดสินความอยู่รอดในระยะยาว ปรับลด Lot อัตโนมัติเมื่อความผันผวนสูง เพื่อให้ความเสี่ยงต่อดอลลาร์คงที่ ป้องกันพอร์ตแตก",
        "icon": "📐",
        "queries": ["kelly criterion trading", "volatility targeting portfolio", "drawdown control financial trading"]
    },
    "13_rough_volatility_and_jumps": {
        "title_th": "หมวดที่ 13: ฟิสิกส์ความขรุขระของราคา (Rough Volatility) และการกระโดดของราคา (Jumps)",
        "title_en": "Rough Volatility, Fractional Dynamics & Price Jumps",
        "desc_th": "ทฤษฎีความขรุขระของตลาดการเงิน (Hurst Parameter H < 0.5) ที่อธิบายว่าทำไมความผันผวนในกราฟสั้นจึงคมและกระชากกว่า Brownian Motion ปกติ",
        "bot_relevance": "ใช้คำนวณระยะ Stop Loss และ Take Profit เชิงฟิสิกส์ที่แท้จริง ไม่ให้ถูกสวิงสะบัดกิน SL ในช่วงที่ตลาดขรุขระผิดปกติ",
        "icon": "🌊",
        "queries": ["rough volatility financial", "rough heston", "jump diffusion high frequency price"]
    }
}

# Load existing database
db_path = "d:/cbot-atgvt/zz_zz PAPER/papers_database.json"
base_dir = "d:/cbot-atgvt/zz_zz PAPER"

with open(db_path, encoding='utf-8') as f:
    existing_papers = json.load(f)

existing_ids = {p['base_id'] for p in existing_papers}
print(f"Starting with {len(existing_papers)} existing papers...")

newly_added_papers = []

for cat_id, meta in new_domains.items():
    print(f"\n=================== Processing: {meta['title_en']} ===================")
    cat_dir = os.path.join(base_dir, cat_id)
    os.makedirs(cat_dir, exist_ok=True)
    
    collected_for_cat = []
    for q in meta["queries"]:
        print(f" Searching: {q}...")
        results = scrape_arxiv_web(q, max_items=5)
        for r in results:
            if r['base_id'] not in existing_ids:
                r['category_folder'] = cat_id
                r['category_title'] = meta['title_th']
                r['category_icon'] = meta['icon']
                collected_for_cat.append(r)
                existing_papers.append(r)
                existing_ids.add(r['base_id'])
                newly_added_papers.append(r)
                print(f"  [+] Added: [{r['arxiv_id']}] {r['title'][:60]}")
        time.sleep(1) # respectful wait
    
    print(f" Total newly collected for {cat_id}: {len(collected_for_cat)}")

print(f"\nTotal new papers added across 7 domains: {len(newly_added_papers)}")
print(f"Total papers in database now: {len(existing_papers)}")

# Save updated database
with open(db_path, "w", encoding="utf-8") as f:
    json.dump(existing_papers, f, ensure_ascii=False, indent=2)

print("Database updated successfully!")
