import urllib.request
import urllib.parse
import re
import sys
import json
import time

sys.stdout.reconfigure(encoding='utf-8')

def scrape_arxiv_web_search(query_term, max_items=10):
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

test_res = scrape_arxiv_web_search("kalman filter", max_items=3)
print(f"Parsed {len(test_res)} items for kalman filter:")
for r in test_res:
    print(f" - [{r['arxiv_id']}] ({r['published']}) {r['title']}")
