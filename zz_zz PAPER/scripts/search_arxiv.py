import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import time
import json
import os

queries = [
    ("DeepLOB & LOB Deep Learning", 'all:"DeepLOB" OR (ti:"Limit Order Book" AND abs:"Deep Learning")'),
    ("Order Flow Imbalance (OFI)", 'all:"Order Flow Imbalance" AND cat:q-fin.TR'),
    ("Market Making & Inventory Risk", 'ti:"Market Making" AND cat:q-fin.TR'),
    ("Optimal Execution & VWAP", '(ti:"Optimal Execution" OR ti:"VWAP") AND cat:q-fin.TR'),
    ("Hawkes Process in Finance", 'ti:"Hawkes" AND cat:q-fin.TR'),
    ("Reinforcement Learning in Trading", '(ti:"Reinforcement Learning" AND (ti:"Trading" OR ti:"Market Making")) AND cat:q-fin.TR'),
    ("Gold & Commodity Microstructure", '(abs:"Gold" OR abs:"XAU") AND (abs:"microstructure" OR abs:"high-frequency" OR abs:"volatility") AND cat:q-fin.*')
]

ns = {'atom': 'http://www.w3.org/2005/Atom'}

results = {}

for category, q in queries:
    print(f"Searching: {category}...")
    encoded_q = urllib.parse.quote(q)
    url = f"http://export.arxiv.org/api/query?search_query={encoded_q}&max_results=5&sortBy=relevance&sortOrder=descending"
    req = urllib.request.Request(url, headers={'User-Agent': 'ResearchPaperBot/1.0 (academic-research)'})
    
    try:
        with urllib.request.urlopen(req) as resp:
            root = ET.fromstring(resp.read())
            entries = root.findall('atom:entry', ns)
            papers = []
            for e in entries:
                title = e.find('atom:title', ns).text.strip().replace('\n', ' ')
                id_url = e.find('atom:id', ns).text.strip()
                arxiv_id = id_url.split('/abs/')[-1]
                published = e.find('atom:published', ns).text.strip()[:10]
                summary = e.find('atom:summary', ns).text.strip().replace('\n', ' ')
                authors = [a.find('atom:name', ns).text for a in e.findall('atom:author', ns)]
                
                # find pdf link
                pdf_link = None
                for link in e.findall('atom:link', ns):
                    if link.attrib.get('title') == 'pdf' or link.attrib.get('type') == 'application/pdf':
                        pdf_link = link.attrib.get('href')
                        break
                if not pdf_link:
                    pdf_link = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
                if not pdf_link.endswith('.pdf'):
                    pdf_link += '.pdf'

                papers.append({
                    'arxiv_id': arxiv_id,
                    'title': title,
                    'authors': authors,
                    'published': published,
                    'pdf_url': pdf_link,
                    'summary': summary[:300] + '...'
                })
            results[category] = papers
            print(f"  Found {len(papers)} papers.")
    except Exception as ex:
        print(f"  Error: {ex}")
    time.sleep(1) # respectful rate limit to arXiv API

print("\n--- Summary of Discovered Papers ---")
for cat, papers in results.items():
    print(f"\n[{cat}]")
    for p in papers:
        print(f" - [{p['arxiv_id']}] ({p['published']}) {p['title']}")
        print(f"   Authors: {', '.join(p['authors'][:3])}")
        print(f"   PDF: {p['pdf_url']}")
