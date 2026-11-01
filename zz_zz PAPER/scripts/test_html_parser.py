import urllib.request
import re
import sys
from html.parser import HTMLParser

sys.stdout.reconfigure(encoding='utf-8')

class HTMLTextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text = []
        self.ignore = False

    def handle_starttag(self, tag, attrs):
        if tag in ['script', 'style', 'nav', 'header', 'footer']:
            self.ignore = True

    def handle_endtag(self, tag):
        if tag in ['script', 'style', 'nav', 'header', 'footer']:
            self.ignore = False

    def handle_data(self, data):
        if not self.ignore:
            self.text.append(data)

    def get_text(self):
        return ' '.join(self.text)

def clean_html_text(html_fragment):
    parser = HTMLTextExtractor()
    parser.feed(html_fragment)
    raw = parser.get_text()
    return re.sub(r'\s+', ' ', raw).strip()

url = "https://arxiv.org/html/1808.03668"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req) as resp:
    html = resp.read().decode('utf-8', errors='ignore')

m = re.search(r'<section\s+id="S1"[^>]*>(.*?)</section>', html, re.DOTALL)
if m:
    p_tags = re.findall(r'<p\s+[^>]*class="ltx_p"[^>]*>(.*?)</p>', m.group(1), re.DOTALL)
    for i, p in enumerate(p_tags[:2], 1):
        print(f"P{i}: {clean_html_text(p)}")
