import sys
import os
import json
import time
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET

sys.stdout.reconfigure(encoding='utf-8')

categories = {
    "01_lob_and_deep_learning": [
        ('ti:DeepLOB', 'DeepLOB: Deep Convolutional Neural Networks'),
        ('ti:"Limit Order Book" AND abs:"Convolutional"', 'CNN on Limit Order Book'),
        ('ti:"Limit Order Books" AND abs:"Deep Learning" AND cat:q-fin.*', 'Deep Learning on LOB'),
        ('ti:"price formation" AND abs:"Deep Learning" AND cat:q-fin.*', 'Price formation & Deep Learning'),
        ('abs:"order book" AND abs:"Transformer" AND cat:q-fin.TR', 'Transformers on Order Book')
    ],
    "02_order_flow_imbalance": [
        ('ti:"Order Book Events" AND ti:"Price Impact"', 'Price Impact of Order Book Events'),
        ('all:"Order Flow Imbalance" AND cat:q-fin.TR', 'Order Flow Imbalance in Trading'),
        ('ti:"Price Impact" AND abs:"Limit Order Book" AND cat:q-fin.TR', 'Price Impact in LOB'),
        ('ti:"Cross-Impact" AND abs:"Order Flow" AND cat:q-fin.*', 'Cross-Impact of Order Flow')
    ],
    "03_market_making_and_spread": [
        ('ti:"Optimal Market Making" AND cat:q-fin.*', 'Optimal Market Making (Gueant)'),
        ('ti:"Inventory Risk" AND abs:"market making" AND cat:q-fin.*', 'Inventory Risk in Market Making'),
        ('ti:"High-frequency" AND abs:"market making" AND cat:q-fin.TR', 'High-frequency Market Making'),
        ('ti:"Market Making" AND abs:"Avellaneda" AND cat:q-fin.*', 'Avellaneda-Stoikov Market Making')
    ],
    "04_optimal_execution_and_vwap": [
        ('ti:"Optimal Execution" AND abs:"Limit Order Book" AND cat:q-fin.TR', 'Optimal Execution in LOB'),
        ('ti:"Optimal Execution" AND abs:"Order Flow" AND cat:q-fin.*', 'Optimal Execution with Order Flow'),
        ('ti:"VWAP" AND cat:q-fin.*', 'VWAP execution strategies'),
        ('abs:"execution" AND abs:"Reinforcement Learning" AND cat:q-fin.TR', 'RL for Execution')
    ],
    "05_hawkes_and_event_clustering": [
        ('ti:Hawkes AND abs:"microstructure" AND cat:q-fin.*', 'Hawkes Process in Microstructure'),
        ('ti:Hawkes AND abs:"limit order book" AND cat:q-fin.*', 'Hawkes LOB Models'),
        ('ti:Hawkes AND abs:"high-frequency" AND cat:q-fin.*', 'Hawkes High-Frequency Finance')
    ],
    "06_gold_and_crypto_microstructure": [
        ('abs:"gold" AND abs:"microstructure" AND cat:q-fin.*', 'Gold Microstructure'),
        ('abs:"gold" AND abs:"price discovery" AND cat:q-fin.*', 'Gold Price Discovery'),
        ('abs:"gold" AND abs:"high-frequency" AND cat:q-fin.*', 'High-frequency Gold Trading'),
        ('abs:"cryptocurrency" AND abs:"limit order book" AND cat:q-fin.TR', 'Crypto LOB Microstructure')
    ]
}

ns = {'atom': 'http://www.w3.org/2005/Atom', 'arxiv': 'http://arxiv.org/schemas/atom'}

selected_papers = {}

for cat_folder, query_list in categories.items():
    print(f"\n=================== Category: {cat_folder} ===================")
    for q, label in query_list:
        url = f"http://export.arxiv.org/api/query?search_query={urllib.parse.quote(q)}&max_results=3&sortBy=relevance&sortOrder=descending"
        req = urllib.request.Request(url, headers={'User-Agent': 'QuantResearch/1.0'})
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
                
                # Filter out pure physics or biology if wrongly returned
                if not (pcat_val.startswith('q-fin') or 'finance' in summary.lower() or 'order book' in summary.lower() or 'market' in summary.lower()):
                    continue
                
                if base_id not in selected_papers:
                    selected_papers[base_id] = {
                        "arxiv_id": raw_id,
                        "base_id": base_id,
                        "title": title,
                        "authors": authors,
                        "published": published,
                        "category_folder": cat_folder,
                        "primary_cat": pcat_val,
                        "pdf_url": f"https://arxiv.org/pdf/{raw_id}.pdf",
                        "abstract": summary
                    }
                    print(f" [+] [{raw_id}] ({published}) {title[:65]}...")
        except Exception as ex:
            print(f" [!] Error searching {label}: {ex}")
        time.sleep(0.5)

print(f"\nTotal uniquely selected financial papers: {len(selected_papers)}")
with open("d:/cbot-atgvt/zz_zz PAPER/scripts/curated_arxiv_papers.json", "w", encoding="utf-8") as f:
    json.dump(list(selected_papers.values()), f, ensure_ascii=False, indent=2)
