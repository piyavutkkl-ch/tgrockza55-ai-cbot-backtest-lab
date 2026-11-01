import urllib.request
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

url = "https://arxiv.org/search/q-fin?query=gold&searchtype=all&source=header"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
try:
    with urllib.request.urlopen(req) as resp:
        html = resp.read().decode('utf-8', errors='ignore')
    
    # Extract titles and arxiv ids from search results
    # <p class="list-title is-inline-block"><a href="https://arxiv.org/abs/2105.xxxxx">arXiv:2105.xxxxx</a>
    # <p class="title is-5 mathjax">...
    items = re.findall(r'<a href="https://arxiv.org/abs/([^"]+)">arXiv:\1</a>.*?<p class="title is-5 mathjax">\s*(.*?)\s*</p>', html, re.DOTALL)
    print(f"Found {len(items)} items from arXiv web search!")
    for aid, title in items[:8]:
        clean_title = re.sub(r'\s+', ' ', title).strip()
        print(f"[{aid}] {clean_title}")
except Exception as e:
    print(f"Web search error: {e}")
