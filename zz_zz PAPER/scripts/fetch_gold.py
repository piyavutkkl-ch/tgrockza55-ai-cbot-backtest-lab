import sys
import os
import json
import time
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET

sys.stdout.reconfigure(encoding='utf-8')

# Read existing papers
json_path = "d:/cbot-atgvt/zz_zz PAPER/scripts/curated_arxiv_papers.json"
with open(json_path, encoding='utf-8') as f:
    papers = json.load(f)

existing_ids = {p['base_id'] for p in papers}

queries = [
    ('all:gold AND abs:price AND cat:q-fin.*', 'Gold Price & Volatility'),
    ('abs:gold AND abs:intraday AND cat:q-fin.*', 'Gold Intraday Dynamics'),
    ('all:commodity AND abs:"limit order book" AND cat:q-fin.*', 'Commodity Order Book Microstructure'),
    ('abs:"precious metals" AND cat:q-fin.*', 'Precious Metals Financial Analysis'),
    ('abs:gold AND abs:"price discovery" AND cat:q-fin.*', 'Gold Price Discovery')
]

ns = {'atom': 'http://www.w3.org/2005/Atom', 'arxiv': 'http://arxiv.org/schemas/atom'}

print("Waiting 5 seconds before starting Category 06 queries to avoid 429...")
time.sleep(5)

added = 0
for q, label in queries:
    print(f"Searching {label}...")
    url = f"http://export.arxiv.org/api/query?search_query={urllib.parse.quote(q)}&max_results=4&sortBy=relevance&sortOrder=descending"
    req = urllib.request.Request(url, headers={'User-Agent': 'QuantTradingPaperBot/1.0 (academic research)'})
    try:
        with urllib.request.urlopen(req) as resp:
            xml_data = resp.read()
        root = ET.fromstring(xml_data)
        entries = root.findall('atom:entry', ns)
        for e in entries:
            id_url = e.find('atom:id', ns).text.strip()
            raw_id = id_url.split('/abs/')[-1]
            base_id = raw_id.split('v')[0]
            title = e.find('atom:title', ns).text.strip().replace('\n', ' ')
            summary = e.find('atom:summary', ns).text.strip().replace('\n', ' ')
            published = e.find('atom:published', ns).text.strip()[:10]
            authors = [a.find('atom:name', ns).text.strip() for a in e.findall('atom:author', ns)]
            pcat = e.find('arxiv:primary_category', ns)
            pcat_val = pcat.attrib.get('term') if pcat is not None else ""
            
            if base_id not in existing_ids:
                papers.append({
                    "arxiv_id": raw_id,
                    "base_id": base_id,
                    "title": title,
                    "authors": authors,
                    "published": published,
                    "category_folder": "06_gold_and_commodity_microstructure",
                    "primary_cat": pcat_val,
                    "pdf_url": f"https://arxiv.org/pdf/{raw_id}.pdf",
                    "abstract": summary
                })
                existing_ids.add(base_id)
                added += 1
                print(f" [+] Added [{raw_id}]: {title[:60]}")
    except Exception as ex:
        print(f" [!] Error: {ex}")
    time.sleep(3)

print(f"\nAdded {added} papers to Category 06. Total papers now: {len(papers)}")
with open(json_path, "w", encoding="utf-8") as f:
    json.dump(papers, f, ensure_ascii=False, indent=2)
