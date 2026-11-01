import urllib.request
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

test_candidates = [
    '2101.07011', '1906.03848', '2203.06450', '2010.03803', '1904.05315', '2301.08745'
]

for cid in test_candidates:
    url = f"https://arxiv.org/abs/{cid}"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
            title_m = re.search(r'<h1 class="title mathjax"><span class="descriptor">Title:</span>(.*?)</h1>', html, re.DOTALL)
            title = title_m.group(1).strip() if title_m else 'No title'
            print(f"[{cid}] {title}")
    except Exception as e:
        print(f"[{cid}] Not found: {e}")
