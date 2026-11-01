import urllib.request
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

url = 'https://arxiv.org/abs/1808.03668'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
try:
    with urllib.request.urlopen(req) as resp:
        html = resp.read().decode('utf-8', errors='ignore')

    title_m = re.search(r'<h1 class="title mathjax"><span class="descriptor">Title:</span>(.*?)</h1>', html, re.DOTALL)
    title = title_m.group(1).strip() if title_m else 'No title'

    abs_m = re.search(r'<blockquote class="abstract mathjax"><span class="descriptor">Abstract:</span>(.*?)</blockquote>', html, re.DOTALL)
    abstract = abs_m.group(1).strip() if abs_m else 'No abstract'

    print('Status: OK (HTTP 200)')
    print('Title:', title)
    print('Abstract preview:', abstract[:150] + '...')
except Exception as e:
    print('Error:', e)
