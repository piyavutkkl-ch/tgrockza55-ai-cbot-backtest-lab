"""
Test SSRN paper metadata and abstract harvesting via Crossref API & Semantic Scholar
"""

import sys
import json
import urllib.request
import urllib.parse

sys.stdout.reconfigure(encoding='utf-8')

queries = [
    'gold intraday trading vwap microstructure',
    'order flow imbalance limit order book alpha',
    'market making optimal bid ask spread inventory',
    'high frequency algorithmic trading execution vwap',
    'rough volatility jumps gold commodities hawkes',
    'auction market theory value area volume profile'
]

papers = []
seen_dois = set()

for q in queries:
    url = f'https://api.crossref.org/works?query={urllib.parse.quote(q)}&filter=prefix:10.2139&rows=8'
    req = urllib.request.Request(url, headers={'User-Agent': 'QuantResearchTool/1.0 (mailto:quant@cbot-lab.org)'})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            items = data['message']['items']
            for item in items:
                doi = item.get('DOI', '')
                if doi in seen_dois:
                    continue
                seen_dois.add(doi)
                title = item.get('title', [''])[0]
                abstract = item.get('abstract', '')
                authors = [f"{a.get('given','')} {a.get('family','')}".strip() for a in item.get('author', [])]
                created = item.get('created', {}).get('date-time', '')
                url_link = item.get('URL', '')
                papers.append({
                    'doi': doi,
                    'title': title,
                    'authors': authors,
                    'abstract': abstract,
                    'created': created,
                    'url': url_link,
                    'query': q
                })
    except Exception as e:
        print(f"Error on {q}: {e}")

print(f"Retrieved {len(papers)} unique SSRN papers.")
for i, p in enumerate(papers[:15]):
    abs_len = len(p['abstract'])
    print(f"{i+1:2d}. [{p['doi']}] {p['title'][:70]}... (Abstract: {abs_len} chars)")
