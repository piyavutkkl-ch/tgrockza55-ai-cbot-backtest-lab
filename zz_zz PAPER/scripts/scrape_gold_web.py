import urllib.request
import re
import sys
import json

sys.stdout.reconfigure(encoding='utf-8')

url = "https://arxiv.org/search/q-fin?query=gold&searchtype=all&source=header"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
with urllib.request.urlopen(req) as resp:
    html = resp.read().decode('utf-8', errors='ignore')

# Match each search result block:
# <li class="arxiv-result"> ...
blocks = re.findall(r'<li class="arxiv-result">(.*?)</li>', html, re.DOTALL)
print(f"Total blocks found: {len(blocks)}")

gold_papers = []
for b in blocks:
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
    pub_date = date_m.group(1) if date_m else "2024"
    
    abs_m = re.search(r'<span class="abstract-full[^"]*">(.*?)<a class="is-size-7', b, re.DOTALL)
    if not abs_m:
        abs_m = re.search(r'<span class="abstract-short[^"]*">(.*?)</span>', b, re.DOTALL)
    abstract = re.sub(r'<[^>]+>', '', abs_m.group(1)).strip() if abs_m else ""
    abstract = re.sub(r'\s+', ' ', abstract).replace('▽ More', '').strip()
    
    # filter for high relevance to gold / commodities
    if any(k in title.lower() or k in abstract.lower() for k in ['gold', 'commodity', 'precious metal', 'xau', 'safe haven', 'portfolio']):
        gold_papers.append({
            "arxiv_id": aid,
            "base_id": base_id,
            "title": title,
            "authors": authors,
            "published": pub_date,
            "category_folder": "06_gold_commodity_and_macro",
            "primary_cat": "q-fin.PM",
            "pdf_url": f"https://arxiv.org/pdf/{aid}.pdf",
            "abstract": abstract
        })

print(f"Relevant gold papers parsed: {len(gold_papers)}")
for p in gold_papers[:6]:
    print(f"[{p['arxiv_id']}] {p['title']}")

with open("d:/cbot-atgvt/zz_zz PAPER/scripts/scraped_gold_papers.json", "w", encoding="utf-8") as f:
    json.dump(gold_papers[:8], f, ensure_ascii=False, indent=2)
