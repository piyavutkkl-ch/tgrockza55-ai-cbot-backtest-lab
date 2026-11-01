import sys
import os
import json
import time
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET

sys.stdout.reconfigure(encoding='utf-8')

# Selected high-value papers by category
target_categories = {
    "01_lob_and_deep_learning": {
        "name_th": "โครงสร้าง Limit Order Book (LOB/DOM) และโมเดล Deep Learning",
        "name_en": "Limit Order Book Structure & Deep Learning Models",
        "description": "การนำข้อมูล Level 2 (Bid/Ask Depth) มาสร้างฟีเจอร์และป้อนเข้าสู่โมเดล CNN/LSTM/Transformer เพื่อทำนายทิศทางราคาล่วงหน้า",
        "paper_ids": ["1808.03668", "1803.06917", "2403.09267", "2506.05764", "2601.02310"]
    },
    "02_order_flow_imbalance": {
        "name_th": "แรงกดดันคำสั่งซื้อขาย (Order Flow Imbalance) และ Price Impact",
        "name_en": "Order Flow Imbalance (OFI) & Price Impact Dynamics",
        "description": "ทฤษฎีคำนวณความไม่สมดุลของ Order Flow (OFI) ทั้งแบบ Top-of-Book และ Multi-Level Depth เพื่อจับจังหวะการถูกดูดซับสภาพคล่อง (Absorption) และผลกระทบต่อราคา",
        "paper_ids": ["1011.6402", "2112.02947", "2112.13213", "1409.2618", "2408.03594"]
    },
    "03_market_making_and_spread": {
        "name_th": "กลยุทธ์ Market Making และการควบคุม Inventory Risk",
        "name_en": "Market Making Algorithms & Inventory Control",
        "description": "โมเดลคณิตศาสตร์สำหรับบอทวาง Bid/Ask (Avellaneda-Stoikov & Guéant models), การปรับสเปรดตามความผันผวน, และการป้องกันความเสี่ยงเมื่อถือครองสถานะเกินกำหนด",
        "paper_ids": ["1605.01862", "1105.3115", "1304.4054", "2307.14129"]
    },
    "04_optimal_execution_and_vwap": {
        "name_th": "การส่งคำสั่งอย่างเหมาะสม (Optimal Execution) และกลยุทธ์ VWAP/TWAP",
        "name_en": "Optimal Execution & VWAP/TWAP Strategies",
        "description": "วิธีแบ่งออเดอร์ (Order Slicing) เพื่อลด Slippage, การเทรดตาม Volume Profile/VWAP, และการใช้ Reinforcement Learning ช่วยกำหนดจังหวะ Execution",
        "paper_ids": ["1811.05214", "2004.06985", "1906.02312"]
    },
    "05_hawkes_and_event_clustering": {
        "name_th": "แบบจำลอง Hawkes Process และการจับกลุ่มการกระชากของคำสั่ง (Order Clustering)",
        "name_en": "Hawkes Processes & High-Frequency Event Clustering",
        "description": "แบบจำลอง Point Process สำหรับตรวจจับ Trade Clustering และ Flash Crash เมื่อเกิดคำสั่งไหลทะลักอย่างผิดปกติ",
        "paper_ids": ["1502.04592", "2105.10430", "2610.37324"]
    },
    "06_gold_and_commodity_microstructure": {
        "name_th": "จุลภาคตลาดทองคำ (Gold/XAU) และสินทรัพย์ความผันผวนสูง",
        "name_en": "Gold & Commodity Market Microstructure",
        "description": "พฤติกรรมโครงสร้างสภาพคล่องของทองคำ (XAUUSD), ผลกระทบช่วง London/NY Session Open, และการกระชากของราคาหลังข่าว Macroeconomics",
        "paper_ids": ["2204.05834", "2009.07188", "2108.08381"]
    }
}

# Collect all IDs
all_ids = []
id_to_cat = {}
for cat_key, cat_data in target_categories.items():
    for pid in cat_data["paper_ids"]:
        all_ids.append(pid)
        id_to_cat[pid] = cat_key

print(f"Total target papers to query: {len(all_ids)}")

url = f"http://export.arxiv.org/api/query?id_list={','.join(all_ids)}&max_results=50"
req = urllib.request.Request(url, headers={'User-Agent': 'QuantTradingPaperBot/1.0 (academic-research)'})

papers_data = []

with urllib.request.urlopen(req) as resp:
    xml_content = resp.read()

root = ET.fromstring(xml_content)
ns = {'atom': 'http://www.w3.org/2005/Atom', 'arxiv': 'http://arxiv.org/schemas/atom'}

for entry in root.findall('atom:entry', ns):
    id_url = entry.find('atom:id', ns).text.strip()
    raw_id = id_url.split('/abs/')[-1]
    # base id without version
    base_id = raw_id.split('v')[0]
    
    title = entry.find('atom:title', ns).text.strip().replace('\n', ' ')
    summary = entry.find('atom:summary', ns).text.strip().replace('\n', ' ')
    published = entry.find('atom:published', ns).text.strip()[:10]
    updated = entry.find('atom:updated', ns).text.strip()[:10]
    authors = [a.find('atom:name', ns).text.strip() for a in entry.findall('atom:author', ns)]
    
    # Primary category
    primary_cat = None
    pcat_elem = entry.find('arxiv:primary_category', ns)
    if pcat_elem is not None:
        primary_cat = pcat_elem.attrib.get('term')
    
    # PDF URL
    pdf_url = f"https://arxiv.org/pdf/{raw_id}.pdf"
    
    cat_key = id_to_cat.get(base_id, "01_lob_and_deep_learning")
    
    paper_info = {
        "arxiv_id": raw_id,
        "base_id": base_id,
        "title": title,
        "authors": authors,
        "published": published,
        "updated": updated,
        "primary_cat": primary_cat,
        "category_folder": cat_key,
        "pdf_url": pdf_url,
        "abstract": summary
    }
    papers_data.append(paper_info)
    print(f"Fetched [{base_id}]: {title[:60]}... ({published})")

output_json = "d:/cbot-atgvt/zz_zz PAPER/scripts/fetched_arxiv_metadata.json"
with open(output_json, "w", encoding="utf-8") as f:
    json.dump(papers_data, f, ensure_ascii=False, indent=2)

print(f"\nSaved metadata for {len(papers_data)} papers to {output_json}")
