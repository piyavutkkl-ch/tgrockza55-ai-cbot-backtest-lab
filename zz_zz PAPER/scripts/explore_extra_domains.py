import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import sys
import re

sys.stdout.reconfigure(encoding='utf-8')

extra_queries = [
    ('Regime Detection (HMM/Clustering)', 'ti:"Regime" AND (ti:"Hidden Markov" OR ti:"clustering") AND cat:q-fin.*'),
    ('Lead-Lag Microstructure', 'ti:"lead-lag" AND cat:q-fin.*'),
    ('Synthetic Data & GANs in LOB', '(ti:"GAN" OR ti:"Diffusion" OR ti:"synthetic") AND (abs:"limit order book" OR abs:"financial") AND cat:q-fin.*'),
    ('Rough Volatility', 'ti:"Rough Volatility" AND cat:q-fin.*'),
    ('Kalman Filter / Statistical Arbitrage', 'ti:"Kalman" AND cat:q-fin.*'),
    ('NLP / LLM in Trading', '(ti:"LLM" OR ti:"sentiment" OR ti:"language model") AND (ti:"trading" OR abs:"trading strategy") AND cat:q-fin.*'),
    ('Volatility Targeting & Dynamic Sizing', '(ti:"Volatility Targeting" OR ti:"Kelly") AND cat:q-fin.*')
]

ns = {'atom': 'http://www.w3.org/2005/Atom'}

for label, q in extra_queries:
    url = f"http://export.arxiv.org/api/query?search_query={urllib.parse.quote(q)}&max_results=2&sortBy=relevance&sortOrder=descending"
    req = urllib.request.Request(url, headers={'User-Agent': 'QuantResearchExplorer/1.0'})
    try:
        with urllib.request.urlopen(req) as resp:
            root = ET.fromstring(resp.read())
        entries = root.findall('atom:entry', ns)
        print(f"\n=== {label} ===")
        for e in entries:
            title = e.find('atom:title', ns).text.strip().replace('\n', ' ')
            aid = e.find('atom:id', ns).text.strip().split('/abs/')[-1]
            pub = e.find('atom:published', ns).text.strip()[:10]
            summary = e.find('atom:summary', ns).text.strip().replace('\n', ' ')
            print(f"  [{aid}] ({pub}) {title}")
            print(f"    Summary: {summary[:160]}...")
    except Exception as ex:
        print(f"  Error for {label}: {ex}")
