import json
import re
import sys
import os

sys.stdout.reconfigure(encoding='utf-8')

# Search for the saved file or download properly to a fixed path
save_path = r"d:\cbot-atgvt\research\chatgpt_share_clean.html"

import urllib.request
url = 'https://chatgpt.com/share/6ae73db5-ca58-83ec-9817-7d253371a924'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
with urllib.request.urlopen(req, timeout=15) as resp:
    html = resp.read().decode('utf-8', errors='ignore')

with open(save_path, 'w', encoding='utf-8') as f:
    f.write(html)

print(f"Downloaded HTML length: {len(html)}")

# Check for __NEXT_DATA__
match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html, re.DOTALL)
if match:
    data = json.loads(match.group(1))
    print("Found __NEXT_DATA__!")
    with open(r"d:\cbot-atgvt\research\chatgpt_next_data.json", 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("Saved __NEXT_DATA__ to chatgpt_next_data.json")
else:
    print("No __NEXT_DATA__ found, checking for window.__remixContext or other script blobs...")
    # Find all json script tags
    scripts = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL)
    for i, s in enumerate(scripts):
        if 'serverResponse' in s or 'linear_conversation' in s or 'title' in s or 'mapping' in s or 'messages' in s:
            print(f"Found candidate script {i}, len {len(s)}")
            with open(rf"d:\cbot-atgvt\research\chatgpt_script_{i}.js", 'w', encoding='utf-8') as f:
                f.write(s)
