import urllib.request
import re
import sys
from html.parser import HTMLParser

sys.stdout.reconfigure(encoding='utf-8')

class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text = []
        self.ignore = False
    def handle_starttag(self, tag, attrs):
        if tag in ['script', 'style']: self.ignore = True
    def handle_endtag(self, tag):
        if tag in ['script', 'style']: self.ignore = False
    def handle_data(self, data):
        if not self.ignore: self.text.append(data)
    def get_text(self):
        return ' '.join(self.text)

def clean(s):
    t = TextExtractor()
    t.feed(s)
    return re.sub(r'\s+', ' ', t.get_text()).strip()

url = "https://arxiv.org/html/1808.03668"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req) as resp:
    html = resp.read().decode('utf-8', errors='ignore')

for sec_id in ['S3', 'S4', 'S5']:
    m = re.search(rf'<section\s+id="{sec_id}"[^>]*>(.*?)</section>', html, re.DOTALL)
    if m:
        sec_text = m.group(1)
        h2 = re.search(r'<h2[^>]*>(.*?)</h2>', sec_text, re.DOTALL)
        t = clean(h2.group(1)) if h2 else sec_id
        print(f"\n==================== {t} ====================")
        paras = re.findall(r'<p\s+[^>]*class="ltx_p"[^>]*>(.*?)</p>', sec_text, re.DOTALL)
        for p in paras[:4]:
            print(" -", clean(p))
