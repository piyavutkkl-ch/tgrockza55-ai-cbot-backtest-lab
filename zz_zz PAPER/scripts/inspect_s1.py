import urllib.request
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

url = "https://arxiv.org/html/1808.03668"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req) as resp:
    html = resp.read().decode('utf-8', errors='ignore')

m = re.search(r'<section\s+id="S1"[^>]*>(.*?)</section>', html, re.DOTALL)
if m:
    content = m.group(1)
    print("Section 1 snippet:")
    print(content[:800])
