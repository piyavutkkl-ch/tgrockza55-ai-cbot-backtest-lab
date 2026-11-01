import urllib.request, re, sys
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

# find subsections or math
m = re.search(r'<section\s+id="S3"[^>]*>(.*?)</section>', html, re.DOTALL)
if m:
    s3_content = m.group(1)
    paras = re.findall(r'<p\s+[^>]*class="ltx_p"[^>]*>(.*?)</p>', s3_content, re.DOTALL)
    print(f"Total paragraphs in S3: {len(paras)}")
    for i, p in enumerate(paras):
        txt = clean(p)
        if any(w in txt.lower() for w in ['label', 'horizon', 'mid-price', 'threshold', 'alpha', 'formula']):
            print(f"[{i}] {txt}\n")
